#!/usr/bin/env python3
"""Independent Dev Flow Bench contract tests."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
BENCH_PATH = ROOT / "benchmarks" / "dev_flow_bench.py"
REGRESSION = ROOT / "benchmarks" / "suites" / "dev-flow-regression.json"
CAPABILITY = ROOT / "benchmarks" / "suites" / "dev-flow-capability.json"
SPEC = importlib.util.spec_from_file_location("dev_flow_bench", BENCH_PATH)
assert SPEC is not None and SPEC.loader is not None
BENCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BENCH)


def digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode()).hexdigest()


def study_identity(
    candidate: str = "candidate-a",
    context: str = "context-a",
    *,
    suite: str = "fixture",
    execution_extra: dict[str, object] | None = None,
) -> dict[str, object]:
    candidate_identity = {"tree_sha256": digest(candidate)}
    environment = {"fixture": True, "context": context}
    execution = {"fixture": True, **(execution_extra or {})}
    core = {
        "schema_version": BENCH.IDENTITY_SCHEMA,
        "candidate": candidate_identity,
        "environment": environment,
        "execution": execution,
        "suite": suite,
    }
    comparison_execution = {
        key: value for key, value in execution.items() if key != "selection_sha256"
    }
    return {
        **core,
        "candidate_sha256": BENCH._canonical_sha256(candidate_identity),
        "comparison_context_sha256": BENCH._canonical_sha256(
            {"environment": environment, "execution": comparison_execution, "suite": suite}
        ),
        "sha256": BENCH._canonical_sha256(core),
    }


def graded_result(
    results: list[dict[str, str]],
    *,
    candidate: str = "candidate-a",
    context: str = "context-a",
    selection: str | None = None,
) -> dict[str, object]:
    mismatched = [item["id"] for item in results if item["status"] == "mismatched"]
    return {
        "status": "mismatched" if mismatched else "matched",
        "schema_version": BENCH.RESULT_SCHEMA,
        "suite": "fixture",
        "kind": "regression",
        "cases": len(results),
        "matched": len(results) - len(mismatched),
        "mismatched": mismatched,
        "results": results,
        "safety_authority": [],
        "study_identity": study_identity(
            candidate,
            context,
            execution_extra={"selection_sha256": digest(selection)} if selection else None,
        ),
        "trial": 1,
        "source_run_sha256": digest("run"),
        "source_evidence_sha256": digest("evidence"),
        "observations_sha256": digest("observations"),
        "case_contracts": {item["id"]: digest("contract-" + item["id"]) for item in results},
        "aggregate_score": None,
        "release_gate": False,
        "claim_limit": "fixture",
    }


class DevFlowBenchTests(unittest.TestCase):
    def test_shipped_regression_suite_is_valid(self) -> None:
        result = BENCH.audit_suite(BENCH.load_suite(REGRESSION))
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["errors"], [])
        self.assertIn("no model capability or release claim", result["claim_limit"])

    def test_every_migrated_case_has_a_suite_health_disposition(self) -> None:
        suite_paths = sorted((ROOT / "benchmarks" / "suites").glob("*.json"))
        suites = [BENCH.load_suite(path) for path in suite_paths]
        catalog_ids = set(suites[0]["case_by_id"])
        disposed = {entry["id"] for suite in suites for entry in suite["entries"]}
        self.assertEqual(disposed, catalog_ids)
        self.assertEqual(len(catalog_ids), 26)

    def test_active_bench_has_no_r4_qualification_or_campaign_surface(self) -> None:
        active_paths = [
            BENCH_PATH,
            ROOT / "benchmarks" / "dev_flow_bench_contracts.py",
            ROOT / "benchmarks" / "dev_flow_bench_executor.py",
            ROOT / "benchmarks" / "cases" / "dev-flow-cases.json",
            ROOT / "skills" / "dev-flow" / "scripts" / "flow_metrics.py",
            ROOT / "skills" / "dev-flow" / "scripts" / "dev_flow.py",
        ]
        serialized = "\n".join(path.read_text(encoding="utf-8") for path in active_paths)
        for obsolete in (
            '"release_tier": "R4"',
            "--qualification",
            "qualification_requested",
            "qualification_eligible",
            "campaign_budget",
            "reserve_campaign_budget",
            "flow.transition.catalog.v1",
            "flow.transition.observations.v1",
        ):
            self.assertNotIn(obsolete, serialized)
        self.assertFalse((ROOT / "evals" / "run_transition_trials.py").exists())
        self.assertFalse((ROOT / "evals" / "flow-transition-semantic-cases.json").exists())

    def test_plan_is_non_spending_and_has_no_release_score(self) -> None:
        suite = BENCH.load_suite(REGRESSION)
        cases, entries = BENCH.selected_cases(suite, None, False)
        result = BENCH.study_plan(suite, cases, entries, 1)
        self.assertFalse(result["executes_model"])
        self.assertFalse(result["release_gate"])
        self.assertIsNone(result["aggregate_score"])
        self.assertTrue(all(value == "accepted" for value in result["case_health"].values()))

    def test_provisional_cases_require_explicit_inclusion(self) -> None:
        suite = BENCH.load_suite(CAPABILITY)
        _, ordinary = BENCH.selected_cases(suite, None, False)
        _, exploratory = BENCH.selected_cases(suite, None, True)
        self.assertNotIn("METHOD-SELECTED-REALIZATION-OUTPUT", {item["id"] for item in ordinary})
        self.assertIn("METHOD-SELECTED-REALIZATION-OUTPUT", {item["id"] for item in exploratory})

    def test_live_execution_without_spend_acknowledgement_fails_before_model(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(BENCH_PATH), "run", str(REGRESSION), "--execute"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("--acknowledge-model-spend", result["errors"][0])

    def test_expected_forbidden_overlap_is_a_real_negative_control(self) -> None:
        suite = BENCH.load_suite(REGRESSION)
        first = suite["case_by_id"][suite["entries"][0]["id"]]["turns"][0]
        token = first["expected"][0]
        first["forbidden"].append(token)
        result = BENCH.audit_suite(suite)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("overlap" in error for error in result["errors"]), result["errors"])

    def test_suite_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory) / "suite.json"
            try:
                link.symlink_to(REGRESSION)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            with self.assertRaises(BENCH.BenchError):
                BENCH.load_suite(link)

    def test_live_output_symlink_is_rejected_before_model(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.mkdir()
            link = root / "output"
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(BENCH_PATH),
                    "run",
                    str(REGRESSION),
                    "--execute",
                    "--acknowledge-model-spend",
                    "--model",
                    "fixture-model",
                    "--reasoning-effort",
                    "low",
                    "--output-dir",
                    str(link),
                    "--max-total-tokens",
                    "10",
                    "--per-call-token-limit",
                    "10",
                    "--per-call-timeout-seconds",
                    "1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("must not be a symlink", completed.stdout)

    def test_compare_reports_case_regression_without_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            candidate = root / "candidate.json"
            baseline.write_text(json.dumps(graded_result([{"id": "A", "status": "matched"}])) )
            candidate.write_text(
                json.dumps(
                    graded_result(
                        [{"id": "A", "status": "mismatched"}], candidate="candidate-b"
                    )
                )
            )
            result = BENCH.compare_results(baseline, candidate)
        self.assertEqual(result["candidate_regressions"], ["A"])
        self.assertIsNone(result["aggregate_score"])

    def test_compare_rejects_silent_case_loss_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            candidate = root / "candidate.json"
            baseline.write_text(
                json.dumps(
                    graded_result(
                        [{"id": "A", "status": "matched"}, {"id": "B", "status": "matched"}],
                        selection="A+B",
                    )
                )
            )
            candidate.write_text(
                json.dumps(
                    graded_result(
                        [{"id": "A", "status": "matched"}],
                        candidate="candidate-b",
                        selection="A",
                    )
                )
            )
            with self.assertRaisesRegex(BENCH.BenchError, "identical case sets"):
                BENCH.compare_results(baseline, candidate)
            partial = BENCH.compare_results(baseline, candidate, allow_partial=True)
        self.assertEqual(partial["missing_in_candidate"], ["B"])

    def test_compare_rejects_duplicate_ids_and_unknown_statuses(self) -> None:
        duplicate = graded_result([{"id": "A", "status": "matched"}, {"id": "A", "status": "matched"}])
        unknown = graded_result([{"id": "A", "status": "matched"}])
        unknown["results"][0]["status"] = "banana"
        with self.assertRaisesRegex(BENCH.BenchError, "duplicate or invalid"):
            BENCH._validate_graded_result(duplicate, "fixture")
        with self.assertRaisesRegex(BENCH.BenchError, "invalid status"):
            BENCH._validate_graded_result(unknown, "fixture")

    def test_compare_rejects_different_execution_contexts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            candidate = root / "candidate.json"
            baseline.write_text(json.dumps(graded_result([{"id": "A", "status": "matched"}])))
            candidate.write_text(
                json.dumps(
                    graded_result(
                        [{"id": "A", "status": "matched"}],
                        candidate="candidate-b",
                        context="context-b",
                    )
                )
            )
            with self.assertRaisesRegex(BENCH.BenchError, "same model, executor, limits"):
                BENCH.compare_results(baseline, candidate)

    def test_safety_grade_keeps_every_selected_safety_case(self) -> None:
        suite_path = ROOT / "benchmarks" / "suites" / "dev-flow-safety-authority.json"
        suite = BENCH.load_suite(suite_path)
        cases, entries = BENCH.selected_cases(suite, None, False)
        contract = BENCH.selection_contract(suite, cases, entries)
        results = [
            {
                "id": entry["id"],
                "status": "matched",
                "categories": suite["case_by_id"][entry["id"]]["categories"],
            }
            for entry in entries
        ]
        contracts = SimpleNamespace(
            run_benchmark_catalog=lambda *args, **kwargs: {
                "status": "matched",
                "cases": len(results),
                "matched": len(results),
                "mismatched": [],
                "results": results,
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            evidence = root / "trial-001-evidence.json"
            evidence.write_text(json.dumps({"cases": []}))
            observations = root / "observations.json"
            observations.write_text(
                json.dumps({"schema_version": BENCH.OBSERVATIONS_SCHEMA, "cases": []})
            )
            run_result = root / "result.json"
            run_identity = study_identity(
                suite=suite["id"],
                execution_extra={"selection_sha256": contract["sha256"], "trials": 1},
            )
            run_result.write_text(
                json.dumps(
                    {
                        "schema_version": BENCH.RUN_SCHEMA,
                        "status": "awaiting-assessment",
                        "suite": suite["id"],
                        "selection_contract": contract,
                        "study_identity": run_identity,
                        "candidate_sha256": run_identity["candidate_sha256"],
                        "evidence": [evidence.name],
                    }
                )
            )
            args = SimpleNamespace(
                case=None,
                include_provisional=False,
                run_result=run_result,
                trial=1,
                observations=observations,
            )
            with patch.object(BENCH, "_contracts", return_value=contracts):
                result = BENCH.grade_study(args, suite)
        self.assertEqual(
            [item["id"] for item in result["safety_authority"]],
            [item["id"] for item in results],
        )

    def test_live_run_stops_on_identity_drift_without_retry(self) -> None:
        suite = BENCH.load_suite(REGRESSION)
        first_identity = study_identity()
        changed_identity = study_identity(candidate="candidate-b")
        engine = SimpleNamespace(
            TrialError=RuntimeError,
            run_attempt=lambda **kwargs: (
                {"schema_version": "dev-flow.benchmark.evidence.v1", "cases": []},
                {"consumed_tokens": 1},
            ),
        )
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "study"
            args = SimpleNamespace(
                case=None,
                include_provisional=False,
                trials=1,
                execute=True,
                acknowledge_model_spend=True,
                model="fixture-model",
                reasoning_effort="low",
                output_dir=output,
                max_total_tokens=10,
                per_call_token_limit=10,
                per_call_timeout_seconds=1,
                candidate=ROOT,
                codex="fixture-codex",
            )
            with (
                patch.object(BENCH, "_engine", return_value=engine),
                patch.object(BENCH, "study_identity", side_effect=[first_identity, changed_identity]),
            ):
                result = BENCH.run_study(args, suite)
        self.assertEqual(result["classification"], "environment-drift")
        self.assertFalse(result["retry_performed"])

    def test_output_directory_claim_is_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "study"
            BENCH._claim_output_dir(output, "run-a")
            with self.assertRaisesRegex(BENCH.BenchError, "absent or empty|already owned"):
                BENCH._claim_output_dir(output, "run-b")

    def test_model_evidence_is_locally_redacted_before_retention(self) -> None:
        secret = "sk-proj-" + "a" * 48
        evidence = {
            "schema_version": "dev-flow.benchmark.evidence.v1",
            "cases": [{"response_text": secret}],
        }
        redacted = BENCH._redact_evidence(evidence)
        self.assertNotIn(secret, json.dumps(redacted))
        self.assertEqual(redacted["redaction_summary"]["finding_count"], 1)

    def test_observation_must_bind_the_selected_trial_evidence(self) -> None:
        selected = {"A"}
        evidence = {
            "cases": [
                {
                    "id": "A",
                    "turns": [{"turn": 1, "evidence_sha256": digest("actual")}],
                }
            ]
        }
        observations = {
            "schema_version": BENCH.OBSERVATIONS_SCHEMA,
            "cases": [
                {
                    "id": "A",
                    "turns": [{"turn": 1, "evidence_sha256": digest("different")}],
                }
            ],
        }
        with self.assertRaisesRegex(BENCH.BenchError, "not bound"):
            BENCH._validate_observation_binding(observations, evidence, selected)

    def test_compare_can_fail_for_automation_on_regression(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            baseline = root / "baseline.json"
            candidate = root / "candidate.json"
            baseline.write_text(json.dumps(graded_result([{"id": "A", "status": "matched"}])))
            candidate.write_text(
                json.dumps(
                    graded_result(
                        [{"id": "A", "status": "mismatched"}], candidate="candidate-b"
                    )
                )
            )
            result = BENCH.compare_results(
                baseline, candidate, fail_on_regression=True
            )
        self.assertEqual(result["status"], "regressed")


if __name__ == "__main__":
    unittest.main()
