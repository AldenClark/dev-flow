#!/usr/bin/env python3
"""Stable-validation simulation tests."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "simulate_stable_validation.py"
SPEC = importlib.util.spec_from_file_location("simulate_stable_validation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
SIMULATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SIMULATOR)


class StableValidationSimulationTests(unittest.TestCase):
    def test_repository_simulation_is_non_mutating_and_ready(self) -> None:
        result = SIMULATOR.simulate(ROOT, "v1.1.2", "WORKTREE")
        self.assertEqual(result["status"], "ready", result["policy_errors"])
        self.assertEqual(len(result["static_review"]["methods"]), 6)
        self.assertEqual(len(result["functional_acceptance"]["journeys"]), 5)
        self.assertFalse(any(result["actions"].values()))
        self.assertGreater(result["delta"]["changed_files"], 0)

    def test_missing_baseline_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            SIMULATOR.simulate(ROOT, "definitely-missing-stable-tag", "WORKTREE")

    def test_obsolete_active_r4_release_tier_blocks_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=root, check=True)
            for relative in SIMULATOR.ACTIVE_POLICY_FILES:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("current policy\n", encoding="utf-8")
            (root / "docs" / "releasing.md").write_text(
                "| R4 model-semantic | obsolete | gate |\n", encoding="utf-8"
            )
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=root, check=True)
            subprocess.run(["git", "tag", "v1.1.2"], cwd=root, check=True)
            result = SIMULATOR.simulate(root, "v1.1.2", "WORKTREE")
        self.assertEqual(result["status"], "blocked")
        self.assertTrue(any("obsolete stable R4 rule" in item for item in result["policy_errors"]))


if __name__ == "__main__":
    unittest.main()
