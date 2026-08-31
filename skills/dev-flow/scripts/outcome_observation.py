#!/usr/bin/env python3
"""Private, local, opt-in Dev Flow outcome observations."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import stat
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # Windows uses msvcrt byte-range locking below.
    fcntl = None  # type: ignore[assignment]

try:
    import msvcrt
except ImportError:  # POSIX uses flock above.
    msvcrt = None  # type: ignore[assignment]


SCHEMA = "dev-flow.outcome.v1"
DEFAULT_RELATIVE_PATH = Path(".codex/dev-flow/outcomes-v1.jsonl")
MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_LINE_BYTES = 4096
MAX_RECORDS = 10_000
CONDITIONS = frozenset({"baseline", "dev-flow"})
TASK_SHAPES = frozenset({"micro", "bounded", "managed", "cross-boundary"})
OUTCOMES = frozenset({"completed", "partial", "blocked", "abandoned"})
VERIFICATION_STATES = frozenset({"passed", "failed", "not-run", "blocked", "not-applicable"})
TRISTATES = frozenset({"yes", "no", "unknown"})
COUNTER_FIELDS = (
    "corrections",
    "rework_events",
    "reverted_edits",
    "escaped_defects",
    "false_blocks",
    "tool_failures",
    "route_calls",
)
OPTIONAL_FIELDS = ("elapsed_minutes", "token_count", "cost_micros")
RECORD_KEYS = {
    "schema",
    "day",
    "condition",
    "task_shape",
    "outcome",
    "verification",
    "first_valid_patch",
    "counters",
    "resources",
}


class OutcomeError(ValueError):
    """Raised when an outcome record or store violates the privacy contract."""


def default_path(cwd: Path | None = None) -> Path:
    return (cwd or Path.cwd()) / DEFAULT_RELATIVE_PATH


def _bounded_nonnegative(value: Any, label: str, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= maximum:
        raise OutcomeError(f"{label} must be an integer from 0 to {maximum}")
    return value


def build_record(args: argparse.Namespace, *, today: dt.date | None = None) -> dict[str, Any]:
    counters = {
        name: _bounded_nonnegative(getattr(args, name), name, 1_000_000)
        for name in COUNTER_FIELDS
    }
    resources = {
        name: _bounded_nonnegative(getattr(args, name), name, 10**12)
        for name in OPTIONAL_FIELDS
        if getattr(args, name) is not None
    }
    record = {
        "schema": SCHEMA,
        "day": (today or dt.datetime.now(dt.timezone.utc).date()).isoformat(),
        "condition": args.condition,
        "task_shape": args.task_shape,
        "outcome": args.outcome,
        "verification": args.verification,
        "first_valid_patch": args.first_valid_patch,
        "counters": counters,
        "resources": resources,
    }
    validate_record(record)
    return record


def validate_record(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != RECORD_KEYS:
        raise OutcomeError("outcome record has unknown or missing fields")
    if value.get("schema") != SCHEMA:
        raise OutcomeError("unsupported outcome schema")
    day = value.get("day")
    try:
        parsed_day = dt.date.fromisoformat(day) if isinstance(day, str) else None
    except ValueError as exc:
        raise OutcomeError("day must be an ISO date bucket") from exc
    if parsed_day is None or parsed_day.isoformat() != day:
        raise OutcomeError("day must be an ISO date bucket")
    vocabularies = {
        "condition": CONDITIONS,
        "task_shape": TASK_SHAPES,
        "outcome": OUTCOMES,
        "verification": VERIFICATION_STATES,
        "first_valid_patch": TRISTATES,
    }
    for field, allowed in vocabularies.items():
        if value.get(field) not in allowed:
            raise OutcomeError(f"{field} is outside the bounded vocabulary")
    counters = value.get("counters")
    if not isinstance(counters, dict) or set(counters) != set(COUNTER_FIELDS):
        raise OutcomeError("counters must use the exact bounded counter inventory")
    for field in COUNTER_FIELDS:
        _bounded_nonnegative(counters[field], field, 1_000_000)
    resources = value.get("resources")
    if not isinstance(resources, dict) or not set(resources).issubset(OPTIONAL_FIELDS):
        raise OutcomeError("resources contain an unknown field")
    for field, number in resources.items():
        _bounded_nonnegative(number, field, 10**12)
    serialized = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(serialized) > MAX_LINE_BYTES:
        raise OutcomeError("outcome record exceeds the bounded line size")
    return value


def _contained_relative(path: Path, containment_root: Path) -> tuple[Path, Path]:
    try:
        root = containment_root.resolve(strict=True)
        absolute = Path(os.path.abspath(os.fspath(path)))
        relative = absolute.relative_to(root)
    except (OSError, ValueError) as exc:
        raise OutcomeError("outcome store escapes its repository root") from exc
    if not relative.parts or ".." in relative.parts:
        raise OutcomeError("outcome store escapes its repository root")
    return root, relative


def _reject_contained_symlinks(path: Path, containment_root: Path) -> tuple[Path, Path]:
    root, relative = _contained_relative(path, containment_root)
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            break
        except OSError as exc:
            raise OutcomeError("outcome store path is unavailable") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise OutcomeError("outcome store path must not contain repository symlinks")
    return root, relative


def _prepare_parent(path: Path, *, containment_root: Path | None = None) -> None:
    parent = path.parent
    try:
        if containment_root is None:
            parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            root, relative = _reject_contained_symlinks(path, containment_root)
            current = root
            for part in relative.parent.parts:
                current = current / part
                try:
                    metadata = current.lstat()
                except FileNotFoundError:
                    current.mkdir(mode=0o700)
                    metadata = current.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                    raise OutcomeError("outcome parent must be a real contained directory")
            _reject_contained_symlinks(path, containment_root)
        if parent.is_symlink() or not parent.is_dir():
            raise OutcomeError("outcome parent must be a real directory")
    except OSError as exc:
        raise OutcomeError("outcome parent is unavailable") from exc


def _open_append(path: Path, *, containment_root: Path | None = None) -> int:
    _prepare_parent(path, containment_root=containment_root)
    if path.is_symlink():
        raise OutcomeError("outcome store must not be a symlink")
    flags = os.O_RDWR | os.O_CREAT | os.O_APPEND
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        raise OutcomeError("outcome store could not be opened safely") from exc
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise OutcomeError("outcome store must be a regular file")
        if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
            raise OutcomeError("outcome store permissions must be 0600")
        if info.st_size > MAX_FILE_BYTES:
            raise OutcomeError("outcome store exceeds the bounded file size")
    except Exception:
        os.close(descriptor)
        raise
    return descriptor


def _validate_existing_store(descriptor: int) -> None:
    try:
        os.lseek(descriptor, 0, os.SEEK_SET)
        chunks: list[bytes] = []
        observed = 0
        while True:
            chunk = os.read(descriptor, min(128 * 1024, MAX_FILE_BYTES + 1 - observed))
            if not chunk:
                break
            chunks.append(chunk)
            observed += len(chunk)
            if observed > MAX_FILE_BYTES:
                raise OutcomeError("outcome store exceeds the bounded file size")
        raw = b"".join(chunks)
    except OSError as exc:
        raise OutcomeError("outcome store could not be inspected before append") from exc
    if raw and not raw.endswith(b"\n"):
        raise OutcomeError("outcome store ends with an incomplete record")
    lines = raw.splitlines(keepends=True)
    if len(lines) >= MAX_RECORDS:
        raise OutcomeError("outcome store reached the bounded record count")
    for line_number, line in enumerate(lines, 1):
        if len(line) > MAX_LINE_BYTES:
            raise OutcomeError(f"existing line {line_number} exceeds the bounded size")
        try:
            validate_record(json.loads(line.decode("utf-8")))
        except (UnicodeDecodeError, json.JSONDecodeError, OutcomeError) as exc:
            raise OutcomeError(f"existing line {line_number} is invalid") from exc


def _lock_store(descriptor: int) -> str:
    if fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        return "flock"
    if msvcrt is not None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
        return "msvcrt"
    raise OutcomeError("this platform has no supported local outcome append lock")


def _unlock_store(descriptor: int, lock_kind: str | None) -> None:
    if lock_kind == "flock" and fcntl is not None:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
    elif lock_kind == "msvcrt" and msvcrt is not None:
        os.lseek(descriptor, 0, os.SEEK_SET)
        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)


def append_record(
    path: Path,
    record: dict[str, Any],
    *,
    containment_root: Path | None = None,
) -> None:
    validate_record(record)
    line = json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(line) > MAX_LINE_BYTES:
        raise OutcomeError("outcome record exceeds the bounded line size")
    descriptor = _open_append(path, containment_root=containment_root)
    lock_kind: str | None = None
    try:
        lock_kind = _lock_store(descriptor)
        _validate_existing_store(descriptor)
        if os.fstat(descriptor).st_size + len(line) > MAX_FILE_BYTES:
            raise OutcomeError("outcome store would exceed the bounded file size")
        written = os.write(descriptor, line)
        if written != len(line):
            raise OutcomeError("outcome record append was incomplete")
        os.fsync(descriptor)
    except OSError as exc:
        raise OutcomeError("outcome record could not be appended") from exc
    finally:
        if lock_kind is not None:
            try:
                _unlock_store(descriptor, lock_kind)
            except OSError:
                pass
        os.close(descriptor)


def read_records(
    path: Path,
    *,
    missing_ok: bool = False,
    containment_root: Path | None = None,
) -> list[dict[str, Any]]:
    if containment_root is not None:
        _reject_contained_symlinks(path, containment_root)
    try:
        info = path.lstat()
    except FileNotFoundError:
        if missing_ok:
            return []
        raise OutcomeError("outcome store does not exist")
    except OSError as exc:
        raise OutcomeError("outcome store is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise OutcomeError("outcome store must be a regular non-symlink file")
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
        raise OutcomeError("outcome store permissions must be 0600")
    if info.st_size > MAX_FILE_BYTES:
        raise OutcomeError("outcome store exceeds the bounded file size")
    records: list[dict[str, Any]] = []
    try:
        with path.open("rb") as stream:
            for line_number, raw in enumerate(stream, 1):
                if line_number > MAX_RECORDS:
                    raise OutcomeError("outcome store exceeds the bounded record count")
                if len(raw) > MAX_LINE_BYTES:
                    raise OutcomeError(f"line {line_number} exceeds the bounded size")
                try:
                    value = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    raise OutcomeError(f"line {line_number} is not valid UTF-8 JSON") from exc
                try:
                    records.append(validate_record(value))
                except OutcomeError as exc:
                    raise OutcomeError(f"line {line_number}: {exc}") from exc
    except OSError as exc:
        raise OutcomeError("outcome store could not be read") from exc
    return records


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    distributions = {
        field: dict(sorted(collections.Counter(record[field] for record in records).items()))
        for field in ("condition", "task_shape", "outcome", "verification", "first_valid_patch")
    }
    counter_totals = {
        field: sum(record["counters"][field] for record in records)
        for field in COUNTER_FIELDS
    }
    resource_totals = {
        field: sum(record["resources"].get(field, 0) for record in records)
        for field in OPTIONAL_FIELDS
    }
    return {
        "schema": "dev-flow.outcome-summary.v1",
        "records": len(records),
        "distributions": distributions,
        "counter_totals": counter_totals,
        "resource_totals": resource_totals,
        "claim_limit": "local opt-in descriptive counts only; no productivity, causal-effect, user, agent, or task ranking claim",
    }


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("outcomes", help="Record or summarize private local enum/count outcomes")
    parser.add_argument("--store", type=Path, help="override the ignored local JSONL store")
    actions = parser.add_subparsers(dest="outcome_action", required=True)
    record = actions.add_parser("record", help="append one privacy-minimized observation")
    record.add_argument("--condition", choices=sorted(CONDITIONS), required=True)
    record.add_argument("--task-shape", choices=sorted(TASK_SHAPES), required=True)
    record.add_argument("--outcome", choices=sorted(OUTCOMES), required=True)
    record.add_argument("--verification", choices=sorted(VERIFICATION_STATES), required=True)
    record.add_argument("--first-valid-patch", choices=sorted(TRISTATES), default="unknown")
    for field in COUNTER_FIELDS:
        record.add_argument("--" + field.replace("_", "-"), type=int, default=0)
    for field in OPTIONAL_FIELDS:
        record.add_argument("--" + field.replace("_", "-"), type=int)
    actions.add_parser("summary", help="summarize distributions and totals without scores")
    actions.add_parser("validate", help="validate the bounded local store")
    parser.set_defaults(func=command)
    return parser


def command(args: argparse.Namespace) -> int:
    default_root = Path.cwd().resolve() if args.store is None else None
    path = Path(os.path.abspath(os.fspath((args.store or default_path()).expanduser())))
    try:
        if args.outcome_action == "record":
            append_record(path, build_record(args), containment_root=default_root)
            payload = {
                "status": "recorded",
                "schema": SCHEMA,
                "stored_content": "bounded-enums-counts-only",
                "claim_limit": "one local append; no outcome or productivity claim",
            }
        else:
            records = read_records(
                path,
                missing_ok=args.outcome_action == "summary",
                containment_root=default_root,
            )
            payload = summarize(records)
            payload["status"] = "valid" if args.outcome_action == "validate" else "summarized"
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    except OutcomeError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
        return 2
