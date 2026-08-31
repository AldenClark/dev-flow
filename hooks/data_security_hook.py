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
from dlp_approval import (  # noqa: E402
    ApprovalError,
    StateUnavailable,
    canonical_scope,
    confirm_tool_request_from_prompt,
    consume_prompt_request,
    consume_tool_request,
    current_mode,
    find_approved_tool_request,
    issue_request,
    parse_prompt_marker,
)
from dlp_policy import (  # noqa: E402
    declares_test_data,
    primary_category,
    requires_hard_block,
    safe_summary,
    storage_advice,
)


MAX_HOOK_BYTES = 4_194_304
MAX_ADDITIONAL_CONTEXT_CHARS = 4_000
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


def _prompt_allow_context(context: str) -> dict[str, Any]:
    return {
        "systemMessage": "A one-shot personal DLP confirmation was consumed.",
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": context,
        },
    }


def _pretool_allow_context(context: str) -> dict[str, Any]:
    return {
        "systemMessage": "A one-shot personal DLP confirmation was consumed.",
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "additionalContext": context,
        },
    }


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


def _storage_text(category: str) -> str:
    advice = storage_advice(category)
    return (
        f"Recommended reference: ${advice.env_name}. Safe storage: {advice.save_command} "
        f"Agent use: {advice.use_pattern}. {advice.caution}"
    )


def _hard_block_reason(findings: list[Any], path_categories: list[str], *, status: str) -> str:
    category = primary_category(findings)
    summary = safe_summary(findings, path_categories)
    return (
        f"DLP blocked {summary}; {status}. The value was not echoed. "
        f"{_storage_text(category)} This event requires replacement with a reference; it cannot use a one-shot override."
    )


def _prompt_confirmation_reason(findings: list[Any], request: Any) -> str:
    category = primary_category(findings)
    return (
        f"Possible test {safe_summary(findings)} detected locally; the prompt was not forwarded. "
        f"{_storage_text(category)} Preferred: replace the value with ${storage_advice(category).env_name}. "
        f"To disclose this exact test value once, prefix {request.prompt_marker} and retry within 5 minutes. "
        "Any content change requires a new confirmation. The UI may already have created an empty task shell."
    )


def _tool_confirmation_reason(findings: list[Any], request: Any) -> str:
    category = primary_category(findings)
    return (
        f"Possible {safe_summary(findings)} detected locally; the tool was not executed. "
        f"{_storage_text(category)} Preferred: retry with ${storage_advice(category).env_name}. "
        f"To confirm this exact tool call, ask the user to submit exactly {request.prompt_marker} "
        "as the next message within 5 minutes. No local Agent command can approve it. "
        "After that UserPromptSubmit event, retry the unchanged tool input once."
    )


def _handle_prompt(event: dict[str, Any]) -> int:
    prompt = event.get("prompt")
    if not isinstance(prompt, str):
        return _safe_failure("UserPromptSubmit", "Invalid prompt payload was blocked locally.")
    request_id, token, inspected_prompt = parse_prompt_marker(prompt)
    session_id = event.get("session_id")
    if request_id is not None and token is not None and not inspected_prompt.strip():
        if current_mode() == "strict":
            _emit(_prompt_block("Strict DLP mode does not accept one-shot tool confirmations."))
            return 0
        try:
            confirm_tool_request_from_prompt(
                request_id,
                token,
                session_id=session_id,
            )
        except (ApprovalError, StateUnavailable) as exc:
            _emit(_prompt_block(f"The one-shot tool confirmation was rejected: {exc}."))
            return 0
        _emit(
            _prompt_allow_context(
                "A UserPromptSubmit event confirmed one exact pending tool input. Retry only that unchanged tool call; approval is session-bound, expiring, and consumed by the retry."
            )
        )
        return 0
    try:
        findings = scan_text(inspected_prompt, include_identifiers=False)
    except InspectionLimit:
        return _safe_failure("UserPromptSubmit", SAFE_LIMIT_REASON)
    high_confidence = contains_high_confidence(findings)
    if request_id is not None and not high_confidence:
        _emit(_prompt_block("The one-shot DLP marker did not match a confirmable secret. Remove it and retry."))
        return 0
    if not high_confidence:
        return 0
    if current_mode() == "strict":
        _emit(_prompt_block(_hard_block_reason(findings, [], status="the prompt was not forwarded")))
        return 0
    if request_id is not None and token is not None:
        try:
            scope = canonical_scope("UserPromptSubmit", str(event.get("cwd") or ""), inspected_prompt)
            consume_prompt_request(
                request_id,
                token,
                scope,
                session_id=session_id,
            )
        except (ApprovalError, StateUnavailable) as exc:
            _emit(_prompt_block(f"The one-shot DLP confirmation was rejected: {exc}. Remove the marker and retry."))
            return 0
        _emit(
            _prompt_allow_context(
                "The user explicitly confirmed this exact test-secret disclosure once. The confirmation is already consumed; do not reuse or repeat the value."
            )
        )
        return 0
    if requires_hard_block(findings) or not declares_test_data(inspected_prompt):
        _emit(_prompt_block(_hard_block_reason(findings, [], status="the prompt was not forwarded")))
        return 0
    try:
        scope = canonical_scope("UserPromptSubmit", str(event.get("cwd") or ""), inspected_prompt)
        request = issue_request(
            "UserPromptSubmit",
            scope,
            session_id=session_id,
        )
    except (ApprovalError, StateUnavailable):
        _emit(_prompt_block(_hard_block_reason(findings, [], status="local confirmation state was unavailable")))
        return 0
    _emit(_prompt_block(_prompt_confirmation_reason(findings, request)))
    return 0


def _handle_pretool(event: dict[str, Any]) -> int:
    tool_input = event.get("tool_input", {})
    try:
        findings = scan_value(tool_input, include_identifiers=False)
        path_categories = sensitive_path_categories(tool_input)
    except InspectionLimit:
        return _safe_failure("PreToolUse", SAFE_LIMIT_REASON)
    if not contains_high_confidence(findings) and not path_categories:
        return 0
    if current_mode() == "strict" or requires_hard_block(findings, path_categories):
        _emit(_pretool_deny(_hard_block_reason(findings, path_categories, status="the tool was not executed")))
        return 0
    if not declares_test_data(tool_input):
        _emit(
            _pretool_deny(
                _hard_block_reason(
                    findings,
                    path_categories,
                    status="the tool input was not explicitly declared as test data and was not executed",
                )
            )
        )
        return 0
    session_id = event.get("session_id")
    try:
        scope = canonical_scope(
            "PreToolUse",
            str(event.get("cwd") or ""),
            tool_input,
            tool_name=str(event.get("tool_name") or ""),
        )
        approved_request = find_approved_tool_request(scope, session_id=session_id)
        if approved_request is not None:
            consume_tool_request(approved_request, scope, session_id=session_id)
            _emit(
                _pretool_allow_context(
                    "The user explicitly confirmed this exact tool input once. The authorization is already consumed; do not reuse or print the value."
                )
            )
            return 0
        request = issue_request("PreToolUse", scope, session_id=session_id)
    except (ApprovalError, StateUnavailable):
        _emit(_pretool_deny(_hard_block_reason(findings, path_categories, status="local confirmation state was unavailable")))
        return 0
    _emit(_pretool_deny(_tool_confirmation_reason(findings, request)))
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
