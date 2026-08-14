#!/usr/bin/env python3
"""Synthetic blue/red tests for the packaged confidentiality controls."""

from __future__ import annotations

import base64
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "data_security.py"
DOCTOR_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "doctor.py"
HOOK_PATH = ROOT / "hooks" / "data_security_hook.py"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


dlp = _load_module("data_security_test_module", ENGINE_PATH)
doctor = _load_module("data_security_doctor_test_module", DOCTOR_PATH)


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


def invoke_hook(event: dict[str, Any] | bytes, *, timeout: int = 10) -> tuple[int, str, str]:
    payload = event if isinstance(event, bytes) else json.dumps(event, ensure_ascii=False).encode("utf-8")
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=payload,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    return result.returncode, result.stdout.decode("utf-8"), result.stderr.decode("utf-8")


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
