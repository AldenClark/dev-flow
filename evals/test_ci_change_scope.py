#!/usr/bin/env python3
"""Tests for compatibility CI change scoping."""

from __future__ import annotations

from pathlib import Path
import json
import re
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import ci_change_scope  # noqa: E402


class CompatibilityChangeScopeTests(unittest.TestCase):
    def test_all_dlp_audits_trigger_and_run_in_compatibility(self) -> None:
        audit_paths = sorted((ROOT / "evals").glob("test_dlp_*_audit.py"))
        self.assertTrue(audit_paths)
        workflow = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
        compatibility = re.search(r"(?ms)^  compatibility:\n(.*?)(?=^  [A-Za-z0-9_-]+:|\Z)", workflow).group(1)
        modules = set(re.findall(r"^\s+(evals\.[A-Za-z0-9_]+)\s*$", compatibility, re.MULTILINE))
        for path in audit_paths:
            relative = path.relative_to(ROOT).as_posix()
            with self.subTest(path=relative, contract="change-discovery"):
                self.assertTrue(ci_change_scope.requires_compatibility([relative])[0])
            with self.subTest(path=relative, contract="test-execution"):
                self.assertIn("evals." + path.stem, modules)

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
            "skills/dev-flow/scripts/public_cli.py",
            "skills/dev-flow/scripts/runtime_doctor.py",
            "skills/company-data-security/scripts/dlp_approval.py",
            "skills/manage-engineering-profiles/scripts/profile-tool.py",
            "skills/repository-knowledge/scripts/repository_knowledge.py",
            "hooks/hooks.json",
            "skills/dev-flow/assets/agent-configs/dev-flow-worker.toml",
            "evals/test_agent_dispatch.py",
            "evals/test_rc7_testing_behavior.py",
            "evals/test_resource_coordination.py",
            "benchmarks/dev_flow_bench_fixture_mcp.py",
            "benchmarks/dev_flow_bench.py",
            "benchmarks/dev_flow_bench_executor.py",
            "benchmarks/cases/dev-flow-cases.json",
            "evals/test_dev_flow_bench_executor.py",
            ".github/workflows/ci.yml",
            "governance/compatibility-surfaces.json",
            "governance/product-state.json",
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

    def test_machine_inventory_is_exact_and_rejects_ambiguous_patterns(self) -> None:
        self.assertIn("skills/dev-flow/scripts/**", ci_change_scope.load_patterns())
        with tempfile.TemporaryDirectory() as temp:
            inventory = Path(temp) / "surfaces.json"
            inventory.write_text(
                json.dumps(
                    {
                        "schema_version": ci_change_scope.INVENTORY_SCHEMA,
                        "patterns": ["hooks/**", "hooks/**"],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                ci_change_scope.load_patterns(inventory)


if __name__ == "__main__":
    unittest.main()
