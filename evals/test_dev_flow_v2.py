#!/usr/bin/env python3
"""Focused acceptance tests for the Dev Flow 2.0 operating model."""

from __future__ import annotations

import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
LEGACY_FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev_flow.py"
DEV_FLOW_SKILL = ROOT / "skills" / "dev-flow" / "SKILL.md"
QUALITY_CALIBRATION = ROOT / "skills" / "dev-flow" / "references" / "quality-calibration.md"
VERIFICATION_SKILL = ROOT / "skills" / "verification" / "SKILL.md"


def run_flow(*args: object, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FLOW), *(str(arg) for arg in args)],
        cwd=cwd or ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def route(*args: object) -> dict[str, object]:
    result = run_flow("route-task", *args)
    if result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class RuntimeGuidanceContractTests(unittest.TestCase):
    def test_failure_isolation_is_non_persistent_and_change_sensitive(self) -> None:
        guidance = QUALITY_CALIBRATION.read_text(encoding="utf-8")
        for phrase in (
            "transient",
            "invariant",
            "authority",
            "external",
            "observable readiness facts are unchanged",
            "continue unrelated safe repository-native checks",
            "do not add a readiness registry",
        ):
            self.assertIn(phrase, guidance)
        self.assertIn("Retry once when a relevant fact changes", guidance)

    def test_continuation_contract_has_semantic_checkpoint_and_negative_trigger(self) -> None:
        guidance = DEV_FLOW_SKILL.read_text(encoding="utf-8")
        continuation = QUALITY_CALIBRATION.read_text(encoding="utf-8")
        self.assertIn("semantic checkpoint", guidance)
        self.assertIn("never automatically creates a host task or worktree", guidance)
        self.assertIn("an unchanged narrow follow-up", guidance.lower())
        for phrase in (
            "affected Git roots",
            "user-owned changes",
            "stale evidence",
            "recommended next slice",
        ):
            self.assertIn(phrase, continuation)

    def test_evidence_freshness_distinguishes_affected_and_unrelated_edits(self) -> None:
        guidance = VERIFICATION_SKILL.read_text(encoding="utf-8")
        evidence = (
            ROOT / "skills" / "verification" / "references" / "evidence-contract.md"
        ).read_text(encoding="utf-8")
        self.assertIn("invalidates that PASS", evidence)
        self.assertIn("unrelated documentation-only edit", evidence)
        self.assertIn("fallback proves only its own narrower claim", guidance)


class RoutingTests(unittest.TestCase):
    def test_new_intent_is_primary_and_legacy_task_type_remains_compatible(self) -> None:
        current = route("--intent", "diagnose")
        self.assertEqual(current["intent"], "diagnose")
        self.assertEqual(current["intent_source"], "explicit-intent")
        self.assertIsNone(current["legacy_task_type"])
        self.assertEqual(current["mutation_intent"], "none")
        self.assertIn("systematic-debugging", [item["skill"] for item in current["routes"]])

        compatible = route("--task-type", "bugfix")
        self.assertEqual(compatible["intent"], "change")
        self.assertEqual(compatible["intent_source"], "legacy-task-type:bugfix")
        self.assertEqual(compatible["legacy_task_type"], "bugfix")
        self.assertEqual(compatible["mutation_intent"], "persistent")
        self.assertIn("systematic-debugging", [item["skill"] for item in compatible["routes"]])

    def test_diagnosis_is_an_allowlisted_intent_alias(self) -> None:
        payload = route("--intent", "diagnosis")
        self.assertEqual(payload["intent"], "diagnose")
        self.assertEqual(payload["intent_source"], "alias-intent:diagnosis")
        self.assertIn("systematic-debugging", [item["skill"] for item in payload["routes"]])

        inline = route("--intent=diagnosis", "--compact")
        self.assertEqual(inline["intent"], "diagnose")

    def test_documented_route_value_errors_are_structured_and_replayable(self) -> None:
        invalid_values = {
            "--intent": "diagnoise",
            "--requirement-class": "structural-adjusment",
            "--ui-impact": "preserv",
            "--method-depth": "depp",
            "--mutation": "persistnt",
            "--unknown": "compatiblity",
            "--work-mode": "managd",
            "--knowledge-impact": "current-trut",
            "--overlay": "migraton",
        }
        for option, invalid_value in invalid_values.items():
            with self.subTest(option=option):
                completed = run_flow(
                    "route-task",
                    "--intent",
                    "change",
                    option,
                    invalid_value,
                    "--multi-session",
                    "--compact",
                )
                self.assertEqual(completed.returncode, 2)
                self.assertNotIn("usage:", completed.stderr.lower())
                payload = json.loads(completed.stdout)
                self.assertEqual(payload["status"], "invalid")
                self.assertIsNotNone(payload["corrected_command"])
                replay = subprocess.run(
                    shlex.split(payload["corrected_command"]),
                    cwd=ROOT.parent,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(replay.returncode, 0, replay.stderr or replay.stdout)
                replayed = json.loads(replay.stdout)
                self.assertEqual(replayed["work_mode"], "managed")

    def test_route_programmer_syntax_errors_remain_argparse_diagnostics(self) -> None:
        for args in (
            ("--unknown-option", "value"),
            ("--intent",),
            ("--unknown-option", "value", "--intent", "diagnoise"),
            ("--intent", "--ui-impact", "preserv"),
            ("--intent", "diagnoise", "--task-type", "routine"),
        ):
            with self.subTest(args=args):
                completed = run_flow("route-task", *args)
                self.assertEqual(completed.returncode, 2)
                self.assertIn("usage:", completed.stderr.lower())
                self.assertEqual(completed.stdout, "")

    def test_every_legacy_task_type_has_a_valid_orthogonal_route(self) -> None:
        expected = {
            "micro": "change",
            "routine": "change",
            "bugfix": "change",
            "large-feature": "change",
            "large-refactor": "change",
            "migration": "change",
            "security": "change",
            "performance": "change",
            "release-hotfix": "delivery",
            "read-only-audit": "review",
            "spike": "design",
            "dependency-change": "change",
            "rollback": "delivery",
        }
        for task_type, intent in expected.items():
            with self.subTest(task_type=task_type):
                payload = route("--task-type", task_type)
                self.assertEqual(payload["intent"], intent)

    def test_routine_persistent_work_is_direct_and_packet_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            before = list(root.iterdir())
            payload = route("--task-type", "routine", "--mutation", "persistent")
            self.assertEqual(payload["work_mode"], "direct")
            self.assertEqual(payload["risk_overlays"], [])
            self.assertEqual([item["skill"] for item in payload["routes"]], ["repo-context", "verification"])
            self.assertFalse(payload["continuity"]["documents_required"])
            self.assertEqual(list(root.iterdir()), before)

    def test_direct_work_can_request_durable_knowledge_without_managed_state(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--knowledge-impact",
            "current-truth",
            "--knowledge-impact",
            "change-record",
        )
        self.assertEqual(payload["work_mode"], "direct")
        self.assertFalse(payload["continuity"]["documents_required"])
        self.assertEqual(payload["knowledge"]["disposition"], ["current-truth", "change-record"])
        self.assertEqual(payload["knowledge"]["default_change_record_path"], "docs/change-notes/<slug>.md")
        self.assertFalse(payload["knowledge"]["artifact_created"])

    def test_managed_workstream_supersedes_separate_change_record(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--multi-session",
            "--knowledge-impact",
            "change-record",
            "--knowledge-impact",
            "current-truth",
        )
        self.assertEqual(payload["work_mode"], "managed")
        self.assertEqual(payload["knowledge"]["disposition"], ["workstream", "current-truth"])
        self.assertEqual(payload["knowledge"]["superseded"], ["change-record:managed-workstream"])

    def test_none_knowledge_impact_cannot_hide_a_durable_impact(self) -> None:
        result = run_flow(
            "route-task",
            "--intent",
            "change",
            "--knowledge-impact",
            "none",
            "--knowledge-impact",
            "current-truth",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot be combined", result.stdout)

    def test_managed_mode_is_selected_by_continuity(self) -> None:
        payload = route("--task-type", "large-feature", "--multi-session", "--multi-slice")
        self.assertEqual(payload["work_mode"], "managed")
        self.assertTrue(payload["continuity"]["documents_required"])
        self.assertEqual(payload["continuity"]["artifacts"], ["implementation.md", "progress.md"])
        self.assertEqual(
            payload["continuity"]["conditional_artifacts"],
            ["requirements.md", "design.md", "decisions.md"],
        )
        self.assertIsNone(payload["quality_calibration"]["artifact"])
        self.assertIn("first-surprising-failure", payload["quality_calibration"]["recheck_on"])
        self.assertIn("route-agent", payload["delegation"])

    def test_managed_continuity_alone_does_not_imply_requirements(self) -> None:
        review = route("--intent", "review", "--multi-session")
        self.assertEqual(review["work_mode"], "managed")
        self.assertNotIn("requirements-design", [item["skill"] for item in review["routes"]])

        semantic = route(
            "--intent",
            "change",
            "--multi-session",
            "--requirement-class",
            "semantic-change",
            "--understanding-confirmed",
        )
        self.assertIn("requirements-design", [item["skill"] for item in semantic["routes"]])

    def test_persisted_data_alone_does_not_imply_migration_overlay(self) -> None:
        local_state = route("--intent", "change", "--risk", "persisted-data")
        self.assertNotIn("migration", [item["overlay"] for item in local_state["risk_overlays"]])
        self.assertIn("signal:state-lifecycle", local_state["capability_activation"]["method"]["reasons"])

        for companion in ("schema", "version-compatibility", "rollback"):
            with self.subTest(companion=companion):
                payload = route(
                    "--intent",
                    "change",
                    "--risk",
                    "persisted-data",
                    "--risk",
                    companion,
                )
                self.assertIn("migration", [item["overlay"] for item in payload["risk_overlays"]])

        data_loss = route("--intent", "change", "--risk", "data-loss")
        self.assertIn("migration", [item["overlay"] for item in data_loss["risk_overlays"]])

    def test_design_intent_and_durable_plan_are_independent(self) -> None:
        direct = route("--intent", "design")
        self.assertEqual(direct["work_mode"], "direct")
        self.assertIn("requirements-design", [item["skill"] for item in direct["routes"]])
        self.assertEqual(direct["requirement_understanding"]["class"], "semantic-change")
        self.assertFalse(direct["requirement_understanding"]["design_allowed"])
        self.assertEqual(
            direct["requirement_understanding"]["next_action"],
            "publish-detailed-understanding-and-stop",
        )

        managed = route("--intent", "design", "--durable-plan")
        self.assertEqual(managed["work_mode"], "managed")
        self.assertIn("durable-plan", managed["work_mode_reasons"])
        self.assertTrue(managed["requirement_understanding"]["durable_requirement_source"])

    def test_semantic_change_requires_default_mode_confirmation_before_design(self) -> None:
        pending = route(
            "--intent",
            "change",
            "--requirement-class",
            "semantic-change",
        )
        understanding = pending["requirement_understanding"]
        self.assertTrue(understanding["detailed_output"])
        self.assertTrue(understanding["confirmation_required"])
        self.assertEqual(understanding["confirmation"], "required")
        self.assertFalse(understanding["design_allowed"])
        self.assertEqual(understanding["stop_before"], "technical-design")
        self.assertIn("remain in Default mode", understanding["rules"])
        self.assertIn("requirements-design", [item["skill"] for item in pending["routes"]])

        confirmed = route(
            "--intent",
            "change",
            "--requirement-class",
            "semantic-change",
            "--understanding-confirmed",
        )
        self.assertEqual(confirmed["requirement_understanding"]["confirmation"], "confirmed")
        self.assertEqual(confirmed["requirement_understanding"]["class"], "semantic-change")
        self.assertTrue(confirmed["requirement_understanding"]["design_allowed"])
        self.assertEqual(confirmed["requirement_understanding"]["next_action"], "continue")

        help_result = run_flow("route-task", "--help")
        self.assertIn("retain semantic-change and continue", help_result.stdout)

    def test_explicit_waiver_allows_design_without_an_approval_record(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--requirement-class",
            "semantic-change",
            "--waive-understanding-confirmation",
        )
        understanding = payload["requirement_understanding"]
        self.assertEqual(understanding["confirmation"], "waived")
        self.assertTrue(understanding["design_allowed"])

    def test_established_defect_and_mechanical_work_skip_confirmation(self) -> None:
        defect = route("--task-type", "bugfix")
        self.assertEqual(defect["requirement_understanding"]["class"], "defect-correction")
        self.assertFalse(defect["requirement_understanding"]["confirmation_required"])
        self.assertTrue(defect["requirement_understanding"]["design_allowed"])

        mechanical = route("--task-type", "micro")
        self.assertEqual(mechanical["requirement_understanding"]["class"], "mechanical")
        self.assertFalse(mechanical["requirement_understanding"]["detailed_output"])
        self.assertEqual(mechanical["requirement_understanding"]["next_action"], "continue")

    def test_ambiguous_defect_upgrades_to_semantic_confirmation(self) -> None:
        payload = route(
            "--task-type",
            "bugfix",
            "--requirement-class",
            "defect-correction",
            "--ambiguity",
        )
        understanding = payload["requirement_understanding"]
        self.assertEqual(understanding["class"], "semantic-change")
        self.assertEqual(understanding["class_source"], "ambiguous-defect-upgrade")
        self.assertFalse(understanding["design_allowed"])

    def test_read_only_intents_do_not_acquire_a_requirements_confirmation(self) -> None:
        for intent in ("research", "review", "delivery"):
            with self.subTest(intent=intent):
                payload = route("--intent", intent)
                understanding = payload["requirement_understanding"]
                self.assertEqual(understanding["class"], "read-only")
                self.assertFalse(understanding["confirmation_required"])
                self.assertTrue(understanding["design_allowed"])

    def test_review_and_delivery_intents_route_to_distinct_owners(self) -> None:
        review = route("--intent", "review")
        review_routes = [item["skill"] for item in review["routes"]]
        self.assertIn("verification", review_routes)
        self.assertIn("change-review", review_routes)
        self.assertNotIn("delivery-readiness", review_routes)

        delivery = route("--intent", "delivery")
        delivery_routes = [item["skill"] for item in delivery["routes"]]
        self.assertIn("delivery-readiness", delivery_routes)
        self.assertIn("verification", delivery_routes)
        self.assertNotIn("change-review", delivery_routes)
        self.assertEqual([item["overlay"] for item in delivery["risk_overlays"]], ["release"])

    def test_architecture_risk_review_keeps_review_intent_and_loads_owner(self) -> None:
        payload = route("--intent", "review", "--risk", "ffi")
        self.assertEqual(payload["intent"], "review")
        self.assertFalse(payload["requirement_understanding"]["confirmation_required"])
        self.assertIn("architecture-decisions", [item["skill"] for item in payload["routes"]])

    def test_research_and_review_have_distinct_read_only_routes(self) -> None:
        research = route("--intent", "research")
        self.assertEqual([item["skill"] for item in research["routes"]], ["repo-context"])

        review = route("--intent", "review", "--risk", "security")
        review_routes = [item["skill"] for item in review["routes"]]
        self.assertEqual(review_routes, ["repo-context", "verification", "change-review"])
        self.assertNotIn("architecture-decisions", review_routes)

        legacy = route("--intent", "research-audit")
        self.assertEqual(legacy["intent"], "review")
        self.assertEqual(legacy["intent_source"], "legacy-intent:research-audit")

    def test_review_and_fix_must_use_change_with_review_need(self) -> None:
        invalid = run_flow("route-task", "--intent", "review", "--mutation", "persistent")
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("use change with --need review", invalid.stdout)

        change = route("--intent", "change", "--need", "review")
        self.assertEqual(change["mutation_intent"], "persistent")
        self.assertIn("change-review", [item["skill"] for item in change["routes"]])

    def test_security_is_an_overlay_not_a_mode_escalation(self) -> None:
        payload = route("--task-type", "routine", "--risk", "security")
        self.assertEqual(payload["work_mode"], "direct")
        self.assertEqual([item["overlay"] for item in payload["risk_overlays"]], ["security"])
        self.assertNotIn("architecture-decisions", [item["skill"] for item in payload["routes"]])
        self.assertNotIn("change-review", [item["skill"] for item in payload["routes"]])

    def test_material_security_exposure_adds_review_without_changing_mode(self) -> None:
        payload = route("--task-type", "routine", "--risk", "security", "--need", "review")
        self.assertEqual(payload["work_mode"], "direct")
        self.assertEqual([item["overlay"] for item in payload["risk_overlays"]], ["security"])
        self.assertNotIn("architecture-decisions", [item["skill"] for item in payload["routes"]])
        self.assertIn("change-review", [item["skill"] for item in payload["routes"]])

    def test_security_adds_architecture_only_when_requested(self) -> None:
        payload = route("--intent", "change", "--risk", "security", "--need", "architecture")
        self.assertIn("architecture-decisions", [item["skill"] for item in payload["routes"]])

    def test_high_leverage_risk_actively_matches_a_bounded_method(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--risk",
            "ffi",
            "--method-signal",
            "multi-version-coexistence",
        )
        activation = payload["capability_activation"]
        self.assertIsNone(activation["artifact"])
        self.assertEqual(
            activation["passes"],
            ["after-repository-discovery", "after-material-requirement-confirmation"],
        )
        self.assertTrue(activation["method"]["active_match_required"])
        self.assertIn("risk:ffi", activation["method"]["reasons"])
        self.assertIn("signal:multi-version-coexistence", activation["method"]["reasons"])
        self.assertEqual(activation["method"]["maximum_loaded_methods"], 3)
        self.assertFalse(activation["method"]["persisted"])
        selection = activation["method"]["selection"]
        self.assertEqual(selection["phase"], "implementation")
        self.assertEqual(selection["depth"], "deep")
        self.assertIn("RM-ABI-FFI-BOUNDARY", selection["matched_risk_models"])
        considered = set(selection["selected"]) | {
            item["method"] for item in selection["blocked"]
        }
        self.assertIn("cross-language-abi-contract", considered)
        self.assertNotIn("data-lineage-provenance", considered)
        self.assertLessEqual(len(considered), 3)

    def test_method_activation_selects_real_methods_when_prerequisites_exist(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--risk",
            "ffi",
            "--method-signal",
            "multi-version-coexistence",
            "--method-prerequisite",
            "repository-facts",
            "--method-prerequisite",
            "requirement-baseline",
            "--method-prerequisite",
            "boundary-inventory",
            "--method-prerequisite",
            "consumer-toolchain",
        )
        selection = payload["capability_activation"]["method"]["selection"]
        self.assertLessEqual(len(selection["selected"]), 3)
        self.assertIn("cross-language-abi-contract", selection["selected"])
        self.assertEqual(
            {item["method"] for item in selection["guidance"]},
            set(selection["selected"]),
        )
        self.assertFalse(selection["persisted"])

    def test_task_facing_method_aliases_normalize_to_canonical_signals(self) -> None:
        cases = {
            "concurrent-state-lifecycle": ["state-lifecycle"],
            "concurrency-ordering": ["state-lifecycle"],
            "cross-boundary-state": ["cross-participant-flow"],
            "distributed-state": ["cross-participant-flow", "state-lifecycle"],
            "migration-rollback": ["multi-version-coexistence"],
            "ordering-sensitive-concurrency": ["state-lifecycle"],
        }
        for alias, expected in cases.items():
            with self.subTest(alias=alias):
                payload = route(
                    "--intent",
                    "change",
                    "--method-signal",
                    alias,
                )
                normalization = payload["capability_activation"]["method"]["signal_normalization"]
                self.assertEqual(normalization["input"], [alias])
                self.assertEqual(normalization["canonical"], expected)
                self.assertEqual(normalization["derived_from_risks"], [])
                self.assertEqual(normalization["translations"][0]["kind"], "alias")

    def test_explicit_signal_is_supplemented_by_uncovered_risk_families(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--risk",
            "data-deletion",
            "--risk",
            "recovery",
            "--risk",
            "concurrency",
            "--method-signal",
            "migration-rollback",
        )
        method = payload["capability_activation"]["method"]
        self.assertEqual(
            method["signal_normalization"]["canonical"],
            ["multi-version-coexistence", "state-lifecycle"],
        )
        self.assertEqual(
            method["signal_normalization"]["derived_from_risks"],
            ["state-lifecycle"],
        )
        selection = method["selection"]
        self.assertEqual(selection["phase"], "design")
        considered = set(selection["selected"]) | {
            item["method"] for item in selection["blocked"]
        }
        self.assertIn("state-transition-model", considered)
        self.assertTrue(
            considered & {"branch-abstraction-feature-flag", "parallel-change-expand-contract"}
        )

    def test_risk_only_activation_derives_foundational_method_signal(self) -> None:
        payload = route("--intent", "change", "--risk", "concurrency")
        method = payload["capability_activation"]["method"]
        self.assertTrue(method["active_match_required"])
        self.assertEqual(
            method["signal_normalization"]["derived_from_risks"],
            ["state-lifecycle"],
        )
        self.assertIn("signal:state-lifecycle", method["reasons"])
        selection = method["selection"]
        self.assertEqual(selection["phase"], "design")
        self.assertEqual(selection["phase_source"], "signal-adjacent-owner")
        self.assertTrue(selection["actionable"])
        self.assertIn(
            "state-transition-model",
            set(selection["selected"]) | {item["method"] for item in selection["blocked"]},
        )

    def test_risk_signal_derivation_covers_each_foundational_family(self) -> None:
        cases = {
            "ordering": ["state-lifecycle"],
            "recovery": ["state-lifecycle"],
            "distributed-state": ["cross-participant-flow"],
            "migration": ["multi-version-coexistence"],
            "version-compatibility": ["multi-version-coexistence"],
            "rollback": ["multi-version-coexistence"],
            "security": ["trust-boundary"],
            "authorization": ["trust-boundary"],
            "privacy": ["trust-boundary"],
            "persisted-data": ["state-lifecycle"],
            "data-deletion": ["state-lifecycle"],
        }
        for risk, expected in cases.items():
            with self.subTest(risk=risk):
                payload = route("--intent", "change", "--risk", risk)
                derived = payload["capability_activation"]["method"]["signal_normalization"][
                    "derived_from_risks"
                ]
                self.assertEqual(derived, expected)

    def test_route_risk_alias_preserves_canonical_method_output(self) -> None:
        payload = route("--intent", "change", "--risk", "data-loss")
        normalization = payload["capability_activation"]["method"]["risk_normalization"]
        self.assertEqual(normalization["canonical"], ["persisted-data"])
        self.assertEqual(
            normalization["translations"],
            [{"input": "data-loss", "canonical": ["persisted-data"], "kind": "alias"}],
        )
        self.assertIn("migration", [item["overlay"] for item in payload["risk_overlays"]])

    def test_task_facing_route_aliases_preserve_canonical_output(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--requirement-class",
            "U3",
            "--risk",
            "external-system",
            "--repository-facts",
            "language=swift",
        )
        self.assertEqual(payload["requirement_understanding"]["class"], "defect-correction")
        normalization = payload["capability_activation"]["method"]["risk_normalization"]
        self.assertEqual(normalization["canonical"], ["external-write"])
        self.assertEqual(
            normalization["translations"],
            [{"input": "external-system", "canonical": ["external-write"], "kind": "alias"}],
        )

    def test_specialist_skill_need_aliases_preserve_canonical_output(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--requirement-class",
            "U1",
            "--need",
            "requirements-design",
            "--need",
            "systematic-debugging",
        )
        route_names = [item["skill"] for item in payload["routes"]]
        self.assertIn("requirements-design", route_names)
        self.assertIn("systematic-debugging", route_names)
        self.assertEqual(
            payload["need_normalization"],
            [
                {
                    "input": "requirements-design",
                    "canonical": "requirements",
                    "kind": "alias",
                },
                {
                    "input": "systematic-debugging",
                    "canonical": "diagnosis",
                    "kind": "alias",
                },
            ],
        )

    def test_invalid_need_returns_portable_semantics_preserving_correction(self) -> None:
        result = run_flow(
            "route-task",
            "--intent",
            "change",
            "--requirement-class",
            "U1",
            "--need",
            "requirement-design",
            "--compact",
        )
        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["suggestions"], {"requirement-design": ["requirements-design"]})
        corrected = subprocess.run(
            shlex.split(payload["corrected_command"]),
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(corrected.returncode, 0, corrected.stderr or corrected.stdout)
        corrected_payload = json.loads(corrected.stdout)
        self.assertEqual(corrected_payload["status"], "routed")
        self.assertIn("requirements-design", corrected_payload["routes"])

    def test_invalid_method_signal_returns_portable_semantics_preserving_correction(self) -> None:
        original = (
            "--intent",
            "change",
            "--risk",
            "concurrency",
            "--need",
            "review",
            "--ui-impact",
            "preserve",
            "--ambiguity",
            "--material-exposure",
            "--independent-review-authorized",
            "--repo-fact",
            "language=python",
            "--effective-skill",
            "dev-flow:verification",
            "--method-signal",
            "concurreny-ordering",
            "--method-prerequisite",
            "stable-contract",
            "--method-depth",
            "deep",
            "--requirement-class",
            "structural-adjustment",
            "--understanding-confirmed",
            "--profile-operation",
            "--suite-maintenance",
            "--mutation",
            "persistent",
            "--unknown",
            "data",
            "--work-mode",
            "managed",
            "--multi-session",
            "--multi-slice",
            "--cross-module",
            "--coordination",
            "--material-tradeoff",
            "--durable-plan",
            "--knowledge-impact",
            "current-truth",
            "--overlay",
            "external-system",
        )
        help_result = run_flow("route-task", "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr or help_result.stdout)
        public_options = set(re.findall(r"--[a-z][a-z-]*", help_result.stdout))
        replayed_options = {value for value in original if value.startswith("--")}
        replayed_options.update(
            {
                "--help",
                "--task-type",
                "--repository-fact",
                "--repository-facts",
                "--waive-understanding-confirmation",
                "--previous-route",
                "--compact",
                "--explain",
            }
        )
        self.assertEqual(public_options, replayed_options)
        completed = run_flow(
            "route-task",
            *original,
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["suggestions"]["concurreny-ordering"], ["concurrency-ordering"])
        self.assertEqual(
            payload["method_signal_aliases"]["concurrency-ordering"],
            ["state-lifecycle"],
        )
        corrected_argv = shlex.split(payload["corrected_command"])
        self.assertEqual(Path(corrected_argv[1]), FLOW)
        self.assertIn("--method-signal", corrected_argv)
        self.assertIn("concurrency-ordering", corrected_argv)
        self.assertIn("--multi-session", corrected_argv)
        self.assertIn("--material-exposure", corrected_argv)
        self.assertIn("stable-contract", corrected_argv)
        self.assertIn("--method-depth", corrected_argv)
        with tempfile.TemporaryDirectory() as temp:
            corrected = subprocess.run(
                corrected_argv,
                cwd=Path(temp),
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(corrected.returncode, 0, corrected.stderr or corrected.stdout)
        expected = run_flow(
            "route-task",
            *("concurrency-ordering" if value == "concurreny-ordering" else value for value in original),
        )
        self.assertEqual(expected.returncode, 0, expected.stderr or expected.stdout)
        self.assertEqual(json.loads(corrected.stdout), json.loads(expected.stdout))
        self.assertIn("Use --risk", payload["risk_signal_guidance"])

        legacy = run_flow(
            "route-task",
            "--task-type",
            "bugfix",
            "--method-signal",
            "concurreny-ordering",
            "--compact",
        )
        legacy_payload = json.loads(legacy.stdout)
        self.assertEqual(legacy.returncode, 2)
        legacy_argv = shlex.split(legacy_payload["corrected_command"])
        self.assertIn("--task-type", legacy_argv)
        self.assertIn("bugfix", legacy_argv)
        self.assertIn("--compact", legacy_argv)
        legacy_replay = subprocess.run(
            legacy_argv,
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(legacy_replay.returncode, 0, legacy_replay.stderr or legacy_replay.stdout)

    def test_invalid_risk_returns_bounded_correction_contract(self) -> None:
        completed = run_flow(
            "route-task",
            "--intent",
            "change",
            "--risk",
            "concurency",
            "--multi-session",
            "--compact",
        )
        self.assertEqual(completed.returncode, 2)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload["status"], "invalid")
        self.assertEqual(payload["suggestions"]["concurency"], ["concurrency"])
        self.assertIn("concurrency", payload["allowed_risks"])
        self.assertEqual(payload["risk_aliases"]["data-loss"], ["persisted-data"])
        corrected = subprocess.run(
            shlex.split(payload["corrected_command"]),
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(corrected.returncode, 0, corrected.stderr or corrected.stdout)
        corrected_payload = json.loads(corrected.stdout)
        self.assertEqual(corrected_payload["work_mode"], "managed")
        considered = set(corrected_payload["method"]["selected"]) | set(
            corrected_payload["method"]["blocked"]
        )
        self.assertIn("state-transition-model", considered)

        workflow = run_flow(
            "route-task",
            "--intent",
            "review",
            "--risk",
            "workflow",
        )
        workflow_payload = json.loads(workflow.stdout)
        self.assertEqual(workflow.returncode, 2)
        self.assertIsNone(workflow_payload["corrected_command"])
        self.assertIn("Do not translate workflow labels", workflow_payload["risk_signal_guidance"])

        combined = run_flow(
            "route-task",
            "--intent",
            "change",
            "--risk",
            "concurency",
            "--method-signal",
            "concurreny-ordering",
            "--material-exposure",
        )
        combined_payload = json.loads(combined.stdout)
        self.assertEqual(combined.returncode, 2)
        self.assertEqual(
            combined_payload["method_signal_suggestions"]["concurreny-ordering"],
            ["concurrency-ordering"],
        )
        self.assertIn("model-evaluation", combined_payload["allowed_method_signals"])
        replay = subprocess.run(
            shlex.split(combined_payload["corrected_command"]),
            cwd=ROOT.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr or replay.stdout)
        replay_payload = json.loads(replay.stdout)
        self.assertIn("risk:concurrency", replay_payload["capability_activation"]["method"]["reasons"])
        self.assertIn(
            "signal:state-lifecycle",
            replay_payload["capability_activation"]["method"]["reasons"],
        )

    def test_weak_oracle_and_model_evaluation_are_task_facing_methods(self) -> None:
        weak = route("--intent", "review", "--risk", "weak-tests")
        weak_method = weak["capability_activation"]["method"]
        self.assertTrue(weak_method["active_match_required"])
        self.assertEqual(
            weak_method["signal_normalization"]["derived_from_risks"],
            ["oracle-challenge"],
        )
        self.assertIn("RM-WEAK-ORACLE", weak_method["selection"]["matched_risk_models"])
        self.assertTrue(weak_method["selection"]["actionable"])

        model = route(
            "--intent",
            "change",
            "--suite-maintenance",
            "--risk",
            "weak-tests",
            "--method-signal",
            "model-evaluation",
            "--method-prerequisite",
            "evaluator-contract",
            "--method-prerequisite",
            "isolated-environment",
            "--method-prerequisite",
            "model-identity",
            "--method-depth",
            "deep",
        )
        method = model["capability_activation"]["method"]
        self.assertEqual(method["selection"]["phase"], "verification")
        self.assertEqual(method["selection"]["phase_source"], "signal-adjacent-owner")
        self.assertTrue(
            {
                "agent-evaluation-design",
                "eval-contamination-case-health",
                "model-tool-identity-pinning",
            }.issubset(method["selection"]["selected"])
        )
        self.assertIn("RM-AI-STOCHASTIC-EVAL-VALIDITY", method["selection"]["matched_risk_models"])

        review_model = route(
            "--intent",
            "review",
            "--suite-maintenance",
            "--risk",
            "weak-tests",
            "--method-signal",
            "model-evaluation",
            "--method-prerequisite",
            "evaluator-contract",
            "--method-prerequisite",
            "isolated-environment",
            "--method-prerequisite",
            "model-identity",
            "--method-depth",
            "deep",
        )
        review_selection = review_model["capability_activation"]["method"]["selection"]
        self.assertEqual(review_selection["phase"], "verification")
        self.assertIn("agent-evaluation-design", review_selection["selected"])

    def test_ready_method_guidance_is_not_crowded_out_by_blocked_methods(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--risk",
            "compatibility",
            "--method-signal",
            "multi-version-coexistence",
            "--method-prerequisite",
            "repository-facts",
            "--method-prerequisite",
            "requirement-baseline",
        )
        selection = payload["capability_activation"]["method"]["selection"]
        self.assertEqual(selection["status"], "selected")
        self.assertIn("characterization-golden-master", selection["selected"])
        self.assertIn(
            "parallel-change-expand-contract",
            {item["method"] for item in selection["blocked"]},
        )
        self.assertLessEqual(len(selection["selected"]), 3)
        self.assertLessEqual(len(selection["blocked"]), 2)
        self.assertEqual(
            {item["method"] for item in selection["guidance"]},
            set(selection["selected"]),
        )

    def test_route_infers_only_established_common_method_prerequisites(self) -> None:
        payload = route(
            "--intent",
            "review",
            "--risk",
            "weak-tests",
            "--method-signal",
            "model-evaluation",
            "--repo-fact",
            "context=synthetic-evaluation",
            "--method-prerequisite",
            "evaluator-contract",
            "--method-prerequisite",
            "isolated-environment",
            "--method-prerequisite",
            "model-identity",
        )
        selection = payload["capability_activation"]["method"]["selection"]
        self.assertEqual(
            selection["inferred_prerequisites"],
            ["repository-facts", "requirement-baseline"],
        )
        self.assertIn("agent-evaluation-design", selection["selected"])

        pending = route(
            "--intent",
            "change",
            "--requirement-class",
            "semantic-change",
            "--risk",
            "weak-tests",
            "--method-signal",
            "model-evaluation",
            "--repo-fact",
            "context=synthetic-evaluation",
        )
        pending_selection = pending["capability_activation"]["method"]["selection"]
        self.assertEqual(pending_selection["inferred_prerequisites"], ["repository-facts"])
        self.assertNotIn(
            "requirement-baseline", pending_selection["available_prerequisites"]
        )

    def test_broad_security_does_not_surface_unrelated_domain_methods(self) -> None:
        payload = route("--intent", "change", "--risk", "security")
        selection = payload["capability_activation"]["method"]["selection"]
        considered = set(selection["selected"]) | {
            item["method"] for item in selection["blocked"]
        }
        self.assertNotIn("linddun-privacy-model", considered)
        self.assertNotIn("agent-memory-lifecycle-governance", considered)
        self.assertNotIn("multi-agent-topology-ownership", considered)

    def test_privacy_method_requires_and_uses_a_privacy_data_map(self) -> None:
        blocked_payload = route("--intent", "change", "--risk", "privacy")
        blocked = blocked_payload["capability_activation"]["method"]["selection"]
        linddun = next(item for item in blocked["blocked"] if item["method"] == "linddun-privacy-model")
        self.assertEqual(linddun["missing_prerequisites"], ["privacy-data-map"])

        ready_payload = route(
            "--intent",
            "change",
            "--risk",
            "privacy",
            "--method-prerequisite",
            "privacy-data-map",
        )
        ready = ready_payload["capability_activation"]["method"]["selection"]
        self.assertEqual(ready["phase"], "design")
        self.assertIn("linddun-privacy-model", ready["selected"])

    def test_multi_agent_method_requires_actual_delegation(self) -> None:
        base_args = (
            "--intent",
            "change",
            "--risk",
            "concurrency",
            "--risk",
            "ordering",
            "--risk",
            "resource-limits",
            "--method-prerequisite",
            "task-dependency-graph",
            "--method-prerequisite",
            "repository-facts",
        )
        without_delegation = route(*base_args)
        blocked = without_delegation["capability_activation"]["method"]["selection"]
        considered = set(blocked["selected"]) | {item["method"] for item in blocked["blocked"]}
        self.assertNotIn("multi-agent-topology-ownership", considered)

        with_delegation = route(*base_args, "--repo-fact", "delegation=planned")
        selected = with_delegation["capability_activation"]["method"]["selection"]
        self.assertIn("multi-agent-topology-ownership", selected["selected"])

    def test_compact_route_avoids_the_duplicate_explanatory_envelope(self) -> None:
        payload = route(
            "--intent",
            "review",
            "--risk",
            "ffi",
            "--method-signal",
            "multi-version-coexistence",
            "--compact",
        )
        self.assertEqual(
            set(payload),
            {
                "status",
                "intent",
                "work_mode",
                "requirement_understanding",
                "routes",
                "risk_overlays",
                "method",
                "independent_review",
                "knowledge",
                "route_basis",
            },
        )
        self.assertEqual(payload["intent"], "review")
        self.assertEqual(
            set(payload["requirement_understanding"]), {"class", "next_action"}
        )
        self.assertNotIn("confirmation_required", payload["requirement_understanding"])
        self.assertNotIn("method_selection", payload)

    def test_diagnosis_and_review_use_their_method_phases(self) -> None:
        diagnosis = route(
            "--intent",
            "diagnose",
            "--method-signal",
            "repeated-failure",
            "--method-prerequisite",
            "repository-facts",
        )
        self.assertEqual(
            diagnosis["capability_activation"]["method"]["selection"]["phase"],
            "diagnosis",
        )
        review = route(
            "--intent",
            "review",
            "--risk",
            "public-api",
            "--method-prerequisite",
            "stable-contract",
        )
        self.assertEqual(
            review["capability_activation"]["method"]["selection"]["phase"],
            "review",
        )

    def test_low_risk_work_keeps_advanced_activation_quiet(self) -> None:
        payload = route("--task-type", "micro")
        activation = payload["capability_activation"]
        self.assertFalse(activation["method"]["active_match_required"])
        self.assertFalse(activation["independent_review"]["required"])
        self.assertEqual(
            activation["specialist"]["source"],
            "effective-current-turn-skill-surface",
        )
        self.assertFalse(activation["specialist"]["persisted"])

    def test_repository_facts_activate_only_effective_specialists(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--repo-fact",
            "language=rust",
            "--repo-fact",
            "framework=axum",
            "--risk",
            "concurrency",
            "--effective-skill",
            "rust-code-review",
            "--effective-skill",
            "tokio-async-code-review",
            "--effective-skill",
            "axum-code-review",
        )
        matches = {
            item["capability"]: item
            for item in payload["capability_activation"]["specialist"]["matches"]
        }
        self.assertEqual(matches["quality.rust.correctness"]["route"], "rust-code-review")
        self.assertEqual(matches["quality.rust.async"]["route"], "tokio-async-code-review")
        self.assertEqual(matches["quality.rust.axum"]["route"], "axum-code-review")
        self.assertNotIn("quality.swift.correctness", matches)

    def test_swift_background_lifecycle_activates_only_its_effective_specialist(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--repo-fact",
            "language=swift",
            "--risk",
            "platform-lifecycle",
            "--effective-skill",
            "background-execution",
        )
        matches = {
            item["capability"]: item
            for item in payload["capability_activation"]["specialist"]["matches"]
        }
        background = matches["quality.swift.background-execution"]
        self.assertEqual(background["status"], "effective-skill")
        self.assertEqual(background["route"], "background-execution")

        unrelated = route(
            "--intent",
            "change",
            "--repo-fact",
            "language=swift",
            "--effective-skill",
            "background-execution",
        )
        unrelated_ids = {
            item["capability"]
            for item in unrelated["capability_activation"]["specialist"]["matches"]
        }
        self.assertNotIn("quality.swift.background-execution", unrelated_ids)

    def test_plugin_prefixed_skill_name_is_effective_and_missing_route_falls_back(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--repo-fact",
            "language=typescript",
            "--repo-fact",
            "framework=react",
            "--effective-skill",
            "build-web-apps:react-best-practices",
        )
        matches = {
            item["capability"]: item
            for item in payload["capability_activation"]["specialist"]["matches"]
        }
        self.assertEqual(matches["quality.react.performance"]["status"], "effective-skill")
        self.assertEqual(matches["quality.react.performance"]["route"], "react-best-practices")
        self.assertEqual(matches["quality.typescript.correctness"]["status"], "qualified-fallback")

    def test_invalid_repository_fact_fails_closed(self) -> None:
        completed = run_flow("route-task", "--intent", "change", "--repo-fact", "rust")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("key=value", completed.stdout)
        payload = json.loads(completed.stdout)
        self.assertIn("--repo-fact context=rust", payload["corrected_command"])

    def test_material_exposure_adds_independent_review_without_managed_mode(self) -> None:
        payload = route(
            "--intent",
            "change",
            "--risk",
            "security",
            "--material-exposure",
        )
        self.assertEqual(payload["work_mode"], "direct")
        self.assertIn("change-review", [item["skill"] for item in payload["routes"]])
        review = payload["capability_activation"]["independent_review"]
        self.assertTrue(review["required"])
        self.assertEqual(review["reasons"], ["material-exposure"])
        self.assertTrue(review["blue_red_are_lenses"])
        self.assertFalse(review["same_context_is_independent"])
        self.assertFalse(review["empty_wait_is_independent"])
        self.assertEqual(
            review["evidence_required"]["reviewer_identity"],
            "non-empty-dispatched-reviewer-or-receiver-id",
        )
        self.assertTrue(review["evidence_required"]["completed_result"])
        self.assertEqual(review["execution"], "explicit-downgrade")
        self.assertFalse(review["delegation_authorized"])
        self.assertFalse(review["authorization_from_route"])
        self.assertIsNone(review["route_agent"])
        self.assertEqual(review["downgrade"]["required_report"], "common-mode-risk")

        authorized = route(
            "--intent",
            "change",
            "--risk",
            "security",
            "--material-exposure",
            "--independent-review-authorized",
        )["capability_activation"]["independent_review"]
        self.assertTrue(authorized["delegation_authorized"])
        self.assertEqual(authorized["execution"], "route-agent-or-explicit-downgrade")
        self.assertEqual(authorized["route_agent"]["role"], "dev-flow-red-reviewer")

    def test_intrinsically_consequential_risks_require_review_without_extra_flag(self) -> None:
        for risk in ("data-deletion", "rollback", "version-compatibility"):
            with self.subTest(risk=risk):
                payload = route("--intent", "change", "--risk", risk)
                review = payload["capability_activation"]["independent_review"]
                self.assertTrue(review["required"])
                self.assertIn(f"risk:{risk}", review["reasons"])
                self.assertIn("change-review", [item["skill"] for item in payload["routes"]])

        durable = route(
            "--intent",
            "change",
            "--risk",
            "persisted-data",
            "--risk",
            "external-write",
            "--risk",
            "backpressure",
        )
        review = durable["capability_activation"]["independent_review"]
        self.assertTrue(review["required"])
        self.assertIn("cross-system-durability", review["reasons"])
        self.assertIn("change-review", [item["skill"] for item in durable["routes"]])

    def test_security_family_labels_do_not_imply_architecture(self) -> None:
        for risk in (
            "authentication",
            "authorization",
            "privacy",
            "secrets",
            "security",
            "untrusted-input",
        ):
            with self.subTest(risk=risk):
                payload = route("--intent", "change", "--risk", risk)
                self.assertNotIn("architecture-decisions", [item["skill"] for item in payload["routes"]])

        compatible = route("--task-type", "security")
        self.assertNotIn("architecture-decisions", [item["skill"] for item in compatible["routes"]])


class WorkstreamTests(unittest.TestCase):
    def test_managed_route_exposes_restartable_interruption_contract(self) -> None:
        payload = route("--intent", "change", "--multi-session")
        continuity = payload["continuity"]
        self.assertIn("assumption-breaking-first-failure", continuity["update_on"])
        self.assertIn("interruption-or-handoff", continuity["update_on"])
        self.assertEqual(continuity["resume"][0], "read-current-workstream")
        self.assertIn(
            "reconcile-changed-paths-and-parallel-changes",
            continuity["resume"],
        )
        self.assertEqual(
            continuity["interruption_handoff"],
            [
                "done",
                "current",
                "next",
                "blockers-or-unrun-gates",
                "worktree-and-parallel-change-state",
            ],
        )
        self.assertEqual(
            continuity["conditional_artifact_rules"]["requirements.md"],
            "only-confirmed-complex-semantics-not-an-unknown-baseline",
        )

    def test_initializer_creates_tracked_knowledge_without_runtime_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run_flow(
                "init-workstream",
                "--root",
                root,
                "--slug",
                "customer-migration",
                "--objective",
                "Move customer records without downtime",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            workstream = root / "docs" / "workstreams" / "customer-migration"
            self.assertEqual(payload["packet"], None)
            self.assertEqual(
                sorted(path.name for path in workstream.iterdir()),
                ["implementation.md", "progress.md"],
            )
            self.assertIn("Move customer records without downtime", (workstream / "implementation.md").read_text())
            self.assertIn("Scope and acceptance", (workstream / "implementation.md").read_text())
            self.assertIn("State: active", (workstream / "progress.md").read_text())
            self.assertFalse((workstream / "design.md").exists())
            self.assertFalse((root / ".codex").exists())

    def test_optional_decisions_reuse_and_path_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run_flow(
                "init-workstream",
                "--root",
                root,
                "--slug",
                "platform-refresh",
                "--objective",
                "Refresh platform boundaries",
                "--with-requirements",
                "--with-design",
                "--with-decisions",
            )
            self.assertEqual(created.returncode, 0, created.stderr or created.stdout)
            self.assertTrue((root / "docs" / "workstreams" / "platform-refresh" / "requirements.md").is_file())
            self.assertTrue((root / "docs" / "workstreams" / "platform-refresh" / "design.md").is_file())
            self.assertTrue((root / "docs" / "workstreams" / "platform-refresh" / "decisions.md").is_file())
            reused = run_flow(
                "init-workstream",
                "--root",
                root,
                "--slug",
                "platform-refresh",
                "--objective",
                "Refresh platform boundaries",
                "--with-requirements",
                "--with-design",
                "--with-decisions",
                "--reuse",
            )
            self.assertEqual(json.loads(reused.stdout)["status"], "reused")
            escaped = run_flow(
                "init-workstream",
                "--root",
                root,
                "--slug",
                "escape-check",
                "--objective",
                "Do not escape",
                "--path",
                "../outside",
            )
            self.assertEqual(escaped.returncode, 2)
            self.assertFalse((root.parent / "outside").exists())

    def test_requirements_document_is_conditional(self) -> None:
        help_result = run_flow("init-workstream", "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr or help_result.stdout)
        self.assertIn("unknown baselines or unanswered questions", help_result.stdout)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run_flow(
                "init-workstream",
                "--root",
                root,
                "--slug",
                "shared-semantics",
                "--objective",
                "Preserve cross-team business semantics",
                "--with-requirements",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(
                payload["artifacts"],
                ["requirements.md", "implementation.md", "progress.md"],
            )
            requirements = root / "docs" / "workstreams" / "shared-semantics" / "requirements.md"
            self.assertIn("Acceptance behavior", requirements.read_text())


class ActiveGuidanceTests(unittest.TestCase):
    def test_unavailable_optional_capability_stays_repository_local(self) -> None:
        skill = DEV_FLOW_SKILL.read_text(encoding="utf-8")
        calibration = QUALITY_CALIBRATION.read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        self.assertIn("optional capability/scanner failure", frontmatter)
        for phrase in (
            "does not authorize discovering, installing, or invoking an external capability",
            "do not call Web, browser, MCP, app, computer-use, image-generation, or dynamic tools",
            "continue safe native checks",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, skill + "\n" + calibration)

    def test_diagnosis_only_stops_before_repair(self) -> None:
        guidance = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(
            "A diagnosis-only request stops there; repair only when requested.",
            guidance,
        )

    def test_main_skill_is_implicitly_discoverable_from_repository_task_language(self) -> None:
        skill = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        for trigger in (
            "repository engineering",
            "diagnose/fix bugs",
            "change behavior or architecture",
            "review/verify changes",
            "persistent-data",
            "concurrency",
            "migration",
            "cross-module",
            "external-system",
            "assess delivery",
            "long-running work",
        ):
            self.assertIn(trigger, frontmatter)
        policy = (ROOT / "skills" / "dev-flow" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("allow_implicit_invocation: true", policy)

    def test_main_skill_excludes_narrow_read_only_repository_lookups(self) -> None:
        skill = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        frontmatter = skill.split("---", 2)[1]
        for phrase in (
            "Exclude narrow read-only.",
            "use `repo-context` alone",
            "do not run `route-task`",
            "do not sustain Dev Flow",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, frontmatter if phrase.startswith("Exclude") else skill)

    def test_engineering_specialists_reconnect_material_work_to_kernel(self) -> None:
        specialists = (
            "repo-context",
            "requirements-design",
            "systematic-debugging",
            "architecture-decisions",
            "dependency-decisions",
            "product-ux-discovery",
            "verification",
            "change-review",
            "delivery-readiness",
        )
        for name in specialists:
            with self.subTest(skill=name):
                text = (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("load `dev-flow` as the coordinating kernel", text)
                self.assertIn("not already active", text)

    def test_explicit_material_route_and_review_downgrade_are_active_guidance(self) -> None:
        skill = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("one compact `route-task` is mandatory", skill)
        self.assertIn("before technical design or implementation", skill)
        self.assertIn("Do not replace this inspectable activation step", skill)
        self.assertIn("python3 <dev-flow-skill-dir>/scripts/dev-flow.py route-task", skill)
        self.assertIn("Confirmation changes the gate state, not the requirement class", skill)
        self.assertIn("design or change public contracts, data lifecycles", skill)

        for owner in ("requirements-design", "architecture-decisions"):
            owner_skill = (ROOT / "skills" / owner / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("even when", owner_skill)
            self.assertIn("Load `dev-flow` before technical design", owner_skill)
        self.assertIn("Run the route as a standalone command", skill)
        self.assertIn('JSON says `"status": "routed"`', skill)
        self.assertIn("use its exact `corrected_command` at most once", skill)
        self.assertIn("Canonical `--need` values", skill)
        self.assertIn("Continuity facts are part of the route contract", skill)
        self.assertIn("does not justify a stub requirements file", skill)
        self.assertIn("optional only for a one-line mechanical change", skill)
        self.assertIn("exceptions override explicit invocation", skill)
        self.assertIn("show its non-persisted decision", skill)
        self.assertIn("explicitly downgrade the claim", skill)
        self.assertIn("never independent review", skill)
        self.assertIn("non-empty reviewer/receiver identity", skill)
        self.assertIn("Never call `wait` or poll unless", skill)
        self.assertIn("label its findings same-context", skill)
        self.assertIn("review requirement never grants delegation authority", skill)
        self.assertIn("execution=explicit-downgrade", skill)

    def test_review_and_fix_is_explicit_in_the_active_skill(self) -> None:
        skill = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review-and-fix request as change intent with a review need", skill)
        self.assertIn("then use `change-review` against the final diff", skill)

    def test_method_selection_accepts_the_same_intent_vocabulary(self) -> None:
        result = subprocess.run(
            [sys.executable, str(LEGACY_FLOW), "select-methods", "--phase", "design", "--intent", "change"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        request = json.loads(result.stdout)["request"]
        self.assertEqual(request["intent"], "change")
        self.assertEqual(request["intent_source"], "explicit-intent")
        self.assertEqual(request["method_task_type"], "routine")

    def test_advanced_guidance_uses_repository_handoffs_not_legacy_bindings(self) -> None:
        references = ROOT / "skills" / "dev-flow" / "references"
        delivery = (references / "methods-delivery-agent.md").read_text(encoding="utf-8")
        agent_control = (references / "methods-agent-control-evaluation.md").read_text(encoding="utf-8")
        discovery = (references / "methods-discovery-requirements.md").read_text(encoding="utf-8")
        combined = "\n".join((delivery, agent_control, discovery))
        for legacy in (
            "requirement/design digests",
            "active IDs/slice",
            "resource leases",
            "compact AC/SC/VO",
            "Record the fallback",
        ):
            self.assertNotIn(legacy, combined)
        self.assertIn("repository `progress.md` or its native equivalent", delivery)
        self.assertIn("owned paths or read-only responsibility", agent_control)

    def test_requirements_agent_prompt_stops_u1_before_technical_design(self) -> None:
        prompt = (ROOT / "skills" / "requirements-design" / "agents" / "openai.yaml").read_text(
            encoding="utf-8"
        )
        self.assertIn("for U1", prompt)
        self.assertIn("technology-neutral understanding", prompt)
        self.assertIn("stop in Default mode", prompt)
        self.assertIn("before technical design", prompt)
        self.assertNotIn("approved requirement, design, and change-scope baseline", prompt)

    def test_readme_describes_every_change_review_trigger(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("`review` 意图、显式 `--need review` 或 `--material-exposure`", readme)
        self.assertIn("overlay 本身仍保留对应的领域控制和验证", readme)


class DefaultHookTests(unittest.TestCase):
    def test_default_manifest_has_no_dev_flow_process_hook(self) -> None:
        manifest = json.loads((ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
        hooks = manifest["hooks"]
        self.assertFalse({"Stop", "SubagentStart", "SubagentStop"} & hooks.keys())
        commands = [
            hook["command"]
            for entries in hooks.values()
            for entry in entries
            for hook in entry["hooks"]
        ]
        self.assertTrue(commands)
        self.assertTrue(all("data_security_hook.py" in command for command in commands))
        self.assertFalse((ROOT / "hooks" / "dev_flow_hook.py").exists())


if __name__ == "__main__":
    unittest.main()
