#!/usr/bin/env python3
"""Synthetic blue/red tests for the packaged confidentiality controls."""

from __future__ import annotations

import base64
import concurrent.futures
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "data_security.py"
DOCTOR_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "doctor.py"
HOOK_PATH = ROOT / "hooks" / "data_security_hook.py"
APPROVAL_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "dlp_approval.py"
POLICY_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "dlp_policy.py"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dlp = _load_module("data_security_test_module", ENGINE_PATH)
doctor = _load_module("data_security_doctor_test_module", DOCTOR_PATH)
approval = _load_module("dlp_approval_test_module", APPROVAL_PATH)
policy = _load_module("dlp_policy_test_module", POLICY_PATH)


def synthetic_token(kind: str = "github") -> str:
    if kind == "github":
        return "gh" + "p_" + "A" * 36
    if kind == "openai":
        return "s" + "k-proj-" + "B" * 28
    if kind == "aws":
        return "AK" + "IA" + "C" * 16
    if kind == "slack":
        return "xo" + "xb-" + "D" * 24
    if kind == "jwt":
        return "eyJ" + "a" * 12 + "." + "b" * 12 + "." + "c" * 12
    raise ValueError(kind)


def invoke_hook(
    event: dict[str, Any] | bytes,
    *,
    timeout: int = 10,
    state_dir: Path | None = None,
    mode: str = "personal",
) -> tuple[int, str, str]:
    payload = event if isinstance(event, bytes) else json.dumps(event, ensure_ascii=False).encode("utf-8")

    def run(directory: Path) -> tuple[int, str, str]:
        environment = os.environ.copy()
        environment[approval.STATE_DIR_ENV] = str(directory)
        environment[approval.MODE_ENV] = mode
        result = subprocess.run(
            [sys.executable, str(HOOK_PATH)],
            input=payload,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
            env=environment,
        )
        return result.returncode, result.stdout.decode("utf-8"), result.stderr.decode("utf-8")

    if state_dir is not None:
        return run(state_dir)
    with tempfile.TemporaryDirectory() as directory:
        return run(Path(directory))


def hook_event(name: str, **fields: Any) -> dict[str, Any]:
    return {
        "session_id": "synthetic-session",
        "turn_id": "synthetic-turn",
        "cwd": str(ROOT),
        "hook_event_name": name,
        **fields,
    }


class EngineBlueTests(unittest.TestCase):
    def test_high_confidence_detector_families(self) -> None:
        private_key = "-----BEGIN PRIVATE KEY-----\n" + "Z" * 40 + "\n-----END PRIVATE KEY-----"
        cases = {
            "private": private_key,
            "aws": synthetic_token("aws"),
            "github": synthetic_token("github"),
            "openai": synthetic_token("openai"),
            "slack": synthetic_token("slack"),
            "jwt": synthetic_token("jwt"),
            "authorization": "Authorization: Bearer " + "E" * 24,
            "url": "postgres://user:" + "F" * 20 + "@db.invalid/main",
            "assignment": "client_secret=S3cret-" + "G7h9" * 6,
        }
        for name, value in cases.items():
            with self.subTest(name=name):
                findings = dlp.scan_text(value, include_identifiers=False)
                self.assertTrue(dlp.contains_high_confidence(findings), f"{name} detector did not fire")

    def test_placeholders_and_public_decoys_are_allowed(self) -> None:
        decoys = [
            "client_secret=${CLIENT_SECRET}",
            "password=<redacted>",
            "api_key=YOUR_API_KEY",
            "password=notsecret",
            "use $DATABASE_URL without expanding it",
            "ordinary internal roadmap text",
            "the prefix sk- is discussed without a value",
            "read .env.example for documented key names",
        ]
        for text in decoys:
            with self.subTest(text=text):
                self.assertFalse(dlp.contains_high_confidence(dlp.scan_text(text, include_identifiers=False)))

    def test_identifier_pseudonyms_preserve_relationships(self) -> None:
        source = "Owner person@corp.invalid, reviewer person@corp.invalid, phone +1 202 555 0179"
        redacted, findings = dlp.redact_text(source, salt=b"synthetic-test-salt-material")
        labels = [item for item in redacted.split() if "DLP:EMAIL" in item]
        self.assertEqual(len(labels), 2)
        self.assertEqual(labels[0].rstrip(","), labels[1].rstrip(","))
        self.assertFalse("person@corp.invalid" in redacted, "email remained in redacted output")
        self.assertTrue(any(item.category == "phone" for item in findings))

    def test_scan_summary_never_contains_value(self) -> None:
        token = synthetic_token()
        summary = json.dumps(dlp.finding_summary(dlp.scan_text(token)), sort_keys=True)
        self.assertFalse(token in summary, "finding metadata leaked the synthetic token")
        self.assertIn("access_token", summary)

    def test_nested_redaction_keeps_shape(self) -> None:
        token = synthetic_token("openai")
        value = {"items": [{"credential": token, "state": "failed"}], "count": 1}
        redacted, findings = dlp.redact_value(value, salt=b"synthetic-test-salt-material")
        self.assertEqual(redacted["items"][0]["state"], "failed")
        self.assertEqual(redacted["count"], 1)
        self.assertTrue(redacted["items"][0]["credential"].startswith("{{DLP:SECRET:"))
        self.assertTrue(dlp.contains_high_confidence(findings))

    def test_finding_paths_never_copy_object_keys(self) -> None:
        token = synthetic_token("github")
        findings = dlp.scan_value({token: {"customer-name": token}})
        self.assertTrue(findings)
        self.assertTrue(all(token not in item.path for item in findings))
        self.assertTrue(all("customer-name" not in item.path for item in findings))

    def test_sensitive_path_detection_has_safe_template_exclusion(self) -> None:
        self.assertEqual(dlp.sensitive_path_categories({"command": "cat /tmp/.aws/credentials"}), ["credential_store_path"])
        self.assertEqual(dlp.sensitive_path_categories({"path": "/workspace/.env.example"}), [])

    def test_dictionary_keys_are_scanned_and_redacted(self) -> None:
        token = synthetic_token("github")
        redacted, findings = dlp.redact_value({token: "state"}, salt=b"synthetic-test-salt-material")
        redacted_key = next(iter(redacted))
        self.assertTrue(redacted_key.startswith("{{DLP:SECRET:"))
        self.assertTrue(dlp.contains_high_confidence(findings))
        self.assertFalse(token in json.dumps(redacted), "secret remained in a redacted object key")

    def test_size_and_depth_limits_are_explicit(self) -> None:
        with self.assertRaises(dlp.InspectionLimit):
            dlp.scan_text("a" * (dlp.MAX_TEXT_BYTES + 1))
        nested: Any = "leaf"
        for _ in range(dlp.MAX_DEPTH + 2):
            nested = [nested]
        with self.assertRaises(dlp.InspectionLimit):
            dlp.scan_value(nested)


class EngineRedTests(unittest.TestCase):
    def test_base64_wrapped_secret_is_detected_and_wholly_redacted(self) -> None:
        token = synthetic_token("github")
        wrapped = base64.urlsafe_b64encode(("value=" + token).encode("utf-8")).decode("ascii")
        findings = dlp.scan_text(wrapped, include_identifiers=False)
        self.assertTrue(any(item.rule_id == "C4-ENCODED-SECRET" for item in findings))
        redacted, _ = dlp.redact_text(wrapped)
        self.assertTrue(redacted.startswith("{{DLP:SECRET:"))
        self.assertFalse(token in redacted, "decoded token leaked after redaction")

    def test_encoded_public_decoy_is_not_flagged(self) -> None:
        wrapped = base64.urlsafe_b64encode(b"public documentation without credentials").decode("ascii")
        self.assertFalse(dlp.scan_text(wrapped, include_identifiers=False))

    def test_nfkc_obfuscated_authorization_header_is_detected(self) -> None:
        text = "Authorization\uff1a Bearer " + "Q7r-" * 8
        findings = dlp.scan_text(text, include_identifiers=False)
        self.assertTrue(any(item.rule_id == "C4-NORMALIZED-SECRET" for item in findings))

    def test_finding_cap_is_enforced(self) -> None:
        many = " ".join(synthetic_token("github")[:-1] + chr(65 + index % 20) for index in range(dlp.MAX_FINDINGS + 20))
        self.assertEqual(len(dlp.scan_text(many, include_identifiers=False)), dlp.MAX_FINDINGS)


class ApprovalStateTests(unittest.TestCase):
    def test_prompt_approval_is_scoped_one_shot_and_never_persists_raw_input(self) -> None:
        sample = synthetic_token("github")
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {approval.STATE_DIR_ENV: directory, approval.MODE_ENV: "personal"},
        ):
            scope = approval.canonical_scope("UserPromptSubmit", str(ROOT), "测试密钥 " + sample)
            request = approval.issue_request(
                "UserPromptSubmit", scope, session_id="session-a", now=100
            )
            persisted = b"".join(path.read_bytes() for path in Path(directory).rglob("*") if path.is_file())
            self.assertNotIn(sample.encode("utf-8"), persisted)
            approval.consume_prompt_request(
                request.request_id, request.token, scope, session_id="session-a", now=101
            )
            with self.assertRaises(approval.ApprovalError):
                approval.consume_prompt_request(
                    request.request_id, request.token, scope, session_id="session-a", now=102
                )

    def test_changed_or_expired_prompt_scope_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {approval.STATE_DIR_ENV: directory, approval.MODE_ENV: "personal"},
        ):
            scope = approval.canonical_scope("UserPromptSubmit", str(ROOT), "synthetic scope")
            request = approval.issue_request(
                "UserPromptSubmit", scope, session_id="session-a", now=100
            )
            changed = approval.canonical_scope("UserPromptSubmit", str(ROOT), "synthetic scope changed")
            with self.assertRaisesRegex(approval.ApprovalError, "scope changed"):
                approval.consume_prompt_request(
                    request.request_id, request.token, changed, session_id="session-a", now=101
                )
            with self.assertRaisesRegex(approval.ApprovalError, "expired"):
                approval.consume_prompt_request(
                    request.request_id, request.token, scope, session_id="session-a", now=401
                )

    def test_concurrent_consumers_allow_exactly_one(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {approval.STATE_DIR_ENV: directory, approval.MODE_ENV: "personal"},
        ):
            scope = approval.canonical_scope("UserPromptSubmit", str(ROOT), "concurrent synthetic scope")
            request = approval.issue_request(
                "UserPromptSubmit", scope, session_id="session-a", now=100
            )

            def consume() -> bool:
                try:
                    approval.consume_prompt_request(
                        request.request_id,
                        request.token,
                        scope,
                        session_id="session-a",
                        now=101,
                    )
                    return True
                except approval.ApprovalError:
                    return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: consume(), range(2)))
            self.assertEqual(results.count(True), 1)
            self.assertEqual(results.count(False), 1)

    def test_mode_defaults_personal_and_invalid_override_fails_strict(self) -> None:
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ,
            {approval.STATE_DIR_ENV: directory},
            clear=False,
        ):
            os.environ.pop(approval.MODE_ENV, None)
            self.assertEqual(approval.current_mode(), "personal")
            approval.configure_mode("strict")
            self.assertEqual(approval.current_mode(), "strict")
            os.environ[approval.MODE_ENV] = "unsupported"
            self.assertEqual(approval.current_mode(), "strict")

    @unittest.skipIf(os.name == "nt", "POSIX permission mode check")
    def test_existing_broad_state_directory_is_rejected_without_chmod(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory) / "existing-state"
            state_dir.mkdir(mode=0o755)
            state_dir.chmod(0o755)
            original_mode = state_dir.stat().st_mode & 0o777
            with patch.dict(
                os.environ,
                {approval.STATE_DIR_ENV: str(state_dir), approval.MODE_ENV: "personal"},
            ):
                scope = approval.canonical_scope("UserPromptSubmit", str(ROOT), "bounded test scope")
                with self.assertRaises(approval.StateUnavailable):
                    approval.issue_request(
                        "UserPromptSubmit", scope, session_id="session-a", now=100
                    )
            self.assertEqual(state_dir.stat().st_mode & 0o777, original_mode)

            settings = state_dir / "settings.json"
            settings.write_text('{"schema":"dev-flow.dlp-settings.v1","mode":"personal"}', encoding="utf-8")
            settings.chmod(0o600)
            with patch.dict(os.environ, {approval.STATE_DIR_ENV: str(state_dir)}, clear=False):
                os.environ.pop(approval.MODE_ENV, None)
                self.assertEqual(approval.current_mode(), "strict")
            self.assertEqual(state_dir.stat().st_mode & 0o777, original_mode)


class PolicyTests(unittest.TestCase):
    def test_test_declaration_is_context_not_placeholder_proof(self) -> None:
        self.assertTrue(policy.declares_test_data("这是测试密钥"))
        self.assertTrue(policy.declares_test_data({"purpose": "sandbox credential"}))
        self.assertFalse(policy.declares_test_data("production credential"))

    def test_macos_keychain_advice_uses_interactive_input_and_command_scoped_env(self) -> None:
        advice = policy.storage_advice("access_token", platform="darwin")
        self.assertTrue(advice.save_command.endswith(" -w"))
        self.assertNotIn(" -A", advice.save_command)
        self.assertIn("TEST_API_KEY=", advice.use_pattern)
        self.assertIn("your-test-command", advice.use_pattern)

    def test_policy_exposes_no_agent_runnable_approval_command(self) -> None:
        self.assertFalse(hasattr(policy, "approve_command"))


class HookBlueTests(unittest.TestCase):
    def assert_no_leak(self, value: str, stdout: str, stderr: str) -> None:
        self.assertFalse(value in stdout or value in stderr, "Hook output leaked the synthetic value")

    def test_user_prompt_safe_pass_and_secret_block(self) -> None:
        code, stdout, stderr = invoke_hook(hook_event("UserPromptSubmit", prompt="Explain a public API schema"))
        self.assertEqual(code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "")

        token = synthetic_token()
        code, stdout, stderr = invoke_hook(hook_event("UserPromptSubmit", prompt="debug " + token))
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["decision"], "block")
        self.assert_no_leak(token, stdout, stderr)

    def test_declared_test_prompt_can_be_confirmed_once_without_raw_state(self) -> None:
        sample = synthetic_token("github")
        prompt_text = "这是测试密钥，仅用于沙箱：" + sample
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            code, stdout, stderr = invoke_hook(
                hook_event("UserPromptSubmit", prompt=prompt_text),
                state_dir=state_dir,
            )
            self.assertEqual((code, stderr), (0, ""))
            first = json.loads(stdout)
            self.assertEqual(first["decision"], "block")
            self.assertIn("security add-generic-password", first["reason"])
            self.assertIn("prompt was not forwarded", first["reason"])
            self.assert_no_leak(sample, stdout, stderr)
            marker_match = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[^\]]+\]\]", first["reason"])
            self.assertIsNotNone(marker_match)
            assert marker_match is not None
            confirmed_prompt = marker_match.group(0) + "\n" + prompt_text

            code, stdout, stderr = invoke_hook(
                hook_event("UserPromptSubmit", prompt=confirmed_prompt),
                state_dir=state_dir,
            )
            self.assertEqual((code, stderr), (0, ""))
            allowed = json.loads(stdout)
            self.assertNotIn("decision", allowed)
            self.assertIn("already consumed", allowed["hookSpecificOutput"]["additionalContext"])
            self.assert_no_leak(sample, stdout, stderr)

            code, stdout, stderr = invoke_hook(
                hook_event("UserPromptSubmit", prompt=confirmed_prompt),
                state_dir=state_dir,
            )
            self.assertEqual((code, stderr), (0, ""))
            self.assertEqual(json.loads(stdout)["decision"], "block")
            self.assertIn("already consumed", stdout)
            persisted = b"".join(path.read_bytes() for path in state_dir.rglob("*") if path.is_file())
            self.assertNotIn(sample.encode("utf-8"), persisted)

    def test_declared_test_prompt_confirmation_rejects_changed_content_and_strict_mode(self) -> None:
        sample = synthetic_token("openai")
        prompt_text = "testing-only sandbox key " + sample
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            _, stdout, _ = invoke_hook(hook_event("UserPromptSubmit", prompt=prompt_text), state_dir=state_dir)
            marker_match = re.search(r"\[\[DEV_FLOW_DLP_CONFIRM:[^\]]+\]\]", json.loads(stdout)["reason"])
            self.assertIsNotNone(marker_match)
            assert marker_match is not None
            _, changed_stdout, _ = invoke_hook(
                hook_event("UserPromptSubmit", prompt=marker_match.group(0) + "\n" + prompt_text + " changed"),
                state_dir=state_dir,
            )
            self.assertIn("scope changed", json.loads(changed_stdout)["reason"])

            _, strict_stdout, _ = invoke_hook(
                hook_event("UserPromptSubmit", prompt=prompt_text),
                state_dir=state_dir,
                mode="strict",
            )
            strict_reason = json.loads(strict_stdout)["reason"]
            self.assertNotIn("DEV_FLOW_DLP_CONFIRM", strict_reason)
            self.assertIn("cannot use a one-shot override", strict_reason)

    def test_high_risk_private_material_has_no_personal_override(self) -> None:
        material = (
            "-----BEGIN PRIVATE "
            + "KEY-----\n"
            + "Z" * 40
            + "\n-----END PRIVATE "
            + "KEY-----"
        )
        prompt_text = "这是测试密钥 " + material
        code, stdout, stderr = invoke_hook(hook_event("UserPromptSubmit", prompt=prompt_text))
        self.assertEqual((code, stderr), (0, ""))
        reason = json.loads(stdout)["reason"]
        self.assertNotIn("DEV_FLOW_DLP_CONFIRM", reason)
        self.assertIn("cannot use a one-shot override", reason)
        self.assert_no_leak(material, stdout, stderr)

    def test_pretool_blocks_secret_and_credential_store_but_allows_reference(self) -> None:
        token = synthetic_token("openai")
        code, stdout, stderr = invoke_hook(hook_event("PreToolUse", tool_name="Bash", tool_input={"command": "curl -H 'Authorization: Bearer " + token + "' https://invalid"}))
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assert_no_leak(token, stdout, stderr)

        code, stdout, _ = invoke_hook(hook_event("PreToolUse", tool_name="Bash", tool_input={"command": "cat /tmp/.aws/credentials"}))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

        code, stdout, stderr = invoke_hook(hook_event("PreToolUse", tool_name="Bash", tool_input={"command": "psql \"$DATABASE_URL\""}))
        self.assertEqual((code, stdout, stderr), (0, "", ""))

    def test_pretool_confirmation_is_exact_and_consumed_once(self) -> None:
        sample = synthetic_token("github")
        tool_event = hook_event(
            "PreToolUse",
            tool_name="Bash",
            tool_input={"command": "run-synthetic-test --credential " + sample},
        )
        with tempfile.TemporaryDirectory() as directory:
            state_dir = Path(directory)
            code, stdout, stderr = invoke_hook(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, ""))
            denied = json.loads(stdout)
            reason = denied["hookSpecificOutput"]["permissionDecisionReason"]
            self.assertEqual(denied["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("tool was not executed", reason)
            self.assertIn("security add-generic-password", reason)
            self.assertIn("No local Agent command can approve it", reason)
            self.assert_no_leak(sample, stdout, stderr)
            marker_match = re.search(
                r"\[\[DEV_FLOW_DLP_CONFIRM:([0-9a-f]{24}):([A-Za-z0-9_-]{24,96})\]\]",
                reason,
            )
            self.assertIsNotNone(marker_match)
            assert marker_match is not None
            marker = marker_match.group(0)

            environment = os.environ.copy()
            environment[approval.STATE_DIR_ENV] = str(state_dir)
            local_approve = subprocess.run(
                [
                    sys.executable,
                    str(APPROVAL_PATH),
                    "approve",
                    "--request",
                    marker_match.group(1),
                    "--token",
                    marker_match.group(2),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=10,
                text=True,
                env=environment,
            )
            self.assertEqual(local_approve.returncode, 2)
            self.assertIn("invalid choice", local_approve.stderr)

            wrong_session = hook_event(
                "UserPromptSubmit",
                prompt=marker,
                session_id="different-session",
            )
            code, stdout, stderr = invoke_hook(wrong_session, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, ""))
            self.assertEqual(json.loads(stdout)["decision"], "block")
            self.assertIn("host session changed", stdout)

            code, stdout, stderr = invoke_hook(
                hook_event("UserPromptSubmit", prompt=marker),
                state_dir=state_dir,
            )
            self.assertEqual((code, stderr), (0, ""))
            confirmed = json.loads(stdout)
            self.assertNotIn("decision", confirmed)
            self.assertIn("UserPromptSubmit event confirmed", confirmed["hookSpecificOutput"]["additionalContext"])
            self.assert_no_leak(sample, marker + stdout, stderr)

            code, stdout, stderr = invoke_hook(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, ""))
            allowed = json.loads(stdout)
            self.assertNotIn("permissionDecision", allowed["hookSpecificOutput"])
            self.assertIn("already consumed", allowed["hookSpecificOutput"]["additionalContext"])
            self.assert_no_leak(sample, stdout, stderr)

            code, stdout, stderr = invoke_hook(tool_event, state_dir=state_dir)
            self.assertEqual((code, stderr), (0, ""))
            replay = json.loads(stdout)
            self.assertEqual(replay["hookSpecificOutput"]["permissionDecision"], "deny")
            persisted = b"".join(path.read_bytes() for path in state_dir.rglob("*") if path.is_file())
            self.assertNotIn(sample.encode("utf-8"), persisted)

    def test_posttool_replaces_secret_and_identifier_output(self) -> None:
        token = synthetic_token("slack")
        response = {"owner": "person@corp.invalid", "credential": token, "state": "failed"}
        code, stdout, stderr = invoke_hook(hook_event("PostToolUse", tool_name="Bash", tool_input={"command": "safe-command"}, tool_response=response))
        self.assertEqual(code, 0)
        payload = json.loads(stdout)
        self.assertIs(payload["continue"], False)
        context = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("DLP-safe tool result", context)
        self.assertIn("failed", context)
        self.assertIn("{{DLP:SECRET:", context)
        self.assert_no_leak(token, stdout, stderr)
        self.assertFalse("person@corp.invalid" in stdout, "Hook output leaked the synthetic email")

    def test_posttool_safe_output_passes_without_hook_context(self) -> None:
        code, stdout, stderr = invoke_hook(hook_event("PostToolUse", tool_name="Bash", tool_input={"command": "safe-command"}, tool_response={"status": "ok", "count": 2}))
        self.assertEqual((code, stdout, stderr), (0, "", ""))


class HookRedTests(unittest.TestCase):
    def test_base64_and_nested_payloads_do_not_bypass_hook(self) -> None:
        token = synthetic_token("github")
        wrapped = base64.urlsafe_b64encode(token.encode("utf-8")).decode("ascii")
        event = hook_event("PreToolUse", tool_name="mcp__synthetic__send", tool_input={"payload": {"encoded": wrapped}})
        code, stdout, stderr = invoke_hook(event)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertFalse(token in stdout or token in stderr, "Hook leaked decoded token")

    def test_malformed_event_uses_event_specific_safe_failure(self) -> None:
        raw = b'{"hook_event_name":"PreToolUse","tool_input":'
        code, stdout, stderr = invoke_hook(raw)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(stderr, "")

    def test_unknown_malformed_event_uses_documented_exit_two(self) -> None:
        code, stdout, stderr = invoke_hook(b"not-json")
        self.assertEqual(code, 2)
        self.assertEqual(stdout, "")
        self.assertIn("Malformed Hook input", stderr)

    def test_oversized_prompt_fails_closed_with_bounded_output(self) -> None:
        raw = (json.dumps({"hook_event_name": "UserPromptSubmit", "prompt": "A" * (4_194_304 + 100)})).encode("utf-8")
        code, stdout, stderr = invoke_hook(raw)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout)["decision"], "block")
        self.assertLess(len(stdout), 1000)
        self.assertEqual(stderr, "")


class DoctorTests(unittest.TestCase):
    def make_plugin_copy(self, destination: Path) -> Path:
        for relative in (
            *doctor.PROTECTED_PATHS,
            doctor.BASELINE_PATH,
            "hooks/hooks.json",
            "governance/capability-contracts.json",
            "governance/claim-kinds.json",
        ):
            source = ROOT / relative
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        return destination

    def run_doctor(self, root: Path, *extra: str) -> tuple[int, dict[str, Any]]:
        result = subprocess.run(
            [sys.executable, str(DOCTOR_PATH), "--plugin-root", str(root), *extra],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
            text=True,
        )
        self.assertEqual(result.stderr, "")
        return result.returncode, json.loads(result.stdout)

    def test_protected_controls_are_checked_out_with_lf_bytes(self) -> None:
        result = subprocess.run(
            ["git", "check-attr", "eol", "--", *doctor.PROTECTED_PATHS],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        observed: dict[str, str] = {}
        for line in result.stdout.splitlines():
            path, attribute, value = line.split(": ", 2)
            self.assertEqual(attribute, "eol")
            observed[path] = value
        self.assertEqual(set(observed), set(doctor.PROTECTED_PATHS))
        self.assertEqual({path: value for path, value in observed.items() if value != "lf"}, {})

    def test_intact_plugin_passes_with_honest_manual_gates(self) -> None:
        code, report = self.run_doctor(ROOT)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "valid_with_manual_gates")
        self.assertEqual(report["required_failures"], 0)
        self.assertGreater(report["manual_gates"], 0)
        self.assertIn("not central immutability", report["claim_limit"])
        self.assertTrue(any(item["id"] == "surface.codex.synthetic_self_test_passed" and item["status"] == "pass" for item in report["checks"]))

    def test_byte_tamper_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_plugin_copy(Path(directory))
            target = root / "skills/company-data-security/assets/ordinary-chat-instructions.md"
            target.write_text(target.read_text(encoding="utf-8") + "\ndrift\n", encoding="utf-8")
            code, report = self.run_doctor(root)
            self.assertEqual(code, 2)
            self.assertGreater(report["required_failures"], 0)
            self.assertTrue(any(item["id"].endswith("ordinary-chat-instructions.md") and item["status"] == "fail" for item in report["checks"]))

    def test_semantic_hook_drift_is_detected_even_after_baseline_refresh(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_plugin_copy(Path(directory))
            hooks_path = root / "hooks/hooks.json"
            hooks = json.loads(hooks_path.read_text(encoding="utf-8"))
            hooks["hooks"]["PreToolUse"][0]["matcher"] = "Bash"
            hooks_path.write_text(json.dumps(hooks, indent=2), encoding="utf-8")
            baseline = doctor.build_baseline(root)
            (root / doctor.BASELINE_PATH).write_text(json.dumps(baseline, indent=2, sort_keys=True), encoding="utf-8")
            code, report = self.run_doctor(root)
            self.assertEqual(code, 2)
            matching = [item for item in report["checks"] if item["id"] == "hook.PreToolUse"]
            self.assertEqual(matching[0]["status"], "fail")

    def test_capability_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_plugin_copy(Path(directory))
            contract_path = root / "governance/capability-contracts.json"
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            contract["capabilities"] = [item for item in contract["capabilities"] if item.get("skill") != "company-data-security"]
            contract_path.write_text(json.dumps(contract), encoding="utf-8")
            code, report = self.run_doctor(root)
            self.assertEqual(code, 2)
            matching = [item for item in report["checks"] if item["id"] == "capability.registration"]
            self.assertEqual(matching[0]["status"], "fail")

    def test_explicit_attestation_is_labeled_self_attested_not_proven(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            attestation = Path(directory) / "attestation.json"
            attestation.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "codex": {"hook_trust_reviewed": True, "synthetic_self_test_passed": True},
                        "chatgpt_work": {"instructions_reviewed": True, "synthetic_self_test_passed": True},
                        "ordinary_chat": {"instructions_reviewed": True, "synthetic_self_test_passed": True},
                    }
                ),
                encoding="utf-8",
            )
            code, report = self.run_doctor(ROOT, "--attestation", str(attestation))
            self.assertEqual(code, 0)
            self.assertTrue(all(item["status"] == "self_attested" for item in report["checks"] if item["id"].startswith("surface.") and item["id"] != "surface.codex.synthetic_self_test_passed"))
            self.assertTrue(any(item["id"] == "surface.codex.synthetic_self_test_passed" and item["status"] == "pass" for item in report["checks"]))


if __name__ == "__main__":
    unittest.main()
