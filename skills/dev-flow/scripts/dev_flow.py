#!/usr/bin/env python3
"""Stdlib-only runtime for Dev Flow."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Iterable

import engineering_context


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
MICRO_HEADINGS = (
    "Authority and repository facts",
    "Requirement and design",
    "Scope and protected behavior",
    "Progress and decisions",
    "Verification",
    "Blue and red audit",
    "Delivery and residual risk",
)
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
VERSION_RE = re.compile(r"(?:codex-cli\s+)?(\d+)\.(\d+)\.(\d+)(?:[-+][^\s]+)?")
FEATURE_RE = re.compile(r"^(multi_agent(?:_v2)?|hooks)\s+\S+\s+(true|false)\s*$", re.MULTILINE)


def documentation_family(profile: Any) -> str | None:
    if profile in {"micro", "trace"}:
        return "trace"
    if profile in {"full", "governed"}:
        return "governed"
    return None


def select_work_mode(task_type: str, risks: Iterable[str], requested: str = "auto") -> tuple[str, list[str]]:
    risk_set = set(risks)
    governed = {
        "security",
        "unsafe",
        "ffi",
        "abi",
        "public-api",
        "protocol",
        "persisted-data",
        "migration",
        "release",
        "deployment",
        "regulated",
    }
    if risk_set & governed or task_type in {"migration", "security", "release-hotfix", "dependency-change", "rollback"}:
        automatic, reasons = "governed", sorted(risk_set & governed) or [task_type]
    elif task_type in {"micro", "spike"}:
        automatic, reasons = "direct", [task_type]
    else:
        automatic, reasons = "traced", [task_type]
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


def ensure_local_exclude(root: Path) -> None:
    result = run(["git", "rev-parse", "--git-path", "info/exclude"], cwd=root)
    if result.returncode:
        return
    exclude = Path(result.stdout.strip())
    if not exclude.is_absolute():
        exclude = root / exclude
    exclude.parent.mkdir(parents=True, exist_ok=True)
    current = exclude.read_text(encoding="utf-8") if exclude.exists() else ""
    rule = ".codex/dev-flow/"
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

    try:
        work_mode, mode_reasons = select_work_mode(args.task_type, args.risk, args.work_mode)
    except ValueError as exc:
        return emit({"status": "error", "errors": [str(exc)]}, 2)
    if args.ui_impact == "material" and work_mode != "governed":
        if args.work_mode != "auto":
            return emit({"status": "error", "errors": ["material UI impact requires governed work mode"]}, 2)
        work_mode, mode_reasons = "governed", ["material-ui-impact"]
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
        current = root / ".codex" / "dev-flow" / "current"
        current.write_text(args.change_id + "\n", encoding="utf-8")
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
        elif work_mode == "traced":
            collaboration_profile = "execute"
        else:
            collaboration_profile = "checkpointed"
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": plugin_version(),
        "change_id": args.change_id,
        "state": "discovering",
        "work_mode": work_mode,
        "work_mode_reasons": mode_reasons,
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
        "ambiguity_ids": [],
        "ambiguities": [],
        "dependency_changes": [],
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
    write_packet(packet, metadata, "packet-created", {"from": None, "to": "discovering", "reasons": mode_reasons})
    current = root / ".codex" / "dev-flow" / "current"
    current.write_text(args.change_id + "\n", encoding="utf-8")
    ensure_local_exclude(root)
    return emit(
        {
            "status": "created",
            "packet": str(packet),
            "work_mode": work_mode,
            "profile": profile,
            "artifacts": ["packet.json", "events.jsonl", *(["trace.md"] if work_mode == "traced" else list(FULL_FILES))],
            "next_state": "awaiting-approval",
        }
    )


def load_packet(packet: Path) -> tuple[dict[str, Any], list[str]]:
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
    return metadata, errors


def validate_event_projection(packet: Path, metadata: dict[str, Any]) -> list[str]:
    if metadata.get("schema_version") != "2.0":
        return []
    ledger = packet / "events.jsonl"
    if not ledger.is_file():
        return ["missing required file: events.jsonl"]
    errors: list[str] = []
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
        if not isinstance(record.get("event"), str) or not record["event"]:
            errors.append(f"events.jsonl:{index}: event name is required")
        if parsed_timestamp(record.get("at")) is None:
            errors.append(f"events.jsonl:{index}: timezone-aware timestamp is required")
        if record.get("work_mode") != metadata.get("work_mode"):
            errors.append(f"events.jsonl:{index}: work_mode drifted from packet projection")
    if not events:
        return [*errors, "events.jsonl: at least one event is required"]
    if events[0].get("event") != "packet-created":
        errors.append("events.jsonl: first event must be packet-created")
    state_events = [item for item in events if item.get("event") in {"packet-created", "transition"}]
    history = metadata.get("history", [])
    if not isinstance(history, list) or len(state_events) != len(history):
        errors.append("events.jsonl: state events must project exactly to packet history")
    else:
        for index, (event, projected) in enumerate(zip(state_events, history, strict=True), start=1):
            payload = event.get("payload", {})
            if not isinstance(payload, dict) or payload.get("from") != projected.get("from") or payload.get("to") != projected.get("to"):
                errors.append(f"events.jsonl: state event {index} does not match packet history")
        if state_events and state_events[-1].get("state") != metadata.get("state"):
            errors.append("events.jsonl: final state does not match packet projection")
    return errors


def transition_packet(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    old = metadata.get("state")
    new = args.state
    now = utc_now()
    transition_at = parsed_timestamp(now)
    assert transition_at is not None
    schema_version = metadata.get("schema_version")
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
            validation, validation_code = validate_packet_data(packet)
            if validation_code:
                validation["status"] = "approval-blocked"
                return emit(validation, 2)
    if new == "accepted":
        report, code = validate_packet_data(packet, state_override="accepted")
        if code:
            report["status"] = "acceptance-blocked"
            return emit(report, 2)
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
        metadata.setdefault("approvals", {})["design"] = design_record
    write_packet(packet, metadata, "transition", {"from": old, "to": new, "note": args.note})
    return emit(
        {
            "status": "transitioned",
            "packet": str(packet),
            "from": old,
            "to": new,
            "requirement_revision": metadata.get("requirement_revision") if schema_version in CONTENT_BOUND_SCHEMA_VERSIONS else None,
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
    write_packet(packet, metadata, "approval-recorded", {"kind": args.kind, "id": args.id})
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
    write_packet(packet, metadata, "ambiguity-recorded", {"id": ambiguity_id})
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
    write_packet(packet, metadata, "ambiguity-resolved", {"id": args.id, "status": args.status})
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


def ids(text: str, kind: str) -> set[str]:
    return set(ID_PATTERNS[kind].findall(text))


def unresolved_audit_findings(text: str, prefix: str) -> list[str]:
    """Return prefixed finding IDs whose Markdown status cell is unresolved."""
    unresolved: list[str] = []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        finding_id = cells[0].split(":", 1)[0].strip()
        status = cells[-1].strip("*_`").lower()
        if re.fullmatch(rf"{re.escape(prefix)}-\d+", finding_id) and status in {"open", "pending", "unresolved"}:
            unresolved.append(finding_id)
    return unresolved


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
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        errors.append(f"packet.json: unsupported schema_version {metadata.get('schema_version')!r}")
    errors.extend(validate_event_projection(packet, metadata))
    if metadata.get("state") not in STATES:
        errors.append(f"packet.json: invalid state {metadata.get('state')!r}")
    if metadata.get("task_type") not in TASK_TYPES:
        errors.append(f"packet.json: invalid task_type {metadata.get('task_type')!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", str(metadata.get("change_id", ""))):
        errors.append("packet.json: invalid change_id")
    if schema_version in READINESS_SCHEMA_VERSIONS:
        collaboration_profile = metadata.get("collaboration_profile")
        ui_impact = metadata.get("ui_impact")
        if collaboration_profile not in COLLABORATION_PROFILES:
            errors.append(f"packet.json: invalid collaboration_profile {collaboration_profile!r}")
        if ui_impact not in UI_IMPACTS:
            errors.append(f"packet.json: invalid ui_impact {ui_impact!r}")

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

    state = state_override or metadata.get("state")
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
        if family == "trace":
            verification_body = heading_body(texts.get("trace.md", ""), "Verification") or ""
            statuses = set(re.findall(r"\b(?:PASSED|FAILED|FLAKY|BLOCKED|NOT RUN|WAIVED)\b", verification_body))
            invalid_statuses = statuses & {"FAILED", "FLAKY", "BLOCKED", "NOT RUN"}
            if invalid_statuses:
                errors.append(f"accepted trace retains unresolved verification statuses: {sorted(invalid_statuses)}")
            if "PASSED" not in statuses and not ("WAIVED" in statuses and approvals.get("waivers")):
                errors.append("accepted trace requires PASSED evidence or an approved WAIVED verification")
        else:
            matrix_rows: list[tuple[str, int, str, bool]] = []
            for line in texts.get("test-matrix.md", "").splitlines():
                if not re.match(r"^\|\s*TM-\d+\s*\|", line):
                    continue
                cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
                if len(cells) < 8:
                    errors.append(f"test-matrix.md: malformed matrix row `{line}`")
                    continue
                try:
                    attempts = int(cells[5])
                except ValueError:
                    errors.append(f"test-matrix.md: invalid attempts for {cells[0]}")
                    continue
                status_value = cells[6]
                if status_value not in STATUS_WORDS:
                    errors.append(f"test-matrix.md: invalid status {status_value!r} for {cells[0]}")
                    continue
                required = cells[4].lower() == "yes"
                matrix_rows.append((cells[0], attempts, status_value, required))
            if not matrix_rows:
                errors.append("accepted packet requires at least one parsed test-matrix cell")
            for cell, attempts, status_value, required in matrix_rows:
                if status_value == "PASSED" and attempts < 1:
                    errors.append(f"{cell}: PASSED requires at least one attempt")
                if required and status_value not in {"PASSED", "WAIVED"}:
                    errors.append(f"{cell}: required cell is {status_value}")
                if status_value == "WAIVED" and not approvals.get("waivers"):
                    errors.append(f"{cell}: WAIVED requires a waiver approval record")
            for audit, prefix in (("blue-audit.md", "BLUE"), ("red-audit.md", "RED")):
                unresolved = unresolved_audit_findings(texts.get(audit, ""), prefix)
                if unresolved:
                    warnings.append(f"{audit}: unresolved finding statuses: {', '.join(unresolved)}")

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


def added_diff(root: Path, base: str | None) -> tuple[list[str], dict[str, str]]:
    command = ["git", "diff", "--unified=0"]
    if base:
        command.append(base)
    result = run(command, cwd=root)
    staged = run(["git", "diff", "--cached", "--unified=0"], cwd=root)
    names_command = ["git", "diff", "--name-only"] + ([base] if base else [])
    names = run(names_command, cwd=root)
    staged_names = run(["git", "diff", "--cached", "--name-only"], cwd=root)
    untracked = run(["git", "ls-files", "--others", "--exclude-standard"], cwd=root)
    untracked_files = untracked.stdout.splitlines() if untracked.returncode == 0 else []
    files = sorted(set(names.stdout.splitlines()) | set(staged_names.stdout.splitlines()) | set(untracked_files))
    diff = result.stdout + "\n" + staged.stdout
    added_by_file: dict[str, list[str]] = {}
    current_file: str | None = None
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
            added_by_file.setdefault(current_file, [])
        elif line.startswith("+++"):
            current_file = None
        elif current_file and line.startswith("+"):
            added_by_file[current_file].append(line[1:])
    for relative in untracked_files:
        path = root / relative
        if path.is_file() and path.stat().st_size <= 2_000_000:
            try:
                added_by_file.setdefault(relative, []).append(path.read_text(encoding="utf-8"))
            except UnicodeDecodeError:
                continue
    return files, {path: "\n".join(lines) for path, lines in added_by_file.items()}


def audit_preferences(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    files, added_by_file = added_diff(root, args.base)
    findings: list[dict[str, str]] = []
    packet_meta: dict[str, Any] = {}
    if args.packet:
        packet_meta, _ = load_packet(args.packet.resolve())
    approved_dependencies = {
        item.get("id") for item in packet_meta.get("approvals", {}).get("dependencies", []) if isinstance(item, dict)
    }
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
            if matches and not approved_dependencies:
                evidence = ", ".join(matches)
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
    output_path = args.output
    if output_path is None and args.packet:
        output_path = args.packet / "context-readiness.json"
    if output_path:
        engineering_context.write_json(output_path.resolve(), result)
    code = 2 if result["outcome"] == "blocked" else 0
    return emit({"status": result["outcome"], "output": str(output_path.resolve()) if output_path else None, "readiness": result}, code)


def route_task(args: argparse.Namespace) -> int:
    routes: list[str] = ["repo-context"]
    reasons: dict[str, list[str]] = {"repo-context": ["repository facts and task-relative readiness"]}

    def add(skill: str, reason: str) -> None:
        if skill not in routes:
            routes.append(skill)
        reasons.setdefault(skill, []).append(reason)

    needs = set(args.need)
    risks = set(args.risk)
    try:
        work_mode, mode_reasons = select_work_mode(args.task_type, risks, args.work_mode)
    except ValueError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if args.ui_impact == "material" and work_mode != "governed":
        if args.work_mode != "auto":
            return emit({"status": "invalid", "errors": ["material UI impact requires governed work mode"]}, 2)
        work_mode, mode_reasons = "governed", ["material-ui-impact"]
    if args.profile_operation:
        add("manage-engineering-profiles", "explicit profile or instruction lifecycle operation")
    if args.ambiguity or args.task_type in {"large-feature", "large-refactor", "migration", "dependency-change"}:
        add("requirements-design", "material requirement, design, scope, or compatibility baseline")
    if args.ui_impact in {"preserve", "material"}:
        add("product-ux-discovery", f"UI impact is {args.ui_impact}")
    if "architecture" in needs or args.task_type in {"large-feature", "large-refactor", "performance"}:
        add("architecture-decisions", "material architecture or language/boundary decision")
    if "dependency" in needs or args.task_type == "dependency-change":
        add("dependency-decisions", "dependency, tool, service, plugin, or feature decision")
    if args.task_type == "bugfix" or "diagnosis" in needs:
        add("systematic-debugging", "failure reproduction and causal diagnosis")
    mutating = args.task_type not in {"read-only-audit", "spike"}
    if mutating or "verification" in needs:
        add("verification", "risk-based fresh evidence")
    review_risks = {"security", "unsafe", "ffi", "abi", "migration", "public-api", "protocol", "persisted-data"}
    if (
        "review" in needs
        or risks & review_risks
        or args.ui_impact == "material"
        or args.task_type in {"security", "migration", "release-hotfix", "dependency-change", "rollback"}
    ):
        add("change-review", "independent specification and adversarial review")
    if "delivery" in needs or args.task_type in {"release-hotfix", "rollback"}:
        add("delivery-readiness", "acceptance, rollback, and delivery authority accounting")
    if args.suite_maintenance:
        add("dev-flow-maintainer", "explicit Dev Flow suite maintenance")
    return emit(
        {
            "status": "routed",
            "kernel": "dev-flow",
            "work_mode": work_mode,
            "work_mode_reasons": mode_reasons,
            "routes": [{"skill": skill, "reasons": reasons[skill]} for skill in routes],
            "excluded": {
                "manage-engineering-profiles": "ordinary profile consumption does not activate management" if not args.profile_operation else None,
                "dev-flow-maintainer": "explicit-only" if not args.suite_maintenance else None,
            },
        }
    )


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
            expected_url = f"{str(manifest.get('repository', '')).rstrip('/')}.git"
            if source.get("source") != "url" or source.get("url") != expected_url:
                errors.append("marketplace source URL must match the plugin repository")
            if source.get("ref") != f"v{manifest.get('version')}":
                errors.append("marketplace ref must match the v-prefixed plugin version")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid marketplace manifest: {exc}")

    expected_skills = {
        "architecture-decisions",
        "change-review",
        "delivery-readiness",
        "dependency-decisions",
        "dev-flow",
        "dev-flow-maintainer",
        "manage-engineering-profiles",
        "product-ux-discovery",
        "repo-context",
        "requirements-design",
        "systematic-debugging",
        "verification",
    }
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

    return emit({"status": "valid" if not errors else "invalid", "plugin": str(root), "errors": errors, "warnings": warnings}, 0 if not errors else 2)


def runtime_config_paths(destination: Path) -> tuple[list[Path], list[Path]]:
    source = skill_root() / "assets" / "agent-configs"
    configs = sorted(source.glob("*.toml"))
    return configs, [destination / config.name for config in configs]


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
    archive = parent / "archive" / packet.name
    if archive.exists():
        return emit({"status": "blocked", "errors": [f"archive target exists: {archive}"]}, 2)
    archive.parent.mkdir(exist_ok=True)
    now = utc_now()
    metadata["history"].append({"from": "accepted", "to": "archived", "at": now, "note": args.note})
    metadata["state"] = "archived"
    metadata["updated_at"] = now
    write_packet(packet, metadata, "transition", {"from": "accepted", "to": "archived", "note": args.note})
    packet.rename(archive)
    current = parent / "current"
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

    route = sub.add_parser("route-task", help="Select the minimal built-in Skill composition for a classified task")
    route.add_argument("--task-type", choices=sorted(TASK_TYPES), required=True)
    route.add_argument("--risk", action="append", default=[])
    route.add_argument("--need", choices=("architecture", "dependency", "diagnosis", "verification", "review", "delivery"), action="append", default=[])
    route.add_argument("--ui-impact", choices=sorted(UI_IMPACTS), default="none")
    route.add_argument("--ambiguity", action="store_true")
    route.add_argument("--profile-operation", action="store_true")
    route.add_argument("--suite-maintenance", action="store_true")
    route.add_argument("--work-mode", choices=("auto", *sorted(WORK_MODES)), default="auto")
    route.set_defaults(func=route_task)

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
