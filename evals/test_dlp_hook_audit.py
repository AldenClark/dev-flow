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
    process_cwd: Path | None = None,
) -> tuple[int, bytes, bytes]:
    raw = event if isinstance(event, bytes) else json.dumps(event, ensure_ascii=True).encode("utf-8")

    if state_dir is not None:
        return _run(raw, state_dir, mode, process_cwd)
    with tempfile.TemporaryDirectory() as directory:
        return _run(raw, Path(directory), mode, process_cwd)


def _run(raw: bytes, state_dir: Path, mode: str, process_cwd: Path | None = None) -> tuple[int, bytes, bytes]:
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
        cwd=process_cwd,
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

    def test_posttool_existing_redaction_marker_keeps_safe_reports_visible(self) -> None:
        field = "pass" + "word"
        for padding in ("", "ordinary report text\n" * 400):
            response = {"report": padding + field + ": [REDACTED_SECRET]"}
            event = _base_event("PostToolUse") | {
                "tool_name": "Bash",
                "tool_input": {},
                "tool_response": response,
            }
            with self.subTest(long_report=bool(padding)):
                self.assertEqual(_invoke(event), (0, b"", b""))

            token = _synthetic_token()
            event["tool_response"] = {"report": response, "nested": [{field: token}]}
            code, stdout, stderr = _invoke(event)
            self.assertEqual((code, stderr), (0, b""))
            result = json.loads(stdout)
            self.assertEqual(result["decision"], "block")
            self.assertFalse(result["continue"])
            self.assertNotIn(token, stdout.decode("utf-8"))

    def test_posttool_inline_documentation_reference_stays_visible(self) -> None:
        field = "pass" + "word"
        response = {"report": "ordinary report text\n" * 400 + field + ": [configuration reference](docs/configuration.md)"}
        event = _base_event("PostToolUse") | {
            "tool_name": "Bash",
            "tool_input": {},
            "tool_response": response,
        }
        self.assertEqual(_invoke(event), (0, b"", b""))

        token = _synthetic_token()
        event["tool_response"] = {"report": field + ": [" + token + "](docs/configuration.md)"}
        code, stdout, stderr = _invoke(event)
        self.assertEqual((code, stderr), (0, b""))
        result = json.loads(stdout)
        self.assertEqual(result["decision"], "block")
        self.assertFalse(result["continue"])
        self.assertNotIn(token, stdout.decode("utf-8"))

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


class HookCwdCompatibilityTests(unittest.TestCase):
    def call(self, event: dict[str, Any], state: Path, process_cwd: Path) -> dict[str, Any]:
        code, stdout, stderr = _invoke(event, state_dir=state, process_cwd=process_cwd)
        self.assertEqual((code, stderr), (0, b""))
        self.assertNotIn(_synthetic_token().encode(), stdout)
        return json.loads(stdout) if stdout else {}

    def pending(self, cwd: Path, state: Path, host: Path) -> tuple[dict[str, Any], str]:
        event = _base_event("PreToolUse") | {
            "cwd": str(cwd), "turn_id": "turn-1", "tool_use_id": "original-command",
            "tool_name": "Bash", "tool_input": {"command": "echo synthetic test " + _synthetic_token()},
        }
        result = self.call(event, state, host)
        self.assertEqual(result["hookSpecificOutput"]["permissionDecision"], "deny")
        marker = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[^\]]+\]\]", result["hookSpecificOutput"]["permissionDecisionReason"])
        self.assertIsNotNone(marker)
        return event, marker.group(0)

    def confirm(self, marker: str, cwd: Path, state: Path, host: Path) -> None:
        # UserPromptSubmit retains the host directory, not the command workdir.
        result = self.call(_base_event("UserPromptSubmit") | {
            "cwd": str(cwd), "turn_id": "turn-2", "prompt": marker,
        }, state, host)
        self.assertNotIn("decision", result)
        self.assertIn("confirmed", result["hookSpecificOutput"]["additionalContext"])

    def test_tool_confirmation_is_cwd_bound_and_one_shot_across_turns(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            host, first, other = (root / name for name in ("host", "first", "other"))
            for path in (host, first, other):
                path.mkdir()
            state = root / "state"
            event, marker = self.pending(first, state, host)
            self.confirm(marker, host, state, other)
            wrong = self.call(event | {"cwd": str(other)}, state, host)
            self.assertEqual(wrong["hookSpecificOutput"]["permissionDecision"], "deny")
            retry = event | {"turn_id": "turn-3", "tool_use_id": "retry-command"}
            allowed = self.call(retry, state, other)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
            self.assertIn("already consumed", allowed["hookSpecificOutput"]["additionalContext"])
            replay = self.call(retry, state, host)
            self.assertEqual(replay["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(len(list((state / "used").glob("*.json"))), 1)

    def test_relative_retry_cannot_use_hook_process_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            event, marker = self.pending(root, root / "state", root)
            self.confirm(marker, root, root / "state", root)
            rejected = self.call(event | {"cwd": "."}, root / "state", root)
            self.assertEqual(rejected.get("hookSpecificOutput", {}).get("permissionDecision"), "deny")
            allowed = self.call(event, root / "state", root)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])

    def test_invalid_cwd_cannot_confirm_pending_tool_request(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for index, cwd in enumerate((None, "", ".", "child", "file:///synthetic", "ssh://host.invalid/repo", str(root) + "\0")):
                with self.subTest(cwd=cwd):
                    state = root / f"state-{index}"
                    event, marker = self.pending(root, state, root)
                    result = self.call(_base_event("UserPromptSubmit") | {"cwd": cwd, "prompt": marker}, state, root)
                    self.assertEqual(result.get("decision"), "block")
                    self.confirm(marker, root, state, root)
                    allowed = self.call(event, state, root)
                    self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])

    def test_invalid_cwd_blocks_all_supported_events_without_creating_state(self) -> None:
        payloads = {
            "UserPromptSubmit": {"prompt": "ordinary"},
            "PreToolUse": {"tool_name": "Bash", "tool_input": {"command": "echo ordinary"}},
            "PostToolUse": {"tool_name": "Bash", "tool_response": "ordinary"},
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            state = root / "state"
            for name, fields in payloads.items():
                for cwd in (None, "", ".", "../other", "file:///synthetic", "ssh://host.invalid/repo", str(root) + "\0"):
                    with self.subTest(event=name, cwd=cwd):
                        event = _base_event(name) | fields
                        if cwd is None:
                            del event["cwd"]
                        else:
                            event["cwd"] = cwd
                        result = self.call(event, state, root)
                        if name == "PreToolUse":
                            self.assertEqual(result.get("hookSpecificOutput", {}).get("permissionDecision"), "deny")
                        else:
                            self.assertEqual(result.get("decision"), "block")
            self.assertFalse(state.exists())

    def test_delayed_bash_result_keeps_original_cwd_without_consuming_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            original, later = root / "original", root / "later-turn"
            original.mkdir()
            later.mkdir()
            state = root / "state"
            event, marker = self.pending(original, state, root)
            self.confirm(marker, later, state, later)
            # PR57203: write_stdin completion reports the original Bash input,
            # tool_use_id and execution cwd; only turn/process cwd have changed.
            post = event | {"hook_event_name": "PostToolUse", "turn_id": "later-turn", "tool_response": _synthetic_token()}
            result = self.call(post, state, later)
            self.assertEqual(result["decision"], "block")
            self.assertRegex(result["hookSpecificOutput"]["additionalContext"], r"\{\{DLP:SECRET:[0-9a-f]{8}\}\}")
            self.assertEqual(len(list((state / "used").glob("*.json"))), 0)
            allowed = self.call(event | {"turn_id": "next-turn"}, state, later)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])

    def test_host_cwd_is_not_inferred_from_remote_payload_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            state = root / "state"
            # MCP input retains arguments; a remote workdir is payload, never a
            # replacement for top-level host cwd. Bash exposes command only.
            event = _base_event("PreToolUse") | {
                "cwd": str(root), "tool_name": "mcp__synthetic__remote",
                "tool_input": {"command": "echo synthetic test " + _synthetic_token(), "workdir": "remote/relative"},
            }
            denied = self.call(event, state, root)
            marker = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[^\]]+\]\]", denied["hookSpecificOutput"]["permissionDecisionReason"])
            self.assertIsNotNone(marker)
            self.confirm(marker.group(0), root, state, root)
            altered = event | {"tool_input": event["tool_input"] | {"workdir": "remote/other"}}
            self.assertEqual(self.call(altered, state, root)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertEqual(self.call(event | {"cwd": "ssh://host.invalid/repo"}, state, root)["hookSpecificOutput"]["permissionDecision"], "deny")
            allowed = self.call(event, state, root)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])


if __name__ == "__main__":
    unittest.main()
