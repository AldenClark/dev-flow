#!/usr/bin/env python3
"""Read-only source, runtime, cache, Hook, and outcome diagnosis."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any

import outcome_observation


MAX_JSON_BYTES = 262_144
DEFAULT_MAX_CACHE_FILES = 20_000
MAX_CACHE_DIRECTORIES = 20_000
MAX_CACHE_DEPTH = 12
EXECUTING_PLUGIN_ROOT = Path(__file__).resolve().parents[3]
SAFE_GIT_PREFIX = [
    "git",
    "-c",
    "core.fsmonitor=false",
    "-c",
    f"core.hooksPath={os.devnull}",
]


def _sha256_bytes(data: bytes) -> str:
    hasher = hashlib.sha256()
    hasher.update(data)
    return "sha256:" + hasher.hexdigest()


def _read_root_file(root: Path, relative: Path | str, *, max_bytes: int) -> bytes:
    root = root.resolve(strict=True)
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("input must be a repository-relative file")
    current = root
    for part in relative.parts:
        current = current / part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("input path must not contain symlinks")
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root) or not stat.S_ISREG(current.lstat().st_mode):
        raise ValueError("input is not a rooted regular file")
    raw = current.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError("input exceeds its bounded size")
    return raw


def _read_json(root: Path, relative: Path | str) -> Any:
    raw = _read_root_file(root, relative, max_bytes=MAX_JSON_BYTES)
    return json.loads(raw.decode("utf-8"))


def _git_observation(root: Path) -> dict[str, Any]:
    if not (root / ".git").exists():
        return {"status": "not_observed", "reason": "plugin root is not a Git checkout"}
    result: dict[str, Any] = {"status": "observed"}
    commands = {
        "head": [*SAFE_GIT_PREFIX, "rev-parse", "HEAD"],
        "branch": [*SAFE_GIT_PREFIX, "branch", "--show-current"],
        "exact_tags": [*SAFE_GIT_PREFIX, "tag", "--points-at", "HEAD"],
    }
    git_environment = {
        key: value for key, value in os.environ.items() if not key.startswith("GIT_")
    }
    git_environment.update(
        {
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    for field, command in commands.items():
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            env=git_environment,
        )
        if completed.returncode != 0:
            return {"status": "unavailable", "reason": "Git observation failed"}
        value = completed.stdout.strip()
        result[field] = value.splitlines() if field == "exact_tags" and value else [] if field == "exact_tags" else value
    changed = subprocess.run(
        [
            *SAFE_GIT_PREFIX,
            "status",
            "--porcelain=v1",
            "-z",
            "--ignore-submodules=all",
            "--untracked-files=normal",
        ],
        cwd=root,
        capture_output=True,
        check=False,
        env=git_environment,
    )
    result["worktree_changed_paths"] = (
        sum(1 for item in changed.stdout.split(b"\0") if item) if changed.returncode == 0 else None
    )
    return result


def _product_state(root: Path) -> dict[str, Any]:
    validator = EXECUTING_PLUGIN_ROOT / "tools" / "validate_product_state.py"
    if validator.is_symlink() or not validator.is_file():
        return {"status": "unavailable", "reason": "trusted product-state validator is not packaged"}
    try:
        spec = importlib.util.spec_from_file_location("dev_flow_product_state_doctor", validator)
        if spec is None or spec.loader is None:
            raise ValueError("validator could not be loaded")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.validate(root, check_git=False)
    except Exception as exc:  # bounded diagnostic projection; never expose path/content details
        return {"status": "unavailable", "reason": type(exc).__name__}


def _installed_versions(codex_home: Path | None) -> dict[str, Any]:
    if codex_home is None:
        return {"status": "not_observed", "reason": "pass --codex-home to inspect installed cache identity"}
    target = codex_home.expanduser().resolve() / "plugins" / "cache" / "dev-flow" / "dev-flow"
    try:
        if target.is_symlink() or not target.is_dir():
            return {"status": "not_observed", "versions": []}
        versions = sorted(
            entry.name
            for entry in target.iterdir()
            if entry.is_dir() and not entry.is_symlink() and len(entry.name) <= 64
        )
        if len(versions) > 64:
            return {"status": "unavailable", "reason": "installed version inventory exceeds limit"}
        return {"status": "observed", "versions": versions}
    except OSError:
        return {"status": "unavailable", "reason": "installed cache could not be inspected"}


def _loaded_identity(root: Path, supplied: Path | None) -> dict[str, Any]:
    candidate = supplied
    source = "argument"
    if candidate is None:
        environment = os.environ.get("DEV_FLOW_LOADED_PLUGIN_ROOT")
        if environment:
            candidate = Path(environment)
            source = "environment"
    if candidate is None:
        return {"status": "not_observed", "reason": "loaded plugin root was not supplied"}
    try:
        loaded = candidate.expanduser().resolve(strict=True)
        manifest = _read_json(loaded, ".codex-plugin/plugin.json")
        source_manifest = _read_json(root, ".codex-plugin/plugin.json")
        if not isinstance(manifest, dict) or not isinstance(source_manifest, dict):
            raise ValueError("manifest is not an object")
        return {
            "status": "observed",
            "source": source,
            "version": manifest.get("version"),
            "matches_source_root": loaded == root,
            "matches_source_version": manifest.get("version") == source_manifest.get("version"),
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"status": "unavailable", "source": source, "reason": "loaded root identity is invalid"}


def _cache_inventory(
    path: Path,
    *,
    limit: int,
    containment_root: Path | None = None,
) -> dict[str, Any]:
    if limit < 1 or limit > 100_000:
        return {"status": "invalid", "reason": "cache file limit must be from 1 to 100000"}
    if containment_root is not None:
        try:
            root = containment_root.resolve(strict=True)
            absolute = Path(os.path.abspath(os.fspath(path)))
            relative = absolute.relative_to(root)
            if not relative.parts or ".." in relative.parts:
                raise ValueError("cache path escapes target root")
            current = root
            for part in relative.parts:
                current = current / part
                try:
                    metadata = current.lstat()
                except FileNotFoundError:
                    break
                if stat.S_ISLNK(metadata.st_mode):
                    raise ValueError("cache path contains a symlink")
            if current.exists() and not current.resolve(strict=True).is_relative_to(root):
                raise ValueError("cache path escapes target root")
        except (OSError, ValueError):
            return {"status": "unavailable", "reason": "cache root is not contained in target root"}
    if not path.exists():
        return {"status": "not_observed", "files": 0, "directories": 0, "bytes": 0, "groups": []}
    if path.is_symlink() or not path.is_dir():
        return {"status": "unavailable", "reason": "cache root is not a real directory"}
    files = 0
    directories = 1
    total = 0
    incomplete = False
    group_values: dict[str, list[int]] = {}
    stack: list[tuple[Path, int]] = [(path, 0)]
    try:
        while stack:
            current, depth = stack.pop()
            if depth > MAX_CACHE_DEPTH:
                incomplete = True
                continue
            with os.scandir(current) as entries:
                for entry in entries:
                    if entry.is_symlink():
                        continue
                    relative = Path(entry.path).relative_to(path)
                    if entry.is_dir(follow_symlinks=False):
                        directories += 1
                        if directories > MAX_CACHE_DIRECTORIES:
                            incomplete = True
                            stack.clear()
                            break
                        stack.append((Path(entry.path), depth + 1))
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    group = relative.parts[0] if relative.parts else "root"
                    counters = group_values.setdefault(group, [0, 0])
                    files += 1
                    if files > limit:
                        incomplete = True
                        stack.clear()
                        break
                    size = entry.stat(follow_symlinks=False).st_size
                    total += size
                    counters[0] += 1
                    counters[1] += size
    except OSError:
        return {"status": "unavailable", "reason": "cache traversal failed", "files": files, "bytes": total}
    ranked_groups = sorted(group_values.values(), key=lambda values: (-values[1], -values[0]))[:8]
    groups = [
        {"group": f"group-{index}", "files": values[0], "bytes": values[1]}
        for index, values in enumerate(ranked_groups, 1)
    ]
    return {
        "status": "partial" if incomplete else "observed",
        "files": min(files, limit),
        "directories": min(directories, MAX_CACHE_DIRECTORIES),
        "bytes": total,
        "groups": groups,
        "group_names_exposed": False,
        "incomplete": incomplete,
        "cleanup_performed": False,
    }


def _hook_observation(root: Path, *, run_self_test: bool) -> dict[str, Any]:
    try:
        config_value = _read_json(root, "hooks/hooks.json")
        hook_bytes = _read_root_file(root, "hooks/data_security_hook.py", max_bytes=2_097_152)
        command = 'python3 "$PLUGIN_ROOT/hooks/data_security_hook.py"'
        hooks = config_value.get("hooks") if isinstance(config_value, dict) else None
        matches: dict[str, int] = {}
        if isinstance(hooks, dict):
            for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse"):
                registrations = hooks.get(event, [])
                event_matches = 0
                for registration in registrations if isinstance(registrations, list) else []:
                    if not isinstance(registration, dict):
                        continue
                    event_matches += sum(
                        1
                        for handler in registration.get("hooks", [])
                        if isinstance(handler, dict) and handler.get("command") == command
                    )
                matches[event] = event_matches
        packaged = (
            matches == {"UserPromptSubmit": 1, "PreToolUse": 1, "PostToolUse": 1}
            and bool(hook_bytes)
        )
        result: dict[str, Any] = {
            "status": "packaged" if packaged else "invalid",
            "hook_sha256": _sha256_bytes(hook_bytes),
            "trust": "manual-review-required",
            "live_activation": "not_observed",
        }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return {"status": "unavailable", "live_activation": "not_observed"}
    if not run_self_test:
        result["control_self_test"] = "not-run"
        return result
    if root.resolve() != EXECUTING_PLUGIN_ROOT:
        result["control_self_test"] = {
            "status": "not-run",
            "reason": "target root is not the executing plugin root",
        }
        return result
    doctor = EXECUTING_PLUGIN_ROOT / "skills" / "company-data-security" / "scripts" / "doctor.py"
    if doctor.is_symlink() or not doctor.is_file():
        result["control_self_test"] = {"status": "unavailable"}
        return result
    completed = subprocess.run(
        [sys.executable, str(doctor), "--plugin-root", str(root)],
        capture_output=True,
        text=True,
        check=False,
        timeout=20,
    )
    try:
        payload = json.loads(completed.stdout)
        result["control_self_test"] = {
            "status": payload.get("status"),
            "required_failures": payload.get("required_failures"),
            "manual_gates": payload.get("manual_gates"),
        }
    except json.JSONDecodeError:
        result["control_self_test"] = {"status": "unavailable"}
    return result


def _outcome_observation(path: Path, *, containment_root: Path | None = None) -> dict[str, Any]:
    try:
        records = outcome_observation.read_records(
            path,
            missing_ok=True,
            containment_root=containment_root,
        )
        size = path.stat().st_size if path.exists() else 0
        return {
            "status": "observed" if path.exists() else "not_observed",
            "records": len(records),
            "bytes": size,
            "content": "bounded-enums-counts-only",
        }
    except (OSError, outcome_observation.OutcomeError) as exc:
        return {"status": "invalid", "reason": str(exc)}


def diagnose(args: argparse.Namespace) -> dict[str, Any]:
    root = args.plugin_root.expanduser().resolve()
    default_outcome_root = Path.cwd().resolve() if args.outcome_store is None else None
    outcome_path = Path(
        os.path.abspath(os.fspath((args.outcome_store or outcome_observation.default_path()).expanduser()))
    )
    return {
        "schema": "dev-flow.doctor.v1",
        "status": "observed",
        "source": {
            "product_state": _product_state(root),
            "git": _git_observation(root),
        },
        "runtime": {
            "installed": _installed_versions(args.codex_home),
            "loaded": _loaded_identity(root, args.loaded_plugin_root),
            "hook": _hook_observation(root, run_self_test=not args.skip_control_self_test),
        },
        "local_state": {
            "cache": _cache_inventory(
                root / ".codex" / "dev-flow",
                limit=args.max_cache_files,
                containment_root=root,
            ),
            "outcomes": _outcome_observation(
                outcome_path,
                containment_root=default_outcome_root,
            ),
        },
        "actions": {"cleanup_performed": False, "mutation_performed": False},
        "claim_limit": (
            "read-only bounded observations at check time; no live Hook/account activation, hosted state, "
            "cache safety-to-delete, delivery, or outcome effectiveness is inferred"
        ),
    }


def add_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser], *, default_root: Path) -> argparse.ArgumentParser:
    parser = subparsers.add_parser("doctor", help="Inspect source/runtime/cache/outcome truth without cleanup")
    parser.add_argument("--plugin-root", type=Path, default=default_root)
    parser.add_argument("--codex-home", type=Path)
    parser.add_argument("--loaded-plugin-root", type=Path)
    parser.add_argument("--outcome-store", type=Path)
    parser.add_argument("--max-cache-files", type=int, default=DEFAULT_MAX_CACHE_FILES)
    parser.add_argument("--skip-control-self-test", action="store_true")
    parser.set_defaults(func=command)
    return parser


def command(args: argparse.Namespace) -> int:
    try:
        payload = diagnose(args)
        print(json.dumps(payload, indent=2, sort_keys=True))
        product_status = payload["source"]["product_state"].get("status")
        hook_status = payload["runtime"]["hook"].get("status")
        return 0 if product_status == "valid" and hook_status == "packaged" else 2
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "unavailable", "error": str(exc)}, sort_keys=True))
        return 2
