#!/usr/bin/env python3
"""Stdlib-only behavioral and mutation tests for Dev Flow."""

from __future__ import annotations

import json
import os
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


def write_valid_packet(
    packet: Path,
    *,
    state: str = "verifying",
    dependency_approved: bool = True,
    matrix_status: str = "PASSED",
    matrix_attempts: int = 1,
) -> None:
    for folder in ("briefs", "reports", "artifacts"):
        (packet / folder).mkdir(parents=True, exist_ok=True)
    now = "2026-08-08T00:00:00+00:00"
    metadata = {
        "schema_version": "1.0",
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
            "Task graph": "T1 maps AC-1 and SC-D1 to VO-1 and is complete under root ownership.",
            "Progress ledger": "E1 recorded discovery; E2 recorded approval; E3 recorded implementation; E4 recorded final verification.",
            "Agent ledger": "The root performed the bounded task without child delegation.",
            "Decisions and drift": "D1 kept the change inside approved scope; no drift occurred.",
            "Environment and resource ownership": "The root owned the temporary test directory and released it.",
            "Findings and repair rounds": "No verified finding required repair.",
            "Blockers and next ready task": "No blocker remains; acceptance review is ready."
        }),
        "test-matrix.md": section_document("Test matrix: sample-change", {
            "Dimensions and selection rationale": "The affected package and default configuration cover the bounded contract.",
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
            "Requirement and scope review": "AC-1 and SC-D1 map completely; protected behavior is unchanged.",
            "Integration and maintainability review": "The change follows existing idioms, error handling, tests, and documentation.",
            "Findings": "No verified blue finding remains.",
            "Disposition": "Accepted after the final scoped review."
        }),
        "red-audit.md": section_document("Red audit: sample-change", {
            "Audit brief": "A clean read-only brief covered boundary and failure behavior.",
            "Threat and failure hypotheses": "Invalid input and unchanged neighboring inputs were inspected.",
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
    for filename, text in docs.items():
        (packet / filename).write_text(text, encoding="utf-8")


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
    def test_contract_and_plugin_checks(self) -> None:
        contracts = run(PYTHON, str(ROOT / "evals" / "run_contract_checks.py"))
        self.assertEqual(contracts.returncode, 0, contracts.stderr or contracts.stdout)
        plugin = run(PYTHON, str(FLOW), "check", "--plugin-root", str(ROOT))
        self.assertEqual(plugin.returncode, 0, plugin.stderr or plugin.stdout)


if __name__ == "__main__":
    unittest.main()
