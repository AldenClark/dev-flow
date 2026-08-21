#!/usr/bin/env python3
"""Regression simulations for material, multi-boundary Dev Flow tasks."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "skills" / "dev-flow" / "scripts" / "flow_metrics.py"
CATALOG = ROOT / "evals" / "large-task-routing-cases.json"

FAMILY_CONTRACT = {
    "F01": "issue diagnosis",
    "F02": "bounded defect fix",
    "F03": "structural defect fix",
    "F04": "feature implementation",
    "F05": "cross-module feature",
    "F06": "behavior-preserving refactor",
    "F07": "performance and resources",
    "F08": "concurrency and distributed state",
    "F09": "data lifecycle and migration",
    "F10": "API, protocol, and ABI contracts",
    "F11": "dependency and toolchain change",
    "F12": "security and privacy",
    "F13": "UI, accessibility, and platform lifecycle",
    "F14": "tests, evaluation, and CI",
    "F15": "code and proposal review",
    "F16": "architecture and product design",
    "F17": "repository and option research",
    "F18": "build, operations, and scientific workflows",
    "F19": "release and delivery readiness",
    "F20": "long-horizon coordinated evolution",
}


def option_values(command: list[str], option: str) -> list[str]:
    return [command[index + 1] for index, value in enumerate(command[:-1]) if value == option]


def family_contract_errors(cases: list[dict[str, object]]) -> list[str]:
    counts = {family: 0 for family in FAMILY_CONTRACT}
    errors: list[str] = []
    for case in cases:
        case_id = case["id"]
        match = re.match(r"^LARGE-(F\d{2})-", case_id)
        if match is None:
            errors.append(f"{case_id}: missing structured family id")
            continue
        family = match.group(1)
        if family not in FAMILY_CONTRACT:
            errors.append(f"{case_id}: unknown family {family}")
            continue
        counts[family] += 1
    for family, count in counts.items():
        if count != 4:
            errors.append(f"{family}: expected 4 variants, observed {count}")
    if len(cases) != 80:
        errors.append(f"catalog: expected 80 cases, observed {len(cases)}")
    return errors


class LargeTaskRoutingSimulationTests(unittest.TestCase):
    def run_catalog(self, path: Path = CATALOG) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(RUNNER), str(path)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_material_scenarios_follow_expected_dev_flow_branches(self) -> None:
        completed = self.run_catalog()
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["cases"], 80)
        self.assertEqual(result["matched"], 80)
        self.assertFalse(result["effect_measurement"])
        self.assertIsNone(result["aggregate_score"])

    def test_catalog_has_twenty_balanced_common_task_families(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(family_contract_errors(catalog["cases"]), [])

        missing = catalog["cases"][1:]
        errors = family_contract_errors(missing)
        self.assertTrue(any("F01: expected 4 variants, observed 3" in error for error in errors))
        self.assertTrue(any("expected 80 cases, observed 79" in error for error in errors))

    def test_catalog_covers_route_dimensions_not_just_case_count(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cases = catalog["cases"]
        self.assertTrue(all(case["command"][0] == "route-task" for case in cases))
        self.assertEqual(len({tuple(case["command"]) for case in cases}), 80)
        for case in cases:
            checks = sum(len(case.get(field, {})) for field in ("expect", "contains", "excludes"))
            self.assertGreaterEqual(checks, 3, case["id"])
        intents = {
            value
            for case in cases
            for value in option_values(case["command"], "--intent")
        }
        self.assertEqual(intents, {"research", "diagnose", "design", "change", "review", "delivery"})
        requirement_classes = {
            value
            for case in cases
            for value in option_values(case["command"], "--requirement-class")
        }
        self.assertEqual(
            requirement_classes,
            {"semantic-change", "structural-adjustment", "defect-correction", "mechanical", "read-only"},
        )
        expected_modes = [case["expect"].get("work_mode") for case in cases]
        self.assertGreaterEqual(expected_modes.count("direct"), 30)
        self.assertGreaterEqual(expected_modes.count("managed"), 30)
        risks = {
            value
            for case in cases
            for value in option_values(case["command"], "--risk")
        }
        self.assertGreaterEqual(len(risks), 45)
        method_signals = {
            value
            for case in cases
            for value in option_values(case["command"], "--method-signal")
        }
        self.assertGreaterEqual(len(method_signals), 10)
        self.assertGreaterEqual(sum("excludes" in case for case in cases), 15)

    def test_scenarios_cover_owners_overlays_methods_and_recent_failures(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        serialized = json.dumps(catalog)
        self.assertNotIn("select-methods", serialized)
        for control in (
            "repo-context",
            "requirements-design",
            "systematic-debugging",
            "architecture-decisions",
            "dependency-decisions",
            "product-ux-discovery",
            "background-execution",
            "dev-flow-maintainer",
            "verification",
            "change-review",
            "delivery-readiness",
            "state-transition-model",
            "agent-evaluation-design",
            "common-mode-risk",
            "reconcile-changed-paths-and-parallel-changes",
        ):
            self.assertIn(control, serialized)
        for overlay in (
            "security",
            "migration",
            "external-system",
            "release",
            "irreversible",
            "ui-product",
        ):
            self.assertIn(overlay, serialized)
        for boundary in (
            "PUSH-LATENCY",
            "DURABLE-OUTBOX",
            "RECOVERABLE-DELETION",
            "SSE-PARTIAL-RESPONSE",
            "MODEL-EVALUATION",
            "EXPAND-CONTRACT",
            "INTERRUPTED-WORKSTREAM",
            "ROLLBACK-ASSESSMENT",
        ):
            self.assertIn(boundary, serialized)

    def test_large_scenario_oracle_detects_a_missing_advanced_method(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        candidate = next(case for case in catalog["cases"] if case["id"] == "LARGE-F14-TESTING-RC-MODEL-EVALUATION")
        candidate["contains"]["capability_activation.method.selection.selected"].append(
            "nonexistent-evaluation-method"
        )
        catalog["cases"] = [candidate]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "mutated-large-task-cases.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            completed = self.run_catalog(path)
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        self.assertEqual(result["mismatched"], ["LARGE-F14-TESTING-RC-MODEL-EVALUATION"])
        self.assertIn(
            "nonexistent-evaluation-method",
            "\n".join(result["results"][0]["observations"]),
        )

    def test_negative_oracles_detect_overactivation_and_missing_specialist(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        mutations = (
            ("LARGE-F06-REFACTOR-MECHANICAL-RENAME", "contains", "routes", "change-review"),
            (
                "LARGE-F13-UI-IOS-BACKGROUND-LIFECYCLE",
                "contains",
                "capability_activation.specialist.matches",
                "nonexistent-platform-specialist",
            ),
        )
        for case_id, field, path, value in mutations:
            with self.subTest(case_id=case_id):
                candidate = next(case for case in catalog["cases"] if case["id"] == case_id)
                candidate.setdefault(field, {}).setdefault(path, [])
                expected = candidate[field][path]
                if not isinstance(expected, list):
                    candidate[field][path] = [expected]
                candidate[field][path].append(value)
                mutated = {**catalog, "cases": [candidate]}
                with tempfile.TemporaryDirectory() as temp:
                    path_obj = Path(temp) / "mutated-large-task-cases.json"
                    path_obj.write_text(json.dumps(mutated), encoding="utf-8")
                    completed = self.run_catalog(path_obj)
                self.assertEqual(completed.returncode, 1)
                result = json.loads(completed.stdout)
                self.assertEqual(result["mismatched"], [case_id])
                self.assertIn(value, "\n".join(result["results"][0]["observations"]))


if __name__ == "__main__":
    unittest.main()
