#!/usr/bin/env python3
"""Short-lived, local, one-shot approvals for personal DLP confirmations.

Approval records contain only bounded metadata and a keyed scope fingerprint.
They never contain the inspected prompt, tool input, or credential value.
"""

from __future__ import annotations

import argparse
import hashlib
import hmac
import itertools
import json
import os
import re
import secrets
import stat
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STATE_DIR_ENV = "DEV_FLOW_DLP_STATE_DIR"
MODE_ENV = "DEV_FLOW_DLP_MODE"
DEFAULT_MODE = "personal"
VALID_MODES = frozenset({"personal", "strict"})
APPROVAL_TTL_SECONDS = 300
MAX_PENDING_REQUESTS = 128
MAX_STATE_FILE_BYTES = 16_384
_REQUEST_ID_RE = re.compile(r"^[0-9a-f]{24}$")
_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{24,96}$")
_PROMPT_MARKER_RE = re.compile(
    r"\A\[\[DEV_FLOW_DLP_CONFIRM:([0-9a-f]{24}):([A-Za-z0-9_-]{24,96})\]\]\s*"
)


class ApprovalError(ValueError):
    """Raised when an approval is absent, stale, altered, or already consumed."""


class StateUnavailable(RuntimeError):
    """Raised when local approval state cannot be protected or inspected safely."""


@dataclass(frozen=True)
class ApprovalRequest:
    request_id: str
    token: str
    expires_at: int

    @property
    def prompt_marker(self) -> str:
        return f"[[DEV_FLOW_DLP_CONFIRM:{self.request_id}:{self.token}]]"


def _state_root() -> Path:
    override = os.environ.get(STATE_DIR_ENV)
    if override:
        return Path(override).expanduser().resolve()
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Codex" / "dev-flow" / "dlp"
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "Codex" / "dev-flow" / "dlp"
    base = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return base / "codex" / "dev-flow" / "dlp"


def _ensure_private_dir(path: Path) -> None:
    try:
        try:
            path.mkdir(mode=0o700, parents=True, exist_ok=False)
        except FileExistsError:
            pass
        info = path.lstat()
    except OSError as exc:
        raise StateUnavailable("local DLP state directory is unavailable") from exc
    if path.is_symlink() or not stat.S_ISDIR(info.st_mode):
        raise StateUnavailable("local DLP state directory is not a regular directory")
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
        raise StateUnavailable("local DLP state directory permissions are too broad")


def _paths() -> tuple[Path, Path, Path]:
    root = _state_root()
    pending = root / "pending"
    used = root / "used"
    for path in (root, pending, used):
        _ensure_private_dir(path)
    return root, pending, used


def _exclusive_write(path: Path, data: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(path, flags, 0o600)
    except FileExistsError:
        raise
    except OSError as exc:
        raise StateUnavailable("local DLP state could not be created") from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
        raise StateUnavailable("local DLP state could not be persisted") from exc


def _atomic_replace(path: Path, data: bytes) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    _exclusive_write(temporary, data)
    try:
        os.replace(temporary, path)
        if os.name != "nt":
            path.chmod(0o600)
    except OSError as exc:
        temporary.unlink(missing_ok=True)
        raise StateUnavailable("local DLP state could not be updated") from exc


def _private_regular_file(path: Path) -> None:
    try:
        info = path.lstat()
    except OSError as exc:
        raise StateUnavailable("local DLP state file is unavailable") from exc
    if path.is_symlink() or not stat.S_ISREG(info.st_mode):
        raise StateUnavailable("local DLP state file is not a regular file")
    if os.name != "nt" and stat.S_IMODE(info.st_mode) & 0o077:
        raise StateUnavailable("local DLP state file permissions are too broad")


def _master_key() -> bytes:
    root, _, _ = _paths()
    path = root / ("approval" + chr(46) + "key")
    try:
        _exclusive_write(path, secrets.token_bytes(32))
    except FileExistsError:
        pass
    _private_regular_file(path)
    try:
        value = path.read_bytes()
    except OSError as exc:
        raise StateUnavailable("local DLP approval key is unreadable") from exc
    if len(value) != 32:
        raise StateUnavailable("local DLP approval key is invalid")
    return value


def canonical_scope(event_name: str, cwd: str, payload: Any, *, tool_name: str = "") -> bytes:
    """Return the exact bounded approval scope used for local keyed matching."""
    if not isinstance(cwd, str) or not cwd:
        raise ApprovalError("approval scope requires a working directory")
    try:
        serialized = json.dumps(
            {
                "event": event_name,
                "cwd": str(Path(cwd).resolve()),
                "tool_name": tool_name,
                "payload": payload,
            },
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, OSError) as exc:
        raise ApprovalError("approval scope is not bounded JSON") from exc
    if len(serialized) > 4_194_304:
        raise ApprovalError("approval scope exceeds the local limit")
    return serialized


def parse_prompt_marker(prompt: str) -> tuple[str | None, str | None, str]:
    match = _PROMPT_MARKER_RE.match(prompt)
    if match is None:
        return None, None, prompt
    return match.group(1), match.group(2), prompt[match.end():]


def _scope_mac(scope: bytes) -> str:
    return hmac.new(_master_key(), scope, hashlib.sha256).hexdigest()


def _session_mac(session_id: str) -> str:
    if (
        not isinstance(session_id, str)
        or not session_id
        or len(session_id) > 256
        or any(ord(character) < 32 for character in session_id)
    ):
        raise ApprovalError("approval requires a bounded host session id")
    return _scope_mac(b"host-session\0" + session_id.encode("utf-8"))


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _validate_request_values(request_id: str, token: str | None = None) -> None:
    if _REQUEST_ID_RE.fullmatch(request_id) is None:
        raise ApprovalError("approval request id is invalid")
    if token is not None and _TOKEN_RE.fullmatch(token) is None:
        raise ApprovalError("approval token is invalid")


def _read_record(path: Path) -> dict[str, Any]:
    _private_regular_file(path)
    try:
        raw = path.read_bytes()
        if len(raw) > MAX_STATE_FILE_BYTES:
            raise ApprovalError("approval record exceeds the local limit")
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ApprovalError("approval record is unreadable") from exc
    if not isinstance(value, dict):
        raise ApprovalError("approval record is invalid")
    return value


def _bounded_entries(directory: Path, limit: int) -> list[Path]:
    try:
        entries = list(itertools.islice(directory.iterdir(), limit + 1))
    except OSError as exc:
        raise StateUnavailable("local DLP state could not be inspected") from exc
    if len(entries) > limit:
        raise StateUnavailable("local DLP state contains too many records")
    return entries


def _cleanup(now: int) -> int:
    _, pending, used = _paths()
    active = 0
    for directory in (pending, used):
        entries = _bounded_entries(directory, MAX_PENDING_REQUESTS * 2)
        for path in entries:
            try:
                record = _read_record(path)
                expires_at = int(record.get("expires_at", 0))
                if expires_at <= now:
                    path.unlink(missing_ok=True)
                elif directory == pending:
                    active += 1
            except (ApprovalError, OSError, TypeError, ValueError):
                raise StateUnavailable("local DLP state contains an invalid record")
    return active


def issue_request(
    kind: str,
    scope: bytes,
    *,
    session_id: str,
    now: int | None = None,
) -> ApprovalRequest:
    if kind not in {"UserPromptSubmit", "PreToolUse"}:
        raise ApprovalError("unsupported approval kind")
    current = int(time.time() if now is None else now)
    if _cleanup(current) >= MAX_PENDING_REQUESTS:
        raise StateUnavailable("too many pending local DLP confirmations")
    _, pending, _ = _paths()
    for _ in range(4):
        request_id = secrets.token_hex(12)
        token = secrets.token_urlsafe(24)
        expires_at = current + APPROVAL_TTL_SECONDS
        record = {
            "schema": "dev-flow.dlp-approval.v2",
            "request_id": request_id,
            "kind": kind,
            "scope_mac": _scope_mac(scope),
            "session_mac": _session_mac(session_id),
            "token_hash": _token_hash(token),
            "created_at": current,
            "expires_at": expires_at,
            "approved": False,
        }
        try:
            _exclusive_write(
                pending / f"{request_id}.json",
                json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"),
            )
            return ApprovalRequest(request_id, token, expires_at)
        except FileExistsError:
            continue
    raise StateUnavailable("local DLP request id allocation failed")


def _load_pending(request_id: str, *, now: int) -> tuple[Path, dict[str, Any]]:
    _validate_request_values(request_id)
    _, pending, used = _paths()
    if (used / f"{request_id}.json").exists():
        raise ApprovalError("approval was already consumed")
    path = pending / f"{request_id}.json"
    record = _read_record(path)
    if record.get("schema") != "dev-flow.dlp-approval.v2" or record.get("request_id") != request_id:
        raise ApprovalError("approval record schema is invalid")
    if int(record.get("expires_at", 0)) <= now:
        path.unlink(missing_ok=True)
        raise ApprovalError("approval expired")
    return path, record


def confirm_tool_request_from_prompt(
    request_id: str,
    token: str,
    *,
    session_id: str,
    now: int | None = None,
) -> None:
    """Advance a tool request only from the UserPromptSubmit Hook path."""
    _validate_request_values(request_id, token)
    current = int(time.time() if now is None else now)
    path, record = _load_pending(request_id, now=current)
    if record.get("kind") != "PreToolUse":
        raise ApprovalError("confirmation marker does not belong to a tool request")
    if not hmac.compare_digest(str(record.get("session_mac", "")), _session_mac(session_id)):
        raise ApprovalError("approval host session changed")
    if not hmac.compare_digest(str(record.get("token_hash", "")), _token_hash(token)):
        raise ApprovalError("approval token does not match")
    if record.get("approved") is True:
        raise ApprovalError("tool request was already confirmed")
    record["approved"] = True
    record["approved_at"] = current
    record["approval_event"] = "UserPromptSubmit"
    _atomic_replace(path, json.dumps(record, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _consume(
    request_id: str,
    scope: bytes,
    *,
    kind: str,
    token: str | None,
    session_id: str,
    now: int,
) -> None:
    path, record = _load_pending(request_id, now=now)
    if record.get("kind") != kind:
        raise ApprovalError("approval kind does not match")
    if not hmac.compare_digest(str(record.get("session_mac", "")), _session_mac(session_id)):
        raise ApprovalError("approval host session changed")
    if not hmac.compare_digest(str(record.get("scope_mac", "")), _scope_mac(scope)):
        raise ApprovalError("approval scope changed")
    if kind == "UserPromptSubmit":
        if token is None:
            raise ApprovalError("prompt confirmation token is missing")
        _validate_request_values(request_id, token)
        if not hmac.compare_digest(str(record.get("token_hash", "")), _token_hash(token)):
            raise ApprovalError("approval token does not match")
    elif record.get("approved") is not True:
        raise ApprovalError("tool request has not been confirmed")
    _, _, used = _paths()
    used_record = json.dumps(
        {"schema": "dev-flow.dlp-used.v1", "request_id": request_id, "expires_at": int(record["expires_at"])},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    try:
        _exclusive_write(used / f"{request_id}.json", used_record)
    except FileExistsError as exc:
        raise ApprovalError("approval was already consumed") from exc
    try:
        path.unlink(missing_ok=True)
    except OSError:
        # The used marker is authoritative; stale pending metadata is bounded and
        # will be removed by expiry cleanup.
        pass


def consume_prompt_request(
    request_id: str,
    token: str,
    scope: bytes,
    *,
    session_id: str,
    now: int | None = None,
) -> None:
    _consume(
        request_id,
        scope,
        kind="UserPromptSubmit",
        token=token,
        session_id=session_id,
        now=int(time.time() if now is None else now),
    )


def consume_tool_request(
    request_id: str,
    scope: bytes,
    *,
    session_id: str,
    now: int | None = None,
) -> None:
    _consume(
        request_id,
        scope,
        kind="PreToolUse",
        token=None,
        session_id=session_id,
        now=int(time.time() if now is None else now),
    )


def find_approved_tool_request(
    scope: bytes,
    *,
    session_id: str,
    now: int | None = None,
) -> str | None:
    current = int(time.time() if now is None else now)
    _cleanup(current)
    _, pending, _ = _paths()
    expected = _scope_mac(scope)
    expected_session = _session_mac(session_id)
    for path in _bounded_entries(pending, MAX_PENDING_REQUESTS):
        record = _read_record(path)
        if (
            record.get("kind") == "PreToolUse"
            and record.get("approved") is True
            and int(record.get("expires_at", 0)) > current
            and hmac.compare_digest(str(record.get("scope_mac", "")), expected)
            and hmac.compare_digest(str(record.get("session_mac", "")), expected_session)
        ):
            return str(record.get("request_id"))
    return None


def current_mode() -> str:
    override = os.environ.get(MODE_ENV)
    if override is not None:
        return override if override in VALID_MODES else "strict"
    root = _state_root()
    path = root / "settings.json"
    if not path.exists():
        return DEFAULT_MODE
    try:
        _ensure_private_dir(root)
        record = _read_record(path)
    except (ApprovalError, StateUnavailable):
        return "strict"
    mode = record.get("mode")
    return str(mode) if mode in VALID_MODES else "strict"


def configure_mode(mode: str) -> None:
    if mode not in VALID_MODES:
        raise ApprovalError("DLP mode must be personal or strict")
    root, _, _ = _paths()
    value = json.dumps(
        {"schema": "dev-flow.dlp-settings.v1", "mode": mode},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    _atomic_replace(root / "settings.json", value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Configure local Dev Flow DLP behavior")
    subparsers = parser.add_subparsers(dest="command", required=True)
    configure = subparsers.add_parser("configure", help="select personal or strict local DLP behavior")
    configure.add_argument("--mode", choices=sorted(VALID_MODES), required=True)
    subparsers.add_parser("mode", help="print the active local DLP mode")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "configure":
            configure_mode(args.mode)
            print(json.dumps({"status": "configured", "mode": args.mode}, sort_keys=True))
            return 0
        if args.command == "mode":
            print(json.dumps({"status": "ok", "mode": current_mode()}, sort_keys=True))
            return 0
    except (ApprovalError, StateUnavailable) as exc:
        print(json.dumps({"status": "blocked", "error": str(exc)}, sort_keys=True))
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
