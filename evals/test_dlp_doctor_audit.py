#!/usr/bin/env python3
"""Focused malformed-input and read-bound tests for the DLP doctor."""

from __future__ import annotations

import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
DOCTOR_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "doctor.py"


def _load_doctor():
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("dlp_doctor_audit_module", DOCTOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


doctor = _load_doctor()


class RecordingReader(io.BytesIO):
    def __init__(self, raw: bytes) -> None:
        super().__init__(raw)
        self.read_sizes: list[int] = []

    def read(self, size: int = -1) -> bytes:
        self.read_sizes.append(size)
        return super().read(size)


class DoctorInputAuditTests(unittest.TestCase):
    def test_posttool_semantic_self_test_rejects_missing_block_decision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT / "skills/company-data-security/scripts", root / "skills/company-data-security/scripts")
            hook = root / "hooks/data_security_hook.py"
            hook.parent.mkdir()
            source = (ROOT / "hooks/data_security_hook.py").read_text()
            start = source.index("def _posttool_replace(")
            end = source.index("\ndef _safe_failure(", start)
            body = source[start:end]
            self.assertEqual(body.count('"decision": "block",'), 1)
            hook.write_text(source[:start] + body.replace('"decision": "block",', '') + source[end:])
            checks = {item.check_id: item.status for item in doctor._self_test_checks(root)}
            self.assertEqual(checks["self-test.post-redaction"], "fail")

    def test_json_reader_caps_read_before_rejecting_oversized_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic.json"
            path.write_bytes(b"x" * 1_000_000)
            reader = RecordingReader(path.read_bytes())
            with patch.object(Path, "open", autospec=True, return_value=reader):
                with self.assertRaisesRegex(ValueError, "doctor input limit"):
                    doctor._read_json(path, max_bytes=16)
            self.assertEqual(reader.read_sizes, [17])

    def test_template_checks_report_missing_and_invalid_utf8_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            checks = doctor._template_checks(root)
            by_id = {item.check_id: item for item in checks}
            self.assertEqual(by_id["skill.metadata"].status, "fail")
            self.assertIn("unreadable or invalid", by_id["skill.metadata"].detail)
            self.assertEqual(by_id["template.chatgpt_work"].status, "fail")
            self.assertEqual(by_id["template.ordinary_chat"].status, "fail")

            openai = root / "skills/company-data-security/agents/openai.yaml"
            work_template = root / "skills/company-data-security/assets/chatgpt-work-instructions.md"
            ordinary_template = root / "skills/company-data-security/assets/ordinary-chat-instructions.md"
            openai.parent.mkdir(parents=True)
            work_template.parent.mkdir(parents=True)
            openai.write_bytes(b"\xff")
            work_template.write_bytes(b"\xff")
            ordinary_template.write_text("not a deterministic pre-send interception layer", encoding="utf-8")

            checks = doctor._template_checks(root)
            by_id = {item.check_id: item for item in checks}
            self.assertEqual(by_id["skill.metadata"].status, "fail")
            self.assertEqual(by_id["template.chatgpt_work"].status, "fail")
            self.assertEqual(by_id["template.ordinary_chat"].status, "pass")
            self.assertNotIn("\ufffd", json.dumps([item.as_dict() for item in checks]))

            openai.write_bytes(b"x" * (262_144 + 1))
            checks = doctor._template_checks(root)
            self.assertEqual(next(item for item in checks if item.check_id == "skill.metadata").status, "fail")

    def test_registry_container_types_return_failure_checks_not_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            governance = root / "governance"
            governance.mkdir()
            capability_path = governance / "capability-contracts.json"
            kinds_path = governance / "claim-kinds.json"

            for capabilities in (42, {"unexpected": []}):
                capability_path.write_text(
                    json.dumps({"capabilities": capabilities}), encoding="utf-8"
                )
                kinds_path.write_text(json.dumps({"kinds": []}), encoding="utf-8")
                checks = doctor._capability_checks(root)
                registration = next(item for item in checks if item.check_id == "capability.registration")
                self.assertEqual(registration.status, "fail")
                self.assertIn("unreadable or invalid", registration.detail)

            capability_path.write_text(json.dumps({"capabilities": []}), encoding="utf-8")
            for kinds in (42, {"unexpected": []}):
                kinds_path.write_text(json.dumps({"kinds": kinds}), encoding="utf-8")
                checks = doctor._capability_checks(root)
                claim_kinds = next(item for item in checks if item.check_id == "capability.claim-kinds")
                self.assertEqual(claim_kinds.status, "fail")
                self.assertIn("unreadable or invalid", claim_kinds.detail)


if __name__ == "__main__":
    unittest.main()
