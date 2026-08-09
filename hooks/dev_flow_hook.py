#!/usr/bin/env python3
"""Conservative Codex hooks for an explicitly active Dev Flow packet."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any


MUTATION_RE = re.compile(
    r"(?:apply_patch|\b(?:sed\s+-i|perl\s+-i|tee|touch|mkdir|mv|cp|git\s+(?:add|commit)|cargo\s+add|pnpm\s+add|npm\s+install)\b)",
    re.IGNORECASE,
)
DEPENDENCY_RE = re.compile(
    r"(?:Cargo\.toml|Cargo\.lock|package\.json|pnpm-lock\.yaml|package-lock\.json|yarn\.lock|"
    r"pyproject\.toml|requirements[^/\s]*\.txt|go\.mod|Gemfile|Podfile|Package\.swift|"
    r"build\.gradle|libs\.versions\.toml)",
    re.IGNORECASE,
)
COMPLETION_RE = re.compile(
    r"(?:\bcomplete(?:d)?\b|\bfixed\b|\bpassing\b|\bverified\b|\brelease[- ]ready\b|"
    r"已完成|已修复|全部通过|验证通过|可以发布|提交完成)",
    re.IGNORECASE,
)


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def locate_packet(cwd: Path) -> Path | None:
    for root in (cwd, *cwd.parents):
        flow = root / ".codex" / "dev-flow"
        current = flow / "current"
        if not current.is_file():
            continue
        change_id = current.read_text(encoding="utf-8").strip()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", change_id):
            return None
        packet = (flow / change_id).resolve()
        if packet.parent != flow.resolve() or not packet.is_dir():
            return None
        return packet
    return None


def tool_text(event: dict[str, Any]) -> str:
    value = event.get("tool_input", {})
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def packet_metadata(packet: Path) -> dict[str, Any]:
    try:
        return json.loads((packet / "packet.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def context_readiness(packet: Path) -> dict[str, Any]:
    path = packet / "context-readiness.json"
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"outcome": "invalid", "errors": ["context-readiness.json is unreadable"]}
    return value if isinstance(value, dict) else {"outcome": "invalid", "errors": ["context-readiness.json must be an object"]}


def string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        return [item for nested in value.values() for item in string_values(nested)]
    if isinstance(value, list):
        return [item for nested in value for item in string_values(nested)]
    return []


def mutation_is_packet_only(event: dict[str, Any], packet: Path) -> bool:
    if str(event.get("tool_name", "")) != "apply_patch":
        return False
    patch_text = "\n".join(string_values(event.get("tool_input", {})))
    targets = re.findall(r"(?m)^\*\*\* (?:Update|Add|Delete) File: (.+?)\s*$", patch_text)
    if not targets:
        return False
    cwd = Path(str(event.get("cwd") or os.getcwd())).resolve()
    for target in targets:
        path = Path(target.strip())
        resolved = (path if path.is_absolute() else cwd / path).resolve()
        if not resolved.is_relative_to(packet):
            return False
    return True


def open_material_ambiguity_ids(metadata: dict[str, Any]) -> list[str]:
    if metadata.get("schema_version") != "1.2" or metadata.get("state") not in {
        "implementing",
        "verifying",
        "blocked",
    }:
        return []
    records = metadata.get("ambiguities", [])
    if not isinstance(records, list):
        return []
    return [
        str(record.get("id"))
        for record in records
        if isinstance(record, dict)
        and record.get("status") == "open"
        and record.get("materiality") in {"material", "high-risk"}
    ]


def pre_tool(event: dict[str, Any], packet: Path) -> None:
    name = str(event.get("tool_name", ""))
    text = tool_text(event)
    metadata = packet_metadata(packet)
    if name == "Agent":
        briefs = [path for path in (packet / "briefs").glob("*.md") if not path.name.startswith("README.")]
        if not briefs:
            output(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "Create a bounded task brief in the active packet before spawning an agent.",
                    }
                }
            )
            return
    explicit_dependency_command = bool(re.search(r"\b(?:cargo\s+add|pnpm\s+add|npm\s+install|yarn\s+add|bun\s+add)\b", text, re.IGNORECASE))
    if explicit_dependency_command:
        approvals = metadata.get("approvals", {}).get("dependencies", [])
        if not approvals:
            output(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": "Manifest or lockfile mutation requires a named dependency decision and explicit approval recorded in packet.json.",
                    }
                }
            )
            return
    is_mutation = name == "apply_patch" or bool(MUTATION_RE.search(text))
    open_ambiguities = open_material_ambiguity_ids(metadata)
    if is_mutation and open_ambiguities and not mutation_is_packet_only(event, packet):
        output(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        f"Open material semantic ambiguity {', '.join(open_ambiguities)} blocks product mutation. "
                        "Update the active packet, reopen awaiting approval, and obtain an authorized disposition first."
                    ),
                }
            }
        )
        return
    readiness = context_readiness(packet)
    packet_only = mutation_is_packet_only(event, packet)
    if is_mutation and not packet_only and readiness.get("outcome") in {"blocked", "invalid"}:
        output(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Engineering Context Readiness blocks product mutation. Repair or explicitly waive the "
                        "recorded governed gap in context-readiness.json; packet-only repair remains allowed."
                    ),
                }
            }
        )
        return
    advisory: list[str] = []
    if (
        is_mutation
        and not packet_only
        and readiness.get("outcome") == "checkpoint"
        and not readiness.get("suppression")
    ):
        advisory.append(
            "Engineering Context Readiness is at a checkpoint. Review its minimal recommendations and record an owner skip or waiver before claiming completion."
        )
    if (
        is_mutation
        and not packet_only
        and not readiness
        and metadata.get("state") in {"implementing", "verifying"}
        and metadata.get("risk_modifiers")
    ):
        advisory.append(
            "No context-readiness.json is recorded. For risk-bearing work, run task-relative assess-context; absence alone is advisory and does not block this mutation."
        )
    if is_mutation and DEPENDENCY_RE.search(text):
        advisory.append(
            "This mutation touches a manifest or lockfile. Inspect the exact diff and stop before any new dependency or material feature/tool/service expansion unless its named approval is recorded."
        )
    if advisory:
        output({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": " ".join(advisory)}})


def post_tool(event: dict[str, Any], packet: Path) -> None:
    name = str(event.get("tool_name", ""))
    text = tool_text(event)
    if name == "apply_patch" or MUTATION_RE.search(text):
        output(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": (
                        f"Active Dev Flow packet: {packet}. Update execution progress, decisions/drift, "
                        "scope mapping, and evidence for this material mutation before closing the slice."
                    ),
                }
            }
        )


def agent_marker(event: dict[str, Any]) -> Path:
    data_root = Path(os.environ.get("PLUGIN_DATA", Path.home() / ".codex" / "plugins" / "data" / "dev-flow"))
    identity = f"{event.get('session_id', '')}:{event.get('agent_id', '')}".encode("utf-8")
    return data_root / "agent-runs" / f"{hashlib.sha256(identity).hexdigest()}.json"


def packet_identifier(packet: Path) -> str:
    return hashlib.sha256(str(packet).encode("utf-8")).hexdigest()


def prune_agent_markers(marker_directory: Path, *, max_age_seconds: float = 7 * 24 * 60 * 60) -> None:
    cutoff = time.time() - max_age_seconds
    try:
        candidates = list(marker_directory.glob("*.json"))
    except OSError:
        return
    for candidate in candidates:
        try:
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            continue


def subagent_start(event: dict[str, Any], packet: Path) -> None:
    marker = agent_marker(event)
    marker.parent.mkdir(parents=True, exist_ok=True)
    prune_agent_markers(marker.parent)
    marker.write_text(
        json.dumps({"packet_hash": packet_identifier(packet), "started_at": time.time()}, ensure_ascii=False),
        encoding="utf-8",
    )
    output(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": (
                    f"Use the written brief under {packet / 'briefs'}. Respect exclusive ownership, do not add "
                    f"dependencies or expand scope, and write only the assigned report under {packet / 'reports'}."
                ),
            }
        }
    )


def subagent_stop(event: dict[str, Any], packet: Path) -> None:
    started_at = 0.0
    marker = agent_marker(event)
    try:
        marker_data = json.loads(marker.read_text(encoding="utf-8"))
        if marker_data.get("packet_hash") == packet_identifier(packet):
            started_at = float(marker_data.get("started_at", 0.0))
    except (OSError, ValueError, json.JSONDecodeError):
        pass
    reports = [
        path
        for path in (packet / "reports").glob("*.md")
        if not path.name.startswith("README.") and path.stat().st_mtime >= started_at - 1.0
    ]
    if not reports and not bool(event.get("stop_hook_active")):
        output({"decision": "block", "reason": f"Write the required bounded agent report under {packet / 'reports'} before stopping."})
    else:
        marker.unlink(missing_ok=True)
        output({})


def load_validator() -> Any:
    root = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
    module_path = root / "skills" / "dev-flow" / "scripts" / "dev_flow.py"
    spec = importlib.util.spec_from_file_location("dev_flow_hook_runtime", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load validator: {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def stop(event: dict[str, Any], packet: Path) -> None:
    metadata = packet_metadata(packet)
    message = str(event.get("last_assistant_message") or "")
    should_gate = metadata.get("state") in {"verifying", "accepted"} or bool(COMPLETION_RE.search(message))
    if not should_gate:
        output({})
        return
    try:
        report, code = load_validator().validate_packet_data(packet)
    except Exception as exc:  # Hook must fail conservatively without leaking internals.
        output({"systemMessage": f"Dev Flow could not validate the active packet: {exc}"})
        return
    if code and not bool(event.get("stop_hook_active")):
        summary = "; ".join(report.get("errors", [])[:5])
        output({"decision": "block", "reason": f"Completion is not traceable yet. Repair the active packet: {summary}"})
    elif code:
        output({"systemMessage": "Dev Flow packet remains invalid after the stop-hook continuation; report it as an explicit blocker."})
    else:
        output({})


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    packet = locate_packet(Path(str(event.get("cwd") or os.getcwd())).resolve())
    if packet is None:
        if event.get("hook_event_name") in {"SubagentStop", "Stop"}:
            output({})
        return 0
    hook = event.get("hook_event_name")
    if hook == "PreToolUse":
        pre_tool(event, packet)
    elif hook == "PostToolUse":
        post_tool(event, packet)
    elif hook == "SubagentStart":
        subagent_start(event, packet)
    elif hook == "SubagentStop":
        subagent_stop(event, packet)
    elif hook == "Stop":
        stop(event, packet)
    return 0


if __name__ == "__main__":
    sys.exit(main())
