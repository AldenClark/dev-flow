from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validator():
    path = ROOT / "tools" / "validate_rc5_coverage.py"
    spec = importlib.util.spec_from_file_location("validate_rc5_coverage", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class RC5StaticCoverageTests(unittest.TestCase):
    def test_requirement_decision_implementation_test_coverage_is_complete(self) -> None:
        result = load_validator().validate(ROOT, check_worktree=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["coverage_percent"], 100)
        self.assertEqual(result["decisions_covered"], 8)

    def test_post_rc5_worktree_is_not_inherited_as_rc5_ownership(self) -> None:
        result = load_validator().validate(ROOT, check_worktree=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["changed_paths_checked"], 0)
        self.assertEqual(result["uncovered_changed_paths"], [])

    def test_ci_does_not_assign_later_push_paths_to_rc5(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("python tools/validate_rc5_coverage.py --root .", workflow)
        self.assertNotIn("python tools/validate_rc5_coverage.py --root . --check-event", workflow)

    def test_source_markers_and_test_symbols_are_independent_oracles(self) -> None:
        validator = load_validator()
        requirements = (
            ROOT / "docs" / "workstreams" / "dev-flow-2.0-rc.5" / "requirements.md"
        ).read_text(encoding="utf-8")
        identifiers = validator.traceability_core.source_requirement_ids(requirements)
        self.assertEqual(len(identifiers), 8)
        self.assertIn("RC5-DLP-MEMORY", identifiers)
        symbols = validator.traceability_core.python_test_symbols(
            ROOT / "evals" / "test_public_cli.py"
        )
        self.assertIn("PublicCliTests", symbols)


if __name__ == "__main__":
    unittest.main()
