#!/usr/bin/env python3
"""Tests for compatibility-named Flow Activation Coverage."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skills" / "dev-flow" / "scripts" / "flow_metrics.py"
CATALOG = ROOT / "evals" / "flow-activation-cases.json"
SEMANTIC_CATALOG = ROOT / "evals" / "flow-activation-semantic-cases.json"
PROFESSIONAL_OWNERS = {
    "architecture-decisions",
    "change-review",
    "company-data-security",
    "delivery-readiness",
    "dependency-decisions",
    "dev-flow-maintainer",
    "manage-engineering-profiles",
    "product-ux-discovery",
    "repo-context",
    "repository-knowledge",
    "requirements-design",
    "systematic-debugging",
    "test-system-engineering",
    "verification",
}


class FlowActivationCoverageTests(unittest.TestCase):
    def test_shipped_catalog_matches_without_effect_score(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "matched")
        self.assertGreaterEqual(result["cases"], 27)
        self.assertEqual(result["matched"], result["cases"])
        self.assertFalse(result["effect_measurement"])
        self.assertIsNone(result["aggregate_score"])

    def test_mismatch_is_reported_as_activation_observation(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        catalog["cases"] = [{
            "id": "MISMATCH",
            "command": ["route-task", "--intent", "change", "--requirement-class", "mechanical"],
            "expect": {"work_mode": "managed"},
        }]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER), str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        self.assertEqual(result["mismatched"], ["MISMATCH"])
        self.assertIn("expected 'managed'", result["results"][0]["observations"][0])

    def test_invalid_catalog_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "cases.json"
            path.write_text('{"schema_version":"1.0","purpose":"x","cases":[]}', encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER), str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "invalid")

    def test_semantic_catalog_is_bounded_and_activation_only(self) -> None:
        catalog = json.loads(SEMANTIC_CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(set(catalog), {"schema_version", "purpose", "cases"})
        self.assertEqual(catalog["schema_version"], "1.0")
        self.assertIn("no effect", catalog["purpose"])
        self.assertGreaterEqual(len(catalog["cases"]), 5)
        ids = set()
        explicit_prompts = 0
        implicit_prompts = 0
        implicit_positive = 0
        implicit_negative = 0
        for case in catalog["cases"]:
            self.assertEqual(set(case), {"id", "repository", "prompt", "expected", "forbidden"})
            self.assertNotIn(case["id"], ids)
            ids.add(case["id"])
            self.assertTrue(case["repository"])
            self.assertTrue(case["expected"])
            self.assertTrue(case["forbidden"])
            if "$dev-flow" in case["prompt"]:
                explicit_prompts += 1
            else:
                implicit_prompts += 1
                if "dev-flow" in case["expected"]:
                    implicit_positive += 1
                if any(value in {"dev-flow", "sustained-dev-flow"} for value in case["forbidden"]):
                    implicit_negative += 1
        self.assertGreaterEqual(explicit_prompts, 3)
        self.assertGreaterEqual(implicit_prompts, 6)
        self.assertGreaterEqual(implicit_positive, 3)
        self.assertGreaterEqual(implicit_negative, 3)
        serialized = json.dumps(catalog).lower()
        for forbidden in ("productivity_score", "effect_score", "aggregate_score", "developer_rank"):
            self.assertNotIn(forbidden, serialized)

    def test_semantic_catalog_has_an_owner_complete_discovery_matrix(self) -> None:
        catalog = json.loads(SEMANTIC_CATALOG.read_text(encoding="utf-8"))
        registered = {
            path.parent.name
            for path in (ROOT / "skills").glob("*/SKILL.md")
            if path.parent.name != "dev-flow"
        }
        self.assertEqual(registered, PROFESSIONAL_OWNERS)
        positive = {
            value
            for case in catalog["cases"]
            for value in case["expected"]
            if value in PROFESSIONAL_OWNERS
        }
        self.assertEqual(positive, PROFESSIONAL_OWNERS)
        self.assertTrue(
            any(
                "dev-flow-maintainer" in case["forbidden"]
                and "$dev-flow-maintainer" not in case["prompt"]
                for case in catalog["cases"]
            ),
            "the explicit-only maintainer needs an implicit quietness case",
        )

    def test_semantic_lane_evaluates_first_attempt_observations(self) -> None:
        catalog = json.loads(SEMANTIC_CATALOG.read_text(encoding="utf-8"))
        observations = {
            "schema_version": "flow.activation.observations.v1",
            "cases": [
                {
                    "id": case["id"],
                    "observed": case["expected"],
                    "evidence": [f"isolated first attempt for {case['id']}"],
                    "unmet_prerequisites": [],
                    "authority_violations": [],
                }
                for case in catalog["cases"]
            ],
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "observations.json"
            path.write_text(json.dumps(observations), encoding="utf-8")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"),
                    "flow-metrics",
                    "--lane",
                    "semantic",
                    "--observations",
                    str(path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["lane"], "semantic-observation")
        self.assertEqual(result["matched"], len(catalog["cases"]))
        self.assertFalse(result["effect_measurement"])
        self.assertIsNone(result["aggregate_score"])

    def test_semantic_lane_reports_missing_forbidden_and_authority_observations(self) -> None:
        catalog = json.loads(SEMANTIC_CATALOG.read_text(encoding="utf-8"))
        first = catalog["cases"][0]
        observations = {
            "schema_version": "flow.activation.observations.v1",
            "cases": [{
                "id": first["id"],
                "observed": [first["forbidden"][0]],
                "evidence": ["preserved first response"],
                "unmet_prerequisites": ["repository unavailable"],
                "authority_violations": ["source mutated"],
            }],
        }
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "observations.json"
            path.write_text(json.dumps(observations), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER), "--lane", "semantic", "--observations", str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        details = "\n".join(result["results"][0]["observations"])
        self.assertIn("missing expected activation", details)
        self.assertIn("forbidden activation observed", details)
        self.assertIn("unmet prerequisites", details)
        self.assertIn("authority violations", details)
        self.assertGreater(len(result["mismatched"]), 1, "missing case observations must also fail")

    def test_semantic_lane_requires_actual_observations(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--lane", "semantic"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("requires --observations", completed.stdout)

    def test_deterministic_catalog_covers_required_branch_families(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        serialized = json.dumps(catalog)
        for intent in ("research", "diagnose", "design", "change", "review", "delivery"):
            self.assertIn(f'"--intent", "{intent}"', serialized)
        for overlay in ("security", "migration", "external-system", "release", "irreversible", "ui-product"):
            self.assertIn(overlay, serialized)
        for profile in ("P0", "P1", "P2", "P3", "P4", "P5", "P6"):
            self.assertIn(f'"{profile}"', serialized)
        for boundary in (
            "AMBIGUOUS-DEFECT",
            "PLUGIN-PREFIXED",
            "QUALIFIED-FALLBACK",
            "ROOT-DECISIONS",
            "KNOWLEDGE-UPDATES",
            "NATIVE-ADAPTERS",
        ):
            self.assertIn(boundary, serialized)

    def test_active_method_guidance_uses_integrated_route(self) -> None:
        guidance = (ROOT / "skills" / "dev-flow" / "references" / "quality-calibration.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("dev-flow.py route-task", guidance)
        self.assertIn("--method-signal", guidance)
        self.assertIn("--compact", guidance)
        self.assertIn("at most one selection", guidance)
        self.assertIn("do not browse", guidance)
        self.assertIn("Do not recursively review a review", guidance)
        self.assertNotIn("`select-methods --intent", guidance)


if __name__ == "__main__":
    unittest.main()
