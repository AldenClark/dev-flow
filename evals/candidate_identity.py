"""Bounded RC.4 semantic-runtime and qualification-execution identities."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import platform
import re
from pathlib import Path
import sys
from typing import Any, Iterable


IDENTITY_SCHEMA = "dev-flow.rc4.candidate-identity.v1"
MAX_FILES = 8192
MAX_FILE_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024
SEMANTIC_ROOTS = (".codex-plugin/plugin.json", "hooks", "skills", "governance")
EVIDENCE_ONLY_PATHS = (
    "docs/workstreams/dev-flow-2.0-rc.4/audit.md",
    "docs/workstreams/dev-flow-2.0-rc.4/progress.md",
    "CHANGELOG.md",
)
DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
EXECUTION_INPUT_KEYS = {
    "repository_dependencies_sha256",
    "codex_executable_sha256",
    "model",
    "reasoning_effort",
    "environment_policy",
    "python_implementation",
    "python_version",
    "platform",
    "execution_policy",
}


class CandidateIdentityError(ValueError):
    pass


def _files_below(path: Path) -> Iterable[Path]:
    if path.is_file() or path.is_symlink():
        yield path
        return
    if not path.is_dir():
        return
    for candidate in sorted(path.rglob("*")):
        if candidate.is_dir() or "__pycache__" in candidate.parts or candidate.suffix == ".pyc":
            continue
        yield candidate


def semantic_runtime_files(root: Path) -> list[Path]:
    files = [candidate for relative in SEMANTIC_ROOTS for candidate in _files_below(root / relative)]
    if not files:
        raise CandidateIdentityError("semantic runtime identity has no inputs")
    return sorted(set(files))


def _resolve_local_module(root: Path, module: str) -> Path | None:
    relative = Path(*module.split("."))
    for base in (root / "evals", root / "skills" / "dev-flow" / "scripts"):
        for candidate in (base / relative.with_suffix(".py"), base / relative / "__init__.py"):
            if candidate.is_file():
                return candidate.resolve()
    return None


def qualification_dependency_files(root: Path, runner: Path, catalog: Path) -> list[Path]:
    root = root.resolve()
    pending = [runner.resolve()]
    observed: set[Path] = {catalog.resolve()}
    while pending:
        path = pending.pop()
        if path in observed:
            continue
        observed.add(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeDecodeError, SyntaxError) as exc:
            raise CandidateIdentityError(f"cannot inspect qualification dependency {path}: {exc}") from exc
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                modules.add(node.module)
        for module in sorted(modules):
            resolved = _resolve_local_module(root, module)
            if resolved is not None and resolved not in observed:
                pending.append(resolved)
    return sorted(observed)


def hash_files(root: Path, files: Iterable[Path]) -> dict[str, Any]:
    resolved_root = root.resolve()
    entries: list[tuple[str, Path]] = []
    for path in files:
        absolute = path.absolute() if path.is_symlink() else path.resolve()
        if not absolute.is_relative_to(resolved_root):
            raise CandidateIdentityError(f"identity input escaped repository: {path}")
        entries.append((absolute.relative_to(resolved_root).as_posix(), path))
    return hash_named_files(entries)


def hash_named_files(entries: Iterable[tuple[str, Path]]) -> dict[str, Any]:
    digest = hashlib.sha256()
    total = 0
    manifest: list[str] = []
    unique = sorted(entries, key=lambda item: item[0])
    labels = [label for label, _ in unique]
    if len(labels) != len(set(labels)):
        raise CandidateIdentityError("identity contains duplicate logical paths")
    if len(unique) > MAX_FILES:
        raise CandidateIdentityError("identity exceeded bounded file count")
    for relative, path in unique:
        if (
            not relative
            or relative.startswith("/")
            or ".." in Path(relative).parts
            or len(relative) > 1024
        ):
            raise CandidateIdentityError(f"identity logical path is unsafe: {relative!r}")
        if path.is_symlink():
            content = ("symlink:" + os.readlink(path)).encode("utf-8")
        elif path.is_file():
            size = path.stat().st_size
            if size > MAX_FILE_BYTES:
                raise CandidateIdentityError(f"identity input exceeded bounded size: {relative}")
            content = path.read_bytes()
        else:
            raise CandidateIdentityError(f"identity input is not a file: {relative}")
        total += len(content)
        if total > MAX_TOTAL_BYTES:
            raise CandidateIdentityError("identity exceeded bounded total bytes")
        encoded = relative.encode("utf-8")
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
        manifest.append(relative)
    return {"sha256": "sha256:" + digest.hexdigest(), "files": manifest, "file_count": len(manifest), "total_bytes": total}


def build_identities(
    root: Path,
    *,
    runner: Path,
    catalog: Path,
    codex_executable_sha256: str,
    model: str,
    reasoning_effort: str,
    environment_policy: str,
    execution_policy: dict[str, Any],
) -> dict[str, Any]:
    semantic = hash_files(root, semantic_runtime_files(root))
    tool_root = runner.resolve().parents[1]
    dependency_files = qualification_dependency_files(tool_root, runner, catalog)
    qualification_entries: list[tuple[str, Path]] = []
    catalog_resolved = catalog.resolve()
    for path in dependency_files:
        resolved = path.resolve()
        if resolved == catalog_resolved:
            label = "catalog/input.json"
        elif resolved.is_relative_to(tool_root):
            label = "tool/" + resolved.relative_to(tool_root).as_posix()
        else:
            raise CandidateIdentityError(
                f"qualification dependency escaped admitted domains: {path}"
            )
        qualification_entries.append((label, path))
    qualification = hash_named_files(qualification_entries)
    execution_inputs = {
        "repository_dependencies_sha256": qualification["sha256"],
        "codex_executable_sha256": codex_executable_sha256,
        "model": model,
        "reasoning_effort": reasoning_effort,
        "environment_policy": environment_policy,
        "python_implementation": platform.python_implementation(),
        "python_version": platform.python_version(),
        "platform": sys.platform,
        "execution_policy": execution_policy,
    }
    execution_sha = "sha256:" + hashlib.sha256(
        json.dumps(execution_inputs, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "schema": IDENTITY_SCHEMA,
        "semantic_runtime": semantic,
        "qualification_execution": {
            **qualification,
            "execution_inputs": execution_inputs,
            "sha256": execution_sha,
        },
    }


def evidence_only_changes(paths: Iterable[str]) -> tuple[bool, list[str]]:
    rejected = sorted(path for path in paths if path not in EVIDENCE_ONLY_PATHS)
    return not rejected, rejected


def identity_errors(identity: Any, label: str) -> list[str]:
    errors: list[str] = []
    if not isinstance(identity, dict):
        return [f"{label} identity must be an object"]
    if set(identity) != {"schema", "semantic_runtime", "qualification_execution"}:
        errors.append(f"{label} identity must use the exact top-level schema")
    if identity.get("schema") != IDENTITY_SCHEMA:
        errors.append(f"{label} identity schema is invalid")
    section_keys = {
        "semantic_runtime": {"sha256", "files", "file_count", "total_bytes"},
        "qualification_execution": {
            "sha256",
            "files",
            "file_count",
            "total_bytes",
            "execution_inputs",
        },
    }
    for section, required_keys in section_keys.items():
        value = identity.get(section)
        if not isinstance(value, dict):
            errors.append(f"{label} {section} identity must be an object")
            continue
        if set(value) != required_keys:
            errors.append(f"{label} {section} identity must use the exact schema")
        digest = value.get("sha256")
        if not isinstance(digest, str) or DIGEST_PATTERN.fullmatch(digest) is None:
            errors.append(f"{label} {section} identity digest is invalid")
        files = value.get("files")
        file_count = value.get("file_count")
        total_bytes = value.get("total_bytes")
        if (
            not isinstance(files, list)
            or not all(
                isinstance(path, str)
                and path
                and not path.startswith("/")
                and ".." not in Path(path).parts
                and len(path) <= 1024
                for path in files
            )
            or len(files) != len(set(files))
            or files != sorted(files)
        ):
            errors.append(f"{label} {section} file manifest is invalid")
        if not isinstance(file_count, int) or isinstance(file_count, bool) or file_count < 1:
            errors.append(f"{label} {section} file count is invalid")
        elif isinstance(files, list) and file_count != len(files):
            errors.append(f"{label} {section} file count does not match its manifest")
        if not isinstance(total_bytes, int) or isinstance(total_bytes, bool) or total_bytes < 1:
            errors.append(f"{label} {section} total bytes is invalid")
        if section == "qualification_execution":
            execution_inputs = value.get("execution_inputs")
            if not isinstance(execution_inputs, dict) or set(execution_inputs) != EXECUTION_INPUT_KEYS:
                errors.append(
                    f"{label} qualification execution inputs must use the exact schema"
                )
            else:
                for digest_key in (
                    "repository_dependencies_sha256",
                    "codex_executable_sha256",
                ):
                    digest_value = execution_inputs[digest_key]
                    if (
                        not isinstance(digest_value, str)
                        or DIGEST_PATTERN.fullmatch(digest_value) is None
                    ):
                        errors.append(
                            f"{label} qualification {digest_key} is invalid"
                        )
                for text_key in (
                    "model",
                    "reasoning_effort",
                    "environment_policy",
                    "python_implementation",
                    "python_version",
                    "platform",
                ):
                    if not isinstance(execution_inputs[text_key], str) or not execution_inputs[text_key]:
                        errors.append(
                            f"{label} qualification {text_key} is invalid"
                        )
                if not isinstance(execution_inputs["execution_policy"], dict):
                    errors.append(f"{label} qualification execution policy is invalid")
    return errors


def verify_frozen(
    previous: dict[str, Any], current: dict[str, Any], changed_paths: Iterable[str]
) -> dict[str, Any]:
    allowed, rejected = evidence_only_changes(changed_paths)
    errors = identity_errors(previous, "previous") + identity_errors(current, "current")
    identities_valid = not errors
    semantic_unchanged = bool(
        identities_valid
        and previous["semantic_runtime"]["sha256"]
        == current["semantic_runtime"]["sha256"]
    )
    execution_unchanged = bool(
        identities_valid
        and previous["qualification_execution"]["sha256"]
        == current["qualification_execution"]["sha256"]
    )
    if not allowed:
        errors.append(f"post-observation changes are not evidence-only: {rejected}")
    if not semantic_unchanged:
        errors.append("semantic-runtime identity changed")
    if not execution_unchanged:
        errors.append("qualification-execution identity changed")
    return {
        "status": "valid" if not errors else "invalid",
        "semantic_runtime_unchanged": semantic_unchanged,
        "qualification_execution_unchanged": execution_unchanged,
        "evidence_only_changes": allowed,
        "rejected_paths": rejected,
        "errors": errors,
    }
