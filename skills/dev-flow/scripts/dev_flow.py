#!/usr/bin/env python3
"""Stdlib-only runtime for Dev Flow."""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Iterable

import agent_dispatch
import engineering_context
import knowledge_system
import methodology_system
from dependency_contracts import (
    action_reference_scan,
    approval_binds_file,
    matches_dependency_request,
    validate_dependency_approval,
)
from path_contracts import PathContractError, atomic_write_text, contained_path


MIN_CODEX = (0, 147, 0)
SCHEMA_VERSION = "2.0"
SUPPORTED_SCHEMA_VERSIONS = {"1.0", "1.1", "1.2", "2.0"}
READINESS_SCHEMA_VERSIONS = {"1.1", "1.2", "2.0"}
CONTENT_BOUND_SCHEMA_VERSIONS = {"1.2", "2.0"}
WORK_MODES = {"direct", "traced", "governed"}
COLLABORATION_PROFILES = {"execute", "checkpointed", "co-design"}
UI_IMPACTS = {"none", "preserve", "material"}
READINESS_APPROVAL_IDS = {"requirements": "REQ-READY", "ux": "UX-READY"}
AMBIGUITY_MATERIALITIES = {"low", "material", "high-risk"}
AMBIGUITY_OWNERS = {"codex", "user"}
AMBIGUITY_STATUSES = {
    "open",
    "resolved-by-evidence",
    "user-confirmed",
    "safe-assumption",
    "deferred-out-of-scope",
}
STATES = {
    "discovering",
    "awaiting-approval",
    "approved",
    "implementing",
    "verifying",
    "accepted",
    "blocked",
    "archived",
}
TRANSITIONS = {
    "discovering": {"awaiting-approval", "blocked"},
    "awaiting-approval": {"discovering", "approved", "blocked"},
    "approved": {"implementing", "blocked"},
    "implementing": {"verifying", "blocked"},
    "verifying": {"implementing", "accepted", "blocked"},
    "accepted": {"archived"},
    "blocked": {"discovering", "awaiting-approval"},
    "archived": set(),
}
TASK_TYPES = {
    "micro",
    "routine",
    "bugfix",
    "large-feature",
    "large-refactor",
    "migration",
    "security",
    "performance",
    "release-hotfix",
    "read-only-audit",
    "spike",
    "dependency-change",
    "rollback",
}
REQUIREMENTS_ROUTING_RISKS = {
    "accessibility",
    "authentication",
    "authorization",
    "compatibility",
    "data-deletion",
    "migration",
    "persisted-data",
    "privacy",
    "protocol",
    "public-api",
    "schema",
    "security",
    "version-compatibility",
}
ARCHITECTURE_ROUTING_RISKS = {
    "abi",
    "architecture",
    "authentication",
    "authorization",
    "backpressure",
    "cancellation",
    "compatibility",
    "concurrency",
    "distributed-state",
    "entitlement",
    "ffi",
    "idempotency",
    "memory",
    "migration",
    "native-packaging",
    "ordering",
    "performance",
    "persisted-data",
    "platform-lifecycle",
    "privacy",
    "protocol",
    "public-api",
    "recovery",
    "resource-limits",
    "schema",
    "secrets",
    "security",
    "unsafe",
    "untrusted-input",
    "version-compatibility",
}
DIAGNOSIS_ROUTING_RISKS = {"flaky-baseline", "incomplete-reproduction"}
ITERATION_KINDS = {"hypothesis", "repair"}
ITERATION_OUTCOMES = {"failed", "succeeded", "reassessed"}
ITERATION_OWNERS = {
    "architecture-decisions",
    "dependency-decisions",
    "dev-flow",
    "product-ux-discovery",
    "repo-context",
    "requirements-design",
    "systematic-debugging",
    "verification",
}
PACKET_EVENTS = {
    "ambiguity-recorded",
    "ambiguity-resolved",
    "approval-recorded",
    "checkpoint-invalidated",
    "checkpoint-recorded",
    "knowledge-bound",
    "method-selection-recorded",
    "iteration-recorded",
    "iteration-reassessed",
    "packet-created",
    "transition",
}
CHANGE_SET_SKILL_VERSION_TAG = "change-set-transition-v1"
QUALITY_KERNEL_SKILL_VERSION_TAG = "quality-kernel-v1"
METHOD_SELECTION_SKILL_VERSION_TAG = "method-selection-v1"
METHOD_SELECTION_PACKET_SCHEMA_VERSION = "method.selection.packet.v1"
METHOD_SELECTION_RECORD_SCHEMA_VERSION = "1.0"
METHOD_SELECTION_PROJECTION_FIELDS = {
    "schema_version",
    "json_path",
    "json_sha256",
    "markdown_path",
    "markdown_sha256",
    "latest_sequence",
}
METHOD_SELECTION_RECORD_FIELDS = {
    "schema_version",
    "sequence",
    "phase",
    "recorded_at",
    "recorded_state",
    "preliminary",
    "registry_sha256",
    "packet_binding",
    "artifact_bindings",
    "selection",
}
CREATION_CONTRACT_SCHEMA_VERSION = "1.0"
ENGINEERING_CONTEXT_PROJECTION_SCHEMA_VERSION = "1.0"
QUALITY_PROJECTION_FIELDS = {
    "mutation_intent",
    "design_digest",
    "continuity_checkpoint",
    "knowledge_manifest",
}
QUALITY_EVENT_MARKERS = {
    "checkpoint-invalidated",
    "checkpoint-recorded",
    "knowledge-bound",
}
QUALITY_PAYLOAD_FIELDS = {
    "checkpoint_invalidation",
    "continuity_checkpoint",
    "design_digest",
    "knowledge_manifest",
}
CHECKPOINT_INVALIDATION_SCHEMA_VERSION = "1.0"
CHECKPOINT_INVALIDATION_FIELDS = {
    "schema_version",
    "reason",
    "ambiguity_id",
    "invalidated_checkpoint_sha256",
    "from_requirement_revision",
    "new_requirement_revision",
}
ITERATION_CAUSE_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")
FULL_FILES = (
    "context.md",
    "requirements.md",
    "design.md",
    "execution.md",
    "test-matrix.md",
    "blue-audit.md",
    "red-audit.md",
    "evidence.md",
    "decisions.md",
)
FULL_HEADINGS = {
    "context.md": (
        "Objective and authority",
        "Repository facts",
        "Current behavior or reproduction",
        "Constraints and protected behavior",
        "Assumptions and open questions",
    ),
    "requirements.md": (
        "Requirement delta",
        "Acceptance criteria",
        "Non-functional requirements",
        "Compatibility and exclusions",
        "Confirmation record",
    ),
    "design.md": (
        "Decision",
        "Engineering preferences applied",
        "Alternatives",
        "Architecture and failure behavior",
        "Dependency decisions",
        "Change scope",
        "Compatibility, rollout, rollback, and cleanup",
        "Verification obligations",
        "Approval record",
    ),
    "execution.md": (
        "Task graph",
        "Progress ledger",
        "Agent ledger",
        "Decisions and drift",
        "Environment and resource ownership",
        "Findings and repair rounds",
        "Blockers and next ready task",
    ),
    "test-matrix.md": (
        "Dimensions and selection rationale",
        "Resource ownership",
        "Cells",
        "Flaky triage",
        "Teardown and leaked resources",
        "Acceptance and release gates",
    ),
    "blue-audit.md": (
        "Audit brief",
        "Requirement and scope review",
        "Integration and maintainability review",
        "Findings",
        "Disposition",
    ),
    "red-audit.md": (
        "Audit brief",
        "Threat and failure hypotheses",
        "Adversarial checks",
        "Findings",
        "Disposition",
    ),
    "evidence.md": (
        "Acceptance traceability",
        "Commands and results",
        "Audit summary",
        "Test matrix summary",
        "Changed-file accounting",
        "Residual risks and remaining gates",
        "Delivery status",
    ),
    "decisions.md": (
        "Decision ledger",
        "Approval ledger",
        "Source registry",
        "Superseded decisions",
    ),
}
SCHEMA_1_1_HEADINGS = {
    "context.md": (
        "Instruction and convention ledger",
        "Collaboration and readiness",
    ),
    "requirements.md": (
        "User and product outcome",
        "Requirement Ready gate",
    ),
    "design.md": ("Product and UX contract",),
    "evidence.md": ("Instruction, collaboration, and UX evidence",),
}
SCHEMA_1_2_HEADINGS = {
    "context.md": ("Semantic input and ambiguity ownership",),
    "requirements.md": ("Requirement baseline", "Ambiguity ledger"),
    "design.md": ("Requirement baseline and reopening",),
    "blue-audit.md": ("Finding classification and requirement reopening",),
    "red-audit.md": ("Finding classification and requirement reopening",),
    "evidence.md": ("Semantic clarification evidence",),
}
CHANGE_SET_FIELDS = (
    "Intent and protected behavior",
    "Final bytes or read-only target",
    "Changed files",
    "Decisions and drift",
    "Narrow checks",
    "Limits",
)
MICRO_HEADINGS = (
    "Authority and repository facts",
    "Requirement and design",
    "Scope and protected behavior",
    "Progress and decisions",
    "Verification",
    "Blue and red audit",
    "Delivery and residual risk",
)
QUALITY_GOVERNED_HEADINGS = {
    "context.md": ("Quality and capability snapshot",),
    "requirements.md": ("Requirement source and understanding revisions",),
    "design.md": ("Testing and implementation strategy",),
    "execution.md": ("Continuity checkpoint", "Slice and commit readiness", "Knowledge disposition"),
    "test-matrix.md": ("Technique accountability", "Oracle validity review"),
    "evidence.md": ("Engineering-practice and knowledge evidence",),
}
QUALITY_TRACE_HEADINGS = (
    "Requirement source and understanding revisions",
    "Engineering context and quality routes",
    "Continuity checkpoint",
    "Test technique accountability",
    "Knowledge and commit readiness",
)
CONTINUITY_FIELDS = (
    "Trigger",
    "Requirement baseline",
    "Design baseline",
    "Engineering context",
    "Repository baseline",
    "Repository reconciliation",
    "Active objective and slice",
    "Last completed and evidence",
    "Next action and stop condition",
    "Drift review",
)
CONTINUITY_CHECKPOINT_FIELDS = {
    "schema_version",
    "trigger",
    "requirement_revision",
    "requirements_digest",
    "design_digest",
    "engineering_context_fingerprint",
    "repository_snapshot",
    "repository_reconciliation",
    "active_ids",
    "active_objective",
    "last_evidence",
    "next_action",
    "stop_condition",
    "drift",
    "ledger",
    "section_sha256",
    "at",
}
COMMIT_READY_FIELDS = (
    "Status",
    "Slice",
    "Narrow and integration checks",
    "Diff and scope audit",
    "Test-oracle audit",
    "Comment and documentation audit",
    "Delivery authority",
)
CONTINUITY_TRIGGERS = {
    "implementation-start",
    "resume",
    "user-steering",
    "slice-start",
    "slice-end",
    "delegation",
    "reconciliation",
    "premise-change",
    "phase-transition",
    "pre-verification",
    "final-claim",
}
OPEN_CONTINUITY_TRIGGERS = {
    "implementation-start",
    "resume",
    "user-steering",
    "slice-start",
    "reconciliation",
    "premise-change",
}
SEALED_CONTINUITY_TRIGGERS = CONTINUITY_TRIGGERS - OPEN_CONTINUITY_TRIGGERS
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>|\b(?:TODO|TBD|FIXME)\b|^\s*X\s*$", re.IGNORECASE | re.MULTILINE)
ID_PATTERNS = {
    "acceptance": re.compile(r"\bAC-\d+\b"),
    "scope": re.compile(r"\bSC-[DICPOL]\d+\b"),
    "verification": re.compile(r"\bVO-\d+\b"),
    "dependency": re.compile(r"\bDEP-\d+\b"),
    "instruction": re.compile(r"\bINS-\d+\b"),
    "ambiguity": re.compile(r"\bAMB-\d+\b"),
}
STATUS_WORDS = {"PASSED", "FAILED", "FLAKY", "BLOCKED", "NOT RUN", "WAIVED"}
TEST_MATRIX_CELL_RE = re.compile(r"TM-[1-9][0-9]*(?:[A-Z][A-Z0-9]*)?")
TEST_MATRIX_REQUIRED_WORDS = {"yes", "no"}
VERSION_RE = re.compile(r"(?:codex-cli\s+)?(\d+)\.(\d+)\.(\d+)(?:[-+][^\s]+)?")
FEATURE_RE = re.compile(r"^(multi_agent(?:_v2)?|hooks)\s+\S+\s+(true|false)\s*$", re.MULTILINE)


def documentation_family(profile: Any) -> str | None:
    if profile in {"micro", "trace"}:
        return "trace"
    if profile in {"full", "governed"}:
        return "governed"
    return None


def select_work_mode(
    task_type: str,
    risks: Iterable[str],
    requested: str = "auto",
    *,
    persistent_mutation: bool = False,
) -> tuple[str, list[str]]:
    risk_set = engineering_context.canonical_risks(risks)
    governed = engineering_context.GOVERNED_RISKS
    if risk_set & governed or task_type in {"migration", "security", "release-hotfix", "dependency-change", "rollback"}:
        automatic, reasons = "governed", sorted(risk_set & governed) or [task_type]
    elif task_type in {"micro", "spike"} and not persistent_mutation:
        automatic, reasons = "direct", [task_type]
    else:
        automatic, reasons = "traced", ["persistent-mutation", task_type] if persistent_mutation else [task_type]
    if requested == "auto":
        return automatic, reasons
    if requested not in WORK_MODES:
        raise ValueError(f"work mode must be auto or one of {sorted(WORK_MODES)}")
    rank = {"direct": 0, "traced": 1, "governed": 2}
    if rank[requested] < rank[automatic]:
        raise ValueError(f"work mode {requested} cannot downgrade required {automatic} mode")
    return requested, ["explicit-work-mode", *reasons]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def concrete_readiness_records(approvals: Any, kind: str) -> list[dict[str, Any]]:
    if not isinstance(approvals, dict):
        return []
    records = approvals.get(kind, [])
    if not isinstance(records, list):
        return []
    expected_id = READINESS_APPROVAL_IDS[kind]
    concrete: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict) or record.get("id") != expected_id:
            continue
        if (
            all(isinstance(record.get(field), str) and record[field].strip() for field in ("by", "note"))
            and parsed_timestamp(record.get("at")) is not None
        ):
            concrete.append(record)
    return concrete


def concrete_design_record(approvals: Any) -> dict[str, Any] | None:
    if not isinstance(approvals, dict):
        return None
    record = approvals.get("design")
    if not isinstance(record, dict):
        return None
    if (
        all(isinstance(record.get(field), str) and record[field].strip() for field in ("by", "note"))
        and parsed_timestamp(record.get("at")) is not None
    ):
        return record
    return None


def parsed_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def history_times(metadata: dict[str, Any], target_state: str) -> list[dt.datetime]:
    history = metadata.get("history", [])
    if not isinstance(history, list):
        return []
    values = [
        parsed_timestamp(event.get("at"))
        for event in history
        if isinstance(event, dict) and event.get("to") == target_state
    ]
    return [value for value in values if value is not None]


def history_windows(
    metadata: dict[str, Any],
    target_state: str,
    *,
    open_until: dt.datetime,
) -> list[tuple[dt.datetime, dt.datetime]]:
    history = metadata.get("history", [])
    if not isinstance(history, list):
        return []
    windows: list[tuple[dt.datetime, dt.datetime]] = []
    for index, event in enumerate(history):
        if not isinstance(event, dict) or event.get("to") != target_state:
            continue
        start = parsed_timestamp(event.get("at"))
        if start is None:
            continue
        end = open_until
        for later in history[index + 1 :]:
            if not isinstance(later, dict) or later.get("from") != target_state:
                continue
            candidate = parsed_timestamp(later.get("at"))
            if candidate is not None:
                end = candidate
                break
        windows.append((start, end))
    return windows


def requirement_content(packet: Path, profile: Any) -> bytes | None:
    """Return the exact requirement baseline bytes for content-bound packets."""
    family = documentation_family(profile)
    if family == "governed":
        path = packet / "requirements.md"
        return path.read_bytes() if path.is_file() else None
    if family == "trace":
        path = packet / "trace.md"
        if not path.is_file():
            return None
        body = heading_body(path.read_text(encoding="utf-8"), "Requirement and design")
        return body.encode("utf-8") if body is not None else None
    return None


def current_requirements_digest(packet: Path, profile: Any) -> str | None:
    content = requirement_content(packet, profile)
    if content is None:
        return None
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def design_content(packet: Path, profile: Any) -> bytes | None:
    """Return exact design bytes for the quality-kernel approval contract."""
    family = documentation_family(profile)
    if family == "governed":
        path = packet / "design.md"
        return path.read_bytes() if path.is_file() else None
    if family == "trace":
        path = packet / "trace.md"
        if not path.is_file():
            return None
        body = heading_body(path.read_text(encoding="utf-8"), "Requirement and design")
        return body.encode("utf-8") if body is not None else None
    return None


def current_design_digest(packet: Path, profile: Any) -> str | None:
    content = design_content(packet, profile)
    return f"sha256:{hashlib.sha256(content).hexdigest()}" if content is not None else None


def semantic_metadata_errors(
    metadata: dict[str, Any],
    *,
    declared_trace_ids: set[str],
    require_ready: bool,
) -> list[str]:
    """Validate a content-bound ambiguity ledger without trusting container shapes."""
    errors: list[str] = []
    validation_time = parsed_timestamp(utc_now())
    assert validation_time is not None
    awaiting_windows = history_windows(metadata, "awaiting-approval", open_until=validation_time)
    revision = metadata.get("requirement_revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append("packet.json: requirement_revision must be a positive integer")
    digest = metadata.get("requirements_digest")
    if digest is not None and not (
        isinstance(digest, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
    ):
        errors.append("packet.json: requirements_digest must be null or a sha256 digest")

    raw_ids = metadata.get("ambiguity_ids")
    if not isinstance(raw_ids, list):
        errors.append("packet.json: ambiguity_ids must be a list")
        ambiguity_ids: list[Any] = []
    else:
        ambiguity_ids = raw_ids
        if any(not isinstance(value, str) or not ID_PATTERNS["ambiguity"].fullmatch(value) for value in raw_ids):
            errors.append("packet.json: ambiguity_ids must contain only AMB-n identifiers")
        if len(raw_ids) != len(set(value for value in raw_ids if isinstance(value, str))):
            errors.append("packet.json: ambiguity_ids must be unique")

    records = metadata.get("ambiguities")
    if not isinstance(records, list):
        errors.append("packet.json: ambiguities must be a list")
        records = []
    record_ids: list[str] = []
    for index, record in enumerate(records):
        label = f"packet.json: ambiguities[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        ambiguity_id = record.get("id")
        if not isinstance(ambiguity_id, str) or not ID_PATTERNS["ambiguity"].fullmatch(ambiguity_id):
            errors.append(f"{label}.id must be an AMB-n identifier")
        else:
            record_ids.append(ambiguity_id)
            label = f"packet.json: ambiguity {ambiguity_id}"
        for field in ("summary", "source", "recommendation"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"{label} requires non-empty {field}")
        interpretations = record.get("interpretations")
        if not isinstance(interpretations, list) or len(interpretations) < 2 or any(
            not isinstance(value, str) or not value.strip() for value in interpretations
        ):
            errors.append(f"{label} requires at least two non-empty interpretations")
        elif len({value.strip() for value in interpretations}) != len(interpretations):
            errors.append(f"{label} interpretations must be distinct")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or any(not isinstance(value, str) or not value.strip() for value in evidence):
            errors.append(f"{label}.evidence must be a list of non-empty strings")
        materiality = record.get("materiality")
        owner = record.get("owner")
        status = record.get("status")
        if materiality not in AMBIGUITY_MATERIALITIES:
            errors.append(f"{label} has invalid materiality {materiality!r}")
        if owner not in AMBIGUITY_OWNERS:
            errors.append(f"{label} has invalid owner {owner!r}")
        if materiality == "high-risk" and owner != "user":
            errors.append(f"{label} high-risk ambiguity must be user-owned")
        if status not in AMBIGUITY_STATUSES:
            errors.append(f"{label} has invalid status {status!r}")
        created_at = parsed_timestamp(record.get("created_at"))
        if created_at is None:
            errors.append(f"{label} requires a timezone-aware created_at")
        elif created_at > validation_time:
            errors.append(f"{label}.created_at cannot be in the future")
        discovered_revision = record.get("discovered_in_revision")
        if not isinstance(discovered_revision, int) or isinstance(discovered_revision, bool) or discovered_revision < 1:
            errors.append(f"{label}.discovered_in_revision must be a positive integer")
        elif isinstance(revision, int) and discovered_revision > revision:
            errors.append(f"{label}.discovered_in_revision cannot exceed the current requirement revision")

        affected = record.get("affected_ids")
        if not isinstance(affected, list) or any(not isinstance(value, str) for value in affected):
            errors.append(f"{label}.affected_ids must be a list of trace identifiers")
            affected_ids: set[str] = set()
        else:
            affected_ids = set(affected)
            if len(affected) != len(affected_ids):
                errors.append(f"{label}.affected_ids must be unique")
            malformed = sorted(
                value
                for value in affected_ids
                if not any(ID_PATTERNS[kind].fullmatch(value) for kind in ("acceptance", "scope", "verification"))
            )
            if malformed:
                errors.append(f"{label}.affected_ids contains invalid identifiers: {malformed}")
            undeclared = affected_ids - declared_trace_ids
            if undeclared:
                errors.append(f"{label}.affected_ids contains undeclared identifiers: {sorted(undeclared)}")
        if require_ready and not affected_ids:
            errors.append(f"{label} requires at least one affected trace identifier before approval")

        resolution = record.get("resolution")
        if status == "open":
            if resolution is not None:
                errors.append(f"{label} open ambiguity must not have a resolution")
            if require_ready:
                errors.append(f"{label} remains open at Requirement Ready")
            continue
        if not isinstance(resolution, dict):
            errors.append(f"{label} resolved ambiguity requires a resolution object")
            continue
        for field in ("by", "text"):
            if not isinstance(resolution.get(field), str) or not resolution[field].strip():
                errors.append(f"{label}.resolution requires non-empty {field}")
        resolution_at = parsed_timestamp(resolution.get("at"))
        if resolution_at is None:
            errors.append(f"{label}.resolution requires a timezone-aware timestamp")
        else:
            if resolution_at > validation_time:
                errors.append(f"{label}.resolution.at cannot be in the future")
            if created_at is not None and resolution_at < created_at:
                errors.append(f"{label}.resolution cannot predate ambiguity creation")
        resolution_evidence = resolution.get("evidence")
        if not isinstance(resolution_evidence, list) or not resolution_evidence or any(
            not isinstance(value, str) or not value.strip() for value in resolution_evidence
        ):
            errors.append(f"{label}.resolution.evidence requires at least one non-empty item")
        if owner == "user" and status not in {"user-confirmed", "deferred-out-of-scope"}:
            errors.append(f"{label} user-owned ambiguity requires user-confirmed or deferred-out-of-scope status")
        if owner == "user" and resolution_at is not None and not any(
            start <= resolution_at <= end for start, end in awaiting_windows
        ):
            errors.append(f"{label} user-owned resolution must occur during an awaiting-approval window")
        if owner == "codex":
            if status == "resolved-by-evidence":
                pass
            elif status in {"safe-assumption", "deferred-out-of-scope"} and materiality == "low":
                pass
            else:
                errors.append(f"{label} Codex-owned resolution is not authorized for {materiality}/{status}")

    if len(record_ids) != len(set(record_ids)):
        errors.append("packet.json: ambiguity record IDs must be unique")
    if set(value for value in ambiguity_ids if isinstance(value, str)) != set(record_ids):
        errors.append("packet.json: ambiguity_ids must equal ambiguity record IDs")
    return errors


def find_ambiguity(metadata: dict[str, Any], ambiguity_id: str) -> dict[str, Any] | None:
    records = metadata.get("ambiguities", [])
    if not isinstance(records, list):
        return None
    return next(
        (record for record in records if isinstance(record, dict) and record.get("id") == ambiguity_id),
        None,
    )


def declared_trace_ids(metadata: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for field in ("acceptance_ids", "scope_ids", "verification_ids"):
        values = metadata.get(field, [])
        if isinstance(values, list):
            result.update(value for value in values if isinstance(value, str))
    return result


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def plugin_version() -> str:
    manifest = json.loads((plugin_root() / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    return str(manifest["version"])


def packet_skill_version() -> str:
    """Tag new packets with additive, independently detectable capabilities."""
    return (
        f"{plugin_version()}+{CHANGE_SET_SKILL_VERSION_TAG}."
        f"{QUALITY_KERNEL_SKILL_VERSION_TAG}.{METHOD_SELECTION_SKILL_VERSION_TAG}"
    )


def skill_capabilities(value: object) -> set[str]:
    if not isinstance(value, str) or "+" not in value:
        return set()
    build = value.split("+", 1)[1]
    return {token for token in build.split(".") if token}


def has_skill_capability(value: object, capability: str) -> bool:
    return capability in skill_capabilities(value)


def has_change_set_contract(value: object) -> bool:
    return has_skill_capability(value, CHANGE_SET_SKILL_VERSION_TAG)


def has_quality_kernel_contract(value: object) -> bool:
    return has_skill_capability(value, QUALITY_KERNEL_SKILL_VERSION_TAG)


def has_method_selection_contract(value: object) -> bool:
    return has_skill_capability(value, METHOD_SELECTION_SKILL_VERSION_TAG)


def creation_contract(metadata: dict[str, Any]) -> dict[str, Any]:
    """Return the immutable packet classification and authority envelope."""

    return {
        "schema_version": CREATION_CONTRACT_SCHEMA_VERSION,
        "skill_version": metadata.get("skill_version"),
        "capabilities": sorted(skill_capabilities(metadata.get("skill_version"))),
        "task_type": metadata.get("task_type"),
        "mutation_intent": metadata.get("mutation_intent"),
        "work_mode": metadata.get("work_mode"),
        "documentation_profile": metadata.get("documentation_profile"),
        "repository_roots": metadata.get("repository_roots"),
        "authority": metadata.get("authority"),
        "collaboration_profile": metadata.get("collaboration_profile"),
        "ui_impact": metadata.get("ui_impact"),
        "compatibility_required": metadata.get("compatibility_required"),
        "risk_modifiers": metadata.get("risk_modifiers"),
    }


def packet_creation_contract(packet: Path) -> dict[str, Any] | None:
    """Read a new packet's immutable contract without interpreting mutable metadata."""

    ledger = packet / "events.jsonl"
    if not ledger.is_file():
        return None
    try:
        first = next(line for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip())
        event = json.loads(first)
    except (OSError, StopIteration, json.JSONDecodeError):
        return None
    payload = event.get("payload") if isinstance(event, dict) else None
    contract = payload.get("creation_contract") if isinstance(payload, dict) else None
    return contract if isinstance(contract, dict) else None


def packet_has_creation_capability(packet: Path, metadata: dict[str, Any], capability: str) -> bool:
    contract = packet_creation_contract(packet)
    capabilities = contract.get("capabilities") if isinstance(contract, dict) else None
    if isinstance(capabilities, list):
        return capability in capabilities
    return has_skill_capability(metadata.get("skill_version"), capability)


def packet_has_immutable_creation_capability(packet: Path, capability: str) -> bool:
    contract = packet_creation_contract(packet)
    capabilities = contract.get("capabilities") if isinstance(contract, dict) else None
    return isinstance(capabilities, list) and capability in capabilities


def quality_provenance_markers(metadata: dict[str, Any], events: list[dict[str, Any]]) -> set[str]:
    """Find any current-quality provenance before interpreting a packet schema."""

    markers = {f"packet.{field}" for field in QUALITY_PROJECTION_FIELDS if field in metadata}
    if has_quality_kernel_contract(metadata.get("skill_version")):
        markers.add("packet.skill_version.quality-kernel-v1")
    for event in events:
        name = event.get("event")
        if name in QUALITY_EVENT_MARKERS:
            markers.add(f"event.{name}")
        if has_quality_kernel_contract(event.get("skill_version")):
            markers.add("event.skill_version.quality-kernel-v1")
        payload = event.get("payload")
        if not isinstance(payload, dict):
            continue
        if has_quality_kernel_contract(payload.get("skill_version")):
            markers.add("event.payload.skill_version.quality-kernel-v1")
        if name == "packet-created" and "creation_contract" in payload:
            markers.add("event.payload.creation_contract")
        for field in QUALITY_PAYLOAD_FIELDS:
            if field in payload:
                markers.add(f"event.payload.{field}")
        contract = payload.get("creation_contract")
        if isinstance(contract, dict):
            if has_quality_kernel_contract(contract.get("skill_version")):
                markers.add("event.payload.creation_contract.skill_version.quality-kernel-v1")
            capabilities = contract.get("capabilities")
            if isinstance(capabilities, list) and QUALITY_KERNEL_SKILL_VERSION_TAG in capabilities:
                markers.add("event.payload.creation_contract.capabilities.quality-kernel-v1")
        design_approval = payload.get("design_approval")
        if isinstance(design_approval, dict) and "design_digest" in design_approval:
            markers.add("event.payload.design_approval.design_digest")
    return markers


def quality_provenance_errors(packet: Path, metadata: dict[str, Any]) -> list[str]:
    """Fail closed on partial current-quality state before schema dispatch."""

    ledger = packet / "events.jsonl"
    events: list[dict[str, Any]] = []
    ledger_errors: list[str] = []
    if ledger.is_file():
        try:
            lines = ledger.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            lines = []
            ledger_errors.append(f"events.jsonl cannot be read: {exc}")
        for index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                ledger_errors.append(f"events.jsonl:{index}: invalid JSON while resolving quality provenance: {exc}")
                continue
            if isinstance(event, dict):
                events.append(event)
            else:
                ledger_errors.append(f"events.jsonl:{index}: non-object event while resolving quality provenance")
    markers = quality_provenance_markers(metadata, events)
    if not markers:
        return []

    errors = list(ledger_errors)
    creation_payload = events[0].get("payload") if events else None
    contract = creation_payload.get("creation_contract") if isinstance(creation_payload, dict) else None
    capabilities = contract.get("capabilities") if isinstance(contract, dict) else None
    immutable_quality = (
        isinstance(contract, dict)
        and has_quality_kernel_contract(contract.get("skill_version"))
        and isinstance(capabilities, list)
        and QUALITY_KERNEL_SKILL_VERSION_TAG in capabilities
    )
    marker_text = f"; residual markers={sorted(markers)}"
    if metadata.get("schema_version") != "2.0":
        errors.append("quality provenance requires packet schema 2.0" + marker_text)
    if not immutable_quality:
        errors.append("quality provenance requires an immutable current-quality creation contract" + marker_text)
    return errors


def canonical_json_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rendered = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        handle.write(rendered)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def append_packet_event(packet: Path, metadata: dict[str, Any], event: str, payload: dict[str, Any] | None = None) -> None:
    if metadata.get("schema_version") != "2.0":
        return
    ledger = packet / "events.jsonl"
    sequence = 1
    if ledger.is_file():
        sequence += sum(1 for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip())
    record = {
        "schema_version": "1.0",
        "sequence": sequence,
        "event": event,
        "at": metadata.get("updated_at"),
        "state": metadata.get("state"),
        "work_mode": metadata.get("work_mode"),
        "payload": payload or {},
    }
    with ledger.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_packet(packet: Path, metadata: dict[str, Any], event: str, payload: dict[str, Any] | None = None) -> None:
    append_packet_event(packet, metadata, event, payload)
    write_json(packet / "packet.json", metadata)


def methodology_registry_digest(path: Path | None = None) -> str:
    registry = methodology_registry_path(path)
    return "sha256:" + hashlib.sha256(registry.read_bytes()).hexdigest()


def default_method_artifact(owner: str, phase: str) -> str:
    """Map a selected owner to the smallest existing governed-packet artifact."""
    if owner == "repo-context":
        return "context.md"
    if owner in {"requirements-design", "product-ux-discovery"}:
        return "requirements.md" if phase in {"discovery", "requirements"} else "design.md"
    if owner in {"architecture-decisions", "dependency-decisions", "company-data-security"}:
        return "design.md"
    if owner == "systematic-debugging":
        return "execution.md"
    if owner == "verification":
        return "test-matrix.md"
    if owner == "change-review":
        return "blue-audit.md"
    if owner == "delivery-readiness":
        return "evidence.md"
    if phase in {"implementation", "diagnosis", "operations"}:
        return "execution.md"
    if phase in {"verification", "acceptance", "delivery"}:
        return "evidence.md"
    return "design.md"


def render_method_selection_ledger(payload: dict[str, Any]) -> str:
    """Render the machine-readable selection history as a concise owner/artifact ledger."""
    lines = [
        f"# Assurance method selection: {payload.get('change_id', 'unknown')}",
        "",
        "Generated from `method-selection.json`; edit by rerunning `record-methods`.",
        "",
    ]
    records = payload.get("records", [])
    for record in records if isinstance(records, list) else []:
        if not isinstance(record, dict):
            continue
        selection = record.get("selection", {})
        request = selection.get("request", {}) if isinstance(selection, dict) else {}
        lines.extend(
            [
                f"## Selection {record.get('sequence')}: {record.get('phase')}",
                "",
                f"- Recorded: {record.get('recorded_at')} in `{record.get('recorded_state')}`",
                f"- Preliminary: {'yes' if record.get('preliminary') else 'no'}",
                f"- Task/depth: `{request.get('task_type')}` / `{request.get('depth')}`",
                f"- Input risks: {', '.join(request.get('input_risks', [])) or 'none'}",
                f"- Canonical method risks: {', '.join(request.get('risks', [])) or 'none'}",
                f"- Signals: {', '.join(request.get('signals', [])) or 'none'}",
                f"- Registry: `{record.get('registry_sha256')}`",
                "",
                "| Method | Owner | Planned artifact | Purpose |",
                "|---|---|---|---|",
            ]
        )
        bindings = record.get("artifact_bindings", {})
        for method in selection.get("selected_methods", []) if isinstance(selection, dict) else []:
            if not isinstance(method, dict):
                continue
            method_id = str(method.get("id", ""))
            artifacts = bindings.get(method_id, []) if isinstance(bindings, dict) else []
            summary = str(method.get("summary", "")).replace("|", "\\|")
            lines.append(
                f"| `{method_id}` | `{method.get('owner')}` | "
                f"{', '.join(f'`{item}`' for item in artifacts) or 'unbound'} | {summary} |"
            )
        blocked = selection.get("blocked_methods", []) if isinstance(selection, dict) else []
        unresolved = selection.get("unresolved", []) if isinstance(selection, dict) else []
        blocked_ids = [
            f"`{item.get('method_id')}`"
            for item in blocked
            if isinstance(item, dict)
        ]
        lines.extend(
            [
                "",
                f"- Blocked methods: {', '.join(blocked_ids) or 'none'}",
                f"- Unresolved: {' '.join(str(item) for item in unresolved) or 'none'}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def persist_method_selection(
    packet: Path,
    metadata: dict[str, Any],
    *,
    phase: str,
    risks: list[str],
    signals: list[str],
    available: list[str],
    depth: str,
    max_methods: int | None,
    preliminary: bool,
) -> dict[str, Any]:
    """Select, persist, render, and event-bind one packet method record."""
    registry_path = methodology_registry_path()
    registry = methodology_system.read_registry(registry_path)
    selection = methodology_system.select_methods(
        registry,
        repository_root=plugin_root(),
        phase=phase,
        task_type=str(metadata.get("task_type")),
        risks=risks,
        signals=signals,
        available=available,
        depth=depth,
        max_methods=max_methods,
    )
    json_path = packet / "method-selection.json"
    if json_path.is_file():
        payload = read_json(json_path)
    else:
        payload = {
            "schema_version": METHOD_SELECTION_PACKET_SCHEMA_VERSION,
            "change_id": metadata.get("change_id"),
            "records": [],
        }
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("method-selection.json records must be a list")
    selected_methods = selection.get("selected_methods", [])
    artifact_bindings = {
        str(method["id"]): [default_method_artifact(str(method["owner"]), phase)]
        for method in selected_methods
        if isinstance(method, dict) and method.get("id") and method.get("owner")
    }
    recorded_at = utc_now()
    record = {
        "schema_version": METHOD_SELECTION_RECORD_SCHEMA_VERSION,
        "sequence": len(records) + 1,
        "phase": phase,
        "recorded_at": recorded_at,
        "recorded_state": metadata.get("state"),
        "preliminary": preliminary,
        "registry_sha256": methodology_registry_digest(registry_path),
        "packet_binding": {
            "task_type": metadata.get("task_type"),
            "input_risks": sorted(risks),
            "requirement_revision": metadata.get("requirement_revision"),
            "requirements_digest": current_requirements_digest(
                packet, metadata.get("documentation_profile")
            ),
            "design_digest": current_design_digest(
                packet, metadata.get("documentation_profile")
            ),
        },
        "artifact_bindings": artifact_bindings,
        "selection": selection,
    }
    records.append(record)
    write_json(json_path, payload)
    markdown_path = packet / "method-selection.md"
    atomic_write_text(markdown_path, render_method_selection_ledger(payload))
    projection = {
        "schema_version": "1.0",
        "json_path": "method-selection.json",
        "json_sha256": "sha256:" + hashlib.sha256(json_path.read_bytes()).hexdigest(),
        "markdown_path": "method-selection.md",
        "markdown_sha256": "sha256:" + hashlib.sha256(markdown_path.read_bytes()).hexdigest(),
        "latest_sequence": record["sequence"],
    }
    metadata["method_selection"] = projection
    metadata["updated_at"] = recorded_at
    write_packet(
        packet,
        metadata,
        "method-selection-recorded",
        {"record": record, "projection": projection},
    )
    return record


def method_selection_binding_errors(
    packet: Path,
    metadata: dict[str, Any],
    *,
    effective_state: str | None = None,
) -> list[str]:
    """Validate the selection sidecars, event projection, and lifecycle freshness gates."""
    if metadata.get("work_mode") != "governed" or not packet_has_immutable_creation_capability(
        packet, METHOD_SELECTION_SKILL_VERSION_TAG
    ):
        return []
    errors: list[str] = []
    projection = metadata.get("method_selection")
    if not isinstance(projection, dict) or set(projection) != METHOD_SELECTION_PROJECTION_FIELDS:
        return ["packet.json: method_selection must use the exact method-selection-v1 projection"]
    if projection.get("schema_version") != "1.0":
        errors.append("packet.json: method_selection has an unsupported schema_version")
    if projection.get("json_path") != "method-selection.json":
        errors.append("packet.json: method_selection json_path must be method-selection.json")
    if projection.get("markdown_path") != "method-selection.md":
        errors.append("packet.json: method_selection markdown_path must be method-selection.md")
    json_path = packet / "method-selection.json"
    markdown_path = packet / "method-selection.md"
    if not json_path.is_file() or not markdown_path.is_file():
        return [*errors, "governed method selection requires method-selection.json and method-selection.md"]
    observed_json_digest = "sha256:" + hashlib.sha256(json_path.read_bytes()).hexdigest()
    observed_markdown_digest = "sha256:" + hashlib.sha256(markdown_path.read_bytes()).hexdigest()
    if projection.get("json_sha256") != observed_json_digest:
        errors.append("packet.json: method-selection.json digest drifted")
    if projection.get("markdown_sha256") != observed_markdown_digest:
        errors.append("packet.json: method-selection.md digest drifted")
    try:
        payload = read_json(json_path)
    except (OSError, json.JSONDecodeError) as exc:
        return [*errors, f"method-selection.json cannot be read: {exc}"]
    if set(payload) != {"schema_version", "change_id", "records"}:
        errors.append("method-selection.json must use the exact packet schema")
    if payload.get("schema_version") != METHOD_SELECTION_PACKET_SCHEMA_VERSION:
        errors.append("method-selection.json has an unsupported schema_version")
    if payload.get("change_id") != metadata.get("change_id"):
        errors.append("method-selection.json change_id does not match the packet")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        return [*errors, "method-selection.json records must be a non-empty list"]
    rendered = render_method_selection_ledger(payload)
    if markdown_path.read_text(encoding="utf-8") != rendered:
        errors.append("method-selection.md is not the deterministic rendering of method-selection.json")

    event_records: list[dict[str, Any]] = []
    latest_event_projection: Any = None
    ledger = packet / "events.jsonl"
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict) or event.get("event") != "method-selection-recorded":
                continue
            event_payload = event.get("payload")
            if not isinstance(event_payload, dict) or set(event_payload) != {"record", "projection"}:
                errors.append("events.jsonl: method selection event must bind record and projection")
                continue
            record = event_payload.get("record")
            if isinstance(record, dict):
                event_records.append(record)
            else:
                errors.append("events.jsonl: method selection event record must be an object")
            latest_event_projection = event_payload.get("projection")
    if event_records != records:
        errors.append("events.jsonl: method selection records must project exactly to the sidecar")
    if latest_event_projection != projection:
        errors.append("events.jsonl: latest method selection projection does not match packet.json")
    if projection.get("latest_sequence") != len(records):
        errors.append("packet.json: method_selection latest_sequence does not match the record count")

    valid_records: list[dict[str, Any]] = []
    phase_record_states = {
        "design": "awaiting-approval",
        "verification": "implementing",
        "review": "verifying",
    }
    for index, record in enumerate(records, start=1):
        label = f"method-selection.json record {index}"
        if not isinstance(record, dict) or set(record) != METHOD_SELECTION_RECORD_FIELDS:
            errors.append(f"{label} must use the exact record schema")
            continue
        if record.get("schema_version") != METHOD_SELECTION_RECORD_SCHEMA_VERSION:
            errors.append(f"{label} has an unsupported schema_version")
        if record.get("sequence") != index:
            errors.append(f"{label} sequence must be contiguous from 1")
        if parsed_timestamp(record.get("recorded_at")) is None:
            errors.append(f"{label} requires a timezone-aware recorded_at")
        if not isinstance(record.get("registry_sha256"), str) or re.fullmatch(
            r"sha256:[0-9a-f]{64}", record["registry_sha256"]
        ) is None:
            errors.append(f"{label} registry_sha256 must be an exact SHA-256 digest")
        if not isinstance(record.get("preliminary"), bool):
            errors.append(f"{label} preliminary must be boolean")
        phase = record.get("phase")
        if phase not in phase_record_states:
            errors.append(f"{label} phase must be design, verification, or review")
        expected_recorded_state = (
            "discovering" if record.get("preliminary") is True else phase_record_states.get(phase)
        )
        if record.get("recorded_state") != expected_recorded_state:
            errors.append(f"{label} recorded_state does not match its lifecycle gate")
        if record.get("preliminary") is True and phase != "design":
            errors.append(f"{label} preliminary selection is only valid for design")
        selection = record.get("selection")
        if not isinstance(selection, dict) or selection.get("schema_version") != methodology_system.OUTPUT_SCHEMA:
            errors.append(f"{label} must bind a {methodology_system.OUTPUT_SCHEMA} selection")
            continue
        request = selection.get("request")
        if not isinstance(request, dict) or request.get("phase") != record.get("phase"):
            errors.append(f"{label} phase does not match the selection request")
        if (
            isinstance(request, dict)
            and record.get("registry_sha256") == methodology_registry_digest()
        ):
            try:
                replayed = methodology_system.select_methods(
                    methodology_system.read_registry(methodology_registry_path()),
                    repository_root=plugin_root(),
                    phase=str(request.get("phase")),
                    task_type=str(request.get("task_type")),
                    risks=list(request.get("input_risks", [])),
                    signals=list(request.get("signals", [])),
                    available=list(request.get("available_prerequisites", [])),
                    depth=str(request.get("depth")),
                    max_methods=(
                        selection.get("context_budget", {}).get("limit")
                        if isinstance(selection.get("context_budget"), dict)
                        else None
                    ),
                )
            except (TypeError, ValueError, methodology_system.MethodologyContractError) as exc:
                errors.append(f"{label} cannot replay its deterministic selection: {exc}")
            else:
                if replayed != selection:
                    errors.append(f"{label} does not match deterministic selector replay")
        binding = record.get("packet_binding")
        if not isinstance(binding, dict) or set(binding) != {
            "task_type",
            "input_risks",
            "requirement_revision",
            "requirements_digest",
            "design_digest",
        }:
            errors.append(f"{label} packet_binding must use the exact schema")
        elif isinstance(request, dict):
            if binding.get("input_risks") != request.get("input_risks"):
                errors.append(f"{label} packet_binding input_risks do not match the selection")
            if not isinstance(binding.get("requirement_revision"), int) or isinstance(
                binding.get("requirement_revision"), bool
            ) or binding["requirement_revision"] < 1:
                errors.append(f"{label} packet_binding requirement_revision must be positive")
            for digest_field in ("requirements_digest", "design_digest"):
                if not isinstance(binding.get(digest_field), str) or re.fullmatch(
                    r"sha256:[0-9a-f]{64}", binding[digest_field]
                ) is None:
                    errors.append(f"{label} packet_binding {digest_field} must be an exact SHA-256 digest")
        selected = selection.get("selected_methods")
        selected_ids = {
            item.get("id")
            for item in selected
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        } if isinstance(selected, list) else set()
        bindings = record.get("artifact_bindings")
        if not isinstance(bindings, dict) or set(bindings) != selected_ids:
            errors.append(f"{label} artifact_bindings must map every selected method exactly once")
        else:
            for method_id, paths in bindings.items():
                if not isinstance(paths, list) or not paths or any(
                    not isinstance(path, str) or path not in FULL_FILES for path in paths
                ):
                    errors.append(f"{label} artifact binding for {method_id} is invalid")
        valid_records.append(record)

    state = effective_state or metadata.get("state")
    required_phases = {
        "approved": ("design",),
        "implementing": ("design",),
        "verifying": ("design", "verification"),
        "accepted": ("design", "verification", "review"),
        "archived": ("design", "verification", "review"),
    }.get(str(state), ())
    if not required_phases:
        return errors
    trigger_states = phase_record_states
    current_registry_digest = methodology_registry_digest()
    current_requirement_digest = current_requirements_digest(
        packet, metadata.get("documentation_profile")
    )
    current_design = current_design_digest(packet, metadata.get("documentation_profile"))
    expected_risks, _, unknown_risks = methodology_system.normalize_risks(
        methodology_system.read_registry(methodology_registry_path())["vocabulary"],
        [
            value
            for value in metadata.get("risk_modifiers", [])
            if isinstance(value, str)
        ],
    )
    if unknown_risks:
        errors.append(f"packet risks lack a methodology translation: {unknown_risks}")
    for phase in required_phases:
        candidates = [
            record
            for record in valid_records
            if record.get("phase") == phase and record.get("preliminary") is False
        ]
        if not candidates:
            errors.append(f"method selection gate requires a non-preliminary {phase} record")
            continue
        latest = candidates[-1]
        trigger_times = history_times(metadata, trigger_states[phase])
        recorded_at = parsed_timestamp(latest.get("recorded_at"))
        if trigger_times and (recorded_at is None or recorded_at < max(trigger_times)):
            errors.append(f"{phase} method selection predates the current lifecycle entry")
        if latest.get("registry_sha256") != current_registry_digest:
            errors.append(f"{phase} method selection is stale against the methodology registry")
        binding = latest.get("packet_binding", {})
        if isinstance(binding, dict):
            if binding.get("task_type") != metadata.get("task_type"):
                errors.append(f"{phase} method selection task_type drifted")
            if binding.get("requirement_revision") != metadata.get("requirement_revision"):
                errors.append(f"{phase} method selection requirement revision drifted")
            if binding.get("requirements_digest") != current_requirement_digest:
                errors.append(f"{phase} method selection requirement bytes drifted")
            if binding.get("design_digest") != current_design:
                errors.append(f"{phase} method selection design bytes drifted")
        selection = latest.get("selection", {})
        request = selection.get("request", {}) if isinstance(selection, dict) else {}
        request_risks = set(request.get("risks", [])) if isinstance(request, dict) else set()
        if not set(expected_risks).issubset(request_risks):
            errors.append(f"{phase} method selection does not cover current packet risks")
        foundations = selection.get("foundation", []) if isinstance(selection, dict) else []
        if not any(
            isinstance(entry, dict) and entry.get("status") in {"selected", "selected-shared"}
            for entry in foundations
        ):
            errors.append(f"{phase} method selection did not satisfy its phase foundation")
    return errors


def run(command: list[str], cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=timeout)


def parse_version(text: str) -> tuple[int, int, int]:
    match = VERSION_RE.search(text.strip())
    if not match:
        raise ValueError(f"cannot parse Codex version from {text.strip()!r}")
    return tuple(int(part) for part in match.groups())


def codex_preflight(args: argparse.Namespace) -> int:
    capability_issues: list[str] = []
    warnings: list[str] = []
    dispatch_registry_ready = False
    binary = args.codex or shutil.which("codex")
    version_text = args.version_output
    features_text: str | None = None

    try:
        if args.features_output_file:
            features_text = args.features_output_file.read_text(encoding="utf-8")
        if version_text is None:
            if not binary:
                raise RuntimeError("Codex CLI was not found on PATH")
            result = run([binary, "--version"])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            version_text = result.stdout
        if features_text is None:
            if not binary:
                raise RuntimeError("Codex CLI was not found on PATH")
            result = run([binary, "features", "list"])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            features_text = result.stdout
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        capability_issues.append(str(exc))

    actual: tuple[int, int, int] | None = None
    try:
        actual = parse_version(version_text or "")
        if actual < MIN_CODEX:
            capability_issues.append(f"Codex {'.'.join(map(str, actual))} is below delegation-tested 0.147.0")
    except ValueError as exc:
        capability_issues.append(str(exc))

    features = dict(FEATURE_RE.findall(features_text or ""))
    for feature in ("multi_agent", "multi_agent_v2", "hooks"):
        if features.get(feature) != "true":
            capability_issues.append(f"Codex feature {feature} is not enabled")

    try:
        agent_dispatch.load_registry()
        dispatch_registry_ready = True
    except (OSError, json.JSONDecodeError, agent_dispatch.DispatchContractError) as exc:
        capability_issues.append(f"agent dispatch registry is invalid: {exc}")

    config_path = args.config or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    effective: dict[str, Any] = {}
    if not args.skip_config:
        try:
            effective = tomllib.loads(config_path.read_text(encoding="utf-8"))
            feature_config = effective.get("features", {})
            if not isinstance(feature_config, dict):
                raise ValueError("config [features] must be a table")
            if feature_config.get("multi_agent_v2") is not True:
                capability_issues.append("config must set [features].multi_agent_v2 = true for delegation")
            if feature_config.get("multi_agent") is not True:
                capability_issues.append("config must set [features].multi_agent = true for delegation")
            if feature_config.get("hooks") is not True:
                capability_issues.append("config must set [features].hooks = true for governed hooks")
            agent_config = effective.get("agents", {})
            if not isinstance(agent_config, dict):
                raise ValueError("config [agents] must be a table")
            limit = agent_config.get("max_concurrent_threads_per_session")
            if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
                capability_issues.append("config must set a positive [agents].max_concurrent_threads_per_session for delegation")
            if isinstance(feature_config.get("multi_agent_v2"), dict):
                capability_issues.append("obsolete [features.multi_agent_v2] table is not supported")
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            capability_issues.append(f"cannot read Codex config {config_path}: {exc}")

    if not args.tool_surface_confirmed:
        capability_issues.append("The active root must confirm the collaboration tools before delegation")

    errors = capability_issues if args.require_delegation else []
    if not args.require_delegation:
        warnings.extend(capability_issues)
    delegation_available = not capability_issues
    status = "blocked" if errors else "ready" if delegation_available else "degraded"

    return emit(
        {
            "status": status,
            "codex_binary": binary,
            "actual_version": ".".join(map(str, actual)) if actual else None,
            "features": {name: features.get(name) for name in ("multi_agent", "multi_agent_v2", "hooks")},
            "config": str(config_path),
            "capabilities": {
                "core_workflow": True,
                "delegation": delegation_available,
                "agent_dispatch": dispatch_registry_ready,
                "governed_hooks": features.get("hooks") == "true",
            },
            "required_capability": "delegation" if args.require_delegation else "core-workflow",
            "errors": errors,
            "warnings": warnings,
        },
        0 if not errors else 2,
    )


def git_state(root: Path) -> str:
    result = run(["git", "status", "--short", "--branch"], cwd=root)
    return result.stdout.strip() if result.returncode == 0 else "not-a-git-repository"


def run_bytes(command: list[str], cwd: Path, timeout: int = 60) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, timeout=timeout)


def hash_untracked_bytes(digest: Any, root: Path, payload: bytes) -> None:
    for raw_path in sorted(value for value in payload.split(b"\0") if value):
        digest.update(b"\0path\0" + raw_path + b"\0")
        if raw_path.startswith(b"/") or b".." in raw_path.split(b"/"):
            digest.update(b"invalid-path")
            continue
        candidate = root / os.fsdecode(raw_path)
        try:
            info = candidate.lstat()
        except OSError:
            digest.update(b"missing")
            continue
        digest.update(str(stat.S_IFMT(info.st_mode)).encode("ascii") + b"\0")
        if stat.S_ISLNK(info.st_mode):
            try:
                digest.update(b"symlink\0" + os.fsencode(os.readlink(candidate)))
            except OSError:
                digest.update(b"unreadable-symlink")
        elif stat.S_ISREG(info.st_mode):
            try:
                with candidate.open("rb") as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError:
                digest.update(b"unreadable-file")
        else:
            digest.update(f"special:{info.st_size}:{info.st_mtime_ns}".encode("ascii"))


def submodule_worktree_payload(git_root: Path, scope: str) -> tuple[bytes, list[str]]:
    """Capture changed bytes inside populated submodules, including nested ones."""

    payload = bytearray()
    errors: list[str] = []
    seen: set[Path] = set()

    def visit(parent: Path, prefix: str, restrict: str | None) -> None:
        modules = parent / ".gitmodules"
        if not modules.is_file():
            return
        configured = run_bytes(
            ["git", "config", "--file", ".gitmodules", "--null", "--get-regexp", r"^submodule\..*\.path$"],
            parent,
        )
        if configured.returncode not in {0, 1}:
            errors.append(f"cannot inspect submodule declarations for {parent}")
            return
        entries: list[str] = []
        for raw in configured.stdout.split(b"\0"):
            if not raw or b"\n" not in raw:
                continue
            _, raw_path = raw.split(b"\n", 1)
            entries.append(os.fsdecode(raw_path))
        for relative_text in sorted(entries):
            relative = Path(relative_text)
            if relative.is_absolute() or ".." in relative.parts:
                errors.append(f"submodule path is outside its repository: {relative_text}")
                continue
            combined = (Path(prefix) / relative).as_posix() if prefix else relative.as_posix()
            if restrict not in {None, "."}:
                restrict_path = Path(restrict)
                combined_path = Path(combined)
                if not (combined_path == restrict_path or combined_path.is_relative_to(restrict_path)):
                    continue
            candidate = (parent / relative).resolve()
            if candidate in seen or not candidate.is_dir():
                continue
            seen.add(candidate)
            top = run_bytes(["git", "rev-parse", "--show-toplevel"], candidate)
            if top.returncode or Path(os.fsdecode(top.stdout.strip())).resolve() != candidate:
                errors.append(f"populated submodule cannot be inspected: {combined}")
                continue
            commands = (
                ["git", "rev-parse", "--verify", "HEAD"],
                ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none"],
                ["git", "diff", "--cached", "--binary", "--no-ext-diff", "--no-renames", "--submodule=diff"],
                ["git", "diff", "--binary", "--no-ext-diff", "--no-renames", "--submodule=diff"],
                ["git", "ls-files", "--others", "--exclude-standard", "-z"],
            )
            results = [run_bytes(command, candidate) for command in commands]
            if any(result.returncode for result in results):
                errors.append(f"cannot inspect populated submodule bytes: {combined}")
                continue
            payload.extend(b"\0submodule\0" + os.fsencode(combined) + b"\0")
            for label, result in zip((b"head", b"status", b"staged", b"unstaged"), results[:4], strict=True):
                payload.extend(b"\0" + label + b"\0" + result.stdout)
            child_digest = hashlib.sha256()
            hash_untracked_bytes(child_digest, candidate, results[4].stdout)
            payload.extend(b"\0untracked\0" + child_digest.digest())
            visit(candidate, combined, None)

    visit(git_root, "", scope)
    return bytes(payload), errors


def repository_identities(metadata: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Resolve canonical repository roots and Git identities without scanning bytes."""

    roots = metadata.get("repository_roots")
    if not isinstance(roots, list) or not roots or any(not isinstance(value, str) for value in roots):
        return [], ["packet.json: repository_roots must be a non-empty string list"]
    canonical = sorted({str(Path(value).resolve()) for value in roots})
    if len(canonical) != len(roots):
        return [], ["packet.json: repository_roots must be unique after canonicalization"]
    identities: list[dict[str, Any]] = []
    errors: list[str] = []
    for root_text in canonical:
        root = Path(root_text)
        if not root.is_dir():
            errors.append(f"repository root is unavailable: {root_text}")
            continue
        top = run_bytes(["git", "rev-parse", "--show-toplevel"], root)
        if top.returncode:
            identities.append(
                {
                    "root": str(root),
                    "vcs": "none",
                    "git_root": None,
                    "scope": ".",
                    "head": None,
                    "observable": False,
                }
            )
            continue
        try:
            git_root = Path(os.fsdecode(top.stdout.strip())).resolve()
            relative = root.relative_to(git_root)
        except (OSError, ValueError) as exc:
            errors.append(f"cannot resolve Git identity for {root}: {exc}")
            continue
        head_result = run_bytes(["git", "rev-parse", "--verify", "HEAD"], root)
        head = os.fsdecode(head_result.stdout.strip()) if head_result.returncode == 0 else "unborn"
        identities.append(
            {
                "root": str(root),
                "vcs": "git",
                "git_root": str(git_root),
                "scope": relative.as_posix() if relative.parts else ".",
                "head": head,
                "observable": True,
            }
        )
    return identities, errors


def repository_snapshot(metadata: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    """Capture exact local source identity without persisting source bytes.

    The packet is ignored local state, but the snapshot still stores only a
    digest and a bounded path inventory. Pre-existing user changes are part of
    the checkpoint; only later drift requires reconciliation.
    """

    identities, errors = repository_identities(metadata)
    if errors:
        return [], errors
    snapshots: list[dict[str, Any]] = []
    for identity in identities:
        root = Path(str(identity["root"]))
        if identity["vcs"] == "none":
            snapshots.append(
                {
                    **identity,
                    "worktree_sha256": None,
                    "changed_path_count": 0,
                    "changed_paths": [],
                    "paths_truncated": False,
                }
            )
            continue
        git_root = Path(str(identity["git_root"]))
        head = str(identity["head"])
        scope = str(identity["scope"])
        pathspec = ["--", scope]
        status = run_bytes(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all", "--ignore-submodules=none", *pathspec],
            git_root,
        )
        if status.returncode:
            errors.append(f"cannot inspect Git worktree for {root}: {os.fsdecode(status.stderr).strip()}")
            continue
        tracked_command = ["git", "diff", "--name-only", "-z"]
        if head != "unborn":
            tracked_command.append("HEAD")
        else:
            tracked_command.extend(("--cached",))
        tracked_command.extend(pathspec)
        tracked = run_bytes(tracked_command, git_root)
        staged = run_bytes(
            ["git", "diff", "--cached", "--binary", "--no-ext-diff", "--no-renames", "--submodule=diff", *pathspec],
            git_root,
        )
        unstaged = run_bytes(
            ["git", "diff", "--binary", "--no-ext-diff", "--no-renames", "--submodule=diff", *pathspec],
            git_root,
        )
        untracked = run_bytes(["git", "ls-files", "--others", "--exclude-standard", "-z", *pathspec], git_root)
        if tracked.returncode or staged.returncode or unstaged.returncode or untracked.returncode:
            errors.append(f"cannot inventory Git bytes for {root}")
            continue
        raw_paths = sorted(
            {
                value
                for payload in (tracked.stdout, untracked.stdout)
                for value in payload.split(b"\0")
                if value
            }
        )
        digest = hashlib.sha256()
        digest.update(b"dev-flow-worktree-v2\0")
        digest.update(status.stdout)
        digest.update(b"\0staged\0" + staged.stdout)
        digest.update(b"\0unstaged\0" + unstaged.stdout)
        hash_untracked_bytes(digest, git_root, untracked.stdout)
        submodule_payload, submodule_errors = submodule_worktree_payload(git_root, scope)
        if submodule_errors:
            errors.extend(submodule_errors)
            continue
        digest.update(submodule_payload)
        displays = [value.decode("utf-8", "backslashreplace") for value in raw_paths[:200]]
        snapshots.append(
            {
                **identity,
                "worktree_sha256": "sha256:" + digest.hexdigest(),
                "changed_path_count": len(raw_paths),
                "changed_paths": displays,
                "paths_truncated": len(raw_paths) > len(displays),
            }
        )
    return snapshots, errors


def repository_snapshot_summary(snapshots: object) -> str:
    if not isinstance(snapshots, list):
        return "invalid"
    parts: list[str] = []
    for item in snapshots:
        if not isinstance(item, dict):
            continue
        if item.get("vcs") == "git":
            parts.append(
                f"{item.get('root')} at {item.get('head')}; {item.get('worktree_sha256')}; "
                f"changed paths={item.get('changed_path_count')}"
            )
        else:
            parts.append(f"{item.get('root')} (non-Git; byte drift not mechanically observable)")
    return " | ".join(parts)


def repository_snapshot_digest(snapshots: object) -> str | None:
    if not isinstance(snapshots, list):
        return None
    payload = json.dumps(snapshots, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def repository_snapshot_change_kinds(before: object, after: object) -> set[str]:
    if not isinstance(before, list) or not isinstance(after, list):
        return {"identity", "head", "worktree"}
    previous = {item.get("root"): item for item in before if isinstance(item, dict)}
    current = {item.get("root"): item for item in after if isinstance(item, dict)}
    if set(previous) != set(current):
        return {"identity", "head", "worktree"}
    changes: set[str] = set()
    for root in previous:
        left, right = previous[root], current[root]
        if (
            left.get("vcs"),
            left.get("git_root"),
            left.get("scope"),
            left.get("observable"),
        ) != (
            right.get("vcs"),
            right.get("git_root"),
            right.get("scope"),
            right.get("observable"),
        ):
            changes.add("identity")
        if left.get("head") != right.get("head"):
            changes.add("head")
        if left.get("worktree_sha256") != right.get("worktree_sha256"):
            changes.add("worktree")
    return changes


def repository_head_changes(before: object, after: object) -> dict[str, str]:
    """Return the exact current HEAD required to accept each changed Git root."""

    if not isinstance(before, list) or not isinstance(after, list):
        return {}
    previous = {item.get("root"): item for item in before if isinstance(item, dict)}
    current = {item.get("root"): item for item in after if isinstance(item, dict)}
    changed: dict[str, str] = {}
    for root in sorted(set(previous) & set(current)):
        left, right = previous[root], current[root]
        if left.get("head") == right.get("head") or right.get("vcs") != "git":
            continue
        if isinstance(root, str) and isinstance(right.get("head"), str):
            changed[root] = right["head"]
    return changed


def parse_accepted_heads(values: Iterable[str]) -> tuple[dict[str, str], list[str]]:
    accepted: dict[str, str] = {}
    errors: list[str] = []
    for raw in values:
        if "=" not in raw:
            errors.append("--accept-head must use ROOT=OID")
            continue
        root_text, oid = raw.rsplit("=", 1)
        try:
            root = str(Path(root_text).resolve())
        except OSError as exc:
            errors.append(f"--accept-head root cannot be resolved: {root_text}: {exc}")
            continue
        if root in accepted:
            errors.append(f"--accept-head repeats repository root: {root}")
            continue
        if oid != "unborn" and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None:
            errors.append(f"--accept-head requires an exact Git OID for {root}")
            continue
        accepted[root] = oid
    return accepted, errors


def repository_reconciliation_summary(value: object) -> str:
    if not isinstance(value, dict):
        return "invalid"
    kinds = value.get("change_kinds")
    kinds_text = ",".join(kinds) if isinstance(kinds, list) and kinds else "none"
    heads = value.get("accepted_heads")
    if isinstance(heads, dict) and heads:
        heads_text = ", ".join(f"{root}={oid}" for root, oid in sorted(heads.items()))
    else:
        heads_text = "none"
    return f"changes={kinds_text}; accepted heads={heads_text}; evidence={value.get('evidence')}"


def repository_snapshot_drift_errors(
    metadata: dict[str, Any],
    expected: object,
    *,
    check_worktree: bool,
) -> list[str]:
    required_keys = {
        "root",
        "vcs",
        "git_root",
        "scope",
        "head",
        "observable",
        "worktree_sha256",
        "changed_path_count",
        "changed_paths",
        "paths_truncated",
    }
    if not isinstance(expected, list) or not expected:
        return ["packet.json: continuity checkpoint requires a repository snapshot"]
    if any(not isinstance(item, dict) or set(item) != required_keys for item in expected):
        return ["packet.json: continuity checkpoint repository snapshot has an invalid schema"]
    observed, observation_errors = (
        repository_snapshot(metadata)
        if check_worktree
        else repository_identities(metadata)
    )
    if observation_errors:
        return observation_errors
    expected_by_root = {item.get("root"): item for item in expected if isinstance(item.get("root"), str)}
    observed_by_root = {item.get("root"): item for item in observed if isinstance(item.get("root"), str)}
    if set(expected_by_root) != set(observed_by_root):
        return ["repository roots drifted from the continuity checkpoint"]
    errors: list[str] = []
    for root in sorted(expected_by_root):
        before = expected_by_root[root]
        current = observed_by_root[root]
        if (
            before.get("vcs") != current.get("vcs")
            or before.get("git_root") != current.get("git_root")
            or before.get("scope") != current.get("scope")
            or before.get("observable") != current.get("observable")
        ):
            errors.append(f"repository identity drifted from the checkpoint: {root}")
            continue
        if before.get("head") != current.get("head"):
            errors.append(f"repository HEAD drifted from the checkpoint: {root}")
        if check_worktree and before.get("worktree_sha256") != current.get("worktree_sha256"):
            errors.append(f"repository worktree changed since the checkpoint: {root}")
    return errors


def ensure_local_exclude(root: Path) -> None:
    result = run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=root)
    if result.returncode:
        return
    top = run(["git", "rev-parse", "--show-toplevel"], cwd=root)
    if top.returncode:
        return
    try:
        relative = root.resolve().relative_to(Path(top.stdout.strip()).resolve())
    except (OSError, ValueError):
        return
    exclude = Path(result.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    current = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    prefix = relative.as_posix().rstrip("/") if relative.parts else ""
    rule = f"{prefix + '/' if prefix else ''}.codex/dev-flow/"
    if rule not in {line.strip() for line in current.splitlines()}:
        with exclude.open("a", encoding="utf-8") as handle:
            if current and not current.endswith("\n"):
                handle.write("\n")
            handle.write(f"{rule}\n")


def replace_tokens(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"<{key}>", value)
    return text


def init_packet(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        return emit({"status": "error", "errors": [f"repository root does not exist: {root}"]}, 2)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", args.change_id):
        return emit({"status": "error", "errors": ["change ID must be 3-81 lowercase safe characters"]}, 2)
    if args.task_type not in TASK_TYPES:
        return emit({"status": "error", "errors": [f"unsupported task type: {args.task_type}"]}, 2)
    mutation_intent = args.mutation or ("none" if args.task_type == "read-only-audit" else "persistent")
    if args.task_type == "read-only-audit" and mutation_intent != "none":
        return emit({"status": "error", "errors": ["read-only-audit cannot declare persistent mutation"]}, 2)

    try:
        work_mode, mode_reasons = select_work_mode(
            args.task_type,
            args.risk,
            args.work_mode,
            persistent_mutation=mutation_intent == "persistent",
        )
    except ValueError as exc:
        return emit({"status": "error", "errors": [str(exc)]}, 2)
    if args.ui_impact == "material" and work_mode != "governed":
        if args.work_mode != "auto":
            return emit({"status": "error", "errors": ["material UI impact requires governed work mode"]}, 2)
        work_mode, mode_reasons = "governed", ["material-ui-impact"]
    if work_mode != "direct":
        try:
            current = safe_current_pointer(root)
        except PathContractError as exc:
            return emit({"status": "error", "errors": [str(exc)]}, 2)
    packet = root / ".codex" / "dev-flow" / args.change_id
    if packet.exists():
        if not args.reuse:
            return emit({"status": "error", "errors": [f"packet already exists: {packet}"]}, 2)
        if not packet.is_dir():
            return emit({"status": "error", "errors": [f"packet path is not a directory: {packet}"]}, 2)
        existing, errors = load_packet(packet)
        if errors:
            return emit({"status": "error", "errors": errors}, 2)
        if existing.get("change_id") != args.change_id or existing.get("task_type") != args.task_type:
            return emit({"status": "error", "errors": ["reused packet identity or task type does not match"]}, 2)
        existing_mode = existing.get("work_mode")
        if existing_mode not in WORK_MODES:
            existing_mode = "governed" if documentation_family(existing.get("documentation_profile")) == "governed" else "traced"
        rank = {"direct": 0, "traced": 1, "governed": 2}
        if rank[existing_mode] < rank[work_mode]:
            return emit(
                {
                    "status": "error",
                    "errors": [f"existing {existing_mode} packet must be explicitly migrated before required {work_mode} work"],
                },
                2,
            )
        atomic_write_text(current, args.change_id + "\n")
        ensure_local_exclude(root)
        return emit(
            {
                "status": "reused",
                "packet": str(packet),
                "work_mode": existing_mode,
                "profile": existing.get("documentation_profile"),
                "artifacts": sorted(path.name for path in packet.iterdir() if path.is_file()),
                "next_state": existing.get("state"),
            }
        )
    if work_mode == "direct":
        return emit(
            {
                "status": "not-required",
                "work_mode": "direct",
                "reasons": mode_reasons,
                "packet": None,
                "artifacts": [],
            }
        )
    packet.mkdir(parents=True, exist_ok=True)
    folders = ("briefs", "reports", "artifacts") if work_mode == "governed" else ("artifacts",)
    for folder in folders:
        (packet / folder).mkdir(exist_ok=True)

    now = utc_now()
    profile = "trace" if work_mode == "traced" else "governed"
    collaboration_profile = args.collaboration_profile
    if collaboration_profile is None:
        if args.ui_impact == "material":
            collaboration_profile = "co-design"
        elif work_mode == "traced" and mutation_intent != "persistent":
            collaboration_profile = "execute"
        else:
            collaboration_profile = "checkpointed"
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": packet_skill_version(),
        "change_id": args.change_id,
        "state": "discovering",
        "work_mode": work_mode,
        "work_mode_reasons": mode_reasons,
        "mutation_intent": mutation_intent,
        "documentation_profile": profile,
        "task_type": args.task_type,
        "created_at": now,
        "updated_at": now,
        "repository_roots": [str(root)],
        "base_git_state": git_state(root),
        "authority": args.authority,
        "collaboration_profile": collaboration_profile,
        "ui_impact": args.ui_impact,
        "compatibility_required": args.compatibility_required,
        "risk_modifiers": args.risk,
        "acceptance_ids": [],
        "scope_ids": [],
        "verification_ids": [],
        "requirement_revision": 1,
        "requirements_digest": None,
        "design_digest": None,
        "continuity_checkpoint": None,
        "knowledge_manifest": None,
        "method_selection": None,
        "ambiguity_ids": [],
        "ambiguities": [],
        "dependency_changes": [],
        "iteration_control": {
            "schema_version": "1.0",
            "generation": 1,
            "records": [],
            "blocked": None,
        },
        "approvals": {
            "requirements": [],
            "ux": [],
            "design": None,
            "dependencies": [],
            "waivers": [],
            "delivery": [],
        },
        "history": [{"from": None, "to": "discovering", "at": now, "note": "packet created"}],
    }

    values = {
        "change-id": args.change_id,
        "task-type": args.task_type,
        "objective": args.objective,
        "authority": args.authority,
        "repository-roots": str(root),
        "base-git-state": metadata["base_git_state"],
        "compatibility": "yes" if args.compatibility_required else "no",
        "profiles": ", ".join(args.profile) if args.profile else "to be established from repository evidence",
        "risk-modifiers": ", ".join(args.risk) if args.risk else "none observed during initial classification",
        "collaboration-profile": collaboration_profile,
        "ui-impact": args.ui_impact,
    }
    templates = skill_root() / "templates"
    filenames = ("micro-trace.md",) if work_mode == "traced" else FULL_FILES
    for filename in filenames:
        source = templates / filename
        destination = packet / ("trace.md" if filename == "micro-trace.md" else filename)
        destination.write_text(replace_tokens(source.read_text(encoding="utf-8"), values), encoding="utf-8")

    if work_mode == "governed":
        brief = replace_tokens((templates / "task-brief.md").read_text(encoding="utf-8"), values)
        report = replace_tokens((templates / "agent-report.md").read_text(encoding="utf-8"), values)
        (packet / "briefs" / "README.template.md").write_text(brief, encoding="utf-8")
        (packet / "reports" / "README.template.md").write_text(report, encoding="utf-8")
    write_packet(
        packet,
        metadata,
        "packet-created",
        {
            "from": None,
            "to": "discovering",
            "reasons": mode_reasons,
            "skill_version": metadata["skill_version"],
            "creation_contract": creation_contract(metadata),
        },
    )
    method_artifacts: list[str] = []
    if work_mode == "governed" and has_method_selection_contract(metadata.get("skill_version")):
        try:
            persist_method_selection(
                packet,
                metadata,
                phase="design",
                risks=list(args.risk),
                signals=[],
                available=["repository-facts"],
                depth="starter",
                max_methods=None,
                preliminary=True,
            )
        except (OSError, ValueError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
            return emit(
                {
                    "status": "error",
                    "errors": [f"cannot initialize governed method selection: {exc}"],
                    "packet": str(packet),
                },
                2,
            )
        method_artifacts = ["method-selection.json", "method-selection.md"]
    atomic_write_text(current, args.change_id + "\n")
    ensure_local_exclude(root)
    return emit(
        {
            "status": "created",
            "packet": str(packet),
            "work_mode": work_mode,
            "profile": profile,
            "artifacts": [
                "packet.json",
                "events.jsonl",
                *(["trace.md"] if work_mode == "traced" else list(FULL_FILES)),
                *method_artifacts,
            ],
            "next_state": "awaiting-approval",
        }
    )


def load_packet(
    packet: Path,
    *,
    validate_change_set: bool = True,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    metadata_path = packet / "packet.json"
    if not metadata_path.is_file():
        return {}, ["missing required file: packet.json"]
    try:
        metadata = read_json(metadata_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"invalid packet.json: {exc}"]
    if not isinstance(metadata, dict):
        return {}, ["invalid packet.json: top-level value must be an object"]
    errors.extend(quality_provenance_errors(packet, metadata))
    if metadata.get("schema_version") == "2.0":
        errors.extend(validate_iteration_control(metadata))
        errors.extend(validate_iteration_evidence(packet, metadata))
        errors.extend(validate_event_projection(packet, metadata, quality_provenance_checked=True))
        errors.extend(method_selection_binding_errors(packet, metadata))
        if validate_change_set:
            errors.extend(validate_change_set_binding(packet, metadata))
            errors.extend(validate_continuity_binding(packet, metadata))
    return metadata, errors


def validate_event_projection(
    packet: Path,
    metadata: dict[str, Any],
    *,
    quality_provenance_checked: bool = False,
) -> list[str]:
    errors = [] if quality_provenance_checked else quality_provenance_errors(packet, metadata)
    if metadata.get("schema_version") != "2.0":
        return errors
    ledger = packet / "events.jsonl"
    if not ledger.is_file():
        return [*errors, "missing required file: events.jsonl"]
    events: list[dict[str, Any]] = []
    for index, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"events.jsonl:{index}: invalid JSON: {exc}")
            continue
        if not isinstance(record, dict):
            errors.append(f"events.jsonl:{index}: event must be an object")
            continue
        events.append(record)
        if record.get("schema_version") != "1.0":
            errors.append(f"events.jsonl:{index}: unsupported event schema")
        if record.get("sequence") != len(events):
            errors.append(f"events.jsonl:{index}: sequence must be contiguous from 1")
        if record.get("event") not in PACKET_EVENTS:
            errors.append(f"events.jsonl:{index}: unsupported event name {record.get('event')!r}")
        if parsed_timestamp(record.get("at")) is None:
            errors.append(f"events.jsonl:{index}: timezone-aware timestamp is required")
        if record.get("work_mode") != metadata.get("work_mode"):
            errors.append(f"events.jsonl:{index}: work_mode drifted from packet projection")
    if not events:
        return [*errors, "events.jsonl: at least one event is required"]
    if events[0].get("event") != "packet-created":
        errors.append("events.jsonl: first event must be packet-created")
    creation_payload = events[0].get("payload")
    metadata_skill_version = metadata.get("skill_version")
    creation_skill_version = (
        creation_payload.get("skill_version")
        if isinstance(creation_payload, dict)
        else None
    )
    immutable_contract = (
        creation_payload.get("creation_contract")
        if isinstance(creation_payload, dict)
        else None
    )
    for index, event in enumerate(events, start=1):
        payload = event.get("payload")
        if isinstance(payload, dict) and "skill_version_transition" in payload:
            errors.append(f"events.jsonl:{index}: implicit change-set contract adoption is unsupported")
    creation_tagged = has_change_set_contract(creation_skill_version)
    metadata_tagged = has_change_set_contract(metadata_skill_version)
    creation_quality_tagged = has_quality_kernel_contract(creation_skill_version)
    metadata_quality_tagged = has_quality_kernel_contract(metadata_skill_version)
    quality_markers = quality_provenance_markers(metadata, events)
    if immutable_contract is None and (creation_quality_tagged or metadata_quality_tagged or quality_markers):
        errors.append(
            "events.jsonl: quality-shaped packet is missing its immutable creation contract"
            + (f"; residual markers={sorted(quality_markers)}" if quality_markers else "")
        )
    if creation_tagged or metadata_tagged or creation_quality_tagged or metadata_quality_tagged:
        if creation_skill_version != metadata_skill_version:
            errors.append("events.jsonl: tagged packet creation must exactly match packet skill_version")
    contract_quality_tagged = False
    if immutable_contract is not None:
        expected_contract_keys = set(creation_contract(metadata))
        if not isinstance(immutable_contract, dict) or set(immutable_contract) != expected_contract_keys:
            errors.append("events.jsonl: creation contract must use the exact immutable authority schema")
        else:
            capabilities = immutable_contract.get("capabilities")
            contract_quality_tagged = isinstance(capabilities, list) and QUALITY_KERNEL_SKILL_VERSION_TAG in capabilities
            if not contract_quality_tagged and quality_markers:
                errors.append(
                    "events.jsonl: quality-shaped packet cannot drop its creation capability"
                    f"; residual markers={sorted(quality_markers)}"
                )
            if immutable_contract.get("schema_version") != CREATION_CONTRACT_SCHEMA_VERSION:
                errors.append("events.jsonl: creation contract has an unsupported schema_version")
            if immutable_contract.get("skill_version") != creation_skill_version:
                errors.append("events.jsonl: creation contract skill_version does not match tagged creation")
            if capabilities != sorted(skill_capabilities(immutable_contract.get("skill_version"))):
                errors.append("events.jsonl: creation contract capabilities do not match its skill_version")
            current_contract = creation_contract(metadata)
            for field in expected_contract_keys - {"schema_version", "collaboration_profile"}:
                if immutable_contract.get(field) != current_contract.get(field):
                    errors.append(f"events.jsonl: creation contract {field} drifted from packet projection")
            profile_rank = {"execute": 0, "checkpointed": 1, "co-design": 2}
            original_profile = immutable_contract.get("collaboration_profile")
            current_profile = metadata.get("collaboration_profile")
            if (
                original_profile not in profile_rank
                or current_profile not in profile_rank
                or profile_rank[current_profile] < profile_rank[original_profile]
            ):
                errors.append("events.jsonl: creation contract collaboration_profile was weakened")
    bound_without_contract = any(
        isinstance(event.get("payload"), dict)
        and isinstance(event["payload"].get("change_set"), dict)
        for event in events
    )
    if bound_without_contract and not creation_tagged:
        errors.append("events.jsonl: change-set binding requires tagged packet creation")
    quality_contract = contract_quality_tagged or creation_quality_tagged or metadata_quality_tagged
    replayed_state: Any = None
    replayed_requirement_revision = 1
    previous_event_time: dt.datetime | None = None
    latest_ambiguities: dict[str, Any] = {}
    ambiguity_order: list[str] = []
    malformed_ambiguity_event = False
    latest_checkpoint: dict[str, Any] | None = None
    pending_invalidation: dict[str, Any] | None = None
    pending_invalidation_index: int | None = None
    for index, event in enumerate(events, start=1):
        event_time = parsed_timestamp(event.get("at"))
        if event_time is not None:
            if previous_event_time is not None and event_time < previous_event_time:
                errors.append(f"events.jsonl:{index}: event timestamps must be nondecreasing")
            previous_event_time = event_time
        name = event.get("event")
        payload = event.get("payload")
        if pending_invalidation is not None and not (
            name == "transition"
            and pending_invalidation_index is not None
            and index == pending_invalidation_index + 1
        ):
            errors.append(
                f"events.jsonl:{index}: checkpoint invalidation must be immediately followed by its reopening transition"
            )
            pending_invalidation = None
            pending_invalidation_index = None
        prior_state = replayed_state
        if name == "packet-created":
            if index != 1 or replayed_state is not None:
                errors.append(f"events.jsonl:{index}: packet-created may only initialize the ledger")
            if not isinstance(payload, dict) or payload.get("from") is not None or payload.get("to") != event.get("state"):
                errors.append(f"events.jsonl:{index}: packet-created does not initialize its projected lifecycle state")
            replayed_state = event.get("state")
        elif name == "transition":
            if not isinstance(payload, dict) or payload.get("from") != replayed_state or payload.get("to") != event.get("state"):
                errors.append(f"events.jsonl:{index}: transition does not follow the replayed lifecycle state")
            replayed_state = event.get("state")
        elif event.get("state") != replayed_state:
            errors.append(f"events.jsonl:{index}: non-transition event does not match the replayed lifecycle state")

        record = payload.get("record") if isinstance(payload, dict) else None
        if name == "ambiguity-recorded":
            ambiguity_id = record.get("id") if isinstance(record, dict) else None
            if (
                not isinstance(ambiguity_id, str)
                or ambiguity_id in latest_ambiguities
                or record.get("status") != "open"
                or record.get("resolution") is not None
                or record.get("discovered_in_revision") != replayed_requirement_revision
            ):
                malformed_ambiguity_event = True
            elif isinstance(record, dict):
                ambiguity_order.append(ambiguity_id)
                latest_ambiguities[ambiguity_id] = record
        elif name == "ambiguity-resolved":
            ambiguity_id = record.get("id") if isinstance(record, dict) else None
            previous = latest_ambiguities.get(ambiguity_id) if isinstance(ambiguity_id, str) else None
            if not isinstance(record, dict) or not isinstance(previous, dict) or previous.get("status") != "open":
                malformed_ambiguity_event = True
            else:
                expected = dict(previous)
                expected["status"] = record.get("status")
                expected["resolution"] = record.get("resolution")
                if record.get("status") == "open" or not isinstance(record.get("resolution"), dict) or record != expected:
                    malformed_ambiguity_event = True
                latest_ambiguities[ambiguity_id] = record
        elif name == "checkpoint-recorded":
            if not isinstance(payload, dict):
                errors.append(f"events.jsonl:{index}: checkpoint record must use an object payload")
                latest_checkpoint = None
            elif quality_contract and set(payload) != CONTINUITY_CHECKPOINT_FIELDS:
                errors.append(f"events.jsonl:{index}: checkpoint record must use the exact checkpoint schema")
                latest_checkpoint = None
            else:
                if quality_contract and payload.get("requirement_revision") != replayed_requirement_revision:
                    errors.append(
                        f"events.jsonl:{index}: checkpoint record does not match the replayed requirement premise"
                    )
                latest_checkpoint = payload
        elif name == "checkpoint-invalidated":
            label = f"events.jsonl:{index}: checkpoint invalidation"
            if not isinstance(payload, dict) or set(payload) != CHECKPOINT_INVALIDATION_FIELDS:
                errors.append(f"{label} must use the exact tombstone schema")
            else:
                if payload.get("schema_version") != CHECKPOINT_INVALIDATION_SCHEMA_VERSION:
                    errors.append(f"{label} has an unsupported schema_version")
                if payload.get("reason") != "late-material-requirement-reopening":
                    errors.append(f"{label} has an invalid reason")
                from_revision = payload.get("from_requirement_revision")
                new_revision = payload.get("new_requirement_revision")
                if not isinstance(latest_checkpoint, dict):
                    errors.append(f"{label} does not identify a preceding checkpoint record")
                else:
                    if payload.get("invalidated_checkpoint_sha256") != canonical_json_digest(latest_checkpoint):
                        errors.append(f"{label} hash does not identify the preceding checkpoint record")
                    if from_revision != latest_checkpoint.get("requirement_revision"):
                        errors.append(f"{label} from revision does not match the invalidated checkpoint")
                if (
                    not isinstance(from_revision, int)
                    or isinstance(from_revision, bool)
                    or not isinstance(new_revision, int)
                    or isinstance(new_revision, bool)
                    or from_revision != replayed_requirement_revision
                    or new_revision != replayed_requirement_revision + 1
                ):
                    errors.append(f"{label} revisions do not exactly advance the replayed requirement premise")
                ambiguity = latest_ambiguities.get(payload.get("ambiguity_id"))
                if (
                    not isinstance(ambiguity, dict)
                    or ambiguity.get("status") != "open"
                    or ambiguity.get("materiality") not in {"material", "high-risk"}
                    or ambiguity.get("discovered_in_revision") != replayed_requirement_revision
                ):
                    errors.append(f"{label} does not identify an open material ambiguity at that ledger position")
                pending_invalidation = payload
                pending_invalidation_index = index
        if name == "transition" and isinstance(payload, dict):
            bound_invalidation = payload.get("checkpoint_invalidation")
            reopening = (
                quality_contract
                and payload.get("from") in {"implementing", "verifying", "blocked"}
                and payload.get("to") == "awaiting-approval"
            )
            if bound_invalidation is not None:
                ambiguity = (
                    latest_ambiguities.get(bound_invalidation.get("ambiguity_id"))
                    if isinstance(bound_invalidation, dict)
                    else None
                )
                if (
                    pending_invalidation is None
                    or pending_invalidation_index != index - 1
                    or bound_invalidation != pending_invalidation
                    or payload.get("from") != prior_state
                    or payload.get("to") != "awaiting-approval"
                    or not isinstance(ambiguity, dict)
                    or ambiguity.get("status") != "open"
                    or ambiguity.get("materiality") not in {"material", "high-risk"}
                ):
                    errors.append(
                        f"events.jsonl:{index}: reopening transition does not match the adjacent open ambiguity tombstone"
                    )
                if isinstance(bound_invalidation, dict):
                    new_revision = bound_invalidation.get("new_requirement_revision")
                    if isinstance(new_revision, int) and not isinstance(new_revision, bool):
                        replayed_requirement_revision = new_revision
                latest_checkpoint = None
                pending_invalidation = None
                pending_invalidation_index = None
            elif reopening:
                errors.append(f"events.jsonl:{index}: reopening transition is missing its adjacent checkpoint invalidation")

    if pending_invalidation is not None:
        errors.append("events.jsonl: checkpoint invalidation is missing its immediately following reopening transition")
    if quality_contract and metadata.get("requirement_revision") != replayed_requirement_revision:
        errors.append("events.jsonl: replayed requirement revision does not exactly match the packet projection")

    state_events = [item for item in events if item.get("event") in {"packet-created", "transition"}]
    history = metadata.get("history", [])
    if not isinstance(history, list) or len(state_events) != len(history):
        errors.append("events.jsonl: state events must project exactly to packet history")
    else:
        for index, (event, projected) in enumerate(zip(state_events, history, strict=True), start=1):
            payload = event.get("payload", {})
            if not isinstance(payload, dict) or payload.get("from") != projected.get("from") or payload.get("to") != projected.get("to"):
                errors.append(f"events.jsonl: state event {index} does not match packet history")
            if event.get("state") != projected.get("to"):
                errors.append(f"events.jsonl: state event {index} projected state does not match packet history")
        if state_events and state_events[-1].get("state") != metadata.get("state"):
            errors.append("events.jsonl: final state does not match packet projection")
    control = metadata.get("iteration_control")
    if isinstance(control, dict) and isinstance(control.get("records"), list):
        iteration_events = [
            item for item in events if item.get("event") in {"iteration-recorded", "iteration-reassessed"}
        ]
        if len(iteration_events) != len(control["records"]):
            errors.append("events.jsonl: iteration events must project exactly to iteration_control.records")
        else:
            for index, (event, projected) in enumerate(zip(iteration_events, control["records"], strict=True), start=1):
                if event.get("payload") != projected:
                    errors.append(f"events.jsonl: iteration event {index} does not match packet projection")
                expected_state = None
                sequence = event.get("sequence")
                if isinstance(sequence, int) and sequence > 1:
                    expected_state = events[sequence - 2].get("state")
                if expected_state is not None and event.get("state") != expected_state:
                    errors.append(f"events.jsonl: iteration event {index} projected state is invalid")
    checkpoint_events = [
        item
        for item in events
        if item.get("event") in {"checkpoint-recorded", "checkpoint-invalidated"}
    ]
    projected_checkpoint = metadata.get("continuity_checkpoint")
    if quality_contract:
        if projected_checkpoint is None and checkpoint_events:
            if checkpoint_events[-1].get("event") != "checkpoint-invalidated":
                errors.append("events.jsonl: checkpoint lifecycle is missing from packet projection")
        elif projected_checkpoint is not None:
            if not checkpoint_events:
                errors.append("events.jsonl: continuity checkpoint requires an event projection")
            elif checkpoint_events[-1].get("event") != "checkpoint-recorded" or checkpoint_events[-1].get("payload") != projected_checkpoint:
                errors.append("events.jsonl: latest checkpoint event does not match packet projection")
        knowledge_events = [item for item in events if item.get("event") == "knowledge-bound"]
        projected_knowledge = metadata.get("knowledge_manifest")
        if projected_knowledge is None and knowledge_events:
            errors.append("events.jsonl: knowledge binding is missing from packet projection")
        elif projected_knowledge is not None:
            if not knowledge_events:
                errors.append("events.jsonl: knowledge binding requires an event projection")
            elif knowledge_events[-1].get("payload") != projected_knowledge:
                errors.append("events.jsonl: latest knowledge event does not match packet projection")
    if contract_quality_tagged:
        approval_events = [item for item in events if item.get("event") == "approval-recorded"]
        approvals = metadata.get("approvals")
        if isinstance(approvals, dict):
            for kind in ("requirements", "ux", "dependencies", "waivers", "delivery"):
                projected = [
                    item.get("payload", {}).get("record")
                    for item in approval_events
                    if isinstance(item.get("payload"), dict) and item["payload"].get("kind") == kind
                ]
                if projected != approvals.get(kind):
                    errors.append(f"events.jsonl: approval events must project exactly to approvals.{kind}")
            design_events = [
                item["payload"].get("design_approval")
                for item in events
                if item.get("event") == "transition"
                and isinstance(item.get("payload"), dict)
                and item["payload"].get("to") == "approved"
            ]
            design_history = approvals.get("design_history", [])
            current_design = approvals.get("design")
            if not isinstance(design_history, list):
                errors.append("events.jsonl: approvals.design_history must be a list for exact projection")
                projected_designs: list[Any] = []
            else:
                projected_designs = [*design_history, *([current_design] if current_design else [])]
            if design_events != projected_designs:
                errors.append("events.jsonl: design approval events must project exactly to approvals")
        projected_ambiguities = [latest_ambiguities[value] for value in ambiguity_order if value in latest_ambiguities]
        if malformed_ambiguity_event or projected_ambiguities != metadata.get("ambiguities"):
            errors.append("events.jsonl: ambiguity events must project exactly to packet ambiguities")
        if ambiguity_order != metadata.get("ambiguity_ids"):
            errors.append("events.jsonl: ambiguity events must project exactly to ambiguity_ids")
    return errors


def validate_iteration_control(metadata: dict[str, Any]) -> list[str]:
    control = metadata.get("iteration_control")
    if control is None:
        if metadata.get("schema_version") == "2.0":
            return ["packet.json: schema 2.0 requires iteration_control"]
        return []
    if not isinstance(control, dict) or set(control) != {"schema_version", "generation", "records", "blocked"}:
        return ["packet.json: iteration_control must use the exact schema"]
    errors: list[str] = []
    generation = control.get("generation")
    records = control.get("records")
    if control.get("schema_version") != "1.0":
        errors.append("packet.json: iteration_control schema_version must be 1.0")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 1:
        errors.append("packet.json: iteration_control generation must be a positive integer")
    if not isinstance(records, list):
        return [*errors, "packet.json: iteration_control records must be a list"]
    expected_keys = {
        "generation",
        "kind",
        "cause_id",
        "cause_artifact",
        "cause_digest",
        "round",
        "outcome",
        "reopened_owner",
        "at",
        "note",
    }
    failure_rounds: dict[tuple[int, str, str], int] = {}
    cause_bindings: dict[tuple[int, str], tuple[str, str]] = {}
    digest_bindings: dict[tuple[int, str], str] = {}
    for index, record in enumerate(records):
        label = f"packet.json: iteration_control.records[{index}]"
        if not isinstance(record, dict) or set(record) != expected_keys:
            errors.append(f"{label} must use the exact record schema")
            continue
        record_generation = record.get("generation")
        kind = record.get("kind")
        cause_id = record.get("cause_id")
        outcome = record.get("outcome")
        round_number = record.get("round")
        if (
            not isinstance(record_generation, int)
            or isinstance(record_generation, bool)
            or record_generation < 1
            or not isinstance(generation, int)
            or record_generation > generation
        ):
            errors.append(f"{label} has invalid generation")
        if kind not in ITERATION_KINDS:
            errors.append(f"{label} has invalid kind")
        if not isinstance(cause_id, str) or ITERATION_CAUSE_RE.fullmatch(cause_id) is None:
            errors.append(f"{label} has invalid cause_id")
        cause_artifact = record.get("cause_artifact")
        cause_digest = record.get("cause_digest")
        if (
            not isinstance(cause_artifact, str)
            or not cause_artifact.startswith("artifacts/")
            or Path(cause_artifact).is_absolute()
            or any(part in {"", ".", ".."} for part in Path(cause_artifact).parts)
        ):
            errors.append(f"{label} has invalid cause_artifact")
        if not isinstance(cause_digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", cause_digest) is None:
            errors.append(f"{label} has invalid cause_digest")
        if isinstance(record_generation, int) and isinstance(cause_id, str) and isinstance(cause_artifact, str) and isinstance(cause_digest, str):
            binding_key = (record_generation, cause_id)
            binding = (cause_artifact, cause_digest)
            if binding_key in cause_bindings and cause_bindings[binding_key] != binding:
                errors.append(f"{label} changes the evidence binding for an existing cause_id")
            cause_bindings[binding_key] = binding
            digest_key = (record_generation, cause_digest)
            if digest_key in digest_bindings and digest_bindings[digest_key] != cause_id:
                errors.append(f"{label} aliases an existing cause digest with a different cause_id")
            digest_bindings[digest_key] = cause_id
        if outcome not in ITERATION_OUTCOMES:
            errors.append(f"{label} has invalid outcome")
        if parsed_timestamp(record.get("at")) is None or not isinstance(record.get("note"), str) or not record["note"].strip():
            errors.append(f"{label} requires timestamp and note")
        key = (record_generation, str(kind), str(cause_id))
        if outcome == "failed":
            expected_round = failure_rounds.get(key, 0) + 1
            if round_number != expected_round:
                errors.append(f"{label} failed round must be contiguous for its cause")
            failure_rounds[key] = expected_round
            if record.get("reopened_owner") is not None:
                errors.append(f"{label} failed outcome cannot reopen an owner")
        elif outcome == "succeeded":
            if round_number != 0 or record.get("reopened_owner") is not None:
                errors.append(f"{label} succeeded outcome must reset with round zero")
            failure_rounds[key] = 0
        elif outcome == "reassessed":
            if round_number != 0 or record.get("reopened_owner") not in ITERATION_OWNERS:
                errors.append(f"{label} reassessed outcome requires a reopened owner and round zero")
            failure_rounds[key] = 0
    active_failures = [
        (key, count)
        for key, count in failure_rounds.items()
        if isinstance(generation, int) and key[0] == generation and count >= 3
    ]
    blocked = control.get("blocked")
    if active_failures and blocked is None:
        errors.append("packet.json: third failed round requires an active iteration breaker")
    if len(active_failures) > 1:
        errors.append("packet.json: multiple active iteration breakers are invalid")
    if blocked is not None:
        if not isinstance(blocked, dict) or set(blocked) != {
            "generation",
            "kind",
            "cause_id",
            "cause_artifact",
            "cause_digest",
            "round",
            "at",
        }:
            errors.append("packet.json: iteration_control blocked must use the exact breaker schema")
        else:
            blocked_round = blocked.get("round")
            if (
                not isinstance(blocked_round, int)
                or isinstance(blocked_round, bool)
                or blocked_round != 3
                or parsed_timestamp(blocked.get("at")) is None
            ):
                errors.append("packet.json: iteration_control blocked requires the third failed round")
            matching = [
                record
                for record in records
                if isinstance(record, dict)
                and record.get("generation") == blocked.get("generation")
                and record.get("kind") == blocked.get("kind")
                and record.get("cause_id") == blocked.get("cause_id")
                and record.get("cause_artifact") == blocked.get("cause_artifact")
                and record.get("cause_digest") == blocked.get("cause_digest")
                and record.get("round") == blocked.get("round")
                and record.get("outcome") == "failed"
            ]
            if not matching:
                errors.append("packet.json: iteration_control blocked is not backed by a failed record")
            active_key = (blocked.get("generation"), blocked.get("kind"), blocked.get("cause_id"))
            if not active_failures or active_failures[0][0] != active_key or active_failures[0][1] != 3:
                errors.append("packet.json: iteration_control blocked does not match the active third failure")
        if metadata.get("state") != "blocked":
            errors.append("packet.json: active iteration breaker requires blocked packet state")
    return errors


def validate_iteration_evidence(packet: Path, metadata: dict[str, Any]) -> list[str]:
    control = metadata.get("iteration_control")
    if not isinstance(control, dict) or not isinstance(control.get("records"), list):
        return []
    errors: list[str] = []
    checked: set[tuple[str, str]] = set()
    for index, record in enumerate(control["records"]):
        if not isinstance(record, dict):
            continue
        artifact = record.get("cause_artifact")
        digest = record.get("cause_digest")
        if not isinstance(artifact, str) or not isinstance(digest, str) or (artifact, digest) in checked:
            continue
        checked.add((artifact, digest))
        try:
            relative = Path(artifact).relative_to("artifacts")
            path = contained_path(
                packet / "artifacts",
                relative,
                label="iteration cause artifact",
                require_relative=True,
                reject_symlinks=True,
            )
        except (PathContractError, ValueError) as exc:
            errors.append(f"packet.json: iteration_control.records[{index}] cause artifact is invalid: {exc}")
            continue
        if not path.is_file():
            errors.append(f"packet.json: iteration_control.records[{index}] cause artifact is missing")
            continue
        observed = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
        if observed != digest:
            errors.append(f"packet.json: iteration_control.records[{index}] cause artifact digest drifted")
    return errors


def transition_packet(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(
        packet,
        validate_change_set=args.state not in {"implementing", "awaiting-approval"},
    )
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    old = metadata.get("state")
    new = args.state
    now = utc_now()
    transition_at = parsed_timestamp(now)
    assert transition_at is not None
    schema_version = metadata.get("schema_version")
    iteration_control = metadata.get("iteration_control")
    active_iteration_block = (
        iteration_control.get("blocked")
        if isinstance(iteration_control, dict)
        else None
    )
    checkpoint_invalidation: dict[str, Any] | None = None
    if old == "blocked" and new != "blocked" and active_iteration_block is not None:
        return emit(
            {
                "status": "invalid-transition",
                "from": old,
                "to": new,
                "errors": ["three-attempt breaker requires record-iteration --outcome reassessed before resuming"],
            },
            2,
        )
    direct_reopening = (
        schema_version in CONTENT_BOUND_SCHEMA_VERSIONS
        and old in {"implementing", "verifying"}
        and new == "awaiting-approval"
    )
    history = metadata.get("history", [])
    last_blocked_from = next(
        (
            event.get("from")
            for event in reversed(history if isinstance(history, list) else [])
            if isinstance(event, dict) and event.get("to") == "blocked"
        ),
        None,
    )
    open_material_ambiguities = [
        record
        for record in metadata.get("ambiguities", [])
        if isinstance(record, dict)
        and record.get("status") == "open"
        and record.get("materiality") in {"material", "high-risk"}
    ] if isinstance(metadata.get("ambiguities", []), list) else []
    blocked_reopening = (
        schema_version in CONTENT_BOUND_SCHEMA_VERSIONS
        and old == "blocked"
        and new == "awaiting-approval"
        and last_blocked_from in {"implementing", "verifying"}
        and bool(open_material_ambiguities)
    )
    if (
        schema_version in CONTENT_BOUND_SCHEMA_VERSIONS
        and old == "blocked"
        and new == "discovering"
        and last_blocked_from in {"implementing", "verifying"}
        and open_material_ambiguities
    ):
        return emit(
            {
                "status": "invalid-transition",
                "from": old,
                "to": new,
                "errors": ["late material ambiguity must reopen through awaiting-approval with --ambiguity-id"],
            },
            2,
        )
    reopening = direct_reopening or blocked_reopening
    if old not in STATES or (not reopening and new not in TRANSITIONS.get(str(old), set())):
        return emit({"status": "invalid-transition", "from": old, "to": new}, 2)
    if reopening:
        ambiguity_id = args.ambiguity_id
        ambiguity = find_ambiguity(metadata, ambiguity_id or "")
        if not ambiguity_id or ambiguity is None:
            return emit(
                {"status": "invalid", "errors": ["content-bound requirement reopening requires a known --ambiguity-id"]},
                2,
            )
        if ambiguity.get("status") != "open" or ambiguity.get("materiality") not in {"material", "high-risk"}:
            return emit(
                {
                    "status": "invalid",
                    "errors": ["requirement reopening requires an open material or high-risk ambiguity"],
                },
                2,
            )
        semantic_errors = semantic_metadata_errors(
            metadata,
            declared_trace_ids=declared_trace_ids(metadata),
            require_ready=False,
        )
        if semantic_errors:
            return emit({"status": "invalid", "errors": semantic_errors}, 2)
        approvals = metadata.get("approvals")
        if not isinstance(approvals, dict):
            return emit({"status": "invalid", "errors": ["approvals must be an object"]}, 2)
        previous_design = approvals.get("design")
        if previous_design is not None:
            history = approvals.setdefault("design_history", [])
            if not isinstance(history, list):
                return emit({"status": "invalid", "errors": ["approvals.design_history must be a list"]}, 2)
            history.append(previous_design)
        approvals["design"] = None
        revision = metadata.get("requirement_revision")
        if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
            return emit({"status": "invalid", "errors": ["requirement_revision must be a positive integer"]}, 2)
        metadata["requirement_revision"] = revision + 1
        metadata["requirements_digest"] = None
        if has_quality_kernel_contract(metadata.get("skill_version")):
            metadata["design_digest"] = None
            previous_checkpoint = metadata.get("continuity_checkpoint")
            if not isinstance(previous_checkpoint, dict):
                return emit(
                    {
                        "status": "invalid",
                        "errors": ["quality-kernel requirement reopening requires an intact checkpoint to invalidate"],
                    },
                    2,
                )
            checkpoint_invalidation = {
                "schema_version": CHECKPOINT_INVALIDATION_SCHEMA_VERSION,
                "reason": "late-material-requirement-reopening",
                "ambiguity_id": ambiguity_id,
                "invalidated_checkpoint_sha256": canonical_json_digest(previous_checkpoint),
                "from_requirement_revision": revision,
                "new_requirement_revision": metadata["requirement_revision"],
            }
            metadata["continuity_checkpoint"] = None
    if new == "approved" and not args.approved_by:
        return emit({"status": "invalid", "errors": ["--approved-by is required for approved state"]}, 2)
    if new == "approved" and schema_version in READINESS_SCHEMA_VERSIONS:
        approvals = metadata.get("approvals", {})
        collaboration_profile = metadata.get("collaboration_profile")
        ui_impact = metadata.get("ui_impact")
        if not isinstance(approvals, dict):
            return emit({"status": "invalid", "errors": ["approvals must be an object"]}, 2)
        if not args.approved_by.strip() or not args.note.strip():
            return emit({"status": "invalid", "errors": ["design approval requires non-empty actor and note"]}, 2)
        if collaboration_profile not in COLLABORATION_PROFILES:
            return emit(
                {"status": "invalid", "errors": [f"invalid collaboration_profile {collaboration_profile!r}"]},
                2,
            )
        if ui_impact not in UI_IMPACTS:
            return emit({"status": "invalid", "errors": [f"invalid ui_impact {ui_impact!r}"]}, 2)
        awaiting_times = history_times(metadata, "awaiting-approval")
        if not awaiting_times:
            return emit({"status": "invalid", "errors": ["approval requires an awaiting-approval history event"]}, 2)
        awaiting_at = max(awaiting_times)
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS and awaiting_at > transition_at:
            return emit({"status": "invalid", "errors": ["awaiting-approval history cannot be in the future"]}, 2)
        requirement_records = concrete_readiness_records(approvals, "requirements")
        ux_records = concrete_readiness_records(approvals, "ux")
        current_digest = current_requirements_digest(packet, metadata.get("documentation_profile"))
        revision = metadata.get("requirement_revision")
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
            semantic_errors = semantic_metadata_errors(
                metadata,
                declared_trace_ids=declared_trace_ids(metadata),
                require_ready=True,
            )
            if semantic_errors:
                return emit({"status": "invalid", "errors": semantic_errors}, 2)
            if current_digest is None:
                return emit({"status": "invalid", "errors": ["cannot compute the requirement baseline digest"]}, 2)
            if collaboration_profile == "execute" and metadata.get("requirements_digest") is None:
                metadata["requirements_digest"] = current_digest
            if metadata.get("requirements_digest") != current_digest:
                return emit(
                    {"status": "invalid", "errors": ["requirements changed after Requirement Ready approval"]},
                    2,
                )

        def current_requirement_record(record: dict[str, Any]) -> bool:
            timestamp = parsed_timestamp(record.get("at"))
            if timestamp is None or not awaiting_at <= timestamp <= transition_at:
                return False
            return schema_version not in CONTENT_BOUND_SCHEMA_VERSIONS or (
                record.get("requirement_revision") == revision
                and record.get("requirements_digest") == current_digest
            )

        if collaboration_profile != "execute" and not any(current_requirement_record(record) for record in requirement_records):
            return emit(
                {"status": "invalid", "errors": ["checkpointed and co-design work require Requirement Ready approval"]},
                2,
            )
        if ui_impact == "material" and not any(
            parsed_timestamp(record.get("at")) is not None
            and awaiting_at <= parsed_timestamp(record.get("at")) <= transition_at
            for record in ux_records
        ):
            return emit({"status": "invalid", "errors": ["material UI work requires UX Ready approval"]}, 2)
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
            method_errors = method_selection_binding_errors(
                packet,
                metadata,
                effective_state="approved",
            )
            if method_errors:
                return emit(
                    {
                        "status": "approval-blocked",
                        "packet": str(packet),
                        "errors": method_errors,
                    },
                    2,
                )
            validation, validation_code = validate_packet_data(packet)
            if validation_code:
                validation["status"] = "approval-blocked"
                return emit(validation, 2)
    change_set_record: dict[str, str] | None = None
    continuity_record: dict[str, Any] | None = None
    if new == "implementing" and has_quality_kernel_contract(metadata.get("skill_version")):
        report, code = validate_packet_data(packet, state_override="implementing")
        if code and old == "verifying":
            repairable_prefixes = (
                "repository HEAD drifted from the checkpoint:",
                "repository worktree changed since the checkpoint:",
            )
            repairable_exact = {"packet.json: project-knowledge manifest digest drifted"}
            unexpected = [
                error
                for error in report.get("errors", [])
                if error not in repairable_exact
                and not any(error.startswith(prefix) for prefix in repairable_prefixes)
            ]
            if report.get("errors") and not unexpected:
                code = 0
        if code:
            report["status"] = "implementation-blocked"
            return emit(report, 2)
    if (
        new == "verifying"
        and schema_version == "2.0"
        and (
            has_change_set_contract(metadata.get("skill_version"))
            or has_quality_kernel_contract(metadata.get("skill_version"))
        )
    ):
        report, code = validate_packet_data(packet, state_override="verifying")
        if has_change_set_contract(metadata.get("skill_version")):
            change_set_record, handoff_errors = packet_change_set_record(packet, metadata)
            if handoff_errors:
                report["errors"] = sorted(set([*report.get("errors", []), *handoff_errors]))
                code = 2
        if code:
            report["status"] = "verification-blocked"
            return emit(report, 2)
        if has_quality_kernel_contract(metadata.get("skill_version")):
            projected = metadata.get("continuity_checkpoint")
            if not isinstance(projected, dict):
                return emit({"status": "verification-blocked", "errors": ["missing continuity checkpoint"]}, 2)
            continuity_record = json.loads(json.dumps(projected))
    if new == "accepted":
        report, code = validate_packet_data(packet, state_override="accepted")
        if code:
            report["status"] = "acceptance-blocked"
            return emit(report, 2)
    if checkpoint_invalidation is not None:
        metadata["updated_at"] = now
        append_packet_event(packet, metadata, "checkpoint-invalidated", checkpoint_invalidation)
    metadata["state"] = new
    metadata["updated_at"] = now
    metadata.setdefault("history", []).append({"from": old, "to": new, "at": now, "note": args.note})
    if new == "approved":
        design_record = {
            "by": args.approved_by,
            "at": now,
            "note": args.note,
        }
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
            design_record["requirement_revision"] = metadata["requirement_revision"]
            design_record["requirements_digest"] = metadata["requirements_digest"]
        if has_quality_kernel_contract(metadata.get("skill_version")):
            design_digest = current_design_digest(packet, metadata.get("documentation_profile"))
            if design_digest is None:
                return emit({"status": "invalid", "errors": ["cannot compute the design baseline digest"]}, 2)
            metadata["design_digest"] = design_digest
            design_record["design_digest"] = design_digest
        metadata.setdefault("approvals", {})["design"] = design_record
    transition_payload: dict[str, Any] = {"from": old, "to": new, "note": args.note}
    if new == "approved":
        transition_payload["design_approval"] = json.loads(json.dumps(metadata["approvals"]["design"]))
    if change_set_record is not None:
        transition_payload["change_set"] = change_set_record
    if continuity_record is not None:
        transition_payload["continuity_checkpoint"] = continuity_record
    if checkpoint_invalidation is not None:
        transition_payload["checkpoint_invalidation"] = json.loads(json.dumps(checkpoint_invalidation))
    write_packet(packet, metadata, "transition", transition_payload)
    return emit(
        {
            "status": "transitioned",
            "packet": str(packet),
            "from": old,
            "to": new,
            "requirement_revision": metadata.get("requirement_revision") if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS else None,
        }
    )


def record_iteration(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if metadata.get("schema_version") != "2.0":
        return emit({"status": "invalid", "errors": ["iteration control requires packet schema 2.0"]}, 2)
    if ITERATION_CAUSE_RE.fullmatch(args.cause_id) is None:
        return emit({"status": "invalid", "errors": ["cause-id must be a safe lowercase identifier"]}, 2)
    if not args.note.strip():
        return emit({"status": "invalid", "errors": ["iteration note must be non-empty"]}, 2)
    if args.reopened_owner is not None and args.reopened_owner not in ITERATION_OWNERS:
        return emit({"status": "invalid", "errors": ["reopened-owner must name an upstream core owner"]}, 2)

    try:
        cause_path = contained_path(
            packet / "artifacts",
            args.cause_file,
            label="iteration cause file",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if not cause_path.is_file():
        return emit({"status": "invalid", "errors": ["iteration cause file must be an existing regular file"]}, 2)
    cause_artifact = cause_path.relative_to(packet).as_posix()
    cause_digest = f"sha256:{hashlib.sha256(cause_path.read_bytes()).hexdigest()}"

    control = metadata.get("iteration_control")
    if not isinstance(control, dict):
        return emit({"status": "invalid", "errors": ["schema 2.0 packet requires intact iteration_control"]}, 2)
    control_errors = validate_iteration_control(metadata)
    if control_errors:
        return emit({"status": "invalid", "errors": control_errors}, 2)
    records = control.get("records")
    if (
        control.get("schema_version") != "1.0"
        or not isinstance(control.get("generation"), int)
        or isinstance(control.get("generation"), bool)
        or control["generation"] < 1
        or not isinstance(records, list)
    ):
        return emit({"status": "invalid", "errors": ["packet iteration_control is invalid"]}, 2)
    blocked = control.get("blocked")
    now = utc_now()
    generation_records = [
        item for item in records
        if isinstance(item, dict) and item.get("generation") == control["generation"]
    ]
    for item in generation_records:
        if item.get("cause_id") == args.cause_id and (
            item.get("cause_artifact") != cause_artifact or item.get("cause_digest") != cause_digest
        ):
            return emit({"status": "invalid", "errors": ["cause-id is already bound to different evidence in this generation"]}, 2)
        if item.get("cause_digest") == cause_digest and item.get("cause_id") != args.cause_id:
            return emit({"status": "invalid", "errors": ["cause evidence is already bound to a different cause-id in this generation"]}, 2)

    if args.outcome == "reassessed":
        if not isinstance(blocked, dict):
            return emit({"status": "invalid", "errors": ["no tripped iteration breaker requires reassessment"]}, 2)
        if args.reopened_owner is None:
            return emit({"status": "invalid", "errors": ["reassessment requires --reopened-owner"]}, 2)
        if blocked.get("kind") != args.kind or blocked.get("cause_id") != args.cause_id:
            return emit({"status": "invalid", "errors": ["reassessment must bind the blocked kind and cause-id"]}, 2)
        if blocked.get("cause_artifact") != cause_artifact or blocked.get("cause_digest") != cause_digest:
            return emit({"status": "invalid", "errors": ["reassessment must bind the original cause evidence"]}, 2)
        record = {
            "generation": control["generation"],
            "kind": args.kind,
            "cause_id": args.cause_id,
            "cause_artifact": cause_artifact,
            "cause_digest": cause_digest,
            "round": 0,
            "outcome": "reassessed",
            "reopened_owner": args.reopened_owner,
            "at": now,
            "note": args.note,
        }
        records.append(record)
        control["blocked"] = None
        control["generation"] += 1
        metadata["updated_at"] = now
        write_packet(packet, metadata, "iteration-reassessed", record)
        return emit({"status": "reassessed", "packet": str(packet), **record})

    if args.reopened_owner is not None:
        return emit({"status": "invalid", "errors": ["--reopened-owner is valid only for reassessed outcome"]}, 2)
    if isinstance(blocked, dict):
        return emit(
            {
                "status": "iteration-blocked",
                "errors": ["three failed rounds already reached; reassess and reopen the owning capability before another attempt"],
                "blocked": blocked,
            },
            2,
        )
    if metadata.get("state") == "blocked":
        return emit({"status": "iteration-blocked", "errors": ["resolve the existing packet blocker before another iteration"]}, 2)
    if metadata.get("state") in {"accepted", "archived"}:
        return emit({"status": "invalid", "errors": ["accepted or archived packets cannot record new iterations"]}, 2)

    matching = [
        item
        for item in records
        if isinstance(item, dict)
        and item.get("generation") == control["generation"]
        and item.get("kind") == args.kind
        and item.get("cause_id") == args.cause_id
    ]
    previous_failures = 0
    for item in reversed(matching):
        if item.get("outcome") != "failed":
            break
        previous_failures += 1
    round_number = previous_failures + 1 if args.outcome == "failed" else 0
    record = {
        "generation": control["generation"],
        "kind": args.kind,
        "cause_id": args.cause_id,
        "cause_artifact": cause_artifact,
        "cause_digest": cause_digest,
        "round": round_number,
        "outcome": args.outcome,
        "reopened_owner": None,
        "at": now,
        "note": args.note,
    }
    records.append(record)
    metadata["updated_at"] = now
    breaker_tripped = args.outcome == "failed" and round_number >= 3
    if breaker_tripped:
        old_state = metadata.get("state")
        blocked_record = {
            "generation": control["generation"],
            "kind": args.kind,
            "cause_id": args.cause_id,
            "cause_artifact": cause_artifact,
            "cause_digest": cause_digest,
            "round": round_number,
            "at": now,
        }
        control["blocked"] = blocked_record
        append_packet_event(packet, metadata, "iteration-recorded", record)
        metadata["state"] = "blocked"
        metadata.setdefault("history", []).append(
            {"from": old_state, "to": "blocked", "at": now, "note": f"three failed {args.kind} rounds for {args.cause_id}"}
        )
        write_packet(
            packet,
            metadata,
            "transition",
            {"from": old_state, "to": "blocked", "note": f"three failed {args.kind} rounds for {args.cause_id}"},
        )
    else:
        write_packet(packet, metadata, "iteration-recorded", record)
    return emit(
        {
            "status": "iteration-recorded",
            "packet": str(packet),
            "kind": args.kind,
            "cause_id": args.cause_id,
            "outcome": args.outcome,
            "round": round_number,
            "breaker_tripped": breaker_tripped,
        }
    )


def record_approval(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if any(not value.strip() for value in (args.id, args.by, args.note)):
        return emit({"status": "invalid", "errors": ["approval id, actor, and note must be non-empty"]}, 2)
    if args.kind in READINESS_APPROVAL_IDS:
        expected_id = READINESS_APPROVAL_IDS[args.kind]
        if metadata.get("schema_version") not in READINESS_SCHEMA_VERSIONS:
            return emit({"status": "invalid", "errors": ["readiness approvals require schema 1.1, 1.2, or 2.0"]}, 2)
        if args.id != expected_id:
            return emit({"status": "invalid", "errors": [f"{args.kind} approval id must be {expected_id}"]}, 2)
        if metadata.get("state") != "awaiting-approval":
            return emit(
                {"status": "invalid", "errors": ["readiness approvals may only be recorded while awaiting approval"]},
                2,
            )
    record = {"id": args.id, "by": args.by, "at": utc_now(), "note": args.note}
    if args.kind == "dependencies":
        missing = [
            name
            for name, value in (
                ("--dependency-ecosystem", args.dependency_ecosystem),
                ("--dependency-name", args.dependency_name),
                ("--dependency-version", args.dependency_version),
                ("--dependency-ref", args.dependency_ref),
                ("--dependency-file", args.dependency_file),
                ("--dependency-operation", args.dependency_operation),
            )
            if not value
        ]
        if missing:
            return emit({"status": "invalid", "errors": [f"dependency approval requires {', '.join(missing)}"]}, 2)
        result_sha256: dict[str, str] = {}
        for value in args.dependency_result_sha256:
            if "=" not in value:
                return emit(
                    {"status": "invalid", "errors": ["--dependency-result-sha256 must be PATH=sha256:<hex>"]},
                    2,
                )
            path, digest = value.split("=", 1)
            if path in result_sha256:
                return emit({"status": "invalid", "errors": [f"duplicate dependency result path: {path}"]}, 2)
            result_sha256[path] = digest
        record["dependency"] = {
            "ecosystem": args.dependency_ecosystem,
            "name": args.dependency_name,
            "version": args.dependency_version,
            "ref": args.dependency_ref,
            "command": args.dependency_command,
            "files": args.dependency_file,
            "operations": args.dependency_operation,
            "result_sha256": result_sha256,
        }
        dependency_errors = validate_dependency_approval(record)
        if dependency_errors:
            return emit({"status": "invalid", "errors": dependency_errors}, 2)
    if args.kind == "waivers":
        missing = [
            name
            for name, value in (
                ("--scope", args.scope),
                ("--blocker", args.blocker),
                ("--residual-risk", args.residual_risk),
                ("--expires-at", args.expires_at),
                ("--recheck-trigger", args.recheck_trigger),
            )
            if not value
        ]
        if missing:
            return emit({"status": "invalid", "errors": [f"waiver approval requires {', '.join(missing)}"]}, 2)
        expiry = parsed_timestamp(args.expires_at)
        now = parsed_timestamp(record["at"])
        if expiry is None or now is None or expiry <= now:
            return emit({"status": "invalid", "errors": ["waiver --expires-at must be a future timezone-aware timestamp"]}, 2)
        record.update(
            {
                "scope": args.scope,
                "blockers": args.blocker,
                "residual_risk": args.residual_risk,
                "expires_at": args.expires_at,
                "recheck_trigger": args.recheck_trigger,
            }
        )
    if metadata.get("schema_version") in CONTENT_BOUND_SCHEMA_VERSIONS and args.kind == "requirements":
        semantic_errors = semantic_metadata_errors(
            metadata,
            declared_trace_ids=declared_trace_ids(metadata),
            require_ready=True,
        )
        if semantic_errors:
            return emit({"status": "invalid", "errors": semantic_errors}, 2)
        validation, validation_code = validate_packet_data(packet)
        if validation_code:
            validation["status"] = "approval-blocked"
            return emit(validation, 2)
        digest = current_requirements_digest(packet, metadata.get("documentation_profile"))
        if digest is None:
            return emit({"status": "invalid", "errors": ["cannot compute the requirement baseline digest"]}, 2)
        record["requirement_revision"] = metadata["requirement_revision"]
        record["requirements_digest"] = digest
        metadata["requirements_digest"] = digest
    approvals = metadata.setdefault("approvals", {})
    if not isinstance(approvals, dict):
        return emit({"status": "invalid", "errors": ["approvals must be an object"]}, 2)
    records = approvals.setdefault(args.kind, [])
    if not isinstance(records, list):
        return emit({"status": "invalid", "errors": [f"approvals.{args.kind} must be a list"]}, 2)
    records.append(record)
    if args.kind == "dependencies" and args.id not in metadata.setdefault("dependency_changes", []):
        metadata["dependency_changes"].append(args.id)
    metadata["updated_at"] = record["at"]
    write_packet(packet, metadata, "approval-recorded", {"kind": args.kind, "record": record})
    return emit({"status": "recorded", "kind": args.kind, "record": record})


def record_ambiguity(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if metadata.get("schema_version") not in CONTENT_BOUND_SCHEMA_VERSIONS:
        return emit({"status": "invalid", "errors": ["ambiguity records require a content-bound schema"]}, 2)
    if metadata.get("state") not in {"discovering", "awaiting-approval", "implementing", "verifying"}:
        return emit({"status": "invalid", "errors": ["ambiguities cannot be recorded in the current state"]}, 2)
    semantic_errors = semantic_metadata_errors(
        metadata,
        declared_trace_ids=declared_trace_ids(metadata),
        require_ready=False,
    )
    if semantic_errors:
        return emit({"status": "invalid", "errors": semantic_errors}, 2)
    if args.materiality == "high-risk" and args.owner != "user":
        return emit({"status": "invalid", "errors": ["high-risk ambiguity must be user-owned"]}, 2)
    if (
        metadata.get("state") in {"implementing", "verifying"}
        and args.owner == "user"
        and args.materiality == "low"
    ):
        return emit(
            {"status": "invalid", "errors": ["late user-owned ambiguity must be material or high-risk and reopen approval"]},
            2,
        )
    interpretations = [value.strip() for value in args.interpretation if value.strip()]
    if len(interpretations) < 2 or len(set(interpretations)) != len(interpretations):
        return emit({"status": "invalid", "errors": ["provide at least two distinct --interpretation values"]}, 2)
    affected = list(dict.fromkeys(args.affects))
    known_trace_ids = declared_trace_ids(metadata)
    malformed = [
        value
        for value in affected
        if not any(ID_PATTERNS[kind].fullmatch(value) for kind in ("acceptance", "scope", "verification"))
    ]
    if malformed or set(affected) - known_trace_ids:
        return emit(
            {
                "status": "invalid",
                "errors": [
                    f"--affects values must be declared AC/SC/VO identifiers; invalid={sorted(set(malformed) | (set(affected) - known_trace_ids))}"
                ],
            },
            2,
        )
    records = metadata.get("ambiguities")
    ambiguity_ids = metadata.get("ambiguity_ids")
    if not isinstance(records, list) or not isinstance(ambiguity_ids, list):
        return emit({"status": "invalid", "errors": ["ambiguities and ambiguity_ids must be lists"]}, 2)
    numbers = [int(match.group(1)) for value in ambiguity_ids if isinstance(value, str) and (match := re.fullmatch(r"AMB-(\d+)", value))]
    ambiguity_id = f"AMB-{max(numbers, default=0) + 1}"
    now = utc_now()
    record = {
        "id": ambiguity_id,
        "summary": args.summary.strip(),
        "source": args.source.strip(),
        "interpretations": interpretations,
        "evidence": [value.strip() for value in args.evidence if value.strip()],
        "materiality": args.materiality,
        "owner": args.owner,
        "affected_ids": affected,
        "recommendation": args.recommendation.strip(),
        "status": "open",
        "created_at": now,
        "discovered_in_revision": metadata["requirement_revision"],
        "resolution": None,
    }
    if any(not record[field] for field in ("summary", "source", "recommendation")):
        return emit({"status": "invalid", "errors": ["summary, source, and recommendation must be non-empty"]}, 2)
    records.append(record)
    ambiguity_ids.append(ambiguity_id)
    if (
        metadata.get("collaboration_profile") == "execute"
        and args.owner == "user"
        and args.materiality in {"material", "high-risk"}
    ):
        metadata["collaboration_profile"] = "checkpointed"
    metadata["updated_at"] = now
    write_packet(packet, metadata, "ambiguity-recorded", {"record": record})
    return emit(
        {
            "status": "recorded",
            "ambiguity": record,
            "collaboration_profile": metadata.get("collaboration_profile"),
        }
    )


def resolve_ambiguity(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if metadata.get("schema_version") not in CONTENT_BOUND_SCHEMA_VERSIONS:
        return emit({"status": "invalid", "errors": ["ambiguity resolution requires a content-bound schema"]}, 2)
    record = find_ambiguity(metadata, args.id)
    if record is None:
        return emit({"status": "invalid", "errors": [f"unknown ambiguity {args.id}"]}, 2)
    if record.get("status") != "open":
        return emit({"status": "invalid", "errors": [f"ambiguity {args.id} is already resolved"]}, 2)
    owner = record.get("owner")
    materiality = record.get("materiality")
    if owner == "user":
        if metadata.get("state") != "awaiting-approval":
            return emit({"status": "invalid", "errors": ["user-owned ambiguity may only be resolved while awaiting approval"]}, 2)
        if args.status not in {"user-confirmed", "deferred-out-of-scope"}:
            return emit({"status": "invalid", "errors": ["user-owned ambiguity requires user confirmation or deferral"]}, 2)
    elif owner == "codex":
        allowed = {"resolved-by-evidence"}
        if materiality == "low":
            allowed.update({"safe-assumption", "deferred-out-of-scope"})
        if args.status not in allowed:
            return emit({"status": "invalid", "errors": ["resolution status is not authorized for this Codex-owned ambiguity"]}, 2)
    else:
        return emit({"status": "invalid", "errors": ["ambiguity has an invalid owner"]}, 2)
    evidence = [value.strip() for value in args.evidence if value.strip()]
    if not args.by.strip() or not args.resolution.strip() or not evidence:
        return emit({"status": "invalid", "errors": ["actor, resolution, and at least one evidence item are required"]}, 2)
    now = utc_now()
    record["status"] = args.status
    record["resolution"] = {
        "by": args.by.strip(),
        "at": now,
        "text": args.resolution.strip(),
        "evidence": evidence,
    }
    metadata["updated_at"] = now
    write_packet(packet, metadata, "ambiguity-resolved", {"record": record})
    return emit({"status": "resolved", "ambiguity": record})


def heading_body(text: str, heading: str) -> str | None:
    match = re.search(rf"(?ms)^##\s+{re.escape(heading)}\s*$\n(.*?)(?=^##\s+|\Z)", text)
    return match.group(1).strip() if match else None


def placeholder_error(filename: str, heading: str, body: str | None) -> str | None:
    if body is None:
        return f"{filename}: missing heading `{heading}`"
    meaningful = [line.strip() for line in body.splitlines() if line.strip() and not re.fullmatch(r"[-|: ]+", line)]
    if not meaningful:
        return f"{filename}: empty section `{heading}`"
    if PLACEHOLDER_RE.search(body):
        return f"{filename}: unresolved placeholder in `{heading}`"
    return None


def replace_heading_body(text: str, heading: str, body: str) -> str:
    pattern = re.compile(rf"(?ms)(^##\s+{re.escape(heading)}\s*$\n)(.*?)(?=^##\s+|\Z)")
    if pattern.search(text) is None:
        suffix = "" if text.endswith("\n") else "\n"
        return f"{text}{suffix}\n## {heading}\n\n{body.rstrip()}\n"
    return pattern.sub(lambda match: match.group(1) + "\n" + body.rstrip() + "\n\n", text, count=1)


def labeled_fields(body: str | None, fields: Iterable[str]) -> tuple[dict[str, str], list[str]]:
    values: dict[str, str] = {}
    errors: list[str] = []
    if body is None:
        return values, ["section is missing"]
    for field in fields:
        matches = re.findall(rf"(?im)^\s*(?:[-*]\s*)?{re.escape(field)}\s*:\s*(.+?)\s*$", body)
        if len(matches) != 1 or not matches[0].strip():
            errors.append(f"requires exactly one non-empty `{field}` field")
        else:
            values[field] = matches[0].strip()
    return values, errors


def engineering_context_projection_fingerprint(value: dict[str, Any]) -> str:
    """Digest every governed readiness field while excluding only digest claims."""

    projection = {
        key: nested
        for key, nested in value.items()
        if key != "projection_fingerprint"
    }
    payload = json.dumps(projection, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(
        f"dev-flow-engineering-context-projection-{ENGINEERING_CONTEXT_PROJECTION_SCHEMA_VERSION}\0".encode("ascii")
        + payload
    ).hexdigest()


def validate_engineering_context_projection(value: dict[str, Any]) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    for field in ("schema_version", "tier", "outcome", "quality_coverage"):
        if field not in value:
            errors.append(f"context-readiness.json canonical projection requires {field}")
    claimed = value.get("projection_fingerprint")
    observed = engineering_context_projection_fingerprint(value)
    if not isinstance(claimed, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", claimed) is None:
        errors.append("context-readiness.json requires a valid canonical projection fingerprint")
    elif claimed != observed:
        errors.append("context-readiness.json canonical projection fingerprint drifted")
    return (observed if not errors else None), errors


def engineering_context_fingerprint(packet: Path) -> tuple[str | None, list[str]]:
    path = packet / "context-readiness.json"
    if not path.is_file():
        return None, ["context-readiness.json is required by quality-kernel-v1"]
    try:
        value = read_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return None, [f"context-readiness.json cannot be read: {exc}"]
    outcome = value.get("outcome")
    if outcome in {"blocked", "invalid", "checkpoint"}:
        return None, [f"context-readiness.json outcome {outcome!r} is not implementation-ready"]
    fingerprint = value.get("fingerprint")
    if not isinstance(fingerprint, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint) is None:
        return None, ["context-readiness.json requires a valid fingerprint"]
    return validate_engineering_context_projection(value)


def continuity_ledger(packet: Path, metadata: dict[str, Any]) -> tuple[str | None, Path | None]:
    family = documentation_family(metadata.get("documentation_profile"))
    filename = "trace.md" if family == "trace" else "execution.md" if family == "governed" else None
    return (filename, packet / filename) if filename is not None else (None, None)


def continuity_checkpoint_errors(
    packet: Path,
    metadata: dict[str, Any],
    *,
    effective_state: str,
) -> list[str]:
    if not has_quality_kernel_contract(metadata.get("skill_version")):
        return []
    if effective_state not in {"implementing", "verifying", "accepted", "archived"}:
        return []
    checkpoint = metadata.get("continuity_checkpoint")
    if not isinstance(checkpoint, dict) or set(checkpoint) != CONTINUITY_CHECKPOINT_FIELDS:
        return ["packet.json: quality-kernel-v1 requires an exact continuity_checkpoint"]
    errors: list[str] = []
    if checkpoint.get("schema_version") != "1.1":
        errors.append("packet.json: continuity_checkpoint schema_version must be 1.1")
    if checkpoint.get("trigger") not in CONTINUITY_TRIGGERS:
        errors.append("packet.json: continuity_checkpoint has an invalid trigger")
    if effective_state in {"verifying", "accepted", "archived"} and checkpoint.get("trigger") != "pre-verification":
        errors.append("packet.json: verification requires a fresh pre-verification continuity checkpoint")
    if checkpoint.get("requirement_revision") != metadata.get("requirement_revision"):
        errors.append("packet.json: continuity checkpoint requirement revision is stale")
    if checkpoint.get("requirements_digest") != current_requirements_digest(packet, metadata.get("documentation_profile")):
        errors.append("packet.json: continuity checkpoint requirement digest is stale")
    if checkpoint.get("design_digest") != current_design_digest(packet, metadata.get("documentation_profile")):
        errors.append("packet.json: continuity checkpoint design digest is stale")
    context_fingerprint, context_errors = engineering_context_fingerprint(packet)
    errors.extend(context_errors)
    if checkpoint.get("engineering_context_fingerprint") != context_fingerprint:
        errors.append("packet.json: continuity checkpoint engineering context is stale")
    errors.extend(
        repository_snapshot_drift_errors(
            metadata,
            checkpoint.get("repository_snapshot"),
            check_worktree=effective_state in {"verifying", "accepted", "archived"},
        )
    )
    reconciliation = checkpoint.get("repository_reconciliation")
    if not isinstance(reconciliation, dict) or set(reconciliation) != {
        "changed_since_prior",
        "prior_snapshot_sha256",
        "change_kinds",
        "accepted_heads",
        "evidence",
    }:
        errors.append("packet.json: continuity checkpoint requires exact repository reconciliation evidence")
    else:
        if not isinstance(reconciliation.get("changed_since_prior"), bool):
            errors.append("packet.json: repository reconciliation changed_since_prior must be boolean")
        prior_digest = reconciliation.get("prior_snapshot_sha256")
        if prior_digest is not None and (
            not isinstance(prior_digest, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", prior_digest) is None
        ):
            errors.append("packet.json: repository reconciliation prior snapshot digest is invalid")
        if not isinstance(reconciliation.get("evidence"), str) or not reconciliation["evidence"].strip():
            errors.append("packet.json: repository reconciliation evidence must be non-empty")
        change_kinds = reconciliation.get("change_kinds")
        if (
            not isinstance(change_kinds, list)
            or len(change_kinds) != len(set(change_kinds))
            or change_kinds != sorted(change_kinds)
            or any(value not in {"head", "identity", "worktree"} for value in change_kinds)
        ):
            errors.append("packet.json: repository reconciliation change_kinds must be a sorted unique known list")
            change_kinds = []
        accepted_heads = reconciliation.get("accepted_heads")
        if not isinstance(accepted_heads, dict) or any(
            not isinstance(root, str)
            or not isinstance(oid, str)
            or (oid != "unborn" and re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", oid) is None)
            for root, oid in (accepted_heads.items() if isinstance(accepted_heads, dict) else ())
        ):
            errors.append("packet.json: repository reconciliation accepted_heads must map roots to exact Git OIDs")
            accepted_heads = {}
        current_heads = {
            item.get("root"): item.get("head")
            for item in checkpoint.get("repository_snapshot", [])
            if isinstance(item, dict) and item.get("vcs") == "git"
        } if isinstance(checkpoint.get("repository_snapshot"), list) else {}
        if any(current_heads.get(root) != oid for root, oid in accepted_heads.items()):
            errors.append("packet.json: repository reconciliation accepted_heads do not match the checkpoint")
        if ("head" in change_kinds) != bool(accepted_heads):
            errors.append("packet.json: HEAD changes require exact accepted_heads and unchanged HEAD requires none")
    active_ids = checkpoint.get("active_ids")
    if not isinstance(active_ids, list) or not active_ids or any(not isinstance(value, str) for value in active_ids):
        errors.append("packet.json: continuity_checkpoint active_ids must be a non-empty string list")
        active_set: set[str] = set()
    else:
        active_set = set(active_ids)
        if len(active_set) != len(active_ids):
            errors.append("packet.json: continuity_checkpoint active_ids must be unique")
        undeclared = active_set - declared_trace_ids(metadata)
        if undeclared:
            errors.append(f"packet.json: continuity_checkpoint uses undeclared IDs: {sorted(undeclared)}")
        if not any(value.startswith("AC-") for value in active_set) or not any(value.startswith("SC-") for value in active_set):
            errors.append("packet.json: continuity_checkpoint requires at least one AC and one SC identifier")
        if effective_state in {"verifying", "accepted", "archived"} and not any(value.startswith("VO-") for value in active_set):
            errors.append("packet.json: pre-verification continuity requires at least one VO identifier")
    for field in ("active_objective", "last_evidence", "next_action", "stop_condition"):
        if not isinstance(checkpoint.get(field), str) or not checkpoint[field].strip():
            errors.append(f"packet.json: continuity_checkpoint requires non-empty {field}")
    if checkpoint.get("drift") != "aligned":
        errors.append("packet.json: continuity checkpoint drift must be aligned before implementation or verification")
    if parsed_timestamp(checkpoint.get("at")) is None:
        errors.append("packet.json: continuity_checkpoint requires a timezone-aware timestamp")
    ledger_name, ledger_path = continuity_ledger(packet, metadata)
    if checkpoint.get("ledger") != ledger_name or ledger_path is None or not ledger_path.is_file():
        errors.append("packet.json: continuity_checkpoint ledger is invalid")
    else:
        body = heading_body(ledger_path.read_text(encoding="utf-8"), "Continuity checkpoint")
        section_error = placeholder_error(ledger_name or "ledger", "Continuity checkpoint", body)
        if section_error:
            errors.append(section_error)
        elif body is not None:
            digest = "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest()
            if checkpoint.get("section_sha256") != digest:
                errors.append("packet.json: continuity checkpoint section drifted from its projection")
            fields, field_errors = labeled_fields(body, CONTINUITY_FIELDS)
            errors.extend(f"{ledger_name}: Continuity checkpoint {error}" for error in field_errors)
            if not field_errors:
                expected_values = {
                    "Trigger": str(checkpoint.get("trigger")),
                    "Requirement baseline": f"revision {checkpoint.get('requirement_revision')}; {checkpoint.get('requirements_digest')}",
                    "Design baseline": str(checkpoint.get("design_digest")),
                    "Engineering context": str(checkpoint.get("engineering_context_fingerprint")),
                    "Repository baseline": repository_snapshot_summary(checkpoint.get("repository_snapshot")),
                    "Repository reconciliation": repository_reconciliation_summary(
                        checkpoint.get("repository_reconciliation")
                    ),
                    "Active objective and slice": f"{checkpoint.get('active_objective')}; IDs: {', '.join(active_ids if isinstance(active_ids, list) else [])}",
                    "Last completed and evidence": str(checkpoint.get("last_evidence")),
                    "Next action and stop condition": f"{checkpoint.get('next_action')}; STOP: {checkpoint.get('stop_condition')}",
                    "Drift review": str(checkpoint.get("drift")),
                }
                if fields != expected_values:
                    errors.append(f"{ledger_name}: Continuity checkpoint fields do not match packet projection")
    return errors


def record_checkpoint(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if not has_quality_kernel_contract(metadata.get("skill_version")):
        return emit({"status": "invalid", "errors": ["record-checkpoint requires quality-kernel-v1"]}, 2)
    if metadata.get("state") not in {"awaiting-approval", "approved", "implementing"}:
        return emit({"status": "invalid", "errors": ["checkpoint may be recorded only before verification"]}, 2)
    if args.trigger == "pre-verification" and metadata.get("state") != "implementing":
        return emit({"status": "invalid", "errors": ["pre-verification checkpoint requires implementing state"]}, 2)
    if args.drift == "reopened" and metadata.get("state") != "awaiting-approval":
        return emit({"status": "invalid", "errors": ["reopened drift requires awaiting-approval state"]}, 2)
    active_ids = list(dict.fromkeys(value.strip() for value in args.active_id if value.strip()))
    undeclared = set(active_ids) - declared_trace_ids(metadata)
    if undeclared or not any(value.startswith("AC-") for value in active_ids) or not any(
        value.startswith("SC-") for value in active_ids
    ):
        return emit(
            {
                "status": "invalid",
                "errors": [
                    "checkpoint active IDs require declared AC and SC identifiers"
                    + (f"; undeclared={sorted(undeclared)}" if undeclared else "")
                ],
            },
            2,
        )
    if args.trigger == "pre-verification" and not any(value.startswith("VO-") for value in active_ids):
        return emit({"status": "invalid", "errors": ["pre-verification checkpoint requires a declared VO ID"]}, 2)
    requirement_digest = current_requirements_digest(packet, metadata.get("documentation_profile"))
    design_digest = current_design_digest(packet, metadata.get("documentation_profile"))
    if args.drift == "aligned" and (
        requirement_digest is None
        or requirement_digest != metadata.get("requirements_digest")
        or design_digest is None
        or design_digest != metadata.get("design_digest")
    ):
        return emit({"status": "invalid", "errors": ["approved requirement or design baseline is missing or stale"]}, 2)
    context_fingerprint, context_errors = engineering_context_fingerprint(packet)
    if context_errors:
        return emit({"status": "invalid", "errors": context_errors}, 2)
    source_snapshot, snapshot_errors = repository_snapshot(metadata)
    if snapshot_errors:
        return emit({"status": "invalid", "errors": snapshot_errors}, 2)
    previous_checkpoint = metadata.get("continuity_checkpoint")
    previous_snapshot = (
        previous_checkpoint.get("repository_snapshot")
        if isinstance(previous_checkpoint, dict)
        else None
    )
    change_kinds = repository_snapshot_change_kinds(previous_snapshot, source_snapshot) if previous_snapshot is not None else set()
    reconciliation_text = args.repository_reconciliation.strip() if args.repository_reconciliation else ""
    accepted_heads, accepted_head_errors = parse_accepted_heads(args.accept_head)
    if accepted_head_errors:
        return emit({"status": "invalid", "errors": accepted_head_errors}, 2)
    if change_kinds and not reconciliation_text:
        return emit(
            {
                "status": "invalid",
                "errors": [
                    "repository bytes or identity changed since the prior checkpoint; inspect the delta and provide --repository-reconciliation"
                ],
            },
            2,
        )
    if "identity" in change_kinds:
        return emit(
            {
                "status": "invalid",
                "errors": [
                    "repository identity changed; reopen the affected scope or create a new packet instead of rebinding it in place"
                ],
            },
            2,
        )
    expected_heads = repository_head_changes(previous_snapshot, source_snapshot)
    if "head" in change_kinds:
        if args.trigger not in {"premise-change", "reconciliation"}:
            return emit(
                {
                    "status": "invalid",
                    "errors": [
                        "repository HEAD changed; only premise-change or reconciliation may establish a reviewed new baseline"
                    ],
                },
                2,
            )
        if accepted_heads != expected_heads:
            return emit(
                {
                    "status": "invalid",
                    "errors": [
                        "repository HEAD reconciliation requires one exact --accept-head ROOT=OID for every changed root",
                        f"expected={expected_heads}; received={accepted_heads}",
                    ],
                },
                2,
            )
    elif accepted_heads:
        return emit({"status": "invalid", "errors": ["--accept-head is only valid when HEAD changed"]}, 2)
    if "worktree" in change_kinds and args.trigger in {"implementation-start", "resume", "slice-start", "user-steering"}:
        return emit(
            {
                "status": "invalid",
                "errors": [
                    "an open-slice worktree delta cannot be silently rebound by this trigger; inspect it and use reconciliation or a sealed boundary"
                ],
            },
            2,
        )
    reconciliation = {
        "changed_since_prior": bool(change_kinds),
        "prior_snapshot_sha256": repository_snapshot_digest(previous_snapshot),
        "change_kinds": sorted(change_kinds),
        "accepted_heads": accepted_heads,
        "evidence": reconciliation_text
        or ("initial repository snapshot" if previous_snapshot is None else "repository snapshot unchanged since the prior checkpoint"),
    }
    ledger_name, ledger_path = continuity_ledger(packet, metadata)
    if ledger_name is None or ledger_path is None or not ledger_path.is_file():
        return emit({"status": "invalid", "errors": ["cannot locate the continuity ledger"]}, 2)
    now = utc_now()
    body = "\n".join(
        (
            f"- Trigger: {args.trigger}",
            f"- Requirement baseline: revision {metadata.get('requirement_revision')}; {requirement_digest}",
            f"- Design baseline: {design_digest}",
            f"- Engineering context: {context_fingerprint}",
            f"- Repository baseline: {repository_snapshot_summary(source_snapshot)}",
            f"- Repository reconciliation: {repository_reconciliation_summary(reconciliation)}",
            f"- Active objective and slice: {args.objective.strip()}; IDs: {', '.join(active_ids)}",
            f"- Last completed and evidence: {args.last_evidence.strip()}",
            f"- Next action and stop condition: {args.next_action.strip()}; STOP: {args.stop_condition.strip()}",
            f"- Drift review: {args.drift}",
        )
    )
    ledger_text = ledger_path.read_text(encoding="utf-8")
    atomic_write_text(ledger_path, replace_heading_body(ledger_text, "Continuity checkpoint", body))
    checkpoint = {
        "schema_version": "1.1",
        "trigger": args.trigger,
        "requirement_revision": metadata.get("requirement_revision"),
        "requirements_digest": requirement_digest,
        "design_digest": design_digest,
        "engineering_context_fingerprint": context_fingerprint,
        "repository_snapshot": source_snapshot,
        "repository_reconciliation": reconciliation,
        "active_ids": active_ids,
        "active_objective": args.objective.strip(),
        "last_evidence": args.last_evidence.strip(),
        "next_action": args.next_action.strip(),
        "stop_condition": args.stop_condition.strip(),
        "drift": args.drift,
        "ledger": ledger_name,
        "section_sha256": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "at": now,
    }
    metadata["continuity_checkpoint"] = checkpoint
    metadata["updated_at"] = now
    write_packet(packet, metadata, "checkpoint-recorded", checkpoint)
    report, code = validate_packet_data(packet)
    if code and metadata.get("state") in {"approved", "implementing"}:
        report["status"] = "checkpoint-invalid"
        return emit(report, 2)
    return emit({"status": "recorded", "packet": str(packet), "checkpoint": checkpoint})


def resume_packet(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, load_errors = load_packet(packet)
    report, code = validate_packet_data(packet) if metadata else (
        {"status": "invalid", "packet": str(packet), "errors": load_errors, "warnings": []},
        2,
    )
    checkpoint = metadata.get("continuity_checkpoint") if isinstance(metadata, dict) else None
    resume_status: str | None = None
    if metadata and has_quality_kernel_contract(metadata.get("skill_version")) and isinstance(checkpoint, dict):
        observed_snapshot, observation_errors = repository_snapshot(metadata)
        change_kinds = (
            repository_snapshot_change_kinds(checkpoint.get("repository_snapshot"), observed_snapshot)
            if not observation_errors
            else {"identity", "head", "worktree"}
        )
        if observation_errors:
            report["errors"] = sorted(set([*report.get("errors", []), *observation_errors]))
            code = 2
        elif change_kinds & {"identity", "head"}:
            details = repository_snapshot_drift_errors(
                metadata,
                checkpoint.get("repository_snapshot"),
                check_worktree=False,
            )
            report["errors"] = sorted(set([*report.get("errors", []), *details]))
            resume_status = "blocked"
            code = 2
        elif "worktree" in change_kinds:
            trigger = checkpoint.get("trigger")
            if trigger in OPEN_CONTINUITY_TRIGGERS:
                report["errors"] = sorted(
                    set(
                        [
                            *report.get("errors", []),
                            "open-slice-delta: repository bytes changed inside an open implementation slice; inspect the exact delta and record an explicit reconciliation or sealed boundary checkpoint",
                        ]
                    )
                )
                resume_status = "reconciliation-required"
            else:
                report["errors"] = sorted(
                    set(
                        [
                            *report.get("errors", []),
                            "sealed checkpoint worktree drift: repository bytes changed after the last coherent boundary",
                        ]
                    )
                )
                resume_status = "blocked"
            code = 2
        unobservable = [
            item.get("root")
            for item in observed_snapshot
            if isinstance(item, dict) and item.get("observable") is False
        ]
        if unobservable:
            report["warnings"] = sorted(
                set(
                    [
                        *report.get("warnings", []),
                        "repository byte continuity is not mechanically observable for non-Git roots: "
                        + ", ".join(str(value) for value in unobservable),
                    ]
                )
            )
    open_ambiguities = [
        record.get("id")
        for record in metadata.get("ambiguities", [])
        if isinstance(record, dict) and record.get("status") == "open"
    ] if isinstance(metadata, dict) and isinstance(metadata.get("ambiguities"), list) else []
    legacy = bool(metadata) and not has_quality_kernel_contract(metadata.get("skill_version"))
    payload = {
        "status": (
            "legacy-readable"
            if legacy and code == 0
            else "ready"
            if code == 0
            else resume_status or "blocked"
        ),
        "packet": str(packet),
        "change_id": metadata.get("change_id") if isinstance(metadata, dict) else None,
        "state": metadata.get("state") if isinstance(metadata, dict) else None,
        "requirement_revision": metadata.get("requirement_revision") if isinstance(metadata, dict) else None,
        "requirements_digest": metadata.get("requirements_digest") if isinstance(metadata, dict) else None,
        "design_digest": metadata.get("design_digest") if isinstance(metadata, dict) else None,
        "open_ambiguities": open_ambiguities,
        "checkpoint": checkpoint,
        "legacy_unbound": legacy,
        "errors": report.get("errors", []),
        "warnings": report.get("warnings", []),
    }
    return emit(payload, 0 if code == 0 else 2)


def knowledge_binding_errors(
    packet: Path,
    metadata: dict[str, Any],
    *,
    effective_state: str,
) -> list[str]:
    immutable_quality = packet_has_immutable_creation_capability(packet, QUALITY_KERNEL_SKILL_VERSION_TAG)
    if not immutable_quality and not has_quality_kernel_contract(metadata.get("skill_version")):
        return []
    binding = metadata.get("knowledge_manifest")
    if binding is None:
        return (
            ["packet.json: verification requires an explicit project-knowledge disposition"]
            if effective_state in {"verifying", "accepted", "archived"}
            else []
        )
    expected_keys = {
        "schema_version",
        "impact",
        "rationale",
        "repository_root",
        "project_root",
        "changes_root",
        "convention_path",
        "manifest",
        "sha256",
    }
    if not isinstance(binding, dict) or set(binding) != expected_keys:
        return ["packet.json: knowledge_manifest must use the exact quality-kernel-v1 schema"]
    errors: list[str] = []
    if binding.get("schema_version") != "1.0":
        errors.append("packet.json: knowledge_manifest schema_version must be 1.0")
    impact = binding.get("impact")
    if impact not in knowledge_system.KNOWLEDGE_IMPACTS:
        errors.append("packet.json: knowledge_manifest has an invalid impact")
    if not isinstance(binding.get("rationale"), str) or not binding["rationale"].strip():
        errors.append("packet.json: knowledge_manifest rationale must be non-empty")
    if impact == "none":
        if any(
            binding.get(field) is not None
            for field in ("repository_root", "project_root", "changes_root", "convention_path", "manifest", "sha256")
        ):
            errors.append("packet.json: no-impact knowledge disposition must not bind a manifest")
        return errors
    roots = metadata.get("repository_roots")
    root_text = binding.get("repository_root")
    if not isinstance(roots, list) or root_text not in roots or not isinstance(root_text, str):
        return [*errors, "packet.json: knowledge manifest must bind a declared repository root"]
    root = Path(root_text).resolve()
    manifest_value = binding.get("manifest")
    try:
        manifest_path = contained_path(
            root,
            manifest_value,
            label="knowledge manifest",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        return [*errors, str(exc)]
    if manifest_path.name != "manifest.json" or not manifest_path.is_file():
        return [*errors, "packet.json: knowledge manifest must name an existing manifest.json"]
    observed_digest = "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    if binding.get("sha256") != observed_digest:
        errors.append("packet.json: project-knowledge manifest digest drifted")
    try:
        manifest = read_json(manifest_path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [*errors, f"project-knowledge manifest cannot be read: {exc}"]
    if manifest.get("change_id") != metadata.get("change_id"):
        errors.append("project-knowledge manifest change_id does not match the packet")
    authority_binding = manifest.get("authority_binding")
    if immutable_quality and authority_binding is None:
        errors.append("new quality packet material knowledge requires a complete authority_binding")
    if authority_binding is not None:
        expected_authority_keys = {
            "schema_version",
            "change_id",
            "requirements",
            "design",
            "identifier_sets",
        }
        if not isinstance(authority_binding, dict):
            errors.append("project-knowledge manifest authority_binding must be an object")
        else:
            if set(authority_binding) != expected_authority_keys:
                errors.append("project-knowledge authority binding must use the exact schema")
            if authority_binding.get("schema_version") != "1.0":
                errors.append("project-knowledge authority binding schema_version must be 1.0")
            if authority_binding.get("change_id") != metadata.get("change_id"):
                errors.append("project-knowledge authority binding change_id does not match the packet")
            documents = manifest.get("documents")
            dossier_format = manifest.get("format")
            expected_paths: dict[str, Any] = {"requirements": None, "design": None}
            if isinstance(documents, dict):
                if dossier_format == "governed":
                    expected_paths = {
                        "requirements": documents.get("requirements"),
                        "design": documents.get("design"),
                    }
                elif dossier_format == "single":
                    expected_paths = {
                        "requirements": documents.get("change"),
                        "design": documents.get("change"),
                    }
            current_digests = {
                "requirements": current_requirements_digest(packet, metadata.get("documentation_profile")),
                "design": current_design_digest(packet, metadata.get("documentation_profile")),
            }
            approved_digests = {
                "requirements": metadata.get("requirements_digest"),
                "design": metadata.get("design_digest"),
            }
            for role in ("requirements", "design"):
                record = authority_binding.get(role)
                if not isinstance(record, dict) or set(record) != {"path", "sha256"}:
                    errors.append(f"project-knowledge authority binding {role} must use exact path and sha256 fields")
                    continue
                if record.get("path") != expected_paths[role]:
                    errors.append(f"project-knowledge authority binding {role} path does not match the manifest document role")
                digest = record.get("sha256")
                if digest != current_digests[role] or (
                    approved_digests[role] is not None and digest != approved_digests[role]
                ):
                    errors.append(f"project-knowledge authority binding {role} bytes do not match the packet baseline")
            identifier_sets = authority_binding.get("identifier_sets")
            expected_sets = {
                "acceptance_criteria": metadata.get("acceptance_ids"),
                "scope": metadata.get("scope_ids"),
                "verification_obligations": metadata.get("verification_ids"),
            }
            if not isinstance(identifier_sets, dict) or set(identifier_sets) != set(expected_sets):
                errors.append("project-knowledge authority binding identifier_sets must use the exact identifier families")
            else:
                for family, expected_values in expected_sets.items():
                    observed_values = identifier_sets.get(family)
                    if (
                        not isinstance(observed_values, list)
                        or not isinstance(expected_values, list)
                        or len(observed_values) != len(set(observed_values))
                        or len(expected_values) != len(set(expected_values))
                        or set(observed_values) != set(expected_values)
                    ):
                        errors.append(
                            f"project-knowledge authority binding {family} must exactly equal the packet identifier set"
                        )
    knowledge = manifest.get("knowledge")
    if not isinstance(knowledge, dict) or knowledge.get("impact") != impact:
        errors.append("project-knowledge manifest impact does not match the packet disposition")
    report = knowledge_system.validate_knowledge_system(
        root,
        project_root=binding.get("project_root"),
        changes_root=binding.get("changes_root"),
        convention_path=binding.get("convention_path"),
        change_id=str(metadata.get("change_id")),
    )
    if report.get("status") != "valid":
        errors.extend(f"project knowledge: {error}" for error in report.get("errors", []))
    changes_root = report.get("roots", {}).get("changes") if isinstance(report.get("roots"), dict) else None
    if isinstance(changes_root, str):
        expected_manifest = (root / changes_root / str(metadata.get("change_id")) / "manifest.json").resolve()
        if manifest_path.resolve() != expected_manifest:
            errors.append("packet.json: knowledge manifest is not the configured change dossier")
    if effective_state in {"accepted", "archived"}:
        if manifest.get("status") not in knowledge_system.TERMINAL_ACCEPTED_STATUSES:
            errors.append("accepted packet requires an accepted or superseded change dossier")
        if not isinstance(knowledge, dict) or knowledge.get("disposition") in {None, "pending"}:
            errors.append("accepted packet requires a final project-knowledge disposition")
    return errors


def bind_knowledge(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if not has_quality_kernel_contract(metadata.get("skill_version")):
        return emit({"status": "invalid", "errors": ["bind-knowledge requires quality-kernel-v1"]}, 2)
    if metadata.get("state") not in {"awaiting-approval", "approved", "implementing", "verifying"}:
        return emit({"status": "invalid", "errors": ["knowledge may be bound only before acceptance"]}, 2)
    if not args.rationale.strip():
        return emit({"status": "invalid", "errors": ["knowledge rationale must be non-empty"]}, 2)
    if args.impact == "none":
        if args.manifest is not None or args.root is not None:
            return emit({"status": "invalid", "errors": ["impact none must not bind a repository manifest"]}, 2)
        binding: dict[str, Any] = {
            "schema_version": "1.0",
            "impact": "none",
            "rationale": args.rationale.strip(),
            "repository_root": None,
            "project_root": None,
            "changes_root": None,
            "convention_path": None,
            "manifest": None,
            "sha256": None,
        }
    else:
        roots = metadata.get("repository_roots", [])
        root = args.root.resolve() if args.root is not None else Path(roots[0]).resolve() if len(roots) == 1 else None
        if root is None or str(root) not in roots or args.manifest is None:
            return emit(
                {"status": "invalid", "errors": ["material knowledge impact requires --root and --manifest in a declared repository"]},
                2,
            )
        try:
            manifest_path = contained_path(
                root,
                args.manifest,
                label="knowledge manifest",
                require_relative=True,
                reject_symlinks=True,
            )
        except PathContractError as exc:
            return emit({"status": "invalid", "errors": [str(exc)]}, 2)
        if not manifest_path.is_file():
            return emit({"status": "invalid", "errors": ["knowledge manifest does not exist"]}, 2)
        report = knowledge_system.validate_knowledge_system(
            root,
            project_root=args.project_root,
            changes_root=args.changes_root,
            convention_path=args.convention_path,
            change_id=str(metadata.get("change_id")),
        )
        if report.get("status") != "valid":
            return emit({"status": "invalid", "errors": report.get("errors", [])}, 2)
        resolved_roots = report.get("roots")
        if not isinstance(resolved_roots, dict):
            return emit({"status": "invalid", "errors": ["knowledge validator did not resolve roots"]}, 2)
        project_root = resolved_roots.get("project")
        changes_root = resolved_roots.get("changes")
        if not isinstance(project_root, str) or not isinstance(changes_root, str):
            return emit({"status": "invalid", "errors": ["knowledge validator returned invalid roots"]}, 2)
        expected_manifest = (root / changes_root / str(metadata.get("change_id")) / "manifest.json").resolve()
        if manifest_path.resolve() != expected_manifest:
            return emit({"status": "invalid", "errors": ["knowledge manifest is not the resolved change dossier"]}, 2)
        binding = {
            "schema_version": "1.0",
            "impact": args.impact,
            "rationale": args.rationale.strip(),
            "repository_root": str(root),
            "project_root": project_root,
            "changes_root": changes_root,
            "convention_path": args.convention_path,
            "manifest": manifest_path.relative_to(root).as_posix(),
            "sha256": "sha256:" + hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        }
    candidate = dict(metadata)
    candidate["knowledge_manifest"] = binding
    binding_errors = knowledge_binding_errors(packet, candidate, effective_state=str(metadata.get("state")))
    if binding_errors:
        return emit({"status": "invalid", "errors": binding_errors}, 2)
    now = utc_now()
    metadata["knowledge_manifest"] = binding
    metadata["updated_at"] = now
    write_packet(packet, metadata, "knowledge-bound", binding)
    return emit({"status": "bound", "packet": str(packet), "knowledge_manifest": binding})


def validate_knowledge_command(args: argparse.Namespace) -> int:
    report = knowledge_system.validate_knowledge_system(
        args.root.resolve(),
        project_root=args.project_root,
        changes_root=args.changes_root,
        convention_path=args.convention_path,
        change_id=args.change_id,
    )
    return emit(report, 0 if report.get("status") == "valid" else 2)


def technique_accountability_errors(text: str) -> list[str]:
    body = heading_body(text, "Technique accountability")
    if body is None:
        return ["test-matrix.md: missing heading `Technique accountability`"]
    errors: list[str] = []
    rows: dict[str, list[str]] = {}
    for line in body.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] in {"Black-box", "White-box", "Experience-based / exploratory / adversarial"}:
            rows[cells[0]] = cells
    for perspective in ("Black-box", "White-box"):
        cells = rows.get(perspective)
        if cells is None or len(cells) != 4:
            errors.append(f"test-matrix.md: {perspective} requires one four-column accountability row")
            continue
        derivation, applicability, mapped = cells[1:]
        if not derivation or PLACEHOLDER_RE.search(derivation):
            errors.append(f"test-matrix.md: {perspective} requires concrete derived obligations")
        is_not_applicable = re.search(r"\bN/?A\b|not applicable", applicability, re.IGNORECASE) is not None
        if not applicability or PLACEHOLDER_RE.search(applicability):
            errors.append(f"test-matrix.md: {perspective} requires applicability or a concrete N/A reason")
        elif is_not_applicable:
            reason = re.sub(r"(?i)\bN/?A\b|not applicable|because|[:;-]", " ", applicability).strip()
            if len(reason.split()) < 3:
                errors.append(f"test-matrix.md: {perspective} N/A requires a concrete change-specific reason")
            if TEST_MATRIX_CELL_RE.search(mapped):
                errors.append(f"test-matrix.md: {perspective} N/A must not map executable cells")
        elif not TEST_MATRIX_CELL_RE.search(mapped):
            errors.append(f"test-matrix.md: applicable {perspective} requires at least one mapped TM cell")
    oracle_body = heading_body(text, "Oracle validity review")
    if oracle_body is None:
        errors.append("test-matrix.md: missing heading `Oracle validity review`")
    elif "evidence gap" in oracle_body.lower() and "closed" not in oracle_body.lower():
        errors.append("test-matrix.md: unresolved test-oracle evidence gap blocks verification")
    elif TEST_MATRIX_CELL_RE.search(oracle_body) is None and "no changed test" not in oracle_body.lower():
        errors.append("test-matrix.md: Oracle validity review requires a mapped TM cell or concrete no-changed-test rationale")
    return errors


def trace_technique_accountability_errors(text: str) -> list[str]:
    body = heading_body(text, "Test technique accountability")
    fields, field_errors = labeled_fields(body, ("Black-box", "White-box", "Oracle"))
    errors = [f"trace.md: Test technique accountability {error}" for error in field_errors]
    if field_errors:
        return errors
    for perspective in ("Black-box", "White-box"):
        value = fields[perspective]
        not_applicable = re.search(r"\bN/?A\b|not applicable", value, re.IGNORECASE) is not None
        if not_applicable:
            reason = re.sub(r"(?i)\bN/?A\b|not applicable|because|[:;,.-]", " ", value).strip()
            if len(reason.split()) < 3:
                errors.append(f"trace.md: {perspective} N/A requires a concrete change-specific reason")
        elif re.fullmatch(r"(?i)(?:none|no|unknown|pending|not run|not reviewed)", value.strip()):
            errors.append(f"trace.md: {perspective} requires concrete applicable obligations and evidence")
    oracle = fields["Oracle"]
    if re.search(r"(?i)\b(?:not reviewed|not run|pending|unknown|missing|open)\b", oracle) or len(oracle.split()) < 4:
        errors.append("trace.md: Oracle requires a concrete failure-sensitivity review")
    return errors


def trace_commit_ready_errors(text: str) -> list[str]:
    body = heading_body(text, "Knowledge and commit readiness")
    fields, field_errors = labeled_fields(
        body,
        ("Knowledge impact", "Slice", "Commit-ready", "Delivery authority"),
    )
    errors = [f"trace.md: Knowledge and commit readiness {error}" for error in field_errors]
    if field_errors:
        return errors
    impact = fields["Knowledge impact"].strip().lower()
    if not any(impact.startswith(value) for value in ("none", "add", "update", "deprecate")):
        errors.append("trace.md: Knowledge impact must record none, add, update, or deprecate")
    if re.match(r"(?i)^yes\b", fields["Commit-ready"].strip()) is None:
        errors.append("trace.md: Commit-ready must be yes before verification")
    delivery = fields["Delivery authority"].lower()
    if not all(word in delivery for word in ("stage", "commit", "push")) or not any(
        marker in delivery
        for marker in ("not authorized", "separate authority", "separately authorized", "independent", "no stage")
    ):
        errors.append("trace.md: commit-ready must preserve separate stage, commit, and push authority")
    return errors


def commit_ready_errors(text: str) -> list[str]:
    body = heading_body(text, "Slice and commit readiness")
    fields, errors = labeled_fields(body, COMMIT_READY_FIELDS)
    rendered = [f"execution.md: Slice and commit readiness {error}" for error in errors]
    if errors:
        return rendered
    if fields.get("Status", "").strip().lower() != "commit-ready":
        rendered.append("execution.md: Slice and commit readiness Status must be commit-ready before verification")
    delivery = fields.get("Delivery authority", "").lower()
    if not all(word in delivery for word in ("stage", "commit", "push")) or not any(
        marker in delivery
        for marker in ("not authorized", "separate authority", "separately authorized", "independent", "no stage")
    ):
        rendered.append("execution.md: commit-ready must preserve separate stage, commit, and push authority")
    return rendered


def change_set_errors(filename: str, body: str | None) -> list[str]:
    """Validate the lightweight root handoff before verification starts."""
    if body is None:
        return [f"{filename}: missing heading `Change set`"]
    errors: list[str] = []
    if "change-set.v1" not in body:
        errors.append(f"{filename}: `Change set` must identify change-set.v1")
    for field in CHANGE_SET_FIELDS:
        if re.search(
            rf"(?im)^\s*(?:[-*]\s*)?{re.escape(field)}\s*:\s*\S",
            body,
        ) is None:
            errors.append(f"{filename}: `Change set` requires a non-empty `{field}` field")
    return errors


def packet_change_set_errors(packet: Path, metadata: dict[str, Any]) -> list[str]:
    """Validate the existing-ledger handoff only when a new verification transition occurs."""
    _, errors = packet_change_set_record(packet, metadata)
    return errors


def packet_change_set_record(
    packet: Path,
    metadata: dict[str, Any],
) -> tuple[dict[str, str] | None, list[str]]:
    """Return the canonical existing-ledger binding for change-set.v1."""
    family = documentation_family(metadata.get("documentation_profile"))
    filename = "trace.md" if family == "trace" else "execution.md" if family == "governed" else None
    if filename is None:
        return None, ["packet.json: invalid documentation profile for change-set.v1"]
    path = packet / filename
    if not path.is_file():
        return None, [f"missing required file: {filename}"]
    body = heading_body(path.read_text(encoding="utf-8"), "Change set")
    error = placeholder_error(filename, "Change set", body)
    errors = [error] if error else change_set_errors(filename, body)
    if errors or body is None:
        return None, errors
    return {
        "schema_version": "1.0",
        "artifact": "change-set.v1",
        "ledger": filename,
        "sha256": "sha256:" + hashlib.sha256(body.encode("utf-8")).hexdigest(),
    }, []


def validate_change_set_binding(packet: Path, metadata: dict[str, Any]) -> list[str]:
    """Bind tagged-at-creation packets while preserving the complete legacy contract."""
    ledger = packet / "events.jsonl"
    if not ledger.is_file():
        return []
    try:
        events = [
            json.loads(line)
            for line in ledger.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError):
        return []
    if not events or not isinstance(events[0], dict):
        return []
    verifying_events = [
        event
        for event in events
        if isinstance(event, dict)
        and event.get("event") == "transition"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("to") == "verifying"
    ]
    tagged_creation = (
        isinstance(events[0].get("payload"), dict)
        and has_change_set_contract(events[0]["payload"].get("skill_version"))
    )
    if not tagged_creation:
        return []
    for event in verifying_events:
        marker = event["payload"].get("change_set")
        if not isinstance(marker, dict) or set(marker) != {
            "schema_version",
            "artifact",
            "ledger",
            "sha256",
        }:
            return ["events.jsonl: new verifying transition requires an exact change-set binding"]
        if (
            marker.get("schema_version") != "1.0"
            or marker.get("artifact") != "change-set.v1"
            or marker.get("ledger") not in {"trace.md", "execution.md"}
            or not isinstance(marker.get("sha256"), str)
            or re.fullmatch(r"sha256:[0-9a-f]{64}", marker["sha256"]) is None
        ):
            return ["events.jsonl: verifying transition has an invalid change-set binding"]

    state = metadata.get("state")
    if state not in {"verifying", "accepted", "archived"}:
        return []
    if not verifying_events:
        return ["events.jsonl: new verifying packet is missing its change-set transition binding"]
    expected, errors = packet_change_set_record(packet, metadata)
    if errors:
        return errors
    observed = verifying_events[-1]["payload"]["change_set"]
    if observed != expected:
        return ["events.jsonl: change-set.v1 drifted after the verifying transition"]
    return []


def validate_continuity_binding(packet: Path, metadata: dict[str, Any]) -> list[str]:
    """Freeze the recovery checkpoint at every new-contract verifying transition."""
    if not has_quality_kernel_contract(metadata.get("skill_version")):
        return []
    ledger = packet / "events.jsonl"
    if not ledger.is_file():
        return ["events.jsonl: quality-kernel-v1 requires an event ledger"]
    try:
        events = [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, json.JSONDecodeError):
        return ["events.jsonl: cannot validate continuity checkpoint binding"]
    if not events or not isinstance(events[0], dict):
        return ["events.jsonl: quality-kernel-v1 requires tagged creation evidence"]
    creation_payload = events[0].get("payload")
    if not isinstance(creation_payload, dict) or not has_quality_kernel_contract(
        creation_payload.get("skill_version")
    ):
        return ["events.jsonl: quality-kernel-v1 is missing tagged creation evidence"]
    verifying_events = [
        event
        for event in events
        if isinstance(event, dict)
        and event.get("event") == "transition"
        and isinstance(event.get("payload"), dict)
        and event["payload"].get("to") == "verifying"
    ]
    for event in verifying_events:
        marker = event["payload"].get("continuity_checkpoint")
        if not isinstance(marker, dict) or set(marker) != {
            "schema_version",
            "trigger",
            "requirement_revision",
            "requirements_digest",
            "design_digest",
            "engineering_context_fingerprint",
            "repository_snapshot",
            "repository_reconciliation",
            "active_ids",
            "active_objective",
            "last_evidence",
            "next_action",
            "stop_condition",
            "drift",
            "ledger",
            "section_sha256",
            "at",
        }:
            return ["events.jsonl: quality-kernel verifying transition requires an exact continuity binding"]
    if metadata.get("state") not in {"verifying", "accepted", "archived"}:
        return []
    if not verifying_events:
        return ["events.jsonl: quality-kernel packet is missing its continuity transition binding"]
    if verifying_events[-1]["payload"].get("continuity_checkpoint") != metadata.get("continuity_checkpoint"):
        return ["events.jsonl: continuity checkpoint drifted after the verifying transition"]
    return []


def ids(text: str, kind: str) -> set[str]:
    return set(ID_PATTERNS[kind].findall(text))


def audit_finding_errors(text: str, prefix: str) -> list[str]:
    """Require every declared audit finding to be canonical and closed."""
    errors: list[str] = []
    seen: set[str] = set()
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not cells or not cells[0].strip("*_`").upper().startswith(f"{prefix}-"):
            continue
        finding_id = cells[0].strip("*_`").split(":", 1)[0].strip()
        if len(cells) < 5:
            errors.append(f"malformed finding row for {finding_id or prefix}")
            continue
        if not re.fullmatch(rf"{re.escape(prefix)}-\d+", finding_id):
            errors.append(f"invalid finding id {finding_id!r}; expected {prefix}-n")
            continue
        if finding_id in seen:
            errors.append(f"duplicate finding id {finding_id}")
            continue
        seen.add(finding_id)
        status = cells[-1].strip("*_`").lower()
        if status != "closed":
            errors.append(f"{finding_id} status must be closed, got {status!r}")
    return errors


def applicable_waiver(
    approvals: Any,
    *,
    blockers: Iterable[str],
    scopes: Iterable[str],
    now: dt.datetime | None = None,
) -> dict[str, Any] | None:
    """Return a current waiver that explicitly covers every blocker and one affected scope."""
    if not isinstance(approvals, dict):
        return None
    records = approvals.get("waivers", [])
    if not isinstance(records, list):
        return None
    required_blockers = set(blockers)
    affected_scopes = set(scopes)
    current_time = now or dt.datetime.now(dt.timezone.utc)
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        patterns = record.get("scope")
        covered = record.get("blockers")
        if not isinstance(patterns, list) or not patterns or not all(isinstance(item, str) and item for item in patterns):
            continue
        if not isinstance(covered, list) or not required_blockers or not all(
            blocker in covered or "*" in covered for blocker in required_blockers
        ):
            continue
        if not affected_scopes or not any(
            pattern == "*" or fnmatch.fnmatchcase(scope, pattern)
            for pattern in patterns
            for scope in affected_scopes
        ):
            continue
        if not all(
            isinstance(record.get(field), str) and record[field].strip()
            for field in ("by", "note", "residual_risk", "recheck_trigger")
        ):
            continue
        expiry = parsed_timestamp(record.get("expires_at"))
        if expiry is None or expiry <= current_time:
            continue
        return record
    return None


def accepted_evidence_errors(
    family: str,
    texts: dict[str, str],
    approvals: dict[str, Any],
) -> list[str]:
    """Validate terminal verification and review evidence without packet-shape concerns."""
    errors: list[str] = []
    if family == "trace":
        verification_body = heading_body(texts.get("trace.md", ""), "Verification") or ""
        statuses = set(re.findall(r"\b(?:PASSED|FAILED|FLAKY|BLOCKED|NOT RUN|WAIVED)\b", verification_body))
        invalid_statuses = statuses & {"FAILED", "FLAKY", "BLOCKED", "NOT RUN"}
        if invalid_statuses:
            errors.append(f"accepted trace retains unresolved verification statuses: {sorted(invalid_statuses)}")
        trace_waiver = applicable_waiver(
            approvals,
            blockers=["trace-verification"],
            scopes=["trace.md", "Verification"],
        )
        if "PASSED" not in statuses and not ("WAIVED" in statuses and trace_waiver):
            errors.append("accepted trace requires PASSED evidence or an approved WAIVED verification")
        return errors

    matrix_rows: list[tuple[str, str, int, str, bool]] = []
    seen_cells: set[str] = set()
    for line in texts.get("test-matrix.md", "").splitlines():
        if not re.match(r"^\|\s*TM-", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            errors.append(f"test-matrix.md: malformed matrix row `{line}`")
            continue
        cell = cells[0]
        if not TEST_MATRIX_CELL_RE.fullmatch(cell):
            errors.append(f"test-matrix.md: invalid cell id {cell!r}")
            continue
        if cell in seen_cells:
            errors.append(f"test-matrix.md: duplicate cell id {cell}")
            continue
        seen_cells.add(cell)
        if not cells[1]:
            errors.append(f"test-matrix.md: {cell} requires a non-empty obligation")
            continue
        required_word = cells[4].lower()
        if required_word not in TEST_MATRIX_REQUIRED_WORDS:
            errors.append(f"test-matrix.md: invalid Required value {cells[4]!r} for {cell}; expected yes or no")
            continue
        try:
            attempts = int(cells[5])
        except ValueError:
            errors.append(f"test-matrix.md: invalid attempts for {cell}")
            continue
        status_value = cells[6]
        if status_value not in STATUS_WORDS:
            errors.append(f"test-matrix.md: invalid status {status_value!r} for {cell}")
            continue
        matrix_rows.append((cell, cells[1], attempts, status_value, required_word == "yes"))
    if not matrix_rows:
        errors.append("accepted packet requires at least one parsed test-matrix cell")
    for cell, obligation, attempts, status_value, required in matrix_rows:
        if status_value == "PASSED" and attempts < 1:
            errors.append(f"{cell}: PASSED requires at least one attempt")
        if required and status_value not in {"PASSED", "WAIVED"}:
            errors.append(f"{cell}: required cell is {status_value}")
        if status_value == "WAIVED" and not applicable_waiver(
            approvals,
            blockers=[cell],
            scopes=[cell, obligation],
        ):
            errors.append(f"{cell}: WAIVED requires an applicable waiver approval record")
    for audit, prefix in (("blue-audit.md", "BLUE"), ("red-audit.md", "RED")):
        for error in audit_finding_errors(texts.get(audit, ""), prefix):
            errors.append(f"{audit}: {error}")
    return errors


def validate_packet_data(packet: Path, *, state_override: str | None = None) -> tuple[dict[str, Any], int]:
    errors: list[str] = []
    warnings: list[str] = []
    metadata, metadata_errors = load_packet(packet)
    errors.extend(metadata_errors)
    if not metadata:
        return {"status": "invalid", "packet": str(packet), "errors": errors, "warnings": warnings}, 2
    for field in (
        "schema_version",
        "skill_version",
        "change_id",
        "state",
        "documentation_profile",
        "task_type",
        "created_at",
        "updated_at",
        "repository_roots",
        "base_git_state",
        "authority",
        "approvals",
        "history",
    ):
        value = metadata.get(field)
        if value in (None, "", [], {}):
            errors.append(f"packet.json: missing concrete `{field}`")
    schema_version = metadata.get("schema_version")
    effective_state = state_override or metadata.get("state")
    if not metadata_errors:
        errors.extend(
            method_selection_binding_errors(
                packet,
                metadata,
                effective_state=str(effective_state),
            )
        )
    quality_tagged = packet_has_creation_capability(
        packet,
        metadata,
        QUALITY_KERNEL_SKILL_VERSION_TAG,
    )
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"packet.json: unsupported schema_version {metadata.get('schema_version')!r}")
    if metadata.get("state") not in STATES:
        errors.append(f"packet.json: invalid state {metadata.get('state')!r}")
    if metadata.get("task_type") not in TASK_TYPES:
        errors.append(f"packet.json: invalid task_type {metadata.get('task_type')!r}")
    if metadata.get("task_type") == "read-only-audit" and metadata.get("mutation_intent") != "none":
        errors.append("packet.json: read-only-audit cannot declare persistent mutation")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", str(metadata.get("change_id", ""))):
        errors.append("packet.json: invalid change_id")
    if schema_version in READINESS_SCHEMA_VERSIONS:
        collaboration_profile = metadata.get("collaboration_profile")
        ui_impact = metadata.get("ui_impact")
        if collaboration_profile not in COLLABORATION_PROFILES:
            errors.append(f"packet.json: invalid collaboration_profile {collaboration_profile!r}")
        if ui_impact not in UI_IMPACTS:
            errors.append(f"packet.json: invalid ui_impact {ui_impact!r}")
    if quality_tagged:
        if metadata.get("mutation_intent") not in {"none", "persistent"}:
            errors.append("packet.json: quality-kernel-v1 requires mutation_intent none or persistent")
        for field in ("design_digest", "continuity_checkpoint", "knowledge_manifest"):
            if field not in metadata:
                errors.append(f"packet.json: quality-kernel-v1 requires `{field}` projection")

    profile = metadata.get("documentation_profile")
    family = documentation_family(profile)
    if schema_version == "2.0":
        work_mode = metadata.get("work_mode")
        if work_mode not in {"traced", "governed"}:
            errors.append(f"packet.json: schema 2.0 packet requires traced or governed work_mode, got {work_mode!r}")
        if (work_mode, profile) not in {("traced", "trace"), ("governed", "governed")}:
            errors.append("packet.json: work_mode and documentation_profile do not match")
    elif profile in {"trace", "governed"}:
        errors.append(f"packet.json: documentation_profile {profile!r} requires schema 2.0")
    texts: dict[str, str] = {}
    if family == "trace":
        path = packet / "trace.md"
        if not path.is_file():
            errors.append("missing required file: trace.md")
        else:
            text = path.read_text(encoding="utf-8")
            texts[path.name] = text
            for heading in MICRO_HEADINGS:
                error = placeholder_error(path.name, heading, heading_body(text, heading))
                if error:
                    errors.append(error)
            if quality_tagged:
                for heading in QUALITY_TRACE_HEADINGS:
                    body = heading_body(text, heading)
                    if heading == "Continuity checkpoint" and effective_state not in {
                        "implementing",
                        "verifying",
                        "accepted",
                        "archived",
                    }:
                        if body is None:
                            errors.append("trace.md: missing heading `Continuity checkpoint`")
                        continue
                    error = placeholder_error(path.name, heading, body)
                    if error:
                        errors.append(error)
    elif family == "governed":
        for filename in FULL_FILES:
            path = packet / filename
            if not path.is_file():
                errors.append(f"missing required file: {filename}")
                continue
            text = path.read_text(encoding="utf-8")
            texts[filename] = text
            for heading in FULL_HEADINGS[filename]:
                error = placeholder_error(filename, heading, heading_body(text, heading))
                if error:
                    errors.append(error)
            if schema_version in READINESS_SCHEMA_VERSIONS:
                for heading in SCHEMA_1_1_HEADINGS.get(filename, ()):
                    error = placeholder_error(filename, heading, heading_body(text, heading))
                    if error:
                        errors.append(error)
            if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
                for heading in SCHEMA_1_2_HEADINGS.get(filename, ()):
                    error = placeholder_error(filename, heading, heading_body(text, heading))
                    if error:
                        errors.append(error)
            if quality_tagged:
                for heading in QUALITY_GOVERNED_HEADINGS.get(filename, ()):
                    body = heading_body(text, heading)
                    if heading == "Continuity checkpoint" and effective_state not in {
                        "implementing",
                        "verifying",
                        "accepted",
                        "archived",
                    }:
                        if body is None:
                            errors.append(f"{filename}: missing heading `Continuity checkpoint`")
                        continue
                    error = placeholder_error(filename, heading, body)
                    if error:
                        errors.append(error)
    else:
        errors.append(f"packet.json: invalid documentation_profile {profile!r}")

    all_text = "\n".join(texts.values())
    if schema_version in READINESS_SCHEMA_VERSIONS:
        if family == "governed":
            context_instructions = ids(texts.get("context.md", ""), "instruction")
            if not context_instructions:
                errors.append(f"context.md: schema {schema_version} requires at least one INS-n instruction record")
            for filename in (
                "design.md",
                "execution.md",
                "test-matrix.md",
                "blue-audit.md",
                "red-audit.md",
                "evidence.md",
            ):
                downstream_instructions = ids(texts.get(filename, ""), "instruction")
                if context_instructions != downstream_instructions:
                    errors.append(
                        f"schema {schema_version} instruction IDs must match between context.md and {filename}; "
                        f"context={sorted(context_instructions)}, downstream={sorted(downstream_instructions)}"
                    )
        elif family == "trace" and not ids(all_text, "instruction"):
            errors.append(f"trace.md: schema {schema_version} requires at least one INS-n instruction record")
    required_dirs = (
        ("briefs", "reports", "artifacts")
        if schema_version != "2.0" or family == "governed"
        else ("artifacts",)
    )
    for dirname in required_dirs:
        if not (packet / dirname).is_dir():
            errors.append(f"missing required directory: {dirname}/")

    def declared_set(field: str) -> set[str]:
        value = metadata.get(field, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"packet.json: {field} must be a list of strings")
            return set()
        return set(value)

    declared = {
        "acceptance": declared_set("acceptance_ids"),
        "scope": declared_set("scope_ids"),
        "verification": declared_set("verification_ids"),
    }
    observed = {kind: ids(all_text, kind) for kind in declared}
    for kind in declared:
        if declared[kind] != observed[kind]:
            errors.append(
                f"packet.json {kind}_ids must equal documented IDs; "
                f"declared={sorted(declared[kind])}, documented={sorted(observed[kind])}"
            )

    if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
        ambiguity_ids = metadata.get("ambiguity_ids", [])
        declared_ambiguities = set(value for value in ambiguity_ids if isinstance(value, str)) if isinstance(ambiguity_ids, list) else set()
        observed_ambiguities = ids(all_text, "ambiguity")
        if declared_ambiguities != observed_ambiguities:
            errors.append(
                "packet.json ambiguity_ids must equal documented IDs; "
                f"declared={sorted(declared_ambiguities)}, documented={sorted(observed_ambiguities)}"
            )
        ledger_ambiguities = (
            ids(texts.get("requirements.md", ""), "ambiguity")
            if family == "governed"
            else ids(texts.get("trace.md", ""), "ambiguity")
        )
        if declared_ambiguities != ledger_ambiguities:
            errors.append(
                "packet.json ambiguity_ids must equal requirement-ledger IDs; "
                f"declared={sorted(declared_ambiguities)}, ledger={sorted(ledger_ambiguities)}"
            )
        errors.extend(
            semantic_metadata_errors(
                metadata,
                declared_trace_ids=set().union(*declared.values()),
                require_ready=(state_override or metadata.get("state"))
                in {"approved", "implementing", "verifying", "accepted", "archived"},
            )
        )

    if family == "governed":
        requirements = texts.get("requirements.md", "")
        design = texts.get("design.md", "")
        execution = texts.get("execution.md", "")
        evidence = texts.get("evidence.md", "")
        matrix = texts.get("test-matrix.md", "")
        for acceptance in ids(requirements, "acceptance"):
            if acceptance not in execution:
                errors.append(f"{acceptance} is missing from execution.md")
            if acceptance not in evidence:
                errors.append(f"{acceptance} is missing from evidence.md")
        for scope in ids(design, "scope"):
            if scope not in execution:
                errors.append(f"{scope} is missing from execution.md")
            if scope not in evidence:
                errors.append(f"{scope} is missing from evidence.md")
        for obligation in ids(design, "verification"):
            if obligation not in matrix:
                errors.append(f"{obligation} is missing from test-matrix.md")
            if obligation not in evidence:
                errors.append(f"{obligation} is missing from evidence.md")
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
            for ambiguity_id in declared_ambiguities:
                if ambiguity_id not in execution:
                    errors.append(f"{ambiguity_id} is missing from execution.md")
                if ambiguity_id not in evidence:
                    errors.append(f"{ambiguity_id} is missing from evidence.md")
    errors.extend(continuity_checkpoint_errors(packet, metadata, effective_state=str(effective_state)))
    errors.extend(knowledge_binding_errors(packet, metadata, effective_state=str(effective_state)))
    if quality_tagged and effective_state in {"verifying", "accepted", "archived"}:
        if family == "governed":
            errors.extend(technique_accountability_errors(texts.get("test-matrix.md", "")))
            errors.extend(commit_ready_errors(texts.get("execution.md", "")))
        elif family == "trace":
            trace = texts.get("trace.md", "")
            errors.extend(trace_technique_accountability_errors(trace))
            errors.extend(trace_commit_ready_errors(trace))

    approvals_value = metadata.get("approvals", {})
    if not isinstance(approvals_value, dict):
        errors.append("packet.json: `approvals` must be an object")
        approvals: dict[str, Any] = {}
    else:
        approvals = approvals_value
    if schema_version in READINESS_SCHEMA_VERSIONS:
        for kind, expected_id in READINESS_APPROVAL_IDS.items():
            records = approvals.get(kind, [])
            if not isinstance(records, list):
                errors.append(f"packet.json: `approvals.{kind}` must be a list")
                continue
            for record in records:
                if not isinstance(record, dict):
                    errors.append(f"packet.json: `approvals.{kind}` records must be objects")
                    continue
                if record.get("id") != expected_id:
                    errors.append(f"packet.json: `approvals.{kind}` record id must be {expected_id}")
                for field in ("by", "at", "note"):
                    if not isinstance(record.get(field), str) or not record[field].strip():
                        errors.append(f"packet.json: `approvals.{kind}` record requires non-empty {field}")
                if parsed_timestamp(record.get("at")) is None:
                    errors.append(f"packet.json: `approvals.{kind}` record requires a timezone-aware timestamp")
                if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS and kind == "requirements":
                    revision = record.get("requirement_revision")
                    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
                        errors.append("packet.json: Requirement Ready record requires a positive requirement_revision")
                    if not isinstance(record.get("requirements_digest"), str) or not re.fullmatch(
                        r"sha256:[0-9a-f]{64}", record["requirements_digest"]
                    ):
                        errors.append("packet.json: Requirement Ready record requires a sha256 requirements_digest")
    dependency_values = metadata.get("dependency_changes", [])
    if not isinstance(dependency_values, list) or any(not isinstance(value, str) for value in dependency_values):
        errors.append("packet.json: dependency_changes must be a list of strings")
        dependency_ids: set[str] = set()
    else:
        dependency_ids = set(dependency_values)
    dependency_approvals = approvals.get("dependencies", [])
    if not isinstance(dependency_approvals, list):
        errors.append("packet.json: `approvals.dependencies` must be a list")
        dependency_approvals = []
    approved_dependency_ids = {
        item["id"]
        for item in dependency_approvals
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if dependency_ids - approved_dependency_ids:
        errors.append(f"unapproved dependency changes: {sorted(dependency_ids - approved_dependency_ids)}")
    if schema_version == "2.0":
        for index, record in enumerate(dependency_approvals):
            for error in validate_dependency_approval(record):
                errors.append(f"packet.json: approvals.dependencies[{index}]: {error}")

    state = effective_state
    if state in {"approved", "implementing", "verifying", "accepted", "archived"}:
        if schema_version in READINESS_SCHEMA_VERSIONS and concrete_design_record(approvals) is None:
            errors.append(f"state {state} requires a concrete design approval record")
        elif schema_version not in READINESS_SCHEMA_VERSIONS and not approvals.get("design"):
            errors.append(f"state {state} requires a design approval record")
    if schema_version in READINESS_SCHEMA_VERSIONS and state in {"approved", "implementing", "verifying", "accepted", "archived"}:
        requirement_records = concrete_readiness_records(approvals, "requirements")
        ux_records = concrete_readiness_records(approvals, "ux")
        if metadata.get("collaboration_profile") != "execute" and not requirement_records:
            errors.append(f"state {state} requires Requirement Ready approval for checkpointed or co-design work")
        if metadata.get("ui_impact") == "material" and not ux_records:
            errors.append(f"state {state} requires UX Ready approval for material UI work")
        approved_times = history_times(metadata, "approved")
        awaiting_times = history_times(metadata, "awaiting-approval")
        if not approved_times:
            errors.append(f"state {state} requires an approved transition in history")
        elif not awaiting_times:
            errors.append(f"state {state} requires an awaiting-approval transition in history")
        else:
            approved_at = max(approved_times)
            eligible_awaiting = [value for value in awaiting_times if value <= approved_at]
            if not eligible_awaiting:
                errors.append("approved transition requires an earlier awaiting-approval transition")
                awaiting_at = None
            else:
                awaiting_at = max(eligible_awaiting)
            required_records = []
            if metadata.get("collaboration_profile") != "execute":
                required_records.append(("Requirement Ready", requirement_records))
            if metadata.get("ui_impact") == "material":
                required_records.append(("UX Ready", ux_records))
            for kind, records in required_records:
                valid_times = [parsed_timestamp(record.get("at")) for record in records]
                valid_times = [value for value in valid_times if value is not None]
                if not valid_times:
                    continue
                if awaiting_at is not None and not any(awaiting_at <= value <= approved_at for value in valid_times):
                    errors.append(f"{kind} approval must follow awaiting approval and predate the approved transition")
                if any(value > approved_at for value in valid_times):
                    errors.append(f"{kind} approval cannot be recorded after the approved transition")
        if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS:
            current_digest = current_requirements_digest(packet, profile)
            revision = metadata.get("requirement_revision")
            if current_digest is None:
                errors.append("content-bound packet requires a computable requirement baseline")
            elif metadata.get("requirements_digest") != current_digest:
                errors.append("requirements changed after Requirement Ready or design approval")
            design_record = concrete_design_record(approvals)
            if design_record is not None and (
                design_record.get("requirement_revision") != revision
                or design_record.get("requirements_digest") != current_digest
            ):
                errors.append("design approval does not match the current requirement revision and digest")
            if quality_tagged:
                design_digest = current_design_digest(packet, profile)
                if design_digest is None:
                    errors.append("quality-kernel-v1 requires a computable design baseline")
                elif metadata.get("design_digest") != design_digest:
                    errors.append("design changed after its content-bound approval")
                if design_record is not None and design_record.get("design_digest") != design_digest:
                    errors.append("design approval does not match the current design digest")
            if design_record is not None and approved_times and awaiting_times:
                approved_at = max(approved_times)
                eligible_awaiting = [value for value in awaiting_times if value <= approved_at]
                design_at = parsed_timestamp(design_record.get("at"))
                if eligible_awaiting and design_at is not None and not max(eligible_awaiting) <= design_at <= approved_at:
                    errors.append("design approval must follow awaiting approval and coincide with the approved transition")
            if metadata.get("collaboration_profile") != "execute" and approved_times and awaiting_times:
                approved_at = max(approved_times)
                eligible_awaiting = [value for value in awaiting_times if value <= approved_at]
                if eligible_awaiting:
                    awaiting_at = max(eligible_awaiting)
                    matching = [
                        record
                        for record in requirement_records
                        if record.get("requirement_revision") == revision
                        and record.get("requirements_digest") == current_digest
                        and (timestamp := parsed_timestamp(record.get("at"))) is not None
                        and awaiting_at <= timestamp <= approved_at
                    ]
                    if not matching:
                        errors.append("current requirement revision requires a fresh digest-bound Requirement Ready approval")
    if state in {"accepted", "archived"}:
        if not declared["acceptance"] or not declared["scope"] or not declared["verification"]:
            errors.append("accepted packet requires non-empty acceptance, scope, and verification ID sets")
        errors.extend(accepted_evidence_errors(family, texts, approvals))

    preference_artifact = packet / "effective-preferences.json"
    if preference_artifact.is_file():
        try:
            preferences = read_json(preference_artifact)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"effective-preferences.json: cannot load: {exc}")
        else:
            if preferences.get("schema_version") != "1.0":
                errors.append("effective-preferences.json: unsupported schema_version")
            fingerprint = preferences.get("fingerprint")
            if not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
                errors.append("effective-preferences.json: invalid fingerprint")
            if preferences.get("outcome") not in {"resolved", "blocked"}:
                errors.append("effective-preferences.json: invalid outcome")
            if state in {"accepted", "archived"} and preferences.get("outcome") == "blocked":
                errors.append("accepted packet cannot retain blocked effective preferences")

    readiness_artifact = packet / "context-readiness.json"
    if readiness_artifact.is_file():
        try:
            readiness = read_json(readiness_artifact)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"context-readiness.json: cannot load: {exc}")
        else:
            if readiness.get("schema_version") != "1.0":
                errors.append("context-readiness.json: unsupported schema_version")
            if readiness.get("tier") not in {"T0", "T1", "T2", "T3"}:
                errors.append("context-readiness.json: invalid tier")
            if readiness.get("outcome") not in {"not_applicable", "ready", "partial_advisory", "checkpoint", "blocked", "waived"}:
                errors.append("context-readiness.json: invalid outcome")
            if readiness.get("outcome") == "waived" and not isinstance(readiness.get("waiver"), dict):
                errors.append("context-readiness.json: waived outcome requires the applied waiver record")
            fingerprint = readiness.get("fingerprint")
            if not isinstance(fingerprint, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", fingerprint):
                errors.append("context-readiness.json: invalid fingerprint")
            if quality_tagged:
                _, projection_errors = validate_engineering_context_projection(readiness)
                errors.extend(projection_errors)
            if state in {"accepted", "archived"} and readiness.get("outcome") in {"checkpoint", "blocked"}:
                errors.append("accepted packet cannot retain a context-readiness checkpoint or block")

    report = {
        "status": "valid" if not errors else "invalid",
        "packet": str(packet),
        "change_id": metadata.get("change_id"),
        "state": state,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
    }
    return report, 0 if not errors else 2


def validate_packet(args: argparse.Namespace) -> int:
    report, code = validate_packet_data(args.packet.resolve())
    return emit(report, code)


def added_diff(root: Path, base: str | None) -> tuple[list[str], dict[str, str], dict[str, str]]:
    if base:
        verified = run(["git", "rev-parse", "--verify", f"{base}^{{commit}}"], cwd=root)
        if verified.returncode != 0:
            raise RuntimeError(f"invalid Git base {base!r}: {verified.stderr.strip() or verified.stdout.strip()}")
    command = ["git", "diff", "--unified=0"]
    if base:
        command.append(base)
    result = run(command, cwd=root)
    staged = run(["git", "diff", "--cached", "--unified=0"], cwd=root)
    names_command = ["git", "diff", "--name-only"] + ([base] if base else [])
    names = run(names_command, cwd=root)
    staged_names = run(["git", "diff", "--cached", "--name-only"], cwd=root)
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root)
    failed = [
        (label, result)
        for label, result in (
            ("worktree diff", result),
            ("staged diff", staged),
            ("changed names", names),
            ("staged names", staged_names),
            ("untracked names", untracked),
        )
        if result.returncode != 0
    ]
    if failed:
        label, failure = failed[0]
        raise RuntimeError(f"cannot inspect Git {label}: {failure.stderr.strip() or failure.stdout.strip()}")
    untracked_files = untracked.stdout.splitlines()
    files = sorted(set(names.stdout.splitlines()) | set(staged_names.stdout.splitlines()) | set(untracked_files))
    diff = result.stdout + "\n" + staged.stdout
    added_by_file: dict[str, list[str]] = {}
    removed_by_file: dict[str, list[str]] = {}
    current_file: str | None = None
    old_file: str | None = None
    for line in diff.splitlines():
        if line.startswith("--- a/"):
            old_file = line[6:]
        elif line.startswith("---"):
            old_file = None
        elif line.startswith("+++ b/"):
            current_file = line[6:]
            added_by_file.setdefault(current_file, [])
        elif line.startswith("+++"):
            current_file = old_file
        elif current_file and line.startswith("+"):
            added_by_file[current_file].append(line[1:])
        elif current_file and line.startswith("-"):
            removed_by_file.setdefault(current_file, []).append(line[1:])
    for relative in untracked_files:
        path = root / relative
        if path.is_file() and path.stat().st_size <= 2_000_000:
            try:
                added_by_file.setdefault(relative, []).append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    return (
        files,
        {path: "\n".join(lines) for path, lines in added_by_file.items()},
        {path: "\n".join(lines) for path, lines in removed_by_file.items()},
    )


def audit_preferences(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    try:
        files, added_by_file, removed_by_file = added_diff(root, args.base)
    except RuntimeError as exc:
        return emit({"status": "blocked", "root": str(root), "changed_files": [], "findings": [{
            "severity": "gate",
            "rule": "POLICY-AUDIT-INPUT",
            "evidence": str(exc),
            "message": "Preference audit could not establish a trustworthy Git diff baseline.",
        }]}, 2)
    findings: list[dict[str, str]] = []
    packet_meta: dict[str, Any] = {}
    if args.packet:
        packet_meta, _ = load_packet(args.packet.resolve())
    approvals_value = packet_meta.get("approvals", {})
    dependency_records = approvals_value.get("dependencies", []) if isinstance(approvals_value, dict) else []
    if not isinstance(dependency_records, list):
        dependency_records = []
    registry_path = plugin_root() / "skills" / "architecture-decisions" / "references" / "neutral-policy-registry.json"
    registry = read_json(registry_path)
    for rule in registry.get("audit_rules", []):
        kind = rule.get("kind")
        evidence: str | None = None
        path_pattern = str(rule.get("path_pattern", ".*"))
        candidate_files = [path for path in files if re.search(path_pattern, path, re.IGNORECASE)]
        if kind == "added_regex":
            matches = [
                path
                for path in candidate_files
                if re.search(str(rule["pattern"]), added_by_file.get(path, ""), re.MULTILINE | re.IGNORECASE)
            ]
            evidence = ", ".join(matches) if matches else None
        elif kind == "filename_regex":
            matches = [path for path in files if re.search(str(rule["pattern"]), path, re.IGNORECASE)]
            evidence = ", ".join(matches) if matches else None
        elif kind == "dependency_approval":
            matches = [path for path in files if re.search(str(rule["pattern"]), path, re.IGNORECASE)]
            unbound = [
                path
                for path in matches
                if not any(approval_binds_file(record, path, root / path) for record in dependency_records)
            ]
            if unbound:
                evidence = ", ".join(unbound)
        elif kind == "exclusive_added_regex":
            families = rule.get("families", [])
            candidate_text = "\n".join(added_by_file.get(path, "") for path in candidate_files)
            if sum(1 for pattern in families if re.search(str(pattern), candidate_text, re.MULTILINE | re.IGNORECASE)) > 1:
                evidence = ", ".join(candidate_files)
        if evidence:
            findings.append(
                {
                    "severity": str(rule["severity"]),
                    "rule": str(rule["policy_id"]),
                    "evidence": evidence,
                    "message": str(rule["message"]),
                }
            )
    base_ref = args.base or "HEAD"
    has_base = run(["git", "rev-parse", "--verify", f"{base_ref}^{{commit}}"], cwd=root).returncode == 0
    if args.base and not has_base:
        return emit({"status": "blocked", "root": str(root), "changed_files": files, "findings": [{
            "severity": "gate", "rule": "POLICY-AUDIT-INPUT", "evidence": f"invalid Git base {base_ref!r}",
            "message": "Preference audit could not establish a trustworthy Git action baseline.",
        }]}, 2)
    unapproved_actions: list[str] = []
    invalid_actions: list[str] = []
    for path, added_text in added_by_file.items():
        if not re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path):
            continue
        added_refs, invalid_refs = action_reference_scan(added_text)
        removed_refs, invalid_removed_refs = action_reference_scan(removed_by_file.get(path, ""))
        existing_action_refs: set[tuple[str, str]] = set()
        if has_base:
            listing = run(["git", "ls-tree", "--name-only", base_ref, "--", path], cwd=root)
            if listing.returncode != 0:
                return emit({"status": "blocked", "root": str(root), "changed_files": files, "findings": [{
                    "severity": "gate", "rule": "POLICY-AUDIT-INPUT", "evidence": listing.stderr.strip(),
                    "message": "Preference audit could not resolve a workflow-specific Git baseline.",
                }]}, 2)
            if path in listing.stdout.splitlines():
                baseline = run(["git", "show", f"{base_ref}:{path}"], cwd=root)
                if baseline.returncode != 0:
                    return emit({"status": "blocked", "root": str(root), "changed_files": files, "findings": [{
                        "severity": "gate", "rule": "POLICY-AUDIT-INPUT", "evidence": baseline.stderr.strip(),
                        "message": "Preference audit could not read a workflow-specific Git baseline.",
                    }]}, 2)
                existing_action_refs = action_reference_scan(baseline.stdout)[0]
        invalid_actions.extend(f"{path}:{item}" for item in invalid_refs)
        invalid_actions.extend(f"{path}:{item}" for item in invalid_removed_refs)
        replaced_names = {name for name, _ in added_refs} & {name for name, _ in removed_refs}
        for name, ref in sorted(added_refs - existing_action_refs):
            operation = "update" if any(existing_name == name for existing_name, _ in existing_action_refs) else "add"
            if not any(
                matches_dependency_request(
                    record,
                    ecosystem="github-actions",
                    name=name,
                    ref=ref,
                    operation=operation,
                    file=path,
                    command=None,
                )
                for record in dependency_records
            ):
                unapproved_actions.append(f"{path}:{name}@{ref}")
        for name, ref in sorted(removed_refs):
            if name in replaced_names:
                continue
            if not any(
                matches_dependency_request(
                    record,
                    ecosystem="github-actions",
                    name=name,
                    ref=ref,
                    operation="remove",
                    file=path,
                    command=None,
                )
                for record in dependency_records
            ):
                unapproved_actions.append(f"{path}:remove:{name}@{ref}")
    if invalid_actions or unapproved_actions:
        findings.append(
            {
                "severity": "gate",
                "rule": "POLICY-GITHUB-ACTION-APPROVAL",
                "evidence": ", ".join(sorted(invalid_actions) + unapproved_actions),
                "message": "A new or updated external GitHub Action use is unparseable or does not exactly match a machine-readable dependency approval.",
            }
        )
    status = "blocked" if any(item["severity"] == "gate" for item in findings) else "pass"
    return emit({"status": status, "root": str(root), "changed_files": files, "findings": findings}, 2 if status == "blocked" else 0)


def validate_profile_command(args: argparse.Namespace) -> int:
    try:
        data = engineering_context.read_toml(args.profile.resolve())
    except (OSError, tomllib.TOMLDecodeError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "profile": str(args.profile), "errors": [str(exc)]}, 2)
    errors = engineering_context.validate_profile_data(data, source=str(args.profile.resolve()))
    return emit(
        {"status": "valid" if not errors else "invalid", "profile": str(args.profile.resolve()), "errors": errors},
        0 if not errors else 2,
    )


def resolve_profiles_command(args: argparse.Namespace) -> int:
    try:
        snapshot = engineering_context.resolve_profiles(
            args.root.resolve(),
            facts=args.fact,
            task_paths=args.path,
            codex_home=args.codex_home,
            baseline=skill_root() / "references" / "neutral-baseline.toml",
            task_profiles=args.task_profile,
            profile_mode=args.profile_mode,
        )
    except (OSError, ValueError, tomllib.TOMLDecodeError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if args.output:
        engineering_context.write_json(args.output.resolve(), snapshot)
    code = 2 if snapshot["outcome"] == "blocked" else 0
    return emit({"status": snapshot["outcome"], "output": str(args.output.resolve()) if args.output else None, "snapshot": snapshot}, code)


def assess_context_command(args: argparse.Namespace) -> int:
    registry = plugin_root() / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json"
    try:
        result = engineering_context.assess_context(
            args.root.resolve(),
            task_type=args.task_type,
            risks=args.risk,
            task_paths=args.path,
            facts=args.fact,
            tier=args.tier,
            codex_home=args.codex_home,
            skill_roots=args.skill_root,
            capability_registry=registry,
            task_profiles=args.task_profile,
            packet=args.packet.resolve() if args.packet else None,
            profile_mode=args.profile_mode,
            working_directory=args.working_directory,
            detail=args.detail,
        )
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    result["projection_fingerprint"] = engineering_context_projection_fingerprint(result)
    output_path = args.output
    if output_path is None and args.packet:
        output_path = args.packet / "context-readiness.json"
    if output_path:
        engineering_context.write_json(output_path.resolve(), result)
    code = 2 if result["outcome"] == "blocked" else 0
    return emit({"status": result["outcome"], "output": str(output_path.resolve()) if output_path else None, "readiness": result}, code)


def methodology_registry_path(path: Path | None = None) -> Path:
    return path.resolve() if path is not None else plugin_root() / "governance" / "methodology-pool.json"


def validate_methods_command(args: argparse.Namespace) -> int:
    """Validate the source, method, and risk-model contracts as one graph."""
    registry_path = methodology_registry_path(args.registry)
    repository_root = args.root.resolve() if args.root else plugin_root()
    try:
        payload = methodology_system.read_registry(registry_path)
        errors = methodology_system.validate_registry(payload, repository_root=repository_root)
    except (OSError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": [str(exc)]}, 2)
    if errors:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": errors}, 2)
    method_risks = set(payload["vocabulary"]["risks"])
    alias_targets = {
        target
        for targets in methodology_system.ENGINEERING_RISK_ALIASES.values()
        for target in targets
    }
    expected_aliases = engineering_context.RISK_TOKENS - method_risks
    unexpected_aliases = sorted(
        set(methodology_system.ENGINEERING_RISK_ALIASES) - expected_aliases
    )
    uncovered_engineering_risks = sorted(
        engineering_context.RISK_TOKENS
        - method_risks
        - set(methodology_system.ENGINEERING_RISK_ALIASES)
    )
    invalid_alias_targets = sorted(alias_targets - method_risks)
    if uncovered_engineering_risks or invalid_alias_targets or unexpected_aliases:
        coverage_errors = []
        if uncovered_engineering_risks:
            coverage_errors.append(
                f"engineering risks lack methodology translation {uncovered_engineering_risks}"
            )
        if invalid_alias_targets:
            coverage_errors.append(
                f"methodology risk aliases target unknown risks {invalid_alias_targets}"
            )
        if unexpected_aliases:
            coverage_errors.append(
                f"methodology risk aliases are not routing-only engineering risks {unexpected_aliases}"
            )
        return emit(
            {"status": "invalid", "registry": str(registry_path), "errors": coverage_errors},
            2,
        )
    return emit(
        {
            "status": "valid",
            "registry": str(registry_path),
            "schema_version": payload["schema_version"],
            "sources": len(payload["sources"]),
            "methods": len(payload["methods"]),
            "risk_models": len(payload["risk_models"]),
            "engineering_risks_covered": len(engineering_context.RISK_TOKENS),
            "risk_aliases": len(methodology_system.ENGINEERING_RISK_ALIASES),
            "phases": payload["selection_contract"]["phase_order"],
        }
    )


def select_methods_command(args: argparse.Namespace) -> int:
    """Select a bounded assurance-method stack from explicit observed facts."""
    registry_path = methodology_registry_path(args.registry)
    repository_root = args.root.resolve() if args.root else plugin_root()
    try:
        payload = methodology_system.read_registry(registry_path)
        result = methodology_system.select_methods(
            payload,
            repository_root=repository_root,
            phase=args.phase,
            task_type=args.task_type,
            risks=args.risk,
            signals=args.signal,
            available=args.available,
            depth=args.depth,
            max_methods=args.max_methods,
        )
    except (OSError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": [str(exc)]}, 2)
    result["registry"] = str(registry_path)
    return emit(result)


def record_methods_command(args: argparse.Namespace) -> int:
    """Persist a fresh packet-bound method selection and owner/artifact trace."""
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if metadata.get("work_mode") != "governed" or not packet_has_immutable_creation_capability(
        packet, METHOD_SELECTION_SKILL_VERSION_TAG
    ):
        return emit(
            {
                "status": "invalid",
                "errors": [
                    "record-methods requires a governed packet created with method-selection-v1"
                ],
            },
            2,
        )
    allowed_states = {
        "design": {"awaiting-approval"},
        "verification": {"implementing"},
        "review": {"verifying"},
    }
    allowed = allowed_states.get(args.phase)
    if allowed is not None and metadata.get("state") not in allowed:
        return emit(
            {
                "status": "invalid",
                "errors": [
                    f"{args.phase} method selection requires packet state in {sorted(allowed)}"
                ],
            },
            2,
        )
    raw_risks = sorted(
        {
            value
            for value in [*metadata.get("risk_modifiers", []), *args.risk]
            if isinstance(value, str)
        }
    )
    try:
        risks = sorted(engineering_context.canonical_risks(raw_risks))
        record = persist_method_selection(
            packet,
            metadata,
            phase=args.phase,
            risks=risks,
            signals=args.signal,
            available=args.available,
            depth=args.depth,
            max_methods=args.max_methods,
            preliminary=False,
        )
    except (OSError, ValueError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    selection = record["selection"]
    return emit(
        {
            "status": "recorded",
            "packet": str(packet),
            "phase": record["phase"],
            "sequence": record["sequence"],
            "selection_status": selection["status"],
            "selected_methods": [item["id"] for item in selection["selected_methods"]],
            "blocked_methods": [item["method_id"] for item in selection["blocked_methods"]],
            "artifacts": ["method-selection.json", "method-selection.md"],
        }
    )


def route_task(args: argparse.Namespace) -> int:
    routes: list[str] = ["repo-context"]
    reasons: dict[str, list[str]] = {"repo-context": ["repository facts and task-relative readiness"]}

    def add(skill: str, reason: str) -> None:
        if skill not in routes:
            routes.append(skill)
        reasons.setdefault(skill, []).append(reason)

    needs = set(args.need)
    unknowns = set(args.unknown)
    # An unresolved delivery dimension is not delivery intent or authority.
    needs.update(value for value in unknowns if value in {"architecture", "dependency", "diagnosis", "review"})
    mutation_intent = args.mutation or ("none" if args.task_type == "read-only-audit" else "persistent")
    if args.task_type == "read-only-audit" and mutation_intent != "none":
        return emit({"status": "invalid", "errors": ["read-only-audit cannot declare persistent mutation"]}, 2)
    decision_work = args.task_type != "read-only-audit"
    mutating = decision_work and mutation_intent == "persistent"
    conservative_risks = list(args.risk)
    conservative_risks.extend(
        {
            "security": "security",
            "data": "persisted-data",
            "compatibility": "compatibility",
            "dependency": "dependency",
        }[value]
        for value in sorted(unknowns & {"security", "data", "compatibility", "dependency"})
    )
    try:
        risks = engineering_context.canonical_risks(conservative_risks)
        work_mode, mode_reasons = select_work_mode(
            args.task_type,
            risks,
            args.work_mode,
            persistent_mutation=mutating,
        )
    except ValueError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if (args.ui_impact == "material" or "ui" in unknowns) and work_mode != "governed":
        if args.work_mode != "auto":
            message = (
                "material UI impact requires governed work mode"
                if args.ui_impact == "material"
                else "unresolved UI impact requires governed work mode"
            )
            return emit({"status": "invalid", "errors": [message]}, 2)
        work_mode, mode_reasons = "governed", ["material-ui-impact" if args.ui_impact == "material" else "unresolved-ui-impact"]
    if args.profile_operation:
        add("manage-engineering-profiles", "explicit profile or instruction lifecycle operation")
    if args.ui_impact in {"preserve", "material"} or "ui" in unknowns:
        add(
            "product-ux-discovery",
            "material or unresolved UI intent and UX Ready baseline"
            if args.ui_impact == "material" or "ui" in unknowns
            else "existing UI intent and protected behavior",
        )
    if (
        mutating
        or
        args.ambiguity
        or args.task_type in {"large-feature", "large-refactor", "migration", "dependency-change", "security"}
        or args.ui_impact == "material"
        or unknowns & {"compatibility", "data", "security", "ui"}
        or decision_work and risks & REQUIREMENTS_ROUTING_RISKS
    ):
        add("requirements-design", "durable requirement understanding, scope, and compatibility baseline")
    if args.task_type == "bugfix" or "diagnosis" in needs or risks & DIAGNOSIS_ROUTING_RISKS:
        add("systematic-debugging", "failure reproduction and causal diagnosis")
    if (
        "architecture" in needs
        or args.task_type in {"large-feature", "large-refactor", "migration", "performance", "security"}
        or decision_work and risks & ARCHITECTURE_ROUTING_RISKS
    ):
        add("architecture-decisions", "material boundary, ownership, state, compatibility, or resource decision")
    if "dependency" in needs or args.task_type == "dependency-change" or decision_work and "dependency" in risks:
        add("dependency-decisions", "dependency, tool, service, plugin, or feature decision")
    if args.suite_maintenance:
        add("dev-flow-maintainer", "explicit Dev Flow suite maintenance")
    if mutating or "verification" in needs:
        add("verification", "risk-based fresh evidence")
    review_risks = engineering_context.GOVERNED_RISKS
    if (
        "review" in needs
        or risks & review_risks
        or args.ui_impact == "material"
        or args.suite_maintenance
        or args.task_type in {"security", "migration", "release-hotfix", "dependency-change", "rollback"}
    ):
        add("change-review", "independent specification and adversarial review")
    if "delivery" in needs:
        add("delivery-readiness", "acceptance, rollback, and delivery authority accounting")
    method_risks, risk_translations, unmapped_method_risks = methodology_system.normalize_risks(
        methodology_system.read_registry(methodology_registry_path())["vocabulary"],
        sorted(risks),
    )
    return emit(
        {
            "status": "routed",
            "kernel": "dev-flow",
            "quality_kernel": {
                "always_loaded": True,
                "requirements": "resolve repository facts, persist understood semantics, and stop affected slices on open material ambiguity",
                "continuity": "rehydrate at lifecycle and premise-change triggers from digest-bound requirement, design, context, and checkpoint state",
                "testing": "account black-box and white-box views separately; challenge oracle failure sensitivity",
                "challenge": "root performs basic specification and adversarial checks at every phase; independent deep review remains risk-routed",
                "knowledge": "record a project-knowledge impact/disposition and promote only implemented, verified, reusable truth",
                "specialists": "derive neutral outcomes first, then load the minimum repository-valid technical Skills; re-resolve on path, phase, rule, or risk drift",
            },
            "work_mode": work_mode,
            "work_mode_reasons": mode_reasons,
            "routes": [{"skill": skill, "reasons": reasons[skill]} for skill in routes],
            "unresolved_dimensions": sorted(unknowns),
            "method_selection": {
                "required": work_mode == "governed",
                "input_risks": sorted(risks),
                "canonical_risks": method_risks,
                "translations": risk_translations,
                "unmapped_risks": unmapped_method_risks,
                "lifecycle_gates": ["design", "verification", "review"]
                if work_mode == "governed"
                else [],
            },
            "excluded": {
                "manage-engineering-profiles": "ordinary profile consumption does not activate management" if not args.profile_operation else None,
                "dev-flow-maintainer": "explicit-only" if not args.suite_maintenance else None,
            },
        }
    )


def route_agent_command(args: argparse.Namespace) -> int:
    """Resolve a child role/workload to a concrete Multi-Agent V2 request."""
    try:
        result = agent_dispatch.route_agent(
            role=args.role,
            workload=args.workload,
            risks=args.risk,
            signals=args.signal,
            requested_profile=args.profile,
            acknowledge_exception=args.acknowledge_exception,
            acknowledge_downgrade=args.acknowledge_downgrade,
            registry_path=args.registry,
        )
    except (agent_dispatch.DispatchContractError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    return emit(result)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    skill_file = path / "SKILL.md"
    try:
        frontmatter = parse_frontmatter(skill_file)
        if frontmatter.get("name") != path.name:
            errors.append(f"{path.name}: frontmatter name must equal directory name")
        if not frontmatter.get("description"):
            errors.append(f"{path.name}: missing description")
    except (OSError, ValueError) as exc:
        return [f"{path.name}: {exc}"]
    text = skill_file.read_text(encoding="utf-8")
    for reference in re.findall(r"`((?:references|templates|scripts|assets)/[^`]+)`", text):
        if any(char in reference for char in "*<>"):
            continue
        if not (path / reference).exists():
            errors.append(f"{path.name}: broken resource reference {reference}")
    yaml_path = path / "agents" / "openai.yaml"
    if not yaml_path.is_file() or f"${path.name}" not in yaml_path.read_text(encoding="utf-8"):
        errors.append(f"{path.name}: agents/openai.yaml default prompt must mention ${path.name}")
    return errors


def check_plugin(args: argparse.Namespace) -> int:
    root = (args.plugin_root or plugin_root()).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest: dict[str, Any] = {}
    try:
        manifest = read_json(root / ".codex-plugin" / "plugin.json")
        if manifest.get("name") != "dev-flow":
            errors.append("plugin name must be dev-flow")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(manifest.get("version", ""))):
            errors.append("plugin version is not valid semver")
        if manifest.get("license") != "MIT":
            errors.append("plugin license must be MIT")
        for field in ("homepage", "repository"):
            if not str(manifest.get(field, "")).startswith("https://"):
                errors.append(f"plugin {field} must be an absolute HTTPS URL")
        author = manifest.get("author", {})
        if not isinstance(author, dict) or not author.get("name") or not str(author.get("url", "")).startswith("https://"):
            errors.append("plugin author must include a name and absolute HTTPS URL")
        if not isinstance(manifest.get("keywords"), list) or not manifest["keywords"]:
            errors.append("plugin keywords must be a non-empty list")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin manifest: {exc}")

    for required_document in (
        "LICENSE",
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".agents/plugins/marketplace.json",
    ):
        if not (root / required_document).is_file():
            errors.append(f"missing public repository document: {required_document}")

    try:
        marketplace = read_json(root / ".agents" / "plugins" / "marketplace.json")
        entries = marketplace.get("plugins", [])
        matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == manifest.get("name")]
        if len(matching) != 1:
            errors.append("marketplace must contain exactly one dev-flow entry")
        else:
            source = matching[0].get("source", {})
            if source != {"source": "local", "path": "."}:
                errors.append("marketplace plugin source must be the current immutable marketplace snapshot")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid marketplace manifest: {exc}")

    try:
        capabilities = read_json(root / "governance" / "capability-contracts.json").get("capabilities", [])
        expected_skills = {
            item.get("skill")
            for item in capabilities
            if isinstance(item, dict) and isinstance(item.get("skill"), str) and item["skill"]
        }
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid capability registry: {exc}")
        expected_skills = set()
    observed_skills = {path.name for path in (root / "skills").glob("*/") if path.is_dir()}
    if observed_skills != expected_skills:
        errors.append(f"skill inventory mismatch: expected {sorted(expected_skills)}, observed {sorted(observed_skills)}")
    for path in sorted((root / "skills").glob("*/")):
        errors.extend(validate_skill(path))
        skill_lines = (path / "SKILL.md").read_text(encoding="utf-8").count("\n") + 1
        if skill_lines > 500:
            errors.append(f"{path.name}: SKILL.md exceeds the 500-line progressive-disclosure envelope")

    for json_path in sorted(root.rglob("*.json")):
        if "/.git/" in str(json_path):
            continue
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {json_path.relative_to(root)}: {exc}")

    for toml_path in sorted(root.rglob("*.toml")):
        try:
            tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"invalid TOML {toml_path.relative_to(root)}: {exc}")

    hooks = root / "hooks" / "hooks.json"
    if not hooks.is_file():
        errors.append("missing plugin hooks/hooks.json")
    for required in (
        root / "skills" / "dev-flow" / "references" / "neutral-baseline.toml",
        root / "skills" / "architecture-decisions" / "references" / "neutral-policy-registry.json",
        root / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json",
        root / "governance" / "industry-practices.json",
        root / "governance" / "methodology-pool.json",
        root / "evals" / "structural-coverage.json",
    ):
        if not required.is_file():
            errors.append(f"missing required governance file: {required.relative_to(root)}")

    try:
        baseline = engineering_context.read_toml(root / "skills" / "dev-flow" / "references" / "neutral-baseline.toml")
        errors.extend(engineering_context.validate_profile_data(baseline, source="neutral-baseline.toml"))
        engineering_context.load_capability_registry(
            root / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json"
        )
    except (OSError, tomllib.TOMLDecodeError, json.JSONDecodeError, engineering_context.ContractError) as exc:
        errors.append(f"invalid engineering context governance: {exc}")

    try:
        agent_dispatch.load_registry(
            root / "skills" / "dev-flow" / "references" / "agent-dispatch-profiles.json"
        )
    except (OSError, json.JSONDecodeError, agent_dispatch.DispatchContractError) as exc:
        errors.append(f"invalid agent dispatch registry: {exc}")

    try:
        methodology_registry = methodology_system.read_registry(
            root / "governance" / "methodology-pool.json"
        )
        errors.extend(
            f"methodology registry: {error}"
            for error in methodology_system.validate_registry(
                methodology_registry,
                repository_root=root,
            )
        )
    except (OSError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        errors.append(f"invalid methodology registry: {exc}")

    return emit({"status": "valid" if not errors else "invalid", "plugin": str(root), "errors": errors, "warnings": warnings}, 0 if not errors else 2)


def runtime_config_paths(destination: Path) -> tuple[list[Path], list[Path]]:
    source = skill_root() / "assets" / "agent-configs"
    configs = sorted(source.glob("*.toml"))
    return configs, [destination / config.name for config in configs]


def safe_current_pointer(root: Path) -> Path:
    flow = root / ".codex" / "dev-flow"
    if flow.is_symlink():
        raise PathContractError(f"Dev Flow state directory must not be a symlink: {flow}")
    if flow.exists() and not flow.is_dir():
        raise PathContractError(f"Dev Flow state path must be a directory: {flow}")
    return contained_path(flow, "current", label="current pointer", reject_symlinks=True)


def same_file_contents(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def atomic_copy(source: Path, target: Path) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".dev-flow-", dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def runtime_destination(args: argparse.Namespace) -> Path:
    configured = args.destination or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "agents"
    return configured.expanduser()


def install_runtime(args: argparse.Namespace) -> int:
    destination = runtime_destination(args)
    if destination.is_symlink():
        return emit({"status": "blocked", "errors": [f"runtime destination is a symlink: {destination}"]}, 2)
    if destination.exists() and not destination.is_dir():
        return emit({"status": "blocked", "errors": [f"runtime destination is not a directory: {destination}"]}, 2)
    destination.mkdir(parents=True, exist_ok=True)
    configs, targets = runtime_config_paths(destination)
    unchanged: list[str] = []
    to_install: list[tuple[Path, Path]] = []
    conflicts: list[dict[str, str]] = []
    unsafe: list[dict[str, str]] = []

    for config, target in zip(configs, targets, strict=True):
        if target.is_symlink():
            unsafe.append({"path": str(target), "reason": "symlink target is never overwritten"})
        elif not target.exists():
            to_install.append((config, target))
        elif not target.is_file():
            unsafe.append({"path": str(target), "reason": "target exists and is not a regular file"})
        elif same_file_contents(config, target):
            unchanged.append(str(target))
        else:
            conflicts.append({"path": str(target), "reason": "existing file differs from bundled config"})

    if unsafe or (conflicts and not args.force):
        return emit(
            {
                "status": "blocked",
                "installed": [],
                "unchanged": unchanged,
                "conflicts": [*unsafe, *conflicts],
                "hint": "Inspect the conflicts. Use --force only to replace differing regular files after backups are created.",
            },
            2,
        )

    backups: list[dict[str, str]] = []
    if conflicts:
        backup_root = destination / ".dev-flow-backups"
        if backup_root.is_symlink():
            return emit({"status": "blocked", "errors": [f"backup root is a symlink: {backup_root}"]}, 2)
        if backup_root.exists() and not backup_root.is_dir():
            return emit({"status": "blocked", "errors": [f"backup root is not a directory: {backup_root}"]}, 2)
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_dir = backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=False)
        conflict_paths = {entry["path"] for entry in conflicts}
        for config, target in zip(configs, targets, strict=True):
            if str(target) not in conflict_paths:
                continue
            backup = backup_dir / target.name
            shutil.copy2(target, backup)
            backups.append({"source": str(target), "backup": str(backup)})
            to_install.append((config, target))

    installed: list[str] = []
    for config, target in to_install:
        atomic_copy(config, target)
        installed.append(str(target))
    status = "installed" if installed else "unchanged"
    return emit(
        {
            "status": status,
            "installed": installed,
            "unchanged": unchanged,
            "backups": backups,
            "restart_required": bool(installed),
        }
    )


def uninstall_runtime(args: argparse.Namespace) -> int:
    destination = runtime_destination(args)
    if destination.is_symlink():
        return emit({"status": "blocked", "errors": [f"runtime destination is a symlink: {destination}"]}, 2)
    if destination.exists() and not destination.is_dir():
        return emit({"status": "blocked", "errors": [f"runtime destination is not a directory: {destination}"]}, 2)
    configs, targets = runtime_config_paths(destination)
    removable: list[Path] = []
    missing: list[str] = []
    conflicts: list[dict[str, str]] = []

    for config, target in zip(configs, targets, strict=True):
        if target.is_symlink():
            conflicts.append({"path": str(target), "reason": "symlink target is never removed"})
        elif not target.exists():
            missing.append(str(target))
        elif not target.is_file():
            conflicts.append({"path": str(target), "reason": "target exists and is not a regular file"})
        elif same_file_contents(config, target):
            removable.append(target)
        else:
            conflicts.append({"path": str(target), "reason": "file was modified or is not owned by this plugin version"})

    if conflicts:
        return emit(
            {
                "status": "blocked",
                "removed": [],
                "missing": missing,
                "conflicts": conflicts,
                "hint": "No files were removed. Resolve modified or unsafe targets manually, then retry.",
            },
            2,
        )

    for target in removable:
        target.unlink()
    return emit({"status": "uninstalled" if removable else "unchanged", "removed": [str(path) for path in removable], "missing": missing})


def archive_packet(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    if metadata.get("state") != "accepted":
        return emit({"status": "blocked", "errors": ["only an accepted packet can be archived"]}, 2)
    parent = packet.parent
    try:
        current = contained_path(parent, "current", label="current pointer", reject_symlinks=True)
        archive = contained_path(
            parent,
            Path("archive") / packet.name,
            label="packet archive",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        return emit({"status": "blocked", "errors": [str(exc)]}, 2)
    if archive.exists():
        return emit({"status": "blocked", "errors": [f"archive target exists: {archive}"]}, 2)
    archive.parent.mkdir(exist_ok=True)
    now = utc_now()
    metadata["history"].append({"from": "accepted", "to": "archived", "at": now, "note": args.note})
    metadata["state"] = "archived"
    metadata["updated_at"] = now
    write_packet(packet, metadata, "transition", {"from": "accepted", "to": "archived", "note": args.note})
    packet.rename(archive)
    if current.exists() and current.read_text(encoding="utf-8").strip() == packet.name:
        current.unlink()
    return emit({"status": "archived", "packet": str(archive)})


def deactivate_packet(args: argparse.Namespace) -> int:
    """Remove only a matching terminal packet from the active pointer."""
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    state = metadata.get("state")
    if state not in {"accepted", "archived"}:
        return emit(
            {
                "status": "blocked",
                "errors": ["only an accepted or archived packet can be deactivated"],
            },
            2,
        )

    flow = packet.parent.parent if packet.parent.name == "archive" else packet.parent
    direct_packet = packet.parent == flow
    archived_packet = packet.parent.name == "archive" and packet.parent.parent == flow
    valid_flow = flow.name == "dev-flow" and flow.parent.name == ".codex"
    if not valid_flow or not (direct_packet or archived_packet):
        return emit({"status": "blocked", "errors": ["packet is outside a Dev Flow packet directory"]}, 2)

    current = flow / "current"
    if current.is_symlink():
        return emit({"status": "blocked", "errors": [f"current pointer must not be a symlink: {current}"]}, 2)
    if not current.exists():
        return emit({"status": "unchanged", "packet": str(packet), "reason": "current pointer is already absent"})
    if not current.is_file():
        return emit({"status": "blocked", "errors": [f"current pointer must be a regular file: {current}"]}, 2)
    try:
        active_change_id = current.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return emit({"status": "blocked", "errors": [f"cannot read current pointer: {exc}"]}, 2)
    if active_change_id != packet.name:
        return emit(
            {
                "status": "blocked",
                "errors": [f"current pointer names {active_change_id!r}, not {packet.name!r}"],
            },
            2,
        )
    try:
        current.unlink()
    except OSError as exc:
        return emit({"status": "blocked", "errors": [f"cannot deactivate current pointer: {exc}"]}, 2)
    return emit({"status": "deactivated", "packet": str(packet), "current": str(current)})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--codex")
    preflight.add_argument("--version-output")
    preflight.add_argument("--features-output-file", type=Path)
    preflight.add_argument("--config", type=Path)
    preflight.add_argument("--skip-config", action="store_true")
    preflight.add_argument("--tool-surface-confirmed", action="store_true")
    preflight.add_argument("--require-delegation", action="store_true")
    preflight.set_defaults(func=codex_preflight)

    init = sub.add_parser("init-packet")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--change-id", required=True)
    init.add_argument("--task-type", required=True)
    init.add_argument("--objective", required=True)
    init.add_argument("--authority", default="local edits and tests only")
    init.add_argument("--profile", action="append", default=[])
    init.add_argument("--risk", action="append", default=[])
    init.add_argument("--collaboration-profile", choices=sorted(COLLABORATION_PROFILES))
    init.add_argument("--ui-impact", choices=sorted(UI_IMPACTS), default="none")
    init.add_argument("--compatibility-required", action="store_true")
    init.add_argument("--mutation", choices=("none", "persistent"))
    init.add_argument("--reuse", action="store_true")
    init.add_argument("--work-mode", choices=("auto", *sorted(WORK_MODES)), default="auto")
    init.set_defaults(func=init_packet)

    validate = sub.add_parser("validate-packet")
    validate.add_argument("packet", type=Path)
    validate.set_defaults(func=validate_packet)

    transition = sub.add_parser("transition")
    transition.add_argument("packet", type=Path)
    transition.add_argument("state", choices=sorted(STATES))
    transition.add_argument("--note", required=True)
    transition.add_argument("--approved-by")
    transition.add_argument("--ambiguity-id", help="Open material AMB-n that justifies content-bound reopening")
    transition.set_defaults(func=transition_packet)

    checkpoint = sub.add_parser("record-checkpoint", help="Persist a digest-bound semantic recovery checkpoint")
    checkpoint.add_argument("packet", type=Path)
    checkpoint.add_argument("--trigger", choices=sorted(CONTINUITY_TRIGGERS), required=True)
    checkpoint.add_argument("--objective", required=True)
    checkpoint.add_argument("--active-id", action="append", required=True)
    checkpoint.add_argument("--last-evidence", required=True)
    checkpoint.add_argument("--next-action", required=True)
    checkpoint.add_argument("--stop-condition", required=True)
    checkpoint.add_argument(
        "--repository-reconciliation",
        help="required when repository identity, HEAD, or worktree bytes changed since the prior checkpoint",
    )
    checkpoint.add_argument(
        "--accept-head",
        action="append",
        default=[],
        metavar="ROOT=OID",
        help="exact current Git OID accepted for each changed repository root; repeat per root",
    )
    checkpoint.add_argument("--drift", choices=("aligned", "reopened"), default="aligned")
    checkpoint.set_defaults(func=record_checkpoint)

    resume = sub.add_parser("resume-packet", help="Rehydrate the current requirement, design, context, and checkpoint")
    resume.add_argument("packet", type=Path)
    resume.set_defaults(func=resume_packet)

    bind = sub.add_parser("bind-knowledge", help="Bind a final knowledge disposition or tracked change dossier")
    bind.add_argument("packet", type=Path)
    bind.add_argument("--impact", choices=sorted(knowledge_system.KNOWLEDGE_IMPACTS), required=True)
    bind.add_argument("--rationale", required=True)
    bind.add_argument("--root", type=Path)
    bind.add_argument("--project-root")
    bind.add_argument("--changes-root")
    bind.add_argument("--convention-path", default=knowledge_system.DEFAULT_CONVENTION_PATH)
    bind.add_argument("--manifest", help="repository-relative path to the change dossier manifest")
    bind.set_defaults(func=bind_knowledge)

    knowledge = sub.add_parser("validate-knowledge", help="Validate tracked project truth and change dossiers")
    knowledge.add_argument("--root", type=Path, required=True)
    knowledge.add_argument("--project-root")
    knowledge.add_argument("--changes-root")
    knowledge.add_argument("--convention-path", default=knowledge_system.DEFAULT_CONVENTION_PATH)
    knowledge.add_argument("--change-id")
    knowledge.set_defaults(func=validate_knowledge_command)

    iteration = sub.add_parser("record-iteration", help="Record a causal hypothesis or repair attempt and enforce the three-round breaker")
    iteration.add_argument("packet", type=Path)
    iteration.add_argument("--kind", choices=sorted(ITERATION_KINDS), required=True)
    iteration.add_argument("--cause-id", required=True)
    iteration.add_argument("--cause-file", required=True, help="relative path below packet artifacts/ containing stable causal evidence")
    iteration.add_argument("--outcome", choices=sorted(ITERATION_OUTCOMES), required=True)
    iteration.add_argument("--reopened-owner", choices=sorted(ITERATION_OWNERS))
    iteration.add_argument("--note", required=True)
    iteration.set_defaults(func=record_iteration)

    approval = sub.add_parser("record-approval")
    approval.add_argument("packet", type=Path)
    approval.add_argument("kind", choices=("requirements", "ux", "dependencies", "waivers", "delivery"))
    approval.add_argument("--id", required=True)
    approval.add_argument("--by", required=True)
    approval.add_argument("--note", required=True)
    approval.add_argument("--scope", action="append", default=[])
    approval.add_argument("--blocker", action="append", default=[])
    approval.add_argument("--residual-risk")
    approval.add_argument("--expires-at")
    approval.add_argument("--recheck-trigger")
    approval.add_argument("--dependency-ecosystem", choices=("cargo", "npm", "github-actions", "other"))
    approval.add_argument("--dependency-name")
    approval.add_argument("--dependency-version")
    approval.add_argument("--dependency-ref")
    approval.add_argument("--dependency-command")
    approval.add_argument("--dependency-file", action="append", default=[])
    approval.add_argument("--dependency-operation", action="append", choices=("add", "update", "remove"), default=[])
    approval.add_argument("--dependency-result-sha256", action="append", default=[])
    approval.set_defaults(func=record_approval)

    ambiguity = sub.add_parser("record-ambiguity", help="Record a structured content-bound semantic ambiguity")
    ambiguity.add_argument("packet", type=Path)
    ambiguity.add_argument("--summary", required=True)
    ambiguity.add_argument("--source", required=True)
    ambiguity.add_argument("--interpretation", action="append", required=True)
    ambiguity.add_argument("--evidence", action="append", default=[])
    ambiguity.add_argument("--materiality", choices=sorted(AMBIGUITY_MATERIALITIES), required=True)
    ambiguity.add_argument("--owner", choices=sorted(AMBIGUITY_OWNERS), required=True)
    ambiguity.add_argument("--affects", action="append", default=[])
    ambiguity.add_argument("--recommendation", required=True)
    ambiguity.set_defaults(func=record_ambiguity)

    resolution = sub.add_parser("resolve-ambiguity", help="Resolve an open content-bound semantic ambiguity")
    resolution.add_argument("packet", type=Path)
    resolution.add_argument("--id", required=True)
    resolution.add_argument(
        "--status",
        choices=sorted(AMBIGUITY_STATUSES - {"open"}),
        required=True,
    )
    resolution.add_argument("--by", required=True)
    resolution.add_argument("--resolution", required=True)
    resolution.add_argument("--evidence", action="append", required=True)
    resolution.set_defaults(func=resolve_ambiguity)

    audit = sub.add_parser("audit-preferences")
    audit.add_argument("--root", type=Path, required=True)
    audit.add_argument("--packet", type=Path)
    audit.add_argument("--base")
    audit.set_defaults(func=audit_preferences)

    profile = sub.add_parser("validate-profile", help="Validate one engineering profile TOML file")
    profile.add_argument("profile", type=Path)
    profile.set_defaults(func=validate_profile_command)

    resolve = sub.add_parser("resolve-profiles", help="Resolve layered engineering profiles for a task")
    resolve.add_argument("--root", type=Path, required=True)
    resolve.add_argument("--output", type=Path)
    resolve.add_argument("--path", action="append", default=[])
    resolve.add_argument("--fact", action="append", default=[])
    resolve.add_argument("--task-profile", type=Path, action="append", default=[])
    resolve.add_argument("--codex-home", type=Path)
    resolve.add_argument("--profile-mode", choices=sorted(engineering_context.PROFILE_MODES), default="personal-interactive")
    resolve.set_defaults(func=resolve_profiles_command)

    readiness = sub.add_parser("assess-context", help="Assess task-relative Engineering Context Readiness and quality coverage")
    readiness.add_argument("--root", type=Path, required=True)
    readiness.add_argument("--task-type", choices=sorted(TASK_TYPES), required=True)
    readiness.add_argument("--risk", action="append", default=[])
    readiness.add_argument("--path", action="append", default=[])
    readiness.add_argument("--fact", action="append", default=[])
    readiness.add_argument("--tier", choices=sorted(engineering_context.TIERS))
    readiness.add_argument("--task-profile", type=Path, action="append", default=[])
    readiness.add_argument("--skill-root", type=Path, action="append", default=[])
    readiness.add_argument("--codex-home", type=Path)
    readiness.add_argument("--profile-mode", choices=sorted(engineering_context.PROFILE_MODES), default="personal-interactive")
    readiness.add_argument("--working-directory", type=Path)
    readiness.add_argument("--detail", choices=sorted(engineering_context.READINESS_DETAILS), default="compact")
    readiness.add_argument("--packet", type=Path)
    readiness.add_argument("--output", type=Path)
    readiness.set_defaults(func=assess_context_command)

    validate_methods = sub.add_parser(
        "validate-methods",
        help="Validate the assurance methodology pool, sources, references, and risk models",
    )
    validate_methods.add_argument("--registry", type=Path)
    validate_methods.add_argument("--root", type=Path)
    validate_methods.set_defaults(func=validate_methods_command)

    select_methods = sub.add_parser(
        "select-methods",
        help="Select a bounded method stack from lifecycle, risk, and observed failure signals",
    )
    select_methods.add_argument("--phase", required=True)
    select_methods.add_argument("--task-type", choices=sorted(TASK_TYPES), required=True)
    select_methods.add_argument("--risk", action="append", default=[])
    select_methods.add_argument("--signal", action="append", default=[])
    select_methods.add_argument("--available", action="append", default=[])
    select_methods.add_argument("--depth", choices=("starter", "deep", "formal"), default="starter")
    select_methods.add_argument("--max-methods", type=int)
    select_methods.add_argument("--registry", type=Path)
    select_methods.add_argument("--root", type=Path)
    select_methods.set_defaults(func=select_methods_command)

    record_methods = sub.add_parser(
        "record-methods",
        help="Select and persist a packet-bound method stack for a lifecycle gate",
    )
    record_methods.add_argument("packet", type=Path)
    record_methods.add_argument(
        "--phase", choices=("design", "verification", "review"), required=True
    )
    record_methods.add_argument("--risk", action="append", default=[])
    record_methods.add_argument("--signal", action="append", default=[])
    record_methods.add_argument("--available", action="append", default=[])
    record_methods.add_argument(
        "--depth", choices=("starter", "deep", "formal"), default="starter"
    )
    record_methods.add_argument("--max-methods", type=int)
    record_methods.set_defaults(func=record_methods_command)

    route = sub.add_parser("route-task", help="Select the minimal built-in Skill composition for a classified task")
    route.add_argument("--task-type", choices=sorted(TASK_TYPES), required=True)
    route.add_argument("--risk", action="append", default=[])
    route.add_argument("--need", choices=("architecture", "dependency", "diagnosis", "verification", "review", "delivery"), action="append", default=[])
    route.add_argument("--ui-impact", choices=sorted(UI_IMPACTS), default="none")
    route.add_argument("--ambiguity", action="store_true")
    route.add_argument("--profile-operation", action="store_true")
    route.add_argument("--suite-maintenance", action="store_true")
    route.add_argument("--mutation", choices=("none", "persistent"))
    route.add_argument(
        "--unknown",
        choices=("architecture", "compatibility", "data", "delivery", "dependency", "diagnosis", "review", "security", "ui"),
        action="append",
        default=[],
        help="Unresolved risk dimension; route conservatively until repository evidence closes it",
    )
    route.add_argument("--work-mode", choices=("auto", *sorted(WORK_MODES)), default="auto")
    route.set_defaults(func=route_task)

    agent_route = sub.add_parser(
        "route-agent",
        help="Select a deterministic Multi-Agent V2 dispatch profile for one child workload",
    )
    agent_route.add_argument("--role", required=True)
    agent_route.add_argument("--workload", required=True)
    agent_route.add_argument("--risk", action="append", default=[])
    agent_route.add_argument("--signal", action="append", default=[])
    agent_route.add_argument("--profile")
    agent_route.add_argument(
        "--acknowledge-exception",
        action="store_true",
        help="Required for the explicit PX exceptional profile",
    )
    agent_route.add_argument(
        "--acknowledge-downgrade",
        action="store_true",
        help="Allow an explicit profile below the policy minimum without hiding the downgrade",
    )
    agent_route.add_argument("--registry", type=Path)
    agent_route.set_defaults(func=route_agent_command)

    check = sub.add_parser("check")
    check.add_argument("--plugin-root", type=Path)
    check.set_defaults(func=check_plugin)

    install = sub.add_parser("install-runtime", help="Install bundled Codex agent configs without silent overwrite")
    install.add_argument("--destination", type=Path)
    install.add_argument("--force", action="store_true", help="Back up and replace differing regular files")
    install.set_defaults(func=install_runtime)

    uninstall = sub.add_parser("uninstall-runtime", help="Remove only unmodified bundled Codex agent configs")
    uninstall.add_argument("--destination", type=Path)
    uninstall.set_defaults(func=uninstall_runtime)

    archive = sub.add_parser("archive-packet")
    archive.add_argument("packet", type=Path)
    archive.add_argument("--note", required=True)
    archive.set_defaults(func=archive_packet)

    deactivate = sub.add_parser(
        "deactivate-packet",
        help="Remove a matching accepted/archived packet from the active current pointer without deleting the packet",
    )
    deactivate.add_argument("packet", type=Path)
    deactivate.set_defaults(func=deactivate_packet)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
