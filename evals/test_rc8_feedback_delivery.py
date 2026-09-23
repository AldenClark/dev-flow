#!/usr/bin/env python3
"""Deterministic RC.8 false-green fixtures using a project's native unittest path.

These synthetic host fixtures test oracle sensitivity, not model behavior or a
physical-device/deployed environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _run_native(project: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return result.stdout + result.stderr


def _write_test(project: Path, body: str) -> None:
    tests = project / "tests"
    tests.mkdir(exist_ok=True)
    (tests / "test_outcome.py").write_text(
        "import json, unittest\n"
        "from pathlib import Path\n"
        "class Outcome(unittest.TestCase):\n"
        "    def test_user_outcome(self):\n"
        + body,
        encoding="utf-8",
    )


class RC8FeedbackDeliveryTests(unittest.TestCase):
    def test_wrong_source_makes_weak_feedback_green_and_real_oracle_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            events = project / "events.json"
            events.write_text(
                json.dumps([{"source": "background-sync", "request": "heartbeat", "target": "content", "outcome": "loaded"}]),
                encoding="utf-8",
            )
            _write_test(
                project,
                "        events = json.loads(Path('events.json').read_text())\n"
                "        self.assertTrue(any(event['outcome'] == 'loaded' for event in events))\n",
            )
            weak = _run_native(project)
            self.assertEqual(weak.returncode, 0, _output(weak))
            self.assertIn("Ran 1 test", _output(weak))

            _write_test(
                project,
                "        events = json.loads(Path('events.json').read_text())\n"
                "        self.assertTrue(any(event['source'] == 'app-ui' and "
                "event['request'] == 'open-home' and event['target'] == 'content' "
                "and event['outcome'] == 'loaded' for event in events))\n",
            )
            wrong_source = _run_native(project)
            self.assertNotEqual(wrong_source.returncode, 0, _output(wrong_source))
            self.assertIn("AssertionError", _output(wrong_source))
            self.assertIn("test_user_outcome", _output(wrong_source))

            events.write_text(
                json.dumps([{"source": "app-ui", "request": "open-home", "target": "content", "outcome": "loaded"}]),
                encoding="utf-8",
            )
            intended_source = _run_native(project)
            self.assertEqual(intended_source.returncode, 0, _output(intended_source))

    def test_wrong_artifact_then_stale_effective_config_block_target_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            candidate_bytes = b"candidate-build"
            (project / "candidate.bin").write_bytes(candidate_bytes)
            (project / "candidate.json").write_text(
                json.dumps({"artifact_sha256": hashlib.sha256(candidate_bytes).hexdigest(), "route": "new"}),
                encoding="utf-8",
            )
            installed_artifact = project / "installed.bin"
            installed_artifact.write_bytes(b"prior-build")
            effective_config = project / "effective-config.json"
            effective_config.write_text(json.dumps({"route": "old"}), encoding="utf-8")
            _write_test(
                project,
                "        candidate = json.loads(Path('candidate.json').read_text())\n"
                "        self.assertEqual(len(candidate['artifact_sha256']), 64)\n",
            )
            build_only = _run_native(project)
            self.assertEqual(build_only.returncode, 0, _output(build_only))

            _write_test(
                project,
                "        import hashlib\n"
                "        candidate = json.loads(Path('candidate.json').read_text())\n"
                "        installed_hash = hashlib.sha256(Path('installed.bin').read_bytes()).hexdigest()\n"
                "        effective = json.loads(Path('effective-config.json').read_text())\n"
                "        self.assertEqual(installed_hash, candidate['artifact_sha256'])\n"
                "        self.assertEqual(effective['route'], candidate['route'])\n",
            )
            wrong_artifact = _run_native(project)
            self.assertNotEqual(wrong_artifact.returncode, 0, _output(wrong_artifact))
            self.assertIn("AssertionError", _output(wrong_artifact))

            installed_artifact.write_bytes(candidate_bytes)
            stale_config = _run_native(project)
            self.assertNotEqual(stale_config.returncode, 0, _output(stale_config))
            self.assertIn("'old' != 'new'", _output(stale_config))

            effective_config.write_text(json.dumps({"route": "new"}), encoding="utf-8")
            matched = _run_native(project)
            self.assertEqual(matched.returncode, 0, _output(matched))

    def test_skill_contracts_keep_feedback_and_delivery_conditional(self) -> None:
        files = {
            name: (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            for name in ("repo-context", "test-system-engineering", "verification", "delivery-readiness")
        }
        self.assertIn("smallest project-native capability", files["test-system-engineering"])
        self.assertIn("A small closed task with adequate feedback needs no setup expansion", files["test-system-engineering"])
        self.assertIn("wrong actor/source", files["test-system-engineering"])
        self.assertIn("actual target and install", files["verification"])
        self.assertIn("effective configuration and data", files["verification"])
        self.assertIn("host-green/device-unknown", files["delivery-readiness"])
        self.assertIn("safe recovery/rollback", files["delivery-readiness"])
        self.assertIn("Configured is not passed", files["repo-context"])


if __name__ == "__main__":
    unittest.main()
