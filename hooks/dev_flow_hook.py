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


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PLUGIN_ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dependency_contracts import (  # noqa: E402
    DEPENDENCY_FILE_RE,
    action_reference_diff,
    action_reference_scan,
    looks_like_package_mutation,
    matches_dependency_request,
    parse_package_command,
)

SHELL_MUTATION_RE = re.compile(
    r"(?:"
    r"\b(?:apply_patch|sed\s+-i|perl\s+-i|tee|touch|mkdir|mv|cp|rm|ln|chmod|chown|truncate|install|dd)\b|"
    r"\bgit\s+(?:add|commit|merge|rebase|tag|push)\b|"
    r"\b(?:cargo\s+add|pnpm\s+add|npm\s+install|yarn\s+add|bun\s+add)\b|"
    r"(?:^|[;&|]\s*)[^;&|\n]*(?:>>?|2>)\s*[^&|\n]+"
    r")",
    re.IGNORECASE,
)
TYPED_MUTATION_TOOLS = {"apply_patch", "Edit", "Write"}
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
AGENT_LIFECYCLE_STATES = {
    "discovering",
    "awaiting-approval",
    "approved",
    "implementing",
    "verifying",
}


def output(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def locate_packet(cwd: Path) -> Path | None:
    for root in (cwd, *cwd.parents):
        flow = root / ".codex" / "dev-flow"
        current = flow / "current"
        if flow.is_symlink() or current.is_symlink():
            continue
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
        value = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def agent_lifecycle_active(metadata: dict[str, Any]) -> bool:
    """Return whether this packet may govern child-agent lifecycle hooks."""
    return metadata.get("state") in AGENT_LIFECYCLE_STATES


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


def mutation_targets(event: dict[str, Any]) -> list[str]:
    name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    if name == "apply_patch":
        patch_text = "\n".join(string_values(tool_input))
        return re.findall(r"(?m)^\*\*\* (?:Update|Add|Delete) File: (.+?)\s*$", patch_text)
    if name in {"Edit", "Write"} and isinstance(tool_input, dict):
        return [
            value
            for key in ("file_path", "filePath", "path", "target_file")
            if isinstance((value := tool_input.get(key)), str) and value.strip()
        ]
    return []


def event_is_mutation(event: dict[str, Any], text: str | None = None) -> bool:
    name = str(event.get("tool_name", ""))
    if name in TYPED_MUTATION_TOOLS:
        return True
    return name == "Bash" and bool(SHELL_MUTATION_RE.search(text if text is not None else tool_text(event)))


def bash_command(event: dict[str, Any]) -> str:
    tool_input = event.get("tool_input")
    if not isinstance(tool_input, dict):
        return ""
    command = tool_input.get("command")
    return command if isinstance(command, str) else ""


def relative_target(target: str, cwd: Path, root: Path) -> str | None:
    path = Path(target.strip())
    resolved = (path if path.is_absolute() else cwd / path).resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def package_command_requests(event: dict[str, Any], root: Path) -> tuple[list[dict[str, Any]], bool]:
    command = bash_command(event).strip()
    parsed = parse_package_command(command)
    if parsed is None:
        return [], looks_like_package_mutation(command)
    cwd = Path(str(event.get("cwd") or os.getcwd())).resolve()
    try:
        cwd_relative = cwd.relative_to(root.resolve())
    except ValueError:
        return [], True
    prefix = "" if str(cwd_relative) == "." else cwd_relative.as_posix() + "/"
    manifest = (
        "Cargo.lock"
        if parsed["ecosystem"] == "cargo" and parsed["operation"] == "update"
        else "Cargo.toml"
        if parsed["ecosystem"] == "cargo"
        else "package.json"
    )
    return [
        {
            **parsed,
            "file": prefix + manifest,
        }
    ], False


def dependency_requests(event: dict[str, Any], packet: Path, text: str) -> tuple[list[dict[str, Any]], bool]:
    root = packet.parents[2]
    name = str(event.get("tool_name", ""))
    if name == "Bash":
        requests, unbindable = package_command_requests(event, root)
        if requests or unbindable:
            return requests, unbindable
        if event_is_mutation(event, text) and DEPENDENCY_RE.search(text):
            return [], True
        return [], False
    if name not in TYPED_MUTATION_TOOLS:
        return [], False
    cwd = Path(str(event.get("cwd") or os.getcwd())).resolve()
    targets = [relative_target(target, cwd, root) for target in mutation_targets(event)]
    if any(target is None for target in targets):
        return [], True
    normalized_targets = [target for target in targets if target is not None]
    if any(DEPENDENCY_FILE_RE.search(target) for target in normalized_targets):
        return [], True
    requests: list[dict[str, Any]] = []
    mutation_text = "\n".join(string_values(event.get("tool_input", {})))
    added_refs, removed_refs, invalid_refs = action_reference_diff(mutation_text)
    all_refs, all_invalid_refs = action_reference_scan(mutation_text)
    invalid_refs.extend(all_invalid_refs)
    workflow_targets = [target for target in normalized_targets if re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", target)]
    if invalid_refs or ((added_refs or removed_refs or all_refs) and not workflow_targets):
        return [], True
    for target in workflow_targets:
        current_refs: set[tuple[str, str]] = set()
        current_path = root / target
        if current_path.is_file() and not current_path.is_symlink():
            try:
                current_refs = action_reference_scan(current_path.read_text(encoding="utf-8"))[0]
            except (OSError, UnicodeDecodeError):
                return [], True
        if not added_refs and not removed_refs and name in {"Write", "Edit"}:
            tool_input = event.get("tool_input", {})
            if not isinstance(tool_input, dict):
                return [], True
            if name == "Write":
                proposed_text = next(
                    (tool_input[key] for key in ("content", "text") if isinstance(tool_input.get(key), str)),
                    None,
                )
                if proposed_text is None:
                    return [], True
                proposed_refs, proposed_invalid = action_reference_scan(proposed_text)
                if proposed_invalid:
                    return [], True
                added_refs = proposed_refs - current_refs
                removed_refs = current_refs - proposed_refs
            else:
                old_text = next(
                    (tool_input[key] for key in ("old_string", "oldText") if isinstance(tool_input.get(key), str)),
                    None,
                )
                new_text = next(
                    (tool_input[key] for key in ("new_string", "newText") if isinstance(tool_input.get(key), str)),
                    None,
                )
                if old_text is None or new_text is None:
                    return [], True
                old_refs, old_invalid = action_reference_scan(old_text)
                new_refs, new_invalid = action_reference_scan(new_text)
                if old_invalid or new_invalid:
                    return [], True
                added_refs = new_refs - old_refs
                removed_refs = old_refs - new_refs
        replaced_names = {action_name for action_name, _ in added_refs} & {
            action_name for action_name, _ in removed_refs
        }
        requests.extend(
            {
                "ecosystem": "github-actions",
                "name": action_name,
                "ref": action_ref,
                "operation": "update" if action_name in replaced_names or any(
                    current_name == action_name for current_name, _ in current_refs
                ) else "add",
                "file": target,
                "command": None,
            }
            for action_name, action_ref in added_refs
        )
        requests.extend(
            {
                "ecosystem": "github-actions",
                "name": action_name,
                "ref": action_ref,
                "operation": "remove",
                "file": target,
                "command": None,
            }
            for action_name, action_ref in removed_refs
            if action_name not in replaced_names
        )
    return requests, False


def mutation_is_packet_only(event: dict[str, Any], packet: Path) -> bool:
    targets = mutation_targets(event)
    if not targets:
        return False
    cwd = Path(str(event.get("cwd") or os.getcwd())).resolve()
    packet_root = packet.resolve()
    for target in targets:
        path = Path(target.strip())
        resolved = (path if path.is_absolute() else cwd / path).resolve()
        if not resolved.is_relative_to(packet_root):
            return False
    return True


def open_material_ambiguity_ids(metadata: dict[str, Any]) -> list[str]:
    if metadata.get("schema_version") not in {"1.2", "2.0"} or metadata.get("state") not in {
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
    if name == "Agent" and agent_lifecycle_active(metadata):
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
    is_mutation = event_is_mutation(event, text)
    gate_mutation = is_mutation or name == "Bash"
    requests, unbindable_dependency = dependency_requests(event, packet, text)
    if requests or unbindable_dependency:
        approvals_value = metadata.get("approvals", {})
        approvals = approvals_value.get("dependencies", []) if isinstance(approvals_value, dict) else []
        approved = isinstance(approvals, list) and not unbindable_dependency and all(
            any(matches_dependency_request(record, **request) for record in approvals)
            for request in requests
        )
        if not approved:
            output(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": (
                            "Dependency mutation is unbindable or does not exactly match an approved ecosystem, name, "
                            "version/ref, operation, and file in packet.json. Use a single exact package-manager command "
                            "or record a machine-readable dependency decision first."
                        ),
                    }
                }
            )
            return
    open_ambiguities = open_material_ambiguity_ids(metadata)
    if gate_mutation and open_ambiguities and not mutation_is_packet_only(event, packet):
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
    if gate_mutation and not packet_only and readiness.get("outcome") in {"blocked", "invalid"}:
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
    if requests:
        advisory.append(
            "This mutation touches a manifest or lockfile. Inspect the exact diff and stop before any new dependency or material feature/tool/service expansion unless its named approval is recorded."
        )
    if advisory:
        output({"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": " ".join(advisory)}})


def post_tool(event: dict[str, Any], packet: Path) -> None:
    text = tool_text(event)
    if event_is_mutation(event, text):
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


def remove_agent_marker(event: dict[str, Any]) -> None:
    try:
        agent_marker(event).unlink(missing_ok=True)
    except OSError:
        pass


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
    marker_advisory = ""
    try:
        marker.parent.mkdir(parents=True, exist_ok=True)
        prune_agent_markers(marker.parent)
        marker.write_text(
            json.dumps({"packet_hash": packet_identifier(packet), "started_at": time.time()}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        marker_advisory = " DEV_FLOW_AGENT_MARKER_UNAVAILABLE: lifecycle remains fail-open; root reconciliation is required."
    output(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": (
                    f"Use the written brief under {packet / 'briefs'}. Respect exclusive ownership, do not add "
                    "dependencies or expand scope, and return a bounded native final result. Write under "
                    f"{packet / 'reports'} only when the brief explicitly assigns a durable report.{marker_advisory}"
                ),
            }
        }
    )


def subagent_stop(event: dict[str, Any], packet: Path) -> None:
    started_at: float | None = None
    marker = agent_marker(event)
    try:
        marker_data = json.loads(marker.read_text(encoding="utf-8"))
        if isinstance(marker_data, dict) and marker_data.get("packet_hash") == packet_identifier(packet):
            started_at = float(marker_data.get("started_at", 0.0))
    except (OSError, ValueError, json.JSONDecodeError):
        pass

    report_found = False
    if started_at is not None:
        try:
            for path in (packet / "reports").glob("*.md"):
                try:
                    if not path.name.startswith("README.") and path.stat().st_mtime >= started_at - 1.0:
                        report_found = True
                        break
                except OSError:
                    continue
        except OSError:
            pass
    remove_agent_marker(event)

    if report_found:
        output({})
        return
    output(
        {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStop",
                "additionalContext": (
                    "DEV_FLOW_AGENT_REPORT_MISSING: native subagent stop is allowed. Reconcile the native final "
                    "result and record an explicit disposition; do not redispatch solely because a durable report "
                    "is absent."
                ),
            }
        }
    )


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
        if event.get("hook_event_name") == "SubagentStop":
            remove_agent_marker(event)
            output({})
        elif event.get("hook_event_name") == "Stop":
            output({})
        return 0
    hook = event.get("hook_event_name")
    metadata = packet_metadata(packet)
    if hook in {"SubagentStart", "SubagentStop"} and not agent_lifecycle_active(metadata):
        if hook == "SubagentStop":
            remove_agent_marker(event)
            output({})
        return 0
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
