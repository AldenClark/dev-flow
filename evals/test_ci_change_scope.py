#!/usr/bin/env python3
"""Tests for compatibility CI change scoping."""

from __future__ import annotations

from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ci_change_scope  # noqa: E402


class CompatibilityChangeScopeTests(unittest.TestCase):
    def test_docs_only_change_skips_compatibility(self) -> None:
        required, matched = ci_change_scope.requires_compatibility(
            ["README.md", "docs/workstreams/example/progress.md"]
        )
        self.assertFalse(required)
        self.assertEqual(matched, [])

    def test_runtime_and_host_paths_require_compatibility(self) -> None:
        for path in (
            "skills/dev-flow/scripts/dev_flow.py",
            "skills/dev-flow/scripts/path_contracts.py",
            "hooks/hooks.json",
            "skills/dev-flow/assets/agent-configs/dev-flow-worker.toml",
            "evals/test_agent_dispatch.py",
            ".github/workflows/ci.yml",
        ):
            with self.subTest(path=path):
                required, matched = ci_change_scope.requires_compatibility([path])
                self.assertTrue(required)
                self.assertEqual(matched, [path])

    def test_mixed_change_reports_only_matching_paths(self) -> None:
        required, matched = ci_change_scope.requires_compatibility(
            ["docs/releasing.md", "tools/ci_change_scope.py", "skills/dev-flow/SKILL.md"]
        )
        self.assertTrue(required)
        self.assertEqual(matched, ["tools/ci_change_scope.py"])


if __name__ == "__main__":
    unittest.main()
