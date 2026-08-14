#!/usr/bin/env python3
"""Deterministic contracts for the assurance methodology pool and selector."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_ROOT = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPT_ROOT))

import methodology_system  # noqa: E402


FLOW = SCRIPT_ROOT / "dev-flow.py"
REGISTRY = ROOT / "governance" / "methodology-pool.json"


def run_flow(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FLOW), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class MethodologySystemContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = methodology_system.read_registry(REGISTRY)
        cls.all_available = cls.pool["vocabulary"]["prerequisites"]

    def select(
        self,
        *,
        phase: str,
        task_type: str = "large-feature",
        risks: list[str] | None = None,
        signals: list[str] | None = None,
        available: list[str] | None = None,
        depth: str = "deep",
        max_methods: int | None = None,
    ) -> dict[str, object]:
        return methodology_system.select_methods(
            self.pool,
            repository_root=ROOT,
            phase=phase,
            task_type=task_type,
            risks=risks or [],
            signals=signals or [],
            available=self.all_available if available is None else available,
            depth=depth,
            max_methods=max_methods,
        )

    @staticmethod
    def selected_ids(result: dict[str, object]) -> set[str]:
        return {
            item["id"]
            for item in result["selected_methods"]  # type: ignore[index]
        }

    @staticmethod
    def excluded_by_id(result: dict[str, object], method_id: str) -> list[dict[str, object]]:
        return [
            entry
            for entry in result["excluded_methods"]  # type: ignore[index]
            if entry["method_id"] == method_id
        ]

    def test_canonical_pool_is_valid_broad_and_source_grounded(self) -> None:
        self.assertEqual(
            methodology_system.validate_registry(self.pool, repository_root=ROOT),
            [],
        )
        self.assertEqual(len(self.pool["methods"]), 111)
        self.assertEqual(len(self.pool["sources"]), 67)
        self.assertEqual(len(self.pool["risk_models"]), 32)
        self.assertEqual(
            set(self.pool["selection_contract"]["phase_order"]),
            {
                "discovery",
                "requirements",
                "design",
                "implementation",
                "diagnosis",
                "verification",
                "review",
                "acceptance",
                "delivery",
                "operations",
            },
        )
        for phase in self.pool["selection_contract"]["phase_order"]:
            foundations = [
                method
                for method in self.pool["methods"]
                if method["selection"] == "foundation" and phase in method["phases"]
            ]
            self.assertGreaterEqual(len(foundations), 1, phase)

    def test_validator_rejects_missing_safety_metadata_and_dangling_graph_edges(self) -> None:
        missing_negative = copy.deepcopy(self.pool)
        missing_negative["methods"][0]["negative_trigger"] = ""
        self.assertTrue(
            any(
                "negative_trigger must be a non-empty string" in error
                for error in methodology_system.validate_registry(missing_negative)
            )
        )

        dangling_source = copy.deepcopy(self.pool)
        dangling_source["methods"][0]["source_ids"] = ["SRC-DOES-NOT-EXIST"]
        errors = methodology_system.validate_registry(dangling_source)
        self.assertTrue(any("references unknown source" in error for error in errors))

        dangling_method = copy.deepcopy(self.pool)
        dangling_method["risk_models"][0]["method_ids"].append("unknown-method")
        errors = methodology_system.validate_registry(dangling_method)
        self.assertTrue(any("references unknown method" in error for error in errors))

        broken_guidance = copy.deepcopy(self.pool)
        broken_guidance["methods"][0]["guidance_ref"] = "skills/dev-flow/references/missing.md"
        errors = methodology_system.validate_registry(broken_guidance, repository_root=ROOT)
        self.assertTrue(any("guidance_ref does not exist" in error for error in errors))

    def test_cli_validation_reports_current_inventory(self) -> None:
        completed = run_flow("validate-methods")
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual((payload["methods"], payload["sources"], payload["risk_models"]), (111, 67, 32))

    def test_low_risk_routine_selects_only_phase_foundation(self) -> None:
        result = self.select(
            phase="implementation",
            task_type="routine",
            risks=[],
            signals=["low-risk-routine"],
            depth="formal",
        )
        self.assertEqual(self.selected_ids(result), {"coherent-vertical-slice"})
        self.assertEqual(result["reasoning_model"]["matched_risk_models"], [])  # type: ignore[index]
        self.assertFalse(result["context_budget"]["full_pool_loaded_into_working_set"])  # type: ignore[index]

    def test_identity_migration_escalates_from_ledger_to_alloy_only_at_formal_depth(self) -> None:
        common = {
            "phase": "requirements",
            "task_type": "migration",
            "risks": ["migration"],
            "signals": ["cross-boundary-identity", "multi-version-coexistence"],
        }
        deep = self.select(**common, depth="deep")
        self.assertIn("ontology-identity-ledger", self.selected_ids(deep))
        self.assertNotIn("alloy-relational-model", self.selected_ids(deep))
        self.assertEqual(self.excluded_by_id(deep, "alloy-relational-model")[0]["status"], "depth-excluded")

        formal = self.select(**common, depth="formal")
        self.assertIn("alloy-relational-model", self.selected_ids(formal))

    def test_feature_interaction_selects_decision_state_and_combinatorial_methods(self) -> None:
        result = self.select(
            phase="verification",
            signals=["interacting-features", "high-configuration"],
            depth="deep",
        )
        selected = self.selected_ids(result)
        self.assertTrue({"decision-table", "state-transition-model", "combinatorial-tway-testing"}.issubset(selected))
        self.assertNotIn("petri-net-process-model", selected)

    def test_temporal_concurrency_requires_formal_depth_for_tla(self) -> None:
        common = {
            "phase": "design",
            "risks": ["concurrency"],
            "signals": ["temporal-progress", "fairness-required"],
        }
        deep = self.select(**common, depth="deep")
        self.assertIn("state-transition-model", self.selected_ids(deep))
        self.assertNotIn("tla-temporal-model", self.selected_ids(deep))
        formal = self.select(**common, depth="formal")
        self.assertIn("tla-temporal-model", self.selected_ids(formal))

    def test_public_contract_migration_selects_coexistence_and_compatibility_evidence(self) -> None:
        implementation = self.select(
            phase="implementation",
            task_type="migration",
            risks=["public-api"],
            signals=["multi-version-coexistence", "public-contract-change"],
            depth="starter",
        )
        self.assertIn("parallel-change-expand-contract", self.selected_ids(implementation))

        verification = self.select(
            phase="verification",
            task_type="migration",
            risks=["public-api"],
            signals=["multi-version-coexistence", "behavior-preservation"],
            depth="deep",
        )
        self.assertTrue(
            {"contract-consumer-testing", "differential-testing", "compatibility-matrix"}.issubset(
                self.selected_ids(verification)
            )
        )

    def test_weak_oracle_stack_and_missing_prerequisites_are_explicit(self) -> None:
        result = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["weak-oracle"],
            available=["requirement-baseline", "test-oracle"],
            depth="deep",
        )
        selected = self.selected_ids(result)
        self.assertIn("metamorphic-testing", selected)
        self.assertIn("property-based-testing", selected)
        blocked_ids = {entry["method_id"] for entry in result["blocked_methods"]}
        self.assertIn("differential-testing", blocked_ids)
        self.assertIn("mutation-testing", blocked_ids)
        self.assertEqual(result["status"], "selected-with-unresolved-prerequisites")
        self.assertTrue(result["unresolved"])

    def test_low_risk_negative_rule_suppresses_semantic_mutation_but_high_consequence_overrides(self) -> None:
        low = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["weak-oracle", "low-risk-routine"],
            depth="formal",
            max_methods=14,
        )
        exclusion = self.excluded_by_id(low, "semantic-mutation-testing")[0]
        self.assertEqual(exclusion["status"], "negative-triggered")
        self.assertIn("NEG-LOW-RISK-FORMAL", exclusion["matched_global_rules"])

        high = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["weak-oracle", "low-risk-routine", "high-consequence"],
            depth="formal",
            max_methods=30,
        )
        self.assertIn("semantic-mutation-testing", self.selected_ids(high))

    def test_security_privacy_safety_performance_ux_and_agent_scenarios(self) -> None:
        security = self.select(
            phase="design",
            task_type="security",
            risks=["security"],
            signals=["adversarial-input"],
            depth="deep",
        )
        self.assertTrue({"stride-threat-model", "attack-tree"}.issubset(self.selected_ids(security)))

        privacy = self.select(
            phase="design",
            risks=["privacy"],
            signals=["privacy-data-flow"],
            depth="deep",
        )
        self.assertTrue({"data-lineage-provenance", "linddun-privacy-model"}.issubset(self.selected_ids(privacy)))

        safety = self.select(
            phase="review",
            signals=["safety-hazard", "high-consequence"],
            depth="formal",
            max_methods=30,
        )
        self.assertTrue({"fmea-fta", "stpa-control-analysis", "gsn-assurance-case"}.issubset(self.selected_ids(safety)))

        performance = self.select(
            phase="verification",
            task_type="performance",
            risks=["performance"],
            signals=["performance-budget"],
            depth="deep",
        )
        self.assertIn("performance-load-stress-soak", self.selected_ids(performance))

        ux = self.select(
            phase="verification",
            risks=["accessibility"],
            signals=["uncertain-user-need"],
            depth="deep",
        )
        self.assertTrue(
            {"accessibility-conformance-testing", "moderated-usability-testing"}.issubset(
                self.selected_ids(ux)
            )
        )

        agent = self.select(
            phase="verification",
            signals=["ai-agent-task", "model-evaluation"],
            depth="deep",
        )
        self.assertTrue(
            {"agent-evaluation-design", "model-tool-identity-pinning", "eval-contamination-case-health"}.issubset(
                self.selected_ids(agent)
            )
        )
        self.assertNotIn("multiple-first-attempts", self.selected_ids(agent))

    def test_agent_autonomy_partial_observability_and_patch_overfit_stacks(self) -> None:
        autonomy = self.select(
            phase="design",
            signals=["autonomy-choice", "stable-workflow"],
            depth="deep",
            max_methods=30,
        )
        self.assertTrue(
            {"minimum-effective-autonomy", "human-agent-function-allocation"}.issubset(
                self.selected_ids(autonomy)
            )
        )

        belief = self.select(
            phase="discovery",
            signals=["partial-observability", "stale-observation"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("belief-state-active-information", self.selected_ids(belief))

        repair = self.select(
            phase="verification",
            task_type="bugfix",
            risks=["weak-tests"],
            signals=["ai-code-repair", "weak-oracle"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("counterexample-guided-repair", self.selected_ids(repair))

    def test_agent_context_side_effect_and_memory_controls(self) -> None:
        context = self.select(
            phase="design",
            task_type="security",
            risks=["security"],
            signals=["untrusted-context", "prompt-injection-exposure"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("instruction-data-provenance-taint", self.selected_ids(context))
        self.assertNotIn("agent-memory-lifecycle-governance", self.selected_ids(context))

        memory = self.select(
            phase="design",
            risks=["persisted-data"],
            signals=["persistent-agent-memory", "multi-user-state"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("agent-memory-lifecycle-governance", self.selected_ids(memory))

        effects = self.select(
            phase="design",
            risks=["recovery"],
            signals=[
                "agent-external-action",
                "external-side-effects",
                "multi-step-external-action",
                "irreversible-action",
            ],
            depth="deep",
            max_methods=30,
        )
        self.assertTrue(
            {
                "runtime-assurance-safety-shield",
                "saga-compensating-actions",
                "temporal-runtime-verification",
            }.issubset(self.selected_ids(effects))
        )
        self.assertNotIn("digital-twin-agent-simulation", self.selected_ids(effects))

        simulation = self.select(
            phase="design",
            risks=["unsafe"],
            signals=["unsafe-live-environment", "no-live-authority"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("digital-twin-agent-simulation", self.selected_ids(simulation))

    def test_formal_agent_calibration_and_dynamic_allocation_require_formal_depth(self) -> None:
        calibration = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["model-evaluation", "calibration-data", "high-consequence"],
            depth="formal",
            max_methods=30,
        )
        self.assertIn("conformal-risk-control-selective-action", self.selected_ids(calibration))

        uncalibrated = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["model-evaluation", "high-consequence"],
            depth="formal",
            max_methods=30,
        )
        self.assertNotIn("conformal-risk-control-selective-action", self.selected_ids(uncalibrated))

        allocation = self.select(
            phase="design",
            risks=["concurrency"],
            signals=["multi-agent-work", "heterogeneous-agents", "dynamic-task-allocation"],
            depth="formal",
            max_methods=30,
        )
        self.assertTrue(
            {"multi-agent-topology-ownership", "contract-net-task-allocation"}.issubset(
                self.selected_ids(allocation)
            )
        )

        deep = self.select(
            phase="design",
            risks=["concurrency"],
            signals=["multi-agent-work", "heterogeneous-agents", "dynamic-task-allocation"],
            depth="deep",
            max_methods=30,
        )
        self.assertNotIn("contract-net-task-allocation", self.selected_ids(deep))
        self.assertEqual(
            self.excluded_by_id(deep, "contract-net-task-allocation")[0]["status"],
            "depth-excluded",
        )

        generic = self.select(
            phase="design",
            risks=["concurrency"],
            signals=["multi-agent-work", "parallelizable-task"],
            depth="formal",
            max_methods=30,
        )
        self.assertIn("multi-agent-topology-ownership", self.selected_ids(generic))
        self.assertNotIn("contract-net-task-allocation", self.selected_ids(generic))

    def test_reactive_and_hierarchical_planning_do_not_collapse_into_generic_drift(self) -> None:
        reactive = self.select(
            phase="design",
            signals=["reactive-environment", "dynamic-environment"],
            depth="deep",
            max_methods=30,
        )
        self.assertIn("behavior-tree-reactive-execution", self.selected_ids(reactive))

        drift = self.select(
            phase="design",
            signals=["open-loop-drift", "long-running-agent"],
            depth="formal",
            max_methods=30,
        )
        self.assertNotIn("hierarchical-task-network-planning", self.selected_ids(drift))

        hierarchical = self.select(
            phase="design",
            signals=["hierarchical-task-domain", "repeated-domain-workflow"],
            depth="formal",
            max_methods=30,
        )
        self.assertIn("hierarchical-task-network-planning", self.selected_ids(hierarchical))

    def test_agent_methods_block_on_real_prerequisite_gaps(self) -> None:
        result = self.select(
            phase="design",
            risks=["recovery"],
            signals=["agent-external-action", "irreversible-action"],
            available=["requirement-baseline", "repository-facts"],
            depth="deep",
            max_methods=30,
        )
        blocked_ids = {entry["method_id"] for entry in result["blocked_methods"]}
        self.assertIn("runtime-assurance-safety-shield", blocked_ids)
        self.assertIn("saga-compensating-actions", blocked_ids)
        self.assertEqual(result["status"], "selected-with-unresolved-prerequisites")

        simulation = self.select(
            phase="design",
            signals=["unsafe-live-environment", "no-live-authority"],
            available=["requirement-baseline", "repository-facts"],
            depth="deep",
            max_methods=30,
        )
        simulation_blocked = {entry["method_id"] for entry in simulation["blocked_methods"]}
        self.assertIn("digital-twin-agent-simulation", simulation_blocked)

    def test_broad_risks_do_not_overtrigger_privacy_supply_chain_or_high_assurance(self) -> None:
        persisted = self.select(
            phase="design",
            risks=["persisted-data"],
            depth="deep",
        )
        persisted_models = {
            item["id"] for item in persisted["reasoning_model"]["matched_risk_models"]
        }
        self.assertNotIn("RM-PRIVACY-DATA", persisted_models)

        security = self.select(
            phase="design",
            task_type="security",
            risks=["security"],
            depth="formal",
        )
        security_models = {
            item["id"] for item in security["reasoning_model"]["matched_risk_models"]
        }
        self.assertNotIn("RM-SUPPLY-CHAIN", security_models)
        self.assertNotIn("RM-HIGH-CONSEQUENCE-ASSURANCE", security_models)

        deployment = self.select(
            phase="delivery",
            risks=["deployment"],
            depth="deep",
        )
        deployment_models = {
            item["id"] for item in deployment["reasoning_model"]["matched_risk_models"]
        }
        self.assertNotIn("RM-SUPPLY-CHAIN", deployment_models)

    def test_no_live_authority_excludes_live_experiments_and_preserves_plan_boundary(self) -> None:
        result = self.select(
            phase="delivery",
            task_type="release-hotfix",
            risks=["deployment"],
            signals=["rollout-risk", "no-live-authority"],
            depth="deep",
            max_methods=20,
        )
        selected = self.selected_ids(result)
        self.assertIn("rollout-readiness", selected)
        for method_id in (
            "fault-injection-chaos",
            "canary-progressive-delivery",
            "blue-green-shadow-traffic",
            "game-day-runbook",
        ):
            exclusion = self.excluded_by_id(result, method_id)[0]
            self.assertEqual(exclusion["status"], "negative-triggered")
            self.assertIn("NEG-NO-LIVE-AUTHORITY", exclusion["matched_global_rules"])
        self.assertIn("not proof or authority", result["assurance_boundary"])

    def test_context_cap_is_deterministic_and_never_loads_the_pool(self) -> None:
        result = self.select(
            phase="verification",
            risks=["weak-tests"],
            signals=["weak-oracle", "critical-calculation"],
            depth="formal",
            max_methods=2,
        )
        self.assertEqual(result["context_budget"]["selected"], 2)
        self.assertEqual(result["context_budget"]["pool_size"], 111)
        self.assertFalse(result["context_budget"]["full_pool_loaded_into_working_set"])
        self.assertTrue(
            any(entry["status"] == "context-cap-excluded" for entry in result["excluded_methods"])
        )

    def test_invalid_or_duplicate_inputs_fail_closed(self) -> None:
        with self.assertRaisesRegex(methodology_system.MethodologyContractError, "unknown signal"):
            self.select(phase="design", signals=["magic-method"])
        with self.assertRaisesRegex(methodology_system.MethodologyContractError, "duplicate risk"):
            self.select(phase="design", risks=["architecture", "architecture"])
        completed = run_flow(
            "select-methods",
            "--phase",
            "unknown",
            "--task-type",
            "routine",
        )
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(json.loads(completed.stdout)["status"], "invalid")

    def test_selector_rejects_dangling_guidance_for_custom_pool(self) -> None:
        broken = copy.deepcopy(self.pool)
        broken["methods"][0]["guidance_ref"] = "skills/dev-flow/references/missing.md"
        with self.assertRaisesRegex(methodology_system.MethodologyContractError, "guidance_ref does not exist"):
            methodology_system.select_methods(
                broken,
                repository_root=ROOT,
                phase="discovery",
                task_type="routine",
                risks=[],
                signals=[],
                available=self.all_available,
                depth="starter",
            )

    def test_cli_output_is_byte_stable_and_sorted_for_equivalent_calls(self) -> None:
        args = (
            "select-methods",
            "--phase",
            "verification",
            "--task-type",
            "large-feature",
            "--risk",
            "weak-tests",
            "--signal",
            "weak-oracle",
            "--available",
            "requirement-baseline",
            "--available",
            "test-oracle",
            "--depth",
            "deep",
        )
        first = run_flow(*args)
        second = run_flow(*args)
        self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
        self.assertEqual(first.stdout, second.stdout)
        payload = json.loads(first.stdout)
        self.assertEqual(payload["request"]["risks"], sorted(payload["request"]["risks"]))
        self.assertEqual(payload["schema_version"], "method.selection.v1")

    def test_progressive_guidance_and_novice_template_are_linked(self) -> None:
        for method in self.pool["methods"]:
            self.assertTrue((ROOT / method["guidance_ref"]).is_file(), method["id"])
        for path in (
            "skills/dev-flow/references/methodology-system.md",
            "skills/dev-flow/templates/method-selection.md",
            "docs/methodology-pool.md",
        ):
            self.assertTrue((ROOT / path).is_file(), path)
        skill = (ROOT / "skills/dev-flow/SKILL.md").read_text(encoding="utf-8")
        orchestration = (ROOT / "skills/dev-flow/references/orchestration.md").read_text(encoding="utf-8")
        self.assertIn("run `select-methods`", skill)
        self.assertIn("methodology-system.md", skill)
        self.assertIn("observation → failure hypothesis → method → owner artifact → evidence", orchestration)


if __name__ == "__main__":
    unittest.main()
