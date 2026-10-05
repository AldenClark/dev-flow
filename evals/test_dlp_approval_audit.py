#!/usr/bin/env python3
"""Focused synthetic-state audits for local DLP approval records."""

from __future__ import annotations

import concurrent.futures
from contextlib import contextmanager
import importlib.util
import json
import os
import re
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from typing import Any, Iterator
from unittest.mock import patch

from evals.test_data_security import hook_event, invoke_hook, synthetic_token


ROOT = Path(__file__).resolve().parents[1]
APPROVAL_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "dlp_approval.py"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


approval = _load_module("dlp_approval_audit_module", APPROVAL_PATH)


class ApprovalStateAuditTests(unittest.TestCase):
    def test_master_key_control_bytes_round_trip_without_text_translation(self) -> None:
        key = bytes([13, 10, 26, 10]) + bytes(range(28))
        self.assertEqual(len(key), 32)
        with self.local_state() as root:
            with patch.object(approval.secrets, "token_bytes", return_value=key):
                self.assertEqual(approval._master_key(), key)
            if os.name == "nt":
                descriptor = os.open(root / ("approval" + chr(46) + "key"), os.O_RDONLY | os.O_TEXT)
                try:
                    self.assertNotEqual(os.read(descriptor, 33), key, "native text-mode negative control must alter the control bytes")
                finally:
                    os.close(descriptor)
            self.assertEqual(approval._master_key(), key)
            request = approval.issue_request("UserPromptSubmit", b"binary-roundtrip", session_id="s", now=100)
            approval.consume_prompt_request(request.request_id, request.token, b"binary-roundtrip", session_id="s", now=101)
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(request.request_id, request.token, b"binary-roundtrip", session_id="s", now=102)

    def test_exact_prompt_confirmation_preserves_original_leading_whitespace(self) -> None:
        for leading in ("  ", "\n", "\t"):
            with tempfile.TemporaryDirectory() as directory:
                state = Path(directory)
                original = leading + "testing-only credential " + synthetic_token()
                code, out, err = invoke_hook(hook_event("UserPromptSubmit", prompt=original), state_dir=state)
                self.assertEqual((code, err), (0, ""))
                marker = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[^\]]+\]\]", out)
                self.assertIsNotNone(marker)
                retry = marker.group(0) + "\n" + original
                self.assertEqual(approval.parse_prompt_marker(retry)[2], original)
                code, out, err = invoke_hook(hook_event("UserPromptSubmit", prompt=retry), state_dir=state)
                self.assertEqual((code, err), (0, ""))
                self.assertNotIn("decision", json.loads(out))
                code, out, err = invoke_hook(hook_event("UserPromptSubmit", prompt=retry), state_dir=state)
                self.assertEqual(json.loads(out)["decision"], "block")

    def test_prompt_retry_rechecks_current_hard_policy_before_consuming(self) -> None:
        # Historical Hooks could issue this request before truncated-key
        # detection existed. Model the issued state, then run the current Hook.
        for hardened in (False, True):
            with self.subTest(hardened=hardened), self.local_state() as state:
                original = "synthetic test credential " + synthetic_token()
                if hardened:
                    original += "\n-----BEGIN PRIVATE KEY-----\n" + "Z" * 40
                event = hook_event("UserPromptSubmit", prompt=original)
                scope = approval.canonical_scope("UserPromptSubmit", event["cwd"], original)
                request = approval.issue_request("UserPromptSubmit", scope, session_id=event["session_id"])
                retry = request.prompt_marker + "\n" + original
                code, out, err = invoke_hook(hook_event("UserPromptSubmit", prompt=retry), state_dir=state)
                self.assertEqual((code, err), (0, ""))
                if hardened:
                    self.assertEqual(json.loads(out).get("decision"), "block")
                    self.assertTrue((state / "pending" / f"{request.request_id}.json").exists())
                    self.assertFalse((state / "used" / f"{request.request_id}.json").exists())
                else:
                    self.assertNotIn("decision", json.loads(out))
                    self.assertTrue((state / "used" / f"{request.request_id}.json").exists())

    @contextmanager
    def local_state(self) -> Iterator[Path]:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict(os.environ, {approval.STATE_DIR_ENV: directory}):
                yield Path(directory)

    def test_malformed_settings_schema_fails_closed_to_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "settings.json"
            settings.write_text(
                json.dumps({"schema": "unexpected", "mode": "personal"}),
                encoding="utf-8",
            )
            settings.chmod(0o600)
            with patch.dict(os.environ, {approval.STATE_DIR_ENV: directory}, clear=False):
                os.environ.pop(approval.MODE_ENV, None)
                self.assertEqual(approval.current_mode(), "strict")

    def test_unresolvable_state_root_is_typed_and_mode_fails_closed(self) -> None:
        with self.local_state():
            for failure in (OSError("unavailable"), RuntimeError("no home"), ValueError("invalid path")):
                with self.subTest(failure=type(failure).__name__), patch.object(Path, "expanduser", side_effect=failure):
                    with self.assertRaises(approval.StateUnavailable):
                        approval.issue_request("UserPromptSubmit", b"scope", session_id="s")
                    with patch.dict(os.environ):
                        os.environ.pop(approval.MODE_ENV, None)
                        self.assertEqual(approval.current_mode(), "strict")

    def test_ambiguous_settings_and_pending_json_are_rejected(self) -> None:
        with self.local_state() as root:
            settings = root / "settings.json"
            cases = (
                '{"schema":"dev-flow.dlp-settings.v1","mode":"strict","mode":"personal"}',
                '{"schema":"invalid","schema":"dev-flow.dlp-settings.v1","mode":"personal"}',
                '{"schema":"dev-flow.dlp-settings.v1","mode":"personal","extra":NaN}',
                '{"schema":"dev-flow.dlp-settings.v1","mode":"personal","extra":1e999}',
            )
            for text in cases:
                settings.write_text(text, encoding="utf-8")
                settings.chmod(0o600)
                with self.subTest(record=text), patch.dict(os.environ):
                    os.environ.pop(approval.MODE_ENV, None)
                    self.assertEqual(approval.current_mode(), "strict")
            request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
            path = root / "pending" / f"{request.request_id}.json"
            text = path.read_text(encoding="utf-8")
            path.write_text(text[:-1] + ',"expires_at":400}', encoding="utf-8")
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(request.request_id, request.token, b"scope", session_id="s", now=101)

    @unittest.skipIf(os.name == "nt", "named-user tilde expansion is a POSIX path behavior")
    def test_unexpandable_state_root_hook_still_denies(self) -> None:
        root = Path("~__dev_flow_missing_test_user__/dlp")
        event = hook_event("PreToolUse", tool_name="Bash", tool_input={"cmd": "testing-only " + synthetic_token()})
        code, out, err = invoke_hook(event, state_dir=root)
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(json.loads(out)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertNotIn(synthetic_token(), out)

    def test_malformed_expiry_is_rejected_as_approval_state(self) -> None:
        with self.local_state() as state_dir:
            request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
            path = state_dir / "pending" / f"{request.request_id}.json"
            record = json.loads(path.read_text(encoding="utf-8"))
            record["expires_at"] = []
            path.write_text(json.dumps(record), encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(
                    request.request_id,
                    request.token,
                    b"scope",
                    session_id="s",
                    now=101,
                )
            record["expires_at"] = request.expires_at
            record["kind"] = []
            path.write_text(json.dumps(record), encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(
                    request.request_id,
                    request.token,
                    b"scope",
                    session_id="s",
                    now=101,
                )

    def test_expiration_is_rejected_at_the_exact_deadline(self) -> None:
        with self.local_state() as state_dir:
            request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
            with self.assertRaisesRegex(approval.ApprovalError, "expired"):
                approval.consume_prompt_request(
                    request.request_id,
                    request.token,
                    b"scope",
                    session_id="s",
                    now=request.expires_at,
                )

    def test_session_and_scope_are_both_bound_to_tool_confirmation(self) -> None:
        with self.local_state():
            scope = b"exact tool name and payload"
            request = approval.issue_request("PreToolUse", scope, session_id="session-a", now=100)
            with self.assertRaisesRegex(approval.ApprovalError, "session changed"):
                approval.confirm_tool_request_from_prompt(
                    request.request_id,
                    request.token,
                    session_id="session-b",
                    now=101,
                )
            approval.confirm_tool_request_from_prompt(
                request.request_id,
                request.token,
                session_id="session-a",
                now=102,
            )
            self.assertIsNone(
                approval.find_approved_tool_request(
                    b"changed payload", session_id="session-a", now=103
                )
            )
            self.assertIsNone(
                approval.find_approved_tool_request(
                    scope, session_id="session-b", now=103
                )
            )
            self.assertEqual(
                approval.find_approved_tool_request(scope, session_id="session-a", now=103),
                request.request_id,
            )
            with self.assertRaisesRegex(approval.ApprovalError, "session changed"):
                approval.consume_tool_request(
                    request.request_id, scope, session_id="session-b", now=104
                )
            with self.assertRaisesRegex(approval.ApprovalError, "scope changed"):
                approval.consume_tool_request(
                    request.request_id, b"changed payload", session_id="session-a", now=104
                )
            approval.consume_tool_request(request.request_id, scope, session_id="session-a", now=104)
            with self.assertRaisesRegex(approval.ApprovalError, "already consumed"):
                approval.consume_tool_request(request.request_id, scope, session_id="session-a", now=105)

    def test_concurrent_issuance_cannot_exceed_pending_limit(self) -> None:
        with self.local_state() as state_dir:
            for index in range(approval.MAX_PENDING_REQUESTS - 1):
                approval.issue_request(
                    "UserPromptSubmit", f"existing-{index}".encode(), session_id="s", now=100
                )
            start = threading.Barrier(8)

            def issue(index: int) -> str:
                start.wait(timeout=10)
                try:
                    approval.issue_request(
                        "UserPromptSubmit", f"racing-{index}".encode(), session_id="s", now=101
                    )
                    return "issued"
                except approval.StateUnavailable:
                    return "bounded"

            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                outcomes = list(executor.map(issue, range(8)))
            pending = list((state_dir / "pending").iterdir())
            self.assertEqual(outcomes.count("issued"), 1)
            self.assertEqual(len(pending), approval.MAX_PENDING_REQUESTS)

    def test_held_state_lock_returns_bounded_failure(self) -> None:
        with self.local_state():
            root, _, _ = approval._paths()
            held = threading.Event()
            release = threading.Event()

            def hold_lock() -> None:
                with approval._state_lock(root):
                    held.set()
                    release.wait(timeout=3)

            holder = threading.Thread(target=hold_lock)
            holder.start()
            self.assertTrue(held.wait(timeout=2))
            started = time.monotonic()
            try:
                with self.assertRaises(approval.StateUnavailable):
                    with approval._state_lock(root):
                        self.fail("a second process-style lock acquisition must not pass")
                self.assertLess(time.monotonic() - started, 1.5)
            finally:
                release.set()
                holder.join(timeout=3)
            self.assertFalse(holder.is_alive())

    def test_consumed_record_capacity_recovers_after_expiry(self) -> None:
        with self.local_state() as state_dir:
            bounded = False
            for index in range(approval.MAX_PENDING_REQUESTS * 2 + 1):
                try:
                    request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
                    approval.consume_prompt_request(request.request_id, request.token, b"scope", session_id="s", now=101)
                except approval.StateUnavailable:
                    bounded = True
                    break
            self.assertTrue(bounded, "completed approvals must not overfill their cleanup capacity")
            self.assertLessEqual(len(list((state_dir / "used").iterdir())), approval.MAX_PENDING_REQUESTS * 2)
            fresh = approval.issue_request("UserPromptSubmit", b"fresh", session_id="s", now=1000)
            approval.consume_prompt_request(fresh.request_id, fresh.token, b"fresh", session_id="s", now=1001)
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(fresh.request_id, fresh.token, b"fresh", session_id="s", now=1002)

    def test_legacy_overflow_expiry_cleanup_makes_bounded_progress(self) -> None:
        for kind in ("pending", "used"):
            with self.subTest(directory=kind), self.local_state() as state_dir:
                request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
                original = state_dir / "pending" / f"{request.request_id}.json"
                record = json.loads(original.read_text(encoding="utf-8")) if kind == "pending" else {
                    "schema": "dev-flow.dlp-used.v1", "expires_at": 400,
                }
                original.unlink()
                directory = state_dir / kind
                total = approval.MAX_PENDING_REQUESTS * 2 + 1
                for index in range(total):
                    request_id = f"{index:024x}"
                    approval._exclusive_write(directory / f"{request_id}.json", json.dumps({
                        **record, "request_id": request_id,
                    }).encode())
                with self.assertRaises(approval.StateUnavailable):
                    approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=1000)
                self.assertLess(len(list(directory.iterdir())), total, "an expired oversized directory must make cleanup progress")
                fresh = approval.issue_request("UserPromptSubmit", b"fresh", session_id="s", now=1000)
                self.assertTrue(fresh.request_id)
                self.assertEqual(len(list(directory.iterdir())), 1 if kind == "pending" else 0)

    def test_concurrent_tool_confirmation_and_consumption_remain_one_shot(self) -> None:
        with self.local_state() as state_dir:
            scope = b"concurrent exact tool payload"
            request = approval.issue_request("PreToolUse", scope, session_id="s", now=100)

            def confirm(_: int) -> bool:
                try:
                    approval.confirm_tool_request_from_prompt(
                        request.request_id,
                        request.token,
                        session_id="s",
                        now=101,
                    )
                    return True
                except approval.ApprovalError:
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                confirmations = list(executor.map(confirm, range(2)))
            self.assertEqual(confirmations.count(True), 1)
            self.assertEqual(confirmations.count(False), 1)

            def consume(_: int) -> bool:
                try:
                    approval.consume_tool_request(request.request_id, scope, session_id="s", now=102)
                    return True
                except approval.ApprovalError:
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                consumptions = list(executor.map(consume, range(2)))
            self.assertEqual(consumptions.count(True), 1)
            self.assertEqual(consumptions.count(False), 1)
            self.assertEqual(list((state_dir / "pending").iterdir()), [])

    def test_consumed_stale_pending_never_shadows_a_fresh_tool_request(self) -> None:
        with self.local_state() as state_dir:
            scope = b"retry after pending removal failure"
            old = approval.issue_request("PreToolUse", scope, session_id="s", now=100)
            approval.confirm_tool_request_from_prompt(old.request_id, old.token, session_id="s", now=101)
            pending = (state_dir / "pending" / f"{old.request_id}.json").resolve()
            original_unlink = Path.unlink

            def fail_pending_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
                if path == pending:
                    raise PermissionError("synthetic pending removal failure")
                original_unlink(path, *args, **kwargs)

            with patch.object(Path, "unlink", fail_pending_unlink):
                approval.consume_tool_request(old.request_id, scope, session_id="s", now=102)
            self.assertTrue(pending.exists())
            with self.assertRaises(approval.ApprovalError):
                approval.consume_tool_request(old.request_id, scope, session_id="s", now=103)
            self.assertIsNone(approval.find_approved_tool_request(scope, session_id="s", now=103))
            fresh = approval.issue_request("PreToolUse", scope, session_id="s", now=103)
            approval.confirm_tool_request_from_prompt(fresh.request_id, fresh.token, session_id="s", now=104)
            self.assertEqual(approval.find_approved_tool_request(scope, session_id="s", now=105), fresh.request_id)
            approval.consume_tool_request(fresh.request_id, scope, session_id="s", now=105)
            with self.assertRaises(approval.ApprovalError):
                approval.consume_tool_request(fresh.request_id, scope, session_id="s", now=106)

    def test_atomic_replace_orphan_does_not_poison_recovered_confirmation(self) -> None:
        with self.local_state() as state_dir:
            scope = b"confirmation after staging failure"
            request = approval.issue_request("PreToolUse", scope, session_id="s", now=100)
            original_unlink = Path.unlink

            def fail_staging_unlink(path: Path, *args: Any, **kwargs: Any) -> None:
                if path.name.endswith(".tmp"):
                    raise PermissionError("synthetic staging cleanup failure")
                original_unlink(path, *args, **kwargs)

            with patch.object(approval.os, "replace", side_effect=PermissionError("synthetic replace failure")), patch.object(Path, "unlink", fail_staging_unlink):
                with self.assertRaises(approval.StateUnavailable):
                    approval.confirm_tool_request_from_prompt(request.request_id, request.token, session_id="s", now=101)
            self.assertEqual(len(list((state_dir / "pending").glob("*.tmp"))), 1)
            approval.confirm_tool_request_from_prompt(request.request_id, request.token, session_id="s", now=102)
            self.assertEqual(approval.find_approved_tool_request(scope, session_id="s", now=103), request.request_id)
            self.assertEqual(list((state_dir / "pending").glob("*.tmp")), [])
            approval.consume_tool_request(request.request_id, scope, session_id="s", now=104)

    def test_cleanup_discards_only_owned_staging_names_even_if_write_was_partial(self) -> None:
        with self.local_state() as state_dir:
            approval._paths()
            pending = state_dir / "pending"
            staging = pending / ("." + "a" * 24 + ".json." + "b" * 16 + ".tmp")
            approval._exclusive_write(staging, b'{"schema":')
            self.assertTrue(approval.issue_request("PreToolUse", b"scope", session_id="s", now=100))
            self.assertFalse(staging.exists())
            unknown = pending / "unowned.tmp"
            approval._exclusive_write(unknown, b"unknown")
            with self.assertRaises(approval.StateUnavailable):
                approval.issue_request("PreToolUse", b"other", session_id="s", now=101)
            self.assertTrue(unknown.exists())

    def test_record_read_rejects_large_files_without_reading_them(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            with path.open("wb") as stream:
                stream.truncate(4 * 1024 * 1024)
            path.chmod(0o600)
            original_read = approval.os.read
            bytes_read = 0

            def count_read(descriptor: int, size: int) -> bytes:
                nonlocal bytes_read
                value = original_read(descriptor, size)
                bytes_read += len(value)
                return value

            with patch.object(approval.os, "read", count_read):
                with self.assertRaisesRegex(approval.ApprovalError, "exceeds the local limit"):
                    approval._read_record(path)
            self.assertLessEqual(bytes_read, approval.MAX_STATE_FILE_BYTES + 1)

    def test_deeply_nested_record_is_rejected_as_approval_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested.json"
            path.write_text("[" * 2000 + "0" + "]" * 2000, encoding="utf-8")
            path.chmod(0o600)
            with self.assertRaises(approval.ApprovalError):
                approval._read_record(path)

    def test_oversized_master_key_is_bounded_and_rejected(self) -> None:
        with self.local_state():
            root, _, _ = approval._paths()
            path = root / ("approval" + chr(46) + "key")
            path.write_bytes(b"x" * (4 * 1024 * 1024))
            path.chmod(0o600)
            original_read = approval.os.read
            bytes_read = 0

            def count_read(descriptor: int, size: int) -> bytes:
                nonlocal bytes_read
                value = original_read(descriptor, size)
                bytes_read += len(value)
                return value

            with patch.object(approval.os, "read", count_read):
                with self.assertRaises(approval.StateUnavailable):
                    approval._master_key()
            self.assertLessEqual(bytes_read, 33)

    def test_expired_file_cleanup_failure_is_typed_and_stays_blocked(self) -> None:
        with self.local_state() as state_dir:
            request = approval.issue_request("UserPromptSubmit", b"scope", session_id="s", now=100)
            expired_path = (state_dir / "pending" / f"{request.request_id}.json").resolve()
            path_type = type(expired_path)
            original_unlink = path_type.unlink

            def fail_target(path: Path, *args: Any, **kwargs: Any) -> None:
                if path == expired_path:
                    raise PermissionError("synthetic cleanup failure")
                original_unlink(path, *args, **kwargs)

            with patch.object(path_type, "unlink", fail_target):
                with self.assertRaises(approval.StateUnavailable):
                    approval.consume_prompt_request(
                        request.request_id,
                        request.token,
                        b"scope",
                        session_id="s",
                        now=request.expires_at,
                    )

    def test_atomic_replace_cleanup_failure_keeps_typed_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "settings.json"
            path_type = type(target)
            with patch.object(approval.os, "replace", side_effect=OSError("synthetic replace failure")):
                with patch.object(path_type, "unlink", side_effect=PermissionError("synthetic cleanup failure")):
                    with self.assertRaises(approval.StateUnavailable):
                        approval._atomic_replace(target, b"{}")


if __name__ == "__main__":
    unittest.main()
