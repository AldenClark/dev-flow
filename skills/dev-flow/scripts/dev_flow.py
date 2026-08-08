#!/usr/bin/env python3
"""Stdlib-only runtime for Dev Flow."""

from __future__ import annotations

import argparse
import datetime as dt
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


MIN_CODEX = (0, 147, 0)
SCHEMA_VERSION = "1.0"
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
}
STATUS_WORDS = {"PASSED", "FAILED", "FLAKY", "BLOCKED", "NOT RUN", "WAIVED"}
VERSION_RE = re.compile(r"(?:codex-cli\s+)?(\d+)\.(\d+)\.(\d+)(?:[-+][^\s]+)?")
FEATURE_RE = re.compile(r"^(multi_agent(?:_v2)?|hooks)\s+\S+\s+(true|false)\s*$", re.MULTILINE)


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


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
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command: list[str], cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=timeout)


def parse_version(text: str) -> tuple[int, int, int]:
    match = VERSION_RE.search(text.strip())
    if not match:
        raise ValueError(f"cannot parse Codex version from {text.strip()!r}")
    return tuple(int(part) for part in match.groups())


def codex_preflight(args: argparse.Namespace) -> int:
    errors: list[str] = []
    warnings: list[str] = []
    binary = args.codex or shutil.which("codex")
    version_text = args.version_output
    features_text = args.features_output_file.read_text(encoding="utf-8") if args.features_output_file else None

    try:
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
        errors.append(str(exc))

    actual: tuple[int, int, int] | None = None
    try:
        actual = parse_version(version_text or "")
        if actual < MIN_CODEX:
            errors.append(f"Codex {'.'.join(map(str, actual))} is below required 0.147.0")
    except ValueError as exc:
        errors.append(str(exc))

    features = dict(FEATURE_RE.findall(features_text or ""))
    for feature in ("multi_agent", "multi_agent_v2", "hooks"):
        if features.get(feature) != "true":
            errors.append(f"Codex feature {feature} is not enabled")

    config_path = args.config or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    effective: dict[str, Any] = {}
    if not args.skip_config:
        try:
            effective = tomllib.loads(config_path.read_text(encoding="utf-8"))
            feature_config = effective.get("features", {})
            if feature_config.get("multi_agent_v2") is not True:
                errors.append("config must set [features].multi_agent_v2 = true")
            if feature_config.get("multi_agent") is not True:
                errors.append("config must set [features].multi_agent = true")
            if feature_config.get("hooks") is not True:
                errors.append("config must set [features].hooks = true")
            limit = effective.get("agents", {}).get("max_concurrent_threads_per_session")
            if limit != 3:
                errors.append("config must set [agents].max_concurrent_threads_per_session = 3")
            if isinstance(feature_config.get("multi_agent_v2"), dict):
                errors.append("obsolete [features.multi_agent_v2] table is not supported")
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"cannot read Codex config {config_path}: {exc}")

    if not args.tool_surface_confirmed:
        warnings.append("The active root must confirm the collaboration tools before delegation")

    return emit(
        {
            "status": "ready" if not errors else "blocked",
            "codex_binary": binary,
            "actual_version": ".".join(map(str, actual)) if actual else None,
            "features": {name: features.get(name) for name in ("multi_agent", "multi_agent_v2", "hooks")},
            "config": str(config_path),
            "max_children": 3,
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

    packet = root / ".codex" / "dev-flow" / args.change_id
    if packet.exists() and not args.reuse:
        return emit({"status": "error", "errors": [f"packet already exists: {packet}"]}, 2)
    packet.mkdir(parents=True, exist_ok=True)
    for folder in ("briefs", "reports", "artifacts"):
        (packet / folder).mkdir(exist_ok=True)

    now = utc_now()
    profile = "micro" if args.task_type == "micro" else "full"
    metadata: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "skill_version": plugin_version(),
        "change_id": args.change_id,
        "state": "discovering",
        "documentation_profile": profile,
        "task_type": args.task_type,
        "created_at": now,
        "updated_at": now,
        "repository_roots": [str(root)],
        "base_git_state": git_state(root),
        "authority": args.authority,
        "compatibility_required": args.compatibility_required,
        "risk_modifiers": args.risk,
        "acceptance_ids": [],
        "scope_ids": [],
        "verification_ids": [],
        "dependency_changes": [],
        "approvals": {"design": None, "dependencies": [], "waivers": [], "delivery": []},
        "history": [{"from": None, "to": "discovering", "at": now, "note": "packet created"}],
    }
    write_json(packet / "packet.json", metadata)

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
    }
    templates = skill_root() / "templates"
    filenames = ("micro-trace.md",) if profile == "micro" else FULL_FILES
    for filename in filenames:
        source = templates / filename
        destination = packet / ("trace.md" if filename == "micro-trace.md" else filename)
        destination.write_text(replace_tokens(source.read_text(encoding="utf-8"), values), encoding="utf-8")

    brief = replace_tokens((templates / "task-brief.md").read_text(encoding="utf-8"), values)
    report = replace_tokens((templates / "agent-report.md").read_text(encoding="utf-8"), values)
    (packet / "briefs" / "README.template.md").write_text(brief, encoding="utf-8")
    (packet / "reports" / "README.template.md").write_text(report, encoding="utf-8")
    current = root / ".codex" / "dev-flow" / "current"
    current.write_text(args.change_id + "\n", encoding="utf-8")
    ensure_local_exclude(root)
    return emit({"status": "created", "packet": str(packet), "profile": profile, "next_state": "awaiting-approval"})


def load_packet(packet: Path) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    metadata_path = packet / "packet.json"
    if not metadata_path.is_file():
        return {}, ["missing required file: packet.json"]
    try:
        metadata = read_json(metadata_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"invalid packet.json: {exc}"]
    return metadata, errors


def transition_packet(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    old = metadata.get("state")
    new = args.state
    if old not in STATES or new not in TRANSITIONS.get(str(old), set()):
        return emit({"status": "invalid-transition", "from": old, "to": new}, 2)
    if new == "approved" and not args.approved_by:
        return emit({"status": "invalid", "errors": ["--approved-by is required for approved state"]}, 2)
    if new == "accepted":
        report, code = validate_packet_data(packet, state_override="accepted")
        if code:
            report["status"] = "acceptance-blocked"
            return emit(report, 2)
    now = utc_now()
    metadata["state"] = new
    metadata["updated_at"] = now
    metadata.setdefault("history", []).append({"from": old, "to": new, "at": now, "note": args.note})
    if new == "approved":
        metadata.setdefault("approvals", {})["design"] = {
            "by": args.approved_by,
            "at": now,
            "note": args.note,
        }
    write_json(packet / "packet.json", metadata)
    return emit({"status": "transitioned", "packet": str(packet), "from": old, "to": new})


def record_approval(args: argparse.Namespace) -> int:
    packet = args.packet.resolve()
    metadata, errors = load_packet(packet)
    if errors:
        return emit({"status": "invalid", "errors": errors}, 2)
    record = {"id": args.id, "by": args.by, "at": utc_now(), "note": args.note}
    approvals = metadata.setdefault("approvals", {})
    approvals.setdefault(args.kind, []).append(record)
    if args.kind == "dependencies" and args.id not in metadata.setdefault("dependency_changes", []):
        metadata["dependency_changes"].append(args.id)
    metadata["updated_at"] = record["at"]
    write_json(packet / "packet.json", metadata)
    return emit({"status": "recorded", "kind": args.kind, "record": record})


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
    if metadata.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"packet.json: unsupported schema_version {metadata.get('schema_version')!r}")
    if metadata.get("state") not in STATES:
        errors.append(f"packet.json: invalid state {metadata.get('state')!r}")
    if metadata.get("task_type") not in TASK_TYPES:
        errors.append(f"packet.json: invalid task_type {metadata.get('task_type')!r}")
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", str(metadata.get("change_id", ""))):
        errors.append("packet.json: invalid change_id")

    profile = metadata.get("documentation_profile")
    texts: dict[str, str] = {}
    if profile == "micro":
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
    elif profile == "full":
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
    else:
        errors.append(f"packet.json: invalid documentation_profile {profile!r}")

    all_text = "\n".join(texts.values())
    required_dirs = ("briefs", "reports", "artifacts")
    for dirname in required_dirs:
        if not (packet / dirname).is_dir():
            errors.append(f"missing required directory: {dirname}/")

    declared = {
        "acceptance": set(metadata.get("acceptance_ids", [])),
        "scope": set(metadata.get("scope_ids", [])),
        "verification": set(metadata.get("verification_ids", [])),
    }
    observed = {kind: ids(all_text, kind) for kind in declared}
    for kind in declared:
        if declared[kind] != observed[kind]:
            errors.append(
                f"packet.json {kind}_ids must equal documented IDs; "
                f"declared={sorted(declared[kind])}, documented={sorted(observed[kind])}"
            )

    if profile == "full":
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

    approvals = metadata.get("approvals", {})
    dependency_ids = set(metadata.get("dependency_changes", []))
    approved_dependency_ids = {item.get("id") for item in approvals.get("dependencies", []) if isinstance(item, dict)}
    if dependency_ids - approved_dependency_ids:
        errors.append(f"unapproved dependency changes: {sorted(dependency_ids - approved_dependency_ids)}")

    state = state_override or metadata.get("state")
    if state in {"approved", "implementing", "verifying", "accepted", "archived"} and not approvals.get("design"):
        errors.append(f"state {state} requires a design approval record")
    if state in {"accepted", "archived"}:
        if not declared["acceptance"] or not declared["scope"] or not declared["verification"]:
            errors.append("accepted packet requires non-empty acceptance, scope, and verification ID sets")
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
        if profile == "full":
            for audit in ("blue-audit.md", "red-audit.md"):
                if re.search(r"\b(?:open|unresolved|pending)\b", texts.get(audit, ""), re.IGNORECASE):
                    warnings.append(f"{audit}: verify that no finding remains open")

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
    registry_path = plugin_root() / "skills" / "engineering-preferences" / "references" / "preference-registry.json"
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

    for path in sorted((root / "skills").glob("*/")):
        errors.extend(validate_skill(path))

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
        root / "skills" / "engineering-preferences" / "references" / "preference-registry.json",
        root / "governance" / "industry-practices.json",
        root / "evals" / "structural-coverage.json",
    ):
        if not required.is_file():
            errors.append(f"missing required governance file: {required.relative_to(root)}")

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
    write_json(packet / "packet.json", metadata)
    packet.rename(archive)
    current = parent / "current"
    if current.exists() and current.read_text(encoding="utf-8").strip() == packet.name:
        current.unlink()
    return emit({"status": "archived", "packet": str(archive)})


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
    preflight.set_defaults(func=codex_preflight)

    init = sub.add_parser("init-packet")
    init.add_argument("--root", type=Path, required=True)
    init.add_argument("--change-id", required=True)
    init.add_argument("--task-type", required=True)
    init.add_argument("--objective", required=True)
    init.add_argument("--authority", default="local edits and tests only")
    init.add_argument("--profile", action="append", default=[])
    init.add_argument("--risk", action="append", default=[])
    init.add_argument("--compatibility-required", action="store_true")
    init.add_argument("--reuse", action="store_true")
    init.set_defaults(func=init_packet)

    validate = sub.add_parser("validate-packet")
    validate.add_argument("packet", type=Path)
    validate.set_defaults(func=validate_packet)

    transition = sub.add_parser("transition")
    transition.add_argument("packet", type=Path)
    transition.add_argument("state", choices=sorted(STATES))
    transition.add_argument("--note", required=True)
    transition.add_argument("--approved-by")
    transition.set_defaults(func=transition_packet)

    approval = sub.add_parser("record-approval")
    approval.add_argument("packet", type=Path)
    approval.add_argument("kind", choices=("dependencies", "waivers", "delivery"))
    approval.add_argument("--id", required=True)
    approval.add_argument("--by", required=True)
    approval.add_argument("--note", required=True)
    approval.set_defaults(func=record_approval)

    audit = sub.add_parser("audit-preferences")
    audit.add_argument("--root", type=Path, required=True)
    audit.add_argument("--packet", type=Path)
    audit.add_argument("--base")
    audit.set_defaults(func=audit_preferences)

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
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
