#!/usr/bin/env python3
"""Behavior-boundary tests for the RC.7 Dev Flow maintainer evolution."""

from __future__ import annotations

import copy
import runpy
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYZER = ROOT / "skills" / "dev-flow-maintainer" / "scripts" / "analyze_dogfood.py"
MODULE = runpy.run_path(str(ANALYZER))
analyze = MODULE["analyze"]
DogfoodContractError = MODULE["DogfoodContractError"]


def method() -> dict[str, object]:
    return {
        "eligible": False,
        "activated": False,
        "selected": False,
        "readiness": "not-applicable",
        "disposition": "not-applicable",
        "realized": False,
        "evidence_effect": "not-observed",
    }


def rc4() -> dict[str, object]:
    return {
        "route": {
            "initial": 1,
            "material_transitions": 0,
            "delta_routes": 0,
            "unchanged_routes": 1,
        },
        "convergence": {
            "checkpoint_required": False,
            "checkpoint_resolved": False,
            "third_tweak": False,
        },
        "resource": {"preflight": "observed", "lease": "none"},
        "workstream": {"check": "not-applicable", "contradictions": []},
        "test_system": {
            "eligible": True,
            "activated": True,
            "negative_control": "failed-as-expected",
        },
        "evidence_status": "passed",
    }


def observation(*, slice_record: dict[str, object] | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        "task_shape": "implementation",
        "dev_flow_expected": True,
        "transitions": ["none"],
        "corrections": ["none"],
        "scope": {"mode": "bounded", "conformed": True},
        "method": method(),
    }
    if slice_record is not None:
        result["rc4"] = rc4()
        result["slice"] = slice_record
    return result


def repair_slice() -> dict[str, object]:
    return {
        "black_box_oracle": True,
        "claim": "behavior-repair-observed",
        "outcome": "passed",
        "owner": "verification",
        "structural_signals": ["coverage-green", "schema-green"],
        "termination": "proved-and-stopped",
    }


class Rc7MaintainerBehaviorTests(unittest.TestCase):
    def test_legacy_v1_output_remains_compatible(self) -> None:
        result = analyze(
            {"schema_version": "dev-flow.dogfood.observations.v1", "observations": [observation()]}
        )
        self.assertEqual(result["schema_version"], "dev-flow.dogfood.aggregate.v1")
        self.assertIsNone(result["aggregate_score"])
        self.assertNotIn("behavior_slices", result)

    def test_observed_repair_records_owner_and_bounded_closure(self) -> None:
        result = analyze(
            {
                "schema_version": "dev-flow.dogfood.observations.v3",
                "observations": [observation(slice_record=repair_slice())],
            }
        )
        self.assertEqual(result["schema_version"], "dev-flow.dogfood.aggregate.v3")
        slices = result["behavior_slices"]
        self.assertEqual(slices["claims"], {"behavior-repair-observed": 1})
        self.assertEqual(slices["affected_owners"], {"verification": 1})
        self.assertIsNone(slices["productivity_claim"])
        self.assertEqual(result["rc4"]["route"]["initial"], 1)
        self.assertEqual(result["rc4"]["test_system"]["activated"], 1)

    def test_v3_is_additive_and_rejects_slice_only_observations(self) -> None:
        slice_only = observation(slice_record=repair_slice())
        del slice_only["rc4"]
        with self.assertRaisesRegex(DogfoodContractError, "exact aggregate-safe schema"):
            analyze(
                {
                    "schema_version": "dev-flow.dogfood.observations.v3",
                    "observations": [slice_only],
                }
            )

    def test_structural_green_cannot_impersonate_behavior_repair(self) -> None:
        structural_only = repair_slice()
        structural_only["black_box_oracle"] = False
        with self.assertRaisesRegex(DogfoodContractError, "black-box pass"):
            analyze(
                {
                    "schema_version": "dev-flow.dogfood.observations.v3",
                    "observations": [observation(slice_record=structural_only)],
                }
            )

    def test_observed_regression_must_reopen_with_affected_owner(self) -> None:
        regression = copy.deepcopy(repair_slice())
        regression.update(
            {
                "claim": "behavior-regression-observed",
                "outcome": "failed",
                "owner": "systematic-debugging",
                "termination": "proved-and-stopped",
            }
        )
        with self.assertRaisesRegex(DogfoodContractError, "reopen with its owner"):
            analyze(
                {
                    "schema_version": "dev-flow.dogfood.observations.v3",
                    "observations": [observation(slice_record=regression)],
                }
            )

    def test_observed_regression_is_carried_to_its_owner(self) -> None:
        regression = copy.deepcopy(repair_slice())
        regression.update(
            {
                "claim": "behavior-regression-observed",
                "outcome": "failed",
                "owner": "systematic-debugging",
                "termination": "reopened-with-owner",
            }
        )
        result = analyze(
            {
                "schema_version": "dev-flow.dogfood.observations.v3",
                "observations": [observation(slice_record=regression)],
            }
        )
        self.assertEqual(result["behavior_slices"]["affected_owners"], {"systematic-debugging": 1})
        self.assertEqual(result["behavior_slices"]["terminations"], {"reopened-with-owner": 1})

    def test_blocked_slice_cannot_be_closed_as_a_pass(self) -> None:
        blocked = copy.deepcopy(repair_slice())
        blocked.update(
            {
                "claim": "no-improvement-claim",
                "outcome": "blocked",
                "owner": "not-applicable",
                "termination": "proved-and-stopped",
            }
        )
        with self.assertRaisesRegex(DogfoodContractError, "must end externally-blocked"):
            analyze(
                {
                    "schema_version": "dev-flow.dogfood.observations.v3",
                    "observations": [observation(slice_record=blocked)],
                }
            )


if __name__ == "__main__":
    unittest.main()
