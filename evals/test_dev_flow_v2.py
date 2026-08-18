#!/usr/bin/env python3
"""Focused acceptance tests for the Dev Flow 2.0 operating model."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"


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
        self.assertTrue(confirmed["requirement_understanding"]["design_allowed"])
        self.assertEqual(confirmed["requirement_understanding"]["next_action"], "continue")

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
        payload = route("--intent", "review", "--risk", "ffi", "--compact")
        self.assertEqual(payload["intent"], "review")
        self.assertFalse(payload["requirement_understanding"]["confirmation_required"])
        self.assertIn("architecture-decisions", payload["routes"])

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
            },
        )
        self.assertEqual(payload["intent"], "review")
        self.assertFalse(payload["requirement_understanding"]["confirmation_required"])
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
    def test_review_and_fix_is_explicit_in_the_active_skill(self) -> None:
        skill = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("review-and-fix request as change intent with a review need", skill)
        self.assertIn("then use `change-review` against the final diff", skill)

    def test_method_selection_accepts_the_same_intent_vocabulary(self) -> None:
        result = run_flow("select-methods", "--phase", "design", "--intent", "change")
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
