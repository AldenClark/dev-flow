#!/usr/bin/env python3
"""Stdlib-only behavioral and mutation tests for Dev Flow."""

from __future__ import annotations

import json
import hashlib
import io
import os
import runpy
import shutil
import signal
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
import codex_model_adapter as model_adapter  # noqa: E402


def run(*args: str, cwd: Path | None = None, stdin: str | None = None, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, input=stdin, env=env, check=False, capture_output=True, text=True)


def legacy_development_config() -> dict[str, object]:
    """Project the current development config onto the supported 1.6 single-pass ABI."""
    config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
    config["schema_version"] = "1.6"
    config.pop("executor_pipeline", None)
    identity = config.get("evaluator_identity")
    if isinstance(identity, dict) and ("draft" in identity or "inventory" in identity):
        identity["executor"] = identity.pop("draft", identity.pop("inventory", None))
        identity.pop("assembler", None)
        identity["receipt_schema_version"] = "1.0"
    return config


def resolve_fake_release_backend(
    test_case: unittest.TestCase,
    contract: dict[str, object],
    *,
    evaluator_label: str = "release evaluator",
) -> tuple[dict[str, object], dict[str, object]]:
    """Resolve an approved backend without depending on a host Codex install."""
    temp = tempfile.TemporaryDirectory()
    test_case.addCleanup(temp.cleanup)
    fake_backend = Path(temp.name) / ("codex.exe" if sys.platform == "win32" else "codex")
    fake_backend.write_bytes(b"deterministic fake Codex backend")
    approved_contract = json.loads(json.dumps(contract))
    platform_key = paired_eval.release_platform_key(evaluator_label=evaluator_label)
    approved_contract["backend"]["artifacts"][platform_key] = paired_eval.file_sha256(fake_backend)
    version_result = subprocess.CompletedProcess(
        [str(fake_backend), "--version"],
        0,
        stdout=f"{approved_contract['backend']['version']}\n",
        stderr="",
    )
    with (
        mock.patch.object(paired_eval.shutil, "which", return_value=str(fake_backend)),
        mock.patch.object(paired_eval.subprocess, "run", return_value=version_result),
    ):
        identity = paired_eval.resolve_release_backend_identity(
            approved_contract,
            evaluator_label=evaluator_label,
        )
    return approved_contract, identity


def write_fake_codex(root: Path, source: str) -> Path:
    """Create a PATH-resolvable fake Codex launcher on POSIX and Windows."""
    if os.name == "nt":
        script = root / "codex.py"
        script.write_text(source, encoding="utf-8")
        launcher = root / "codex.cmd"
        launcher.write_text(
            f'@echo off\r\n"{PYTHON}" "%~dp0codex.py" %*\r\n',
            encoding="utf-8",
        )
        return launcher
    launcher = root / "codex"
    launcher.write_text(source, encoding="utf-8")
    launcher.chmod(0o755)
    return launcher


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
    def test_wilson_interval_does_not_overstate_small_samples(self) -> None:
        fourteen_of_fifteen = paired_eval.wilson_interval(14, 15)
        self.assertAlmostEqual(fourteen_of_fifteen["point"], 14 / 15)
        self.assertLess(fourteen_of_fifteen["lower"], 0.71)
        self.assertGreater(fourteen_of_fifteen["upper"], 0.98)

        thirty_five_of_thirty_six = paired_eval.wilson_interval(35, 36)
        perfect_thirty_six = paired_eval.wilson_interval(36, 36)
        self.assertLess(thirty_five_of_thirty_six["lower"], 0.9)
        self.assertGreaterEqual(perfect_thirty_six["lower"], 0.9)

        underpowered = {"pass_rate_interval_95": fourteen_of_fifteen}
        self.assertLess(
            underpowered["pass_rate_interval_95"]["lower"],
            0.9,
        )

    def test_quality_scorecard_equal_weights_tasks_and_categories(self) -> None:
        def pair(category: str, pass_rate: float, semantic_coverage: float) -> dict[str, object]:
            aggregate = {
                "pass_rate": pass_rate,
                "semantic_coverage": {
                    "mean": semantic_coverage,
                    "standard_deviation": 0.0,
                    "samples": 3,
                    "unit": "equal-weight work-unit coverage from 0 to 1 per valid grader run",
                },
            }
            return {"category": category, "baseline": aggregate, "candidate": aggregate}

        scorecard = paired_eval.quality_scorecard(
            {
                "PAIR-SMALL": pair("CAT-SMALL", 0.0, 0.0),
                "PAIR-LARGE-1": pair("CAT-LARGE", 1.0, 1.0),
                "PAIR-LARGE-2": pair("CAT-LARGE", 1.0, 1.0),
                "PAIR-LARGE-3": pair("CAT-LARGE", 1.0, 1.0),
            },
            ["CAT-SMALL", "CAT-LARGE"],
        )
        self.assertAlmostEqual(scorecard["task_macro"]["candidate"]["strict_pass_rate"], 0.75)
        self.assertAlmostEqual(scorecard["category_macro"]["candidate"]["strict_pass_rate"], 0.5)
        self.assertAlmostEqual(scorecard["category_macro"]["candidate"]["semantic_coverage"], 0.5)
        self.assertEqual(scorecard["headline"], "category-macro-strict-pass-rate")

    def test_inventory_v2_materializes_a_complete_owner_kind_ledger(self) -> None:
        inventory = {
            "schema_version": "1.0", "case_id": "PAIR-INVENTORY", "attempt": 1,
            "claimed_outcome": "completed",
            "inventory_items": [
                {
                    "item_id": "IT-1", "evidence_family": "analysis",
                    "action": "Inspect the bounded repository state.",
                    "protected_behavior": "Existing local changes remain untouched.",
                    "oracle_or_evidence": "Record the bounded fixture fact exactly.",
                    "status": "verified", "limitation": None,
                    "evidence_refs": [{"source": "fixture", "quote": "bounded fixture fact"}],
                },
                {
                    "item_id": "IT-2", "evidence_family": "test",
                    "action": "Run a deterministic compatibility check.",
                    "protected_behavior": "Compatibility failure remains visible.",
                    "oracle_or_evidence": "Require an explicit pass or fail result.",
                    "status": "not-run", "limitation": "Execution is unavailable.",
                    "evidence_refs": [],
                },
            ],
            "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
        }
        paired_eval.validate_inventory_result(inventory, "PAIR-INVENTORY")
        paired_eval.validate_inventory_evidence_refs(
            inventory,
            fixture="The bounded fixture fact is authoritative.",
            task_prompt="Analyze it.",
        )
        manifest = {
            "schema_version": "1.0", "case_id": "PAIR-INVENTORY", "attempt": 1,
            "supplemental_items": [],
            "claim_assemblies": [
                {"claim_id": "CL-1", "owner": "repo-context", "kind": "repo-context.analysis", "source_item_ids": ["IT-1"]},
                {"claim_id": "CL-2", "owner": "verification", "kind": "verification.test", "source_item_ids": ["IT-2"]},
            ],
            "dispositions": [],
        }
        paired_eval.validate_assembly_manifest(manifest, "PAIR-INVENTORY")
        final, summary = paired_eval.materialize_inventory_claims(
            inventory,
            manifest,
            claim_owner_vocabulary=["repo-context", "verification"],
            claim_kind_vocabulary=[
                {"id": "repo-context.analysis", "owner": "repo-context"},
                {"id": "verification.test", "owner": "verification"},
            ],
        )
        self.assertEqual([claim["claim_id"] for claim in final["claims"]], ["CL-1", "CL-2"])
        self.assertEqual([claim["status"] for claim in final["claims"]], ["verified", "not-run"])
        self.assertTrue(summary["all_sources_accounted"])
        self.assertEqual(summary["final_claims"], 2)

        duplicate_inventory = json.loads(json.dumps(inventory))
        duplicate_inventory["inventory_items"].append({
            **duplicate_inventory["inventory_items"][1], "item_id": "IT-3",
        })
        duplicate_manifest = json.loads(json.dumps(manifest))
        duplicate_manifest["dispositions"] = [{
            "item_id": "IT-3", "disposition": "duplicate",
            "consumed_as_item_id": "IT-2", "rationale": "Byte-identical duplicate.",
        }]
        duplicate_final, duplicate_summary = paired_eval.materialize_inventory_claims(
            duplicate_inventory,
            duplicate_manifest,
            claim_owner_vocabulary=["repo-context", "verification"],
            claim_kind_vocabulary=[
                {"id": "repo-context.analysis", "owner": "repo-context"},
                {"id": "verification.test", "owner": "verification"},
            ],
        )
        self.assertEqual(duplicate_final, final)
        self.assertEqual(duplicate_summary["duplicate_dispositions"], 1)

    def test_inventory_v2_rejects_drop_reuse_family_laundering_and_verified_supplements(self) -> None:
        item = {
            "item_id": "IT-1", "evidence_family": "test",
            "action": "Keep a physical check distinct.",
            "protected_behavior": "Virtual evidence is not promoted.",
            "oracle_or_evidence": "Record an explicit device result.",
            "status": "not-run", "limitation": "No device is available.", "evidence_refs": [],
        }
        inventory = {
            "schema_version": "1.0", "case_id": "PAIR-GUARD", "attempt": 1,
            "claimed_outcome": "completed", "inventory_items": [item],
            "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
        }
        base = {
            "schema_version": "1.0", "case_id": "PAIR-GUARD", "attempt": 1,
            "supplemental_items": [], "dispositions": [],
            "claim_assemblies": [{"claim_id": "CL-1", "owner": "verification", "kind": "verification.test", "source_item_ids": ["IT-1"]}],
        }
        kwargs = {
            "claim_owner_vocabulary": ["verification"],
            "claim_kind_vocabulary": [
                {"id": "verification.test", "owner": "verification"},
                {"id": "verification.limitation", "owner": "verification"},
            ],
        }
        with self.assertRaisesRegex(paired_eval.EvaluationError, "account for every"):
            paired_eval.materialize_inventory_claims(inventory, {**base, "claim_assemblies": []}, **kwargs)
        with self.assertRaisesRegex(paired_eval.EvaluationError, "at most once"):
            paired_eval.materialize_inventory_claims(
                inventory,
                {**base, "claim_assemblies": [*base["claim_assemblies"], {**base["claim_assemblies"][0], "claim_id": "CL-2"}]},
                **kwargs,
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "evidence family"):
            paired_eval.materialize_inventory_claims(
                inventory,
                {**base, "claim_assemblies": [{**base["claim_assemblies"][0], "kind": "verification.limitation"}]},
                **kwargs,
            )
        supplement = {**item, "item_id": "SP-1", "status": "verified", "limitation": None}
        with self.assertRaisesRegex(paired_eval.EvaluationError, "planned or not-run"):
            paired_eval.validate_assembly_manifest(
                {**base, "supplemental_items": [supplement]},
                "PAIR-GUARD",
            )

    def test_inventory_v2_requests_hide_owner_kind_from_stage_one(self) -> None:
        input_value = {
            "fixture": "bounded fixture",
            "capability_sources": {"repo-context": '<source path="secret">neutral guidance</source>'},
            "claim_owner_vocabulary": ["repo-context"],
            "claim_kind_vocabulary": [{"id": "repo-context.analysis", "owner": "repo-context"}],
            "contract": {"prompt": "analyze", "work_units": [{"gold": "CANARY"}]},
        }
        request = paired_eval.build_inventory_stage_request(
            pair_id="PAIR-BLIND-V2", variant="candidate",
            pair_capabilities=["repo-context"], input_value=input_value,
        )
        self.assertNotIn("claim_owner_vocabulary", request)
        self.assertNotIn("claim_kind_vocabulary", request)
        self.assertNotIn("CANARY", json.dumps(request))
        self.assertNotIn("secret", json.dumps(request))

    def test_inventory_grounding_failure_blocks_assembler_and_grader(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            call_log = root / "calls.jsonl"
            output = root / "output"
            fake_codex = write_fake_codex(
                root,
                f'''#!{PYTHON}
import json, pathlib, sys
if "--version" in sys.argv:
    print("codex-cli fake 1.0")
    raise SystemExit(0)
schema = pathlib.Path(sys.argv[sys.argv.index("--output-schema") + 1]).name
role = "inventory" if schema == "inventory-result.json" else ("assembler" if schema == "assembler-result.json" else "grader")
output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
prompt = sys.stdin.read()
case_id = prompt.split('case_id must be "', 1)[1].split('"', 1)[0]
with pathlib.Path({str(call_log)!r}).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"role": role}}) + "\\n")
if role == "inventory":
    result = {{
        "schema_version": "1.0", "case_id": case_id, "attempt": 1,
        "claimed_outcome": "completed",
        "inventory_items": [{{
            "item_id": "IT-1", "evidence_family": "analysis",
            "action": "Inspect the bounded structured-input behavior.",
            "protected_behavior": "Ambiguous evidence never reaches a downstream stage.",
            "oracle_or_evidence": "The duplicated fixture phrase is intentionally ambiguous.",
            "status": "verified", "limitation": None,
            "evidence_refs": [{{"source": "fixture", "quote": "request_user_input"}}]
        }}],
        "interactions": {{"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0}}
    }}
else:
    result = {{}}
output.write_text(json.dumps(result), encoding="utf-8")
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}}}))
''',
            )
            config = json.loads(
                (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
            )
            spec = {"model": "fake-model", "reasoning_effort": "medium"}
            config["evaluator_identity"] = {
                "adapter": "evals/codex_model_adapter.py",
                "backend": {
                    "command": "codex", "version": "codex-cli fake 1.0",
                    "artifacts": {
                        paired_eval.release_platform_key():
                            "sha256:" + hashlib.sha256(fake_codex.read_bytes()).hexdigest()
                    },
                },
                "result_schema_version": "1.3", "receipt_schema_version": "1.2",
                "inventory": spec, "assembler": spec, "grader": spec,
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            adapter = f"{PYTHON} evals/codex_model_adapter.py"
            environment = dict(os.environ)
            environment["PATH"] = str(root) + os.pathsep + environment.get("PATH", "")
            result = run(
                PYTHON, str(PAIRED_RUNNER),
                "--attested-pilot", "--config", str(config_path),
                "--executor-draft", f"{adapter} inventory --model fake-model --reasoning-effort medium",
                "--executor-assembler", f"{adapter} assembler --model fake-model --reasoning-effort medium",
                "--grader", f"{adapter} grader --model fake-model --reasoning-effort medium",
                "--output", str(output),
                "--pair", "PAIR-STRUCTURED-INPUT", "--trials", "3", "--timeout", "30",
                env=environment,
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertTrue((output / "report.json").exists(), result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["records"]), 1)
            record = report["records"][0]
            self.assertIn("quote must occur exactly once", record["executor_error"])
            self.assertEqual(len(record["draft_attempts"]), 1)
            self.assertEqual(record["assembler_attempts"], [])
            self.assertEqual(record["grader_attempts"], [])
            self.assertIsNone(record["inventory_result"])
            self.assertEqual(
                [json.loads(line)["role"] for line in call_log.read_text(encoding="utf-8").splitlines()],
                ["inventory"],
            )
            self.assertIn("terminal evaluator failure circuit opened", " ".join(report["errors"]))

    def test_inventory_v2_native_semantic_stop_is_strict_and_diagnostic_only(self) -> None:
        self.assertTrue(paired_eval.strict_candidate_pass({
            "verdict": "pass", "policy_verdict_checks": {"a": True, "b": True},
        }))
        self.assertFalse(paired_eval.strict_candidate_pass({
            "verdict": "pass", "policy_verdict_checks": {"a": True, "b": False},
        }))
        self.assertFalse(paired_eval.strict_candidate_pass(None))

    def test_inventory_v2_native_semantic_stop_writes_terminal_evidence_before_next_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            call_log = root / "calls.jsonl"
            fake_codex = write_fake_codex(
                root,
                f'''#!{PYTHON}
import json, pathlib, re, sys
if "--version" in sys.argv:
    print("codex-cli fake 1.0")
    raise SystemExit(0)
prompt = sys.stdin.read()
output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
schema = pathlib.Path(sys.argv[sys.argv.index("--output-schema") + 1]).name
case = re.search(r'case_id must be "([^"]+)"', prompt).group(1)
stage = "inventory" if schema == "inventory-result.json" else ("assembler" if schema == "assembler-result.json" else "grader")
with pathlib.Path({str(call_log)!r}).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"stage": stage}}) + "\\n")
if stage == "inventory":
    result = {{
        "schema_version": "1.0", "case_id": case, "attempt": 1,
        "claimed_outcome": "completed",
        "inventory_items": [{{
            "item_id": "IT-1", "evidence_family": "analysis",
            "action": "Inspect the bounded repository state.",
            "protected_behavior": "Existing local changes remain untouched.",
            "oracle_or_evidence": "Record the bounded state before any change.",
            "status": "planned", "limitation": "Repository execution is unavailable.",
            "evidence_refs": []
        }}],
        "interactions": {{"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0}}
    }}
elif stage == "assembler":
    result = {{
        "schema_version": "1.0", "case_id": case, "attempt": 1,
        "supplemental_items": [],
        "claim_assemblies": [{{
            "claim_id": "CL-1", "owner": "repo-context", "kind": "repo-context.analysis",
            "source_item_ids": ["IT-1"]
        }}],
        "dispositions": []
    }}
else:
    work_units = json.loads(re.search(r'<work-units>\\n(.*?)\\n</work-units>', prompt, re.S).group(1))
    result = {{
        "schema_version": "1.3", "case_id": case, "graded_attempt": 1,
        "requirement_fidelity": 0, "scope_discipline": 4, "evidence_quality": 1,
        "forbidden_actions": [], "structural_coverage": ["bounded"],
        "work_unit_assessments": [{{
            "work_unit_id": unit["id"],
            "facet_assessments": [{{
                "facet_id": facet["id"], "status": "missing",
                "evidence": "The bounded plan does not cover this facet.", "support_refs": []
            }} for facet in unit["facets"]]
        }} for unit in work_units],
        "metrics": {{"coverage": 0, "restraint": 4, "ordinary_defect_retention": 0,
                    "actionability": 1, "rework": 4, "unsafe_actions": 0, "false_blocks": 0}},
        "verdict": "fail"
    }}
output.write_text(json.dumps(result), encoding="utf-8")
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}}}))
''',
            )
            config = json.loads(
                (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
            )
            spec = {"model": "fake-model", "reasoning_effort": "medium"}
            config["evaluator_identity"] = {
                "adapter": "evals/codex_model_adapter.py",
                "backend": {
                    "command": "codex", "version": "codex-cli fake 1.0",
                    "artifacts": {
                        paired_eval.release_platform_key():
                            "sha256:" + hashlib.sha256(fake_codex.read_bytes()).hexdigest()
                    },
                },
                "result_schema_version": "1.3", "receipt_schema_version": "1.2",
                "inventory": spec, "assembler": spec, "grader": spec,
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"
            adapter = f"{PYTHON} evals/codex_model_adapter.py"
            environment = dict(os.environ)
            environment["PATH"] = str(root) + os.pathsep + environment.get("PATH", "")
            result = run(
                PYTHON, str(PAIRED_RUNNER), "--attested-pilot", "--config", str(config_path),
                "--pair", "PAIR-ECR", "--trials", "3", "--timeout", "30",
                "--stop-on-first-candidate-fail",
                "--executor-draft", f"{adapter} inventory --model fake-model --reasoning-effort medium",
                "--executor-assembler", f"{adapter} assembler --model fake-model --reasoning-effort medium",
                "--grader", f"{adapter} grader --model fake-model --reasoning-effort medium",
                "--output", str(output), env=environment,
            )
            self.assertEqual(result.returncode, 3, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual((report["status"], progress["status"]), ("stopped", "stopped"))
            self.assertEqual((len(report["records"]), progress["completed_records"]), (2, 2))
            self.assertEqual([record["variant"] for record in report["records"]], ["baseline", "candidate"])
            self.assertEqual([record["trial"] for record in report["records"]], [1, 1])
            self.assertEqual(report["errors"], [])
            self.assertEqual(report["records"][0]["grader"]["verdict"], "fail")
            self.assertEqual(report["records"][1]["grader"]["verdict"], "fail")
            self.assertFalse(report["release_assessment"]["pilot_thresholds_passed"])
            self.assertEqual(
                [json.loads(line)["stage"] for line in call_log.read_text(encoding="utf-8").splitlines()],
                ["inventory", "assembler", "grader"] * 2,
            )
            self.assertTrue(all(
                record["pipeline_stages"]["state_transitions"] == [
                    "InventoryPending", "InventoryValidated", "AssemblyPending", "FinalValidated", "Graded"
                ]
                for record in report["records"]
            ))

    def test_two_stage_monotonic_failure_blocks_grader_and_marks_final_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            call_log = root / "calls.jsonl"
            fake_codex = write_fake_codex(
                root,
                f'''#!{PYTHON}
import json, pathlib, re, sys
if "--version" in sys.argv:
    print("codex-cli fake 1.0")
    raise SystemExit(0)
prompt = sys.stdin.read()
output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
schema = pathlib.Path(sys.argv[sys.argv.index("--output-schema") + 1]).name
case = re.search(r'case_id must be "([^"]+)"', prompt).group(1)
stage = "grader" if schema.startswith("grader-") else ("assembler" if "blind assembly stage" in prompt else "draft")
with pathlib.Path({str(call_log)!r}).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"stage": stage}}) + "\\n")
if stage in {{"draft", "assembler"}}:
    result = {{
        "schema_version": "1.3", "case_id": case, "attempt": 1,
        "artifact_root": "artifacts",
        "claimed_outcome": "blocked" if stage == "assembler" else "completed",
        "actions": ["inspect bounded repository context"],
        "evidence": ["fixture-grounded only"],
        "claims": [{{
            "claim_id": "CL-1", "owner": "repo-context", "kind": "repo-context.analysis",
            "action": "inspect bounded repository context",
            "protected_behavior": "preserve local changes",
            "oracle_or_evidence": "record the bounded repository state",
            "status": "planned", "limitation": "repository access remains unavailable"
        }}],
        "interactions": {{"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0}},
        "usage": {{"tokens": None, "elapsed_seconds": None, "cost": None}},
    }}
else:
    work_units = json.loads(re.search(r'<work-units>\\n(.*?)\\n</work-units>', prompt, re.S).group(1))
    result = {{
        "schema_version": "1.3", "case_id": case, "graded_attempt": 1,
        "requirement_fidelity": 0, "scope_discipline": 4, "evidence_quality": 1,
        "forbidden_actions": [], "structural_coverage": ["bounded"],
        "work_unit_assessments": [{{
            "work_unit_id": unit["id"],
            "facet_assessments": [{{
                "facet_id": facet["id"], "status": "missing",
                "evidence": "not covered", "support_refs": []
            }} for facet in unit["facets"]]
        }} for unit in work_units],
        "metrics": {{"coverage": 0, "restraint": 4, "ordinary_defect_retention": 0,
                    "actionability": 1, "rework": 4, "unsafe_actions": 0, "false_blocks": 0}},
        "verdict": "fail",
    }}
output.write_text(json.dumps(result), encoding="utf-8")
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}}}))
''',
            )
            config = json.loads(
                (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
            )
            spec = {"model": "fake-model", "reasoning_effort": "medium"}
            config["evaluator_identity"]["backend"] = {
                "command": "codex",
                "version": "codex-cli fake 1.0",
                "artifacts": {
                    paired_eval.release_platform_key():
                        "sha256:" + hashlib.sha256(fake_codex.read_bytes()).hexdigest()
                },
            }
            config["evaluator_identity"].pop("inventory", None)
            config["evaluator_identity"]["draft"] = spec
            config["evaluator_identity"]["assembler"] = spec
            config["evaluator_identity"]["grader"] = spec
            config["evaluator_identity"]["receipt_schema_version"] = "1.1"
            config["schema_version"] = "1.7"
            config["executor_pipeline"] = {
                "protocol": "blind-draft-assembler-v1",
                "stage_order": ["draft", "assembler"],
                "draft_request_schema_version": "1.0",
                "assembler_request_schema_version": "1.0",
                "draft_dto": "content-only-v1",
                "first_attempt_semantics": "single-draft-no-regeneration-v1",
                "capability_projection": "task-neutral-content-only-v1",
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"
            adapter_command = f"{PYTHON} evals/codex_model_adapter.py"
            environment = dict(os.environ)
            environment["PATH"] = str(root) + os.pathsep + environment.get("PATH", "")
            result = run(
                PYTHON, str(PAIRED_RUNNER), "--attested-pilot", "--config", str(config_path),
                "--pair", "PAIR-ECR", "--trials", "3", "--timeout", "30",
                "--executor-draft", f"{adapter_command} executor --model fake-model --reasoning-effort medium",
                "--executor-assembler", f"{adapter_command} assembler --model fake-model --reasoning-effort medium",
                "--grader", f"{adapter_command} grader --model fake-model --reasoning-effort medium",
                "--output", str(output), env=environment,
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertTrue((output / "report.json").is_file(), result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["records"]), 1)
            record = report["records"][0]
            self.assertIsNone(record["executor"])
            self.assertIsNone(record["grader"])
            self.assertEqual(record["grader_attempts"], [])
            self.assertEqual(record["pipeline_stages"]["state"], "AssemblyPending")
            self.assertEqual(record["pipeline_stages"]["state_transitions"], [
                "DraftPending", "DraftValidated", "AssemblyPending"
            ])
            self.assertIsNotNone(record["pipeline_stages"]["draft"]["receipt"])
            self.assertIsNotNone(record["pipeline_stages"]["assembly"]["receipt"])
            self.assertEqual(len(record["draft_attempts"]), 1)
            self.assertEqual(len(record["assembler_attempts"]), 1)
            self.assertEqual([item["stage"] for item in map(json.loads, call_log.read_text().splitlines())], [
                "draft", "assembler"
            ])
            self.assertIn("assembler changed the first-attempt claimed outcome", record["executor_error"])
            self.assertIn("terminal evaluator failure circuit opened", " ".join(report["errors"]))
            self.assertEqual(progress["completed_records"], 1)
            self.assertEqual(progress["failed_records"], 1)
            self.assertEqual(progress["last_record"], {
                "pair_id": "PAIR-ECR", "category": "CAT-MIGRATION", "trial": 1, "variant": "baseline",
                "executor_valid": False, "grader_valid": False,
                "draft_valid": True, "assembler_valid": False,
            })

    def test_blind_two_stage_pipeline_is_opaque_attested_ordered_and_uncached(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            call_log = root / "calls.jsonl"
            fake_codex = write_fake_codex(
                root,
                f'''#!{PYTHON}
import json, pathlib, re, sys
if "--version" in sys.argv:
    print("codex-cli fake 1.0")
    raise SystemExit(0)
prompt = sys.stdin.read()
output = pathlib.Path(sys.argv[sys.argv.index("--output-last-message") + 1])
schema = pathlib.Path(sys.argv[sys.argv.index("--output-schema") + 1]).name
case = re.search(r'case_id must be "([^"]+)"', prompt).group(1)
stage = "grader" if schema.startswith("grader-") else ("assembler" if "blind assembly stage" in prompt else "draft")
with pathlib.Path({str(call_log)!r}).open("a", encoding="utf-8") as handle:
    handle.write(json.dumps({{"stage": stage, "cwd": str(pathlib.Path.cwd())}}) + "\\n")
claims = [
    ("CL-1", "repo-context", "repo-context.analysis", "inspect repository state exactly"),
    ("CL-2", "delivery-readiness", "delivery-readiness.decision", "select compatible rollout route exactly"),
    ("CL-3", "verification", "verification.test", "run independent verification cell exactly"),
    ("CL-4", "delivery-readiness", "delivery-readiness.decision", "record rollback decision route exactly"),
    ("CL-5", "delivery-readiness", "delivery-readiness.limitation", "preserve unavailable release gate exactly"),
]
if stage in {{"draft", "assembler"}}:
    result = {{
        "schema_version": "1.3", "case_id": case, "attempt": 1,
        "artifact_root": "artifacts", "claimed_outcome": "completed",
        "actions": ["bounded first attempt"], "evidence": ["fixture-grounded only"],
        "claims": [{{
            "claim_id": claim_id, "owner": owner, "kind": kind, "action": action,
            "protected_behavior": "preserve bounded behavior", "oracle_or_evidence": "planned deterministic oracle",
            "status": "planned", "limitation": "repository execution remains unavailable"
        }} for claim_id, owner, kind, action in claims],
        "interactions": {{"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0}},
        "usage": {{"tokens": None, "elapsed_seconds": None, "cost": None}},
    }}
else:
    work_units = json.loads(re.search(r'<work-units>\\n(.*?)\\n</work-units>', prompt, re.S).group(1))
    by_kind = {{}}
    for claim_id, owner, kind, action in claims:
        by_kind.setdefault(kind, []).append((claim_id, action))
    assessments = []
    for unit in work_units:
        claim_id, action = by_kind[unit["claim_routes"][0]["kind"]].pop(0)
        assessments.append({{
            "work_unit_id": unit["id"],
            "facet_assessments": [{{
                "facet_id": facet["id"], "status": "covered", "evidence": "direct unique support",
                "support_refs": [{{"claim_id": claim_id, "field": "action", "quote": action}}]
            }} for facet in unit["facets"]]
        }})
    result = {{
        "schema_version": "1.3", "case_id": case, "graded_attempt": 1,
        "requirement_fidelity": 4, "scope_discipline": 4, "evidence_quality": 4,
        "forbidden_actions": [], "structural_coverage": ["bounded"],
        "work_unit_assessments": assessments,
        "metrics": {{"coverage": 4, "restraint": 4, "ordinary_defect_retention": 4, "actionability": 4, "rework": 0, "unsafe_actions": 0, "false_blocks": 0}},
        "verdict": "pass"
    }}
output.write_text(json.dumps(result), encoding="utf-8")
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}}}}))
''',
            )
            config = json.loads(
                (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
            )
            config["schema_version"] = "1.7"
            config["executor_pipeline"] = {
                "protocol": "blind-draft-assembler-v1",
                "stage_order": ["draft", "assembler"],
                "draft_request_schema_version": "1.0",
                "assembler_request_schema_version": "1.0",
                "draft_dto": "content-only-v1",
                "first_attempt_semantics": "single-draft-no-regeneration-v1",
                "capability_projection": "task-neutral-content-only-v1",
            }
            spec = {"model": "fake-model", "reasoning_effort": "medium"}
            config["evaluator_identity"] = {
                "adapter": "evals/codex_model_adapter.py",
                "backend": {
                    "command": "codex",
                    "version": "codex-cli fake 1.0",
                    "artifacts": {
                        paired_eval.release_platform_key(): "sha256:" + hashlib.sha256(fake_codex.read_bytes()).hexdigest()
                    },
                },
                "result_schema_version": "1.3",
                "receipt_schema_version": "1.1",
                "draft": spec,
                "assembler": spec,
                "grader": spec,
            }
            config_path = root / "config.json"
            config_path.write_text(json.dumps(config), encoding="utf-8")
            output = root / "output"
            adapter_command = f"{PYTHON} evals/codex_model_adapter.py"
            environment = dict(os.environ)
            environment["PATH"] = str(root) + os.pathsep + environment.get("PATH", "")
            result = run(
                PYTHON, str(PAIRED_RUNNER), "--attested-pilot", "--config", str(config_path),
                "--pair", "PAIR-ECR", "--trials", "3", "--timeout", "30",
                "--executor-draft", f"{adapter_command} executor --model fake-model --reasoning-effort medium",
                "--executor-assembler", f"{adapter_command} assembler --model fake-model --reasoning-effort medium",
                "--grader", f"{adapter_command} grader --model fake-model --reasoning-effort medium",
                "--output", str(output), env=environment,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual((report["schema_version"], len(report["records"])), ("1.7", 6))
            self.assertTrue(all(record["pipeline_stages"]["state"] == "Graded" for record in report["records"]))
            self.assertTrue(all(record["executor"]["usage"]["tokens"] == 14 for record in report["records"]))
            self.assertEqual(report["aggregates"]["candidate"]["contract_metrics"]["context_cost"]["mean"], 14.0)
            nonces = []
            for record in report["records"]:
                stages = record["pipeline_stages"]
                self.assertEqual(stages["state_transitions"], [
                    "DraftPending", "DraftValidated", "AssemblyPending", "FinalValidated", "Graded"
                ])
                self.assertEqual(stages["aggregate_usage"]["tokens"], 14)
                for name in ("draft", "assembly"):
                    nonces.append(stages[name]["receipt"]["call_nonce"])
                nonces.append(record["grader_model_receipt"]["call_nonce"])
            self.assertEqual(len(nonces), len(set(nonces)))
            logged = [json.loads(line) for line in call_log.read_text(encoding="utf-8").splitlines()]
            self.assertEqual([item["stage"] for item in logged], ["draft", "assembler", "grader"] * 6)
            for item in logged:
                self.assertNotIn("baseline", item["cwd"])
                self.assertNotIn("candidate", item["cwd"])
                self.assertNotIn("trial-", item["cwd"])
            requests = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in (output / "model-runs").glob("*/attempt-1/request.json")
            ]
            self.assertEqual(len(requests), 12)
            self.assertTrue(all("trial" not in request and "variant" not in request for request in requests))
            self.assertTrue(all("evaluation_contract" not in json.dumps(request) for request in requests))
            self.assertTrue(all("<source path=" not in json.dumps(request) for request in requests))
            ajv = shutil.which("ajv")
            if ajv is not None:
                for schema_name, data_path in (
                    ("paired-evaluation-config.json", config_path),
                    ("paired-evaluation-report.json", output / "report.json"),
                    ("paired-evaluation-progress.json", output / "progress.json"),
                ):
                    validation = run(
                        ajv, "validate", "--spec=draft2020",
                        "-s", str(ROOT / "evals" / "schemas" / schema_name),
                        "-d", str(data_path),
                    )
                    self.assertEqual(validation.returncode, 0, validation.stderr or validation.stdout)

    def test_schema_1_7_requires_exact_blind_pipeline_and_three_stage_identities(self) -> None:
        config = json.loads(
            (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
        )
        config["schema_version"] = "1.7"
        config["executor_pipeline"] = {
            "protocol": "blind-draft-assembler-v1",
            "stage_order": ["draft", "assembler"],
            "draft_request_schema_version": "1.0",
            "assembler_request_schema_version": "1.0",
            "draft_dto": "content-only-v1",
            "first_attempt_semantics": "single-draft-no-regeneration-v1",
            "capability_projection": "task-neutral-content-only-v1",
        }
        identity = config["evaluator_identity"]
        identity["receipt_schema_version"] = "1.1"
        if "inventory" in identity:
            identity["draft"] = identity.pop("inventory")
        elif "executor" in identity:
            identity["draft"] = identity.pop("executor")
        identity["assembler"] = dict(identity["draft"])
        validated = paired_eval.validate_config(config)
        self.assertEqual(validated["executor_pipeline"]["stage_order"], ["draft", "assembler"])
        self.assertEqual(set(validated["evaluator_identity"]), {
            "adapter", "backend", "result_schema_version", "receipt_schema_version",
            "draft", "assembler", "grader",
        })

        missing = json.loads(json.dumps(config))
        missing["evaluator_identity"].pop("assembler")
        with self.assertRaisesRegex(paired_eval.EvaluationError, "assembler"):
            paired_eval.validate_config(missing)

    def test_two_stage_requests_are_exact_blind_and_monotonic(self) -> None:
        input_value = {
            "fixture": "bounded fixture",
            "capability_sources": {
                "repo-context": '<source path="skills/repo-context/SKILL.md">\nNeutral guidance.\n</source>'
            },
            "claim_owner_vocabulary": ["repo-context"],
            "claim_kind_vocabulary": [{"id": "repo-context.analysis", "owner": "repo-context"}],
            "contract": {"prompt": "analyze the fixture", "work_units": [{"gold": "CANARY"}]},
        }
        draft_request = paired_eval.build_executor_stage_request(
            pair_id="PAIR-BLIND",
            variant="candidate",
            pair_capabilities=["repo-context"],
            input_value=input_value,
        )
        self.assertEqual(set(draft_request), {
            "schema_version", "case_id", "attempt", "capabilities", "capability_sources",
            "claim_owner_vocabulary", "claim_kind_vocabulary", "fixture", "task_prompt",
        })
        serialized = json.dumps(draft_request)
        for forbidden in ("CANARY", "work_units", "candidate", "trial", "skills/repo-context"):
            self.assertNotIn(forbidden, serialized)

        draft = {
            "schema_version": "1.3", "case_id": "PAIR-BLIND", "attempt": 1,
            "claimed_outcome": "completed", "actions": ["plan"], "evidence": ["bounded"],
            "claims": [{
                "claim_id": "CL-1", "owner": "repo-context", "kind": "repo-context.analysis",
                "action": "inspect state", "protected_behavior": "preserve changes",
                "oracle_or_evidence": "record state", "status": "planned",
                "limitation": "repository access unavailable",
            }],
            "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
        }
        assembly_request = paired_eval.build_assembler_request(draft_request, draft)
        self.assertEqual(set(assembly_request), set(draft_request) | {"draft_result"})
        with self.assertRaisesRegex(paired_eval.EvaluationError, "promote"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "claims": [{**draft["claims"][0], "status": "verified"}]},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "preserve the limitation"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "claims": [{**draft["claims"][0], "limitation": None}]},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "interaction counts"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "interactions": {**draft["interactions"], "reminders": 1}},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "executed command"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "claims": [{
                    **draft["claims"][0],
                    "oracle_or_evidence": "command output proved success",
                }]},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "must remain planned"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "claims": [*draft["claims"], {
                    **draft["claims"][0], "claim_id": "CL-2", "status": "verified",
                }]},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "preserve oracle"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "claims": [{
                    **draft["claims"][0], "oracle_or_evidence": "new planned oracle",
                }]},
            )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "rewrite first-attempt evidence"):
            paired_eval.validate_monotonic_assembly(
                draft,
                {**draft, "evidence": ["new evidence"]},
            )

    def test_receipt_1_1_rejects_cross_call_swap_output_and_draft_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            request = {"schema_version": "1.0", "case_id": "PAIR", "attempt": 1}
            draft = {"content": "immutable"}
            model_output = b'{"bounded":true}'
            (run_root / "model-result.json").write_bytes(model_output)
            backend = {
                "command": "codex", "path": "/approved/codex", "platform": "darwin-arm64",
                "version": "codex-cli test", "sha256": "sha256:" + "a" * 64,
            }
            identity = {
                "role": "executor", "stage": "assembly", "model": "test-model",
                "reasoning_effort": "medium", "receipt_schema_version": "1.1", "backend": backend,
            }
            receipt = {
                "schema_version": "1.1", "role": "executor", "stage": "assembly",
                "status": "completed", "model": "test-model", "reasoning_effort": "medium",
                "call_nonce": "call-a", "request_sha": paired_eval.canonical_json_sha256(request),
                "prompt_sha": "sha256:" + "b" * 64,
                "draft_sha": paired_eval.canonical_json_sha256(draft),
                "model_output_sha": "sha256:" + hashlib.sha256(model_output).hexdigest(),
                "tokens": 3, "token_usage": {"input_tokens": 2, "output_tokens": 1},
                "elapsed_seconds": 0.1, "prompt_bytes": 10, "capability_source_bytes": 0,
                "model_output_bytes": len(model_output), "monetary_cost": None,
                "cost_basis": "not exposed", "codex_exit_code": 0,
                "tool_events": {"policy": "fail-on-any-tool-event", "total": 0, "categories": {}, "invalid_jsonl_lines": 0},
                "backend": backend, "failure": None,
            }
            path = run_root / "model-usage.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            paired_eval.validate_release_model_receipt(
                run_root, identity, request=request, call_nonce="call-a", draft=draft,
            )
            failed_receipt = json.loads(json.dumps(receipt))
            failed_receipt["status"] = "failed"
            failed_receipt["codex_exit_code"] = 2
            failed_receipt["failure"] = {"kind": "infrastructure"}
            path.write_text(json.dumps(failed_receipt), encoding="utf-8")
            failed_summary = paired_eval.validate_bound_attempt_receipt(
                paired_eval.ProgramOutcome(None, "transport", "infrastructure", 0.1, run_root),
                identity,
                request=request,
                call_nonce="call-a",
                draft=draft,
                evaluator_label="attested pilot evaluator",
            )
            self.assertEqual(failed_summary["status"], "failed")
            path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "call_nonce"):
                paired_eval.validate_release_model_receipt(
                    run_root, identity, request=request, call_nonce="call-b", draft=draft,
                )
            with self.assertRaisesRegex(paired_eval.EvaluationError, "draft_sha"):
                paired_eval.validate_release_model_receipt(
                    run_root, identity, request=request, call_nonce="call-a", draft={"content": "changed"},
                )
            (run_root / "model-result.json").write_bytes(b"changed")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "output hash"):
                paired_eval.validate_release_model_receipt(
                    run_root, identity, request=request, call_nonce="call-a", draft=draft,
                )

    def test_stage_local_retry_reuses_bytes_without_regenerating_draft(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            draft_request = {"stage": "draft", "content": "same"}
            assembly_request = {"stage": "assembly", "content": "same", "draft_result": {"fixed": True}}
            draft_outcome, draft_attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", "import json,sys; json.load(sys.stdin); print('{}')"],
                draft_request, root / "draft", 2, 1,
            )
            self.assertIsNone(draft_outcome.error)
            script = (
                "import json,pathlib,sys; json.load(sys.stdin); "
                "first=pathlib.Path.cwd().name == 'attempt-1'; "
                "print(json.dumps({'status':'invalid','error_kind':'infrastructure','error':'transport'}), file=sys.stderr) if first else print('{}'); "
                "raise SystemExit(2 if first else 0)"
            )
            assembly_outcome, assembly_attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", script], assembly_request, root / "assembly", 2, 1,
                attempt_receipt_validator=lambda outcome: {
                    "status": "completed" if outcome.error is None else "failed"
                },
            )
            self.assertIsNone(assembly_outcome.error)
            self.assertEqual(len(draft_attempts), 1)
            self.assertEqual(len(assembly_attempts), 2)
            self.assertEqual(
                (root / "assembly" / "attempt-1" / "request.json").read_bytes(),
                (root / "assembly" / "attempt-2" / "request.json").read_bytes(),
            )
            self.assertEqual(
                [item["model_receipt"]["status"] for item in assembly_attempts],
                ["failed", "completed"],
            )
            rejected, rejected_attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", script], assembly_request, root / "rejected", 2, 1,
                attempt_receipt_validator=lambda outcome: (_ for _ in ()).throw(
                    paired_eval.EvaluationError("receipt mismatch")
                ),
            )
            self.assertEqual(rejected.error_kind, "identity")
            self.assertEqual(len(rejected_attempts), 1)
            self.assertFalse(rejected_attempts[0]["retry_scheduled"])

    def test_attested_timeout_retry_requires_completely_absent_model_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            request = {"stage": "assembly", "draft_result": {"fixed": True}}
            writes_then_hangs = (
                "import pathlib,time; "
                "pathlib.Path('model-result.json').write_text('{}'); time.sleep(1)"
            )
            unsafe, unsafe_attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", writes_then_hangs],
                request,
                root / "unsafe-output",
                0.05,
                1,
                attempt_receipt_validator=lambda outcome: {"status": "completed"},
            )
            self.assertEqual(unsafe.error_kind, "unsafe-output")
            self.assertEqual(len(unsafe_attempts), 1)
            self.assertFalse(unsafe_attempts[0]["retry_scheduled"])
            self.assertTrue((root / "unsafe-output" / "attempt-1" / "model-result.json").is_file())

            no_output_then_succeeds = (
                "import json,pathlib,sys,time; "
                "pathlib.Path('nonce.txt').write_text(sys.argv[-1]); "
                "time.sleep(1) if pathlib.Path.cwd().name == 'attempt-1' else print('{}')"
            )
            clean, clean_attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", no_output_then_succeeds, "--call-nonce", "fixed-nonce"],
                request,
                root / "clean-timeout",
                0.05,
                1,
                attempt_receipt_validator=lambda outcome: {"status": "completed"},
            )
            self.assertIsNone(clean.error)
            self.assertEqual(len(clean_attempts), 2)
            self.assertTrue(clean_attempts[0]["retry_scheduled"])
            self.assertEqual(
                (root / "clean-timeout" / "attempt-1" / "request.json").read_bytes(),
                (root / "clean-timeout" / "attempt-2" / "request.json").read_bytes(),
            )
            self.assertEqual(
                (root / "clean-timeout" / "attempt-1" / "nonce.txt").read_text(),
                (root / "clean-timeout" / "attempt-2" / "nonce.txt").read_text(),
            )

    def test_adapter_classifies_only_known_transport_failures_as_infrastructure(self) -> None:
        self.assertEqual(
            model_adapter.codex_failure_kind(
                "ERROR responses_websocket: failed to connect to websocket: IO error: tls handshake eof"
            ),
            "infrastructure",
        )
        self.assertEqual(model_adapter.codex_failure_kind("HTTP 503 service unavailable"), "infrastructure")
        self.assertIsNone(model_adapter.codex_failure_kind("model result failed schema validation"))
        self.assertEqual(model_adapter.codex_failure_kind("", exit_code=1), "environment")

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

    def test_timeout_only_retry_preserves_first_attempt_in_an_isolated_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            control_root = Path(temp) / "program"
            script = (
                "import json,pathlib,sys,time; "
                "json.load(sys.stdin); "
                "time.sleep(0.2) if pathlib.Path.cwd().name == 'attempt-1' else None; "
                "print('{}')"
            )
            outcome, attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", script],
                {"bounded": True},
                control_root,
                0.05,
                1,
            )
            self.assertIsNone(outcome.error)
            self.assertEqual(outcome.run_root, control_root / "attempt-2")
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]["error_kind"], "timeout")
            self.assertTrue(attempts[0]["retry_scheduled"])
            self.assertEqual(attempts[1]["status"], "completed")
            self.assertFalse(attempts[1]["retry_scheduled"])
            self.assertTrue((control_root / "attempt-1" / "runner-error.txt").is_file())
            self.assertTrue((control_root / "attempt-1" / "request.json").is_file())
            self.assertTrue((control_root / "attempt-2" / "request.json").is_file())

    def test_non_timeout_program_failure_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            control_root = Path(temp) / "program"
            outcome, attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", "raise SystemExit(2)"],
                {"bounded": True},
                control_root,
                2,
                1,
            )
            self.assertEqual(outcome.error_kind, "exit")
            self.assertEqual(outcome.error, "program exited 2")
            self.assertEqual(len(attempts), 1)
            self.assertFalse(attempts[0]["retry_scheduled"])
            self.assertFalse((control_root / "attempt-2").exists())

    def test_typed_infrastructure_failure_is_retried_and_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            control_root = Path(temp) / "program"
            script = (
                "import json,pathlib,sys; json.load(sys.stdin); "
                "first=pathlib.Path.cwd().name == 'attempt-1'; "
                "print(json.dumps({'status':'invalid','error_kind':'infrastructure','error':'transient transport'}), file=sys.stderr) if first else print('{}'); "
                "raise SystemExit(2 if first else 0)"
            )
            outcome, attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", script],
                {"bounded": True},
                control_root,
                2,
                1,
            )
            self.assertIsNone(outcome.error)
            self.assertEqual(len(attempts), 2)
            self.assertEqual(attempts[0]["error_kind"], "infrastructure")
            self.assertTrue(attempts[0]["retry_scheduled"])
            self.assertEqual(attempts[1]["status"], "completed")
            self.assertIn("transient transport", (control_root / "attempt-1" / "stderr.txt").read_text())

    @unittest.skipUnless(os.name == "posix", "POSIX signal semantics are required")
    def test_runner_sigterm_records_terminal_progress_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            executor = root / "executor.py"
            child_pid = root / "executor.pid"
            executor.write_text(
                "import os,pathlib,sys,time\n"
                f"pathlib.Path({str(child_pid)!r}).write_text(str(os.getpid()), encoding='utf-8')\n"
                "time.sleep(30)\n",
                encoding="utf-8",
            )
            grader = root / "grader.py"
            grader.write_text("raise SystemExit('grader must not run')\n", encoding="utf-8")
            output = root / "output"
            config_path = root / "legacy-config.json"
            config_path.write_text(json.dumps(legacy_development_config()), encoding="utf-8")
            owner = subprocess.Popen(
                [
                    PYTHON,
                    str(PAIRED_RUNNER),
                    "--executor",
                    f"{PYTHON} {executor}",
                    "--grader",
                    f"{PYTHON} {grader}",
                    "--output",
                    str(output),
                    "--config",
                    str(config_path),
                    "--pair",
                    "PAIR-ECR",
                    "--trials",
                    "3",
                ],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                deadline = time.monotonic() + 5
                while not child_pid.exists() and time.monotonic() < deadline:
                    time.sleep(0.02)
                self.assertTrue(child_pid.exists(), "executor did not start")
                os.kill(owner.pid, signal.SIGTERM)
                stdout, stderr = owner.communicate(timeout=5)
                self.assertEqual(owner.returncode, 2, stderr or stdout)
                progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
                report = json.loads((output / "report.json").read_text(encoding="utf-8"))
                self.assertEqual(progress["status"], "incomplete")
                self.assertEqual(report["status"], "incomplete")
                self.assertEqual((progress["completed_records"], len(report["records"])), (1, 1))
                self.assertIn("cancelled by SIGTERM", json.dumps(report["errors"]))
                pid = int(child_pid.read_text(encoding="utf-8"))
                with self.assertRaises(ProcessLookupError):
                    os.kill(pid, 0)
            finally:
                if owner.poll() is None:
                    owner.kill()
                    owner.communicate(timeout=2)

    def test_exhausted_infrastructure_failure_opens_circuit_before_more_model_calls(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = root / "offline.py"
            output = root / "output"
            config_path = root / "legacy-config.json"
            config_path.write_text(json.dumps(legacy_development_config()), encoding="utf-8")
            adapter.write_text(
                "import json,sys; json.load(sys.stdin); "
                "print(json.dumps({'status':'invalid','error_kind':'infrastructure','error':'offline'}), file=sys.stderr); "
                "raise SystemExit(2)\n",
                encoding="utf-8",
            )
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                f"{PYTHON} {adapter}",
                "--grader",
                f"{PYTHON} {adapter}",
                "--output",
                str(output),
                "--config",
                str(config_path),
                "--pair",
                "PAIR-EQAC",
                "--trials",
                "3",
                "--infrastructure-retries",
                "1",
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["records"]), 1)
            self.assertEqual(report["infrastructure_summary"]["exhausted_infrastructure"], 1)
            self.assertIn("infrastructure circuit opened", " ".join(report["errors"]))

    def test_nonretryable_evaluator_failure_opens_circuit_after_first_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = root / "broken.py"
            output = root / "output"
            config_path = root / "legacy-config.json"
            config_path.write_text(json.dumps(legacy_development_config()), encoding="utf-8")
            adapter.write_text(
                "import json,sys; json.load(sys.stdin); raise SystemExit(2)\n",
                encoding="utf-8",
            )
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                f"{PYTHON} {adapter}",
                "--grader",
                f"{PYTHON} {adapter}",
                "--output",
                str(output),
                "--config",
                str(config_path),
                "--pair",
                "PAIR-EQAC",
                "--trials",
                "3",
                "--infrastructure-retries",
                "1",
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["records"]), 1)
            self.assertIn("terminal evaluator failure circuit opened", " ".join(report["errors"]))

    def test_postprocess_schema_failure_opens_circuit_after_first_record(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            adapter = root / "empty_object.py"
            output = root / "output"
            config_path = root / "legacy-config.json"
            config_path.write_text(json.dumps(legacy_development_config()), encoding="utf-8")
            adapter.write_text(
                "import json,sys; json.load(sys.stdin); print('{}')\n",
                encoding="utf-8",
            )
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--executor",
                f"{PYTHON} {adapter}",
                "--grader",
                f"{PYTHON} {adapter}",
                "--output",
                str(output),
                "--config",
                str(config_path),
                "--pair",
                "PAIR-EQAC",
                "--trials",
                "3",
                "--infrastructure-retries",
                "1",
            )
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(len(report["records"]), 1)
            self.assertIn("terminal evaluator failure circuit opened", " ".join(report["errors"]))

    def test_invalid_program_output_is_not_retried(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            control_root = Path(temp) / "program"
            outcome, attempts = paired_eval.run_program_with_infrastructure_retry(
                [PYTHON, "-c", "print('not-json')"],
                {"bounded": True},
                control_root,
                2,
                1,
            )
            self.assertEqual(outcome.error_kind, "invalid-output")
            self.assertEqual(len(attempts), 1)
            self.assertFalse(attempts[0]["retry_scheduled"])
            self.assertFalse((control_root / "attempt-2").exists())

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
            config_path = root / "legacy-config.json"
            config_path.write_text(json.dumps(legacy_development_config()), encoding="utf-8")
            executor.write_text(
                """import json
import pathlib
import sys
request = json.load(sys.stdin)
candidate = bool(request["capabilities"])
artifacts = pathlib.Path("artifacts")
artifacts.mkdir()
claim_specs = [
    ("repo-context", "repo-context.analysis"),
    ("delivery-readiness", "delivery-readiness.decision"),
    ("verification", "verification.test"),
    ("delivery-readiness", "delivery-readiness.decision"),
    ("delivery-readiness", "delivery-readiness.limitation"),
]
print(json.dumps({
    "schema_version": "1.3",
    "case_id": request["case_id"],
    "attempt": 1,
    "artifact_root": "artifacts",
    "claimed_outcome": "completed",
    "actions": ["capability-applied" if candidate else "baseline-action"],
    "evidence": ["isolated first attempt"],
    "claims": [
        {
            "claim_id": f"CL-{claim_index}",
            "owner": owner,
            "kind": kind,
            "action": f"bounded material work unit {claim_index}",
            "protected_behavior": "the fixture's protected behavior",
            "oracle_or_evidence": "bounded first-attempt oracle",
            "status": "planned",
            "limitation": "repository execution is outside this fixture"
        }
        for claim_index, (owner, kind) in enumerate(claim_specs, 1)
    ],
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
result = {
    "schema_version": "1.3",
    "case_id": request["case_id"],
    "graded_attempt": 1,
    "requirement_fidelity": score,
    "scope_discipline": score,
    "evidence_quality": score,
    "forbidden_actions": [],
    "structural_coverage": ["bounded"],
    "metrics": {"coverage": score, "restraint": score, "ordinary_defect_retention": score, "actionability": score, "rework": 0 if candidate else 2, "unsafe_actions": 0, "false_blocks": 0},
    "verdict": "pass" if candidate else "fail"
}
contract = request.get("evaluation_contract")
if contract:
    work_units = contract["work_units"]
    claims_by_kind = {}
    for claim in request["executor_result"]["claims"]:
        claims_by_kind.setdefault(claim["kind"], []).append(claim)
    assessments = []
    for work_unit in work_units:
        claim = claims_by_kind[work_unit["claim_routes"][0]["kind"]].pop(0)
        assessments.append({
            "work_unit_id": work_unit["id"],
            "facet_assessments": [
                {
                    "facet_id": facet["id"],
                    "status": "covered",
                    "evidence": "bounded action",
                    "support_refs": [{
                        "claim_id": claim["claim_id"],
                        "field": "action",
                        "quote": claim["action"]
                    }]
                }
                for facet in work_unit["facets"]
            ]
        })
    result["work_unit_assessments"] = assessments
print(json.dumps(result))
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
                "--config",
                str(config_path),
                "--pair",
                "PAIR-ECR",
                "--trials",
                "3",
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            report = json.loads((output / "report.json").read_text(encoding="utf-8"))
            progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(
                (progress["status"], progress["completed_records"], progress["expected_records"]),
                ("complete", 6, 6),
            )
            self.assertEqual(progress["last_record"]["pair_id"], "PAIR-ECR")
            self.assertEqual((report["status"], len(report["records"])), ("complete", 6))
            self.assertEqual(report["aggregates"]["candidate"]["pass_rate"], 1.0)
            self.assertEqual(report["aggregates"]["baseline"]["pass_rate"], 0.0)
            self.assertEqual(report["aggregates"]["candidate"]["semantic_coverage"]["mean"], 1.0)
            self.assertLess(report["aggregates"]["candidate"]["pass_rate_interval_95"]["lower"], 0.5)
            self.assertEqual(
                report["aggregates"]["scorecard"]["category_macro"]["candidate"],
                {"strict_pass_rate": 1.0, "semantic_coverage": 1.0},
            )
            self.assertEqual(report["aggregates"]["candidate"]["grader_calibration"]["policy_overrides"], 0)
            self.assertEqual(report["pair_aggregates"]["PAIR-ECR"]["candidate"]["pass_rate"], 1.0)
            self.assertEqual(report["category_aggregates"]["CAT-MIGRATION"]["candidate"]["pass_rate"], 1.0)
            self.assertEqual(report["candidate_minus_baseline"]["usage"]["tokens"], 10.0)
            self.assertEqual(report["metric_contract"], list(paired_eval.CONTRACT_METRICS))
            self.assertEqual(report["evaluation_plan"]["mode"], "pilot")
            self.assertEqual(report["infrastructure_policy"]["maximum_timeout_retries"], 0)
            self.assertEqual(report["infrastructure_summary"]["executor_retries"], 0)
            self.assertEqual(report["infrastructure_summary"]["grader_retries"], 0)
            self.assertEqual(report["infrastructure_summary"]["maximum_attempts_per_call"], 1)
            self.assertTrue(all(len(item["executor_attempts"]) == 1 for item in report["records"]))
            self.assertTrue(all(len(item["grader_attempts"]) == 1 for item in report["records"]))
            self.assertEqual(report["aggregates"]["candidate"]["contract_metrics"]["ordinary_defect_retention"]["mean"], 4.0)
            self.assertEqual(report["aggregates"]["candidate"]["contract_metrics"]["reminder_rate"]["mean"], 0.0)
            self.assertFalse(report["release_assessment"]["release_ready"])
            self.assertFalse(report["release_assessment"]["model_gate_ready"])
            self.assertEqual(
                report["evidence_layers"]["deterministic_repository_verification"]["status"],
                "external-required",
            )
            self.assertEqual(
                next(item for item in report["release_assessment"]["gates"] if item["gate"] == "evaluation-completeness")["status"],
                "passed",
            )
            self.assertEqual(
                next(
                    item
                    for item in report["release_assessment"]["gates"]
                    if item["gate"] == "category-set-completeness"
                )["status"],
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
            self.assertEqual(
                next(item for item in report["release_assessment"]["gates"] if item["gate"] == "infrastructure-retry-integrity")["status"],
                "passed",
            )
            self.assertTrue(all(item["executor"]["attempt"] == 1 for item in report["records"]))
            grader_request_path = next((output / "grader-runs").glob("*/attempt-1/request.json"))
            grader_request = json.loads(grader_request_path.read_text(encoding="utf-8"))
            self.assertNotIn("variant", grader_request)
            self.assertNotIn("capabilities", grader_request)
            self.assertNotIn("condition", grader_request)
            self.assertIn("evaluation_contract", grader_request)
            self.assertNotIn("baseline", str(grader_request_path))
            self.assertNotIn("candidate", str(grader_request_path))
            self.assertNotIn("artifact_root", grader_request["executor_result"])
            self.assertNotIn("usage", grader_request["executor_result"])
            executor_requests = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in output.glob("PAIR-ECR/trial-*/**/executor/attempt-1/request.json")
            ]
            self.assertEqual(len(executor_requests), 6)
            owner_vocabularies = {tuple(item["claim_owner_vocabulary"]) for item in executor_requests}
            self.assertEqual(len(owner_vocabularies), 1)
            kind_vocabularies = {
                tuple((kind["id"], kind["owner"]) for kind in item["claim_kind_vocabulary"])
                for item in executor_requests
            }
            self.assertEqual(len(kind_vocabularies), 1)
            self.assertTrue(all("evaluation_contract" not in item for item in executor_requests))
            self.assertTrue(all("obligations" not in item for item in executor_requests))

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
                {
                    "CAT-MIGRATION": {
                        "baseline": report["category_aggregates"]["CAT-MIGRATION"]["candidate"],
                        "candidate": report["category_aggregates"]["CAT-MIGRATION"]["candidate"],
                    }
                },
            )
            self.assertTrue(perfect_pilot["pilot_thresholds_passed"])
            self.assertFalse(perfect_pilot["release_ready"])

            canonical_bytes = (ROOT / "evals" / "paired-evaluations-acceptance.json").read_bytes()
            canonical = json.loads(canonical_bytes)
            acceptance_thresholds = canonical["release_thresholds"]
            head = run("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip()
            input_snapshot = {"source": "git-commit", "commit": head, "entries": [], "sha256": "sha256:" + "1" * 64}
            expected_runs = len(canonical["release_plan"]["pair_ids"]) * canonical["release_plan"]["trials_per_pair"]
            full_candidate = {
                **report["aggregates"]["candidate"],
                "runs": expected_runs,
                "valid_executor_runs": expected_runs,
                "valid_grader_runs": expected_runs,
                "pass_rate_interval_95": paired_eval.wilson_interval(
                    expected_runs, expected_runs
                ),
            }
            release_plan = {
                "mode": "release",
                "config_schema_version": canonical["schema_version"],
                "dataset_role": canonical["dataset_role"],
                "required_pair_ids": canonical["release_plan"]["pair_ids"],
                "evaluated_pair_ids": canonical["release_plan"]["pair_ids"],
                "required_category_ids": canonical["release_plan"]["category_ids"],
                "evaluated_category_ids": canonical["release_plan"]["category_ids"],
                "minimum_cases_per_category": canonical["release_plan"]["minimum_cases_per_category"],
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
            full_category = {
                **report["category_aggregates"]["CAT-MIGRATION"]["candidate"],
                "runs": canonical["release_plan"]["minimum_cases_per_category"]
                * canonical["release_plan"]["trials_per_pair"],
                "valid_executor_runs": canonical["release_plan"]["minimum_cases_per_category"]
                * canonical["release_plan"]["trials_per_pair"],
                "valid_grader_runs": canonical["release_plan"]["minimum_cases_per_category"]
                * canonical["release_plan"]["trials_per_pair"],
                "pass_rate_interval_95": paired_eval.wilson_interval(
                    canonical["release_plan"]["minimum_cases_per_category"]
                    * canonical["release_plan"]["trials_per_pair"],
                    canonical["release_plan"]["minimum_cases_per_category"]
                    * canonical["release_plan"]["trials_per_pair"],
                ),
            }
            full_categories = {
                category: {"baseline": full_category, "candidate": full_category}
                for category in canonical["release_plan"]["category_ids"]
            }
            development_plan = {**release_plan, "dataset_role": "development"}
            with mock.patch.object(
                paired_eval,
                "evaluation_input_snapshot",
                return_value=({}, input_snapshot),
            ):
                development_assessment = paired_eval.assess_release(
                    full_candidate,
                    full_candidate,
                    acceptance_thresholds,
                    development_plan,
                    full_categories,
                )
            self.assertFalse(development_assessment["release_ready"])

            with mock.patch.object(
                paired_eval,
                "evaluation_input_snapshot",
                return_value=({}, input_snapshot),
            ):
                complete_assessment = paired_eval.assess_release(
                    full_candidate,
                    full_candidate,
                    acceptance_thresholds,
                    release_plan,
                    full_categories,
                )
            self.assertTrue(complete_assessment["model_gate_ready"])
            self.assertFalse(complete_assessment["release_ready"])
            self.assertEqual(
                next(
                    item
                    for item in complete_assessment["gates"]
                    if item["gate"] == "candidate-pass-rate-confidence-95"
                )["status"],
                "passed",
            )

    def test_executor_artifacts_must_be_a_strict_descendant_not_the_control_root(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            result = {
                "schema_version": "1.3",
                "case_id": "PAIR-ECR",
                "attempt": 1,
                "artifact_root": str(run_root),
                "claimed_outcome": "completed",
                "actions": ["bounded"],
                "evidence": ["bounded"],
                "claims": [
                    {
                        "claim_id": "CL-1",
                        "owner": "repo-context",
                        "kind": "repo-context.analysis",
                        "action": "inspect",
                        "protected_behavior": "bounded behavior",
                        "oracle_or_evidence": "bounded fixture",
                        "status": "planned",
                        "limitation": None,
                    }
                ],
                "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
                "usage": {"tokens": 1, "elapsed_seconds": 0.1, "cost": 0.0},
            }
            with self.assertRaisesRegex(paired_eval.EvaluationError, "strict descendant"):
                paired_eval.validate_executor(
                    result,
                    run_root,
                    "PAIR-ECR",
                    ["repo-context", "verification"],
                )

    def test_executor_claim_ledger_is_versioned_unique_and_owner_allowlisted(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            artifact_root = run_root / "artifacts"
            artifact_root.mkdir()
            result = {
                "schema_version": "1.3",
                "case_id": "PAIR-1",
                "attempt": 1,
                "artifact_root": str(artifact_root),
                "claimed_outcome": "completed",
                "actions": ["inspect"],
                "evidence": ["bounded fixture"],
                "claims": [
                    {
                        "claim_id": "CL-1",
                        "owner": "repo-context",
                        "kind": "repo-context.analysis",
                        "action": "inspect",
                        "protected_behavior": "bounded behavior",
                        "oracle_or_evidence": "fixture",
                        "status": "planned",
                        "limitation": None,
                    }
                ],
                "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
                "usage": {"tokens": 1, "elapsed_seconds": 0.1, "cost": None},
            }
            owners = ["repo-context", "verification"]
            kinds = [
                {"id": "repo-context.analysis", "owner": "repo-context"},
                {"id": "verification.test", "owner": "verification"},
            ]
            self.assertEqual(
                paired_eval.validate_executor(
                    json.loads(json.dumps(result)),
                    run_root,
                    "PAIR-1",
                    owners,
                    kinds,
                    enforce_kind_alignment=True,
                )["claims"][0]["claim_id"],
                "CL-1",
            )
            wrong_version = json.loads(json.dumps(result))
            wrong_version["schema_version"] = "1.0"
            with self.assertRaisesRegex(paired_eval.EvaluationError, "schema_version"):
                paired_eval.validate_executor(wrong_version, run_root, "PAIR-1", owners)
            duplicate = json.loads(json.dumps(result))
            duplicate["claims"].append(json.loads(json.dumps(duplicate["claims"][0])))
            with self.assertRaisesRegex(paired_eval.EvaluationError, "claim_id.*unique"):
                paired_eval.validate_executor(duplicate, run_root, "PAIR-1", owners)
            wrong_owner = json.loads(json.dumps(result))
            wrong_owner["claims"][0]["owner"] = "unregistered-owner"
            with self.assertRaisesRegex(paired_eval.EvaluationError, "allowed claim-owner vocabulary"):
                paired_eval.validate_executor(
                    wrong_owner, run_root, "PAIR-1", owners, kinds, enforce_kind_alignment=True
                )
            wrong_kind = json.loads(json.dumps(result))
            wrong_kind["claims"][0]["kind"] = "verification.test"
            with self.assertRaisesRegex(paired_eval.EvaluationError, "kind registry owner"):
                paired_eval.validate_executor(
                    wrong_kind, run_root, "PAIR-1", owners, kinds, enforce_kind_alignment=True
                )

    def test_runner_rejects_pair_id_path_escape_before_creating_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = legacy_development_config()
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

    def test_schema_1_4_rejects_an_obligation_owner_missing_from_pair_capabilities(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        pair = next(item for item in config["pairs"] if item["id"] == "PAIR-ECR")
        contract = json.loads((ROOT / "evals" / pair["contract"]).read_text(encoding="utf-8"))
        required_owner = contract["work_units"][0]["owner"]
        pair["capabilities"].remove(required_owner)
        pair["capability_context"].pop(required_owner)
        with self.assertRaisesRegex(paired_eval.EvaluationError, "unsupplied owner capabilities"):
            paired_eval.validate_config(config)

    def test_schema_1_4_binds_source_kind_to_dataset_role(self) -> None:
        development = legacy_development_config()
        acceptance = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
        )
        development["dataset_role"] = "acceptance"
        acceptance["dataset_role"] = "development"
        with self.assertRaisesRegex(paired_eval.EvaluationError, "source_kind contract.*development"):
            paired_eval.validate_config(development)
        with self.assertRaisesRegex(paired_eval.EvaluationError, "source_kind catalog.*acceptance"):
            paired_eval.validate_config(acceptance)

    def test_release_evaluator_contract_binds_first_party_roles_models_and_receipts(self) -> None:
        config = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
        )
        validated = paired_eval.validate_config(config)
        contract = validated["release_evaluators"]
        adapter = str(ROOT / contract["adapter"])
        executor = [
            PYTHON,
            adapter,
            "executor",
            "--model",
            contract["executor"]["model"],
            "--reasoning-effort",
            contract["executor"]["reasoning_effort"],
        ]
        identity = paired_eval.validate_release_evaluator_command(executor, "executor", contract)
        self.assertEqual(identity["role"], "executor")
        self.assertEqual(identity["model"], "gpt-5.6-terra")
        self.assertEqual(identity["result_schema_version"], "1.3")
        with mock.patch.object(paired_eval.shutil, "which", return_value=None):
            with self.assertRaisesRegex(paired_eval.EvaluationError, "executable is unavailable"):
                paired_eval.resolve_release_backend_identity(contract)
        _, backend = resolve_fake_release_backend(self, contract)
        identity["backend"] = backend
        self.assertEqual(backend["version"], "codex-cli 0.147.0")
        self.assertRegex(backend["sha256"], r"^sha256:[0-9a-f]{64}$")
        bound = paired_eval.bind_release_backend(executor, backend)
        self.assertEqual(bound[-8:], [
            "--codex-executable",
            backend["path"],
            "--codex-platform",
            backend["platform"],
            "--codex-version",
            backend["version"],
            "--codex-sha256",
            backend["sha256"],
        ])

        for mutated in (
            ["external-evaluator"],
            [*executor[:4], "wrong-model", *executor[5:]],
            [*executor, "--unexpected"],
            [*executor[:2], "grader", *executor[3:]],
        ):
            with self.assertRaisesRegex(paired_eval.EvaluationError, "release evaluator"):
                paired_eval.validate_release_evaluator_command(mutated, "executor", contract)

        with tempfile.TemporaryDirectory() as temp:
            run_root = Path(temp)
            receipt = {
                "schema_version": "1.0",
                "role": "executor",
                "model": "gpt-5.6-terra",
                "reasoning_effort": "medium",
                "tokens": 123,
                "token_usage": {"input_tokens": 100, "output_tokens": 23},
                "elapsed_seconds": 1.0,
                "prompt_bytes": 2000,
                "capability_source_bytes": 500,
                "model_output_bytes": 800,
                "monetary_cost": None,
                "cost_basis": "not exposed",
                "codex_exit_code": 0,
                "tool_events": {
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
                "backend": backend,
            }
            receipt_path = run_root / "model-usage.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            validated_receipt = paired_eval.validate_release_model_receipt(run_root, identity)
            self.assertEqual(validated_receipt["model"], "gpt-5.6-terra")
            self.assertRegex(validated_receipt["sha256"], r"^sha256:[0-9a-f]{64}$")
            receipt["tool_events"]["total"] = 1
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "tool events"):
                paired_eval.validate_release_model_receipt(run_root, identity)

        with tempfile.TemporaryDirectory() as temp:
            fake = Path(temp) / "codex"
            fake.write_text("not the approved backend", encoding="utf-8")
            fake.chmod(0o755)
            with mock.patch.object(paired_eval.shutil, "which", return_value=str(fake)):
                with self.assertRaisesRegex(paired_eval.EvaluationError, "backend.*digest"):
                    paired_eval.resolve_release_backend_identity(contract)

    def test_release_mode_rejects_external_evaluator_before_model_execution(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--release",
                "--expected-commit",
                run("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip(),
                "--trials",
                "12",
                "--executor",
                "external-executor",
                "--grader",
                "external-grader",
                "--output",
                str(Path(temp) / "output"),
            )
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        self.assertIn("release evaluator", result.stderr)

    def test_schema_1_8_development_binds_the_inventory_attested_pipeline(self) -> None:
        development = json.loads(
            (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
        )
        validated = paired_eval.validate_config(development)
        identity = validated["evaluator_identity"]
        self.assertEqual(identity["adapter"], "evals/codex_model_adapter.py")
        self.assertEqual(identity["result_schema_version"], "1.3")
        self.assertEqual(identity["receipt_schema_version"], "1.2")
        self.assertEqual(identity["inventory"], {"model": "gpt-5.6-sol", "reasoning_effort": "medium"})
        self.assertEqual(identity["assembler"], {"model": "gpt-5.6-sol", "reasoning_effort": "high"})
        self.assertEqual(identity["grader"], {"model": "gpt-5.6-sol", "reasoning_effort": "medium"})
        self.assertEqual(
            validated["executor_pipeline"],
            {
                "protocol": "blind-inventory-assembler-v2",
                "stage_order": ["inventory", "assembler"],
                "inventory_request_schema_version": "1.0",
                "inventory_result_schema_version": "1.0",
                "assembler_request_schema_version": "2.0",
                "assembler_result_schema_version": "1.0",
                "final_result_schema_version": "1.3",
                "assembly_manifest": "complete-source-partition-v1",
                "materialization": "deterministic-claim-v1",
                "first_attempt_semantics": "single-inventory-no-regeneration-v2",
                "capability_projection": "task-neutral-content-only-v1",
            },
        )
        report_schema = json.loads(
            (ROOT / "evals" / "schemas" / "paired-evaluation-report.json").read_text(
                encoding="utf-8"
            )
        )
        receipt_schema = report_schema["$defs"]["modelReceipt"]
        self.assertIn("sha256", receipt_schema["required"])
        self.assertIn("token_usage", receipt_schema["required"])
        self.assertEqual(
            report_schema["$defs"]["record"]["properties"]["executor_model_receipt"]["oneOf"][1],
            {"$ref": "#/$defs/modelReceipt"},
        )

        ordinary = json.loads(json.dumps(development))
        ordinary.pop("evaluator_identity")
        with self.assertRaisesRegex(paired_eval.EvaluationError, "requires evaluator_identity"):
            paired_eval.validate_config(ordinary)

        acceptance = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
        )
        acceptance["evaluator_identity"] = identity
        with self.assertRaisesRegex(paired_eval.EvaluationError, "evaluator_identity.*development"):
            paired_eval.validate_config(acceptance)

    def test_attested_pilot_requires_a_filtered_development_identity_and_exact_commands(self) -> None:
        development = json.loads(
            (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
        )
        identity = development["evaluator_identity"]
        adapter = str(ROOT / identity["adapter"])
        draft = (
            f"{PYTHON} {adapter} inventory --model {identity['inventory']['model']} "
            f"--reasoning-effort {identity['inventory']['reasoning_effort']}"
        )
        assembler = (
            f"{PYTHON} {adapter} assembler --model {identity['assembler']['model']} "
            f"--reasoning-effort {identity['assembler']['reasoning_effort']}"
        )
        grader = (
            f"{PYTHON} {adapter} grader --model {identity['grader']['model']} "
            f"--reasoning-effort {identity['grader']['reasoning_effort']}"
        )
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            unfiltered = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--attested-pilot",
                "--executor-draft",
                draft,
                "--executor-assembler",
                assembler,
                "--grader",
                grader,
                "--output",
                str(root / "unfiltered"),
            )
            self.assertEqual(unfiltered.returncode, 2, unfiltered.stderr or unfiltered.stdout)
            self.assertIn("filtered development", unfiltered.stderr)

            missing_identity = json.loads(json.dumps(development))
            missing_identity.pop("evaluator_identity")
            missing_config = root / "missing-identity.json"
            missing_config.write_text(json.dumps(missing_identity), encoding="utf-8")
            missing = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--attested-pilot",
                "--config",
                str(missing_config),
                "--pair",
                "PAIR-ECR",
                "--executor-draft",
                draft,
                "--executor-assembler",
                assembler,
                "--grader",
                grader,
                "--output",
                str(root / "missing"),
            )
            self.assertEqual(missing.returncode, 2, missing.stderr or missing.stdout)
            self.assertIn("requires evaluator_identity", missing.stderr)

            external = run(
                PYTHON,
                str(PAIRED_RUNNER),
                "--attested-pilot",
                "--pair",
                "PAIR-ECR",
                "--executor-draft",
                "external-executor",
                "--executor-assembler",
                "external-assembler",
                "--grader",
                "external-grader",
                "--output",
                str(root / "external"),
            )
            self.assertEqual(external.returncode, 2, external.stderr or external.stdout)
            self.assertIn("attested pilot evaluator", external.stderr)

    def test_attested_backend_and_receipt_are_revalidated_for_each_bound_call(self) -> None:
        development = paired_eval.validate_config(legacy_development_config())
        contract = development["evaluator_identity"]
        adapter = str(ROOT / contract["adapter"])
        command = [
            PYTHON,
            adapter,
            "executor",
            "--model",
            contract["executor"]["model"],
            "--reasoning-effort",
            contract["executor"]["reasoning_effort"],
        ]
        evaluator = paired_eval.validate_release_evaluator_command(
            command,
            "executor",
            contract,
            evaluator_label="attested pilot evaluator",
        )
        for index, wrong_value in ((2, "grader"), (4, "gpt-5.6-terra"), (6, "high")):
            wrong_command = list(command)
            wrong_command[index] = wrong_value
            with self.subTest(argument_index=index), self.assertRaisesRegex(
                paired_eval.EvaluationError,
                "role, model, and reasoning effort",
            ):
                paired_eval.validate_release_evaluator_command(
                    wrong_command,
                    "executor",
                    contract,
                    evaluator_label="attested pilot evaluator",
                )
        approved_backend_contract, backend = resolve_fake_release_backend(
            self,
            contract,
            evaluator_label="attested pilot evaluator",
        )
        wrong_backend_contract = json.loads(json.dumps(approved_backend_contract))
        wrong_backend_contract["backend"]["artifacts"][paired_eval.release_platform_key()] = (
            "sha256:" + "0" * 64
        )
        with mock.patch.object(paired_eval.shutil, "which", return_value=backend["path"]):
            with self.assertRaisesRegex(paired_eval.EvaluationError, "backend digest is not approved"):
                paired_eval.resolve_release_backend_identity(
                    wrong_backend_contract,
                    evaluator_label="attested pilot evaluator",
                )
        evaluator["backend"] = backend

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            receipt = {
                "schema_version": "1.0",
                "role": "executor",
                "model": contract["executor"]["model"],
                "reasoning_effort": contract["executor"]["reasoning_effort"],
                "tokens": 12,
                "token_usage": {"input_tokens": 10, "output_tokens": 2},
                "prompt_bytes": 100,
                "capability_source_bytes": 20,
                "model_output_bytes": 30,
                "codex_exit_code": 0,
                "tool_events": {
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
                "backend": backend,
            }
            receipt_path = root / "model-usage.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            summary = paired_eval.validate_release_model_receipt(
                root,
                evaluator,
                evaluator_label="attested pilot evaluator",
            )
            self.assertEqual(summary["tokens"], 12)
            self.assertEqual(summary["token_usage"], receipt["token_usage"])
            self.assertRegex(summary["sha256"], r"^sha256:[0-9a-f]{64}$")

            receipt["tokens"] = None
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "receipt usage"):
                paired_eval.validate_release_model_receipt(
                    root,
                    evaluator,
                    evaluator_label="attested pilot evaluator",
                )

            receipt["tokens"] = 12
            receipt["role"] = "grader"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "role.*approved identity"):
                paired_eval.validate_release_model_receipt(
                    root,
                    evaluator,
                    evaluator_label="attested pilot evaluator",
                )

            receipt["role"] = "executor"
            receipt["tool_events"]["total"] = 1
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "tool events"):
                paired_eval.validate_release_model_receipt(
                    root,
                    evaluator,
                    evaluator_label="attested pilot evaluator",
                )

            receipt_path.unlink()
            with self.assertRaisesRegex(paired_eval.EvaluationError, "receipt is missing"):
                paired_eval.validate_release_model_receipt(
                    root,
                    evaluator,
                    evaluator_label="attested pilot evaluator",
                )

            fake_backend = root / "codex"
            fake_backend.write_bytes(b"approved")
            bound_backend = {
                "command": "codex",
                "path": str(fake_backend),
                "platform": "darwin-arm64",
                "version": "codex-cli test",
                "sha256": "sha256:" + hashlib.sha256(b"approved").hexdigest(),
            }
            paired_eval.validate_evaluator_backend_digest(
                bound_backend,
                evaluator_label="attested pilot evaluator",
            )
            fake_backend.write_bytes(b"changed")
            with self.assertRaisesRegex(paired_eval.EvaluationError, "backend digest changed"):
                paired_eval.validate_evaluator_backend_digest(
                    bound_backend,
                    evaluator_label="attested pilot evaluator",
                )

    def test_bound_program_rechecks_backend_immediately_before_every_call(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fake_backend = root / "codex"
            fake_backend.write_bytes(b"approved")
            backend = {
                "command": "codex",
                "path": str(fake_backend),
                "platform": "darwin-arm64",
                "version": "codex-cli test",
                "sha256": "sha256:" + hashlib.sha256(b"approved").hexdigest(),
            }
            command = [
                PYTHON,
                "-c",
                "import json; print(json.dumps({'ok': True}))",
            ]
            first, first_attempts = paired_eval.run_bound_program_with_infrastructure_retry(
                command,
                {"request": 1},
                root / "first",
                2,
                0,
                backend_identity=backend,
                evaluator_label="attested pilot evaluator",
            )
            self.assertIsNone(first.error)
            self.assertEqual(len(first_attempts), 1)

            fake_backend.write_bytes(b"changed")
            second, second_attempts = paired_eval.run_bound_program_with_infrastructure_retry(
                command,
                {"request": 2},
                root / "second",
                2,
                1,
                backend_identity=backend,
                evaluator_label="attested pilot evaluator",
            )
            self.assertEqual(second.error_kind, "identity")
            self.assertIn("backend digest changed", second.error or "")
            self.assertEqual(len(second_attempts), 1)
            self.assertFalse(second_attempts[0]["retry_scheduled"])

    def test_executor_request_does_not_disclose_gold_paths_or_condition(self) -> None:
        request = paired_eval.executor_request(
            pair_id="PAIR-ACC-CONTEXT-WORKTREE",
            trial=1,
            variant="candidate",
            pair_capabilities=["repo-context"],
            input_value={
                "fixture": "bounded fixture only",
                "capability_sources": {"repo-context": "bounded source"},
                "claim_owner_vocabulary": ["repo-context"],
                "claim_kind_vocabulary": [
                    {"id": "repo-context.analysis", "owner": "repo-context"}
                ],
                "contract": {"prompt": "analyze the fixture", "obligations": []},
            },
        )
        self.assertNotIn("fixture_path", request)
        self.assertNotIn("condition", request)
        self.assertNotIn("case_source", request)
        self.assertNotIn("obligations", json.dumps(request))
        self.assertEqual(request["fixture"], "bounded fixture only")

    def test_development_and_acceptance_configs_are_disjoint_and_broad(self) -> None:
        development = paired_eval.validate_config(
            json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        )
        acceptance = paired_eval.validate_config(
            json.loads(
                (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
            )
        )
        self.assertEqual(development["dataset_role"], "development")
        self.assertEqual(acceptance["dataset_role"], "acceptance")
        self.assertEqual(paired_eval.DEVELOPMENT_CONFIG.name, "paired-evaluations.json")
        self.assertEqual(paired_eval.CANONICAL_CONFIG.name, "paired-evaluations-acceptance.json")

        def category_counts(config: dict[str, object]) -> dict[str, int]:
            counts: dict[str, int] = {}
            for pair in config["pairs"]:  # type: ignore[index]
                category = pair["category"]  # type: ignore[index]
                counts[category] = counts.get(category, 0) + 1
            return counts

        development_counts = category_counts(development)
        acceptance_counts = category_counts(acceptance)
        self.assertEqual((len(development["pairs"]), len(development_counts)), (39, 12))
        self.assertEqual(development_counts["CAT-REQUIREMENTS"], 6)
        self.assertEqual(
            {count for category, count in development_counts.items() if category != "CAT-REQUIREMENTS"},
            {3},
        )
        self.assertEqual((len(acceptance["pairs"]), len(acceptance_counts)), (56, 16))
        self.assertEqual(set(acceptance_counts.values()), {3, 5})
        combined = {
            category: development_counts.get(category, 0) + acceptance_counts.get(category, 0)
            for category in development_counts.keys() | acceptance_counts.keys()
        }
        self.assertGreaterEqual(min(combined.values()), 5)
        self.assertEqual(len(combined), 16)
        self.assertTrue(
            {
                "CAT-ARCHITECTURE",
                "CAT-SECURITY-PRIVACY",
                "CAT-PERFORMANCE-RESOURCES",
                "CAT-CONCURRENCY-RECOVERY",
            }.issubset(combined)
        )
        self.assertTrue(
            {pair["id"] for pair in development["pairs"]}.isdisjoint(
                pair["id"] for pair in acceptance["pairs"]
            )
        )
        self.assertEqual(
            acceptance["release_plan"]["category_ids"],
            list(acceptance_counts),
        )
        self.assertEqual(development["release_plan"]["trials_per_pair"], 5)
        self.assertEqual(acceptance["release_plan"]["trials_per_pair"], 12)

        requirement_pairs = [
            pair for pair in development["pairs"] if pair["category"] == "CAT-REQUIREMENTS"
        ]
        self.assertEqual(
            {pair["id"] for pair in requirement_pairs},
            {
                "PAIR-ROUTING",
                "PAIR-REQ-DESIGN-CONTRADICTION",
                "PAIR-REQ-MISSING-STATES",
                "PAIR-REQ-AVOIDABLE-QUESTION",
                "PAIR-REQ-SPARSE-BUG",
                "PAIR-REQ-MATERIAL-DEFAULT",
            },
        )
        self.assertEqual(len({pair["fixture"] for pair in requirement_pairs}), 6)
        self.assertEqual(len({pair["contract"] for pair in requirement_pairs}), 6)

    def test_contract_criticality_separates_safety_from_required_completeness(self) -> None:
        development = json.loads(
            (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
        )
        acceptance = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(
                encoding="utf-8"
            )
        )
        counts = {"critical": 0, "required": 0, "supporting": 0}
        task_levels: list[tuple[str, set[str]]] = []
        for pair in development["pairs"]:
            contract = json.loads(
                (ROOT / "evals" / pair["contract"]).read_text(encoding="utf-8")
            )
            levels = {unit["criticality"] for unit in contract["work_units"]}
            task_levels.append((pair["category"], levels))
            for unit in contract["work_units"]:
                counts[unit["criticality"]] += 1
        catalogs: dict[str, dict[str, object]] = {}
        for pair in acceptance["pairs"]:
            catalog = catalogs.setdefault(
                pair["case_source"],
                json.loads(
                    (ROOT / "evals" / pair["case_source"]).read_text(encoding="utf-8")
                ),
            )
            case = next(item for item in catalog["cases"] if item["id"] == pair["case_id"])
            levels = {unit["criticality"] for unit in case["work_units"]}
            task_levels.append((pair["category"], levels))
            for unit in case["work_units"]:
                counts[unit["criticality"]] += 1

        self.assertEqual(counts, {"critical": 134, "required": 330, "supporting": 6})
        self.assertLess(counts["critical"] / sum(counts.values()), 0.3)
        self.assertTrue(all(levels & {"critical", "required"} for _, levels in task_levels))
        self.assertTrue(
            all(
                "critical" in levels
                for category, levels in task_levels
                if category
                in {
                    "CAT-CONCURRENCY-RECOVERY",
                    "CAT-DELIVERY",
                    "CAT-DEPENDENCY",
                    "CAT-FFI",
                    "CAT-INTERACTION",
                    "CAT-MIGRATION",
                    "CAT-REVIEW",
                    "CAT-SECURITY-PRIVACY",
                }
            )
        )

    def test_schema_1_2_rejects_contract_mismatch_and_underpopulated_category(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        mismatched = json.loads(json.dumps(config))
        mismatched["pairs"][0]["contract"] = mismatched["pairs"][1]["contract"]
        with self.assertRaisesRegex(paired_eval.EvaluationError, "contract fixture mismatch|must match"):
            paired_eval.validate_config(mismatched)

        underpopulated = json.loads(json.dumps(config))
        removed = underpopulated["pairs"].pop(0)
        underpopulated["release_plan"]["pair_ids"].remove(removed["id"])
        with self.assertRaisesRegex(paired_eval.EvaluationError, "underpopulated"):
            paired_eval.validate_config(underpopulated)

    def test_diagnostic_grader_requires_each_owner_bound_obligation_once_in_order(self) -> None:
        obligations = [
            {
                "id": "OB-ROUTE",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "criticality": "critical",
                "action": "route the boundary design",
                "evidence_kind": "decision",
            },
            {
                "id": "OB-VERIFY",
                "owner": "verification",
                "kind": "verification.test",
                "criticality": "supporting",
                "action": "verify the boundary",
                "evidence_kind": "test",
            },
        ]
        claims = [
            {
                "claim_id": "CL-ROUTE",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.decision",
                "action": "route specialists",
                "protected_behavior": "boundary safety",
                "oracle_or_evidence": "ordered route",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-VERIFY",
                "owner": "verification",
                "kind": "verification.test",
                "action": "run boundary checks",
                "protected_behavior": "boundary compatibility",
                "oracle_or_evidence": "test matrix",
                "status": "not-run",
                "limitation": "physical environment unavailable",
            },
        ]
        result = {
            "schema_version": "1.3",
            "case_id": "PAIR-1",
            "graded_attempt": 1,
            "requirement_fidelity": 4,
            "scope_discipline": 4,
            "evidence_quality": 4,
            "forbidden_actions": [],
            "structural_coverage": ["bounded"],
            "obligation_assessments": [
                {
                    "obligation_id": "OB-ROUTE",
                    "status": "covered",
                    "evidence": "first claim",
                    "claim_ids": ["CL-ROUTE"],
                },
                {
                    "obligation_id": "OB-VERIFY",
                    "status": "partial",
                    "evidence": "verification is planned but not run",
                    "claim_ids": ["CL-VERIFY"],
                },
            ],
            "metrics": {
                "coverage": 3,
                "restraint": 4,
                "ordinary_defect_retention": 4,
                "actionability": 4,
                "rework": 1,
                "unsafe_actions": 0,
                "false_blocks": 0,
            },
            "verdict": "pass",
        }
        normalized = paired_eval.validate_grader(
            json.loads(json.dumps(result)),
            "PAIR-1",
            obligations,
            claims,
        )
        self.assertEqual(normalized["obligation_assessments"][1]["status"], "partial")
        self.assertEqual(normalized["verdict"], "pass")

        wrong_order = json.loads(json.dumps(result))
        wrong_order["obligation_assessments"].reverse()
        with self.assertRaisesRegex(paired_eval.EvaluationError, "every obligation exactly once in order"):
            paired_eval.validate_grader(wrong_order, "PAIR-1", obligations, claims)

        nonexistent = json.loads(json.dumps(result))
        nonexistent["obligation_assessments"][0]["claim_ids"] = ["CL-NOT-FOUND"]
        with self.assertRaisesRegex(paired_eval.EvaluationError, "unknown executor claim"):
            paired_eval.validate_grader(nonexistent, "PAIR-1", obligations, claims)

        missing_claim = json.loads(json.dumps(result))
        missing_claim["obligation_assessments"][0]["claim_ids"] = []
        with self.assertRaisesRegex(paired_eval.EvaluationError, "covered or partial.*claim"):
            paired_eval.validate_grader(missing_claim, "PAIR-1", obligations, claims)

        wrong_version = json.loads(json.dumps(result))
        wrong_version["schema_version"] = "1.0"
        with self.assertRaisesRegex(paired_eval.EvaluationError, "schema_version"):
            paired_eval.validate_grader(wrong_version, "PAIR-1", obligations, claims)

    def test_legacy_diagnostic_grader_shape_remains_strict(self) -> None:
        result = {
            "schema_version": "1.3",
            "case_id": "PAIR-LEGACY",
            "graded_attempt": 1,
            "requirement_fidelity": 3,
            "scope_discipline": 3,
            "evidence_quality": 3,
            "forbidden_actions": [],
            "structural_coverage": ["legacy expected actions"],
            "obligation_assessments": [
                {"index": 1, "status": "covered", "evidence": "first action"},
                {"index": 2, "status": "partial", "evidence": "second action"},
            ],
            "metrics": {
                "coverage": 3,
                "restraint": 3,
                "ordinary_defect_retention": 3,
                "actionability": 3,
                "rework": 2,
                "unsafe_actions": 0,
                "false_blocks": 0,
            },
            "verdict": "pass",
        }
        normalized = paired_eval.validate_grader(
            json.loads(json.dumps(result)),
            "PAIR-LEGACY",
            2,
            [],
        )
        self.assertEqual(normalized["verdict"], "pass")

        wrong_shape = json.loads(json.dumps(result))
        wrong_shape["obligation_assessments"][0] = {
            "obligation_id": "OB-1",
            "status": "covered",
            "evidence": "wrong protocol",
            "claim_ids": ["CL-1"],
        }
        with self.assertRaisesRegex(paired_eval.EvaluationError, "key mismatch"):
            paired_eval.validate_grader(wrong_shape, "PAIR-LEGACY", 2, [])

    def test_work_unit_facets_allow_distinct_support_but_reject_reuse_overlap_and_gaps(self) -> None:
        work_units = [
            {
                "id": "WU-1",
                "owner": "repo-context",
                "claim_routes": [{"kind": "repo-context.analysis"}],
                "criticality": "critical",
                "protected_behavior": "boundary discovery remains complete",
                "facets": [
                    {"id": "OB-1", "action": "inventory Rust exports"},
                    {"id": "OB-2", "action": "inventory generated Swift bindings"},
                ],
            },
            {
                "id": "WU-2",
                "owner": "repo-context",
                "claim_routes": [{"kind": "repo-context.analysis"}],
                "criticality": "critical",
                "protected_behavior": "deployed variants remain known",
                "facets": [
                    {"id": "OB-3", "action": "inventory deployed versions"},
                ],
            },
        ]
        claims = [
            {
                "claim_id": "CL-INVENTORY",
                "owner": "repo-context",
                "kind": "repo-context.analysis",
                "action": "Inventory Rust exports and generated Swift bindings before design.",
                "protected_behavior": "Existing consumers remain discoverable.",
                "oracle_or_evidence": "A repository trace records each inventory path.",
                "status": "planned",
                "limitation": "Repository bytes are unavailable in this fixture.",
            },
            {
                "claim_id": "CL-VERSIONS",
                "owner": "repo-context",
                "kind": "repo-context.analysis",
                "action": "Inventory deployed versions before design.",
                "protected_behavior": "Deployed consumers remain compatible.",
                "oracle_or_evidence": "A version inventory records supported deployments.",
                "status": "planned",
                "limitation": "Deployment records are unavailable in this fixture.",
            },
        ]
        base = {
            "schema_version": "1.3",
            "case_id": "PAIR-WORK-UNITS",
            "graded_attempt": 1,
            "requirement_fidelity": 4,
            "scope_discipline": 4,
            "evidence_quality": 4,
            "forbidden_actions": [],
            "structural_coverage": ["work-unit facets"],
            "work_unit_assessments": [
                {
                    "work_unit_id": "WU-1",
                    "facet_assessments": [
                        {
                            "facet_id": "OB-1",
                            "status": "covered",
                            "evidence": "Rust export inventory is explicit.",
                            "support_refs": [{"claim_id": "CL-INVENTORY", "field": "action", "quote": "Rust exports"}],
                        },
                        {
                            "facet_id": "OB-2",
                            "status": "covered",
                            "evidence": "Generated Swift binding inventory is explicit.",
                            "support_refs": [{"claim_id": "CL-INVENTORY", "field": "action", "quote": "generated Swift bindings"}],
                        },
                    ],
                },
                {
                    "work_unit_id": "WU-2",
                    "facet_assessments": [
                        {
                            "facet_id": "OB-3",
                            "status": "covered",
                            "evidence": "Deployment versions are explicit.",
                            "support_refs": [{"claim_id": "CL-VERSIONS", "field": "action", "quote": "deployed versions"}],
                        }
                    ],
                },
            ],
            "metrics": {
                "coverage": 4,
                "restraint": 4,
                "ordinary_defect_retention": 4,
                "actionability": 4,
                "rework": 0,
                "unsafe_actions": 0,
                "false_blocks": 0,
            },
            "verdict": "pass",
        }
        normalized = paired_eval.validate_grader(
            json.loads(json.dumps(base)),
            "PAIR-WORK-UNITS",
            work_units,
            claims,
        )
        self.assertEqual(normalized["verdict"], "pass")
        self.assertEqual(
            [item["status"] for item in normalized["obligation_assessments"]],
            ["covered", "covered"],
        )
        self.assertTrue(normalized["policy_verdict_checks"]["critical_support_exclusive"])

        overlap = json.loads(json.dumps(base))
        for facet in overlap["work_unit_assessments"][0]["facet_assessments"]:
            facet["support_refs"][0]["quote"] = claims[0]["action"]
        rejected = paired_eval.validate_grader(
            overlap, "PAIR-WORK-UNITS", work_units, claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_support_exclusive"])

        reused = json.loads(json.dumps(base))
        reused["work_unit_assessments"][1]["facet_assessments"][0]["support_refs"] = [
            {"claim_id": "CL-INVENTORY", "field": "action", "quote": "before design"}
        ]
        rejected = paired_eval.validate_grader(
            reused, "PAIR-WORK-UNITS", work_units, claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_claim_exclusive"])

        missing = json.loads(json.dumps(base))
        facet = missing["work_unit_assessments"][0]["facet_assessments"][1]
        facet["status"] = "missing"
        facet["support_refs"] = []
        rejected = paired_eval.validate_grader(
            missing, "PAIR-WORK-UNITS", work_units, claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_work_units_covered"])

        required_units = json.loads(json.dumps(work_units))
        required_units[0]["criticality"] = "required"
        required_missing = json.loads(json.dumps(base))
        required_facet = required_missing["work_unit_assessments"][0]["facet_assessments"][1]
        required_facet["status"] = "missing"
        required_facet["support_refs"] = []
        required_rejected = paired_eval.validate_grader(
            required_missing, "PAIR-WORK-UNITS", required_units, claims
        )
        self.assertTrue(
            required_rejected["policy_verdict_checks"]["critical_work_units_covered"]
        )
        self.assertFalse(
            required_rejected["policy_verdict_checks"]["required_work_units_covered"]
        )
        self.assertEqual(required_rejected["verdict"], "fail")

        absent = json.loads(json.dumps(base))
        absent["work_unit_assessments"][0]["facet_assessments"][0]["support_refs"][0]["quote"] = "missing support phrase"
        with self.assertRaisesRegex(paired_eval.EvaluationError, "occur exactly once"):
            paired_eval.validate_grader(absent, "PAIR-WORK-UNITS", work_units, claims)

        word_cut = json.loads(json.dumps(base))
        word_cut["work_unit_assessments"][0]["facet_assessments"][0]["support_refs"][0][
            "quote"
        ] = "Rust expo"
        with self.assertRaisesRegex(paired_eval.EvaluationError, "must not cut through a word"):
            paired_eval.validate_grader(word_cut, "PAIR-WORK-UNITS", work_units, claims)

        duplicate_support = json.loads(json.dumps(base))
        duplicate_claims = json.loads(json.dumps(claims))
        duplicate_claims[0]["action"] = "Shared support phrase alpha."
        duplicate_claims[0]["protected_behavior"] = "Shared support phrase alpha."
        duplicate_support["work_unit_assessments"][0]["facet_assessments"][0][
            "support_refs"
        ] = [
            {
                "claim_id": "CL-INVENTORY",
                "field": "action",
                "quote": "Shared support phrase alpha",
            }
        ]
        duplicate_support["work_unit_assessments"][0]["facet_assessments"][1][
            "support_refs"
        ] = [
            {
                "claim_id": "CL-INVENTORY",
                "field": "protected_behavior",
                "quote": "Shared support phrase alpha",
            }
        ]
        rejected = paired_eval.validate_grader(
            duplicate_support, "PAIR-WORK-UNITS", work_units, duplicate_claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_support_exclusive"])

        punctuation_clone = json.loads(json.dumps(base))
        cloned_claims = json.loads(json.dumps(claims))
        cloned_claims[1] = {
            **cloned_claims[0],
            "claim_id": "CL-VERSIONS",
            "action": cloned_claims[0]["action"].removesuffix(".") + "!",
        }
        punctuation_clone["work_unit_assessments"][1]["facet_assessments"][0][
            "support_refs"
        ] = [
            {
                "claim_id": "CL-VERSIONS",
                "field": "action",
                "quote": "generated Swift bindings",
            }
        ]
        rejected = paired_eval.validate_grader(
            punctuation_clone, "PAIR-WORK-UNITS", work_units, cloned_claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_claim_exclusive"])
        self.assertFalse(rejected["policy_verdict_checks"]["critical_support_exclusive"])

        non_support_drift = json.loads(json.dumps(base))
        drifted_claims = json.loads(json.dumps(claims))
        drifted_claims[1] = {
            **drifted_claims[0],
            "claim_id": "CL-VERSIONS",
            "limitation": "Different presentation-only limitation text.",
        }
        non_support_drift["work_unit_assessments"][1]["facet_assessments"][0][
            "support_refs"
        ] = [
            {
                "claim_id": "CL-VERSIONS",
                "field": "action",
                "quote": "generated Swift bindings",
            }
        ]
        rejected = paired_eval.validate_grader(
            non_support_drift, "PAIR-WORK-UNITS", work_units, drifted_claims
        )
        self.assertFalse(rejected["policy_verdict_checks"]["critical_support_exclusive"])

    def test_support_reference_canonicalizes_only_a_unique_wrong_field_match(self) -> None:
        claim = {
            "claim_id": "CL-SUPPORT",
            "owner": "verification",
            "kind": "verification.test",
            "action": "Run the bounded verification cell.",
            "protected_behavior": "Swift and Kotlin bindings remain compatible.",
            "oracle_or_evidence": "Record the independent result.",
            "status": "planned",
            "limitation": "Repository execution is unavailable.",
        }
        reference = {
            "claim_id": "CL-SUPPORT",
            "field": "oracle_or_evidence",
            "quote": "Swift and Kotlin bindings remain compatible",
        }
        resolved = paired_eval.resolve_support_reference(
            reference,
            {claim["claim_id"]: claim},
            "support",
        )
        self.assertEqual(resolved["field"], "protected_behavior")
        self.assertEqual(
            claim["protected_behavior"][resolved["start"]:resolved["end"]],
            reference["quote"],
        )

        ambiguous_fields = json.loads(json.dumps(claim))
        ambiguous_fields["action"] = reference["quote"] + "."
        with self.assertRaisesRegex(paired_eval.EvaluationError, "occur exactly once"):
            paired_eval.resolve_support_reference(
                reference,
                {claim["claim_id"]: ambiguous_fields},
                "support",
            )

        repeated_in_one_field = json.loads(json.dumps(claim))
        repeated_in_one_field["protected_behavior"] = (
            reference["quote"] + "; " + reference["quote"] + "."
        )
        with self.assertRaisesRegex(paired_eval.EvaluationError, "occur exactly once"):
            paired_eval.resolve_support_reference(
                reference,
                {claim["claim_id"]: repeated_in_one_field},
                "support",
            )

        absent = {**reference, "quote": "No matching support phrase exists"}
        with self.assertRaisesRegex(paired_eval.EvaluationError, "occur exactly once"):
            paired_eval.resolve_support_reference(
                absent,
                {claim["claim_id"]: claim},
                "support",
            )

    def test_policy_verdict_closes_critical_partial_reuse_and_owner_gaps(self) -> None:
        obligations = [
            {
                "id": "OB-C1",
                "owner": "verification",
                "kind": "verification.test",
                "criticality": "critical",
                "action": "verify admission",
                "evidence_kind": "test",
            },
            {
                "id": "OB-C2",
                "owner": "verification",
                "kind": "verification.test",
                "criticality": "critical",
                "action": "verify shutdown",
                "evidence_kind": "test",
            },
            {
                "id": "OB-C3",
                "owner": "verification",
                "kind": "verification.test",
                "criticality": "critical",
                "action": "verify recovery",
                "evidence_kind": "test",
            },
            {
                "id": "OB-S1",
                "owner": "change-review",
                "kind": "change-review.analysis",
                "criticality": "supporting",
                "action": "review the result",
                "evidence_kind": "analysis",
            },
        ]
        claims = [
            {
                "claim_id": "CL-C1",
                "owner": "verification",
                "kind": "verification.test",
                "action": "test admission",
                "protected_behavior": "exclusive admission",
                "oracle_or_evidence": "native test",
                "status": "verified",
                "limitation": None,
            },
            {
                "claim_id": "CL-C2",
                "owner": "verification",
                "kind": "verification.test",
                "action": "test shutdown",
                "protected_behavior": "owned drain",
                "oracle_or_evidence": "native test",
                "status": "verified",
                "limitation": None,
            },
            {
                "claim_id": "CL-C3",
                "owner": "verification",
                "kind": "verification.test",
                "action": "test recovery",
                "protected_behavior": "owned recovery",
                "oracle_or_evidence": "native test",
                "status": "verified",
                "limitation": None,
            },
            {
                "claim_id": "CL-S1",
                "owner": "change-review",
                "kind": "change-review.analysis",
                "action": "review",
                "protected_behavior": "independent review",
                "oracle_or_evidence": "finding ledger",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-WRONG-OWNER",
                "owner": "architecture-decisions",
                "kind": "architecture-decisions.test",
                "action": "choose a boundary",
                "protected_behavior": "boundary ownership",
                "oracle_or_evidence": "decision record",
                "status": "planned",
                "limitation": None,
            },
            {
                "claim_id": "CL-WRONG-KIND",
                "owner": "verification",
                "kind": "verification.analysis",
                "action": "test a different security property",
                "protected_behavior": "negative security behavior",
                "oracle_or_evidence": "negative test",
                "status": "verified",
                "limitation": None,
            },
        ]
        base = {
            "schema_version": "1.3",
            "case_id": "PAIR-1",
            "graded_attempt": 1,
            "requirement_fidelity": 3,
            "scope_discipline": 3,
            "evidence_quality": 1,
            "forbidden_actions": [],
            "structural_coverage": ["bounded"],
            "obligation_assessments": [
                {"obligation_id": "OB-C1", "status": "covered", "evidence": "claim one", "claim_ids": ["CL-C1"]},
                {"obligation_id": "OB-C2", "status": "covered", "evidence": "claim two", "claim_ids": ["CL-C2"]},
                {"obligation_id": "OB-C3", "status": "covered", "evidence": "claim three", "claim_ids": ["CL-C3"]},
                {"obligation_id": "OB-S1", "status": "partial", "evidence": "review planned", "claim_ids": ["CL-S1"]},
            ],
            "metrics": {
                "coverage": 3,
                "restraint": 3,
                "ordinary_defect_retention": 3,
                "actionability": 3,
                "rework": 2,
                "unsafe_actions": 0,
                "false_blocks": 0,
            },
            "verdict": "fail",
        }
        normalized = paired_eval.validate_grader(
            json.loads(json.dumps(base)), "PAIR-1", obligations, claims
        )
        self.assertEqual(normalized["model_verdict"], "fail")
        self.assertEqual(normalized["verdict"], "pass")
        self.assertTrue(all(normalized["policy_verdict_checks"].values()))

        cases = {
            "critical_obligations_covered": lambda value: value["obligation_assessments"][0].__setitem__("status", "partial"),
            "critical_claim_exclusive": lambda value: value["obligation_assessments"][1].__setitem__(
                "claim_ids", ["CL-C1"]
            ),
            "claim_owner_alignment": lambda value: value["obligation_assessments"][0].__setitem__("claim_ids", ["CL-WRONG-OWNER"]),
            "claim_kind_alignment": lambda value: value["obligation_assessments"][0].__setitem__(
                "claim_ids", ["CL-WRONG-KIND"]
            ),
            "supporting_obligations_present": lambda value: (
                value["obligation_assessments"][3].__setitem__("status", "missing"),
                value["obligation_assessments"][3].__setitem__("claim_ids", []),
            ),
        }
        for failed_check, mutate in cases.items():
            with self.subTest(check=failed_check):
                value = json.loads(json.dumps(base))
                mutate(value)
                result = paired_eval.validate_grader(value, "PAIR-1", obligations, claims)
                self.assertEqual(result["verdict"], "fail")
                self.assertFalse(result["policy_verdict_checks"][failed_check])

        hard_floor_mutations = {
            "requirement_fidelity_floor": lambda value: value.__setitem__("requirement_fidelity", 2),
            "scope_discipline_floor": lambda value: value.__setitem__("scope_discipline", 2),
            "evidence_present": lambda value: value.__setitem__("evidence_quality", 0),
            "structural_coverage_present": lambda value: value.__setitem__("structural_coverage", []),
            "coverage_floor": lambda value: value["metrics"].__setitem__("coverage", 2),
            "restraint_floor": lambda value: value["metrics"].__setitem__("restraint", 2),
            "ordinary_defect_retention_floor": lambda value: value["metrics"].__setitem__("ordinary_defect_retention", 2),
            "actionability_floor": lambda value: value["metrics"].__setitem__("actionability", 2),
            "rework_ceiling": lambda value: value["metrics"].__setitem__("rework", 3),
            "no_unsafe_actions": lambda value: value["metrics"].__setitem__("unsafe_actions", 1),
            "no_false_blocks": lambda value: value["metrics"].__setitem__("false_blocks", 1),
            "no_forbidden_actions": lambda value: value.__setitem__("forbidden_actions", ["unsupported claim"]),
        }
        for expected_failed_check, mutate in hard_floor_mutations.items():
            with self.subTest(check=expected_failed_check):
                value = json.loads(json.dumps(base))
                mutate(value)
                normalized = paired_eval.validate_grader(value, "PAIR-1", obligations, claims)
                self.assertEqual(normalized["verdict"], "fail")
                self.assertFalse(normalized["policy_verdict_checks"][expected_failed_check])

    def test_category_regression_blocks_an_otherwise_perfect_pilot(self) -> None:
        def records(variant: str, fidelity: int) -> list[dict[str, object]]:
            return [
                {
                    "variant": variant,
                    "executor": {
                        "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
                        "usage": {"tokens": 10, "elapsed_seconds": 1.0, "cost": None},
                    },
                    "grader": {
                        "requirement_fidelity": fidelity,
                        "scope_discipline": 4,
                        "evidence_quality": 4,
                        "metrics": {
                            "coverage": 4,
                            "restraint": 4,
                            "ordinary_defect_retention": 4,
                            "actionability": 4,
                            "rework": 0,
                            "unsafe_actions": 0,
                            "false_blocks": 0,
                        },
                        "verdict": "pass",
                    },
                }
                for _ in range(3)
            ]

        baseline = paired_eval.aggregate(records("baseline", 4), "baseline")
        perfect_candidate = paired_eval.aggregate(records("candidate", 4), "candidate")
        regressed_candidate = paired_eval.aggregate(records("candidate", 3), "candidate")
        thresholds = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))["release_thresholds"]
        plan = {"mode": "pilot", "evaluated_category_ids": ["CAT-FFI"]}
        assessment = paired_eval.assess_release(
            perfect_candidate,
            baseline,
            thresholds,
            plan,
            {"CAT-FFI": {"baseline": baseline, "candidate": regressed_candidate}},
        )
        self.assertFalse(assessment["pilot_thresholds_passed"])
        self.assertEqual(
            next(gate for gate in assessment["gates"] if gate["gate"] == "category-quality:CAT-FFI")["status"],
            "failed",
        )

    def test_legacy_config_without_release_thresholds_uses_safe_defaults(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config.pop("release_thresholds")
        validated = paired_eval.validate_config(config)
        self.assertEqual(validated["release_thresholds"], paired_eval.DEFAULT_RELEASE_THRESHOLDS)

    def test_schema_1_config_without_release_plan_remains_a_valid_pilot(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config["schema_version"] = "1.0"
        config.pop("case_contract")
        config.pop("dataset_role")
        config.pop("evaluator_identity")
        config.pop("executor_pipeline")
        config.pop("release_plan")
        config["pairs"] = [
            {
                key: value
                for key, value in pair.items()
                if key not in {"category", "contract", "capability_context"}
            }
            for pair in config["pairs"]
        ]
        validated = paired_eval.validate_config(config)
        self.assertNotIn("release_plan", validated)

    def test_schema_1_4_snapshots_only_explicit_capability_references(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        for pair in config["pairs"]:
            pair["capability_context"] = {capability: [] for capability in pair["capabilities"]}
        validated = paired_eval.validate_config(config)

        inputs, snapshot = paired_eval.evaluation_input_snapshot(validated, None)
        first = validated["pairs"][0]
        first_sources = inputs[first["id"]]["capability_sources"]
        self.assertTrue(all(source.count("<source path=") == 1 for source in first_sources.values()))
        self.assertFalse(any("/references/" in entry["path"] for entry in snapshot["entries"]))

        first_capability = first["capabilities"][0]
        first["capability_context"][first_capability] = ["references/context-readiness.md"]
        selected = paired_eval.validate_config(validated)
        selected_inputs, selected_snapshot = paired_eval.evaluation_input_snapshot(selected, None)
        selected_path = f"skills/{first_capability}/references/context-readiness.md"
        self.assertIn(selected_path, selected_inputs[first["id"]]["capability_sources"][first_capability])
        self.assertIn(selected_path, {entry["path"] for entry in selected_snapshot["entries"]})

    def test_schema_1_3_rejects_oversized_combined_pair_input(self) -> None:
        config = paired_eval.validate_config(
            json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        )
        with mock.patch.object(paired_eval, "MAX_PAIR_INPUT_BYTES", 1):
            with self.assertRaisesRegex(paired_eval.EvaluationError, "combined input exceeds"):
                paired_eval.evaluation_input_snapshot(config, None)

    def test_schema_1_4_rejects_cross_capability_reference_ownership(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        for pair in config["pairs"]:
            pair["capability_context"] = {capability: [] for capability in pair["capabilities"]}
        first = config["pairs"][0]
        first["capability_context"][first["capabilities"][0]] = [
            "../requirements-design/references/semantic-and-scope.md"
        ]
        with self.assertRaisesRegex(paired_eval.EvaluationError, "owned|capability|contained|unsafe"):
            paired_eval.validate_config(config)

    def test_schema_1_3_rejects_non_object_pair_with_controlled_error(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        config["pairs"][0] = None
        with self.assertRaisesRegex(paired_eval.EvaluationError, r"pairs\[0\] must be an object"):
            paired_eval.validate_config(config)

    def test_schema_1_3_catalog_rejects_unsafe_case_identity_and_non_catalog_source(self) -> None:
        case = {
            "id": "../unsafe",
            "profile": "bounded",
            "prompt": "analyze",
            "fixture": "bounded fixture",
            "expected_actions": ["inspect"],
            "forbidden_actions": ["invent"],
            "required_artifacts": ["evidence.md"],
        }
        with self.assertRaisesRegex(paired_eval.EvaluationError, "safe"):
            paired_eval.validate_catalog_case(case, "catalog case")

        config = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
        )
        config["pairs"][0]["case_source"] = "paired-evaluations-acceptance.json"
        with self.assertRaisesRegex(paired_eval.EvaluationError, "cases/"):
            paired_eval.validate_config(config)

    def test_schema_1_3_catalog_cases_are_selected_and_snapshotted_once(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "evals" / "cases").mkdir(parents=True)
            (root / "skills" / "repo-context").mkdir(parents=True)
            (root / "skills" / "repo-context" / "SKILL.md").write_text(
                "---\nname: repo-context\ndescription: bounded\n---\n# Repo context\n",
                encoding="utf-8",
            )
            cases = []
            for index in range(1, 4):
                cases.append(
                    {
                        "id": f"CASE-CATALOG-{index}",
                        "profile": f"catalog case {index}",
                        "prompt": f"Handle catalog scenario {index}.",
                        "fixture": f"Scenario {index} has a distinct observable constraint.",
                        "expected_actions": ["inspect the bounded scenario"],
                        "forbidden_actions": ["invent repository evidence"],
                        "required_artifacts": ["evidence.md"],
                    }
                )
            catalog = root / "evals" / "cases" / "sample.json"
            catalog.write_text(
                json.dumps({"schema_version": "1.0", "cases": cases}),
                encoding="utf-8",
            )
            pairs = [
                {
                    "id": f"PAIR-CATALOG-{index}",
                    "category": "CAT-CATALOG",
                    "case_source": "cases/sample.json",
                    "case_id": f"CASE-CATALOG-{index}",
                    "capabilities": ["repo-context"],
                    "capability_context": {"repo-context": []},
                    "deterministic_oracle": "distinct catalog scenario contract",
                }
                for index in range(1, 4)
            ]
            config = {
                "schema_version": "1.3",
                "dataset_role": "development",
                "evaluation_contract": "bounded catalog",
                "default_trials": 3,
                "release_plan": {
                    "pair_ids": [pair["id"] for pair in pairs],
                    "category_ids": ["CAT-CATALOG"],
                    "minimum_cases_per_category": 3,
                    "trials_per_pair": 3,
                },
                "metrics": list(paired_eval.CONTRACT_METRICS),
                "pairs": pairs,
            }
            with mock.patch.object(paired_eval, "ROOT", root):
                validated = paired_eval.validate_config(config)
                inputs, snapshot = paired_eval.evaluation_input_snapshot(validated, None)
            self.assertEqual(inputs["PAIR-CATALOG-2"]["fixture"], cases[1]["fixture"])
            self.assertEqual(inputs["PAIR-CATALOG-2"]["contract"]["id"], "CASE-CATALOG-2")
            self.assertEqual(
                [entry["path"] for entry in snapshot["entries"]].count("evals/cases/sample.json"),
                1,
            )

    def test_release_input_snapshot_reads_immutable_commit_blobs(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        head = run("git", "rev-parse", "HEAD", cwd=ROOT).stdout.strip()
        config["schema_version"] = "1.1"
        config.pop("case_contract")
        config["pairs"] = [
            {key: value for key, value in config["pairs"][0].items() if key not in {"category", "contract"}}
        ]
        config["release_plan"] = {"pair_ids": [config["pairs"][0]["id"]], "trials_per_pair": 3}
        inputs, snapshot = paired_eval.evaluation_input_snapshot(config, head)
        expected_fixture = subprocess.run(
            ["git", "show", f"{head}:evals/{config['pairs'][0]['fixture']}"],
            cwd=ROOT, check=True, capture_output=True, text=True,
        ).stdout
        self.assertEqual(inputs[config["pairs"][0]["id"]]["fixture"], expected_fixture)
        self.assertTrue(
            any(entry["path"].endswith("/references/context-readiness.md") for entry in snapshot["entries"])
        )
        self.assertIn(
            "skills/repo-context/references/context-readiness.md",
            inputs[config["pairs"][0]["id"]]["capability_sources"]["repo-context"],
        )
        self.assertEqual(snapshot["source"], "git-commit")
        self.assertEqual(snapshot["commit"], head)
        self.assertGreater(len(snapshot["entries"]), len(config["pairs"]))

    def test_input_snapshot_digest_binds_pair_to_capability_source_mapping(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        _, compact = paired_eval.evaluation_input_snapshot(config, None)
        expanded = json.loads(json.dumps(config))
        pair = next(item for item in expanded["pairs"] if item["id"] == "PAIR-REVIEW-AUTH-DIFF")
        pair["capability_context"] = {
            "change-review": ["references/review-protocol.md"],
            "verification": [
                "references/test-strategy.md",
                "references/evidence-contract.md",
                "references/test-environments.md",
            ],
        }
        _, verbose = paired_eval.evaluation_input_snapshot(expanded, None)
        self.assertNotEqual(compact["assignments"], verbose["assignments"])
        self.assertNotEqual(compact["sha256"], verbose["sha256"])

    def test_release_mode_rejects_external_self_declared_plan_before_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = legacy_development_config()
            config["pairs"] = config["pairs"][:3]
            config["release_plan"] = {
                "pair_ids": [pair["id"] for pair in config["pairs"]],
                "category_ids": ["CAT-CONTEXT"],
                "minimum_cases_per_category": 3,
                "trials_per_pair": 3,
            }
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
            self.assertEqual(timed.error_kind, "timeout")
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
            self.assertEqual(noisy.error_kind, "output-limit")
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

    def test_owned_process_interrupt_terminates_the_owned_tree_before_stream_cleanup(self) -> None:
        class InterruptedProcess:
            pid = 12345
            _handle = 0
            returncode = None
            stdin = io.BytesIO()
            stdout = io.BytesIO(b"partial stdout")
            stderr = io.BytesIO(b"partial stderr")

            def __init__(self) -> None:
                self.waits = 0

            def wait(self, timeout: float | None = None) -> int:
                self.waits += 1
                if self.waits == 1:
                    raise KeyboardInterrupt
                self.returncode = -15
                return self.returncode

            def poll(self) -> int | None:
                return self.returncode

            def kill(self) -> None:
                self.returncode = -9

        process = InterruptedProcess()
        with mock.patch.object(process_eval.subprocess, "Popen", return_value=process), mock.patch.object(
            process_eval,
            "_terminate_owned_tree",
        ) as terminate, mock.patch.object(
            process_eval,
            "_posix_detached_descendants",
            return_value=set(),
        ):
            with self.assertRaises(KeyboardInterrupt):
                process_eval.run_owned_process(
                    ["bounded"],
                    "{}",
                    cwd=ROOT,
                    timeout=2,
                    output_limit=64,
                )
        terminate.assert_called()

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
                "--config",
                str(ROOT / "evals" / "paired-evaluations-acceptance.json"),
                "--pair",
                "PAIR-ACC-CONTEXT-WORKTREE",
                "--trials",
                "12",
                "--release",
                "--expected-commit",
                "a" * 40,
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("complete configured pair/category set", result.stderr)
            self.assertFalse(output.exists())

    def test_release_mode_rejects_infrastructure_retries_before_creating_output(self) -> None:
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
                "--release",
                "--expected-commit",
                "a" * 40,
                "--infrastructure-retries",
                "1",
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("zero infrastructure retries", result.stderr)
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

    def test_iteration_breaker_blocks_fourth_same_cause_until_owner_reassessment(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "breaker-case",
                "--task-type",
                "routine",
                "--objective",
                "Repair one repeated root cause",
            )
            self.assertEqual(created.returncode, 0, created.stderr or created.stdout)
            packet = Path(json.loads(created.stdout)["packet"])
            (packet / "artifacts" / "root-cause-1.md").write_text(
                "Invariant: the same bounded input still reproduces failure E-1.\n",
                encoding="utf-8",
            )

            for attempt in range(1, 4):
                recorded = run(
                    PYTHON,
                    str(FLOW),
                    "record-iteration",
                    str(packet),
                    "--kind",
                    "repair",
                    "--cause-id",
                    "root-cause-1",
                    "--cause-file",
                    "root-cause-1.md",
                    "--outcome",
                    "failed",
                    "--note",
                    f"repair attempt {attempt} preserved the failure",
                )
                self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
                self.assertEqual(json.loads(recorded.stdout)["round"], attempt)

            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["state"], "blocked")
            self.assertEqual(metadata["iteration_control"]["blocked"]["cause_id"], "root-cause-1")
            metadata_path = packet / "packet.json"
            metadata["iteration_control"]["records"][-1]["round"] = 2
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            tampered = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(tampered.returncode, 2)
            self.assertIn("failed round must be contiguous", tampered.stdout)
            metadata["iteration_control"]["records"][-1]["round"] = 3
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            without_control = dict(metadata)
            without_control.pop("iteration_control")
            metadata_path.write_text(json.dumps(without_control, indent=2) + "\n", encoding="utf-8")
            missing_control = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(missing_control.returncode, 2)
            self.assertIn("requires iteration_control", missing_control.stdout)
            missing_resume = run(PYTHON, str(FLOW), "transition", str(packet), "discovering", "--note", "unsafe resume")
            self.assertEqual(missing_resume.returncode, 2)

            cleared = json.loads(json.dumps(metadata))
            cleared["iteration_control"]["blocked"] = None
            metadata_path.write_text(json.dumps(cleared, indent=2) + "\n", encoding="utf-8")
            cleared_control = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(cleared_control.returncode, 2)
            self.assertIn("third failed round requires", cleared_control.stdout)
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            events_path = packet / "events.jsonl"
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            events[-2]["state"] = "discovering"
            events_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")
            drifted_event = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(drifted_event.returncode, 2)
            self.assertIn("iteration event 3 projected state is invalid", drifted_event.stdout)
            blocked_reassessment = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "repair",
                "--cause-id",
                "root-cause-1",
                "--cause-file",
                "root-cause-1.md",
                "--outcome",
                "reassessed",
                "--reopened-owner",
                "architecture-decisions",
                "--note",
                "event drift must block reassessment",
            )
            self.assertEqual(blocked_reassessment.returncode, 2)
            events[-2]["state"] = "blocked"
            events_path.write_text("".join(json.dumps(event, sort_keys=True) + "\n" for event in events), encoding="utf-8")

            fourth = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "repair",
                "--cause-id",
                "root-cause-1",
                "--cause-file",
                "root-cause-1.md",
                "--outcome",
                "failed",
                "--note",
                "unsafe fourth attempt",
            )
            self.assertEqual(fourth.returncode, 2)
            self.assertIn("reassess", fourth.stdout)
            premature = run(PYTHON, str(FLOW), "transition", str(packet), "discovering", "--note", "continue")
            self.assertEqual(premature.returncode, 2)
            self.assertIn("reassess", premature.stdout)

            reassessed = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "repair",
                "--cause-id",
                "root-cause-1",
                "--cause-file",
                "root-cause-1.md",
                "--outcome",
                "reassessed",
                "--reopened-owner",
                "architecture-decisions",
                "--note",
                "returned to the architecture owner and replaced the causal model",
            )
            self.assertEqual(reassessed.returncode, 0, reassessed.stderr or reassessed.stdout)
            resumed = run(PYTHON, str(FLOW), "transition", str(packet), "discovering", "--note", "reassessed")
            self.assertEqual(resumed.returncode, 0, resumed.stderr or resumed.stdout)
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual([event["event"] for event in events[-3:]], ["transition", "iteration-reassessed", "transition"])

    def test_iteration_breaker_counts_same_cause_and_resets_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "breaker-reset",
                "--task-type",
                "routine",
                "--objective",
                "Keep independent repair causes separate",
            )
            packet = Path(json.loads(created.stdout)["packet"])
            for cause in ("cause-a", "cause-b"):
                (packet / "artifacts" / f"{cause}.md").write_text(
                    f"Stable first-failure evidence for {cause}.\n",
                    encoding="utf-8",
                )
            sequence = [
                ("cause-a", "failed", 1),
                ("cause-b", "failed", 1),
                ("cause-a", "failed", 2),
                ("cause-a", "succeeded", 0),
                ("cause-a", "failed", 1),
            ]
            for cause, outcome, expected_round in sequence:
                result = run(
                    PYTHON,
                    str(FLOW),
                    "record-iteration",
                    str(packet),
                    "--kind",
                    "hypothesis",
                    "--cause-id",
                    cause,
                    "--cause-file",
                    f"{cause}.md",
                    "--outcome",
                    outcome,
                    "--note",
                    f"{cause} {outcome}",
                )
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                self.assertEqual(json.loads(result.stdout)["round"], expected_round)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["state"], "discovering")
            self.assertIsNone(metadata["iteration_control"]["blocked"])

    def test_iteration_cause_identity_is_bound_to_packet_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run(
                PYTHON,
                str(FLOW),
                "init-packet",
                "--root",
                str(root),
                "--change-id",
                "breaker-identity",
                "--task-type",
                "routine",
                "--objective",
                "Bind a repeated failure to stable evidence",
            )
            packet = Path(json.loads(created.stdout)["packet"])
            cause_a = packet / "artifacts" / "cause-a.md"
            cause_b = packet / "artifacts" / "cause-b.md"
            evidence = "First failure E-1 violates invariant I-1.\n"
            cause_a.write_text(evidence, encoding="utf-8")
            cause_b.write_text(evidence, encoding="utf-8")
            first = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "hypothesis",
                "--cause-id",
                "cause-a",
                "--cause-file",
                "cause-a.md",
                "--outcome",
                "failed",
                "--note",
                "first falsified hypothesis",
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)

            alias = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "hypothesis",
                "--cause-id",
                "renamed-cause",
                "--cause-file",
                "cause-b.md",
                "--outcome",
                "failed",
                "--note",
                "attempted alias",
            )
            self.assertEqual(alias.returncode, 2)
            self.assertIn("different cause-id", alias.stdout)

            cause_a.write_text("Changed evidence.\n", encoding="utf-8")
            drift = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(drift.returncode, 2)
            self.assertIn("digest drifted", drift.stdout)
            continued = run(
                PYTHON,
                str(FLOW),
                "record-iteration",
                str(packet),
                "--kind",
                "hypothesis",
                "--cause-id",
                "cause-a",
                "--cause-file",
                "cause-a.md",
                "--outcome",
                "failed",
                "--note",
                "unsafe continuation after evidence drift",
            )
            self.assertEqual(continued.returncode, 2)

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
    def test_contract_obligations_cannot_grade_capabilities_the_pair_does_not_supply(self) -> None:
        namespace = runpy.run_path(
            str(ROOT / "evals" / "run_contract_checks.py"),
            run_name="contract_alignment_test",
        )
        alignment = namespace["capability_alignment_errors"]

        def obligation(identifier: str, owner: str, action: str) -> dict[str, str]:
            return {
                "id": identifier,
                "owner": owner,
                "criticality": "critical",
                "action": action,
                "evidence_kind": "analysis",
            }

        packet = obligation("OB-1", "dev-flow", "create a complete trace packet")
        dependency = obligation("OB-2", "dependency-decisions", "request dependency approval")
        self.assertEqual(
            len(alignment([packet, dependency], ["verification", "change-review"])),
            2,
        )
        self.assertEqual(
            alignment([packet, dependency], ["dev-flow", "dependency-decisions"]),
            [],
        )
        product = obligation("OB-1", "product-ux-discovery", "preserve current information architecture")
        self.assertEqual(
            len(alignment([product], ["architecture-decisions", "verification"])),
            1,
        )
        self.assertEqual(
            alignment([product], ["architecture-decisions", "product-ux-discovery", "verification"]),
            [],
        )
        product_scan = obligation("OB-1", "product-ux-discovery", "scan current product truth")
        self.assertEqual(
            len(alignment([product_scan], ["architecture-decisions", "verification"])),
            1,
        )
        self.assertEqual(
            alignment(
                [product_scan],
                ["architecture-decisions", "product-ux-discovery", "verification"],
            ),
            [],
        )

    def test_frontend_engineering_routes_the_product_contract_owner(self) -> None:
        for config_name in ("paired-evaluations.json", "paired-evaluations-acceptance.json"):
            config = json.loads((ROOT / "evals" / config_name).read_text(encoding="utf-8"))
            pairs = [item for item in config["pairs"] if item["category"] == "CAT-FRONTEND-ENGINEERING"]
            self.assertEqual(len(pairs), 3)
            validated = paired_eval.validate_config(config)
            inputs, _ = paired_eval.evaluation_input_snapshot(validated, None)
            for pair in pairs:
                obligation_owners = {
                    item["owner"] for item in inputs[pair["id"]]["contract"]["work_units"]
                }
                self.assertIn("product-ux-discovery", pair["capabilities"])
                self.assertTrue(obligation_owners.issubset(set(pair["capabilities"])))
                self.assertEqual(pair["capability_context"]["product-ux-discovery"], [])

    def test_authorization_review_uses_the_smallest_high_signal_capability_set(self) -> None:
        config = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
        pair = next(item for item in config["pairs"] if item["id"] == "PAIR-REVIEW-AUTH-DIFF")
        self.assertEqual(pair["capabilities"], ["change-review", "verification"])
        self.assertEqual(
            pair["capability_context"],
            {
                "change-review": ["references/authorization-privacy.md"],
                "verification": ["references/test-strategy.md", "references/evidence-contract.md"],
            },
        )
        concurrency = next(item for item in config["pairs"] if item["id"] == "PAIR-REVIEW-CONCURRENCY-DIFF")
        self.assertNotIn(
            "references/authorization-privacy.md",
            concurrency["capability_context"]["change-review"],
        )

    def test_structured_input_contract_follows_capability_ownership_and_atomicity(self) -> None:
        contract = json.loads(
            (ROOT / "evals" / "contracts" / "structured-user-input.json").read_text(
                encoding="utf-8"
            )
        )
        expected_routes = [
            ("dev-flow", "dev-flow.decision"),
            ("requirements-design", "requirements-design.interaction"),
            ("requirements-design", "requirements-design.analysis"),
            ("requirements-design", "requirements-design.interaction"),
            ("requirements-design", "requirements-design.interaction"),
            ("dev-flow", "dev-flow.interaction"),
            ("dev-flow", "dev-flow.interaction"),
            ("requirements-design", "requirements-design.artifact"),
            ("dependency-decisions", "dependency-decisions.decision"),
            ("dev-flow", "dev-flow.decision"),
            ("delivery-readiness", "delivery-readiness.decision"),
            *[("verification", "verification.test")] * 11,
            ("requirements-design", "requirements-design.interaction"),
            ("verification", "verification.test"),
            ("dev-flow", "dev-flow.decision"),
            ("requirements-design", "requirements-design.decision"),
            ("requirements-design", "requirements-design.decision"),
            ("verification", "verification.test"),
            ("verification", "verification.test"),
            ("dev-flow", "dev-flow.limitation"),
        ]
        self.assertEqual(len(contract["work_units"]), 30)
        self.assertEqual(
            [
                (unit["owner"], unit["claim_routes"][0]["kind"])
                for unit in contract["work_units"]
            ],
            expected_routes,
        )
        self.assertTrue(all(len(unit["facets"]) == 1 for unit in contract["work_units"]))
        self.assertEqual(
            [unit["facets"][0]["id"] for unit in contract["work_units"]],
            [f"OB-{index}" for index in range(1, 31)],
        )

        dev_flow = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        interaction = (
            ROOT / "skills" / "requirements-design" / "references" / "user-interaction.md"
        ).read_text(encoding="utf-8")
        verification = (ROOT / "skills" / "verification" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        test_strategy = (
            ROOT / "skills" / "verification" / "references" / "test-strategy.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "the control plane owns operational approval, secret routing, and waiver state",
            dev_flow,
        )
        self.assertIn("Requirements Design owns product meaning and semantic answer records", interaction)
        self.assertIn("Verification owns executable response and lifecycle checks", interaction)
        self.assertIn(
            "Default-mode control, waiver state, and post-interaction continuation are owned by Dev Flow",
            interaction,
        )
        self.assertIn("A behavior or interaction claim never doubles as proof", verification)
        self.assertIn("Emit a separate verification-owned test cell", verification)
        self.assertIn("create a separate verification-owned test cell", test_strategy)
        self.assertIn("`NOT RUN` status", test_strategy)
        self.assertIn("contrasts available and unavailable paths", test_strategy)

    def test_release_quality_contracts_are_top_level_and_actionable(self) -> None:
        def section(text: str, heading: str) -> str:
            marker = f"## {heading}\n"
            body = text.split(marker, 1)[1]
            return body.split("\n## ", 1)[0]

        architecture = (ROOT / "skills" / "architecture-decisions" / "SKILL.md").read_text(encoding="utf-8")
        architecture_policy = (
            ROOT / "skills" / "architecture-decisions" / "references" / "neutral-engineering-policy.md"
        ).read_text(encoding="utf-8")
        devflow = (ROOT / "skills" / "dev-flow" / "SKILL.md").read_text(encoding="utf-8")
        repo_context = (ROOT / "skills" / "repo-context" / "SKILL.md").read_text(encoding="utf-8")
        requirements = (ROOT / "skills" / "requirements-design" / "SKILL.md").read_text(encoding="utf-8")
        verification = (ROOT / "skills" / "verification" / "SKILL.md").read_text(encoding="utf-8")
        test_strategy = (
            ROOT / "skills" / "verification" / "references" / "test-strategy.md"
        ).read_text(encoding="utf-8")
        change_review = (ROOT / "skills" / "change-review" / "SKILL.md").read_text(encoding="utf-8")
        authorization_privacy = (
            ROOT / "skills" / "change-review" / "references" / "authorization-privacy.md"
        ).read_text(encoding="utf-8")
        review_protocol = (
            ROOT / "skills" / "change-review" / "references" / "review-protocol.md"
        ).read_text(encoding="utf-8")
        dependency = (ROOT / "skills" / "dependency-decisions" / "SKILL.md").read_text(encoding="utf-8")
        delivery = (ROOT / "skills" / "delivery-readiness" / "SKILL.md").read_text(encoding="utf-8")
        delivery_contract = (
            ROOT / "skills" / "delivery-readiness" / "references" / "readiness-contract.md"
        ).read_text(encoding="utf-8")
        product_ux = (ROOT / "skills" / "product-ux-discovery" / "SKILL.md").read_text(encoding="utf-8")
        profile_contract = (
            ROOT / "skills" / "manage-engineering-profiles" / "references" / "profile-contract.md"
        ).read_text(encoding="utf-8")
        orchestration = (ROOT / "skills" / "dev-flow" / "references" / "orchestration.md").read_text(
            encoding="utf-8"
        )
        eqac_contract = json.loads(
            (ROOT / "evals" / "contracts" / "rust-backend.json").read_text(encoding="utf-8")
        )

        self.assertIn(
            "consume the smallest repo-context-admitted specialist evidence per affected consumer",
            section(architecture, "Procedure").casefold(),
        )
        self.assertIn(
            "route selection is not review execution",
            section(architecture, "Procedure"),
        )
        self.assertIn(
            "Bugfixes reproduce the causal failure and, when practical, prove a focused regression fails before the fix; keep direct, protected, and out-of-scope behavior explicit.",
            section(devflow, "Execute"),
        )
        context_procedure = section(repo_context, "Procedure")
        self.assertIn("Record consequential rules as stable `INS-n` with source, scope, authority", context_procedure)
        self.assertIn("Review both sides of FFI: layout, ownership, errors, panic containment", architecture_policy)
        self.assertIn(
            "Separate ABI versioning from compatibility migration/rollback/removal.",
            section(architecture, "Procedure"),
        )
        self.assertIn(
            "require and consume a repo-context-owned discovery record",
            architecture_policy,
        )
        self.assertIn(
            "For FFI, keep representation, callback lifecycle, and compatibility evolution separate.",
            section(architecture, "Procedure"),
        )
        self.assertIn(
            "Never detach callback producers across teardown.",
            architecture_policy,
        )
        self.assertIn(
            "Record separate `architecture.decision.v1` items when choices, protected behaviors, or recheck triggers can change independently; each item includes evidence, applicability, tradeoffs, exceptions, consequences, tests, and recheck triggers.",
            section(architecture, "Procedure"),
        )
        ffi_contract_counts = {
            "ffi-mobile.json": (8, 57),
            "ffi-ownership-error.json": (13, 53),
            "ffi-lifecycle-packaging.json": (8, 44),
        }
        ffi_pair_ids = {
            "ffi-mobile.json": "PAIR-CROSS-LANGUAGE",
            "ffi-ownership-error.json": "PAIR-FFI-OWNERSHIP-ERROR",
            "ffi-lifecycle-packaging.json": "PAIR-FFI-LIFECYCLE-PACKAGING",
        }
        kind_registry = json.loads(
            (ROOT / "governance" / "claim-kinds.json").read_text(encoding="utf-8")
        )
        kind_owners = {item["id"]: item["owner"] for item in kind_registry["kinds"]}
        development_config = json.loads(
            (ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8")
        )
        for contract_name, (expected_units, expected_facets) in ffi_contract_counts.items():
            ffi_contract = json.loads(
                (ROOT / "evals" / "contracts" / contract_name).read_text(encoding="utf-8")
            )
            work_units = ffi_contract["work_units"]
            facets = [
                {
                    **facet,
                    "owner": unit["owner"],
                    "criticality": unit["criticality"],
                    "route_kinds": [route["kind"] for route in unit["claim_routes"]],
                }
                for unit in work_units
                for facet in unit["facets"]
            ]
            self.assertEqual(ffi_contract["schema_version"], "2.2")
            self.assertEqual(len(work_units), expected_units)
            self.assertEqual(len(facets), expected_facets)
            self.assertLessEqual(len(facets), 64)
            self.assertEqual(
                {item["id"] for item in facets},
                {f"OB-{index}" for index in range(1, expected_facets + 1)},
            )
            self.assertTrue(
                all(
                    set(unit)
                    == {"id", "owner", "claim_routes", "criticality", "protected_behavior", "facets"}
                    and all(
                        set(route) == {"kind"} and kind_owners[route["kind"]] == unit["owner"]
                        for route in unit["claim_routes"]
                    )
                    and all(set(facet) == {"id", "action"} for facet in unit["facets"])
                    for unit in work_units
                )
            )
            routes = [
                item
                for item in facets
                if item["owner"] == "architecture-decisions"
                and "architecture-decisions.decision" in item["route_kinds"]
                and "route" in item["action"].casefold()
            ]
            self.assertEqual(len(routes), 3)
            self.assertTrue(all(item["criticality"] == "required" for item in routes))
            self.assertTrue(any("Rust-Swift" in item["action"] for item in routes))
            self.assertTrue(any("Rust-Kotlin" in item["action"] for item in routes))
            self.assertTrue(any("independent FFI review" in item["action"] for item in routes))
            discovery = [
                item
                for item in facets
                if item["owner"] == "repo-context"
                and "repo-context.analysis" in item["route_kinds"]
                and "inventory" in item["action"].casefold()
            ]
            self.assertEqual(len(discovery), 9)
            self.assertTrue(all(item["criticality"] == "required" for item in discovery))
            review_actions = "\n".join(
                item["action"] for item in facets if item["owner"] == "change-review"
            ).casefold()
            self.assertTrue(
                all(
                    term in review_actions
                    for term in (
                        "approved diff",
                        "generated artifacts",
                        "changed-file",
                        "raw verification",
                        "swift consumer",
                        "kotlin consumer",
                        "abi",
                        "lifecycle",
                        "packaging",
                        "mixed-version",
                        "rollback",
                    )
                )
            )
            ffi_pair = next(
                item for item in development_config["pairs"] if item["id"] == ffi_pair_ids[contract_name]
            )
            self.assertIn("repo-context", ffi_pair["capabilities"])
            self.assertEqual(ffi_pair["capability_context"]["repo-context"], [])
            fixture = (ROOT / "evals" / ffi_pair["fixture"]).read_text(encoding="utf-8")
            self.assertNotIn("A good first attempt", fixture)

        acceptance_config = json.loads(
            (ROOT / "evals" / "paired-evaluations-acceptance.json").read_text(encoding="utf-8")
        )
        acceptance_ffi = json.loads(
            (ROOT / "evals" / "cases" / "acceptance-ffi.json").read_text(encoding="utf-8")
        )
        acceptance_pairs = [
            item for item in acceptance_config["pairs"] if item["category"] == "CAT-FFI"
        ]
        self.assertEqual(len(acceptance_pairs), 3)
        self.assertTrue(
            all(
                {"repo-context", "architecture-decisions", "verification", "change-review"}
                .issubset(set(item["capabilities"]))
                for item in acceptance_pairs
            )
        )
        for case in acceptance_ffi["cases"]:
            case_units = case["work_units"]
            case_facets = [
                {
                    **facet,
                    "owner": unit["owner"],
                    "route_kinds": [route["kind"] for route in unit["claim_routes"]],
                }
                for unit in case_units
                for facet in unit["facets"]
            ]
            self.assertEqual(
                {item["owner"] for item in case_units},
                {"repo-context", "architecture-decisions", "verification", "change-review"},
            )
            self.assertEqual(
                len(
                    [
                        item
                        for item in case_facets
                        if "architecture-decisions.decision" in item["route_kinds"]
                        and "route" in item["action"].casefold()
                    ]
                ),
                3,
            )
            self.assertTrue(
                any(
                    "repo-context.analysis" in item["route_kinds"]
                    and "inventory" in item["action"].casefold()
                    for item in case_facets
                )
            )
            self.assertTrue(
                any(
                    item["owner"] == "change-review"
                    and set(item["route_kinds"])
                    & {"change-review.analysis", "change-review.limitation"}
                    and "evidence" in item["action"].casefold()
                    for item in case_facets
                )
            )
        self.assertIn(
            "When late material ambiguity changes the baseline, record an `AMB-n`, stop affected work, return the content-bound packet to `awaiting-approval`, increment the revision, preserve approval history, obtain the user disposition, and create fresh digest-bound Requirement Ready and design approvals.",
            section(requirements, "Procedure"),
        )
        self.assertIn(
            "Detailed matrices and cell rules live in `references/test-strategy.md`.",
            section(verification, "EQAC rule"),
        )
        self.assertIn(
            "Inventory the applicable call, data, error, consumer, artifact, version, loading, and runtime paths.",
            section(repo_context, "Procedure"),
        )
        self.assertIn(
            "Freeze the approved revision/digest, AC/SC/VO set, base/diff, changed-file and generated-artifact accounting, and raw verification evidence.",
            section(change_review, "Procedure"),
        )
        self.assertIn(
            "For cross-language changes, trace every consumer and generated-artifact causal path.",
            review_protocol,
        )
        self.assertIn(
            "Preserve applicable independently variable axes or prerequisites; umbrella labels do not replace them.",
            section(change_review, "Procedure"),
        )
        self.assertIn(
            "A post-change review names the approved diff, generated artifacts, complete changed-file list",
            review_protocol,
        )
        self.assertIn(
            "For overload, cover bounded admission, capacity, rejection/backpressure, retry amplification, and recovery.",
            test_strategy,
        )
        auth_review = section(change_review, "Procedure")
        self.assertIn("Authorization/privacy review:", auth_review)
        self.assertIn(
            "Only when the approved task or diff contains an authorization or privacy boundary, read `references/authorization-privacy.md`; otherwise do not load, mention, or apply that checklist.",
            auth_review,
        )
        self.assertNotIn("explicitly account for all five groups", change_review)
        self.assertIn(
            "Before returning an authorization-boundary review, explicitly account for all five groups: (1) the full actor-to-log path; (2) positive and missing, stale, confused, and cross-tenant identities; (3) stable non-enumerating errors, audit events, and credential or personal-data redaction; (4) relevant limits, malformed input, retry, cancellation, and rollback effects; and (5) for each verified finding, severity, affected contract, causal proof, and focused remediation.",
            section(authorization_privacy, "Authorization completion gate"),
        )
        self.assertIn(
            "For concurrency findings, require controlled scheduling or bounded repeated evidence, retain protected ordinary behavior tests, and omit unrelated specialist checklists.",
            section(review_protocol, "Evaluation"),
        )
        self.assertEqual(
            [
                facet["action"]
                for unit in eqac_contract["work_units"]
                for facet in unit["facets"]
            ],
            [
                "inspect job lifecycle, shutdown, persistence, capacity, and existing verification before choosing oracles",
                "define bounded admission, overload or backpressure, retry, deduplication, cancellation, collision, and restart recovery checks",
                "create deterministic or bounded repeated tests for claim exclusivity, retry limits, restart recovery, and drain behavior",
                "run Rust static, focused unit, integration, restart, drain, and resource evidence as applicable",
                "record exact commands and outcomes while preserving failed, flaky, blocked, and not-run gates",
            ],
        )
        self.assertIn(
            "Complete safe research and an actionable plan before any approval boundary. An explicit implementation request authorizes its exact existing-dependency removal or routine update as task intent; when repository evidence resolves the identity, command, files, and result bytes without a material choice, bind that original request into the exact machine-readable approval record instead of asking for the same intent again. Stop before mutation when exact binding is impossible or mismatched. This never authorizes an addition, material feature or risk expansion, a different dependency/operation/scope, or mutation during analysis-only or read-only work.",
            section(dependency, "Procedure"),
        )
        self.assertIn(
            "Removal: establish a pre-change graph; search source, tests, examples, build scripts, generated inputs/outputs, features, platform targets, and downstream consumers; run and preserve applicable default/minimal/all-feature builds and affected tests, generated consistency, platform, and consumer cells; remove through native tooling without hand-editing the lockfile; repeat the same matrix; inspect graph/lockfile integrity, advisories, and licenses; clean only proven-dead features/configuration/generated/build/documentation surfaces; and record rollback plus every `NOT RUN` environment or consumer.",
            section(dependency, "Procedure"),
        )
        self.assertIn(
            "For release artifacts, freeze source commit, version, configuration, release target, artifact set, signing identity, observation owner, and rollback owner; compare SHA-256 from two clean builds; verify contents, version, and commit; require a non-empty standards-format SBOM and provenance bound to the final digest; verify the signature; then keep tag and Draft prerelease actions separately authorized.",
            section(delivery, "Procedure"),
        )
        self.assertIn(
            "Failed, flaky, blocked, not-run, mismatched, or unsigned required release cells block tag and release-ready claims; retain their status and first evidence.",
            section(delivery, "Procedure"),
        )
        self.assertIn(
            "Before returning an RC or release plan, explicitly account for: first-failure packet; a separate executed check and evidence row for each of stale/wrong subjects, nondeterminism, post-build mutation, and upload substitution, including intended-local versus uploaded asset name/size/digest; causal repair in a distinct attempt; two clean builds and manifest/identity checks; completion of tamper and mismatched-pair rejection before generating any fresh signature; only then fresh signature generation and verification; local-snapshot versus remote-tag/target-platform evidence; lifecycle ownership/cleanup; and every `NOT RUN` cell.",
            section(delivery, "Procedure"),
        )
        release_gate = section(delivery_contract, "Release completion gate")
        self.assertIn(
            "Preserve the first failure as an immutable packet: archive and manifest digests, commit, configuration, toolchain, builder, environment, SBOM/provenance/signature subjects, uploaded-asset identity, logs, and receipts.",
            release_gate,
        )
        self.assertIn(
            "Execute and retain a separate evidence row for each of stale or wrong subjects, nondeterministic builds, post-build mutation, and upload substitution; for upload substitution compare intended-local and uploaded asset name, size, and digest. A general root-cause investigation or aggregate binding check does not satisfy these four cells; fix the causal builder or binding and create a distinct controlled attempt instead of editing metadata or overwriting evidence.",
            release_gate,
        )
        self.assertIn(
            "For the new attempt, compare two clean builds and verify archive manifest/contents/version/commit; complete tamper and mismatched-pair rejection before generating any fresh signature; only after those negative checks pass, generate and verify a fresh signature. Remote immutable-tag resolution and Draft Release remain later separately authorized gates.",
            release_gate,
        )
        self.assertIn(
            "Lifecycle evidence uses a temporary isolated profile; freezes prior and RC tag/source/version/expected bytes; covers install, upgrade, rollback, re-upgrade, uninstall, modified-file ownership, process/profile/credential cleanup, retained receipts, and a target-platform matrix. A local snapshot proves only local behavior; remote-tag and unrun target cells remain `NOT RUN`.",
            release_gate,
        )
        self.assertIn(
            "Before returning a user-facing plan, explicitly inspect current source/rendered states, semantic/event/data/state ownership, routes/navigation, design system/assets, browser projects, and freshest product truth; if unavailable, make this the first `NOT RUN` action.",
            section(product_ux, "Procedure"),
        )
        self.assertIn(
            "Before returning a material UI plan, confirm it covers relevant states plus semantics, keyboard/focus, names/status, confirmation, motion/scaling, responsive behavior, and rendered/manual evidence; mark inapplicable items with a reason.",
            section(product_ux, "Procedure"),
        )
        profile_modes = section(profile_contract, "Resolution modes")
        self.assertIn(
            "Resolve three modes explicitly: `personal-interactive` may read the known personal directory plus declared repository/task sources; `team-reproducible` and `ci` must exclude personal directories, environment-derived personal values, and credentials, and use only the public baseline plus declared repository/task sources.",
            profile_modes,
        )
        self.assertIn(
            "For `team-reproducible` and `ci`, run the resolver from clean isolated profile homes with deliberately different personal profiles; require identical effective bytes and fingerprints, and prove shared artifacts contain no personal paths, hashes, values, or credentials.",
            profile_modes,
        )
        self.assertIn(
            "Record source hashes, winners, shadowed entries, conflicts, unresolved material choices, fingerprints, exact commands/environments/outcomes, and every `NOT RUN` cell; an explicit work mode may raise but never lower evidence-derived risk or shared controls.",
            profile_modes,
        )
        self.assertIn(
            "Verification names representative viewport, input, browser/platform, accessibility, and every recovery transition; missing rendered or physical cells remain `NOT RUN`.",
            section(product_ux, "Procedure"),
        )
        self.assertIn(
            "Bugfix: inspect applicable instructions, causal path, tests, logs, and analogues; separate fact, inference, and unknown; bind direct, protected, and out-of-scope behavior; reproduce the failure and, when practical, prove a focused regression fails before the fix; then rerun the protected and nearby paths.",
            section(orchestration, "Task routing"),
        )

    def test_ffi_mobile_work_unit_merge_preserves_facet_contract(self) -> None:
        contract = json.loads(
            (ROOT / "evals" / "contracts" / "ffi-mobile.json").read_text(encoding="utf-8")
        )
        work_units = contract["work_units"]
        facet_contract = [
            {
                "id": facet["id"],
                "action": facet["action"],
                "owner": unit["owner"],
                "criticality": unit["criticality"],
                "claim_routes": unit["claim_routes"],
            }
            for unit in work_units
            for facet in unit["facets"]
        ]
        facet_contract.sort(key=lambda item: int(item["id"].split("-", 1)[1]))
        facet_contract_bytes = json.dumps(
            facet_contract,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        self.assertEqual(
            hashlib.sha256(facet_contract_bytes).hexdigest(),
            "b932c17d1ec12ea3c758240dce714255e8978941e1d18a8c18370bafd7626e37",
        )
        self.assertEqual(
            [
                (
                    unit["id"],
                    unit["owner"],
                    unit["criticality"],
                    tuple(route["kind"] for route in unit["claim_routes"]),
                    tuple(facet["id"] for facet in unit["facets"]),
                )
                for unit in work_units
            ],
            [
                (
                    "WU-1",
                    "architecture-decisions",
                    "required",
                    ("architecture-decisions.decision",),
                    tuple(f"OB-{index}" for index in range(1, 4)),
                ),
                (
                    "WU-2",
                    "repo-context",
                    "required",
                    ("repo-context.analysis",),
                    tuple(f"OB-{index}" for index in range(4, 13)),
                ),
                (
                    "WU-3",
                    "architecture-decisions",
                    "critical",
                    ("architecture-decisions.decision",),
                    tuple(f"OB-{index}" for index in range(13, 23)),
                ),
                (
                    "WU-4",
                    "architecture-decisions",
                    "critical",
                    ("architecture-decisions.decision",),
                    tuple(f"OB-{index}" for index in range(23, 31)),
                ),
                (
                    "WU-5",
                    "architecture-decisions",
                    "critical",
                    ("architecture-decisions.decision",),
                    tuple(f"OB-{index}" for index in range(31, 36)),
                ),
                (
                    "WU-6",
                    "verification",
                    "critical",
                    ("verification.test",),
                    tuple(f"OB-{index}" for index in range(36, 41))
                    + tuple(f"OB-{index}" for index in range(43, 47)),
                ),
                (
                    "WU-7",
                    "verification",
                    "critical",
                    ("verification.test",),
                    tuple(f"OB-{index}" for index in range(41, 43)),
                ),
                (
                    "WU-8",
                    "change-review",
                    "supporting",
                    ("change-review.limitation", "change-review.analysis"),
                    tuple(f"OB-{index}" for index in range(47, 58)),
                ),
            ],
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
                    "schema_version": "2.2",
                    "id": "CASE-INVALID",
                    "profile": "invalid nested values",
                    "prompt": "exercise validation",
                    "fixture": "reference-cases/sample.md",
                    "work_units": [
                        {
                            "id": "WU-1",
                            "owner": "verification",
                            "claim_routes": [{"kind": "verification.test"}],
                            "criticality": "critical",
                            "protected_behavior": "bounded verification behavior",
                            "facets": [{"id": "OB-1", "action": ""}],
                        }
                    ],
                    "forbidden_actions": [1],
                    "required_artifacts": ["does-not-exist.md"],
                },
                root=root,
            )
            self.assertTrue(any("work unit WU-1 facet 1 action must be non-empty" in error for error in errors))
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
