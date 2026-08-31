from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "tools" / "validate_rc4_coverage.py"
    spec = importlib.util.spec_from_file_location("validate_rc4_coverage", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RC4StaticCoverageTests(unittest.TestCase):
    def test_requirement_decision_implementation_test_coverage_is_100_percent(self) -> None:
        result = load_validator().validate(ROOT, check_worktree=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["coverage_percent"], 100)
        self.assertEqual(result["decisions_covered"], 15)

    def test_historical_rc4_trace_remains_valid_without_claiming_rc5_ownership(self) -> None:
        result = load_validator().validate(ROOT, check_worktree=False)
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_static_scan_has_no_route_identity_or_file_drift(self) -> None:
        path = ROOT / "tools" / "static_scan_rc4.py"
        spec = importlib.util.spec_from_file_location("static_scan_rc4", path)
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.scan(ROOT)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["traceability_coverage_percent"], 100)
        self.assertEqual(result["drift_findings"], 0)

    def test_requirement_and_test_oracles_are_independent_sources(self) -> None:
        validator = load_validator()
        requirements = (
            ROOT / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "requirements.md"
        ).read_text(encoding="utf-8")
        identifiers = validator.source_requirement_ids(requirements)
        self.assertEqual(len(identifiers), 11)
        mutated = requirements.replace(
            "<!-- requirement: RC4-RESOURCE -->", "", 1
        )
        self.assertNotEqual(
            set(validator.source_requirement_ids(mutated)), set(identifiers)
        )
        with tempfile.TemporaryDirectory() as temporary:
            fake = Path(temporary) / "test_fake.py"
            fake.write_text(
                "import unittest\nclass NamedButInert(unittest.TestCase):\n"
                "    def test_name_only(self): pass\n",
                encoding="utf-8",
            )
            self.assertNotIn("NamedButInert", validator.python_test_symbols(fake))

    def test_clean_ci_event_diff_supplies_changed_paths(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "RC4 Test"], cwd=root, check=True)
            changed = root / "changed.txt"
            changed.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "changed.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            base = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            changed.write_text("after\n", encoding="utf-8")
            subprocess.run(["git", "commit", "--quiet", "-am", "change"], cwd=root, check=True)
            head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
            event = root / "event.json"
            event.write_text(
                json.dumps(
                    {"pull_request": {"base": {"sha": base}, "head": {"sha": head}}}
                ),
                encoding="utf-8",
            )
            paths = validator.event_changed_paths(root, "pull_request", event)
        self.assertEqual(paths, ["changed.txt"])

    def test_staged_worktree_changes_remain_in_the_local_scan_set(self) -> None:
        validator = load_validator()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.invalid"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "RC4 Test"], cwd=root, check=True)
            tracked = root / "tracked.txt"
            tracked.write_text("before\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt"], cwd=root, check=True)
            subprocess.run(["git", "commit", "--quiet", "-m", "base"], cwd=root, check=True)
            tracked.write_text("after\n", encoding="utf-8")
            added = root / "added.txt"
            added.write_text("new\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.txt", "added.txt"], cwd=root, check=True)
            paths = validator.worktree_changed_paths(root)
        self.assertEqual(paths, ["added.txt", "tracked.txt"])


if __name__ == "__main__":
    unittest.main()
