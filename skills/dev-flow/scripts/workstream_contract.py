"""Read-only structural consistency checks for opted-in managed workstreams."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any


MARKER = "<!-- dev-flow-workstream-contract: v1 -->"
MAX_DOCUMENT_BYTES = 1024 * 1024
SLICE_HEADER = ("Slice", "Outcome", "Write prefixes", "Protected paths", "Evidence", "Status", "Decision")
GATE_HEADER = ("ID", "Condition", "Gate", "Status", "Closure/decision")
CONVERGENCE_HEADER = ("Mechanism", "Non-progress repairs", "Primary progress", "Disposition", "Authority/decision")
SLICE_STATUSES = {"pending", "ready", "in-progress", "blocked", "complete", "deferred"}
GATE_STATUSES = {"open", "passed", "failed", "flaky", "blocked", "not-run", "waived"}
WORKSTREAM_STATES = {"planning", "active", "blocked", "implementation-complete", "release-qualified", "closed"}
TERMINAL_STATES = {"implementation-complete", "release-qualified", "closed"}
CONVERGENCE_DISPOSITIONS = {
    "continue-authorized",
    "simplify",
    "replace",
    "narrower-fallback",
    "defer",
    "blocked",
    "not-run",
}


class WorkstreamContractError(ValueError):
    pass


def _read(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        raise WorkstreamContractError(f"required workstream document is not a regular file: {path.name}")
    if path.stat().st_size > MAX_DOCUMENT_BYTES:
        raise WorkstreamContractError(f"workstream document exceeds bounded size: {path.name}")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise WorkstreamContractError(f"cannot read {path.name} as UTF-8: {exc}") from exc
    if "\r" in text:
        raise WorkstreamContractError(f"{path.name} must use normalized LF text")
    return text


def _rows(text: str, header: tuple[str, ...], source: str) -> list[dict[str, Any]]:
    lines = text.splitlines()
    expected = "| " + " | ".join(header) + " |"
    locations = [index for index, line in enumerate(lines) if line == expected]
    if len(locations) != 1:
        raise WorkstreamContractError(f"{source} must contain exactly one {header[0]} table")
    index = locations[0]
    if index + 1 >= len(lines) or not re.fullmatch(r"\|(?:---:?|:---:?)(?:\|(?:---:?|:---:?)){%d}\|" % (len(header) - 1), lines[index + 1].replace(" ", "")):
        raise WorkstreamContractError(f"{source}:{index + 2}: invalid table delimiter")
    result: list[dict[str, Any]] = []
    for line_number, line in enumerate(lines[index + 2 :], index + 3):
        if not line.startswith("|"):
            break
        cells = [cell.strip() for cell in line[1:-1].split("|")] if line.endswith("|") else []
        if len(cells) != len(header) or any(not cell for cell in cells):
            raise WorkstreamContractError(f"{source}:{line_number}: invalid one-line table row")
        result.append({**dict(zip(header, cells, strict=True)), "_line": line_number})
    if not result:
        raise WorkstreamContractError(f"{source}: {header[0]} table has no rows")
    return result


def _optional_rows(text: str, header: tuple[str, ...], source: str) -> list[dict[str, Any]]:
    expected = "| " + " | ".join(header) + " |"
    if expected not in text:
        return []
    return _rows(text, header, source)


def _field(text: str, label: str) -> str:
    values = re.findall(rf"^- {re.escape(label)}:\s*(.+)$", text, re.MULTILINE)
    if len(values) != 1:
        raise WorkstreamContractError(f"progress.md must contain exactly one '- {label}:' field")
    return values[0].strip()


def _prefixes(cell: str, line: int, findings: list[dict[str, Any]]) -> list[str]:
    if cell == "-":
        return []
    values = re.findall(r"`([^`]+)`", cell)
    if not values or re.sub(r"`[^`]+`|[\s,]", "", cell):
        findings.append({"code": "invalid-prefix-cell", "line": line, "message": "prefix cells contain only comma-separated code literals or '-'"})
        return []
    safe: list[str] = []
    for value in values:
        candidate = PurePosixPath(value)
        unsafe = (
            candidate.is_absolute()
            or ".." in candidate.parts
            or value in {".", "./", "*", "**"}
            or any(character in value for character in "$;&|<>:\\")
            or any(ord(character) < 32 for character in value)
            or "*" in value
            or any(part.casefold() == ".git" for part in candidate.parts)
        )
        normalized = candidate.as_posix()
        if unsafe or not normalized:
            findings.append({"code": "unsafe-prefix", "line": line, "message": f"unsafe repository prefix: {value}"})
        else:
            safe.append(normalized.rstrip("/") + ("/" if value.endswith("/") else ""))
    return safe


def _matches(path: str, prefix: str) -> bool:
    base = prefix.rstrip("/")
    return path == base or path.startswith(base + "/")


def _git_paths(root: Path) -> list[str] | None:
    completed = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    records = completed.stdout.split(b"\0")
    paths: list[str] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        text = record.decode("utf-8", "surrogateescape")
        if len(text) < 4:
            continue
        status, path = text[:2], text[3:]
        if status[0] in {"R", "C"} or status[1] in {"R", "C"}:
            if index < len(records) and records[index]:
                paths.append(records[index].decode("utf-8", "surrogateescape"))
                index += 1
        paths.append(path)
    return sorted(set(paths))


def check(root: Path, target: Path, *, check_worktree: bool = False, strict: bool = False) -> tuple[dict[str, Any], int]:
    findings: list[dict[str, Any]] = []
    implementation = _read(target / "implementation.md")
    progress = _read(target / "progress.md")
    marker_counts = (implementation.count(MARKER), progress.count(MARKER))
    if marker_counts != (1, 1):
        if strict:
            findings.append({"code": "invalid-contract-marker", "line": 1, "message": "both documents require exactly one v1 marker"})
        else:
            if marker_counts == (0, 0):
                return ({"status": "not-applicable", "claim_limit": "structural-consistency-only", "findings": []}, 0)
            findings.append({"code": "invalid-contract-marker", "line": 1, "message": "both documents require exactly one v1 marker"})
    try:
        slices = _rows(implementation, SLICE_HEADER, "implementation.md")
        gates = _rows(progress, GATE_HEADER, "progress.md")
        checkpoints = _optional_rows(progress, CONVERGENCE_HEADER, "progress.md")
        state = _field(progress, "State").lower()
        current = _field(progress, "Current slice")
        _field(progress, "Terminal condition")
    except WorkstreamContractError as exc:
        return ({"status": "invalid", "claim_limit": "structural-consistency-only", "findings": [{"code": "contract-parse", "line": 1, "message": str(exc)}]}, 2)

    slice_ids = [row["Slice"] for row in slices]
    gate_ids = [row["ID"] for row in gates]
    for label, values in (("slice", slice_ids), ("hard-condition", gate_ids)):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        for value in duplicates:
            findings.append({"code": "duplicate-id", "line": 1, "message": f"duplicate {label} id: {value}"})
    if any(not re.fullmatch(r"S[0-9]+", value) for value in slice_ids):
        findings.append({"code": "invalid-slice-id", "line": 1, "message": "slice ids must match S<number>"})
    if any(not re.fullmatch(r"HC[0-9]+", value) for value in gate_ids):
        findings.append({"code": "invalid-gate-id", "line": 1, "message": "hard-condition ids must match HC<number>"})
    for row in slices:
        status = row["Status"].lower()
        if status not in SLICE_STATUSES:
            findings.append({"code": "invalid-slice-status", "line": row["_line"], "message": status})
        if status == "deferred" and row["Decision"] == "-":
            findings.append({"code": "missing-defer-decision", "line": row["_line"], "message": row["Slice"]})
        row["_write"] = _prefixes(row["Write prefixes"], row["_line"], findings)
        row["_protected"] = _prefixes(row["Protected paths"], row["_line"], findings)
    for row in gates:
        gate = row["Gate"].lower()
        status = row["Status"].lower()
        if gate not in {"implementation", "qualification"}:
            findings.append({"code": "invalid-gate-class", "line": row["_line"], "message": gate})
        if status not in GATE_STATUSES:
            findings.append({"code": "invalid-gate-status", "line": row["_line"], "message": status})
        if status == "waived" and row["Closure/decision"] == "-":
            findings.append({"code": "missing-waiver-decision", "line": row["_line"], "message": row["ID"]})
    in_progress = [row["Slice"] for row in slices if row["Status"].lower() == "in-progress"]
    if len(in_progress) > 1:
        findings.append({"code": "multiple-in-progress", "line": 1, "message": ", ".join(in_progress)})
    by_id = {row["Slice"]: row for row in slices}
    if state not in WORKSTREAM_STATES:
        findings.append({"code": "invalid-workstream-state", "line": 1, "message": state})
    elif state not in TERMINAL_STATES:
        if current not in by_id:
            findings.append({"code": "stale-current-slice", "line": 1, "message": current})
        elif in_progress and current != in_progress[0]:
            findings.append({"code": "stale-current-slice", "line": 1, "message": current})
        elif not in_progress and by_id[current]["Status"].lower() not in {"ready", "blocked"}:
            findings.append({"code": "stale-current-slice", "line": 1, "message": current})
    if state in TERMINAL_STATES and any(row["Status"].lower() not in {"complete", "deferred"} for row in slices):
        findings.append({"code": "incomplete-terminal-slice", "line": 1, "message": state})
    if state in TERMINAL_STATES and any(row["Gate"].lower() == "implementation" and row["Status"].lower() not in {"passed", "waived"} for row in gates):
        findings.append({"code": "implementation-gate-open", "line": 1, "message": state})
    if state in {"release-qualified", "closed"} and any(row["Status"].lower() not in {"passed", "waived"} for row in gates):
        findings.append({"code": "qualification-gate-open", "line": 1, "message": state})
    for row in checkpoints:
        try:
            repairs = int(row["Non-progress repairs"])
        except ValueError:
            findings.append({"code": "invalid-convergence-count", "line": row["_line"], "message": row["Non-progress repairs"]})
            continue
        progress_value = row["Primary progress"].lower()
        disposition = row["Disposition"].lower()
        if repairs < 0:
            findings.append({"code": "invalid-convergence-count", "line": row["_line"], "message": row["Non-progress repairs"]})
        if progress_value not in {"advanced", "unchanged"}:
            findings.append({"code": "invalid-primary-progress", "line": row["_line"], "message": row["Primary progress"]})
        if disposition != "pending" and disposition not in CONVERGENCE_DISPOSITIONS:
            findings.append({"code": "invalid-convergence-disposition", "line": row["_line"], "message": row["Disposition"]})
        if repairs >= 2 and progress_value == "unchanged" and disposition == "pending":
            findings.append({"code": "convergence-decision-required", "line": row["_line"], "message": row["Mechanism"]})
        if disposition in {"continue-authorized", "defer"} and row["Authority/decision"] == "-":
            findings.append({"code": "missing-convergence-decision", "line": row["_line"], "message": row["Mechanism"]})

    worktree: dict[str, Any] | None = None
    if check_worktree:
        changed = _git_paths(root)
        if changed is None:
            payload = {
                "status": "not-applicable",
                "claim_limit": "structural-consistency-only",
                "workstream_state": state,
                "current_slice": current,
                "findings": findings,
                "worktree": {
                    "status": "not-applicable",
                    "reason": "root-is-not-a-git-worktree",
                    "authorship_inferred": False,
                },
            }
            return payload, 0 if not findings else 2
        accumulated: list[str] = []
        protected: list[str] = []
        for row in slices:
            if row["Status"].lower() == "complete" or row["Slice"] == current:
                accumulated.extend(row["_write"])
            if row["Slice"] == current:
                protected.extend(row["_protected"])
        ambiguous = [path for path in changed if not any(_matches(path, prefix) for prefix in accumulated)]
        protected_changed = [path for path in changed if any(_matches(path, prefix) for prefix in protected)]
        for path in ambiguous:
            findings.append({"code": "ambiguous-worktree-path", "line": 1, "message": path})
        for path in protected_changed:
            findings.append({"code": "protected-path-changed", "line": 1, "message": path})
        worktree = {"changed_paths": changed, "accumulated_write_prefixes": sorted(set(accumulated)), "ambiguous_paths": ambiguous, "protected_changed_paths": protected_changed, "authorship_inferred": False}

    payload: dict[str, Any] = {
        "status": "valid" if not findings else "invalid",
        "claim_limit": "structural-consistency-only",
        "workstream_state": state,
        "current_slice": current,
        "findings": findings,
    }
    if worktree is not None:
        payload["worktree"] = worktree
    return payload, 0 if not findings else 2
