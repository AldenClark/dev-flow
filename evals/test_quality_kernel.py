#!/usr/bin/env python3
"""Behavioral contracts for the always-on quality kernel and recovery binding."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from evals.test_knowledge_system import bind_governed_authority, make_valid_repository
from evals.test_scripts import write_valid_packet


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev_flow.py"
HOOK = ROOT / "hooks" / "dev_flow_hook.py"


def run_flow(*args: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FLOW), *(str(value) for value in args)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )


def initialize_git_repository(root: Path) -> None:
    for args in (
        ("init", "-q"),
        ("config", "user.email", "dev-flow@example.invalid"),
        ("config", "user.name", "Dev Flow Test"),
    ):
        result = run_git(root, *args)
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
    (root / "tracked.txt").write_text("base\n", encoding="utf-8")
    added = run_git(root, "add", "tracked.txt")
    committed = run_git(root, "commit", "-qm", "base")
    if added.returncode or committed.returncode:
        raise AssertionError(added.stderr or committed.stderr)


def set_packet_skill_version(packet: Path, version: str) -> None:
    metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
    metadata["skill_version"] = version
    capabilities = sorted(version.split("+", 1)[1].split(".")) if "+" in version else []
    if "quality-kernel-v1" not in capabilities:
        for field in ("mutation_intent", "design_digest", "continuity_checkpoint", "knowledge_manifest"):
            metadata.pop(field, None)
    (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    events[0]["payload"]["skill_version"] = version
    contract = events[0]["payload"].get("creation_contract")
    if isinstance(contract, dict):
        if "quality-kernel-v1" not in capabilities:
            events[0]["payload"].pop("creation_contract")
        else:
            contract["skill_version"] = version
            contract["capabilities"] = capabilities
    (packet / "events.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def context_readiness() -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": "1.0",
        "tier": "T1",
        "outcome": "ready",
        "quality_coverage": {},
        "fingerprint": "sha256:" + "1" * 64,
    }
    projection = {key: nested for key, nested in value.items() if key != "projection_fingerprint"}
    payload = json.dumps(projection, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    value["projection_fingerprint"] = "sha256:" + hashlib.sha256(
        b"dev-flow-engineering-context-projection-1.0\0" + payload
    ).hexdigest()
    return value


def concrete_trace() -> str:
    return """# Micro change trace: quality-kernel

## Authority and repository facts

INS-1 permits local edits and tests. The exact root, instructions, and base were inspected.

## Requirement and design

AC-1 requires a recoverable quality-kernel trace. The existing boundary is extended without changing protected behavior.

## Scope and protected behavior

SC-D1 covers the bounded trace. SC-P1 preserves legacy packets. SC-L1 excludes delivery.

## Progress and decisions

E1 records the approved baseline and bounded implementation. D1 keeps the existing ownership boundary.

## Requirement source and understanding revisions

Source: The sanitized user request requires quality to survive routing and context loss.
Revision chain: Revision 1 incorporates repository evidence and the confirmed observable outcome.
Semantic closure: No material or high-risk ambiguity remains.

## Engineering context and quality routes

Binding: INS-1 and the recorded engineering-context fingerprint cover this path and phase.
Always-on kernel: Requirements, continuity, tests, challenge, and knowledge disposition apply.
Specialist routes: No additional technical specialist is required for this fixture.

## Continuity checkpoint

The CLI owns this recovery projection after design approval.

## Test technique accountability

Black-box: The CLI lifecycle and validation result exercise the public boundary.
White-box: Event projection, digest, and binding branches are exercised directly.
Oracle: Removing or drifting a required binding must make validation fail.

## Knowledge and commit readiness

Knowledge impact: none; the fixture changes no reusable project truth.
Slice: The packet contract, tests, and documentation form one bounded slice.
Commit-ready: yes; narrow and integration checks, diff, scope, secrets, comments, and docs were reviewed.
Delivery authority: No stage, commit, push, release, deploy, or external message is authorized.

## Change set

Artifact: change-set.v1
Intent and protected behavior: Bind the quality kernel while preserving legacy packet behavior.
Final bytes or read-only target: The final trace and packet projections are frozen.
Changed files: trace.md and packet.json.
Decisions and drift: The approved requirement and design remain aligned.
Narrow checks: Packet validation exercises these exact bytes.
Limits: Unsigned local state is consistency evidence, not tamper evidence.

## Verification

VO-1 validates the final packet and its failure-sensitive bindings; PASSED.

## Blue and red audit

Blue confirms requirement, scope, integration, and maintainability. Red removes and drifts bindings.

## Delivery and residual risk

Local implementation only; external delivery remains NOT RUN.
"""


def initialize_quality_packet(
    root: Path,
    change_id: str = "quality-kernel",
    *,
    task_type: str = "routine",
) -> Path:
    created = run_flow(
        "init-packet",
        "--root",
        root,
        "--change-id",
        change_id,
        "--task-type",
        task_type,
        "--objective",
        "Keep quality and semantics recoverable",
    )
    if created.returncode:
        raise AssertionError(created.stderr or created.stdout)
    packet = Path(json.loads(created.stdout)["packet"])
    (packet / "trace.md").write_text(concrete_trace(), encoding="utf-8")
    metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
    metadata["acceptance_ids"] = ["AC-1"]
    metadata["scope_ids"] = ["SC-D1", "SC-P1", "SC-L1"]
    metadata["verification_ids"] = ["VO-1"]
    (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    (packet / "context-readiness.json").write_text(
        json.dumps(context_readiness(), indent=2)
        + "\n",
        encoding="utf-8",
    )
    return packet


def initialize_legacy_packet(root: Path, *, change_id: str, skill_version: str) -> Path:
    packet = root / ".codex" / "dev-flow" / change_id
    write_valid_packet(packet, schema_version="1.2")
    metadata_path = packet / "packet.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["change_id"] = change_id
    metadata["skill_version"] = skill_version
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return packet


def write_events(packet: Path, events: list[dict[str, object]]) -> None:
    (packet / "events.jsonl").write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )


def approve_and_implement(packet: Path) -> None:
    for state, extra in (
        ("awaiting-approval", ()),
        (
            "requirements",
            (
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "The current semantic revision is ready",
            ),
        ),
        ("approved", ("--approved-by", "user")),
    ):
        if state == "requirements":
            result = run_flow(*extra)
        else:
            result = run_flow("transition", packet, state, "--note", f"enter {state}", *extra)
        if result.returncode:
            raise AssertionError(result.stderr or result.stdout)
    checkpoint = run_flow(
        "record-checkpoint",
        packet,
        "--trigger",
        "implementation-start",
        "--objective",
        "Implement the quality-kernel packet contract",
        "--active-id",
        "AC-1",
        "--active-id",
        "SC-D1",
        "--last-evidence",
        "Requirement and design approvals match current digests",
        "--next-action",
        "Implement the bounded packet contract",
        "--stop-condition",
        "Stop on baseline, context, scope, or authority drift",
    )
    if checkpoint.returncode:
        raise AssertionError(checkpoint.stderr or checkpoint.stdout)
    implementing = run_flow("transition", packet, "implementing", "--note", "begin implementation")
    if implementing.returncode:
        raise AssertionError(implementing.stderr or implementing.stdout)


def bind_none_and_checkpoint_for_verification(packet: Path) -> None:
    bound = run_flow(
        "bind-knowledge",
        packet,
        "--impact",
        "none",
        "--rationale",
        "This fixture changes no reusable project truth",
    )
    if bound.returncode:
        raise AssertionError(bound.stderr or bound.stdout)
    record_preverification_checkpoint(packet)


def record_preverification_checkpoint(packet: Path) -> None:
    checkpoint = run_flow(
        "record-checkpoint",
        packet,
        "--trigger",
        "pre-verification",
        "--objective",
        "Verify the final quality-kernel packet contract",
        "--active-id",
        "AC-1",
        "--active-id",
        "SC-D1",
        "--active-id",
        "VO-1",
        "--last-evidence",
        "The final change set and both test views are ready",
        "--next-action",
        "Run packet verification and adversarial drift checks",
        "--stop-condition",
        "Stop on any digest, fingerprint, binding, or oracle failure",
    )
    if checkpoint.returncode:
        raise AssertionError(checkpoint.stderr or checkpoint.stdout)


def bind_packet_authority_dossier(
    root: Path,
    packet: Path,
    *,
    change_id: str,
    project_root: str = "docs/project",
    changes_root: str = "docs/changes",
) -> tuple[Path, Path]:
    """Create one exact-byte authority document shared by a traced packet and dossier."""

    _, _, dossier = make_valid_repository(
        root,
        project_root=project_root,
        changes_root=changes_root,
        change_id=change_id,
    )
    manifest_path = dossier / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    promotion_link = manifest["knowledge"]["promotion_links"][0]
    authority_body = (
        "- AC-1: The observable command contract remains stable.\n"
        "- SC-D1: Change the direct implementation.\n"
        "- SC-P1: Preserve unrelated behavior.\n"
        "- SC-L1: Do not perform delivery actions.\n"
        "- VO-1: Exercise the observable and internal oracles.\n\n"
        "[Manifest](./manifest.json)\n\n"
        f"[Promoted current truth]({promotion_link})"
    )
    trace_path = packet / "trace.md"
    trace = trace_path.read_text(encoding="utf-8")
    pattern = re.compile(r"(?ms)(^##\s+Requirement and design\s*$\n)(.*?)(?=^##\s+|\Z)")
    if pattern.search(trace) is None:
        raise AssertionError("traced packet is missing Requirement and design")
    trace_path.write_text(
        pattern.sub(lambda match: match.group(1) + "\n" + authority_body + "\n\n", trace, count=1),
        encoding="utf-8",
    )
    change_path = dossier / "change.md"
    change_path.write_bytes(authority_body.encode("utf-8"))
    digest = "sha256:" + hashlib.sha256(change_path.read_bytes()).hexdigest()
    manifest["authority_binding"] = {
        "schema_version": "1.0",
        "change_id": change_id,
        "requirements": {"path": "change.md", "sha256": digest},
        "design": {"path": "change.md", "sha256": digest},
        "identifier_sets": dict(manifest["traceability"]),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path, change_path


class QualityKernelTests(unittest.TestCase):
    def test_late_material_reopening_invalidates_checkpoint_without_bricking_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "late-reopening")
            approve_and_implement(packet)
            recorded = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "A late material interpretation changes AC-1",
                "--source",
                "implementation evidence",
                "--interpretation",
                "retain the current behavior",
                "--interpretation",
                "change the public behavior",
                "--evidence",
                "the two outcomes are observably different",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "ask the user before continuing",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the late material choice.\n", encoding="utf-8")

            reopened = run_flow(
                "transition",
                packet,
                "awaiting-approval",
                "--ambiguity-id",
                "AMB-1",
                "--note",
                "reopen the affected requirement",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)
            self.assertEqual(run_flow("validate-packet", packet).returncode, 0)
            resolved = run_flow(
                "resolve-ambiguity",
                packet,
                "--id",
                "AMB-1",
                "--status",
                "user-confirmed",
                "--by",
                "user",
                "--resolution",
                "retain the current public behavior",
                "--evidence",
                "user confirmed the intended behavior",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "revision two is ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--approved-by",
                "user",
                "--note",
                "approve revision two design",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            checkpoint = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "implementation-start",
                "--objective",
                "resume the confirmed revision",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "revision two requirement and design are approved",
                "--next-action",
                "continue the bounded implementation",
                "--stop-condition",
                "stop on further semantic drift",
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr or checkpoint.stdout)
            implementing = run_flow("transition", packet, "implementing", "--note", "resume revision two")
            self.assertEqual(implementing.returncode, 0, implementing.stderr or implementing.stdout)

    def test_checkpoint_invalidation_tombstone_is_exact_and_bound_to_reopening(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "checkpoint-tombstone")
            approve_and_implement(packet)
            recorded = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "A late material interpretation changes AC-1",
                "--source",
                "implementation evidence",
                "--interpretation",
                "retain the current behavior",
                "--interpretation",
                "change the public behavior",
                "--evidence",
                "the two outcomes are observably different",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "ask the user before continuing",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the late material choice.\n", encoding="utf-8")
            reopened = run_flow(
                "transition",
                packet,
                "awaiting-approval",
                "--ambiguity-id",
                "AMB-1",
                "--note",
                "reopen the affected requirement",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)

            events_path = packet / "events.jsonl"
            original = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            invalidation_index = next(
                index for index, event in enumerate(original) if event["event"] == "checkpoint-invalidated"
            )
            invalidation = original[invalidation_index]
            transition = original[invalidation_index + 1]
            expected_keys = {
                "schema_version",
                "reason",
                "ambiguity_id",
                "invalidated_checkpoint_sha256",
                "from_requirement_revision",
                "new_requirement_revision",
            }
            self.assertEqual(set(invalidation["payload"]), expected_keys)
            self.assertEqual(invalidation["state"], "implementing")
            self.assertEqual(transition["event"], "transition")
            self.assertEqual(transition["payload"]["checkpoint_invalidation"], invalidation["payload"])

            mutations = {
                "schema": lambda payload: payload.__setitem__("schema_version", "9.9"),
                "reason": lambda payload: payload.__setitem__("reason", "unrelated"),
                "ambiguity": lambda payload: payload.__setitem__("ambiguity_id", "AMB-X"),
                "checkpoint-hash": lambda payload: payload.__setitem__(
                    "invalidated_checkpoint_sha256", "sha256:" + "0" * 64
                ),
                "from-revision": lambda payload: payload.__setitem__("from_requirement_revision", 99),
                "new-revision": lambda payload: payload.__setitem__("new_requirement_revision", 999),
                "missing-field": lambda payload: payload.pop("reason"),
                "extra-field": lambda payload: payload.__setitem__("extra", True),
            }
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    changed = json.loads(json.dumps(original))
                    mutate(changed[invalidation_index]["payload"])
                    mutate(changed[invalidation_index + 1]["payload"]["checkpoint_invalidation"])
                    events_path.write_text(
                        "".join(json.dumps(event, sort_keys=True) + "\n" for event in changed),
                        encoding="utf-8",
                    )
                    invalid = run_flow("validate-packet", packet)
                    self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                    self.assertIn("checkpoint invalidation", invalid.stdout)

            changed = json.loads(json.dumps(original))
            changed[invalidation_index + 1]["payload"]["checkpoint_invalidation"]["ambiguity_id"] = "AMB-X"
            events_path.write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in changed),
                encoding="utf-8",
            )
            unlinked = run_flow("validate-packet", packet)
            self.assertEqual(unlinked.returncode, 2, unlinked.stderr or unlinked.stdout)
            self.assertIn("adjacent open ambiguity tombstone", unlinked.stdout)
            events_path.write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in original),
                encoding="utf-8",
            )
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["requirement_revision"] += 1
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            jumped = run_flow("validate-packet", packet)
            self.assertEqual(jumped.returncode, 2, jumped.stderr or jumped.stdout)
            self.assertIn("exactly match the packet projection", jumped.stdout)
            metadata["requirement_revision"] -= 1
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(run_flow("validate-packet", packet).returncode, 0)

    def test_checkpoint_invalidation_uses_ambiguity_state_at_that_ledger_position(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "ambiguity-replay")
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "clarify the first ambiguity")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            first = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "An early requirement interpretation needs confirmation",
                "--source",
                "requirement review",
                "--interpretation",
                "retain behavior one",
                "--interpretation",
                "retain behavior two",
                "--evidence",
                "the outcomes differ",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "confirm behavior one",
            )
            self.assertEqual(first.returncode, 0, first.stderr or first.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the early choice.\n", encoding="utf-8")
            resolved_first = run_flow(
                "resolve-ambiguity",
                packet,
                "--id",
                "AMB-1",
                "--status",
                "user-confirmed",
                "--by",
                "user",
                "--resolution",
                "retain behavior one",
                "--evidence",
                "user confirmation",
            )
            self.assertEqual(resolved_first.returncode, 0, resolved_first.stderr or resolved_first.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "the clarified requirement is ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--approved-by",
                "user",
                "--note",
                "approve the clarified design",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            checkpoint = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "implementation-start",
                "--objective",
                "implement the clarified requirement",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "AMB-1 is resolved and the design is approved",
                "--next-action",
                "implement until new evidence changes the premise",
                "--stop-condition",
                "stop on a new material ambiguity",
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr or checkpoint.stdout)
            implementing = run_flow("transition", packet, "implementing", "--note", "begin implementation")
            self.assertEqual(implementing.returncode, 0, implementing.stderr or implementing.stdout)
            second = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "New implementation evidence creates a second choice",
                "--source",
                "implementation evidence",
                "--interpretation",
                "preserve the approved boundary",
                "--interpretation",
                "expand the approved boundary",
                "--evidence",
                "the scope outcomes differ",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "reopen only for the new choice",
            )
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-2 records the current late choice.\n", encoding="utf-8")
            reopened = run_flow(
                "transition",
                packet,
                "awaiting-approval",
                "--ambiguity-id",
                "AMB-2",
                "--note",
                "reopen for the current ambiguity",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)
            self.assertEqual(run_flow("validate-packet", packet).returncode, 0)

            events_path = packet / "events.jsonl"
            original = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            invalidation_index = next(
                index for index, event in enumerate(original) if event["event"] == "checkpoint-invalidated"
            )
            changed = json.loads(json.dumps(original))
            changed[invalidation_index]["payload"]["ambiguity_id"] = "AMB-1"
            changed[invalidation_index + 1]["payload"]["checkpoint_invalidation"]["ambiguity_id"] = "AMB-1"
            write_events(packet, changed)
            stale = run_flow("validate-packet", packet)
            self.assertEqual(stale.returncode, 2, stale.stderr or stale.stdout)
            self.assertIn("open material ambiguity at that ledger position", stale.stdout)

            write_events(packet, original)
            resolved_second = run_flow(
                "resolve-ambiguity",
                packet,
                "--id",
                "AMB-2",
                "--status",
                "user-confirmed",
                "--by",
                "user",
                "--resolution",
                "preserve the approved boundary",
                "--evidence",
                "user confirmation after reopening",
            )
            self.assertEqual(resolved_second.returncode, 0, resolved_second.stderr or resolved_second.stdout)
            self.assertEqual(run_flow("validate-packet", packet).returncode, 0)

    def test_checkpoint_invalidation_cannot_skip_a_malformed_latest_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "latest-checkpoint-linkage")
            approve_and_implement(packet)
            second = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "reconciliation",
                "--objective",
                "Reconcile the latest implementation premise",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The current bytes remain aligned",
                "--next-action",
                "Continue the bounded implementation",
                "--stop-condition",
                "Stop on premise drift",
            )
            self.assertEqual(second.returncode, 0, second.stderr or second.stdout)
            recorded = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "A late material interpretation changes AC-1",
                "--source",
                "implementation evidence",
                "--interpretation",
                "retain the current behavior",
                "--interpretation",
                "change the public behavior",
                "--evidence",
                "the outcomes differ",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "confirm the intended behavior",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the late choice.\n", encoding="utf-8")
            reopened = run_flow(
                "transition",
                packet,
                "awaiting-approval",
                "--ambiguity-id",
                "AMB-1",
                "--note",
                "reopen the affected premise",
            )
            self.assertEqual(reopened.returncode, 0, reopened.stderr or reopened.stdout)

            events_path = packet / "events.jsonl"
            events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
            checkpoint_indices = [
                index for index, event in enumerate(events) if event.get("event") == "checkpoint-recorded"
            ]
            self.assertEqual(len(checkpoint_indices), 2)
            previous_checkpoint = events[checkpoint_indices[0]]["payload"]
            previous_digest = "sha256:" + hashlib.sha256(
                json.dumps(
                    previous_checkpoint,
                    ensure_ascii=True,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest()
            events[checkpoint_indices[-1]]["payload"] = []
            invalidation_index = next(
                index for index, event in enumerate(events) if event.get("event") == "checkpoint-invalidated"
            )
            events[invalidation_index]["payload"]["invalidated_checkpoint_sha256"] = previous_digest
            events[invalidation_index + 1]["payload"]["checkpoint_invalidation"][
                "invalidated_checkpoint_sha256"
            ] = previous_digest
            write_events(packet, events)

            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("checkpoint record must use an object payload", invalid.stdout)

    def test_creation_contract_rejects_synchronized_capability_downgrade(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "synchronized-downgrade")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["skill_version"] = "1.0.0+change-set-transition-v1"
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            events[0]["payload"]["skill_version"] = "1.0.0+change-set-transition-v1"
            events[0]["payload"]["creation_contract"]["skill_version"] = "1.0.0+change-set-transition-v1"
            events[0]["payload"]["creation_contract"]["capabilities"] = ["change-set-transition-v1"]
            (packet / "events.jsonl").write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
                encoding="utf-8",
            )
            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("cannot drop its creation capability", invalid.stdout)

        for omitted_field in ("mutation_intent", "design_digest", "continuity_checkpoint", "knowledge_manifest"):
            with self.subTest(omitted_field=omitted_field), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                packet = initialize_quality_packet(root, f"partial-downgrade-{omitted_field}")
                metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
                metadata["skill_version"] = "1.0.0+change-set-transition-v1"
                metadata.pop(omitted_field)
                (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
                events = [
                    json.loads(line)
                    for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()
                ]
                events[0]["payload"]["skill_version"] = "1.0.0+change-set-transition-v1"
                events[0]["payload"].pop("creation_contract")
                (packet / "events.jsonl").write_text(
                    "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
                    encoding="utf-8",
                )

                missing = run_flow("validate-packet", packet)
                self.assertEqual(missing.returncode, 2, missing.stderr or missing.stdout)
                self.assertIn("missing its immutable creation contract", missing.stdout)

                if omitted_field == "knowledge_manifest":
                    event = {
                        "cwd": str(root),
                        "hook_event_name": "PreToolUse",
                        "tool_name": "apply_patch",
                        "tool_input": {
                            "patch": "*** Begin Patch\n*** Update File: product.py\n@@\n-old\n+new\n*** End Patch"
                        },
                    }
                    env = os.environ.copy()
                    env["PLUGIN_ROOT"] = str(ROOT)
                    denied = subprocess.run(
                        [sys.executable, str(HOOK)],
                        cwd=ROOT,
                        check=False,
                        capture_output=True,
                        text=True,
                        input=json.dumps(event),
                        env=env,
                    )
                    self.assertEqual(
                        json.loads(denied.stdout)["hookSpecificOutput"]["permissionDecision"],
                        "deny",
                    )

        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "contract-only-downgrade")
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["skill_version"] = "1.0.0+change-set-transition-v1"
            for field in ("mutation_intent", "design_digest", "continuity_checkpoint", "knowledge_manifest"):
                metadata.pop(field)
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            contract = events[0]["payload"]["creation_contract"]
            events[0]["payload"]["skill_version"] = "1.0.0+change-set-transition-v1"
            contract["skill_version"] = "1.0.0+change-set-transition-v1"
            contract["capabilities"] = ["change-set-transition-v1"]
            contract["mutation_intent"] = None
            (packet / "events.jsonl").write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
                encoding="utf-8",
            )
            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("cannot drop its creation capability", invalid.stdout)

    def test_quality_event_marker_survives_metadata_downgrade_and_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "event-marker-downgrade")
            approve_and_implement(packet)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["skill_version"] = "1.0.0+change-set-transition-v1"
            for field in ("mutation_intent", "design_digest", "continuity_checkpoint", "knowledge_manifest"):
                metadata.pop(field)
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            events[0]["payload"]["skill_version"] = "1.0.0+change-set-transition-v1"
            events[0]["payload"].pop("creation_contract")
            (packet / "events.jsonl").write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
                encoding="utf-8",
            )

            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("quality-shaped packet", invalid.stdout)

    def test_hook_rejects_schema_downgrade_of_immutable_quality_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "schema-downgrade")
            approve_and_implement(packet)
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["schema_version"] = "1.2"
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: product.py\n@@\n-old\n+new\n*** End Patch"
                },
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            denied = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            decision = json.loads(denied.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("requires packet schema 2.0", decision["permissionDecisionReason"])

    def test_schema_independent_quality_provenance_rejects_each_residual_surface(self) -> None:
        event_base: dict[str, object] = {
            "schema_version": "1.0",
            "sequence": 1,
            "event": "packet-created",
            "at": "2026-08-08T00:00:00+00:00",
            "state": "discovering",
            "work_mode": "governed",
            "payload": {"from": None, "to": "discovering"},
        }

        def metadata_field(packet: Path) -> None:
            path = packet / "packet.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["knowledge_manifest"] = None
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

        def metadata_tag(packet: Path) -> None:
            path = packet / "packet.json"
            value = json.loads(path.read_text(encoding="utf-8"))
            value["skill_version"] = "1.0.0+quality-kernel-v1"
            path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

        def quality_event(packet: Path) -> None:
            event = json.loads(json.dumps(event_base))
            event["event"] = "checkpoint-recorded"
            write_events(packet, [event])

        def quality_payload(packet: Path) -> None:
            event = json.loads(json.dumps(event_base))
            event["payload"]["continuity_checkpoint"] = {}
            write_events(packet, [event])

        def creation_contract(packet: Path) -> None:
            event = json.loads(json.dumps(event_base))
            event["payload"]["creation_contract"] = {
                "schema_version": "1.0",
                "skill_version": "1.0.0+change-set-transition-v1",
                "capabilities": ["change-set-transition-v1"],
            }
            write_events(packet, [event])

        def contract_capability(packet: Path) -> None:
            event = json.loads(json.dumps(event_base))
            event["payload"]["creation_contract"] = {
                "schema_version": "1.0",
                "skill_version": "1.0.0+quality-kernel-v1",
                "capabilities": ["quality-kernel-v1"],
            }
            write_events(packet, [event])

        def event_tag(packet: Path) -> None:
            event = json.loads(json.dumps(event_base))
            event["payload"]["skill_version"] = "1.0.0+quality-kernel-v1"
            write_events(packet, [event])

        mutations = {
            "metadata-field": metadata_field,
            "metadata-quality-tag": metadata_tag,
            "quality-event": quality_event,
            "quality-payload": quality_payload,
            "creation-contract": creation_contract,
            "contract-quality-capability": contract_capability,
            "event-quality-tag": event_tag,
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                packet = initialize_legacy_packet(
                    Path(temp),
                    change_id=f"residual-{label}",
                    skill_version="1.0.0",
                )
                mutate(packet)
                invalid = run_flow("validate-packet", packet)
                self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                self.assertIn("quality provenance", invalid.stdout)

    def test_cross_schema_combined_downgrade_is_rejected_by_packet_and_real_hook(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "combined-downgrade")
            metadata_path = packet / "packet.json"
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            metadata["schema_version"] = "1.2"
            metadata["task_type"] = "micro"
            metadata["skill_version"] = "1.0.0"
            metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            events[0]["payload"]["skill_version"] = "1.0.0"
            events[0]["payload"].pop("creation_contract")
            write_events(packet, events)

            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("quality provenance", invalid.stdout)

            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: product.py\n@@\n-old\n+new\n*** End Patch"
                },
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            denied = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            decision = json.loads(denied.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("quality provenance", decision["permissionDecisionReason"])

    def test_packets_without_quality_residue_keep_legacy_compatibility(self) -> None:
        for label, version in (
            ("untagged", "1.0.0"),
            ("change-set-only", "1.0.0+change-set-transition-v1"),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                packet = initialize_quality_packet(Path(temp), f"legacy-{label}")
                set_packet_skill_version(packet, version)
                valid = run_flow("validate-packet", packet)
                self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

        for label, version in (
            ("schema-1.2-untagged", "1.0.0"),
            ("schema-1.2-change-set", "1.0.0+change-set-transition-v1"),
        ):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                packet = initialize_legacy_packet(Path(temp), change_id=label, skill_version=version)
                valid = run_flow("validate-packet", packet)
                self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_read_only_creation_authority_cannot_be_reclassified_in_place(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(
                Path(temp),
                "read-only-authority",
                task_type="read-only-audit",
            )
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["mutation_intent"] = "persistent"
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("read-only-audit cannot declare persistent mutation", invalid.stdout)

            event = {
                "cwd": str(Path(temp)),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: product.py\n@@\n-old\n+new\n*** End Patch"
                },
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            denied = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            decision = json.loads(denied.stdout)["hookSpecificOutput"]
            self.assertEqual(decision["permissionDecision"], "deny")
            self.assertIn("immutable creation authority", decision["permissionDecisionReason"])

    def test_creation_classification_and_authority_envelope_are_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as other_temp:
            packet = initialize_quality_packet(Path(temp), "authority-envelope")
            metadata_path = packet / "packet.json"
            original = json.loads(metadata_path.read_text(encoding="utf-8"))
            mutations = {
                "task_type": "micro",
                "mutation_intent": "none",
                "work_mode": "governed",
                "documentation_profile": "governed",
                "repository_roots": [str(Path(temp).resolve()), str(Path(other_temp).resolve())],
                "authority": "local edits, tests, and delivery",
                "ui_impact": "material",
                "compatibility_required": not original["compatibility_required"],
                "risk_modifiers": ["security"],
            }
            for field, value in mutations.items():
                with self.subTest(field=field):
                    changed = json.loads(json.dumps(original))
                    changed[field] = value
                    metadata_path.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
                    invalid = run_flow("validate-packet", packet)
                    self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                    self.assertIn("creation contract", invalid.stdout)
            metadata_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")

    def test_context_projection_is_recomputed_instead_of_trusting_reported_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "context-projection")
            approve_and_implement(packet)
            readiness = json.loads((packet / "context-readiness.json").read_text(encoding="utf-8"))
            retained = readiness["fingerprint"]
            readiness["tier"] = "T0"
            readiness["outcome"] = "not_applicable"
            readiness["quality_coverage"] = {"routes": ["tampered-route"]}
            self.assertEqual(readiness["fingerprint"], retained)
            (packet / "context-readiness.json").write_text(json.dumps(readiness, indent=2) + "\n", encoding="utf-8")
            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("canonical projection", invalid.stdout)

    def test_dirty_submodule_byte_changes_remain_observable_after_reconciliation(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as child_temp:
            parent = Path(temp)
            child = Path(child_temp)
            initialize_git_repository(parent)
            initialize_git_repository(child)
            added = run_git(parent, "-c", "protocol.file.allow=always", "submodule", "add", "-q", str(child), "sub")
            self.assertEqual(added.returncode, 0, added.stderr or added.stdout)
            self.assertEqual(run_git(parent, "commit", "-qam", "add submodule").returncode, 0)
            packet = initialize_quality_packet(parent, "dirty-submodule")
            approve_and_implement(packet)
            (parent / "sub" / "tracked.txt").write_text("dirty one\n", encoding="utf-8")
            rebound = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "reconciliation",
                "--objective",
                "bind the first dirty submodule state",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "the parent only reports the submodule as dirty",
                "--next-action",
                "continue only while child bytes remain observable",
                "--stop-condition",
                "stop when child bytes change again",
                "--repository-reconciliation",
                "inspected the parent status marker",
            )
            self.assertEqual(rebound.returncode, 0, rebound.stderr or rebound.stdout)
            (parent / "sub" / "tracked.txt").write_text("dirty two\n", encoding="utf-8")
            changed = run_flow("resume-packet", packet)
            self.assertEqual(changed.returncode, 2, changed.stderr or changed.stdout)
            self.assertEqual(json.loads(changed.stdout)["status"], "reconciliation-required")

    def test_quality_event_ledger_exactly_projects_approvals_and_ambiguities(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "interaction-projection")
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "clarify requirements")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            recorded = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "Choose one observable behavior",
                "--source",
                "requirement review",
                "--interpretation",
                "behavior one",
                "--interpretation",
                "behavior two",
                "--evidence",
                "the outcomes differ",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "confirm behavior one",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the material choice.\n", encoding="utf-8")
            resolved = run_flow(
                "resolve-ambiguity",
                packet,
                "--id",
                "AMB-1",
                "--status",
                "user-confirmed",
                "--by",
                "user",
                "--resolution",
                "behavior one",
                "--evidence",
                "user confirmation",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "requirements are ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            original = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            for removed_event, expected in (
                ("approval-recorded", "approval events"),
                ("ambiguity-resolved", "ambiguity events"),
            ):
                remaining = [event for event in original if event["event"] != removed_event]
                for sequence, event in enumerate(remaining, start=1):
                    event["sequence"] = sequence
                (packet / "events.jsonl").write_text(
                    "".join(json.dumps(event, sort_keys=True) + "\n" for event in remaining),
                    encoding="utf-8",
                )
                invalid = run_flow("validate-packet", packet)
                self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                self.assertIn(expected, invalid.stdout)
                (packet / "events.jsonl").write_text(
                    "".join(json.dumps(event, sort_keys=True) + "\n" for event in original),
                    encoding="utf-8",
                )

    def test_event_ledger_replay_rejects_cross_transition_interactions_and_time_reversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "interaction-order")
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "clarify requirements")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            recorded = run_flow(
                "record-ambiguity",
                packet,
                "--summary",
                "Choose one observable behavior",
                "--source",
                "requirement review",
                "--interpretation",
                "behavior one",
                "--interpretation",
                "behavior two",
                "--evidence",
                "the outcomes differ",
                "--materiality",
                "material",
                "--owner",
                "user",
                "--affects",
                "AC-1",
                "--recommendation",
                "confirm behavior one",
            )
            self.assertEqual(recorded.returncode, 0, recorded.stderr or recorded.stdout)
            trace = packet / "trace.md"
            trace.write_text(trace.read_text(encoding="utf-8") + "\nAMB-1 records the material choice.\n", encoding="utf-8")
            resolved = run_flow(
                "resolve-ambiguity",
                packet,
                "--id",
                "AMB-1",
                "--status",
                "user-confirmed",
                "--by",
                "user",
                "--resolution",
                "behavior one",
                "--evidence",
                "user confirmation",
            )
            self.assertEqual(resolved.returncode, 0, resolved.stderr or resolved.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "requirements are ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--approved-by",
                "user",
                "--note",
                "approve the design",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)

            events_path = packet / "events.jsonl"
            original = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]

            for event_name in ("approval-recorded", "ambiguity-resolved"):
                with self.subTest(event_name=event_name):
                    changed = json.loads(json.dumps(original))
                    moved = next(event for event in changed if event["event"] == event_name)
                    changed.remove(moved)
                    approved_index = next(
                        index
                        for index, event in enumerate(changed)
                        if event["event"] == "transition" and event.get("payload", {}).get("to") == "approved"
                    )
                    changed.insert(approved_index + 1, moved)
                    shared_time = changed[0]["at"]
                    for sequence, event in enumerate(changed, start=1):
                        event["sequence"] = sequence
                        event["at"] = shared_time
                    events_path.write_text(
                        "".join(json.dumps(event, sort_keys=True) + "\n" for event in changed),
                        encoding="utf-8",
                    )
                    invalid = run_flow("validate-packet", packet)
                    self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                    self.assertIn("lifecycle state", invalid.stdout)

            equal_time = json.loads(json.dumps(original))
            shared_time = equal_time[0]["at"]
            for event in equal_time:
                event["at"] = shared_time
            events_path.write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in equal_time),
                encoding="utf-8",
            )
            equal_valid = run_flow("validate-packet", packet)
            self.assertEqual(equal_valid.returncode, 0, equal_valid.stderr or equal_valid.stdout)

            reversed_time = json.loads(json.dumps(original))
            reversed_time[-1]["at"] = "2000-01-01T00:00:00+00:00"
            events_path.write_text(
                "".join(json.dumps(event, sort_keys=True) + "\n" for event in reversed_time),
                encoding="utf-8",
            )
            invalid_time = run_flow("validate-packet", packet)
            self.assertEqual(invalid_time.returncode, 2, invalid_time.stderr or invalid_time.stdout)
            self.assertIn("event timestamps must be nondecreasing", invalid_time.stdout)

    def test_persistent_routing_cannot_remove_the_quality_kernel(self) -> None:
        routed = run_flow("route-task", "--task-type", "routine", "--mutation", "persistent")
        self.assertEqual(routed.returncode, 0, routed.stderr or routed.stdout)
        payload = json.loads(routed.stdout)
        self.assertTrue(payload["quality_kernel"]["always_loaded"])
        skills = [item["skill"] for item in payload["routes"]]
        self.assertEqual(skills[0], "repo-context")
        self.assertIn("requirements-design", skills)
        self.assertIn("verification", skills)

    def test_persistent_micro_is_traced_and_nonmutating_micro_can_be_direct(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            persistent = run_flow(
                "init-packet",
                "--root",
                root,
                "--change-id",
                "persistent-micro",
                "--task-type",
                "micro",
                "--objective",
                "Make a persistent bounded change",
            )
            self.assertEqual(persistent.returncode, 0, persistent.stderr or persistent.stdout)
            payload = json.loads(persistent.stdout)
            self.assertEqual(payload["work_mode"], "traced")
            metadata = json.loads((Path(payload["packet"]) / "packet.json").read_text(encoding="utf-8"))
            self.assertIn("quality-kernel-v1", metadata["skill_version"])
            self.assertEqual(metadata["mutation_intent"], "persistent")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            direct = run_flow(
                "init-packet",
                "--root",
                root,
                "--change-id",
                "readonly-micro",
                "--task-type",
                "micro",
                "--objective",
                "Inspect a bounded fact",
                "--mutation",
                "none",
            )
            self.assertEqual(direct.returncode, 0, direct.stderr or direct.stdout)
            self.assertEqual(json.loads(direct.stdout)["work_mode"], "direct")
            self.assertFalse((root / ".codex").exists())

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            read_only = run_flow(
                "init-packet",
                "--root",
                root,
                "--change-id",
                "read-only-default",
                "--task-type",
                "read-only-audit",
                "--objective",
                "Inspect repository behavior without changing it",
            )
            self.assertEqual(read_only.returncode, 0, read_only.stderr or read_only.stdout)
            packet = Path(json.loads(read_only.stdout)["packet"])
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["mutation_intent"], "none")
            contradictory = run_flow(
                "route-task",
                "--task-type",
                "read-only-audit",
                "--mutation",
                "persistent",
            )
            self.assertEqual(contradictory.returncode, 2)
            self.assertIn("cannot declare persistent mutation", contradictory.stdout)

    def test_quality_packet_binds_design_checkpoint_and_knowledge_before_verification(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp))
            approve_and_implement(packet)

            missing_knowledge = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "pre-verification",
                "--objective",
                "Verify the packet",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--active-id",
                "VO-1",
                "--last-evidence",
                "Implementation is complete",
                "--next-action",
                "Enter verification",
                "--stop-condition",
                "Stop on drift",
            )
            self.assertEqual(missing_knowledge.returncode, 0, missing_knowledge.stderr or missing_knowledge.stdout)
            blocked = run_flow("transition", packet, "verifying", "--note", "attempt without knowledge")
            self.assertEqual(blocked.returncode, 2)
            self.assertIn("project-knowledge disposition", blocked.stdout)

            bind_none_and_checkpoint_for_verification(packet)
            verifying = run_flow("transition", packet, "verifying", "--note", "enter verifying")
            self.assertEqual(verifying.returncode, 0, verifying.stderr or verifying.stdout)
            valid = run_flow("validate-packet", packet)
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

            events = [
                json.loads(line)
                for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            verifying_event = next(event for event in reversed(events) if event.get("payload", {}).get("to") == "verifying")
            self.assertEqual(verifying_event["payload"]["continuity_checkpoint"]["trigger"], "pre-verification")
            self.assertIn("change_set", verifying_event["payload"])

            trace = packet / "trace.md"
            trace.write_text(
                trace.read_text(encoding="utf-8").replace(
                    "Run packet verification and adversarial drift checks",
                    "Claim verification without rerunning the checks",
                ),
                encoding="utf-8",
            )
            drift = run_flow("validate-packet", packet)
            self.assertEqual(drift.returncode, 2)
            self.assertIn("continuity checkpoint", drift.stdout)

    def test_engineering_context_fingerprint_drift_blocks_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "context-drift")
            approve_and_implement(packet)
            readiness = json.loads((packet / "context-readiness.json").read_text(encoding="utf-8"))
            readiness["fingerprint"] = "sha256:" + "2" * 64
            (packet / "context-readiness.json").write_text(json.dumps(readiness) + "\n", encoding="utf-8")
            resumed = run_flow("resume-packet", packet)
            self.assertEqual(resumed.returncode, 2)
            self.assertEqual(json.loads(resumed.stdout)["status"], "blocked")
            self.assertIn("engineering context is stale", resumed.stdout)

    def test_governed_design_bytes_are_bound_to_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            created = run_flow(
                "init-packet",
                "--root",
                root,
                "--change-id",
                "design-binding",
                "--task-type",
                "security",
                "--objective",
                "Bind a repository-grounded governed design",
            )
            self.assertEqual(created.returncode, 0, created.stderr or created.stdout)
            packet = Path(json.loads(created.stdout)["packet"])
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            texts: list[str] = []
            instruction_files = {
                "context.md",
                "design.md",
                "execution.md",
                "test-matrix.md",
                "blue-audit.md",
                "red-audit.md",
                "evidence.md",
            }
            for path in sorted(packet.glob("*.md")):
                text = re.sub(r"<[^>\n]+>", "Concrete evidence record", path.read_text(encoding="utf-8"))
                if path.name in instruction_files and "INS-1" not in text:
                    text += "\nINS-1 applies to this governed record.\n"
                path.write_text(text, encoding="utf-8")
                texts.append(text)
            joined = "\n".join(texts)
            metadata["acceptance_ids"] = sorted(set(re.findall(r"\bAC-\d+\b", joined)))
            metadata["scope_ids"] = sorted(set(re.findall(r"\bSC-[DICPOL]\d+\b", joined)))
            metadata["verification_ids"] = sorted(set(re.findall(r"\bVO-\d+\b", joined)))
            scope_projection = "\nScope projection: " + ", ".join(metadata["scope_ids"]) + ".\n"
            for name in ("execution.md", "evidence.md"):
                path = packet / name
                path.write_text(path.read_text(encoding="utf-8") + scope_projection, encoding="utf-8")
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "requirements understood")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "The governed requirement is ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--note",
                "Approve the current design bytes",
                "--approved-by",
                "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            approved_metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            self.assertRegex(approved_metadata["design_digest"], r"^sha256:[0-9a-f]{64}$")

            design = packet / "design.md"
            design.write_text(
                design.read_text(encoding="utf-8").replace(
                    "Concrete evidence record",
                    "Materially different design after approval",
                    1,
                ),
                encoding="utf-8",
            )
            drift = run_flow("validate-packet", packet)
            self.assertEqual(drift.returncode, 2)
            self.assertIn("design changed after its content-bound approval", drift.stdout)

    def test_hook_rehydrates_before_mutation_and_blocks_stale_or_verifying_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "hook-recovery")
            approve_and_implement(packet)
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {
                    "patch": "*** Begin Patch\n*** Update File: src/app.py\n@@\n-old\n+new\n*** End Patch"
                },
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)

            hydrated = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            self.assertEqual(hydrated.returncode, 0, hydrated.stderr or hydrated.stdout)
            output = json.loads(hydrated.stdout)["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", output)
            self.assertIn("DEV_FLOW_RECOVERY", output["additionalContext"])
            self.assertIn("Stop on baseline", output["additionalContext"])

            readiness = json.loads((packet / "context-readiness.json").read_text(encoding="utf-8"))
            readiness["fingerprint"] = "sha256:" + "3" * 64
            (packet / "context-readiness.json").write_text(json.dumps(readiness) + "\n", encoding="utf-8")
            stale = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            self.assertEqual(
                json.loads(stale.stdout)["hookSpecificOutput"]["permissionDecision"],
                "deny",
            )

            readiness["fingerprint"] = "sha256:" + "1" * 64
            (packet / "context-readiness.json").write_text(json.dumps(readiness) + "\n", encoding="utf-8")
            bind_none_and_checkpoint_for_verification(packet)
            verifying = run_flow("transition", packet, "verifying", "--note", "enter verifying")
            self.assertEqual(verifying.returncode, 0, verifying.stderr or verifying.stdout)
            frozen = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            frozen_output = json.loads(frozen.stdout)["hookSpecificOutput"]
            self.assertEqual(frozen_output["permissionDecision"], "deny")
            self.assertIn("implementing state", frozen_output["permissionDecisionReason"])

    def test_material_knowledge_binding_uses_validated_tracked_dossier_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "knowledge-binding")
            manifest, _ = bind_packet_authority_dossier(
                root,
                packet,
                change_id="knowledge-binding",
            )
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "requirements under review")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The verified reusable project contract changes",
                "--root",
                root,
                "--manifest",
                "docs/changes/knowledge-binding/manifest.json",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr or bound.stdout)
            binding = json.loads(bound.stdout)["knowledge_manifest"]
            self.assertEqual(binding["impact"], "update")
            self.assertRegex(binding["sha256"], r"^sha256:[0-9a-f]{64}$")

            value = json.loads(manifest.read_text(encoding="utf-8"))
            value["knowledge"]["rationale"] = "Drifted after packet binding"
            manifest.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            invalid = run_flow("validate-packet", packet)
            self.assertEqual(invalid.returncode, 2)
            self.assertIn("manifest digest drifted", invalid.stdout)

    def test_opted_in_knowledge_authority_must_match_packet_bytes_and_identifier_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "authority-binding")
            _, _, dossier = make_valid_repository(
                root,
                change_id="authority-binding",
                dossier_format="governed",
            )
            bind_governed_authority(dossier)
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "bind exact knowledge authority")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The governed dossier is authoritative",
                "--root",
                root,
                "--manifest",
                "docs/changes/authority-binding/manifest.json",
            )
            self.assertEqual(bound.returncode, 2, bound.stderr or bound.stdout)
            self.assertIn("requirements bytes do not match", bound.stdout)

            manifest_path = dossier / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authority_binding"]["requirements"]["sha256"] = "sha256:" + "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            invalid = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The governed dossier is authoritative",
                "--root",
                root,
                "--manifest",
                "docs/changes/authority-binding/manifest.json",
            )
            self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
            self.assertIn("authority_binding.requirements sha256", invalid.stdout)

    def test_material_quality_binding_requires_authority_but_standalone_legacy_remains_readable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "required-authority")
            make_valid_repository(root, change_id="required-authority")
            standalone = run_flow("validate-knowledge", "--root", root, "--change-id", "required-authority")
            self.assertEqual(standalone.returncode, 0, standalone.stderr or standalone.stdout)
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "bind durable authority")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The durable contract changes",
                "--root",
                root,
                "--manifest",
                "docs/changes/required-authority/manifest.json",
            )
            self.assertEqual(bound.returncode, 2, bound.stderr or bound.stdout)
            self.assertIn("requires a complete authority_binding", bound.stdout)

    def test_quality_authority_rejects_document_path_and_identifier_set_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "authority-projection")
            manifest_path, _ = bind_packet_authority_dossier(
                root,
                packet,
                change_id="authority-projection",
            )
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "bind exact authority")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            original = json.loads(manifest_path.read_text(encoding="utf-8"))

            mutations = {
                "path": lambda value: value["authority_binding"]["requirements"].__setitem__(
                    "path", "other.md"
                ),
                "identifier-set": lambda value: value["authority_binding"]["identifier_sets"].__setitem__(
                    "acceptance_criteria", ["AC-9"]
                ),
            }
            for label, mutate in mutations.items():
                with self.subTest(label=label):
                    changed = json.loads(json.dumps(original))
                    mutate(changed)
                    manifest_path.write_text(json.dumps(changed, indent=2) + "\n", encoding="utf-8")
                    invalid = run_flow(
                        "bind-knowledge",
                        packet,
                        "--impact",
                        "update",
                        "--rationale",
                        "The durable contract changes",
                        "--root",
                        root,
                        "--manifest",
                        "docs/changes/authority-projection/manifest.json",
                    )
                    self.assertEqual(invalid.returncode, 2, invalid.stderr or invalid.stdout)
                    self.assertRegex(invalid.stdout, r"authorit(y|ative).*(path|acceptance_criteria)|authority_binding")

            manifest_path.write_text(json.dumps(original, indent=2) + "\n", encoding="utf-8")
            valid = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The durable contract changes",
                "--root",
                root,
                "--manifest",
                "docs/changes/authority-projection/manifest.json",
            )
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_accepted_material_authority_replays_exact_document_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "accepted-authority")
            _, authority_document = bind_packet_authority_dossier(
                root,
                packet,
                change_id="accepted-authority",
            )
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "review exact authority")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The durable contract changes",
                "--root",
                root,
                "--manifest",
                "docs/changes/accepted-authority/manifest.json",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr or bound.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "the exact requirement is ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--approved-by",
                "user",
                "--note",
                "approve exact requirement and design bytes",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            checkpoint = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "implementation-start",
                "--objective",
                "implement the authority-bound contract",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "the approved packet and dossier bytes match",
                "--next-action",
                "implement and verify the bounded change",
                "--stop-condition",
                "stop on authority or byte drift",
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr or checkpoint.stdout)
            implementing = run_flow("transition", packet, "implementing", "--note", "begin implementation")
            self.assertEqual(implementing.returncode, 0, implementing.stderr or implementing.stdout)
            record_preverification_checkpoint(packet)
            verifying = run_flow("transition", packet, "verifying", "--note", "verify exact authority")
            self.assertEqual(verifying.returncode, 0, verifying.stderr or verifying.stdout)
            accepted = run_flow("transition", packet, "accepted", "--note", "accept verified authority")
            self.assertEqual(accepted.returncode, 0, accepted.stderr or accepted.stdout)

            with authority_document.open("a", encoding="utf-8") as handle:
                handle.write("\nA later edit changes the accepted durable semantics.\n")
            drifted = run_flow("validate-packet", packet)
            self.assertEqual(drifted.returncode, 2, drifted.stderr or drifted.stdout)
            self.assertRegex(drifted.stdout, r"authority_binding\.(requirements|design) sha256|authority binding .* bytes")

    def test_traced_verification_rejects_non_concrete_test_and_commit_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "trace-quality-gates")
            approve_and_implement(packet)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "none",
                "--rationale",
                "This fixture changes no reusable project truth",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr or bound.stdout)
            trace = packet / "trace.md"
            text = trace.read_text(encoding="utf-8")
            text = re.sub(r"(?m)^Black-box:.*$", "Black-box: N/A", text)
            text = re.sub(r"(?m)^White-box:.*$", "White-box: not applicable", text)
            text = re.sub(r"(?m)^Oracle:.*$", "Oracle: not reviewed", text)
            text = re.sub(
                r"(?m)^Commit-ready:.*$",
                "Commit-ready: no; a failing module test and diff audit remain open",
                text,
            )
            trace.write_text(text, encoding="utf-8")
            checkpoint = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "pre-verification",
                "--objective",
                "Attempt verification with incomplete test and commit evidence",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--active-id",
                "VO-1",
                "--last-evidence",
                "The implementation bytes exist but quality evidence is incomplete",
                "--next-action",
                "Enter verification only if the quality gates reject this state",
                "--stop-condition",
                "Stop on incomplete test or commit readiness",
            )
            self.assertEqual(checkpoint.returncode, 0, checkpoint.stderr or checkpoint.stdout)
            blocked = run_flow("transition", packet, "verifying", "--note", "exercise traced gates")
            self.assertEqual(blocked.returncode, 2, blocked.stderr or blocked.stdout)
            self.assertIn("Black-box", blocked.stdout)
            self.assertIn("Oracle", blocked.stdout)
            self.assertIn("Commit-ready", blocked.stdout)

    def test_explicit_knowledge_roots_are_replayed_by_packet_binding(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "custom-knowledge-roots")
            bind_packet_authority_dossier(
                root,
                packet,
                project_root="engineering/current",
                changes_root="engineering/history",
                change_id="custom-knowledge-roots",
            )
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "bind custom roots")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            bound = run_flow(
                "bind-knowledge",
                packet,
                "--impact",
                "update",
                "--rationale",
                "The verified reusable project contract changes",
                "--root",
                root,
                "--project-root",
                "engineering/current",
                "--changes-root",
                "engineering/history",
                "--manifest",
                "engineering/history/custom-knowledge-roots/manifest.json",
            )
            self.assertEqual(bound.returncode, 0, bound.stderr or bound.stdout)
            binding = json.loads(bound.stdout)["knowledge_manifest"]
            self.assertEqual(binding["project_root"], "engineering/current")
            self.assertEqual(binding["changes_root"], "engineering/history")
            valid = run_flow("validate-packet", packet)
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_quality_and_change_set_capability_tokens_remain_additive(self) -> None:
        with self.subTest(capability="quality-only"), tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "quality-only")
            set_packet_skill_version(packet, "1.0.0+quality-kernel-v1")
            approve_and_implement(packet)
            bind_none_and_checkpoint_for_verification(packet)
            verifying = run_flow("transition", packet, "verifying", "--note", "quality-only verifying")
            self.assertEqual(verifying.returncode, 0, verifying.stderr or verifying.stdout)
            valid = run_flow("validate-packet", packet)
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)
            events = [json.loads(line) for line in (packet / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            transition = events[-1]["payload"]
            self.assertIn("continuity_checkpoint", transition)
            self.assertNotIn("change_set", transition)
            metadata = json.loads((packet / "packet.json").read_text(encoding="utf-8"))
            metadata["skill_version"] = "1.0.0"
            (packet / "packet.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
            downgraded = run_flow("validate-packet", packet)
            self.assertEqual(downgraded.returncode, 2, downgraded.stderr or downgraded.stdout)
            self.assertIn("tagged packet creation must exactly match", downgraded.stdout)

        with self.subTest(capability="change-set-only"), tempfile.TemporaryDirectory() as temp:
            packet = initialize_quality_packet(Path(temp), "change-set-only")
            set_packet_skill_version(packet, "1.0.0+change-set-transition-v1")
            awaiting = run_flow("transition", packet, "awaiting-approval", "--note", "requirements understood")
            self.assertEqual(awaiting.returncode, 0, awaiting.stderr or awaiting.stdout)
            ready = run_flow(
                "record-approval",
                packet,
                "requirements",
                "--id",
                "REQ-READY",
                "--by",
                "user",
                "--note",
                "The current semantic revision is ready",
            )
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)
            approved = run_flow(
                "transition",
                packet,
                "approved",
                "--note",
                "Approve the change-set-only design",
                "--approved-by",
                "user",
            )
            self.assertEqual(approved.returncode, 0, approved.stderr or approved.stdout)
            implementing = run_flow("transition", packet, "implementing", "--note", "begin implementation")
            self.assertEqual(implementing.returncode, 0, implementing.stderr or implementing.stdout)
            verifying = run_flow("transition", packet, "verifying", "--note", "change-set-only verifying")
            self.assertEqual(verifying.returncode, 0, verifying.stderr or verifying.stdout)
            valid = run_flow("validate-packet", packet)
            self.assertEqual(valid.returncode, 0, valid.stderr or valid.stdout)

    def test_resume_and_hook_detect_repository_baseline_drift(self) -> None:
        with self.subTest(drift="head"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialize_git_repository(root)
            packet = initialize_quality_packet(root, "head-drift")
            approve_and_implement(packet)
            (root / "tracked.txt").write_text("new committed bytes\n", encoding="utf-8")
            self.assertEqual(run_git(root, "add", "tracked.txt").returncode, 0)
            self.assertEqual(run_git(root, "commit", "-qm", "move head").returncode, 0)
            resumed = run_flow("resume-packet", packet)
            self.assertEqual(resumed.returncode, 2, resumed.stderr or resumed.stdout)
            self.assertIn("repository HEAD drifted", resumed.stdout)

            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"patch": "*** Begin Patch\n*** Update File: tracked.txt\n@@\n-old\n+new\n*** End Patch"},
            }
            env = os.environ.copy()
            env["PLUGIN_ROOT"] = str(ROOT)
            hooked = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            hook_output = json.loads(hooked.stdout)["hookSpecificOutput"]
            self.assertEqual(hook_output["permissionDecision"], "deny")
            self.assertIn("repository HEAD drifted", hook_output["permissionDecisionReason"])

            head = run_git(root, "rev-parse", "HEAD").stdout.strip()
            ordinary_rebind = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "resume",
                "--objective",
                "Resume after an independently changed repository base",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The new commit exists but has not been adopted",
                "--next-action",
                "Review the exact new base",
                "--stop-condition",
                "Stop before silently adopting HEAD",
                "--repository-reconciliation",
                "Inspected the new commit",
                "--accept-head",
                f"{root.resolve()}={head}",
            )
            self.assertEqual(ordinary_rebind.returncode, 2, ordinary_rebind.stderr or ordinary_rebind.stdout)
            self.assertIn("only premise-change or reconciliation", ordinary_rebind.stdout)
            missing_oid = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "reconciliation",
                "--objective",
                "Adopt the reviewed repository base",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The exact commit diff was inspected",
                "--next-action",
                "Continue from the reviewed base",
                "--stop-condition",
                "Stop on any further HEAD change",
                "--repository-reconciliation",
                "Inspected the exact old-to-new commit range",
            )
            self.assertEqual(missing_oid.returncode, 2, missing_oid.stderr or missing_oid.stdout)
            self.assertIn("one exact --accept-head", missing_oid.stdout)
            adopted = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "reconciliation",
                "--objective",
                "Adopt the reviewed repository base",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The exact commit diff was inspected",
                "--next-action",
                "Continue from the reviewed base",
                "--stop-condition",
                "Stop on any further HEAD change",
                "--repository-reconciliation",
                "Inspected the exact old-to-new commit range",
                "--accept-head",
                f"{root.resolve()}={head}",
            )
            self.assertEqual(adopted.returncode, 0, adopted.stderr or adopted.stdout)
            self.assertEqual(run_flow("resume-packet", packet).returncode, 0)

        with self.subTest(drift="worktree"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialize_git_repository(root)
            packet = initialize_quality_packet(root, "worktree-drift")
            approve_and_implement(packet)
            (root / "tracked.txt").write_text("unreconciled worktree bytes\n", encoding="utf-8")
            resumed = run_flow("resume-packet", packet)
            self.assertEqual(resumed.returncode, 2, resumed.stderr or resumed.stdout)
            resume_payload = json.loads(resumed.stdout)
            self.assertEqual(resume_payload["status"], "reconciliation-required")
            self.assertTrue(any("open-slice-delta" in error for error in resume_payload["errors"]))
            self.assertTrue(all("drift" not in error.lower() for error in resume_payload["errors"]))
            silent_rebind = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "resume",
                "--objective",
                "Resume the same bounded implementation slice",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The working tree contains an unreviewed delta",
                "--next-action",
                "Inspect the delta before continuing",
                "--stop-condition",
                "Stop on unexplained worktree changes",
            )
            self.assertEqual(silent_rebind.returncode, 2, silent_rebind.stderr or silent_rebind.stdout)
            self.assertIn("--repository-reconciliation", silent_rebind.stdout)
            reconciled = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "reconciliation",
                "--objective",
                "Resume the same bounded implementation slice",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The exact worktree diff was inspected against AC-1 and SC-D1",
                "--next-action",
                "Continue the bounded implementation",
                "--stop-condition",
                "Stop on further unexplained worktree changes",
                "--repository-reconciliation",
                "Reviewed the exact changed path and retained it inside the active slice",
            )
            self.assertEqual(reconciled.returncode, 0, reconciled.stderr or reconciled.stdout)
            checkpoint = json.loads(reconciled.stdout)["checkpoint"]
            self.assertTrue(checkpoint["repository_reconciliation"]["changed_since_prior"])
            self.assertRegex(
                checkpoint["repository_reconciliation"]["prior_snapshot_sha256"],
                r"^sha256:[0-9a-f]{64}$",
            )
            ready = run_flow("resume-packet", packet)
            self.assertEqual(ready.returncode, 0, ready.stderr or ready.stdout)

            sealed = run_flow(
                "record-checkpoint",
                packet,
                "--trigger",
                "slice-end",
                "--objective",
                "Seal the reviewed implementation slice",
                "--active-id",
                "AC-1",
                "--active-id",
                "SC-D1",
                "--last-evidence",
                "The slice diff and narrow checks were reviewed",
                "--next-action",
                "Prepare the next coherent slice",
                "--stop-condition",
                "Stop on bytes changed after this boundary",
            )
            self.assertEqual(sealed.returncode, 0, sealed.stderr or sealed.stdout)
            (root / "tracked.txt").write_text("bytes changed after sealed boundary\n", encoding="utf-8")
            drifted = run_flow("resume-packet", packet)
            self.assertEqual(drifted.returncode, 2, drifted.stderr or drifted.stdout)
            drift_payload = json.loads(drifted.stdout)
            self.assertEqual(drift_payload["status"], "blocked")
            self.assertIn("sealed checkpoint worktree drift", drifted.stdout)

    def test_repository_snapshot_treats_existing_dirty_bytes_as_baseline_and_hashes_content(self) -> None:
        with self.subTest(change="untracked-content"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialize_git_repository(root)
            (root / "tracked.txt").write_text("pre-existing tracked delta\n", encoding="utf-8")
            (root / "untracked.txt").write_text("first untracked bytes\n", encoding="utf-8")
            packet = initialize_quality_packet(root, "dirty-baseline")
            approve_and_implement(packet)
            initial = run_flow("resume-packet", packet)
            self.assertEqual(initial.returncode, 0, initial.stderr or initial.stdout)
            (root / "untracked.txt").write_text("different untracked bytes\n", encoding="utf-8")
            changed = run_flow("resume-packet", packet)
            self.assertEqual(json.loads(changed.stdout)["status"], "reconciliation-required")

        with self.subTest(change="index-only"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            initialize_git_repository(root)
            (root / "tracked.txt").write_text("staged version one\n", encoding="utf-8")
            self.assertEqual(run_git(root, "add", "tracked.txt").returncode, 0)
            (root / "tracked.txt").write_text("base\n", encoding="utf-8")
            packet = initialize_quality_packet(root, "index-baseline")
            approve_and_implement(packet)
            before_status = run_git(root, "status", "--porcelain=v1").stdout
            (root / "tracked.txt").write_text("staged version two\n", encoding="utf-8")
            self.assertEqual(run_git(root, "add", "tracked.txt").returncode, 0)
            (root / "tracked.txt").write_text("base\n", encoding="utf-8")
            self.assertEqual(run_git(root, "status", "--porcelain=v1").stdout, before_status)
            changed = run_flow("resume-packet", packet)
            self.assertEqual(json.loads(changed.stdout)["status"], "reconciliation-required")

    def test_nested_git_root_and_non_git_observability_are_explicit(self) -> None:
        with self.subTest(root="nested-git"), tempfile.TemporaryDirectory() as temp:
            git_root = Path(temp)
            initialize_git_repository(git_root)
            nested = git_root / "component"
            nested.mkdir()
            (nested / "component.txt").write_text("base component\n", encoding="utf-8")
            self.assertEqual(run_git(git_root, "add", "component/component.txt").returncode, 0)
            self.assertEqual(run_git(git_root, "commit", "-qm", "component base").returncode, 0)
            packet = initialize_quality_packet(nested, "nested-root")
            approve_and_implement(packet)
            checkpoint = json.loads((packet / "packet.json").read_text(encoding="utf-8"))["continuity_checkpoint"]
            self.assertEqual(checkpoint["repository_snapshot"][0]["scope"], "component")
            stable = run_flow("resume-packet", packet)
            self.assertEqual(stable.returncode, 0, stable.stderr or stable.stdout)
            (nested / "component.txt").write_text("changed component\n", encoding="utf-8")
            changed = run_flow("resume-packet", packet)
            self.assertEqual(json.loads(changed.stdout)["status"], "reconciliation-required")

        with self.subTest(root="non-git"), tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            packet = initialize_quality_packet(root, "non-git-observability")
            approve_and_implement(packet)
            resumed = run_flow("resume-packet", packet)
            payload = json.loads(resumed.stdout)
            self.assertEqual(resumed.returncode, 0, resumed.stderr or resumed.stdout)
            self.assertEqual(payload["status"], "ready")
            self.assertTrue(any("not mechanically observable" in warning for warning in payload["warnings"]))
            self.assertFalse(payload["checkpoint"]["repository_snapshot"][0]["observable"])

    def test_pretool_mutation_uses_identity_fast_path_and_templates_match_checkpoint_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as tools_temp:
            root = Path(temp)
            initialize_git_repository(root)
            packet = initialize_quality_packet(root, "hook-fast-path")
            approve_and_implement(packet)
            log = Path(tools_temp) / "git.log"
            wrapper = Path(tools_temp) / "git"
            real_git = shutil.which("git")
            self.assertIsNotNone(real_git)
            wrapper.write_text(
                "#!/bin/sh\nprintf '%s\\n' \"$*\" >> \"$DEV_FLOW_GIT_LOG\"\nexec \"$DEV_FLOW_REAL_GIT\" \"$@\"\n",
                encoding="utf-8",
            )
            wrapper.chmod(0o755)
            env = os.environ.copy()
            env.update(
                {
                    "PLUGIN_ROOT": str(ROOT),
                    "DEV_FLOW_GIT_LOG": str(log),
                    "DEV_FLOW_REAL_GIT": str(real_git),
                    "PATH": f"{tools_temp}{os.pathsep}{env.get('PATH', '')}",
                }
            )
            event = {
                "cwd": str(root),
                "hook_event_name": "PreToolUse",
                "tool_name": "apply_patch",
                "tool_input": {"patch": "*** Begin Patch\n*** Update File: tracked.txt\n@@\n-old\n+new\n*** End Patch"},
            }
            hooked = subprocess.run(
                [sys.executable, str(HOOK)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                input=json.dumps(event),
                env=env,
            )
            self.assertEqual(hooked.returncode, 0, hooked.stderr or hooked.stdout)
            output = json.loads(hooked.stdout)["hookSpecificOutput"]
            self.assertNotIn("permissionDecision", output)
            commands = log.read_text(encoding="utf-8")
            self.assertIn("rev-parse --show-toplevel", commands)
            self.assertIn("rev-parse --verify HEAD", commands)
            self.assertNotRegex(commands, r"(?m)^(?:status|diff|ls-files)\b")

        source = ast.parse(FLOW.read_text(encoding="utf-8"))
        fields: tuple[str, ...] | None = None
        for node in source.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "CONTINUITY_FIELDS" for target in node.targets
            ):
                fields = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(fields)
        self.assertEqual(len(fields or ()), 10)
        for template_name in ("micro-trace.md", "execution.md"):
            template = (ROOT / "skills" / "dev-flow" / "templates" / template_name).read_text(encoding="utf-8")
            for field in fields or ():
                self.assertIn(field, template, f"{template_name} omits {field}")
            self.assertNotIn("eight labeled fields", template)


if __name__ == "__main__":
    unittest.main()
