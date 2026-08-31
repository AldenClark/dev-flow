#!/usr/bin/env python3
"""Tests for multi-turn Flow transition observation coverage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "evals" / "flow-transition-semantic-cases.json"
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def matching_observations(catalog: dict[str, object]) -> dict[str, object]:
    cases = []
    for case in catalog["cases"]:
        repository_version = 0
        turns = []
        for turn_number, turn in enumerate(case["turns"], 1):
            if turn["mutation"] == "repository" or turn.get("pre_turn_fixture"):
                repository_version += 1
            turns.append(
                {
                    "turn": turn_number,
                    "observed": turn["expected"],
                    "evidence": [f"sanitized turn {turn_number} branch observation"],
                    "evidence_sha256": digest(f"{case['id']}:evidence:{turn_number}"),
                    "repository_sha256": digest(
                        f"{case['id']}:repository:{repository_version}"
                    ),
                    "unmet_prerequisites": (
                        ["unmet-prerequisite-observed"]
                        if turn.get("expected_unmet", False)
                        else []
                    ),
                    "authority_violations": [],
                }
            )
        cases.append(
            {
                "id": case["id"],
                "lineage_id": f"isolated-{case['id'].lower()}",
                "initial_git_head_sha256": digest(f"{case['id']}:git-head"),
                "initial_repository_sha256": digest(f"{case['id']}:repository:0"),
                "turns": turns,
            }
        )
    return {"schema_version": "flow.transition.observations.v1", "cases": cases}


class FlowTransitionTests(unittest.TestCase):
    def run_transition(
        self,
        observations: dict[str, object],
    ) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "observations.json"
            path.write_text(json.dumps(observations), encoding="utf-8")
            return subprocess.run(
                [
                    sys.executable,
                    str(FLOW),
                    "flow-metrics",
                    "--lane",
                    "transition",
                    "--observations",
                    str(path),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

    def test_catalog_covers_material_transitions_and_negative_control(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], "flow.transition.catalog.v1")
        self.assertGreaterEqual(len(catalog["cases"]), 21)
        qualification = catalog["qualification"]
        self.assertEqual(qualification["release_tier"], "R4")
        self.assertEqual(len(qualification["categories"]), 9)
        self.assertGreaterEqual(qualification["minimum_cases_per_category"], 3)
        self.assertGreaterEqual(qualification["minimum_first_attempts_per_case"], 3)
        for category in qualification["categories"]:
            covered = [case for case in catalog["cases"] if category in case["categories"]]
            self.assertGreaterEqual(
                len(covered),
                qualification["minimum_cases_per_category"],
                category,
            )
        serialized = json.dumps(catalog)
        for boundary in (
            "DIAGNOSE-CHANGE-REVIEW",
            "REVIEW-DELIVERY",
            "OPTIONAL-CAPABILITY-FAILURE",
            "UNRELATED-LOCAL-MCP-PRESENT",
            "EXPLICIT-SCANNER-MCP",
            "NEW-PLATFORM-EXPANSION",
            "EVIDENCE-FRESHNESS",
            "INTERRUPTION-RESUME",
            "FORK-CONTINUATION",
            "UNCHANGED-FOLLOWUP-NEGATIVE",
            "SCOPE-CLOSED-DEEP-IMPLEMENTATION",
            "SCOPE-EXPLICIT-OPEN-EXPLORATION",
            "METHOD-BLOCKED-TO-READY-DISPOSITION",
            "METHOD-REASONED-ABSTENTION-NEGATIVE",
            "METHOD-SELECTED-REALIZATION-OUTPUT",
            "METHOD-REVIEW-TO-VERIFICATION-ADJACENCY",
            "DELEGATION-MONOTONIC-NARROWING",
            "CONTINUATION-TERMINAL-WITHOUT-DELIVERY",
            "CONTINUATION-PROCESS-SUPERVISION",
            "CONTEXT-EXPLICIT-TASK-SYNTHESIS",
            "CONTEXT-REFERENCE-REPOSITORY-BOUNDARY",
            "ADAPTATION-CONFIRMED-PREFERENCE",
            "NEGATIVE-ORDINARY-CONVERSATION-QUIET",
        ):
            self.assertIn(boundary, serialized)
        for forbidden in (
            "productivity_score",
            "effect_score",
            "aggregate_score",
            "developer_rank",
        ):
            self.assertNotIn(forbidden, serialized.lower())
        capability_case = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        self.assertEqual(
            [turn.get("expected_unmet", False) for turn in capability_case["turns"]],
            [True, True, False],
        )
        self.assertEqual(
            list(capability_case["turns"][2]["pre_turn_fixture"]),
            ["tools/deep_scanner.py"],
        )
        self.assertIn(
            "python3 tools/deep_scanner.py", capability_case["turns"][2]["prompt"]
        )
        unrelated = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-UNRELATED-LOCAL-MCP-PRESENT"
        )
        self.assertEqual(
            unrelated["mcp_fixture"],
            {"server": "runner-context", "tool": "unrelated_status"},
        )
        self.assertTrue(
            all(not turn.get("allowed_mcp_tools") for turn in unrelated["turns"])
        )
        explicit = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-EXPLICIT-SCANNER-MCP"
        )
        self.assertEqual(
            explicit["turns"][0]["allowed_mcp_tools"],
            ["runner-scanner/deep_scan"],
        )
        self.assertNotIn("allowed_mcp_tools", explicit["turns"][1])

    def test_matching_turn_observations_pass_without_effect_score(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        completed = self.run_transition(matching_observations(catalog))
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["lane"], "transition-observation")
        self.assertEqual(result["matched"], len(catalog["cases"]))
        self.assertFalse(result["effect_measurement"])
        self.assertIsNone(result["aggregate_score"])
        self.assertEqual(len(result["qualification"]["category_results"]), 9)
        self.assertTrue(
            all(
                item["status"] == "matched"
                for item in result["qualification"]["category_results"]
            )
        )

    def test_platform_expansion_fixture_declares_a_concrete_delta(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        platform = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-NEW-PLATFORM-EXPANSION"
        )
        self.assertIn("value() -> u8 { 1 }", platform["repository"]["core.rs"])
        self.assertIn("value() -> UInt8 { 1 }", platform["repository"]["ios.swift"])
        self.assertIn("returns `2` instead of `1`", platform["turns"][0]["prompt"])
        self.assertIn("Modify only `core.rs`", platform["turns"][0]["prompt"])
        self.assertIn("returns `2` instead of `1`", platform["turns"][1]["prompt"])
        self.assertIn("Modify only `ios.swift`", platform["turns"][1]["prompt"])

    def test_repository_mutation_turns_declare_exact_existing_paths(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        for case in catalog["cases"]:
            repository_paths = set(case["repository"])
            for turn_number, turn in enumerate(case["turns"], 1):
                with self.subTest(case=case["id"], turn=turn_number):
                    if turn["mutation"] == "repository":
                        self.assertTrue(turn.get("mutation_paths"))
                        self.assertEqual(
                            len(turn["mutation_paths"]),
                            len(set(turn["mutation_paths"])),
                        )
                        self.assertLessEqual(set(turn["mutation_paths"]), repository_paths)
                    else:
                        self.assertNotIn("mutation_paths", turn)

    def test_evidence_freshness_fixture_has_a_self_contained_focused_command(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        case = next(
            item
            for item in catalog["cases"]
            if item["id"] == "TRANSITION-EVIDENCE-FRESHNESS"
        )
        self.assertIn("run_focused_test.py", case["repository"])
        self.assertIn("python3 run_focused_test.py", case["turns"][0]["prompt"])
        self.assertIn("python3 run_focused_test.py", case["turns"][2]["prompt"])
        self.assertNotIn("pytest", case["turns"][0]["prompt"])

    def test_repository_mutation_prompts_lock_baseline_target_and_paths(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cases = {case["id"]: case for case in catalog["cases"]}
        contracts = (
            ("TRANSITION-DIAGNOSE-CHANGE-REVIEW", 2, ("service.py",), "return 2", ("returns `1`", "only `service.py`")),
            ("TRANSITION-NEW-PLATFORM-EXPANSION", 1, ("core.rs",), "{ 1 }", ("returns `2` instead of `1`", "only `core.rs`")),
            ("TRANSITION-NEW-PLATFORM-EXPANSION", 2, ("ios.swift",), "{ 1 }", ("returns `2` instead of `1`", "only `ios.swift`")),
            ("TRANSITION-EVIDENCE-FRESHNESS", 2, ("feature.py",), "return False", ("return bool(0)", "only `feature.py`")),
            ("TRANSITION-INTERRUPTION-RESUME", 1, ("docs/workstreams/sample/implementation.md", "docs/workstreams/sample/progress.md"), "Slice 1: record baseline [ready]", ("Slice 1 is complete", "Slice 2 is next")),
            ("TRANSITION-INTERRUPTION-RESUME", 2, ("docs/workstreams/sample/implementation.md", "docs/workstreams/sample/progress.md"), "Slice 2: record verification", ("terminal implementation complete", "both current workstream files")),
            ("TRANSITION-FORK-CONTINUATION", 2, ("README.md",), "status: draft", ("status: ready", "only `README.md`")),
            ("SCOPE-CLOSED-DEEP-IMPLEMENTATION", 1, ("feature.py",), "return 'target'", ("confirmed-target", "only `feature.py`")),
            ("METHOD-BLOCKED-TO-READY-DISPOSITION", 3, ("privacy.md",), "awaiting discovery", ("trust boundary", "only `privacy.md`")),
            ("METHOD-SELECTED-REALIZATION-OUTPUT", 1, ("test_parser.py",), "assert parse('1') == 1", ("parse('not-an-int')", "only `test_parser.py`")),
            ("CONTINUATION-TERMINAL-WITHOUT-DELIVERY", 1, ("docs/workstreams/sample/progress.md",), "Current: Slice 1", ("terminal implementation complete", "only that file")),
            ("ADAPTATION-CONFIRMED-PREFERENCE", 2, (".dev-flow/preferences.toml",), "# no personal preference", ("layer=`personal`", "only `.dev-flow/preferences.toml`")),
        )
        self.assertEqual(len(contracts), 12)
        for case_id, turn_number, paths, baseline, targets in contracts:
            case = cases[case_id]
            turn = case["turns"][turn_number - 1]
            with self.subTest(case=case_id, turn=turn_number):
                self.assertEqual(tuple(turn["mutation_paths"]), paths)
                self.assertTrue(
                    any(baseline in case["repository"][path] for path in paths),
                    baseline,
                )
                for target in targets:
                    self.assertIn(target, turn["prompt"])

        fork = cases["TRANSITION-FORK-CONTINUATION"]["turns"][1]
        old_prompt = fork["prompt"]
        fork["prompt"] = "Apply the bounded change and verify it."
        required = ("status: draft", "status: ready", "only `README.md`")
        self.assertFalse(all(fragment in fork["prompt"] for fragment in required))
        fork["prompt"] = old_prompt

    def test_expected_unmet_is_a_turn_contract_not_an_unconditional_failure(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        capability = next(
            case
            for case in observations["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][0]["unmet_prerequisites"] = []
        capability["turns"][1]["unmet_prerequisites"] = []
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 0)
        result = json.loads(completed.stdout)
        matched = next(
            case
            for case in result["results"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        self.assertEqual(matched["turns"][0]["status"], "matched")
        self.assertEqual(matched["turns"][1]["status"], "matched")
        capability["turns"][2]["unmet_prerequisites"] = [
            "unmet-prerequisite-observed"
        ]
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        failed = next(
            case
            for case in result["results"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        self.assertIn("unmet prerequisites", failed["turns"][2]["observations"][0])

        capability["turns"][2]["unmet_prerequisites"] = []
        capability["turns"][2]["observed"].append("blocked-claim")
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        failed = next(
            case
            for case in result["results"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        self.assertIn("unmet prerequisites", failed["turns"][2]["observations"][0])

    def test_missing_and_forbidden_turn_observations_fail(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        first_case = observations["cases"][0]
        first_case["turns"][0]["observed"] = [
            catalog["cases"][0]["turns"][0]["forbidden"][0]
        ]
        first_case["turns"].pop()
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 1)
        result = json.loads(completed.stdout)
        details = json.dumps(result["results"][0])
        self.assertIn("missing expected activation", details)
        self.assertIn("forbidden activation observed", details)
        self.assertIn("turn observation is missing", details)

    def test_selected_method_without_concrete_output_fails(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        case_index = next(
            index
            for index, case in enumerate(catalog["cases"])
            if case["id"] == "METHOD-SELECTED-REALIZATION-OUTPUT"
        )
        observed = observations["cases"][case_index]["turns"][0]["observed"]
        observed.remove("method-output:negative-control")
        observed.append("method-name-only")
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 1)
        details = json.dumps(json.loads(completed.stdout)["results"][case_index])
        self.assertIn("missing expected activation", details)
        self.assertIn("forbidden activation observed", details)

    def test_reused_evidence_digest_is_rejected_as_stale(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        first = observations["cases"][0]["turns"]
        first[1]["evidence_sha256"] = first[0]["evidence_sha256"]
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("evidence digest was reused", completed.stdout)

    def test_declared_repository_mutation_requires_changed_byte_binding(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        first = observations["cases"][0]["turns"]
        first[1]["repository_sha256"] = first[0]["repository_sha256"]
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("repository mutation is not bound to changed bytes", completed.stdout)

        observations = matching_observations(catalog)
        case_index = next(
            index
            for index, case in enumerate(catalog["cases"])
            if case["turns"][0]["mutation"] == "repository"
        )
        observed_case = observations["cases"][case_index]
        observed_case["turns"][0]["repository_sha256"] = observed_case[
            "initial_repository_sha256"
        ]
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("repository mutation is not bound to changed bytes", completed.stdout)

    def test_declared_read_only_turn_rejects_changed_repository_bytes(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        case_index = next(
            index
            for index, case in enumerate(catalog["cases"])
            if case["turns"][0]["mutation"] == "none"
        )
        observations["cases"][case_index]["turns"][0]["repository_sha256"] = digest(
            "unexpected-read-only-mutation"
        )
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("mutation=none changed repository bytes", completed.stdout)

    def test_turn_observations_must_be_in_lineage_order(self) -> None:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        observations = matching_observations(catalog)
        first = observations["cases"][0]["turns"]
        first[0], first[1] = first[1], first[0]
        completed = self.run_transition(observations)
        self.assertEqual(completed.returncode, 2)
        self.assertIn("ordered by turn number", completed.stdout)

    def test_transition_lane_requires_observations(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(FLOW), "flow-metrics", "--lane", "transition"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("requires --observations", completed.stdout)


if __name__ == "__main__":
    unittest.main()
