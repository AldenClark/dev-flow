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


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
FLOW = SCRIPTS / "dev-flow.py"
HOOK = ROOT / "hooks" / "dev_flow_hook.py"
PYTHON = sys.executable
AGENT_CONFIGS = ROOT / "skills" / "dev-flow" / "assets" / "agent-configs"


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
            result = run(PYTHON, str(FLOW), "preflight", "--version-output", "codex-cli 0.146.9", "--features-output-file", str(features), "--config", str(config))
            self.assertEqual(result.returncode, 2)
            self.assertIn("below required", result.stdout)

    def test_rejects_obsolete_config_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            config = root / "config.toml"
            write_features(features)
            write_config(config, correct=False)
            result = run(PYTHON, str(FLOW), "preflight", "--version-output", "codex-cli 0.147.0", "--features-output-file", str(features), "--config", str(config))
            self.assertEqual(result.returncode, 2)
            self.assertIn("obsolete", result.stdout)


class PacketTests(unittest.TestCase):
    def test_valid_semantic_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet)
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

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

    def test_rejects_accepted_not_run_cell(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = Path(temp) / "packet"
            write_valid_packet(packet, state="accepted", matrix_status="NOT RUN")
            result = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("required cell is NOT RUN", result.stdout)

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

    def test_init_creates_traceable_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = run(PYTHON, str(FLOW), "init-packet", "--root", str(root), "--change-id", "micro-fix", "--task-type", "micro", "--objective", "Fix the bounded typo")
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            packet = root / ".codex" / "dev-flow" / "micro-fix"
            self.assertTrue((packet / "packet.json").is_file())
            self.assertTrue((packet / "trace.md").is_file())
            self.assertTrue((packet / "briefs").is_dir())
            invalid = run(PYTHON, str(FLOW), "validate-packet", str(packet))
            self.assertEqual(invalid.returncode, 2)

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
            self.assertEqual(routine_meta["schema_version"], "1.2")
            self.assertEqual(routine_meta["collaboration_profile"], "checkpointed")
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

    def test_subagent_report_must_be_fresh_for_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            flow = root / ".codex" / "dev-flow"
            packet = flow / "sample-change"
            reports = packet / "reports"
            reports.mkdir(parents=True)
            (flow / "current").write_text("sample-change\n", encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": []}}), encoding="utf-8")
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
            self.assertEqual(json.loads(missing.stdout)["decision"], "block")
            self.assertTrue(markers[0].exists())
            (reports / "agent.md").write_text("fresh report\n", encoding="utf-8")
            present = run(PYTHON, str(HOOK), stdin=json.dumps(stop_event), env=env)
            self.assertEqual(json.loads(present.stdout), {})
            self.assertFalse(markers[0].exists())


class PreferenceAuditTests(unittest.TestCase):
    def test_untracked_rust_manifest_detects_chrono(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init = run("git", "init", "-q", cwd=root)
            self.assertEqual(init.returncode, 0, init.stderr)
            (root / "Cargo.toml").write_text('[package]\nname = "sample"\nversion = "0.1.0"\n\n[dependencies]\nchrono = "0.4"\n', encoding="utf-8")
            packet = root / "packet"
            packet.mkdir()
            (packet / "packet.json").write_text(json.dumps({"approvals": {"dependencies": [{"id": "DEP-1"}]}}), encoding="utf-8")
            result = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root), "--packet", str(packet))
            self.assertEqual(result.returncode, 2)
            self.assertIn("PREF-RUST-TIME", result.stdout)

    def test_documentation_mentions_do_not_trigger_rust_rule(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            init = run("git", "init", "-q", cwd=root)
            self.assertEqual(init.returncode, 0, init.stderr)
            (root / "policy.md").write_text("Chrono is forbidden; use Jiff.\n", encoding="utf-8")
            result = run(PYTHON, str(FLOW), "audit-preferences", "--root", str(root))
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)


class RepositoryContractTests(unittest.TestCase):
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

    def test_contract_and_plugin_checks(self) -> None:
        contracts = run(PYTHON, str(ROOT / "evals" / "run_contract_checks.py"))
        self.assertEqual(contracts.returncode, 0, contracts.stderr or contracts.stdout)
        plugin = run(PYTHON, str(FLOW), "check", "--plugin-root", str(ROOT))
        self.assertEqual(plugin.returncode, 0, plugin.stderr or plugin.stdout)


if __name__ == "__main__":
    unittest.main()
