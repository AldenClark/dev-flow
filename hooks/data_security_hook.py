#!/usr/bin/env python3
"""Codex Hook adapter for bounded local confidentiality controls.

All user/tool payloads stay in memory. Hook output contains only redacted content
or fixed reasons and never includes a matched secret value.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = PLUGIN_ROOT / "skills" / "company-data-security" / "scripts"
sys.path.insert(0, str(ENGINE_DIR))

from data_security import (  # noqa: E402
    InspectionLimit,
    contains_high_confidence,
    finding_summary,
    redact_value,
    scan_text,
    scan_value,
    sensitive_path_categories,
)


MAX_HOOK_BYTES = 4_194_304
MAX_ADDITIONAL_CONTEXT_CHARS = 4_000
SAFE_BLOCK_REASON = (
    "A high-confidence secret or credential-store path was detected locally. "
    "The value was not forwarded. Continue with an environment variable, secret reference, or local redacted result."
)
SAFE_LIMIT_REASON = (
    "The payload exceeded the bounded local DLP inspection limit, so it was not forwarded. "
    "Narrow the source or process it locally before continuing."
)


def _emit(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _event_name_from_raw(raw: bytes) -> str:
    prefix = raw[:8192].decode("utf-8", errors="ignore")
    match = re.search(r'"hook_event_name"\s*:\s*"([A-Za-z]+)"', prefix)
    return match.group(1) if match else ""


def _pretool_deny(reason: str) -> dict[str, Any]:
    return {
        "systemMessage": "Local data-security policy blocked a sensitive tool input.",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
    }


def _prompt_block(reason: str) -> dict[str, Any]:
    return {"decision": "block", "reason": reason}


def _posttool_replace(reason: str, context: str | None = None) -> dict[str, Any]:
    additional = context or (
        "DLP-safe result: the original tool output was withheld locally because it could not be inspected inside the configured limit."
    )
    return {
        "continue": False,
        "stopReason": reason,
        "systemMessage": "Sensitive tool output was replaced locally before model processing.",
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": additional[:MAX_ADDITIONAL_CONTEXT_CHARS],
        },
    }


def _safe_failure(event_name: str, reason: str) -> int:
    if event_name == "UserPromptSubmit":
        _emit(_prompt_block(reason))
        return 0
    if event_name == "PreToolUse":
        _emit(_pretool_deny(reason))
        return 0
    if event_name == "PostToolUse":
        _emit(_posttool_replace(reason))
        return 0
    # Exit 2 is the only event-agnostic fail-closed path documented by Codex.
    sys.stderr.write(reason + "\n")
    return 2


def _read_event() -> tuple[dict[str, Any] | None, str, int | None]:
    raw = sys.stdin.buffer.read(MAX_HOOK_BYTES + 1)
    event_name = _event_name_from_raw(raw)
    if len(raw) > MAX_HOOK_BYTES:
        return None, event_name, _safe_failure(event_name, SAFE_LIMIT_REASON)
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None, event_name, _safe_failure(event_name, "Malformed Hook input was blocked locally.")
    if not isinstance(value, dict):
        return None, event_name, _safe_failure(event_name, "Invalid Hook input was blocked locally.")
    return value, str(value.get("hook_event_name") or event_name), None


def _handle_prompt(event: dict[str, Any]) -> int:
    prompt = event.get("prompt")
    if not isinstance(prompt, str):
        return _safe_failure("UserPromptSubmit", "Invalid prompt payload was blocked locally.")
    try:
        findings = scan_text(prompt, include_identifiers=False)
    except InspectionLimit:
        return _safe_failure("UserPromptSubmit", SAFE_LIMIT_REASON)
    if contains_high_confidence(findings):
        _emit(_prompt_block(SAFE_BLOCK_REASON))
    return 0


def _handle_pretool(event: dict[str, Any]) -> int:
    tool_input = event.get("tool_input", {})
    try:
        findings = scan_value(tool_input, include_identifiers=False)
        path_categories = sensitive_path_categories(tool_input)
    except InspectionLimit:
        return _safe_failure("PreToolUse", SAFE_LIMIT_REASON)
    if contains_high_confidence(findings) or path_categories:
        _emit(_pretool_deny(SAFE_BLOCK_REASON))
    return 0


def _redacted_context(redacted: Any, findings: list[Any]) -> str:
    summary = finding_summary(findings)
    serialized = json.dumps(redacted, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    prefix = (
        "DLP-safe tool result (the original result was withheld):\n"
        f"classes={json.dumps(summary['classes'], sort_keys=True)}; "
        f"categories={json.dumps(summary['categories'], sort_keys=True)}\n"
    )
    if len(prefix) + len(serialized) > MAX_ADDITIONAL_CONTEXT_CHARS:
        return prefix + "Redacted content exceeded the model-visible Hook limit; inspect a narrower local result."
    return prefix + serialized


def _handle_posttool(event: dict[str, Any]) -> int:
    response = event.get("tool_response")
    try:
        redacted, findings = redact_value(response)
    except InspectionLimit:
        return _safe_failure("PostToolUse", SAFE_LIMIT_REASON)
    if findings:
        _emit(_posttool_replace("Sensitive tool output was replaced locally.", _redacted_context(redacted, findings)))
    return 0


def main() -> int:
    event, event_name, early_code = _read_event()
    if early_code is not None:
        return early_code
    assert event is not None
    if event_name == "UserPromptSubmit":
        return _handle_prompt(event)
    if event_name == "PreToolUse":
        return _handle_pretool(event)
    if event_name == "PostToolUse":
        return _handle_posttool(event)
    return _safe_failure(event_name, "Unsupported data-security Hook event was blocked locally.")


if __name__ == "__main__":
    raise SystemExit(main())
