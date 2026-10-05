#!/usr/bin/env python3
"""Focused Hook protocol and malformed-input regression tests."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "data_security_hook.py"
ENGINE_DIR = ROOT / "skills" / "company-data-security" / "scripts"
sys.path.insert(0, str(ENGINE_DIR))

from dlp_approval import MODE_ENV, STATE_DIR_ENV  # noqa: E402


def _synthetic_token() -> str:
    return "gh" + "p_" + "A" * 36


def _base_event(event_name: str) -> dict[str, Any]:
    return {
        "session_id": "synthetic-session",
        "cwd": str(ROOT),
        "hook_event_name": event_name,
    }


def _invoke(
    event: dict[str, Any] | bytes,
    *,
    state_dir: Path | None = None,
    mode: str = "personal",
) -> tuple[int, bytes, bytes]:
    raw = event if isinstance(event, bytes) else json.dumps(event, ensure_ascii=True).encode("utf-8")

    if state_dir is not None:
        return _run(raw, state_dir, mode)
    with tempfile.TemporaryDirectory() as directory:
        return _run(raw, Path(directory), mode)


def _run(raw: bytes, state_dir: Path, mode: str) -> tuple[int, bytes, bytes]:
    environment = os.environ.copy()
    environment[STATE_DIR_ENV] = str(state_dir)
    environment[MODE_ENV] = mode
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=raw,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=False,
        env=environment,
    )
    return result.returncode, result.stdout, result.stderr


class HookPayloadAuditTests(unittest.TestCase):
    def test_pretool_requires_payload_presence_and_accepts_any_json_value(self) -> None:
        cases = [
            {"tool_name": "Bash"},
            {"tool_input": {}},
        ]
        for fields in cases:
            event = _base_event("PreToolUse") | fields
            with self.subTest(fields=fields):
                code, stdout, stderr = _invoke(event)
                self.assertEqual((code, stderr), (0, b""))
                result = json.loads(stdout)
                self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "PreToolUse")
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

        for tool_input in (None, [], "ordinary", 4, True, {}):
            event = _base_event("PreToolUse") | {"tool_name": "Bash", "tool_input": tool_input}
            with self.subTest(tool_input_type=type(tool_input).__name__):
                self.assertEqual(_invoke(event), (0, b"", b""))

        token = _synthetic_token()
        for tool_input in (token, ["nested", token], {"nested": [token]}):
            event = _base_event("PreToolUse") | {"tool_name": "Bash", "tool_input": tool_input}
            with self.subTest(secret_payload_type=type(tool_input).__name__):
                code, stdout, stderr = _invoke(event)
                self.assertEqual((code, stderr), (0, b""))
                result = json.loads(stdout)
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
                self.assertNotIn(token.encode("ascii"), stdout)

        for metadata in (
            {"session_id": {"wrong": "type"}},
            {"session_id": "s" * 257},
            {"session_id": "invalid\nsession"},
            {"cwd": None},
            {"cwd": []},
        ):
            invalid_metadata = _base_event("PreToolUse") | {
                "tool_name": "Bash",
                "tool_input": {},
            } | metadata
            with self.subTest(metadata=metadata):
                code, stdout, stderr = _invoke(invalid_metadata)
                self.assertEqual((code, stderr), (0, b""))
                self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_prompt_payload_must_be_a_string(self) -> None:
        for fields in ({}, {"prompt": None}, {"prompt": ["ordinary"]}):
            event = _base_event("UserPromptSubmit") | fields
            with self.subTest(fields=fields):
                code, stdout, stderr = _invoke(event)
                self.assertEqual((code, stderr), (0, b""))
                self.assertEqual(json.loads(stdout)["decision"], "block")

    def test_posttool_requires_response_field_but_accepts_explicit_null(self) -> None:
        event = _base_event("PostToolUse") | {"tool_name": "Bash", "tool_input": {}}
        code, stdout, stderr = _invoke(event)
        self.assertEqual((code, stderr), (0, b""))
        result = json.loads(stdout)
        self.assertEqual(result["decision"], "block")
        self.assertIn("reason", result)
        self.assertFalse(result["continue"])
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "PostToolUse")
        self.assertLess(len(stdout), 1_000)

        explicit_null = event | {"tool_response": None}
        code, stdout, stderr = _invoke(explicit_null)
        self.assertEqual((code, stdout, stderr), (0, b"", b""))

    def test_nonfinite_and_duplicate_json_are_rejected_with_event_failure(self) -> None:
        prefix = (
            b'{"hook_event_name":"PreToolUse","session_id":"synthetic-session",'
            b'"cwd":"/synthetic","tool_name":"Bash","tool_input":{"value":'
        )
        for number in (b"NaN", b"Infinity", b"-Infinity", b"1e999"):
            with self.subTest(number=number):
                code, stdout, stderr = _invoke(prefix + number + b"}}")
                self.assertEqual((code, stderr), (0, b""))
                result = json.loads(stdout)
                self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

        duplicate = (
            b'{"hook_event_name":"PreToolUse","session_id":"synthetic-session",'
            b'"cwd":"/synthetic","tool_name":"Bash",'
            b'"tool_input":{"value":"safe","value":"also-safe"}}'
        )
        code, stdout, stderr = _invoke(duplicate)
        self.assertEqual((code, stderr), (0, b""))
        self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_malformed_nested_event_name_cannot_redirect_failure_type(self) -> None:
        raw = (
            b'{"metadata":{"hook_event_name":"PostToolUse"},'
            b'"hook_event_name":"PreToolUse","session_id":"synthetic-session",'
            b'"cwd":"/synthetic","tool_name":"Bash","tool_input":{"value":NaN}}'
        )
        code, stdout, stderr = _invoke(raw)
        self.assertEqual((code, stderr), (0, b""))
        result = json.loads(stdout)
        self.assertEqual(result["hookSpecificOutput"]["hookEventName"], "PreToolUse")
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_posttool_redaction_keeps_model_visible_output_bounded(self) -> None:
        token = _synthetic_token()
        event = _base_event("PostToolUse") | {
            "tool_name": "Bash",
            "tool_input": {},
            "tool_response": {"result": "x" * 8_000 + " " + token},
        }
        code, stdout, stderr = _invoke(event)
        self.assertEqual((code, stderr), (0, b""))
        result = json.loads(stdout)
        self.assertEqual(result["decision"], "block")
        context = result["hookSpecificOutput"]["additionalContext"]
        self.assertFalse(result["continue"])
        self.assertNotIn(token, stdout.decode("utf-8"))
        self.assertNotIn("x" * 100, context)
        self.assertLess(len(context), 1_000)
        self.assertLess(len(stdout), 2_000)

    def test_unicode_and_deep_json_fail_closed_without_tracebacks(self) -> None:
        token = _synthetic_token()
        invalid_unicode = _base_event("PostToolUse") | {
            "tool_response": "client_secret=S3cret-" + "G7h9" * 6 + token + "\ud800",
        }
        code, stdout, stderr = _invoke(invalid_unicode)
        self.assertEqual((code, stderr), (0, b""))
        self.assertEqual(json.loads(stdout)["decision"], "block")
        self.assertFalse(json.loads(stdout)["continue"])
        self.assertNotIn(token.encode("ascii"), stdout)
        self.assertLess(len(stdout), 1_000)

        nested: Any = "ordinary"
        for _ in range(20):
            nested = [nested]
        deep_event = _base_event("PostToolUse") | {"tool_response": nested}
        code, stdout, stderr = _invoke(deep_event)
        self.assertEqual((code, stderr), (0, b""))
        self.assertEqual(json.loads(stdout)["decision"], "block")
        self.assertFalse(json.loads(stdout)["continue"])

        parser_deep = (
            b'{"hook_event_name":"PostToolUse","session_id":"synthetic-session",'
            b'"cwd":"/synthetic","tool_response":'
            + b"[" * 1_500
            + b'"ordinary"'
            + b"]" * 1_500
            + b"}"
        )
        code, stdout, stderr = _invoke(parser_deep)
        self.assertEqual((code, stderr), (0, b""))
        self.assertEqual(json.loads(stdout)["decision"], "block")
        self.assertFalse(json.loads(stdout)["continue"])
        self.assertLess(len(stdout), 1_000)

    def test_one_shot_tool_confirmation_still_requires_host_prompt_and_exact_retry(self) -> None:
        token = _synthetic_token()
        tool_event = _base_event("PreToolUse") | {
            "tool_name": "Bash",
            "tool_input": {"command": "echo synthetic test " + token},
        }
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            code, stdout, stderr = _invoke(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, b""))
            denied = json.loads(stdout)
            reason = denied["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            marker_match = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[0-9a-f]{24}:[A-Za-z0-9_-]{24,96}\]\]", reason)
            self.assertIsNotNone(marker_match)
            marker = marker_match.group(0)

            prompt_event = _base_event("UserPromptSubmit") | {"prompt": marker}
            code, stdout, stderr = _invoke(prompt_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, b""))
            confirmed = json.loads(stdout)
            self.assertNotIn("decision", confirmed)
            self.assertIn("UserPromptSubmit event confirmed", confirmed["hookSpecificOutput"]["additionalContext"])

            code, stdout, stderr = _invoke(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, b""))
            allowed = json.loads(stdout)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
            self.assertIn("already consumed", allowed["hookSpecificOutput"]["additionalContext"])

            code, stdout, stderr = _invoke(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, b""))
            replay = json.loads(stdout)
            self.assertEqual(replay["hookSpecificOutput"]["permissionDecision"], "deny")


if __name__ == "__main__":
    unittest.main()
