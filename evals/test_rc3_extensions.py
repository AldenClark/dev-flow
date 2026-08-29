#!/usr/bin/env python3
"""Focused deterministic contracts for the RC.3 scope and method extensions."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
DOGFOOD = (
    ROOT / "skills" / "dev-flow-maintainer" / "scripts" / "analyze_dogfood.py"
)
QUALITY = ROOT / "skills" / "dev-flow" / "references" / "quality-calibration.md"
TRANSITIONS = ROOT / "evals" / "flow-transition-semantic-cases.json"
ORCHESTRATION = (
    ROOT / "skills" / "dev-flow" / "references" / "multi-agent-v2-orchestration.md"
)
ADAPTERS = ROOT / "skills" / "dev-flow" / "references" / "codex-native-adapters.md"
METHOD_PAIRS = ROOT / "evals" / "method-marginal-utility-cases.json"
METHOD_POOL = ROOT / "governance" / "methodology-pool.json"


def route(*args: str) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(FLOW), "route-task", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr or completed.stdout)
    return json.loads(completed.stdout)


def dogfood_payload() -> dict[str, object]:
    return {
        "schema_version": "dev-flow.dogfood.observations.v1",
        "observations": [
            {
                "task_shape": "review",
                "dev_flow_expected": True,
                "transitions": ["review-to-verification"],
                "corrections": ["method-realization-added"],
                "scope": {"mode": "bounded", "conformed": True},
                "method": {
                    "eligible": True,
                    "activated": True,
                    "selected": True,
                    "readiness": "ready",
                    "disposition": "execute-ready",
                    "realized": True,
                    "evidence_effect": "oracle-changed",
                },
            },
            {
                "task_shape": "ordinary-conversation",
                "dev_flow_expected": False,
                "transitions": ["none"],
                "corrections": ["none"],
                "scope": {"mode": "not-applicable", "conformed": True},
                "method": {
                    "eligible": False,
                    "activated": False,
                    "selected": False,
                    "readiness": "not-applicable",
                    "disposition": "not-applicable",
                    "realized": False,
                    "evidence_effect": "not-observed",
                },
            },
        ],
    }


def dogfood_v2_payload() -> dict[str, object]:
    payload = dogfood_payload()
    payload["schema_version"] = "dev-flow.dogfood.observations.v2"
    for index, observation in enumerate(payload["observations"]):
        observation["rc4"] = {
            "route": {
                "initial": 1 if index == 0 else 0,
                "material_transitions": 1 if index == 0 else 0,
                "delta_routes": 1 if index == 0 else 0,
                "unchanged_routes": 0,
            },
            "convergence": {
                "checkpoint_required": index == 0,
                "checkpoint_resolved": index == 0,
                "third_tweak": False,
            },
            "resource": {
                "preflight": "passed" if index == 0 else "not-run",
                "lease": "conflict" if index == 0 else "none",
            },
            "workstream": {
                "check": "failed" if index == 0 else "not-applicable",
                "contradictions": ["open-hard-condition"] if index == 0 else [],
            },
            "test_system": {
                "eligible": index == 0,
                "activated": index == 0,
                "negative_control": "failed-as-expected" if index == 0 else "not-run",
            },
            "evidence_status": "passed" if index == 0 else "not-run",
        }
    return payload


class ScopeAndContinuationContracts(unittest.TestCase):
    def test_scope_envelope_keeps_depth_separate_from_breadth(self) -> None:
        guidance = QUALITY.read_text(encoding="utf-8")
        for phrase in (
            "Scope envelope and convergence",
            "Implementation and repair default to `closed`",
            "Diagnosis and review default to `bounded`",
            "`Open` exploration requires an explicit breadth request",
            "reasoning effort, or method count never changes the discovery mode",
            "`required defect`",
            "`necessary enabler`",
            "`optional opportunity`",
            "Reconcile the final diff",
        ):
            self.assertIn(phrase, guidance)

    def test_auxiliary_repairs_have_a_cumulative_convergence_checkpoint(self) -> None:
        guidance = QUALITY.read_text(encoding="utf-8")
        for phrase in (
            "Auxiliary-mechanism convergence",
            "two consecutive repairs",
            "primary terminal condition",
            "do not make a third tweak",
            "simplify or replace",
            "explicitly asks for continued exploration",
        ):
            self.assertIn(phrase, guidance)

        catalog = json.loads(TRANSITIONS.read_text(encoding="utf-8"))
        case = next(
            item
            for item in catalog["cases"]
            if item["id"] == "CONTINUATION-AUXILIARY-CONVERGENCE"
        )
        final_turn = case["turns"][-1]
        self.assertIn("auxiliary-convergence-checkpoint", final_turn["expected"])
        self.assertIn("simpler-fallback", final_turn["expected"])
        self.assertIn("third-auxiliary-tweak", final_turn["forbidden"])
        for turn in case["turns"]:
            self.assertEqual(turn["mutation"], "none")
            self.assertIn(
                "Respond with the decision only; do not modify repository files.",
                turn["prompt"],
            )

    def test_delegation_is_monotonically_narrowed_and_root_verified(self) -> None:
        guidance = ORCHESTRATION.read_text(encoding="utf-8")
        for phrase in (
            "subset of the parent envelope",
            "intersection of all ancestor",
            "cannot restore authority",
            "bounded expansion request",
            "successful dispatch returns a non-empty child identity",
            "empty receiver list or empty agent state is not delegation",
            "never attribute a result to a child",
            "actual returned writes",
            "compliant report never overrides an out-of-scope diff",
        ):
            self.assertIn(phrase, guidance)

        active = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "successful dispatch returns a non-empty child/receiver identity",
            "Never call `wait` or poll unless",
            "never attribute a result to a child",
        ):
            self.assertIn(phrase, active)

    def test_task_history_and_process_adapters_have_negative_boundaries(self) -> None:
        guidance = ADAPTERS.read_text(encoding="utf-8")
        for phrase in (
            "Explicit task history",
            "Process supervision",
            "read every named task",
            "do not start duplicate unchanged work",
            "Do not ambiently scan, rank, merge, archive, or modify tasks",
            "analogy repository",
            "Do not retry while task identity, host connection, tool availability, and user request are unchanged",
            "One bounded retry is allowed only after one of those facts changes",
            "Silent omission and analogy-based contract invention do not pass",
        ):
            self.assertIn(phrase, guidance)

        orchestration = ORCHESTRATION.read_text(encoding="utf-8")
        self.assertIn("explicit renewed authority", orchestration)
        self.assertIn("must not execute that expansion merely because the child requested it", orchestration)


class MethodDispositionContracts(unittest.TestCase):
    def test_method_pair_contract_is_bounded_fixed_and_non_scoring(self) -> None:
        catalog = json.loads(METHOD_PAIRS.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], "method.marginal-utility.catalog.v1")
        self.assertFalse(catalog["execution"]["live_execution"])
        self.assertTrue(catalog["execution"]["requires_separate_model_budget"])
        self.assertEqual(
            catalog["execution"]["conditions"],
            ["without-method", "with-method"],
        )
        self.assertGreaterEqual(
            catalog["execution"]["minimum_first_attempts_per_condition"], 3
        )
        self.assertIsNone(catalog["aggregate_score"])
        self.assertEqual(len(catalog["cases"]), 3)
        method_ids = {
            item["id"]
            for item in json.loads(METHOD_POOL.read_text(encoding="utf-8"))["methods"]
        }
        case_ids = set()
        for case in catalog["cases"]:
            self.assertNotIn(case["id"], case_ids)
            case_ids.add(case["id"])
            self.assertIn(case["method_candidate"], method_ids)
            self.assertEqual(
                set(case["fixed_conditions"]),
                {
                    "requirement",
                    "repository_fixture",
                    "model_identity",
                    "tool_identity",
                    "skill_identity",
                    "acceptance_oracle",
                },
            )
            self.assertTrue(all(case["fixed_conditions"].values()))
            self.assertTrue(case["protected_negative"])

    def test_review_oracle_challenge_prefers_ready_verification(self) -> None:
        payload = route(
            "--intent",
            "review",
            "--risk",
            "weak-tests",
            "--method-signal",
            "oracle-challenge",
            "--method-prerequisite",
            "test-oracle",
            "--method-prerequisite",
            "stable-contract",
        )
        selection = payload["capability_activation"]["method"]["selection"]
        self.assertEqual(selection["phase"], "verification")
        self.assertTrue(selection["selected"])
        self.assertNotEqual(selection["selected"], ["n-version-independent-derivation"])
        self.assertEqual(selection["selection_count_is_quality"], False)
        self.assertIn("execute-ready-method", selection["disposition_options"])

    def test_ready_projection_is_actionable_and_blocked_projection_is_honest(self) -> None:
        ready_payload = route(
            "--intent",
            "review",
            "--risk",
            "weak-tests",
            "--method-prerequisite",
            "test-oracle",
        )
        guidance = ready_payload["capability_activation"]["method"]["selection"]["guidance"][0]
        self.assertEqual(guidance["disposition"], "ready")
        for field in (
            "owner",
            "why",
            "avoid_when",
            "required_prerequisites",
            "cost",
            "expected_outputs",
            "minimum_action",
            "steps",
            "evidence",
            "fallback",
            "limitations",
        ):
            self.assertIn(field, guidance)

        blocked_payload = route("--intent", "change", "--risk", "privacy")
        blocked = blocked_payload["capability_activation"]["method"]["selection"]["blocked"][0]
        self.assertEqual(blocked["disposition"], "blocked")
        self.assertTrue(blocked["missing_prerequisites"])
        self.assertTrue(blocked["fallback"])
        self.assertTrue(blocked["limitations"])

    def test_observed_prerequisite_can_move_blocked_method_to_ready(self) -> None:
        blocked = route("--intent", "change", "--risk", "privacy")
        blocked_selection = blocked["capability_activation"]["method"]["selection"]
        self.assertIn(
            "linddun-privacy-model",
            {item["method"] for item in blocked_selection["blocked"]},
        )
        ready = route(
            "--intent",
            "change",
            "--risk",
            "privacy",
            "--method-prerequisite",
            "privacy-data-map",
        )
        ready_selection = ready["capability_activation"]["method"]["selection"]
        self.assertIn("linddun-privacy-model", ready_selection["selected"])


class DogfoodContracts(unittest.TestCase):
    def run_analyzer(self, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "observations.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return subprocess.run(
                [sys.executable, str(DOGFOOD), str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

    def test_analyzer_emits_only_aggregate_funnel_without_score(self) -> None:
        completed = self.run_analyzer(dogfood_payload())
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["totals"]["observations"], 2)
        self.assertEqual(result["totals"]["negative_controls"], 1)
        self.assertEqual(result["method_funnel"]["eligible"], 1)
        self.assertEqual(result["method_funnel"]["realized"], 1)
        self.assertIsNone(result["aggregate_score"])
        self.assertFalse(result["privacy"]["raw_content_retained"])
        self.assertFalse(result["privacy"]["stable_identifiers_retained"])

    def test_analyzer_rejects_raw_content_and_stable_identifier_fields(self) -> None:
        for field, value in (
            ("transcript", "raw task text"),
            ("task_id", "stable-id"),
            ("path", "/Users/example/private/repo"),
            ("productivity_score", 99),
        ):
            with self.subTest(field=field):
                payload = dogfood_payload()
                payload["observations"][0][field] = value
                completed = self.run_analyzer(payload)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("forbidden", completed.stdout)

    def test_v2_adds_bounded_rc4_funnels_without_changing_v1(self) -> None:
        v1 = json.loads(self.run_analyzer(dogfood_payload()).stdout)
        completed = self.run_analyzer(dogfood_v2_payload())
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        v2 = json.loads(completed.stdout)
        self.assertEqual(v1["schema_version"], "dev-flow.dogfood.aggregate.v1")
        self.assertNotIn("rc4", v1)
        self.assertEqual(v2["schema_version"], "dev-flow.dogfood.aggregate.v2")
        self.assertEqual(v2["rc4"]["route"]["delta_routes"], 1)
        self.assertEqual(v2["rc4"]["resource"]["lease"]["conflict"], 1)
        self.assertIsNone(v2["aggregate_score"])

    def test_v2_rejects_content_fields_and_composite_scores(self) -> None:
        for field, value in (("prompt", "private"), ("path", "/private/repo"), ("score", 1)):
            with self.subTest(field=field):
                payload = dogfood_v2_payload()
                payload["observations"][0]["rc4"][field] = value
                completed = self.run_analyzer(payload)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("exact aggregate-safe v2 schema", completed.stdout)

    def test_ordinary_conversation_cannot_activate_dev_flow(self) -> None:
        payload = dogfood_payload()
        ordinary = payload["observations"][1]
        ordinary["dev_flow_expected"] = True
        completed = self.run_analyzer(payload)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("negative control", completed.stdout)


if __name__ == "__main__":
    unittest.main()
