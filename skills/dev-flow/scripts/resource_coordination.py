"""Cooperative single-host resource leases and measurement-only preflight."""

from __future__ import annotations

import ctypes
import hashlib
import hmac
import json
import math
import os
import platform
import re
import secrets
import shutil
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

try:  # pragma: no cover - platform-specific branch
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

try:  # pragma: no cover - platform-specific branch
    import msvcrt
except ImportError:  # pragma: no cover - POSIX
    msvcrt = None


SCHEMA = "dev-flow.resource-lease.v1"
KINDS = {"build-cache", "container", "device", "disk", "emulator", "port", "simulator"}
MIN_TTL = 1
MAX_TTL = 24 * 60 * 60
MAX_VALUE_CHARS = 256
MAX_STATE_BYTES = 16 * 1024
NETWORK_FILESYSTEMS = {"9p", "afpfs", "cifs", "davfs", "fuse.sshfs", "nfs", "nfs4", "smbfs", "sshfs"}


class ResourceCoordinationError(ValueError):
    pass


class ResourceInputError(ResourceCoordinationError):
    pass


def default_runtime_root() -> Path:
    return Path(tempfile.gettempdir()) / "dev-flow-resource-leases-v1"


def _bounded(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or len(value) > MAX_VALUE_CHARS or any(ord(char) < 32 for char in value):
        raise ResourceInputError(f"{label} must contain 1-{MAX_VALUE_CHARS} printable characters")
    return value


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_inputs(kind: str, resource: str, ttl: int | None = None) -> None:
    if kind not in KINDS:
        raise ResourceInputError(f"kind must be one of {sorted(KINDS)}")
    _bounded(resource, "resource")
    if ttl is not None and (not isinstance(ttl, int) or ttl < MIN_TTL or ttl > MAX_TTL):
        raise ResourceInputError(f"ttl must be between {MIN_TTL} and {MAX_TTL} seconds")


def _moment(now: float | None) -> float:
    value = time.time() if now is None else now
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ResourceInputError("time must be a finite number")
    return float(value)


def _filesystem_type(path: Path) -> str:
    system = platform.system()
    if system == "Windows":
        drive = str(path.drive or path.anchor)
        if not drive:
            return "unknown"
        kind = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(drive + "\\"))
        return "network" if kind == 4 else "local" if kind in {2, 3, 6} else "unknown"
    if system == "Linux":
        try:
            resolved = path.resolve().as_posix()
            candidates: list[tuple[int, str]] = []
            for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
                left, right = line.split(" - ", 1)
                mountpoint = left.split()[4].replace("\\040", " ")
                fs_type = right.split()[0]
                if resolved == mountpoint or resolved.startswith(mountpoint.rstrip("/") + "/"):
                    candidates.append((len(mountpoint), fs_type))
            if not candidates:
                return "unknown"
            fs_type = max(candidates)[1].lower()
            return "network" if fs_type in NETWORK_FILESYSTEMS else "local"
        except (OSError, ValueError, IndexError):
            return "unknown"
    if system == "Darwin":
        completed = subprocess.run(["stat", "-f", "%T", str(path)], capture_output=True, text=True, check=False)
        if completed.returncode != 0:
            return "unknown"
        fs_type = completed.stdout.strip().lower()
        return "network" if fs_type in NETWORK_FILESYSTEMS else "local"
    return "unknown"


def validate_runtime_root(root: Path) -> Path:
    expanded = root.expanduser().absolute()
    if expanded == Path.cwd().resolve() or expanded == Path(expanded.anchor) or expanded == Path.home().resolve():
        raise ResourceCoordinationError("runtime root cannot be the current directory, filesystem root, or home directory")
    if expanded.exists() and (expanded.is_symlink() or not expanded.is_dir()):
        raise ResourceCoordinationError("runtime root must be a non-symlink directory")
    expanded.mkdir(parents=True, exist_ok=True, mode=0o700)
    resolved = expanded.resolve()
    if resolved != expanded.resolve(strict=True):
        raise ResourceCoordinationError("runtime root could not be resolved")
    try:
        os.chmod(resolved, 0o700)
    except OSError as exc:
        raise ResourceCoordinationError(f"cannot restrict runtime root permissions: {exc}") from exc
    if os.name != "nt":
        root_info = resolved.stat()
        if root_info.st_uid != os.getuid():
            raise ResourceCoordinationError("runtime root is not owned by the current user")
        if stat.S_IMODE(root_info.st_mode) & 0o077:
            raise ResourceCoordinationError("runtime root permissions are not user-private")
    fs = _filesystem_type(resolved)
    if fs != "local":
        raise ResourceCoordinationError(f"runtime filesystem is {fs}; safe local atomicity is unavailable")
    return resolved


def _paths(root: Path, kind: str, resource: str) -> tuple[Path, Path]:
    identity = hashlib.sha256(f"{kind}\0{resource}".encode("utf-8")).hexdigest()
    return root / f"{kind}-{identity}.json", root / f"{kind}-{identity}.guard"


def _read_json(path: Path, label: str) -> dict[str, Any] | None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ResourceCoordinationError(f"cannot inspect {label}: {exc}") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode) or info.st_size > MAX_STATE_BYTES:
        raise ResourceCoordinationError(f"{label} is unsafe or oversized")
    if os.name != "nt" and (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077):
        raise ResourceCoordinationError(f"{label} permissions or ownership are unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ResourceCoordinationError(f"{label} is corrupt: {exc}") from exc
    if not isinstance(payload, dict):
        raise ResourceCoordinationError(f"{label} must be a JSON object")
    return payload


def _atomic_json(root: Path, target: Path, payload: dict[str, Any]) -> None:
    content = json.dumps(
        payload, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")
    if len(content) > MAX_STATE_BYTES:
        raise ResourceCoordinationError("lease state exceeded its bounded size")
    temporary = root / f".{target.name}.{secrets.token_hex(8)}.tmp"
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if temporary.stat().st_dev != target.parent.stat().st_dev:
            raise ResourceCoordinationError("atomic replacement crossed filesystems")
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


class _Guard:
    def __init__(self, root: Path, path: Path, now: float) -> None:
        self.root = root
        self.path = path
        self.now = now
        self.descriptor: int | None = None

    @staticmethod
    def _lock(descriptor: int) -> None:
        try:
            if os.name == "nt":  # pragma: no cover - hosted Windows compatibility
                if msvcrt is None:
                    raise ResourceCoordinationError("Windows file locking is unavailable")
                if os.fstat(descriptor).st_size == 0:
                    os.write(descriptor, b"\0")
                    os.fsync(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                if fcntl is None:
                    raise ResourceCoordinationError("POSIX file locking is unavailable")
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, OSError) as exc:
            raise ResourceCoordinationError("resource transition is already in progress") from exc

    @staticmethod
    def _unlock(descriptor: int) -> None:
        if os.name == "nt":  # pragma: no cover - hosted Windows compatibility
            if msvcrt is not None:
                os.lseek(descriptor, 0, os.SEEK_SET)
                msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        elif fcntl is not None:
            fcntl.flock(descriptor, fcntl.LOCK_UN)

    @staticmethod
    def _write_metadata(descriptor: int, now: float) -> None:
        content = json.dumps(
            {"schema": SCHEMA, "created_at": now, "nonce": secrets.token_hex(16)},
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
        os.lseek(descriptor, 0, os.SEEK_SET)
        offset = 0
        while offset < len(content):
            written = os.write(descriptor, content[offset:])
            if written <= 0:
                raise OSError("could not publish transition guard metadata")
            offset += written
        os.ftruncate(descriptor, len(content))
        os.fsync(descriptor)

    def __enter__(self) -> "_Guard":
        flags = os.O_RDWR | os.O_CREAT
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(self.path, flags, 0o600)
        try:
            info = os.fstat(descriptor)
            path_info = self.path.lstat()
            if (
                not stat.S_ISREG(info.st_mode)
                or stat.S_ISLNK(path_info.st_mode)
                or (info.st_dev, info.st_ino) != (path_info.st_dev, path_info.st_ino)
                or info.st_size > MAX_STATE_BYTES
            ):
                raise ResourceCoordinationError("transition guard is unsafe or oversized")
            if os.name != "nt" and (
                info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077
            ):
                raise ResourceCoordinationError("transition guard permissions or ownership are unsafe")
            self._lock(descriptor)
            self._write_metadata(descriptor, self.now)
            self.descriptor = descriptor
            return self
        except Exception:
            os.close(descriptor)
            raise

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.descriptor is not None:
            try:
                self._unlock(self.descriptor)
            finally:
                os.close(self.descriptor)
                self.descriptor = None


def _lease(path: Path, kind: str, resource: str) -> dict[str, Any] | None:
    payload = _read_json(path, "lease state")
    if payload is None:
        return None
    required = {"schema", "status", "kind", "resource_digest", "owner_digest", "token_digest", "generation", "created_at", "renewed_at", "expires_at", "pid"}
    if set(payload) != required or payload.get("schema") != SCHEMA or payload.get("kind") != kind or payload.get("resource_digest") != _digest(resource):
        raise ResourceCoordinationError("lease state violates the exact schema or resource identity")
    digest_pattern = re.compile(r"sha256:[0-9a-f]{64}")
    if payload["status"] not in {"active", "released"} or type(payload["generation"]) is not int or payload["generation"] < 1:
        raise ResourceCoordinationError("lease state has invalid status or generation")
    if any(
        not isinstance(payload[key], str) or digest_pattern.fullmatch(payload[key]) is None
        for key in ("resource_digest", "owner_digest", "token_digest")
    ):
        raise ResourceCoordinationError("lease state has invalid identity digests")
    if type(payload["pid"]) is not int or payload["pid"] < 1:
        raise ResourceCoordinationError("lease state has invalid process metadata")
    timestamps = [payload[key] for key in ("created_at", "renewed_at", "expires_at")]
    if not all(isinstance(value, (int, float)) and math.isfinite(value) for value in timestamps):
        raise ResourceCoordinationError("lease state has invalid timestamps")
    if payload["created_at"] > payload["renewed_at"] or payload["renewed_at"] > payload["expires_at"]:
        raise ResourceCoordinationError("lease state timestamps violate monotonic ordering")
    return payload


def _unavailable(exc: Exception) -> dict[str, Any]:
    return {"status": "unavailable", "reason": str(exc), "claim_limit": "cooperating-same-user-local-filesystem-only"}


def acquire(root: Path, kind: str, resource: str, ttl: int, owner: str | None = None, *, now: float | None = None) -> dict[str, Any]:
    _validate_inputs(kind, resource, ttl)
    owner = _bounded(owner or f"pid:{os.getpid()}", "owner")
    moment = _moment(now)
    try:
        runtime = validate_runtime_root(root)
        state_path, guard_path = _paths(runtime, kind, resource)
        with _Guard(runtime, guard_path, moment):
            moment = _moment(now)
            current = _lease(state_path, kind, resource)
            if current and current["status"] == "active":
                if moment < current["renewed_at"]:
                    raise ResourceCoordinationError("clock rollback detected for lease")
                if moment < current["expires_at"]:
                    return {"status": "conflict", "kind": kind, "generation": current["generation"], "expires_at": current["expires_at"], "claim_limit": "cooperating-same-user-local-filesystem-only"}
            generation = (current["generation"] if current else 0) + 1
            token = secrets.token_urlsafe(32)
            recovered = bool(current and current["status"] == "active")
            payload = {"schema": SCHEMA, "status": "active", "kind": kind, "resource_digest": _digest(resource), "owner_digest": _digest(owner), "token_digest": _digest(token), "generation": generation, "created_at": moment, "renewed_at": moment, "expires_at": moment + ttl, "pid": os.getpid()}
            _atomic_json(runtime, state_path, payload)
            return {"status": "expired-recovered" if recovered else "acquired", "kind": kind, "token": token, "generation": generation, "expires_at": moment + ttl, "claim_limit": "cooperating-same-user-local-filesystem-only"}
    except (OSError, ResourceCoordinationError) as exc:
        if str(exc) == "resource transition is already in progress":
            return {"status": "conflict", "kind": kind, "reason": str(exc), "claim_limit": "cooperating-same-user-local-filesystem-only"}
        return _unavailable(exc)


def inspect(root: Path, kind: str, resource: str, *, now: float | None = None) -> dict[str, Any]:
    _validate_inputs(kind, resource)
    moment = _moment(now)
    try:
        runtime = validate_runtime_root(root)
        state_path, _ = _paths(runtime, kind, resource)
        current = _lease(state_path, kind, resource)
        if not current or current["status"] == "released":
            return {"status": "available", "kind": kind, "claim_limit": "observation-does-not-grant-resource-authority"}
        if moment < current["renewed_at"]:
            raise ResourceCoordinationError("clock rollback detected for lease")
        return {"status": "expired" if moment >= current["expires_at"] else "leased", "kind": kind, "generation": current["generation"], "expires_at": current["expires_at"], "owner_digest": current["owner_digest"], "claim_limit": "observation-does-not-grant-resource-authority"}
    except (OSError, ResourceCoordinationError) as exc:
        return _unavailable(exc)


def renew(root: Path, kind: str, resource: str, token: str, ttl: int, *, now: float | None = None) -> dict[str, Any]:
    _validate_inputs(kind, resource, ttl)
    _bounded(token, "token")
    moment = _moment(now)
    try:
        runtime = validate_runtime_root(root)
        state_path, guard_path = _paths(runtime, kind, resource)
        with _Guard(runtime, guard_path, moment):
            moment = _moment(now)
            current = _lease(state_path, kind, resource)
            if not current or current["status"] != "active" or moment >= current["expires_at"]:
                return {"status": "expired", "kind": kind}
            if moment < current["renewed_at"]:
                raise ResourceCoordinationError("clock rollback detected for lease")
            if not hmac.compare_digest(current["token_digest"], _digest(token)):
                return {"status": "forbidden", "kind": kind}
            current = dict(current)
            current["generation"] += 1
            current["renewed_at"] = moment
            current["expires_at"] = moment + ttl
            _atomic_json(runtime, state_path, current)
            return {"status": "renewed", "kind": kind, "generation": current["generation"], "expires_at": current["expires_at"]}
    except (OSError, ResourceCoordinationError) as exc:
        return _unavailable(exc)


def release(root: Path, kind: str, resource: str, token: str, *, now: float | None = None) -> dict[str, Any]:
    _validate_inputs(kind, resource)
    _bounded(token, "token")
    moment = _moment(now)
    try:
        runtime = validate_runtime_root(root)
        state_path, guard_path = _paths(runtime, kind, resource)
        with _Guard(runtime, guard_path, moment):
            moment = _moment(now)
            current = _lease(state_path, kind, resource)
            if not current or current["status"] == "released":
                return {"status": "available", "kind": kind}
            if moment < current["renewed_at"]:
                raise ResourceCoordinationError("clock rollback detected for lease")
            if moment >= current["expires_at"]:
                return {"status": "expired", "kind": kind}
            if not hmac.compare_digest(current["token_digest"], _digest(token)):
                return {"status": "forbidden", "kind": kind}
            tombstone = dict(current)
            tombstone.update({"status": "released", "generation": current["generation"] + 1, "renewed_at": moment, "expires_at": moment})
            _atomic_json(runtime, state_path, tombstone)
            state_path.unlink()
            return {"status": "released", "kind": kind, "generation": tombstone["generation"]}
    except (OSError, ResourceCoordinationError) as exc:
        return _unavailable(exc)


def preflight(path: Path, estimated_growth_bytes: int | None, reserve_bytes: int | None, require_writable: bool) -> dict[str, Any]:
    target = path.expanduser().resolve()
    if not target.is_dir() or path.is_symlink():
        raise ResourceInputError("preflight path must be an existing non-symlink directory")
    for value, label in ((estimated_growth_bytes, "estimated growth"), (reserve_bytes, "reserve")):
        if value is not None and (not isinstance(value, int) or value < 0):
            raise ResourceInputError(f"{label} must be a non-negative integer")
    usage = shutil.disk_usage(target)
    writable = None
    cleanup = None
    if require_writable:
        probe = target / f".dev-flow-writable-{secrets.token_hex(16)}"
        try:
            descriptor = os.open(probe, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            os.close(descriptor)
            writable = probe.stat().st_size == 0
        except OSError:
            writable = False
        finally:
            try:
                probe.unlink(missing_ok=True)
                cleanup = not probe.exists()
            except OSError:
                cleanup = False
    budgets_supplied = estimated_growth_bytes is not None and reserve_bytes is not None
    capacity_ok = budgets_supplied and usage.free - estimated_growth_bytes >= reserve_bytes
    if writable is False or cleanup is False or (budgets_supplied and not capacity_ok):
        status = "blocked"
    elif budgets_supplied:
        status = "passed"
    else:
        status = "observed"
    return {"status": status, "path_digest": _digest(str(target)), "filesystem_device": target.stat().st_dev, "total_bytes": usage.total, "free_bytes": usage.free, "estimated_growth_bytes": estimated_growth_bytes, "reserve_bytes": reserve_bytes, "writable": writable, "probe_cleanup": cleanup, "claim_limit": "measurement-does-not-prove-quota-or-future-contention"}
