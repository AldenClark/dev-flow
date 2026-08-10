#!/usr/bin/env python3
"""Stdlib-only behavioral and mutation tests for Dev Flow."""

from __future__ import annotations

import json
import hashlib
import os
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
FLOW = SCRIPTS / "dev-flow.py"
HOOK = ROOT / "hooks" / "dev_flow_hook.py"
PYTHON = sys.executable
AGENT_CONFIGS = ROOT / "skills" / "dev-flow" / "assets" / "agent-configs"
PAIRED_RUNNER = ROOT / "evals" / "run_paired_evaluations.py"
sys.path.insert(0, str(ROOT / "evals"))

import process_contracts as process_eval  # noqa: E402
import run_paired_evaluations as paired_eval  # noqa: E402


def run(*args: str, cwd: Path | None = None, stdin: str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, input=stdin, env=env, check=False, capture_output=True, text=True)


def write_features(path: Path) -> None:
    path.write_text("multi_agent stable true\nmulti_agent_v2 stable true\nhooks stable true\n", encoding="utf-8")


def write_config(path: Path, *, correct: bool = True) -> None:
    if correct:
        text = "[features]\nmulti_agent = true\nmulti_agent_v2 = true\nhooks = true\n\n[agents]\nmax_concurrent_threads_per_session = 3\n"
    else:
        text = "[features]\nmulti_agent = true\nhooks = true\n\n[features.multi_agent_v2]\nenabled = true\nmax_concurrent_threads_per_session = 4\n"
    path.write_text(text, encoding="utf-8")


def section_document(title: str, headings: dict[str, str]) -> str:
    parts = [f"# {title}\n"]
    for heading, body in headings.items():
        parts.append(f"## {heading}\n\n{body}\n")
    return "\n".join(parts)


def document_ambiguity(packet: Path, ambiguity_id: str) -> None:
    replacements = {
        "requirements.md": (
            "No semantic ambiguity was found after repository inspection and user confirmation.",
            f"{ambiguity_id} records the competing meanings, affected AC-1 and SC-D1, recommendation, and authorized resolution.",
        ),
        "execution.md": (
            "No verified finding required repair.",
            f"{ambiguity_id} was tracked to AC-1 and resolved before affected implementation continued.",
        ),
        "evidence.md": (
            "no ambiguity required a question or reopening.",
            f"{ambiguity_id} was resolved with its affected AC-1 and SC-D1 before approval.",
        ),
    }
    for filename, (old, new) in replacements.items():
        path = packet / filename
        path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")


def write_valid_packet(
    packet: Path,
    *,
    state: str = "verifying",
    schema_version: str = "1.0",
    collaboration_profile: str = "checkpointed",
    ui_impact: str = "none",
    requirement_approved: bool = True,
    ux_approved: bool = True,
    dependency_approved: bool = True,
    matrix_status: str = "PASSED",
    matrix_attempts: int = 1,
) -> None:
    for folder in ("briefs", "reports", "artifacts"):
        (packet / folder).mkdir(parents=True, exist_ok=True)
    now = "2026-08-08T00:00:00+00:00"
    metadata = {
        "schema_version": schema_version,
        "skill_version": "0.2.0",
        "change_id": "sample-change",
        "state": state,
        "documentation_profile": "full",
        "task_type": "routine",
        "created_at": now,
        "updated_at": now,
        "repository_roots": [str(packet.parent)],
        "base_git_state": "main at abc123, clean",
        "authority": "local edits and tests",
        "compatibility_required": False,
        "risk_modifiers": [],
        "acceptance_ids": ["AC-1"],
        "scope_ids": ["SC-D1"],
        "verification_ids": ["VO-1"],
        "dependency_changes": ["DEP-1"] if dependency_approved else [],
        "approvals": {
            "design": {"by": "user", "at": now, "note": "approved"},
            "dependencies": [{"id": "DEP-1", "by": "user", "at": now, "note": "approved"}] if dependency_approved else [],
            "waivers": [],
            "delivery": []
        },
        "history": [{"from": None, "to": "discovering", "at": now, "note": "created"}]
    }
    if schema_version in {"1.1", "1.2"}:
        metadata["collaboration_profile"] = collaboration_profile
        metadata["ui_impact"] = ui_impact
        metadata["approvals"]["requirements"] = (
            [{"id": "REQ-READY", "by": "user", "at": now, "note": "approved"}]
            if requirement_approved
            else []
        )
        metadata["approvals"]["ux"] = (
            [{"id": "UX-READY", "by": "user", "at": now, "note": "approved"}]
            if ux_approved
            else []
        )
        if state in {"awaiting-approval", "approved", "implementing", "verifying", "accepted", "archived"}:
            metadata["history"].append(
                {"from": "discovering", "to": "awaiting-approval", "at": now, "note": "ready for approval"}
            )
        if state in {"approved", "implementing", "verifying", "accepted", "archived"}:
            metadata["history"].append(
                {"from": "awaiting-approval", "to": "approved", "at": now, "note": "approved"}
            )
    if schema_version == "1.2":
        metadata["requirement_revision"] = 1
        metadata["requirements_digest"] = None
        metadata["ambiguity_ids"] = []
        metadata["ambiguities"] = []
    (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    docs = {
        "context.md": section_document("Change context: sample-change", {
            "Objective and authority": "Implement the confirmed bounded behavior with local edit and test authority.",
            "Repository facts": "The existing module and its direct caller were inspected at the recorded base state.",
            "Current behavior or reproduction": "The existing deterministic test demonstrates the missing result.",
            "Constraints and protected behavior": "The public interface and unrelated call paths remain unchanged.",
            "Assumptions and open questions": "No material assumption remains after repository inspection."
        }),
        "requirements.md": section_document("Change requirements: sample-change", {
            "Requirement delta": "The selected input now produces the confirmed output.",
            "Acceptance criteria": "- AC-1: The selected input returns the confirmed output while existing inputs remain stable.",
            "Non-functional requirements": "The change remains bounded and preserves existing performance.",
            "Compatibility and exclusions": "Compatibility is preserved; unrelated cleanup is excluded.",
            "Confirmation record": "The user approved the requirement and implementation scope."
        }),
        "design.md": section_document("Change design: sample-change", {
            "Decision": "Extend the existing branch at its current ownership boundary.",
            "Engineering preferences applied": "Use native idioms and the existing approved capability.",
            "Alternatives": "A parallel abstraction was rejected because it adds no stable variation axis.",
            "Architecture and failure behavior": "The caller retains ownership; the new branch returns the existing typed error on failure.",
            "Dependency decisions": "DEP-1 records the already approved exact test helper used by this fixture.",
            "Change scope": "SC-D1 changes the bounded branch; all other files remain protected.",
            "Compatibility, rollout, rollback, and cleanup": "Behavior is backward compatible and reverting the bounded edit restores the old path.",
            "Verification obligations": "VO-1 proves the new case and the nearby regression suite.",
            "Approval record": "The user approved the design, dependency decision, and local-only delivery scope."
        }),
        "execution.md": section_document("Change execution: sample-change", {
            "Task graph": "T1 maps INS-1, AC-1, and SC-D1 to VO-1 and is complete under root ownership.",
            "Progress ledger": "E1 recorded discovery; E2 recorded approval; E3 recorded implementation; E4 recorded final verification.",
            "Agent ledger": "The root performed the bounded task without child delegation.",
            "Decisions and drift": "D1 kept the change inside approved scope; no drift occurred.",
            "Environment and resource ownership": "The root owned the temporary test directory and released it.",
            "Findings and repair rounds": "No verified finding required repair.",
            "Blockers and next ready task": "No blocker remains; acceptance review is ready."
        }),
        "test-matrix.md": section_document("Test matrix: sample-change", {
            "Dimensions and selection rationale": "INS-1 requires the affected package and default configuration to cover the bounded contract.",
            "Resource ownership": "TM-1 used an isolated temporary directory owned by root.",
            "Cells": (
                "| Cell | Obligation | Environment | Level and oracle | Required | Attempts | Status | Evidence or blocker |\n"
                "|---|---|---|---|---|---:|---|---|\n"
                f"| TM-1 | VO-1 | Python 3.14 | regression command | yes | {matrix_attempts} | {matrix_status} | recorded artifact |"
            ),
            "Flaky triage": "No instability occurred across the required execution.",
            "Teardown and leaked resources": "The temporary directory and process state were released.",
            "Acceptance and release gates": f"TM-1 is required and recorded as {matrix_status}."
        }),
        "blue-audit.md": section_document("Blue audit: sample-change", {
            "Audit brief": "A clean read-only brief covered the approved contracts and final diff.",
            "Requirement and scope review": "INS-1, AC-1, and SC-D1 map completely; protected behavior is unchanged.",
            "Integration and maintainability review": "The change follows existing idioms, error handling, tests, and documentation.",
            "Findings": "No verified blue finding remains.",
            "Disposition": "Accepted after the final scoped review."
        }),
        "red-audit.md": section_document("Red audit: sample-change", {
            "Audit brief": "A clean read-only brief covered boundary and failure behavior.",
            "Threat and failure hypotheses": "INS-1 requires invalid input and unchanged neighboring inputs to be inspected.",
            "Adversarial checks": "The boundary test rejects invalid input using the existing typed error.",
            "Findings": "No verified red finding remains.",
            "Disposition": "Accepted after the final adversarial check."
        }),
        "evidence.md": section_document("Change evidence: sample-change", {
            "Acceptance traceability": "AC-1 maps to the changed branch, exact regression command, and PASSED result.",
            "Commands and results": "The exact command ran at the absolute root on 2026-08-08T00:00:00+00:00 with exit 0 and one passed test.",
            "Audit summary": "Static, blue, and red checks completed with no verified findings.",
            "Test matrix summary": f"VO-1 maps to TM-1 with status {matrix_status}.",
            "Changed-file accounting": "SC-D1 accounts for the only product file change.",
            "Residual risks and remaining gates": "No residual gate remains for local acceptance.",
            "Delivery status": "Local implementation and verification only; no commit, push, release, deploy, or external message."
        }),
        "decisions.md": section_document("Decision record: sample-change", {
            "Decision ledger": "D1 selects the repository-native bounded branch.",
            "Approval ledger": "The user approved design and DEP-1 for local implementation and tests.",
            "Source registry": "Repository source and the deterministic regression test are the primary evidence.",
            "Superseded decisions": "No decision was superseded."
        })
    }
    if schema_version in {"1.1", "1.2"}:
        docs["context.md"] = section_document("Change context: sample-change", {
            "Objective and authority": "Implement the confirmed bounded behavior with local edit and test authority.",
            "Repository facts": "The existing module and its direct caller were inspected at the recorded base state.",
            "Instruction and convention ledger": "INS-1 maps the repository test rule to VO-1 and final evidence.",
            "Collaboration and readiness": "The checkpointed profile is Instruction Ready, Requirement Ready, and Design Ready; UX is not applicable.",
            **({"Semantic input and ambiguity ownership": "The bounded input is complete; repository facts were investigated; no material semantic ambiguity remains."} if schema_version == "1.2" else {}),
            "Current behavior or reproduction": "The existing deterministic test demonstrates the missing result.",
            "Constraints and protected behavior": "The public interface and unrelated call paths remain unchanged.",
            "Assumptions and open questions": "No material assumption remains after repository inspection."
        })
        docs["requirements.md"] = section_document("Change requirements: sample-change", {
            "User and product outcome": "The caller receives the expected bounded result without changing neighboring behavior.",
            "Requirement delta": "The selected input now produces the confirmed output.",
            "Acceptance criteria": "- AC-1: The selected input returns the confirmed output while existing inputs remain stable.",
            "Non-functional requirements": "The change remains bounded and preserves existing performance.",
            "Compatibility and exclusions": "Compatibility is preserved; unrelated cleanup is excluded.",
            "Requirement Ready gate": "Requirement Ready is approved from repository evidence and the user decision.",
            **({
                "Requirement baseline": "Revision 1 is bound to the exact requirements document by its recorded SHA-256 digest.",
                "Ambiguity ledger": "No semantic ambiguity was found after repository inspection and user confirmation.",
            } if schema_version == "1.2" else {}),
            "Confirmation record": "The user approved the requirement and implementation scope."
        })
        docs["design.md"] = section_document("Change design: sample-change", {
            "Decision": "Extend the existing branch at its current ownership boundary.",
            "Engineering preferences applied": "INS-1 requires the repository test rule; use native idioms and the existing approved capability.",
            "Alternatives": "A parallel abstraction was rejected because it adds no stable variation axis.",
            "Architecture and failure behavior": "The caller retains ownership; the new branch returns the existing typed error on failure.",
            "Product and UX contract": "UI impact is none, so UX Ready is not applicable.",
            **({"Requirement baseline and reopening": "Revision 1 is bound to the current digest; a late material ambiguity reopens approval."} if schema_version == "1.2" else {}),
            "Dependency decisions": "DEP-1 records the already approved exact test helper used by this fixture.",
            "Change scope": "SC-D1 changes the bounded branch; all other files remain protected.",
            "Compatibility, rollout, rollback, and cleanup": "Behavior is backward compatible and reverting the bounded edit restores the old path.",
            "Verification obligations": "VO-1 proves the new case and the nearby regression suite.",
            "Approval record": "The user approved the design, dependency decision, and local-only delivery scope."
        })
        docs["evidence.md"] = section_document("Change evidence: sample-change", {
            "Acceptance traceability": "AC-1 maps to the changed branch, exact regression command, and PASSED result.",
            "Instruction, collaboration, and UX evidence": "INS-1 is verified by VO-1; checkpointed readiness is recorded; UX is not applicable.",
            **({"Semantic clarification evidence": "Revision 1 and its digest match readiness and design approval; no ambiguity required a question or reopening."} if schema_version == "1.2" else {}),
            "Commands and results": "The exact command ran at the absolute root on 2026-08-08T00:00:00+00:00 with exit 0 and one passed test.",
            "Audit summary": "Static, blue, and red checks completed with no verified findings.",
            "Test matrix summary": f"VO-1 maps to TM-1 with status {matrix_status}.",
            "Changed-file accounting": "SC-D1 accounts for the only product file change.",
            "Residual risks and remaining gates": "No residual gate remains for local acceptance.",
            "Delivery status": "Local implementation and verification only; no commit, push, release, deploy, or external message."
        })
        if schema_version == "1.2":
            for audit in ("blue-audit.md", "red-audit.md"):
                source = docs[audit]
                insertion = "\n## Finding classification and requirement reopening\n\nThe review found no requirement ambiguity; no reopening is required.\n"
                source = source.replace("\n## Findings\n", insertion + "\n## Findings\n")
                docs[audit] = source
    for filename, text in docs.items():
        (packet / filename).write_text(text, encoding="utf-8")
    if schema_version == "1.2":
        digest = f"sha256:{hashlib.sha256((packet / 'requirements.md').read_bytes()).hexdigest()}"
        metadata["requirements_digest"] = digest
        for record in metadata["approvals"]["requirements"]:
            record["requirement_revision"] = 1
            record["requirements_digest"] = digest
        if isinstance(metadata["approvals"]["design"], dict):
            metadata["approvals"]["design"]["requirement_revision"] = 1
            metadata["approvals"]["design"]["requirements_digest"] = digest
        (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")


class PreflightTests(unittest.TestCase):
    def test_accepts_current_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            write_features(features)
            write_config(config)
            result = run(PYTHON, str(FLOW), "preflight", "--version-output", "codex-cli 0.147.0", "--features-output-file", str(features), "--config", str(config), "--tool-surface-confirmed")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "ready")

    def test_rejects_old_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            write_features(features)
            write_config(config)
            result = run(PYTHON, str(FLOW), "preflight", "--version-output", "codex-cli 0.146.9", "--features-output-file", str(features), "--config", str(config), "--require-delegation")
            self.assertEqual(result.returncode, 2)
            self.assertIn("below delegation-tested", result.stdout)

    def test_rejects_obsolete_config_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            write_features(features)
            write_config(config, correct=False)
            result = run(PYTHON, str(FLOW), "preflight", "--version-output", "codex-cli 0.147.0", "--features-output-file", str(features), "--config", str(config), "--require-delegation")
            self.assertEqual(result.returncode, 2)
            self.assertIn("obsolete", result.stdout)

    def test_core_workflow_degrades_without_delegation_capabilities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            features.write_text("multi_agent stable false\nmulti_agent_v2 stable false\nhooks stable false\n", encoding="utf-8")
            write_config(config, correct=False)
            result = run(
                PYTHON,
                str(FLOW),
                "preflight",
                "--version-output",
                "codex-cli 0.146.9",
                "--features-output-file",
                str(features),
                "--config",
                str(config),
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "degraded")
            self.assertTrue(payload["capabilities"]["core_workflow"])
            self.assertFalse(payload["capabilities"]["delegation"])

    def test_malformed_config_shapes_degrade_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            write_features(features)
            config.write_text('features = "invalid"\nagents = []\n', encoding="utf-8")
            result = run(
                PYTHON,
                str(FLOW),
                "preflight",
                "--version-output",
                "codex-cli 0.147.0",
                "--features-output-file",
                str(features),
                "--config",
                str(config),
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertIn("[features] must be a table", result.stdout)


class PairedEvaluationRunnerTests(unittest.TestCase):
    def test_program_command_split_preserves_windows_paths_without_a_shell(self) -> None:
        command = r'"C:\Program Files\Python\python.exe" "C:\Temp Dir\executor.py" --flag'
        self.assertEqual(
            paired_eval.split_program_command(command, windows=True),
            [r"C:\Program Files\Python\python.exe", r"C:\Temp Dir\executor.py", "--flag"],
        )

    def test_documented_bundled_adapter_is_bound_before_isolated_cwd(self) -> None:
        command = paired_eval.split_program_command(
            "python3 evals/codex_model_adapter.py executor --model test-model"
        )
        bound = paired_eval.bind_bundled_adapter_command(command)
        self.assertEqual(bound[0], "python3")
        self.assertEqual(bound[1], str(ROOT / "evals" / "codex_model_adapter.py"))
        self.assertEqual(bound[2:], command[2:])
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp) / "isolated-evidence"
            parsed, error, _ = paired_eval.run_program(
                [PYTHON, bound[1], "executor", "--model", "test-model"],
                {"bounded": True},
                run_root,
                2,
            )
            self.assertIsNone(parsed)
            self.assertEqual(error, "program exited 2")
            self.assertIn(
                "executor request is missing case_id or fixture",
                (run_root / "stderr.txt").read_text(encoding="utf-8"),
            )

    def test_external_executor_arguments_are_not_rewritten(self) -> None:
        commands = (
            ["external-evaluator", "evals/codex_model_adapter.py"],
            ["python3", "custom_executor.py", "evals/codex_model_adapter.py"],
            ["python3", "-I", "evals/codex_model_adapter.py"],
        )
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(paired_eval.bind_bundled_adapter_command(command), command)

    def test_supported_python_executable_spellings_bind_the_bundled_adapter(self) -> None:
        script = "evals/codex_model_adapter.py"
        self.assertEqual(
            paired_eval.bind_bundled_adapter_command([script, "executor"]),
            [str(ROOT / script), "executor"],
        )
        for executable in ("python", "python3", "python3.11", "Python", r"C:\Python311\python.exe"):
            with self.subTest(executable=executable):
                bound = paired_eval.bind_bundled_adapter_command([executable, script, "executor"])
                self.assertEqual(bound, [executable, str(ROOT / script), "executor"])

    def test_empty_executor_command_remains_invalid_without_traceback(self) -> None:
        self.assertEqual(paired_eval.bind_bundled_adapter_command([]), [])

    def test_runner_isolates_repeated_first_attempts_and_aggregates_deltas(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executor = root / "executor.py"
            grader = root / "grader.py"
            output = root / "output"
            executor.write_text(
                """import json
import pathlib
import sys
request = json.load(sys.stdin)
candidate = bool(request["capabilities"])
artifacts = pathlib.Path("artifacts")
artifacts.mkdir()
print(json.dumps({
    "case_id": request["case_id"],
    "attempt": 1,
    "artifact_root": "artifacts",
    "claimed_outcome": "completed",
    "actions": ["capability-applied" if candidate else "baseline-action"],
    "evidence": ["isolated first attempt"],
    "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
    "usage": {"tokens": 20 if candidate else 10, "elapsed_seconds": 0.1, "cost": 0.01}
}))
""",
                encoding="utf-8",
            )
            grader.write_text(
                """import json
import sys
request = json.load(sys.stdin)
candidate = request["executor_result"]["actions"] == ["capability-applied"]
score = 4 if candidate else 2
print(json.dumps({
    "case_id": request["case_id"],
    "graded_attempt": 1,
    "requirement_fidelity": score,
    "scope_discipline": score,
    "evidence_quality": score,
    "forbidden_actions": [],
    "structural_coverage": ["bounded"],
    "metrics": {"coverage": score, "restraint": score, "ordinary_defect_retention": score, "actionability": score, "rework": 0 if candidate else 2, "unsafe_actions": 0, "false_blocks": 0},
    "verdict": "pass" if candidate else "fail"
}))
""",
                encoding="utf-8",
            )
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                f"{PYTHON} {executor}",
                "--grader",
                f"{PYTHON} {grader}",
                "--output",
                str(output),
                "--pair",
                "PAIR-ECR",
                "--trials",
                "3",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual((report["status"], len(report["records"])), ("complete", 6))
            self.assertEqual(report["aggregates"]["candidate"]["pass_rate"], 1.0)
            self.assertEqual(report["aggregates"]["baseline"]["pass_rate"], 0.0)
            self.assertEqual(report["pair_aggregates"]["PAIR-ECR"]["candidate"]["pass_rate"], 1.0)
            self.assertEqual(report["candidate_minus_baseline"]["usage"]["tokens"], 10.0)
            self.assertEqual(report["metric_contract"], list(paired_eval.CONTRACT_METRICS))
            self.assertEqual(report["evaluation_plan"]["mode"], "pilot")
            self.assertEqual(report["aggregates"]["candidate"]["contract_metrics"]["ordinary_defect_retention"]["mean"], 4.0)
            self.assertEqual(report["aggregates"]["candidate"]["contract_metrics"]["reminder_rate"]["mean"], 0.0)
            self.assertFalse(report["release_assessment"]["release_ready"])
            self.assertEqual(
                next(item for item in report["release_assessment"]["gates"] if item["gate"] == "evaluation-completeness")["status"],
                "passed",
            )
            self.assertEqual(
                next(item for item in report["release_assessment"]["gates"] if item["gate"] == "context-cost-ratio")["status"],
                "failed",
            )
            self.assertEqual(
                next(item for item in report["release_assessment"]["gates"] if item["gate"] == "release-plan-completeness")["status"],
                "not-evaluable",
            )
            self.assertTrue(all(item["executor"]["attempt"] == 1 for item in report["records"]))
            grader_request_path = next((output / "grader-runs").glob("*/request.json"))
            grader_request = json.loads(grader_request_path.read_text(encoding="utf-8"))
            self.assertNotIn("variant", grader_request)
            self.assertNotIn("capabilities", grader_request)
            self.assertNotIn("condition", grader_request)
            self.assertNotIn("baseline", str(grader_request_path))
            self.assertNotIn("candidate", str(grader_request_path))
            self.assertNotIn("baseline", grader_request["executor_result"]["artifact_root"])
            self.assertNotIn("candidate", grader_request["executor_result"]["artifact_root"])
            self.assertFalse(Path(grader_request["executor_result"]["artifact_root"]).is_relative_to(output))

            incomplete_candidate = {**report["aggregates"]["candidate"], "valid_grader_runs": 2}
            thresholds = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))["release_thresholds"]
            incomplete_assessment = paired_eval.assess_release(
                incomplete_candidate,
                report["aggregates"]["baseline"],
                thresholds,
                report["evaluation_plan"],
            )
            self.assertFalse(incomplete_assessment["release_ready"])
            self.assertEqual(
                next(item for item in incomplete_assessment["gates"] if item["gate"] == "evaluation-completeness")["status"],
                "failed",
            )

            perfect_pilot = paired_eval.assess_release(
                report["aggregates"]["candidate"],
                report["aggregates"]["candidate"],
                thresholds,
                report["evaluation_plan"],
            )
            self.assertTrue(perfect_pilot["pilot_thresholds_passed"])
            self.assertFalse(perfect_pilot["release_ready"])

            canonical_bytes = (ROOT / "evals" / "paired-evaluations.json").read_bytes()
            canonical = json.loads(canonical_bytes)
            head = run("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip()
            input_snapshot = paired_eval.evaluation_input_snapshot(canonical, head)[1]
            expected_runs = len(canonical["release_plan"]["pair_ids"]) * canonical["release_plan"]["trials_per_pair"]
            full_candidate = {
                **report["aggregates"]["candidate"],
                "runs": expected_runs,
                "valid_executor_runs": expected_runs,
                "valid_grader_runs": expected_runs,
            }
            release_plan = {
                "mode": "release",
                "config_schema_version": "1.1",
                "required_pair_ids": canonical["release_plan"]["pair_ids"],
                "evaluated_pair_ids": canonical["release_plan"]["pair_ids"],
                "required_trials_per_pair": canonical["release_plan"]["trials_per_pair"],
                "actual_trials_per_pair": canonical["release_plan"]["trials_per_pair"],
                "config_sha256": "sha256:" + hashlib.sha256(canonical_bytes).hexdigest(),
                "input_snapshot": input_snapshot,
                "source_identity": {
                    "status": "matched-clean-commit",
                    "preflight": {"expected_commit": head},
                },
                "config_identity": {"status": "matched-canonical-commit"},
            }
            complete_assessment = paired_eval.assess_release(
                full_candidate,
                full_candidate,
                thresholds,
                release_plan,
            )
            self.assertTrue(complete_assessment["release_ready"])

    def test_executor_artifacts_must_be_a_strict_descendant_not_the_control_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            result = {
                "case_id": "PAIR-ECR",
                "attempt": 1,
                "artifact_root": str(run_root),
                "claimed_outcome": "completed",
                "actions": ["bounded"],
                "evidence": ["bounded"],
                "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
                "usage": {"tokens": 1, "elapsed_seconds": 0.1, "cost": 0.0},
            }
            with self.assertRaisesRegex(paired_eval.EvaluationError, "strict descendant"):
                paired_eval.validate_executor(result, run_root, "PAIR-ECR")

    def test_runner_rejects_pair_id_path_escape_before_creating_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
            config["pairs"] = [{**config["pairs"][0], "id": "../escaped"}]
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                "unused",
                "--grader",
                "unused",
                "--config",
                str(config_path),
                "--output",
                str(output),
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("safe", result.stderr)
            self.assertFalse((root / "escaped").exists())
            self.assertFalse(output.exists())

    def test_runner_rejects_declared_metric_drift(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config["metrics"].remove("ordinary_defect_retention")
        with self.assertRaisesRegex(paired_eval.EvaluationError, "metrics must exactly match"):
            paired_eval.validate_config(config)

    def test_legacy_config_without_release_thresholds_uses_safe_defaults(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config.pop("release_thresholds")
        validated = paired_eval.validate_config(config)
        self.assertEqual(validated["release_thresholds"], paired_eval.DEFAULT_RELEASE_THRESHOLDS)

    def test_schema_1_config_without_release_plan_remains_a_valid_pilot(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config["schema_version"] = "1.0"
        config.pop("release_plan")
        validated = paired_eval.validate_config(config)
        self.assertNotIn("release_plan", validated)

    def test_release_input_snapshot_reads_immutable_commit_blobs(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        head = run("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip()
        inputs, snapshot = paired_eval.evaluation_input_snapshot(config, head)
        expected_fixture = subprocess.run(
            ["git", "show", f"{head}:evals/{config['pairs'][0]['fixture']}"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout
        self.assertEqual(inputs[config["pairs"][0]["id"]]["fixture"], expected_fixture)
        self.assertEqual(snapshot["source"], "git-commit")
        self.assertEqual(snapshot["commit"], head)
        self.assertGreater(len(snapshot["entries"]), len(config["pairs"]))

    def test_release_mode_rejects_external_self_declared_plan_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
            config["pairs"] = [config["pairs"][0]]
            config["release_plan"] = {"pair_ids": [config["pairs"][0]["id"]], "trials_per_pair": 3}
            config_path = root / "self-declared.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"
            result = run(
                PYTHON, str(PAIRED_RUNNER), "--executor", "unused", "--grader", "unused",
                "--config", str(config_path), "--output", str(output), "--release",
                "--expected-commit", "a" * 40,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("canonical config", result.stderr)
            self.assertFalse(output.exists())

    def test_release_postflight_source_drift_invalidates_assessment(self) -> None:
        plan = {
            "mode": "release",
            "config_schema_version": "1.1",
            "required_pair_ids": ["PAIR-ECR"],
            "evaluated_pair_ids": ["PAIR-ECR"],
            "required_trials_per_pair": 3,
            "actual_trials_per_pair": 3,
            "source_identity": {"status": "pending-postflight", "preflight": {"status": "matched-clean-commit"}},
            "config_identity": {"status": "pending-postflight", "preflight": {"status": "matched-canonical-commit"}},
        }
        with mock.patch.object(paired_eval, "source_identity", return_value={"status": "not-release-bound"}), mock.patch.object(
            paired_eval, "config_identity", return_value={"status": "matched-canonical-commit"}
        ):
            errors = paired_eval.finalize_release_identity(
                plan, config_path=paired_eval.CANONICAL_CONFIG,
                config_digest="sha256:" + "0" * 64, expected_commit="a" * 40,
            )
        self.assertIn("source identity changed", errors[0])
        self.assertEqual(plan["source_identity"]["status"], "source-drift-detected")

    def test_owned_process_timeout_reaps_descendants_and_bounds_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            marker = root / "leaked-child"
            parent = root / "parent.py"
            child_code = (
                "import pathlib,time; time.sleep(2); "
                f"pathlib.Path({str(marker)!r}).write_text('leaked', encoding='utf-8')"
            )
            parent.write_text(
                "import subprocess,sys,time\n"
                f"subprocess.Popen([sys.executable, '-c', {child_code!r}])\n"
                "time.sleep(10)\n",
                encoding="utf-8",
            )
            timed = process_eval.run_owned_process(
                [PYTHON, str(parent)],
                "{}",
                cwd=root,
                timeout=0.1,
                output_limit=1024,
            )
            self.assertIn("timed out", timed.error or "")
            time.sleep(2.2)
            self.assertFalse(marker.exists())

            noisy = process_eval.run_owned_process(
                [PYTHON, "-c", "print('x' * 4096)"],
                "{}",
                cwd=root,
                timeout=2,
                output_limit=64,
            )
            self.assertIn("output exceeded", noisy.error or "")
            self.assertLessEqual(len(noisy.stdout.encode("utf-8")), 64)

            blocked_input = process_eval.run_owned_process(
                [PYTHON, "-c", "import time; time.sleep(10)"],
                "x" * (2 * 1024 * 1024),
                cwd=root,
                timeout=0.1,
                output_limit=64,
            )
            self.assertIn("timed out", blocked_input.error or "")
            self.assertLess(blocked_input.elapsed_seconds, 2)

    def test_runner_output_does_not_follow_a_preexisting_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            run_root = root / "run"
            run_root.mkdir()
            victim = root / "victim"
            victim.write_text("SAFE\n", encoding="utf-8")
            try:
                (run_root / "stdout.txt").symlink_to(victim)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            parsed, error, _ = paired_eval.run_program(
                [PYTHON, "-c", "print('{}')"],
                {"bounded": True},
                run_root,
                2,
            )
            self.assertIsNone(parsed)
            self.assertIn("cannot record program output", error or "")
            self.assertEqual(victim.read_text(encoding="utf-8"), "SAFE\n")

    def test_runner_rejects_fewer_than_three_trials(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                "unused",
                "--grader",
                "unused",
                "--output",
                str(root / "output"),
                "--trials",
                "2",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("at least three", result.stderr)

    def test_release_mode_rejects_subset_before_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "output"
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                "unused",
                "--grader",
                "unused",
                "--output",
                str(output),
                "--pair",
                "PAIR-ECR",
                "--trials",
                "5",
                "--release",
                "--expected-commit",
                "a" * 40,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("complete configured pair set", result.stderr)
            self.assertFalse(output.exists())


class PacketTests(unittest.TestCase):
    def test_valid_semantic_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet)
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_accepted_packet_rejects_blocked_context_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted")
            (packet / "context-readiness.json").write_text(json.dumps({"schema_version": "1.0", "tier": "T3", "outcome": "blocked", "fingerprint": "sha256:" + "0" * 64}), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("cannot retain a context-readiness", result.stdout)

    def test_accepted_audit_gate_uses_finding_status_not_prose(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted")
            blue = packet / "blue-audit.md"
            blue.write_text(
                blue.read_text(encoding="utf-8")
                + "\nThe fail-open behavior and requirement reopening path were verified; no finding remains actionable.\n",
                encoding="utf-8",
            )
            prose = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(prose.returncode, 0, prose.stderr or prose.stdout)
            self.assertEqual(json.loads(prose.stdout)["warnings"], [])

            blue.write_text(
                blue.read_text(encoding="utf-8")
                + "\n| BLUE-7: bounded regression | major | exact path | focused check | open |\n",
                encoding="utf-8",
            )
            finding = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(finding.returncode, 2, finding.stderr or finding.stdout)
            self.assertTrue(any("BLUE-7" in item for item in json.loads(finding.stdout)["errors"]))

            blue.write_text(
                blue.read_text(encoding="utf-8").replace(
                    "| BLUE-7: bounded regression | major | exact path | focused check | open |",
                    "| BLUE-7: bounded regression | major | exact path | focused check | pending-review |",
                ),
                encoding="utf-8",
            )
            unknown = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(unknown.returncode, 2)
            self.assertIn("status must be closed", unknown.stdout)

            blue.write_text(
                blue.read_text(encoding="utf-8").replace(
                    "| BLUE-7: bounded regression | major | exact path | focused check | pending-review |",
                    "| BLUE-7 | malformed |",
                ),
                encoding="utf-8",
            )
            malformed = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("malformed finding row", malformed.stdout)

    def test_accepted_waived_cell_requires_an_applicable_current_waiver(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted", matrix_status="WAIVED")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["waivers"] = [
                {
                    "id": "WAIVER-OLD",
                    "by": "owner",
                    "note": "unrelated expired waiver",
                    "scope": ["src/**"],
                    "blockers": ["different-blocker"],
                    "residual_risk": "unrelated risk",
                    "expires_at": "2020-01-01T00:00:00Z",
                    "recheck_trigger": "unrelated-change",
                }
            ]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            rejected = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(rejected.returncode, 2, rejected.stderr or rejected.stdout)
            self.assertIn("applicable waiver", rejected.stdout)

            metadata["approvals"]["waivers"] = [
                {
                    "id": "WAIVER-TM-1",
                    "by": "owner",
                    "note": "accept this exact omitted verification",
                    "scope": ["TM-1"],
                    "blockers": ["TM-1"],
                    "residual_risk": "the exact regression was not executed",
                    "expires_at": "2999-01-01T00:00:00Z",
                    "recheck_trigger": "verification-environment-available",
                }
            ]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            accepted = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(accepted.returncode, 0, accepted.stderr or accepted.stdout)

    def test_deactivate_packet_removes_only_a_matching_terminal_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            flow = Path(temp) / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            write_valid_packet(packet, state="accepted")
            current = flow / "current"
            current.write_text("sample-change\n", encoding="utf-8")

            result = run(PYTHON, str(FLOW), "deactivate-packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "deactivated")
            self.assertFalse(current.exists())
            self.assertTrue(packet.is_dir())
            self.assertTrue((packet / "packet.json").is_file())

            repeated = run(PYTHON, str(FLOW), "deactivate-packet", str(packet))
            self.assertEqual(repeated.returncode, 0, repeated.stderr or repeated.stdout)
            self.assertEqual(json.loads(repeated.stdout)["status"], "unchanged")

    def test_deactivate_packet_refuses_active_or_mismatched_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            flow = Path(temp) / ".codex" / "dev-flow"
            active = flow / "active-change"
            write_valid_packet(active, state="verifying")
            current = flow / "current"
            current.write_text("active-change\n", encoding="utf-8")
            active_result = run(PYTHON, str(FLOW), "deactivate-packet", str(active))
            self.assertEqual(active_result.returncode, 2)
            self.assertIn("accepted or archived", active_result.stdout)
            self.assertEqual(current.read_text(encoding="utf-8"), "active-change\n")

            accepted = flow / "accepted-change"
            write_valid_packet(accepted, state="accepted")
            mismatched = run(PYTHON, str(FLOW), "deactivate-packet", str(accepted))
            self.assertEqual(mismatched.returncode, 2)
            self.assertIn("not 'accepted-change'", mismatched.stdout)
            self.assertEqual(current.read_text(encoding="utf-8"), "active-change\n")

    def test_deactivate_packet_refuses_symlink_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            flow = Path(temp) / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            write_valid_packet(packet, state="accepted")
            outside = Path(temp) / "outside-current"
            outside.write_text("sample-change\n", encoding="utf-8")
            current = flow / "current"
            try:
                current.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")

            result = run(PYTHON, str(FLOW), "deactivate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("must not be a symlink", result.stdout)
            self.assertEqual(outside.read_text(encoding="utf-8"), "sample-change\n")

    def test_init_packet_refuses_symlink_current_without_overwriting_target(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            flow.mkdir(parents=True)
            outside = root / "outside-current"
            outside.write_text("SAFE\n", encoding="utf-8")
            try:
                (flow / "current").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            result = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "safe-packet",
                "--task-type",
                "routine",
                "--objective",
                "Do not follow current symlinks",
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("must not traverse a symlink", result.stdout)
            self.assertEqual(outside.read_text(encoding="utf-8"), "SAFE\n")
            self.assertFalse((flow / "safe-packet").exists())

    def test_deactivate_archived_packet_is_idempotent_and_preserves_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            flow = Path(temp) / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            write_valid_packet(packet, state="accepted")
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            archived = run(PYTHON, str(FLOW), "archive-packet", str(packet), "--note", "archive accepted fixture")
            self.assertEqual(archived.returncode, 0, archived.stderr or archived.stdout)
            archive_path = flow / "archive" / "sample-change"
            self.assertTrue(archive_path.is_dir())
            self.assertFalse((flow / "current").exists())

            result = run(PYTHON, str(FLOW), "deactivate-packet", str(archive_path))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "unchanged")
            self.assertTrue((archive_path / "packet.json").is_file())

    def test_waiver_approval_requires_scoped_expiring_risk_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet)
            weak = run(PYTHON, str(FLOW), "record-approval", str(packet), "waivers", "--id", "WAIVER-1", "--by", "owner", "--note", "skip")
            self.assertEqual(weak.returncode, 2)
            strong = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "waivers",
                "--id", "WAIVER-1", "--by", "owner", "--note", "accept residual risk",
                "--scope", "src/**", "--blocker", "governed-quality-outcome-uncovered",
                "--residual-risk", "manual review may miss a defect",
                "--expires-at", "2999-01-01T00:00:00Z", "--recheck-trigger", "control-change",
            )
            self.assertEqual(strong.returncode, 0, strong.stderr or strong.stdout)

    def test_valid_schema_1_1_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_valid_schema_1_2_packet_and_digest_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.2")
            valid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

            requirements = packet / "requirements.md"
            requirements.write_text(requirements.read_text(encoding="utf-8") + "\nA late semantic edit.\n", encoding="utf-8")
            stale = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(stale.returncode, 2)
            self.assertIn("requirements changed", stale.stdout)

    def test_schema_1_2_ambiguity_requires_authorized_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="awaiting-approval", schema_version="1.2", requirement_approved=False)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Whether the default changes",
                "--source", "short user request",
                "--interpretation", "change only explicit calls",
                "--interpretation", "change every call",
                "--materiality", "material",
                "--owner", "user",
                "--affects", "AC-1",
                "--affects", "SC-D1",
                "--recommendation", "preserve existing defaults",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            document_ambiguity(packet, "AMB-1")
            blocked = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "requirements",
                "--id", "REQ-READY", "--by", "user", "--note", "approve",
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("remains open", blocked.stdout)

            resolved = run(
                PYTHON, str(FLOW), "resolve-ambiguity", str(packet),
                "--id", "AMB-1", "--status", "user-confirmed", "--by", "user",
                "--resolution", "preserve the default", "--evidence", "user decision in task",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            readiness = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "requirements",
                "--id", "REQ-READY", "--by", "user", "--note", "approved resolved baseline",
            )
            self.assertEqual(readiness.returncode, 0, readiness.stderr or readiness.stdout)
            approved = run(
                PYTHON, str(FLOW), "transition", str(packet), "approved",
                "--note", "approve design", "--approved-by", "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            valid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_schema_1_2_rejects_codex_substitution_for_material_user_decision(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="awaiting-approval", schema_version="1.2", requirement_approved=False)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Product behavior", "--source", "requirement",
                "--interpretation", "behavior A", "--interpretation", "behavior B",
                "--materiality", "material", "--owner", "user", "--affects", "AC-1",
                "--recommendation", "behavior A",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            substituted = run(
                PYTHON, str(FLOW), "resolve-ambiguity", str(packet), "--id", "AMB-1",
                "--status", "resolved-by-evidence", "--by", "codex",
                "--resolution", "choose A", "--evidence", "agent preference",
            )
            self.assertEqual(substituted.returncode, 2)
            self.assertIn("user confirmation", substituted.stdout)

    def test_schema_1_2_late_material_ambiguity_reopens_and_invalidates_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="implementing", schema_version="1.2")
            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Audit found contract ambiguity", "--source", "red audit",
                "--interpretation", "reject legacy input", "--interpretation", "accept legacy input",
                "--materiality", "high-risk", "--owner", "user", "--affects", "AC-1",
                "--recommendation", "preserve legacy input pending user decision",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            document_ambiguity(packet, "AMB-1")
            reopened = run(
                PYTHON, str(FLOW), "transition", str(packet), "awaiting-approval",
                "--note", "late contract ambiguity", "--ambiguity-id", "AMB-1",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["requirement_revision"], 2)
            self.assertIsNone(metadata["requirements_digest"])
            self.assertIsNone(metadata["approvals"]["design"])
            self.assertEqual(len(metadata["approvals"]["design_history"]), 1)

            resolved = run(
                PYTHON, str(FLOW), "resolve-ambiguity", str(packet), "--id", "AMB-1",
                "--status", "user-confirmed", "--by", "user",
                "--resolution", "preserve legacy input", "--evidence", "user confirmation",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            stale = run(
                PYTHON, str(FLOW), "transition", str(packet), "approved",
                "--note", "try stale approval", "--approved-by", "user",
            )
            self.assertEqual(stale.returncode, 2)
            self.assertIn("Requirement Ready", stale.stdout)
            fresh = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "requirements",
                "--id", "REQ-READY", "--by", "user", "--note", "approve revision two",
            )
            self.assertEqual(fresh.returncode, 0, fresh.stderr or fresh.stdout)
            approved = run(
                PYTHON, str(FLOW), "transition", str(packet), "approved",
                "--note", "approve revised design", "--approved-by", "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)

    def test_schema_1_2_blocked_route_cannot_bypass_late_reopening(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="implementing", schema_version="1.2")
            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Blocked late ambiguity", "--source", "audit",
                "--interpretation", "A", "--interpretation", "B",
                "--materiality", "material", "--owner", "user", "--affects", "AC-1",
                "--recommendation", "A",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            document_ambiguity(packet, "AMB-1")
            blocked = run(PYTHON, str(FLOW), "transition", str(packet), "blocked", "--note", "waiting")
            self.assertEqual(blocked.returncode, 0, blocked.stderr or blocked.stdout)
            discovery_bypass = run(
                PYTHON, str(FLOW), "transition", str(packet), "discovering", "--note", "try discovery route"
            )
            self.assertEqual(discovery_bypass.returncode, 2)
            self.assertIn("must reopen through awaiting-approval", discovery_bypass.stdout)
            bypass = run(PYTHON, str(FLOW), "transition", str(packet), "awaiting-approval", "--note", "resume")
            self.assertEqual(bypass.returncode, 2)
            self.assertIn("--ambiguity-id", bypass.stdout)

            reopened = run(
                PYTHON, str(FLOW), "transition", str(packet), "awaiting-approval",
                "--note", "resume with semantic reopening", "--ambiguity-id", "AMB-1",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["requirement_revision"], 2)
            self.assertIsNone(metadata["requirements_digest"])
            self.assertIsNone(metadata["approvals"]["design"])
            self.assertEqual(len(metadata["approvals"]["design_history"]), 1)

    def test_schema_1_2_material_user_ambiguity_escalates_execute_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="discovering",
                schema_version="1.2",
                collaboration_profile="execute",
                requirement_approved=False,
            )
            result = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Scope boundary", "--source", "short request",
                "--interpretation", "one caller", "--interpretation", "all callers",
                "--materiality", "material", "--owner", "user", "--affects", "SC-D1",
                "--recommendation", "one caller",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["collaboration_profile"], "checkpointed")

    def test_schema_1_2_clear_execute_mode_avoids_ceremonial_requirement_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="awaiting-approval",
                schema_version="1.2",
                collaboration_profile="execute",
                requirement_approved=False,
            )
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            approved = run(
                PYTHON, str(FLOW), "transition", str(packet), "approved",
                "--note", "explicit implementation request authorizes the unambiguous baseline",
                "--approved-by", "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["approvals"]["requirements"], [])
            self.assertRegex(metadata["requirements_digest"], r"^sha256:[0-9a-f]{64}$")
            self.assertEqual(
                metadata["approvals"]["design"]["requirements_digest"],
                metadata["requirements_digest"],
            )

        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="awaiting-approval",
                schema_version="1.2",
                collaboration_profile="execute",
                requirement_approved=False,
            )
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            metadata["history"][-1]["at"] = "2099-01-01T00:00:00+00:00"
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            future_history = run(
                PYTHON, str(FLOW), "transition", str(packet), "approved",
                "--note", "invalid future history", "--approved-by", "user",
            )
            self.assertEqual(future_history.returncode, 2)
            self.assertIn("history cannot be in the future", future_history.stdout)

    def test_schema_1_2_malformed_ambiguity_container_is_structured_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.2")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["ambiguities"] = {"AMB-1": "bad"}
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertIn("ambiguities must be a list", result.stdout)

    def test_schema_1_2_rejects_future_or_out_of_window_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="awaiting-approval", schema_version="1.2", requirement_approved=False)
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Future resolution", "--source", "manual mutation",
                "--interpretation", "A", "--interpretation", "B",
                "--materiality", "material", "--owner", "user", "--affects", "AC-1",
                "--recommendation", "A",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            document_ambiguity(packet, "AMB-1")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["ambiguities"][0]["status"] = "user-confirmed"
            metadata["ambiguities"][0]["resolution"] = {
                "by": "user",
                "at": "2099-01-01T00:00:00+00:00",
                "text": "A",
                "evidence": ["manually injected future record"],
            }
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            readiness = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "requirements",
                "--id", "REQ-READY", "--by", "user", "--note", "approve",
            )
            self.assertEqual(readiness.returncode, 2)
            self.assertIn("cannot be in the future", readiness.stdout)
            self.assertIn("awaiting-approval window", readiness.stdout)

        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.2")
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["approvals"]["design"]["at"] = "2099-01-01T00:00:00+00:00"
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            future_design = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(future_design.returncode, 2)
            self.assertIn("design approval must follow awaiting approval", future_design.stdout)

    def test_schema_1_2_requires_ambiguity_in_requirement_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="awaiting-approval", schema_version="1.2", requirement_approved=False)
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            metadata["requirements_digest"] = None
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            recorded = run(
                PYTHON, str(FLOW), "record-ambiguity", str(packet),
                "--summary", "Hidden ledger", "--source", "audit",
                "--interpretation", "A", "--interpretation", "B",
                "--materiality", "material", "--owner", "user", "--affects", "AC-1",
                "--recommendation", "A",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            replacements = {
                "context.md": (
                    "No material assumption remains after repository inspection.",
                    "No material assumption remains after repository inspection. AMB-1 is mentioned outside the ledger.",
                ),
                "execution.md": ("No verified finding required repair.", "AMB-1 was resolved."),
                "evidence.md": (
                    "no ambiguity required a question or reopening.",
                    "AMB-1 was resolved before approval.",
                ),
            }
            for filename, (old, new) in replacements.items():
                path = packet / filename
                path.write_text(path.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
            resolved = run(
                PYTHON, str(FLOW), "resolve-ambiguity", str(packet), "--id", "AMB-1",
                "--status", "user-confirmed", "--by", "user",
                "--resolution", "A", "--evidence", "user decision",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            readiness = run(
                PYTHON, str(FLOW), "record-approval", str(packet), "requirements",
                "--id", "REQ-READY", "--by", "user", "--note", "approve",
            )
            self.assertEqual(readiness.returncode, 2)
            self.assertIn("requirement-ledger IDs", readiness.stdout)

    def test_valid_schema_1_0_micro_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            for folder in ("briefs", "reports", "artifacts"):
                (packet / folder).mkdir(parents=True, exist_ok=True)
            now = "2026-08-08T00:00:00+00:00"
            metadata = {
                "schema_version": "1.0",
                "skill_version": "0.2.0",
                "change_id": "legacy-micro",
                "state": "verifying",
                "documentation_profile": "micro",
                "task_type": "micro",
                "created_at": now,
                "updated_at": now,
                "repository_roots": [str(packet.parent)],
                "base_git_state": "main at abc123, clean",
                "authority": "local edits and tests",
                "compatibility_required": False,
                "risk_modifiers": [],
                "acceptance_ids": ["AC-1"],
                "scope_ids": ["SC-D1", "SC-P1", "SC-L1"],
                "verification_ids": ["VO-1"],
                "dependency_changes": [],
                "approvals": {
                    "design": {"by": "user", "at": now, "note": "approved"},
                    "dependencies": [],
                    "waivers": [],
                    "delivery": [],
                },
                "history": [{"from": None, "to": "discovering", "at": now, "note": "created"}],
            }
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            (packet / "trace.md").write_text(
                section_document(
                    "Micro change trace: legacy-micro",
                    {
                        "Authority and repository facts": "The root, user authority, instruction, current branch, and focused test are recorded.",
                        "Requirement and design": "AC-1 changes the confirmed output through the smallest existing branch.",
                        "Scope and protected behavior": "SC-D1 is the direct edit; SC-P1 preserves neighboring behavior; SC-L1 permits local tests only.",
                        "Progress and decisions": "E1 records the bounded edit; D1 records that no dependency or expansion is needed.",
                        "Verification": "VO-1 ran the focused regression with exit 0 and a passing oracle.",
                        "Blue and red audit": "Blue and red checks found no verified issue in the bounded diff.",
                        "Delivery and residual risk": "Local verification is complete; no delivery action occurred and no gate remains.",
                    },
                ),
                encoding="utf-8",
            )
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            (packet / "briefs").rmdir()
            missing_legacy_directory = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(missing_legacy_directory.returncode, 2)
            self.assertIn("missing required directory: briefs/", missing_legacy_directory.stdout)

    def test_schema_1_2_micro_digest_ignores_progress_but_binds_requirement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            for folder in ("briefs", "reports", "artifacts"):
                (packet / folder).mkdir(parents=True, exist_ok=True)
            now = "2026-08-08T00:00:00+00:00"
            requirement_body = (
                "- INS-1: Apply the repository test rule.\n"
                "- AC-1: The selected input returns the confirmed output.\n"
                "- Decision: Extend the existing bounded branch.\n"
                "- Requirement baseline: revision 1 is content-bound.\n"
                "- Ambiguity ledger: no material ambiguity remains."
            )
            trace = section_document(
                "Micro change trace: semantic-micro",
                {
                    "Authority and repository facts": "Local edits and tests are authorized; INS-1 is the applicable repository rule.",
                    "Requirement and design": requirement_body,
                    "Scope and protected behavior": "SC-D1 is the bounded edit; SC-P1 preserves neighbors; SC-L1 permits local tests only.",
                    "Progress and decisions": "E1 records implementation and D1 records the bounded choice.",
                    "Verification": "VO-1 runs the focused regression and records PASSED evidence.",
                    "Blue and red audit": "Blue and red checks found no defect, evidence gap, or requirement ambiguity.",
                    "Delivery and residual risk": "SC-D1 is local; SC-L1 excludes commit and push; no residual local gate remains.",
                },
            )
            (packet / "trace.md").write_text(trace, encoding="utf-8")
            digest = f"sha256:{hashlib.sha256(requirement_body.encode('utf-8')).hexdigest()}"
            metadata = {
                "schema_version": "1.2",
                "skill_version": "0.3.0",
                "change_id": "semantic-micro",
                "state": "implementing",
                "documentation_profile": "micro",
                "task_type": "micro",
                "created_at": now,
                "updated_at": now,
                "repository_roots": [str(packet.parent)],
                "base_git_state": "main at abc123, clean",
                "authority": "local edits and tests",
                "collaboration_profile": "checkpointed",
                "ui_impact": "none",
                "compatibility_required": False,
                "risk_modifiers": [],
                "acceptance_ids": ["AC-1"],
                "scope_ids": ["SC-D1", "SC-P1", "SC-L1"],
                "verification_ids": ["VO-1"],
                "requirement_revision": 1,
                "requirements_digest": digest,
                "ambiguity_ids": [],
                "ambiguities": [],
                "dependency_changes": [],
                "approvals": {
                    "requirements": [{
                        "id": "REQ-READY", "by": "user", "at": now, "note": "approved",
                        "requirement_revision": 1, "requirements_digest": digest,
                    }],
                    "ux": [],
                    "design": {
                        "by": "user", "at": now, "note": "approved",
                        "requirement_revision": 1, "requirements_digest": digest,
                    },
                    "dependencies": [], "waivers": [], "delivery": [],
                },
                "history": [
                    {"from": None, "to": "discovering", "at": now, "note": "created"},
                    {"from": "discovering", "to": "awaiting-approval", "at": now, "note": "ready"},
                    {"from": "awaiting-approval", "to": "approved", "at": now, "note": "approved"},
                ],
            }
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            valid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

            trace_path = packet / "trace.md"
            trace_path.write_text(trace_path.read_text(encoding="utf-8").replace("E1 records", "E1 and E2 record"), encoding="utf-8")
            progress_only = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(progress_only.returncode, 0, progress_only.stderr or progress_only.stdout)

            trace_path.write_text(trace_path.read_text(encoding="utf-8").replace("confirmed output", "different output"), encoding="utf-8")
            requirement_changed = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(requirement_changed.returncode, 2)
            self.assertIn("requirements changed", requirement_changed.stdout)

    def test_schema_1_1_requires_new_headings(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1")
            context = packet / "context.md"
            context.write_text(
                context.read_text(encoding="utf-8").replace("## Instruction and convention ledger", "## Removed ledger"),
                encoding="utf-8",
            )
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("Instruction and convention ledger", result.stdout)

    def test_schema_1_1_requires_matching_instruction_trace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1")
            context = packet / "context.md"
            context.write_text(context.read_text(encoding="utf-8").replace("INS-1", "RULE-1"), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("instruction IDs must match", result.stdout)

            evidence = packet / "evidence.md"
            evidence.write_text(evidence.read_text(encoding="utf-8").replace("INS-1", "RULE-1"), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("requires at least one INS-n", result.stdout)

        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1")
            for filename in ("design.md", "execution.md", "test-matrix.md", "blue-audit.md", "red-audit.md"):
                path = packet / filename
                path.write_text(path.read_text(encoding="utf-8").replace("INS-1", "RULE-1"), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("instruction IDs must match between context.md and design.md", result.stdout)

    def test_checkpointed_schema_1_1_requires_requirement_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1", requirement_approved=False)
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("Requirement Ready", result.stdout)

    def test_material_ui_schema_1_1_requires_ux_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1", ui_impact="material", ux_approved=False)
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("UX Ready", result.stdout)

    def test_execute_and_preserve_modes_do_not_add_unrelated_approval_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            execute_packet = Path(temp) / "execute"
            write_valid_packet(
                execute_packet,
                schema_version="1.1",
                collaboration_profile="execute",
                requirement_approved=False,
                ux_approved=False,
            )
            execute_result = run(PYTHON, str(FLOW), "validate-packet", str(execute_packet))
            self.assertEqual(execute_result.returncode, 0, execute_result.stderr or execute_result.stdout)

            preserve_packet = Path(temp) / "preserve"
            write_valid_packet(
                preserve_packet,
                schema_version="1.1",
                ui_impact="preserve",
                ux_approved=False,
            )
            preserve_result = run(PYTHON, str(FLOW), "validate-packet", str(preserve_packet))
            self.assertEqual(preserve_result.returncode, 0, preserve_result.stderr or preserve_result.stdout)

    def test_rejects_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet)
            context = packet / "context.md"
            context.write_text(context.read_text(encoding="utf-8").replace("The existing module", "<module>"), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("unresolved placeholder", result.stdout)

    def test_rejects_unapproved_dependency(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["dependencies"] = []
            (packet / "packet.json").write_text(json.dumps(metadata), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("unapproved dependency", result.stdout)

    def test_schema_2_dependency_approval_requires_and_records_exact_scope(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialized = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "dependency-scope",
                "--task-type",
                "dependency-change",
                "--objective",
                "Bind one exact dependency",
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr or initialized.stdout)
            packet = root / ".codex" / "dev-flow" / "dependency-scope"
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["dependency_changes"] = ["DEP-1"]
            metadata["approvals"]["dependencies"] = [
                {"id": "DEP-1", "by": "owner", "at": "2026-08-10T00:00:00Z", "note": "generic"}
            ]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            generic = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(generic.returncode, 2)
            self.assertIn("requires a dependency object", generic.stdout)

            metadata["dependency_changes"] = []
            metadata["approvals"]["dependencies"] = []
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            recorded = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "dependencies",
                "--id",
                "DEP-1",
                "--by",
                "owner",
                "--note",
                "exact crate",
                "--dependency-ecosystem",
                "cargo",
                "--dependency-name",
                "serde",
                "--dependency-version",
                "1.0.219",
                "--dependency-ref",
                "1.0.219",
                "--dependency-command",
                "cargo add serde@1.0.219",
                "--dependency-file",
                "Cargo.toml",
                "--dependency-file",
                "Cargo.lock",
                "--dependency-operation",
                "add",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            record = json.loads(recorded.stdout)["record"]
            self.assertEqual(record["dependency"]["name"], "serde")
            self.assertEqual(record["dependency"]["files"], ["Cargo.toml", "Cargo.lock"])

            invalid_path = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "dependencies",
                "--id",
                "DEP-2",
                "--by",
                "owner",
                "--note",
                "bad path",
                "--dependency-ecosystem",
                "cargo",
                "--dependency-name",
                "other",
                "--dependency-version",
                "1.0.0",
                "--dependency-ref",
                "1.0.0",
                "--dependency-command",
                "cargo add other@1.0.0",
                "--dependency-file",
                "./Cargo.toml",
                "--dependency-operation",
                "add",
            )
            self.assertEqual(invalid_path.returncode, 2)
            self.assertIn("normalized relative paths", invalid_path.stdout)

    def test_rejects_accepted_not_run_cell(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted", matrix_status="NOT RUN")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("required cell is NOT RUN", result.stdout)

    def test_accepted_matrix_rejects_qualified_required_words_and_parses_suffixed_cells(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted")
            matrix = packet / "test-matrix.md"
            matrix.write_text(
                matrix.read_text(encoding="utf-8")
                + "\n| TM-5 | VO-5 | isolated pilot | descriptive | yes for pilot | 1 | FAILED | preserved |\n"
                + "| TM-5F | VO-5 | full run | release | release required | 0 | NOT RUN | pending |\n",
                encoding="utf-8",
            )
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid Required value 'yes for pilot' for TM-5", result.stdout)
            self.assertIn("invalid Required value 'release required' for TM-5F", result.stdout)

            text = matrix.read_text(encoding="utf-8")
            matrix.write_text(
                text.replace("yes for pilot", "yes").replace("release required", "yes"),
                encoding="utf-8",
            )
            canonical = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(canonical.returncode, 2)
            self.assertIn("TM-5: required cell is FAILED", canonical.stdout)
            self.assertIn("TM-5F: required cell is NOT RUN", canonical.stdout)

    def test_accepted_matrix_rejects_unknown_or_duplicate_cell_ids(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted")
            matrix = packet / "test-matrix.md"
            matrix.write_text(
                matrix.read_text(encoding="utf-8")
                + "\n| TM-X | VO-1 | local | check | yes | 1 | PASSED | bad id |\n"
                + "| TM-1 | VO-1 | local | duplicate | yes | 1 | PASSED | duplicate |\n",
                encoding="utf-8",
            )
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("invalid cell id 'TM-X'", result.stdout)
            self.assertIn("duplicate cell id TM-1", result.stdout)

    def test_rejects_passed_cell_without_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted", matrix_attempts=0)
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("PASSED requires at least one attempt", result.stdout)

    def test_acceptance_transition_runs_acceptance_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="verifying", matrix_status="NOT RUN", matrix_attempts=0)
            result = run(PYTHON, str(FLOW), "transition", str(packet), "accepted", "--note", "attempt acceptance")
            self.assertEqual(result.returncode, 2)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["state"], "verifying")

    def test_init_direct_mode_creates_no_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run(PYTHON, str(FLOW), "init-packet", "--root", str(root), "--change-id", "micro-fix", "--task-type", "micro", "--objective", "Fix the bounded typo")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            self.assertEqual((payload["status"], payload["work_mode"]), ("not-required", "direct"))
            self.assertFalse((root / ".codex").exists())

    def test_init_traced_mode_has_three_core_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "routine-fix",
                "--task-type",
                "routine",
                "--objective",
                "Fix the bounded behavior",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)
            packet = Path(payload["packet"])
            self.assertEqual(payload["artifacts"], ["packet.json", "events.jsonl", "trace.md"])
            self.assertEqual({item.name for item in packet.iterdir() if item.is_file()}, {"packet.json", "events.jsonl", "trace.md"})
            self.assertTrue((packet / "artifacts").is_dir())
            self.assertFalse((packet / "briefs").exists())

            packet_before = (packet / "packet.json").read_bytes()
            events_before = (packet / "events.jsonl").read_bytes()
            reused = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "routine-fix",
                "--task-type",
                "routine",
                "--objective",
                "Resume the bounded behavior",
                "--reuse",
            )
            self.assertEqual(reused.returncode, 0, reused.stderr or reused.stdout)
            self.assertEqual(json.loads(reused.stdout)["status"], "reused")
            self.assertEqual((packet / "packet.json").read_bytes(), packet_before)
            self.assertEqual((packet / "events.jsonl").read_bytes(), events_before)

            unsafe_reuse = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "routine-fix",
                "--task-type",
                "routine",
                "--objective",
                "Escalated security work",
                "--risk",
                "security",
                "--reuse",
            )
            self.assertEqual(unsafe_reuse.returncode, 2)
            self.assertIn("must be explicitly migrated", unsafe_reuse.stdout)

    def test_schema_2_trace_validates_and_event_drift_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "valid-trace",
                "--task-type",
                "routine",
                "--objective",
                "Verify schema two trace projection",
            )
            self.assertEqual(created.returncode, 0, created.stderr or created.stdout)
            packet = Path(json.loads(created.stdout)["packet"])
            (packet / "trace.md").write_text(
                """# Trace: valid-trace

## Authority and repository facts
INS-1 applies. Local edits and tests are authorized. Repository root and base state were inspected.

## Requirement and design
AC-1 requires a valid trace. The smallest compatible implementation is selected. No material ambiguity exists.

## Scope and protected behavior
SC-D1 covers the trace. SC-P1 preserves old schemas. SC-L1 excludes delivery.

## Progress and decisions
Implementation and decisions are recorded in order.

## Verification
VO-1 runs packet validation from the repository root; PASSED.

## Blue and red audit
Blue and red checks found no verified issue.

## Delivery and residual risk
Local only. No residual implementation risk remains.
""",
                encoding="utf-8",
            )
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["acceptance_ids"] = ["AC-1"]
            metadata["scope_ids"] = ["SC-D1", "SC-P1", "SC-L1"]
            metadata["verification_ids"] = ["VO-1"]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            valid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

            transitions = (
                ("awaiting-approval", []),
                ("approved", ["--approved-by", "user"]),
                ("implementing", []),
                ("verifying", []),
                ("accepted", []),
            )
            for state, extra in transitions:
                transitioned = run(
                    PYTHON,
                    str(FLOW),
                    "transition",
                    str(packet),
                    state,
                    "--note",
                    f"enter {state}",
                    *extra,
                )
                self.assertEqual(transitioned.returncode, 0, transitioned.stderr or transitioned.stdout)
            accepted = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(accepted["state"], "accepted")

            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            events[-1]["state"] = "blocked"
            (packet / "events.jsonl").write_text(
                "".join(json.dumps(event) + "\n" for event in events), encoding="utf-8"
            )
            invalid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("final state does not match", invalid.stdout)

    def test_init_selects_risk_scaled_collaboration_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            routine = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "routine-change",
                "--task-type",
                "routine",
                "--objective",
                "Extend the bounded behavior",
            )
            self.assertEqual(routine.returncode, 0, routine.stderr or routine.stdout)
            routine_meta = json.loads(
                (root / ".codex" / "dev-flow" / "routine-change" / "packet.json").read_text(encoding="utf-8")
            )
            self.assertEqual(routine_meta["schema_version"], "2.0")
            self.assertEqual(routine_meta["work_mode"], "traced")
            self.assertEqual(routine_meta["documentation_profile"], "trace")
            self.assertEqual(routine_meta["collaboration_profile"], "execute")
            self.assertEqual(routine_meta["ui_impact"], "none")

            material = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "material-ui",
                "--task-type",
                "large-feature",
                "--objective",
                "Redesign the primary workflow",
                "--ui-impact",
                "material",
            )
            self.assertEqual(material.returncode, 0, material.stderr or material.stdout)
            material_meta = json.loads(
                (root / ".codex" / "dev-flow" / "material-ui" / "packet.json").read_text(encoding="utf-8")
            )
            self.assertEqual(material_meta["collaboration_profile"], "co-design")
            self.assertEqual(material_meta["work_mode"], "governed")

            micro_material = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "micro-material-ui",
                "--task-type",
                "micro",
                "--objective",
                "Make a small but product-direction-changing UI edit",
                "--ui-impact",
                "material",
            )
            self.assertEqual(micro_material.returncode, 0, micro_material.stderr or micro_material.stdout)
            micro_material_meta = json.loads(
                (root / ".codex" / "dev-flow" / "micro-material-ui" / "packet.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(micro_material_meta["collaboration_profile"], "co-design")
            self.assertEqual(micro_material_meta["work_mode"], "governed")

    def test_explicit_work_mode_cannot_downgrade_risk_or_material_ui(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            security = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "unsafe-security-mode",
                "--task-type",
                "security",
                "--objective",
                "Change authentication",
                "--work-mode",
                "direct",
            )
            self.assertEqual(security.returncode, 2)
            self.assertIn("cannot downgrade required governed", security.stdout)
            material = run(
                PYTHON,
                str(FLOW),
                "route-task",
                "--task-type",
                "large-feature",
                "--ui-impact",
                "material",
                "--work-mode",
                "traced",
            )
            self.assertEqual(material.returncode, 2)
            self.assertIn("material UI impact requires governed", material.stdout)

            privacy = run(
                PYTHON,
                str(FLOW),
                "route-task",
                "--task-type",
                "routine",
                "--risk",
                "privacy",
            )
            self.assertEqual(privacy.returncode, 0, privacy.stderr or privacy.stdout)
            privacy_payload = json.loads(privacy.stdout)
            self.assertEqual(privacy_payload["work_mode"], "governed")
            self.assertIn("change-review", [item["skill"] for item in privacy_payload["routes"]])

    def test_unknown_risk_token_is_rejected_instead_of_silently_underclassified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                temp,
                "--change-id",
                "invalid-risk",
                "--task-type",
                "routine",
                "--objective",
                "Reject an unknown risk",
                "--risk",
                "high",
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("unknown risk", result.stdout)
            self.assertFalse((Path(temp) / ".codex").exists())

    def test_transition_records_requirement_and_ux_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="awaiting-approval",
                schema_version="1.1",
                ui_impact="material",
                requirement_approved=False,
                ux_approved=False,
            )
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            blocked = run(
                PYTHON,
                str(FLOW),
                "transition",
                str(packet),
                "approved",
                "--note",
                "approve",
                "--approved-by",
                "user",
            )
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("Requirement Ready", blocked.stdout)

            requirement = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "requirements approved",
            )
            self.assertEqual(requirement.returncode, 0, requirement.stderr or requirement.stdout)
            still_blocked = run(
                PYTHON,
                str(FLOW),
                "transition",
                str(packet),
                "approved",
                "--note",
                "approve",
                "--approved-by",
                "user",
            )
            self.assertEqual(still_blocked.returncode, 2)
            self.assertIn("UX Ready", still_blocked.stdout)

            ux = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "ux",
                "--id",
                "UX-READY",
                "--by",
                "user",
                "--note",
                "UX approved",
            )
            self.assertEqual(ux.returncode, 0, ux.stderr or ux.stdout)
            approved = run(
                PYTHON,
                str(FLOW),
                "transition",
                str(packet),
                "approved",
                "--note",
                "approve",
                "--approved-by",
                "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)

    def test_readiness_approvals_reject_malformed_and_late_records(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="awaiting-approval",
                schema_version="1.1",
                ui_impact="material",
                requirement_approved=False,
                ux_approved=False,
            )
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["design"] = None
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            wrong_id = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "ux",
                "--id",
                "NOT-READY",
                "--by",
                "user",
                "--note",
                "not approved",
            )
            self.assertEqual(wrong_id.returncode, 2)
            self.assertIn("UX-READY", wrong_id.stdout)

            blank = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "ux",
                "--id",
                "UX-READY",
                "--by",
                "",
                "--note",
                "",
            )
            self.assertEqual(blank.returncode, 2)
            self.assertIn("must be non-empty", blank.stdout)

            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["requirements"] = [
                {"id": "REQ-READY", "by": "user", "at": "2026-08-08T00:00:00+00:00", "note": "approved"}
            ]
            metadata["approvals"]["ux"] = [{}]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            malformed = run(
                PYTHON,
                str(FLOW),
                "transition",
                str(packet),
                "approved",
                "--note",
                "approve",
                "--approved-by",
                "user",
            )
            self.assertEqual(malformed.returncode, 2)
            self.assertIn("UX Ready", malformed.stdout)

            metadata["approvals"]["requirements"] = [
                {"id": "REQ-READY", "by": "user", "at": "2099-01-01T00:00:00+00:00", "note": "future"}
            ]
            metadata["approvals"]["ux"] = [
                {"id": "UX-READY", "by": "user", "at": "2099-01-01T00:00:00+00:00", "note": "future"}
            ]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            future = run(
                PYTHON,
                str(FLOW),
                "transition",
                str(packet),
                "approved",
                "--note",
                "approve",
                "--approved-by",
                "user",
            )
            self.assertEqual(future.returncode, 2)
            self.assertIn("Requirement Ready", future.stdout)

        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(
                packet,
                state="implementing",
                schema_version="1.1",
                ui_impact="material",
                ux_approved=False,
            )
            late_cli = run(
                PYTHON,
                str(FLOW),
                "record-approval",
                str(packet),
                "ux",
                "--id",
                "UX-READY",
                "--by",
                "user",
                "--note",
                "late approval",
            )
            self.assertEqual(late_cli.returncode, 2)
            self.assertIn("awaiting approval", late_cli.stdout)

            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"]["ux"] = [
                {"id": "UX-READY", "by": "user", "at": "2026-08-09T00:00:00+00:00", "note": "late"}
            ]
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            late_manual = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(late_manual.returncode, 2)
            self.assertIn("cannot be recorded after", late_manual.stdout)

    def test_malformed_approvals_container_is_structured_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.1")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["approvals"] = []
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertIn("approvals` must be an object", result.stdout)

    def test_malformed_dependency_container_is_structured_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, schema_version="1.2")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["dependency_changes"] = {"DEP-1": "bad"}
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual(result.stderr, "")
            self.assertIn("dependency_changes must be a list", result.stdout)


class RuntimeInstallerTests(unittest.TestCase):
    def test_non_directory_destination_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            destination.write_text("not a directory\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("not a directory", result.stdout)

    def test_conflict_blocks_entire_install_without_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            destination.mkdir()
            first = sorted(AGENT_CONFIGS.glob("*.toml"))[0]
            target = destination / first.name
            target.write_text("user-owned config\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual(target.read_text(encoding="utf-8"), "user-owned config\n")
            self.assertEqual([path.name for path in destination.glob("*.toml")], [first.name])
            self.assertEqual(json.loads(result.stdout)["status"], "blocked")

    def test_identical_configs_are_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            first = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            second = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            payload = json.loads(second.stdout)
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            self.assertEqual(payload["status"], "unchanged")
            self.assertEqual(len(payload["unchanged"]), len(list(AGENT_CONFIGS.glob("*.toml"))))
            self.assertFalse(payload["restart_required"])

    def test_force_backs_up_before_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            destination.mkdir()
            source = sorted(AGENT_CONFIGS.glob("*.toml"))[0]
            target = destination / source.name
            original = b"user-owned config\n"
            target.write_bytes(original)
            result = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination), "--force")
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertEqual(len(payload["backups"]), 1)
            backup = Path(payload["backups"][0]["backup"])
            self.assertTrue(backup.is_file())
            self.assertEqual(backup.read_bytes(), original)

    def test_uninstall_removes_only_unmodified_plugin_configs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            install = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            uninstall = run(PYTHON, str(FLOW), "uninstall-runtime", "--destination", str(destination))
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr or uninstall.stdout)
            self.assertEqual(json.loads(uninstall.stdout)["status"], "uninstalled")
            self.assertFalse(list(destination.glob("*.toml")))

    def test_modified_config_blocks_entire_uninstall(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            install = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            target = destination / sorted(AGENT_CONFIGS.glob("*.toml"))[0].name
            target.write_text("locally modified\n", encoding="utf-8")
            uninstall = run(PYTHON, str(FLOW), "uninstall-runtime", "--destination", str(destination))
            self.assertEqual(uninstall.returncode, 2, uninstall.stderr or uninstall.stdout)
            self.assertEqual(len(list(destination.glob("*.toml"))), len(list(AGENT_CONFIGS.glob("*.toml"))))

    def test_symlink_target_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "agents"
            destination.mkdir()
            source = sorted(AGENT_CONFIGS.glob("*.toml"))[0]
            outside = Path(temp) / "outside.toml"
            outside.write_text("outside config\n", encoding="utf-8")
            target = destination / source.name
            try:
                target.symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            result = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination), "--force")
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual(outside.read_text(encoding="utf-8"), "outside config\n")


class HookTests(unittest.TestCase):
    def test_blocking_states_fail_closed_for_every_bash_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "state": "implementing",
                        "ambiguities": [{"id": "AMB-1", "status": "open", "materiality": "material"}],
                        "approvals": {"dependencies": []},
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            commands = (
                "python3 -c 'from pathlib import Path; Path(\"x\").write_text(\"x\")'",
                "git checkout -- src/app.py",
                "git reset -- src/app.py",
                "git clean -f src/app.py",
                "powershell -Command Set-Content src/app.py changed",
                "./ordinary-script.sh",
                "git status --short",
            )
            for command in commands:
                with self.subTest(command=command):
                    event = {
                        "cwd": str(root),
                        "hook_event_name": "PreToolUse",
                        "tool_name": "Bash",
                        "tool_input": {"command": command},
                    }
                    result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
                    self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                    payload = json.loads(result.stdout)["hookSpecificOutput"]
                    self.assertEqual(payload["permissionDecision"], "deny")
                    self.assertIn("AMB-1", payload["permissionDecisionReason"])

    def test_dependency_approval_matches_exact_command_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            approval = {
                "id": "DEP-1",
                "by": "owner",
                "at": "2026-08-10T00:00:00Z",
                "note": "exact crate",
                "dependency": {
                    "ecosystem": "cargo",
                    "name": "approved-crate",
                    "version": "1.2.3",
                    "ref": "1.2.3",
                    "command": "cargo add approved-crate@1.2.3",
                    "files": ["Cargo.toml", "Cargo.lock"],
                    "operations": ["add"],
                    "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)

            def invoke(command: str) -> dict[str, object]:
                event = {
                    "cwd": str(root),
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_input": {"command": command},
                }
                result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                return json.loads(result.stdout)["hookSpecificOutput"]

            allowed = invoke("cargo add approved-crate@1.2.3")
            self.assertNotIn("permissionDecision", allowed)
            self.assertIn("exact diff", allowed["additionalContext"])
            for command in (
                "cargo add different-crate@1.2.3",
                "cargo add approved-crate",
                "cargo add approved-crate@1.2.3 --features=extra",
                "cargo.exe add approved-crate@1.2.3",
                "cargo +stable add approved-crate@1.2.3",
                "cargo --manifest-path=other/Cargo.toml add approved-crate@1.2.3",
                "cargo add approved-crate@1.2.3 --manifest-path=other/Cargo.toml",
                "cargo add approved-crate@1.2.3 --package=member",
                "cargo add approved-crate@1.2.3 -p member",
                "cargo update -p approved-crate --precise 1.2.4",
                "cargo update -p approved-crate --precise 1.2.4 --workspace",
                "cargo remove approved-crate",
                "npm install other@1.2.3",
                "npm --prefix other install approved-crate@1.2.3",
                "npm --workspace=app install approved-crate@1.2.3",
                "npm.cmd install approved-crate@1.2.3",
                "npm install approved-crate@1.2.3 -w=app",
                "npm install approved-crate@1.2.3 --workspace app",
                "pnpm --filter app add approved-crate@1.2.3",
                "pnpm -C other add approved-crate@1.2.3",
                "yarn workspace app add approved-crate@1.2.3",
                "sh -c 'npm install approved-crate@1.2.3'",
                "bash -lc 'cargo add approved-crate@1.2.3'",
                "npm uninstall approved-crate",
            ):
                with self.subTest(command=command):
                    self.assertEqual(invoke(command)["permissionDecision"], "deny")

            for command, operation, ref, file in (
                ("cargo update -p approved-crate --precise 1.2.4", "update", "1.2.4", "Cargo.lock"),
                ("cargo remove approved-crate", "remove", "1.2.3", "Cargo.toml"),
            ):
                with self.subTest(approved_command=command):
                    scoped = approval["dependency"]
                    scoped.update({
                        "version": ref,
                        "ref": ref,
                        "command": command,
                        "files": [file],
                        "operations": [operation],
                    })
                    (packet / "packet.json").write_text(
                        json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                        encoding="utf-8",
                    )
                    self.assertNotIn("permissionDecision", invoke(command))

            scoped = approval["dependency"]
            scoped.update({
                "version": "1.2.3",
                "ref": "1.2.3",
                "command": "cargo add approved-crate@1.2.3 --manifest-path=other/Cargo.toml",
                "files": ["Cargo.toml"],
                "operations": ["add"],
            })
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            self.assertEqual(
                invoke("cargo add approved-crate@1.2.3 --manifest-path=other/Cargo.toml")["permissionDecision"],
                "deny",
            )

    def test_dependency_approval_does_not_unlock_unbindable_manifest_edit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            approval = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "cargo",
                    "name": "approved-crate",
                    "version": "1.2.3",
                    "ref": "1.2.3",
                    "command": "cargo add approved-crate@1.2.3",
                    "files": ["Cargo.toml"],
                    "operations": ["add"],
                    "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(root / "Cargo.toml"), "content": "different = '9'"},
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_github_action_request_requires_exact_path_name_and_ref(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            ref = "a" * 40
            approval = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "github-actions",
                    "name": "owner/action",
                    "version": "1.0.0",
                    "ref": ref,
                    "command": None,
                    "files": [".github/workflows/release.yml"],
                    "operations": ["add"],
                    "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)

            def invoke(action_ref: str) -> dict[str, object]:
                event = {
                    "cwd": str(root),
                    "hook_event_name": "PreToolUse",
                    "tool_name": "apply_patch",
                    "tool_input": {
                        "patch": "*** Begin Patch\n*** Add File: .github/workflows/release.yml\n+steps:\n+  - uses: owner/action@"
                        + action_ref
                        + "\n*** End Patch"
                    },
                }
                result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                return json.loads(result.stdout)["hookSpecificOutput"]

            self.assertNotIn("permissionDecision", invoke(ref))
            self.assertEqual(invoke("b" * 40)["permissionDecision"], "deny")

            approval["dependency"]["name"] = "owner/action/subpath"
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Add File: .github/workflows/release.yml\n+steps:\n+  - uses: owner/action/subpath@"
                    + ref
                    + "\n*** End Patch"
                },
            }
            subpath = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            self.assertNotIn("permissionDecision", json.loads(subpath.stdout)["hookSpecificOutput"])

            workflow = root / ".github" / "workflows" / "release.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(f"steps:\n  - uses: owner/action/subpath@{ref}\n", encoding="utf-8")
            removal_event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: .github/workflows/release.yml\n@@\n-  - uses: owner/action/subpath@"
                    + ref
                    + "\n*** End Patch"
                },
            }
            denied_removal = run(PYTHON, str(HOOK), stdin=json.dumps(removal_event), env=env)
            self.assertEqual(json.loads(denied_removal.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            approval["dependency"]["operations"] = ["remove"]
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": [approval]}}),
                encoding="utf-8",
            )
            approved_removal = run(PYTHON, str(HOOK), stdin=json.dumps(removal_event), env=env)
            self.assertNotIn("permissionDecision", json.loads(approved_removal.stdout)["hookSpecificOutput"])

            approval["dependency"]["operations"] = ["add"]
            yaml_entries = (
                '"uses": owner/action/subpath@' + ref,
                "'uses': owner/action/subpath@" + ref,
                "uses : owner/action/subpath@" + ref,
                "{ name: test, uses: owner/action/subpath@" + ref + " }",
                '"u\\u0073es": owner/action/subpath@' + ref,
                '"u\\x73es": "owner\\/action/subpath@' + ref + '"',
                '"\\U00000075ses": docker://example.invalid/tool@' + ref,
            )
            for entry in yaml_entries:
                with self.subTest(yaml_entry=entry):
                    (packet / "packet.json").write_text(
                        json.dumps({"state": "implementing", "approvals": {"dependencies": []}}),
                        encoding="utf-8",
                    )
                    variant_event = {
                        "cwd": str(root),
                        "hook_event_name": "PreToolUse",
                        "tool_name": "apply_patch",
                        "tool_input": {
                            "patch": "*** Begin Patch\n*** Add File: .github/workflows/other.yml\n+steps:\n+  - "
                            + entry
                            + "\n*** End Patch"
                        },
                    }
                    variant = run(PYTHON, str(HOOK), stdin=json.dumps(variant_event), env=env)
                    self.assertEqual(json.loads(variant.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_typed_write_and_edit_events_are_governed_mutations(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(
                json.dumps(
                    {
                        "schema_version": "2.0",
                        "state": "implementing",
                        "ambiguities": [{"id": "AMB-1", "status": "open", "materiality": "material"}],
                        "approvals": {"dependencies": []},
                    }
                ),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            for tool_name in ("Write", "Edit"):
                with self.subTest(tool_name=tool_name):
                    event = {
                        "cwd": str(root),
                        "hook_event_name": "PreToolUse",
                        "tool_name": tool_name,
                        "tool_input": {"file_path": str(root / "src" / "app.py"), "content": "updated"},
                    }
                    result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
                    self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                    self.assertEqual(json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

            packet_event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(packet / "requirements.md"), "content": "packet repair"},
            }
            allowed = run(PYTHON, str(HOOK), stdin=json.dumps(packet_event), env=env)
            self.assertEqual(allowed.stdout, "")

    def test_blocks_unapproved_manifest_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": []}}), encoding="utf-8")
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "cargo add serde"}
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            self.assertEqual(result.returncode, 0)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_dependency_gate_uses_mutation_target_not_document_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(
                json.dumps({"state": "implementing", "approvals": {"dependencies": []}}),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            documentation = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(root / "README.md"), "content": "Document Cargo.toml without changing it."},
            }
            allowed = run(PYTHON, str(HOOK), stdin=json.dumps(documentation), env=env)
            self.assertEqual(allowed.stdout, "")
            manifest = {
                **documentation,
                "tool_input": {"file_path": str(root / "Cargo.toml"), "content": "[dependencies]"},
            }
            blocked = run(PYTHON, str(HOOK), stdin=json.dumps(manifest), env=env)
            self.assertEqual(json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_open_material_ambiguity_blocks_product_mutation_but_allows_packet_update(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(
                json.dumps({
                    "schema_version": "1.2",
                    "state": "implementing",
                    "ambiguities": [{"id": "AMB-1", "status": "open", "materiality": "material"}],
                    "approvals": {"dependencies": []},
                }),
                encoding="utf-8",
            )
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            product_event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"patch": "*** Begin Patch\n*** Update File: src/app.py\n@@\n-old\n+new\n*** End Patch"},
            }
            blocked = run(PYTHON, str(HOOK), stdin=json.dumps(product_event), env=env)
            self.assertEqual(blocked.returncode, 0, blocked.stderr or blocked.stdout)
            self.assertEqual(json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            self.assertIn("AMB-1", blocked.stdout)

            packet_event = {
                **product_event,
                "tool_input": {
                    "patch": f"*** Begin Patch\n*** Update File: {packet / 'requirements.md'}\n@@\n-old\n+new\n*** End Patch"
                },
            }
            allowed = run(PYTHON, str(HOOK), stdin=json.dumps(packet_event), env=env)
            self.assertEqual(allowed.returncode, 0, allowed.stderr or allowed.stdout)
            self.assertEqual(allowed.stdout, "")

    def test_blocked_readiness_blocks_product_mutation_but_allows_packet_repair(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "approvals": {"dependencies": []}}), encoding="utf-8")
            (packet / "context-readiness.json").write_text(json.dumps({"outcome": "blocked"}), encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            event = {"cwd": str(root), "hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"patch": "*** Begin Patch\n*** Update File: src/app.py\n@@\n-old\n+new\n*** End Patch"}}
            blocked = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            self.assertEqual(json.loads(blocked.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
            repair = {**event, "tool_input": {"patch": f"*** Begin Patch\n*** Update File: {packet / 'context-readiness.json'}\n@@\n-old\n+new\n*** End Patch"}}
            allowed = run(PYTHON, str(HOOK), stdin=json.dumps(repair), env=env)
            self.assertEqual(allowed.stdout, "")

    def test_missing_readiness_is_advisory_for_risk_bearing_work(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "risk_modifiers": ["security"], "approvals": {"dependencies": []}}), encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            event = {"cwd": str(root), "hook_event_name": "PreToolUse", "tool_name": "apply_patch", "tool_input": {"patch": "*** Begin Patch\n*** Update File: src/app.py\n@@\n-old\n+new\n*** End Patch"}}
            result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            payload = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", payload)
            self.assertIn("absence alone is advisory", payload["additionalContext"])

    def test_subagent_missing_report_is_advisory_and_cleans_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            reports = packet / "reports"
            reports.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "approvals": {"dependencies": []}}), encoding="utf-8")
            stale = reports / "old.md"
            stale.write_text("old report\n", encoding="utf-8")
            old_time = time.time() - 10
            os.utime(stale, (old_time, old_time))
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            env["PLUGIN_DATA"] = str(root / "plugin-data")
            common = {"cwd": str(root), "session_id": "session", "agent_id": "agent", "agent_type": "dev-flow-worker"}
            start = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStart"}), env=env)
            self.assertEqual(start.returncode, 0)
            markers = list((root / "plugin-data" / "agent-runs").glob("*.json"))
            self.assertEqual(len(markers), 1)
            marker_text = markers[0].read_text(encoding="utf-8")
            self.assertNotIn(str(packet), marker_text)
            self.assertIn("packet_hash", marker_text)
            stop_event = {**common, "hook_event_name": "SubagentStop", "stop_hook_active": False}
            missing = run(PYTHON, str(HOOK), stdin=json.dumps(stop_event), env=env)
            payload = json.loads(missing.stdout)
            self.assertNotIn("decision", payload)
            self.assertIn("DEV_FLOW_AGENT_REPORT_MISSING", payload["hookSpecificOutput"]["additionalContext"])
            self.assertIn("do not redispatch", payload["hookSpecificOutput"]["additionalContext"])
            self.assertFalse(markers[0].exists())

    def test_subagent_fresh_optional_report_cleans_marker_without_advisory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            reports = packet / "reports"
            reports.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "verifying", "approvals": {"dependencies": []}}), encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            env["PLUGIN_DATA"] = str(root / "plugin-data")
            common = {"cwd": str(root), "session_id": "session", "agent_id": "agent", "agent_type": "dev-flow-worker"}
            start = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStart"}), env=env)
            self.assertEqual(start.returncode, 0)
            markers = list((root / "plugin-data" / "agent-runs").glob("*.json"))
            self.assertEqual(len(markers), 1)
            (reports / "agent.md").write_text("fresh report\n", encoding="utf-8")
            stop_event = {**common, "hook_event_name": "SubagentStop", "stop_hook_active": False}
            present = run(PYTHON, str(HOOK), stdin=json.dumps(stop_event), env=env)
            self.assertEqual(json.loads(present.stdout), {})
            self.assertFalse(markers[0].exists())

    def test_subagent_start_is_fail_open_when_marker_storage_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            packet.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "approvals": {"dependencies": []}}), encoding="utf-8")
            unavailable = root / "plugin-data-file"
            unavailable.write_text("not a directory\n", encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            env["PLUGIN_DATA"] = str(unavailable)
            event = {"cwd": str(root), "session_id": "session", "agent_id": "agent", "hook_event_name": "SubagentStart"}

            result = run(PYTHON, str(HOOK), stdin=json.dumps(event), env=env)
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            payload = json.loads(result.stdout)["hookSpecificOutput"]
            self.assertIn("DEV_FLOW_AGENT_MARKER_UNAVAILABLE", payload["additionalContext"])
            self.assertIn("return a bounded native final result", payload["additionalContext"])

    def test_subagent_stop_is_fail_open_for_non_object_marker_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            (packet / "reports").mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "approvals": {"dependencies": []}}), encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            env["PLUGIN_DATA"] = str(root / "plugin-data")
            common = {"cwd": str(root), "session_id": "session", "agent_id": "agent"}
            start = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStart"}), env=env)
            self.assertEqual(start.returncode, 0)
            marker = next((root / "plugin-data" / "agent-runs").glob("*.json"))
            marker.write_text("[]\n", encoding="utf-8")

            stop = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStop"}), env=env)
            self.assertEqual(stop.returncode, 0, stop.stderr or stop.stdout)
            payload = json.loads(stop.stdout)
            self.assertIn("DEV_FLOW_AGENT_REPORT_MISSING", payload["hookSpecificOutput"]["additionalContext"])
            self.assertFalse(marker.exists())

    def test_terminal_and_blocked_packets_are_inert_for_agent_lifecycle(self) -> None:
        for state in ("accepted", "archived", "blocked"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                flow = root / ".codex" / "dev-flow"
                packet = flow / "sample-change"
                packet.mkdir(parents=True)
                (flow / "current").write_text("sample-change\n", encoding="utf-8")
                (packet / "packet.json").write_text(json.dumps({"state": state, "approvals": {"dependencies": []}}), encoding="utf-8")
                env = os.environ.copy()
                env["PLUGIN_ROOT"] = str(ROOT)
                env["PLUGIN_DATA"] = str(root / "plugin-data")
                common = {"cwd": str(root), "session_id": "session", "agent_id": "agent"}

                start = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStart"}), env=env)
                self.assertEqual(start.returncode, 0)
                self.assertEqual(start.stdout, "")
                self.assertFalse((root / "plugin-data" / "agent-runs").exists())

                stop = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStop"}), env=env)
                self.assertEqual(json.loads(stop.stdout), {})

                agent_call = run(
                    PYTHON,
                    str(HOOK),
                    stdin=json.dumps({"cwd": str(root), "hook_event_name": "PreToolUse", "tool_name": "Agent", "tool_input": {}}),
                    env=env,
                )
                self.assertEqual(agent_call.stdout, "")

    def test_subagent_stop_cleans_marker_after_packet_deactivation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            (packet / "reports").mkdir(parents=True)
            current = flow / "current"
            current.write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"state": "implementing", "approvals": {"dependencies": []}}), encoding="utf-8")
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            env["PLUGIN_DATA"] = str(root / "plugin-data")
            common = {"cwd": str(root), "session_id": "session", "agent_id": "agent"}
            start = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStart"}), env=env)
            self.assertEqual(start.returncode, 0)
            marker = next((root / "plugin-data" / "agent-runs").glob("*.json"))

            current.unlink()
            stop = run(PYTHON, str(HOOK), stdin=json.dumps({**common, "hook_event_name": "SubagentStop"}), env=env)
            self.assertEqual(json.loads(stop.stdout), {})
            self.assertFalse(marker.exists())


class PreferenceAuditTests(unittest.TestCase):
    def test_personal_rust_library_choice_is_not_a_public_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init = run("git", "init", "-q", cwd=root)
            self.assertEqual(init.returncode, 0, init.stderr)
            (root / "Cargo.toml").write_text('[package]\nname = "sample"\nversion = "0.1.0"\n\n[dependencies]\nchrono = "0.4"\n', encoding="utf-8")
            packet = root / "packet"
            packet.mkdir()
            digest = "sha256:" + hashlib.sha256((root / "Cargo.toml").read_bytes()).hexdigest()
            approval = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "cargo",
                    "name": "chrono",
                    "version": "0.4",
                    "ref": "0.4",
                    "command": "cargo add chrono@0.4",
                    "files": ["Cargo.toml"],
                    "operations": ["add"],
                    "result_sha256": {"Cargo.toml": digest},
                },
            }
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [approval]}}), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertNotIn("RUST-TIME", result.stdout)

            (root / "Cargo.toml").write_text(
                (root / "Cargo.toml").read_text(encoding="utf-8") + 'unrelated = "9"\n',
                encoding="utf-8",
            )
            drift = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(drift.returncode, 2)
            self.assertIn("POLICY-DEPENDENCY-APPROVAL", drift.stdout)

    def test_github_action_diff_requires_exact_machine_readable_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
            workflow = root / ".github" / "workflows" / "release.yml"
            workflow.parent.mkdir(parents=True)
            ref = "a" * 40
            workflow.write_text(f"name: release\nsteps:\n  - uses: owner/action@{ref}\n", encoding="utf-8")
            packet = root / "packet"
            packet.mkdir()
            unrelated = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "github-actions",
                    "name": "other/action",
                    "version": "1.0.0",
                    "ref": ref,
                    "command": None,
                    "files": [".github/workflows/release.yml"],
                    "operations": ["add"],
                    "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [unrelated]}}), encoding="utf-8")
            rejected = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(rejected.returncode, 2)
            self.assertIn("POLICY-GITHUB-ACTION-APPROVAL", rejected.stdout)

            unrelated["dependency"]["name"] = "owner/action"
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [unrelated]}}), encoding="utf-8")
            accepted = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(accepted.returncode, 0, accepted.stderr or accepted.stdout)

            workflow.write_text(f"name: release\nsteps:\n  - uses: owner/action/subpath@{ref}\n", encoding="utf-8")
            unrelated["dependency"]["name"] = "owner/action/subpath"
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [unrelated]}}), encoding="utf-8")
            subpath = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(subpath.returncode, 0, subpath.stderr or subpath.stdout)

            workflow.write_text("name: release\nsteps:\n  - uses: ${{ matrix.action }}\n", encoding="utf-8")
            dynamic = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(dynamic.returncode, 2)
            self.assertIn("POLICY-GITHUB-ACTION-APPROVAL", dynamic.stdout)

            for content in (
                f"name: release\nsteps:\n  - {{ name: test, uses: owner/action@{ref} }}\n",
                f'name: release\nsteps:\n  - "u\\u0073es": owner/action@{ref}\n',
                f'name: release\nsteps:\n  - "u\\x73es": "owner\\/action@{ref}"\n',
                f'name: release\nsteps:\n  - "\\U00000075ses": docker://example.invalid/tool@{ref}\n',
            ):
                with self.subTest(yaml_variant=content):
                    workflow.write_text(content, encoding="utf-8")
                    (packet / "packet.json").write_text(
                        json.dumps({"approvals": {"dependencies": []}}), encoding="utf-8"
                    )
                    variant = run(
                        PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet)
                    )
                    self.assertEqual(variant.returncode, 2)
                    self.assertIn("POLICY-GITHUB-ACTION-APPROVAL", variant.stdout)

    def test_preference_audit_rejects_an_invalid_explicit_git_base(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
            result = run(
                PYTHON, str(FLOW), "audit-preferences", "--root", str(root),
                "--base", "definitely-not-a-commit",
            )
            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "blocked")
            self.assertEqual(payload["findings"][0]["rule"], "POLICY-AUDIT-INPUT")

    def test_github_action_removal_requires_exact_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
            workflow = root / ".github" / "workflows" / "ci.yml"
            workflow.parent.mkdir(parents=True)
            ref = "a" * 40
            workflow.write_text(f"steps:\n  - uses: owner/action/subpath@{ref}\n", encoding="utf-8")
            self.assertEqual(run("git", "add", ".", cwd=root).returncode, 0)
            committed = run(
                "git", "-c", "user.name=Dev Flow Test", "-c", "user.email=dev-flow@example.invalid",
                "commit", "-qm", "fixture", cwd=root,
            )
            self.assertEqual(committed.returncode, 0, committed.stderr)
            workflow.write_text("steps: []\n", encoding="utf-8")
            packet = root / "packet"
            packet.mkdir()
            approval = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "github-actions",
                    "name": "owner/action/subpath",
                    "version": "1.0.0",
                    "ref": ref,
                    "command": None,
                    "files": [".github/workflows/ci.yml"],
                    "operations": ["add"],
                    "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [approval]}}), encoding="utf-8")
            denied = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(denied.returncode, 2)
            self.assertIn("remove:owner/action/subpath", denied.stdout)
            approval["dependency"]["operations"] = ["remove"]
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [approval]}}), encoding="utf-8")
            allowed = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(allowed.returncode, 0, allowed.stderr or allowed.stdout)

    def test_github_action_baseline_is_scoped_to_each_workflow_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(run("git", "init", "-q", cwd=root).returncode, 0)
            workflows = root / ".github" / "workflows"
            workflows.mkdir(parents=True)
            ref = "a" * 40
            (workflows / "ci.yml").write_text(f"steps:\n  - uses: owner/action@{ref}\n", encoding="utf-8")
            self.assertEqual(run("git", "add", ".", cwd=root).returncode, 0)
            committed = run(
                "git", "-c", "user.name=Dev Flow Test", "-c", "user.email=dev-flow@example.invalid",
                "commit", "-qm", "fixture", cwd=root,
            )
            self.assertEqual(committed.returncode, 0, committed.stderr)
            (workflows / "release.yml").write_text(f"steps:\n  - uses: owner/action@{ref}\n", encoding="utf-8")
            packet = root / "packet"
            packet.mkdir()
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": []}}), encoding="utf-8")
            denied = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(denied.returncode, 2)
            self.assertIn("POLICY-GITHUB-ACTION-APPROVAL", denied.stdout)

            approval = {
                "id": "DEP-1",
                "dependency": {
                    "ecosystem": "github-actions", "name": "owner/action", "version": "1.0.0",
                    "ref": ref, "command": None, "files": [".github/workflows/release.yml"],
                    "operations": ["add"], "result_sha256": {},
                },
            }
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [approval]}}), encoding="utf-8")
            allowed = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(allowed.returncode, 0, allowed.stderr or allowed.stdout)

    def test_unapproved_manifest_change_remains_a_neutral_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init = run("git", "init", "-q", cwd=root)
            self.assertEqual(init.returncode, 0, init.stderr)
            (root / "Cargo.toml").write_text('[package]\nname = "sample"\nversion = "0.1.0"\n', encoding="utf-8")
            result = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root))
            self.assertEqual(result.returncode, 2)
            self.assertIn("POLICY-DEPENDENCY-APPROVAL", result.stdout)

    def test_documentation_mentions_do_not_trigger_rust_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init = run("git", "init", "-q", cwd=root)
            self.assertEqual(init.returncode, 0, init.stderr)
            (root / "policy.md").write_text("Chrono is forbidden; use Jiff.\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


class RepositoryContractTests(unittest.TestCase):
    def test_release_quality_contracts_are_top_level_and_actionable(self) -> None:
        def section(text: str, heading: str) -> str:
            marker = f"## {heading}\n"
            body = text.split(marker, 1)[1]
            return body.split("\n## ", 1)[0]

        architecture = (ROOT / "skills" / "architecture-decisions" / "SKILL.md").read_text(encoding="utf-8")
        requirements = (ROOT / "skills" / "requirements-design" / "SKILL.md").read_text(encoding="utf-8")
        verification = (ROOT / "skills" / "verification" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn(
            "Rust-Swift/Kotlin FFI with both consumers uses both platform routes and requires language-level and boundary-isolation tests; missing routes are evidence gaps.",
            section(architecture, "Procedure"),
        )
        self.assertIn(
            "FFI work retains an explicit contract for ABI/layout/versioning, nullability, string/buffer encoding, allocation/free ownership, typed error translation, panic/foreign-exception containment, thread or actor affinity, callback reentrancy/late delivery, cancellation/quiescence, generated-binding compatibility, target architectures/native loading, and lifecycle/backgrounding; test each consumer boundary and keep simulator/emulator gates separate from physical-device gates.",
            section(architecture, "Procedure"),
        )
        self.assertIn(
            "When late material ambiguity changes the baseline, record an `AMB-n`, stop affected work, return the content-bound packet to `awaiting-approval`, increment the revision, preserve approval history, obtain the user disposition, and create fresh digest-bound Requirement Ready and design approvals.",
            section(requirements, "Procedure"),
        )
        self.assertIn(
            "Stateful/concurrent work names native oracles first: admission, claim collision/exclusivity, retry/dedup, restart recovery, drain/shutdown. Tie ordinary failures to executable tests or evidence gaps; full-suite labels are insufficient.",
            section(verification, "EQAC rule"),
        )

    def test_contract_validator_rejects_malformed_nested_content(self) -> None:
        namespace = runpy.run_path(str(ROOT / "evals" / "run_contract_checks.py"), run_name="contract_checks_test")
        validate_contract = namespace["validate_contract"]
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "evals" / "reference-cases" / "sample.md"
            fixture.parent.mkdir(parents=True)
            fixture.write_text("# Sample\n", encoding="utf-8")
            errors = validate_contract(
                Path("invalid.json"),
                {
                    "id": "CASE-INVALID",
                    "profile": "invalid nested values",
                    "prompt": "exercise validation",
                    "fixture": "reference-cases/sample.md",
                    "expected_actions": [""],
                    "forbidden_actions": [1],
                    "required_artifacts": ["does-not-exist.md"],
                },
                root=root,
            )
            self.assertTrue(any("expected_actions items" in error for error in errors))
            self.assertTrue(any("forbidden_actions items" in error for error in errors))
            self.assertTrue(any("unknown required artifacts" in error for error in errors))

    def test_context_template_includes_instruction_freshness(self) -> None:
        template = (ROOT / "skills" / "dev-flow" / "templates" / "context.md").read_text(encoding="utf-8")
        self.assertIn("| Freshness |", template)

    def test_agent_handoff_templates_bind_semantic_baseline(self) -> None:
        templates = ROOT / "skills" / "dev-flow" / "templates"
        brief = (templates / "task-brief.md").read_text(encoding="utf-8")
        report = (templates / "agent-report.md").read_text(encoding="utf-8")
        for token in ("revision", "digest", "AMB", "user-owned"):
            self.assertIn(token, brief)
        for token in ("revision", "digest", "AMB", "requirement ambiguity"):
            self.assertIn(token, report)
        for classification in ("implementation defect", "design defect", "evidence gap", "scope change"):
            self.assertIn(classification, report)

    def test_multi_agent_contract_requires_native_result_and_reconciliation(self) -> None:
        orchestration = (ROOT / "skills" / "dev-flow" / "references" / "multi-agent-v2-orchestration.md").read_text(encoding="utf-8")
        execution = (ROOT / "skills" / "dev-flow" / "templates" / "execution.md").read_text(encoding="utf-8")
        brief = (ROOT / "skills" / "dev-flow" / "templates" / "task-brief.md").read_text(encoding="utf-8")
        for token in (
            "spawned -> working -> terminal -> reconciled",
            "orphan-suspected",
            "wait_agent",
            "at most one interrupt",
            "visible thread count does not need to return to one",
            "DEV_FLOW_AGENT_MARKER_UNAVAILABLE",
            "DEV_FLOW_AGENT_REPORT_MISSING",
        ):
            self.assertIn(token, orchestration)
        for token in ("Soft/hard deadline", "Native result", "Durable report", "Resource lease", "Disposition/recovery"):
            self.assertIn(token, execution)
        for token in ("soft observation deadline", "hard stop deadline", "Native result", "Durable report", "must not block native stop"):
            self.assertIn(token, brief)

        for config in AGENT_CONFIGS.glob("*.toml"):
            content = config.read_text(encoding="utf-8")
            self.assertIn("native final", content, config.name)
            self.assertIn("must not delay stop", content, config.name)

    def test_contract_and_plugin_checks(self) -> None:
        contracts = run(PYTHON, str(ROOT / "evals" / "run_contract_checks.py"))
        self.assertEqual(contracts.returncode, 0, contracts.stderr or contracts.stdout)
        plugin = run(PYTHON, str(FLOW), "check", "--plugin-root", str(ROOT))
        self.assertEqual(plugin.returncode, 0, plugin.stderr or plugin.stdout)


if __name__ == "__main__":
    unittest.main()
