from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_discovery(root: Path, start: str, *, environment: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", start, "-v"],
        cwd=root,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )


class TestSystemIntegrityFixtures(unittest.TestCase):
    def test_skill_contract_has_positive_negative_and_six_obligations(self) -> None:
        skill = (ROOT / "skills" / "test-system-engineering" / "SKILL.md").read_text(encoding="utf-8")
        reference = (ROOT / "skills" / "test-system-engineering" / "references" / "test-system-integrity.md").read_text(encoding="utf-8")
        for trigger in ("zero discovery", "selector uncertainty", "inert assertions", "fixture pollution", "misleading runner success"):
            self.assertIn(trigger, skill)
        self.assertIn("Do not activate it merely because a feature has tests", skill)
        for obligation in ("Discovery", "Selection", "Sensitivity", "Isolation", "Interpretation", "Representativeness"):
            self.assertIn(f"## {obligation}", reference)

    def test_zero_discovery_is_detected_independently_of_exit_convention(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "empty").mkdir()
            result = run_discovery(root, "empty")
        combined = result.stdout + result.stderr
        self.assertIn(result.returncode, {0, 5})
        self.assertIn("Ran 0 tests", combined)
        self.assertNotIn("Ran 1 test", combined)

    def test_wrong_selector_can_be_green_while_omitting_the_target(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for directory, name in (("target", "target_contract"), ("decoy", "decoy_contract")):
                suite = root / directory
                suite.mkdir()
                (suite / f"test_{name}.py").write_text(
                    "import unittest\nclass Case(unittest.TestCase):\n    def test_"
                    + name
                    + "(self): self.assertTrue(True)\n",
                    encoding="utf-8",
                )
            result = run_discovery(root, "decoy")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0)
        self.assertIn("decoy_contract", combined)
        self.assertNotIn("target_contract", combined)

    def test_negative_control_proves_oracle_sensitivity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            suite = root / "suite"
            suite.mkdir()
            (suite / "test_oracle.py").write_text(
                "import os, unittest\n"
                "class Oracle(unittest.TestCase):\n"
                "    def test_claim(self): self.assertNotEqual(os.getenv('BREAK_ORACLE'), '1')\n",
                encoding="utf-8",
            )
            control = run_discovery(root, "suite")
            broken_environment = dict(os.environ)
            broken_environment["BREAK_ORACLE"] = "1"
            mutation = run_discovery(root, "suite", environment=broken_environment)
        self.assertEqual(control.returncode, 0)
        self.assertNotEqual(mutation.returncode, 0)
        self.assertIn("FAILED", mutation.stdout + mutation.stderr)

    def test_fixture_pollution_is_distinct_from_product_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            suite = root / "suite"
            suite.mkdir()
            (suite / "test_pollution.py").write_text(
                "import pathlib, unittest\n"
                "MARKER = pathlib.Path(__file__).with_name('leak')\n"
                "class Pollution(unittest.TestCase):\n"
                "    def test_1_writes_shared_state(self): MARKER.write_text('leak')\n"
                "    def test_2_requires_isolation(self): self.assertFalse(MARKER.exists())\n",
                encoding="utf-8",
            )
            result = run_discovery(root, "suite")
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("test_2_requires_isolation", combined)

    def test_skip_only_green_requires_interpretation_and_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            suite = root / "suite"
            suite.mkdir()
            (suite / "test_skip.py").write_text(
                "import unittest\n"
                "class Skipped(unittest.TestCase):\n"
                "    @unittest.skip('environment unavailable')\n"
                "    def test_product(self): self.fail('not executed')\n",
                encoding="utf-8",
            )
            result = run_discovery(root, "suite")
        combined = result.stdout + result.stderr
        self.assertEqual(result.returncode, 0)
        self.assertIn("skipped", combined)
        self.assertNotIn("FAILED", combined)


if __name__ == "__main__":
    unittest.main()
