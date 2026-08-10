"""Lexical and resolved filesystem-boundary contracts for Dev Flow."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path


SAFE_IDENTIFIER_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,80}$")
SAFE_PATH_COMPONENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,80}$")


class PathContractError(ValueError):
    """Raised when a path or identifier escapes its declared owner."""


def safe_identifier(value: str, *, label: str = "identifier") -> str:
    if not isinstance(value, str) or not SAFE_IDENTIFIER_RE.fullmatch(value):
        raise PathContractError(f"{label} must use 1-81 lowercase safe characters")
    return value


def safe_path_component(value: str, *, label: str = "path component") -> str:
    if (
        not isinstance(value, str)
        or value in {".", ".."}
        or not SAFE_PATH_COMPONENT_RE.fullmatch(value)
    ):
        raise PathContractError(f"{label} must be one safe 1-81 character path component")
    return value


def contained_path(
    root: Path,
    candidate: str | Path,
    *,
    label: str,
    require_relative: bool = False,
    reject_symlinks: bool = False,
    allow_root: bool = False,
) -> Path:
    """Validate both lexical and resolved containment below an owned root."""
    owner = Path(os.path.abspath(root))
    raw = Path(candidate)
    if require_relative and raw.is_absolute():
        raise PathContractError(f"{label} must be relative to {owner}: {candidate}")
    if require_relative and any(part in {"", ".", ".."} for part in raw.parts):
        raise PathContractError(f"{label} escapes {owner} through a forbidden path component: {candidate}")
    lexical = Path(os.path.abspath(raw if raw.is_absolute() else owner / raw))
    if lexical != owner and not lexical.is_relative_to(owner):
        raise PathContractError(f"{label} escapes {owner}: {candidate}")
    if lexical == owner and not allow_root:
        raise PathContractError(f"{label} must name a strict descendant of {owner}")
    if reject_symlinks:
        current = owner
        if current.is_symlink():
            raise PathContractError(f"{label} owner must not be a symlink: {current}")
        for part in lexical.relative_to(owner).parts:
            current /= part
            if current.is_symlink():
                raise PathContractError(f"{label} must not traverse a symlink: {current}")
    resolved_owner = owner.resolve()
    resolved = lexical.resolve()
    if resolved != resolved_owner and not resolved.is_relative_to(resolved_owner):
        raise PathContractError(f"{label} resolves outside {resolved_owner}: {candidate}")
    if resolved == resolved_owner and not allow_root:
        raise PathContractError(f"{label} resolves to its owner instead of a strict descendant: {candidate}")
    return lexical


def atomic_write_text(path: Path, text: str) -> None:
    """Replace one regular-file target without following a final symlink."""
    if path.is_symlink():
        raise PathContractError(f"text target must not be a symlink: {path}")
    if path.exists() and not path.is_file():
        raise PathContractError(f"text target must be a regular file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
