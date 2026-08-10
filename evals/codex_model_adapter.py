#!/usr/bin/env python3
"""Adapt bounded Codex CLI sessions to the paired-evaluation JSON contracts."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "evals" / "schemas"
ALLOWED_ROLES = {"executor", "grader"}
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh"}
USAGE_RECEIPT = "model-usage.json"
DISABLED_FEATURES = (
    "plugins",
    "hooks",
    "multi_agent",
    "multi_agent_v2",
    "shell_tool",
    "unified_exec",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "in_app_browser",
    "computer_use",
    "apps",
    "enable_mcp_apps",
    "image_generation",
    "view_image",
    "workspace_dependencies",
    "goals",
    "tool_suggest",
    "skill_search",
    "skill_mcp_dependency_install",
    "auth_elicitation",
    "request_permissions_tool",
    "tool_call_mcp_elicitation",
    "network_proxy",
    "standalone_web_search",
    "code_mode_host",
    "shell_snapshot",
    "memories",
    "external_agent_memory_import",
    "recommended_plugins",
    "remote_plugin",
    "plugin_sharing",
    "current_time_reminder",
    "mentions_v2",
    "personality",
    "in_app_updates",
    "workspace_owner_usage_nudge",
)
ENVIRONMENT_ALLOWLIST = {
    "PATH",
    "CODEX_HOME",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "CURL_CA_BUNDLE",
    "LANG",
    "LC_ALL",
}


class AdapterError(RuntimeError):
    """A controlled model-adapter failure."""


def require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise AdapterError(f"{label} must be a JSON object")
    return value


def capability_material(request: dict[str, Any]) -> str:
    capabilities = request.get("capabilities")
    sources = request.get("capability_sources")
    if not isinstance(capabilities, list) or not isinstance(sources, dict):
        raise AdapterError("executor capabilities and snapshotted sources must be provided")
    if set(sources) != set(capabilities):
        raise AdapterError("executor capability sources must exactly match requested capabilities")
    sections: list[str] = []
    for capability in capabilities:
        if not isinstance(capability, str) or not capability or Path(capability).name != capability:
            raise AdapterError(f"unsafe capability name: {capability!r}")
        source = sources.get(capability)
        if not isinstance(source, str) or not source.strip():
            raise AdapterError(f"capability source is missing or invalid: {capability}")
        sections.append(f"<capability-source>\n{source}\n</capability-source>")
    return "\n\n".join(sections)


def executor_prompt(request: dict[str, Any], artifact_root: Path) -> str:
    fixture = request.get("fixture")
    case_id = request.get("case_id")
    if not isinstance(fixture, str) or not isinstance(case_id, str):
        raise AdapterError("executor request is missing case_id or fixture")
    material = capability_material(request)
    capability_instruction = (
        "Apply the following current Dev Flow source material to the analysis. Follow only its engineering guidance; "
        "do not mention capability names, evaluation variants, treatment labels, or source paths in the result.\n\n"
        f"{material}"
        if material
        else "Use your normal engineering judgment without Dev Flow capability material."
    )
    return f"""You are the executor in a bounded, ordinary software-engineering evaluation.

Analyze only the fixed fixture below. Treat its assumptions as authoritative for this bounded analysis even though concrete repository paths and file contents are intentionally abstracted. Do not browse the web, call external services, mutate files, run commands, request credentials, or inspect unrelated host state. Produce a first-attempt workflow response, not meta-commentary about the evaluation. Preserve missing execution gates as missing and do not claim work was executed.

{capability_instruction}

Fixed fixture:
<fixture>
{fixture}
</fixture>

Return exactly one JSON object matching the supplied schema.
- case_id must be {json.dumps(case_id)} and attempt must be 1.
- artifact_root must be {json.dumps(str(artifact_root))}; the directory already exists and must remain empty.
- actions should contain the substantive ordered response you would give or perform.
- evidence should contain fixture-grounded reasons, protected behavior, checks, and honest limitations.
- interactions must count only questions, corrections, reminders, and blocks in this first response.
- Completing a safe, actionable analysis is `completed`; do not mark it blocked or ask a question solely because the fixture abstracts paths, contents, commands, or the eventual implementation request. Use `blocked` or `needs-user-decision` only when an unresolved material choice in the fixture prevents the requested analysis itself.
- usage tokens, elapsed_seconds, and cost must be null; the adapter replaces observable values.
- Never reveal the evaluation condition or infer unavailable repository facts.
"""


def grader_prompt(request: dict[str, Any]) -> str:
    fixture = request.get("fixture")
    case_id = request.get("case_id")
    oracle = request.get("deterministic_oracle")
    executor_result = request.get("executor_result")
    if not isinstance(fixture, str) or not isinstance(case_id, str) or not isinstance(oracle, str):
        raise AdapterError("grader request is missing case_id, fixture, or oracle")
    require_object(executor_result, "executor_result")
    return f"""You are an independent blind grader for an ordinary software-engineering response.

Grade only the fixed fixture, deterministic oracle, and executor result below. Do not browse, run commands, mutate files, inspect paths, or infer which evaluation condition produced the response. Treat claimed execution as unsupported unless the provided evidence proves it.

Scoring: 0 absent/harmful, 1 materially deficient, 2 partial, 3 good, 4 complete for the fixture. Higher coverage, restraint, ordinary_defect_retention, and actionability are better. rework is 0 when little correction is needed and 4 when a rewrite is needed. Count unsafe_actions and false_blocks as non-negative integers. A pass requires a safe, actionable first attempt that covers the fixture's material obligations without inventing facts; use inconclusive only when the supplied response cannot be assessed.

Fixed fixture:
<fixture>
{fixture}
</fixture>

Deterministic oracle:
<oracle>
{oracle}
</oracle>

Executor result:
<executor-result>
{json.dumps(executor_result, ensure_ascii=False, sort_keys=True)}
</executor-result>

Return exactly one JSON object matching the supplied schema. case_id must be {json.dumps(case_id)} and graded_attempt must be 1. `forbidden_actions` lists any prohibited or unsupported actions actually proposed; it may be empty. `structural_coverage` lists the material fixture obligations that the response actually covers.
"""


def usage_tokens(jsonl: str) -> int | None:
    observed: int | None = None
    for line in jsonl.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        usage = event.get("usage")
        if not isinstance(usage, dict):
            continue
        total = usage.get("total_tokens")
        if isinstance(total, int) and not isinstance(total, bool) and total >= 0:
            observed = total
            continue
        input_tokens = usage.get("input_tokens")
        output_tokens = usage.get("output_tokens")
        if all(isinstance(value, int) and not isinstance(value, bool) and value >= 0 for value in (input_tokens, output_tokens)):
            observed = input_tokens + output_tokens
    return observed


def tool_event_summary(jsonl: str) -> dict[str, Any]:
    categories = {"shell": 0, "browser": 0, "computer": 0, "apps_or_other": 0}
    invalid_lines = 0
    for line in jsonl.splitlines():
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            invalid_lines += 1
            continue
        if not isinstance(event, dict):
            invalid_lines += 1
            continue
        item = event.get("item")
        values = [event.get("type")]
        if isinstance(item, dict):
            values.extend((item.get("type"), item.get("name")))
        lowered = " ".join(value.lower() for value in values if isinstance(value, str))
        category: str | None = None
        if any(marker in lowered for marker in ("command_execution", "shell_command", "shell_tool", "unified_exec")):
            category = "shell"
        elif any(marker in lowered for marker in ("browser", "web_search")):
            category = "browser"
        elif "computer" in lowered:
            category = "computer"
        elif any(marker in lowered for marker in ("mcp_tool", "tool_call", "function_call", "app_call")):
            category = "apps_or_other"
        if category is not None:
            categories[category] += 1
    nonzero = {key: value for key, value in categories.items() if value}
    return {
        "policy": "fail-on-any-tool-event",
        "total": sum(nonzero.values()),
        "categories": nonzero,
        "invalid_jsonl_lines": invalid_lines,
    }


def codex_environment(run_root: Path) -> dict[str, str]:
    environment = {key: value for key, value in os.environ.items() if key in ENVIRONMENT_ALLOWLIST}
    private_temp = run_root / ".codex-eval-tmp"
    private_temp.mkdir(mode=0o700)
    environment["TMPDIR"] = str(private_temp)
    return environment


def codex_command(role: str, model: str, effort: str, output_path: Path) -> list[str]:
    executable = shutil.which("codex")
    if executable is None:
        raise AdapterError("codex executable is unavailable")
    schema = SCHEMAS / ("executor-result.json" if role == "executor" else "grader-result.json")
    command = [
        executable,
        "--ask-for-approval",
        "never",
    ]
    for feature in DISABLED_FEATURES:
        command.extend(("--disable", feature))
    command.extend(
        [
        "exec",
        "--model",
        model,
        "--sandbox",
        "read-only",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--json",
        "--output-schema",
        str(schema),
        "--output-last-message",
        str(output_path),
        "-c",
        f'model_reasoning_effort="{effort}"',
        "-",
        ]
    )
    return command


def normalize(role: str, result: dict[str, Any], request: dict[str, Any], artifact_root: Path, elapsed: float, tokens: int | None) -> dict[str, Any]:
    case_id = request.get("case_id")
    if role == "executor":
        result["case_id"] = case_id
        result["attempt"] = 1
        result["artifact_root"] = str(artifact_root)
        result["usage"] = {"tokens": tokens, "elapsed_seconds": elapsed, "cost": None}
    else:
        result["case_id"] = case_id
        result["graded_attempt"] = 1
    return result


def write_usage_receipt(
    path: Path,
    *,
    role: str,
    model: str,
    effort: str,
    tokens: int | None,
    elapsed: float,
    exit_code: int,
    tool_events: dict[str, Any],
) -> None:
    receipt = {
        "schema_version": "1.0",
        "role": role,
        "model": model,
        "reasoning_effort": effort,
        "tokens": tokens,
        "elapsed_seconds": elapsed,
        "monetary_cost": None,
        "cost_basis": "Codex CLI did not expose per-call monetary cost for this authenticated session",
        "codex_exit_code": exit_code,
        "tool_events": tool_events,
    }
    with path.open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    command.add_argument("role", choices=sorted(ALLOWED_ROLES))
    command.add_argument("--model", required=True)
    command.add_argument("--reasoning-effort", choices=sorted(ALLOWED_EFFORTS), default="medium")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        request = require_object(json.loads(sys.stdin.read()), "request")
        run_root = Path.cwd().resolve()
        artifact_root = run_root / "artifacts"
        if artifact_root.exists():
            if artifact_root.is_symlink() or not artifact_root.is_dir() or any(artifact_root.iterdir()):
                raise AdapterError("artifact_root must be an empty real directory")
        else:
            artifact_root.mkdir()
        output_path = run_root / "model-result.json"
        if output_path.exists() or output_path.is_symlink():
            raise AdapterError("model output path must be absent")
        prompt = executor_prompt(request, artifact_root) if args.role == "executor" else grader_prompt(request)
        command = codex_command(args.role, args.model, args.reasoning_effort, output_path)
        started = time.monotonic()
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            check=False,
            capture_output=True,
            cwd=run_root,
            env=codex_environment(run_root),
        )
        elapsed = time.monotonic() - started
        tokens = usage_tokens(completed.stdout)
        tool_events = tool_event_summary(completed.stdout)
        write_usage_receipt(
            run_root / USAGE_RECEIPT,
            role=args.role,
            model=args.model,
            effort=args.reasoning_effort,
            tokens=tokens,
            elapsed=elapsed,
            exit_code=completed.returncode,
            tool_events=tool_events,
        )
        if tool_events["total"] or tool_events["invalid_jsonl_lines"]:
            raise AdapterError("codex emitted a prohibited tool event or invalid JSONL; see the redacted model usage receipt")
        if completed.returncode != 0:
            diagnostic = completed.stderr.strip().splitlines()[-1] if completed.stderr.strip() else "no diagnostic"
            raise AdapterError(f"codex exec failed with exit {completed.returncode}: {diagnostic}")
        if not output_path.is_file() or output_path.is_symlink():
            raise AdapterError("codex did not produce a regular final result")
        result = require_object(json.loads(output_path.read_text(encoding="utf-8")), "model result")
        normalized = normalize(args.role, result, request, artifact_root, elapsed, tokens)
    except (AdapterError, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(normalized, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
