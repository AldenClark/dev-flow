#!/usr/bin/env python3
"""Deterministic profile resolution and context-readiness primitives for Dev Flow."""

from __future__ import annotations

import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import tomllib
from pathlib import Path
from typing import Any, Iterable


PROFILE_SCHEMA_VERSION = "1.0"
READINESS_SCHEMA_VERSION = "1.0"
HOST_ADAPTER_VERSION = "1.0"
PROFILE_MODES = {"personal-interactive", "team-reproducible", "ci"}
READINESS_DETAILS = {"compact", "full"}
DEFAULT_PROJECT_DOC_MAX_BYTES = 32 * 1024
LAYERS = ("baseline", "personal", "team", "project", "component", "task")
LAYER_ORDER = {name: index for index, name in enumerate(LAYERS)}
PROFILE_KINDS = {"constraint", "preference", "quality-policy"}
STRENGTHS = {"must", "should", "may"}
PROFILE_STATUSES = {"draft", "trial", "active", "deprecated", "retired"}
ENTRY_STATUSES = {"applied", "shadowed", "inapplicable", "conflicting", "stale", "unknown"}
ROUTE_STATUSES = {
    "approved",
    "trial",
    "available-unassessed",
    "incompatible",
    "stale",
    "conflicting",
    "untrusted",
    "missing",
    "not-applicable",
}
TIERS = {"T0", "T1", "T2", "T3"}
GOVERNED_RISKS = {
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
    "accessibility",
}
IGNORED_DIRECTORIES = {".git", ".codex", "node_modules", "target", "dist", "build", ".venv", "__pycache__"}
CONDITION_RE = re.compile(r"^([a-z][a-z0-9_.-]*)(!?=)([^=]+)$")
SAFE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class ContractError(ValueError):
    """Raised when a profile, manifest, admission, or readiness contract is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def nonempty_regular_file(path: Path) -> bool:
    return path.is_file() and not path.is_symlink() and bool(path.read_bytes().strip())


class CodexHostAdapter:
    """Bounded adapter for Codex instruction and Skill discovery semantics."""

    def __init__(
        self,
        root: Path,
        *,
        codex_home: Path | None = None,
        working_directory: Path | None = None,
    ) -> None:
        self.root = root.resolve()
        self.codex_home = (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))).resolve()
        candidate = (working_directory or self.root).resolve()
        if candidate != self.root and not candidate.is_relative_to(self.root):
            raise ContractError(f"working directory must be the repository root or a descendant: {candidate}")
        self.working_directory = candidate if candidate.is_dir() else candidate.parent
        self.fallback_filenames: list[str] = []
        self.project_doc_max_bytes = DEFAULT_PROJECT_DOC_MAX_BYTES
        self.errors: list[str] = []
        self._load_config()

    def _load_config(self) -> None:
        path = self.codex_home / "config.toml"
        if not path.is_file():
            return
        try:
            config = read_toml(path)
        except (OSError, tomllib.TOMLDecodeError, ContractError) as exc:
            self.errors.append(f"cannot load Codex host config {path}: {exc}")
            return
        fallbacks = config.get("project_doc_fallback_filenames", [])
        if isinstance(fallbacks, list) and all(
            isinstance(item, str)
            and item.strip()
            and not Path(item.strip()).is_absolute()
            and Path(item.strip()).name == item.strip()
            and item.strip() not in {".", ".."}
            for item in fallbacks
        ):
            self.fallback_filenames = [item.strip() for item in fallbacks]
        elif "project_doc_fallback_filenames" in config:
            self.errors.append(f"{path}: project_doc_fallback_filenames must contain only non-empty filenames")
        maximum = config.get("project_doc_max_bytes", DEFAULT_PROJECT_DOC_MAX_BYTES)
        if isinstance(maximum, int) and not isinstance(maximum, bool) and maximum > 0:
            self.project_doc_max_bytes = maximum
        elif "project_doc_max_bytes" in config:
            self.errors.append(f"{path}: project_doc_max_bytes must be a positive integer")

    def _project_directories(self) -> list[Path]:
        relative = self.working_directory.relative_to(self.root)
        directories = [self.root]
        current = self.root
        for part in relative.parts:
            current = current / part
            directories.append(current)
        return directories

    def instruction_chain(self) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for name in ("AGENTS.override.md", "AGENTS.md"):
            selected = self.codex_home / name
            if nonempty_regular_file(selected):
                result.append(
                    {
                        "kind": "agents-override" if name == "AGENTS.override.md" else "agents",
                        "path": str(selected),
                        "scope": "global",
                        "hash": sha256_file(selected),
                        "bytes": selected.stat().st_size,
                    }
                )
                break
        consumed = 0
        for directory in self._project_directories():
            selected: Path | None = None
            for name in ("AGENTS.override.md", "AGENTS.md", *self.fallback_filenames):
                candidate = directory / name
                if nonempty_regular_file(candidate):
                    selected = candidate
                    break
            if selected is None:
                continue
            size = selected.stat().st_size
            if consumed + size > self.project_doc_max_bytes:
                self.errors.append(
                    f"Codex project instruction budget exhausted before {selected} "
                    f"({consumed}+{size}>{self.project_doc_max_bytes} bytes)"
                )
                break
            consumed += size
            result.append(
                {
                    "kind": "agents-override" if selected.name == "AGENTS.override.md" else "agents",
                    "path": str(selected),
                    "scope": directory.relative_to(self.root).as_posix() or ".",
                    "hash": sha256_file(selected),
                    "bytes": size,
                }
            )
        return result

    def skill_roots(self, explicit_roots: Iterable[Path] = ()) -> list[Path]:
        candidates = [
            self.codex_home / "skills",  # legacy Codex location
            *(directory / ".agents" / "skills" for directory in self._project_directories()),
            Path.home() / ".agents" / "skills",
            Path("/etc/codex/skills"),
            *explicit_roots,
        ]
        result: list[Path] = []
        seen: set[str] = set()
        for candidate in candidates:
            resolved = candidate.resolve()
            if str(resolved) not in seen:
                seen.add(str(resolved))
                result.append(resolved)
        return result

    def summary(self) -> dict[str, Any]:
        return {
            "name": "codex",
            "adapter_version": HOST_ADAPTER_VERSION,
            "working_directory": str(self.working_directory),
            "project_doc_max_bytes": self.project_doc_max_bytes,
            "project_doc_fallback_filenames": self.fallback_filenames,
            "errors": self.errors,
        }


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path}: top-level JSON value must be an object")
    return value


def read_toml(path: Path) -> dict[str, Any]:
    value = tomllib.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ContractError(f"{path}: top-level TOML value must be a table")
    return value


def require_text(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"{label} must be a non-empty string")


def require_text_list(value: Any, label: str, errors: list[str], *, allow_empty: bool = True) -> None:
    if not isinstance(value, list) or (not allow_empty and not value):
        errors.append(f"{label} must be a{' non-empty' if not allow_empty else ''} list")
        return
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{label} items must be non-empty strings")


def validate_condition(condition: str, label: str, errors: list[str]) -> None:
    if not CONDITION_RE.fullmatch(condition):
        errors.append(f"{label} must use key=value or key!=value syntax: {condition!r}")


def validate_profile_data(data: dict[str, Any], *, source: str = "profile") -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        errors.append(f"{source}: unsupported schema_version {data.get('schema_version')!r}")
    for field in ("id", "layer", "owner", "version", "status"):
        require_text(data.get(field), f"{source}.{field}", errors)
    if data.get("layer") not in LAYER_ORDER:
        errors.append(f"{source}.layer must be one of {list(LAYERS)}")
    if data.get("status") not in PROFILE_STATUSES:
        errors.append(f"{source}.status must be one of {sorted(PROFILE_STATUSES)}")
    profile_id = data.get("id")
    if isinstance(profile_id, str) and not SAFE_NAME_RE.fullmatch(profile_id):
        errors.append(f"{source}.id contains unsupported characters")
    preferences = data.get("preferences", [])
    if not isinstance(preferences, list):
        return [*errors, f"{source}.preferences must be a list"]
    seen: set[str] = set()
    for index, entry in enumerate(preferences):
        label = f"{source}.preferences[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be a table")
            continue
        for field in ("key", "kind", "strength", "rationale", "exception_policy", "review_trigger"):
            require_text(entry.get(field), f"{label}.{field}", errors)
        key = entry.get("key")
        if isinstance(key, str):
            if key in seen:
                errors.append(f"{label}.key duplicates {key!r} in the same profile")
            seen.add(key)
        if entry.get("kind") not in PROFILE_KINDS:
            errors.append(f"{label}.kind must be one of {sorted(PROFILE_KINDS)}")
        if entry.get("strength") not in STRENGTHS:
            errors.append(f"{label}.strength must be one of {sorted(STRENGTHS)}")
        for field in ("applies_when", "avoid_when", "alternatives", "required_evidence", "required_capabilities", "fallbacks"):
            if field in entry:
                require_text_list(entry[field], f"{label}.{field}", errors)
                if field in {"applies_when", "avoid_when"} and isinstance(entry[field], list):
                    for condition in entry[field]:
                        if isinstance(condition, str):
                            validate_condition(condition, f"{label}.{field}", errors)
        if entry.get("kind") == "quality-policy":
            if "outcome" not in entry:
                errors.append(f"{label}.outcome is required for quality-policy")
            else:
                require_text(entry.get("outcome"), f"{label}.outcome", errors)
            coverage = [entry.get("required_evidence"), entry.get("required_capabilities"), entry.get("fallbacks")]
            if not any(isinstance(item, list) and item for item in coverage):
                errors.append(f"{label} must declare required_evidence, required_capabilities, or fallbacks")
        elif "value" not in entry:
            errors.append(f"{label}.value is required for {entry.get('kind')!r}")
    return errors


def load_profile(path: Path) -> dict[str, Any]:
    try:
        data = read_toml(path)
    except (OSError, tomllib.TOMLDecodeError, ContractError) as exc:
        raise ContractError(f"cannot load profile {path}: {exc}") from exc
    errors = validate_profile_data(data, source=str(path))
    if errors:
        raise ContractError("; ".join(errors))
    return data


def validate_manifest_data(data: dict[str, Any], *, source: str = "manifest") -> list[str]:
    errors: list[str] = []
    if data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        errors.append(f"{source}: unsupported schema_version {data.get('schema_version')!r}")
    if "include_personal" in data and not isinstance(data["include_personal"], bool):
        errors.append(f"{source}.include_personal must be a boolean")
    sources = data.get("profile_sources", [])
    if not isinstance(sources, list):
        return [*errors, f"{source}.profile_sources must be a list"]
    seen: set[str] = set()
    for index, item in enumerate(sources):
        label = f"{source}.profile_sources[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be a table")
            continue
        for field in ("id", "path", "layer"):
            require_text(item.get(field), f"{label}.{field}", errors)
        if item.get("layer") not in {"team", "project", "component"}:
            errors.append(f"{label}.layer must be team, project, or component")
        source_id = item.get("id")
        if isinstance(source_id, str):
            if source_id in seen:
                errors.append(f"{label}.id duplicates {source_id!r}")
            seen.add(source_id)
        for field in ("scope",):
            if field in item:
                require_text_list(item[field], f"{label}.{field}", errors, allow_empty=False)
        if "required" in item and not isinstance(item["required"], bool):
            errors.append(f"{label}.required must be a boolean")
        digest = item.get("digest")
        if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)):
            errors.append(f"{label}.digest must be sha256:<64 lowercase hex characters>")
    return errors


def condition_matches(condition: str, facts: dict[str, set[str]]) -> bool:
    match = CONDITION_RE.fullmatch(condition)
    if not match:
        return False
    key, operator, expected = match.groups()
    values = facts.get(key, set())
    matched = expected in values or any(fnmatch.fnmatch(value, expected) for value in values)
    return matched if operator == "=" else not matched


def entry_applies(entry: dict[str, Any], facts: dict[str, set[str]]) -> tuple[bool, str]:
    applies = entry.get("applies_when", [])
    avoids = entry.get("avoid_when", [])
    if applies and not all(condition_matches(item, facts) for item in applies):
        return False, "applies_when did not match the task facts"
    if any(condition_matches(item, facts) for item in avoids):
        return False, "avoid_when matched the task facts"
    return True, "applicable"


def source_in_scope(scopes: list[str], paths: list[str]) -> bool:
    if not scopes:
        return True
    if not paths:
        return any(scope in {"*", "**", "**/*"} for scope in scopes)
    def matches(path: str, scope: str) -> bool:
        if fnmatch.fnmatch(path, scope):
            return True
        if scope.endswith("/**"):
            prefix = scope[:-3].rstrip("/")
            return path == prefix or path.startswith(prefix + "/")
        return False

    return any(matches(path, scope) for path in paths for scope in scopes)


def path_relevant(relative: Path, selected_paths: Iterable[str]) -> bool:
    selected = [Path(item).as_posix().strip("/") for item in selected_paths if item]
    if not selected or len(relative.parts) == 1 or (relative.parts and relative.parts[0] in {".github", ".gitlab"}):
        return True
    candidate = relative.as_posix()
    return any(
        candidate == item
        or candidate.startswith(item + "/")
        or item.startswith(candidate.rstrip("/") + "/")
        or fnmatch.fnmatch(candidate, item)
        for item in selected
    )


def safe_repository_source(root: Path, raw_path: str) -> Path:
    base = (root / ".dev-flow").resolve()
    candidate = (base / raw_path).resolve()
    if candidate != base and not candidate.is_relative_to(base):
        raise ContractError(f"profile source escapes {base}: {raw_path}")
    return candidate


def discover_profile_sources(
    root: Path,
    *,
    codex_home: Path | None = None,
    task_paths: Iterable[str] = (),
    baseline: Path | None = None,
    task_profiles: Iterable[Path] = (),
    profile_mode: str = "personal-interactive",
) -> tuple[list[dict[str, Any]], list[str], Path | None]:
    root = root.resolve()
    paths = [Path(item).as_posix().lstrip("./") for item in task_paths]
    errors: list[str] = []
    if profile_mode not in PROFILE_MODES:
        raise ContractError(f"profile mode must be one of {sorted(PROFILE_MODES)}")
    sources: list[dict[str, Any]] = []
    if baseline and baseline.is_file():
        sources.append({"path": baseline.resolve(), "layer": "baseline", "scope": [], "required": True})
    manifest_path = root / ".dev-flow" / "preferences.toml"
    manifest: dict[str, Any] = {}
    if manifest_path.is_file():
        if manifest_path.is_symlink():
            errors.append(f"preference manifest must not be a symlink: {manifest_path}")
        else:
            try:
                manifest = read_toml(manifest_path)
                manifest_errors = validate_manifest_data(manifest, source=str(manifest_path))
                errors.extend(manifest_errors)
            except (OSError, tomllib.TOMLDecodeError, ContractError) as exc:
                errors.append(f"cannot load manifest {manifest_path}: {exc}")
    include_personal = profile_mode == "personal-interactive" and (manifest.get("include_personal", True) if not errors else False)
    effective_codex_home = (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))).resolve()
    if include_personal:
        personal_dir = effective_codex_home / "dev-flow" / "profiles"
        if personal_dir.is_dir():
            for path in sorted(personal_dir.glob("*.toml")):
                if path.is_file() and not path.is_symlink():
                    sources.append({"path": path.resolve(), "layer": "personal", "scope": [], "required": False})
    if manifest and not errors:
        for item in manifest.get("profile_sources", []):
            scopes = list(item.get("scope", []))
            if source_in_scope(scopes, paths):
                try:
                    path = safe_repository_source(root, item["path"])
                except ContractError as exc:
                    errors.append(str(exc))
                    continue
                sources.append(
                    {
                        "path": path,
                        "layer": item["layer"],
                        "scope": scopes,
                        "required": item.get("required", True),
                        "digest": item.get("digest"),
                        "source_id": item["id"],
                    }
                )
    implicit_project = root / ".dev-flow" / "profiles" / "project.toml"
    if implicit_project.is_file() and all(source["path"] != implicit_project.resolve() for source in sources):
        sources.append({"path": implicit_project.resolve(), "layer": "project", "scope": [], "required": False})
    for path in task_profiles:
        sources.append({"path": path.resolve(), "layer": "task", "scope": paths, "required": True})
    return sources, errors, manifest_path if manifest_path.is_file() else None


def normalize_facts(values: Iterable[str], paths: Iterable[str]) -> dict[str, set[str]]:
    facts: dict[str, set[str]] = {"path": {Path(path).as_posix().lstrip("./") for path in paths}}
    for raw in values:
        match = CONDITION_RE.fullmatch(raw)
        if not match or match.group(2) != "=":
            raise ContractError(f"fact must use key=value syntax: {raw!r}")
        key, _, value = match.groups()
        facts.setdefault(key, set()).add(value)
    return facts


def decision_exceptions(root: Path) -> list[dict[str, Any]]:
    directory = root / ".dev-flow" / "decisions"
    result: list[dict[str, Any]] = []
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("PREF-*.json")):
        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError, ContractError):
            continue
        expires_at = data.get("expires_at")
        expiry_valid = False
        if isinstance(expires_at, str):
            try:
                expiry = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                expiry_valid = expiry.tzinfo is not None and expiry > dt.datetime.now(dt.timezone.utc)
            except ValueError:
                pass
        if (
            data.get("schema_version") == "1.0"
            and data.get("status") == "active"
            and isinstance(data.get("id"), str)
            and isinstance(data.get("approved_by"), str)
            and isinstance(data.get("keys"), list)
            and isinstance(data.get("scope"), list)
            and isinstance(data.get("reason"), str)
            and isinstance(data.get("residual_risk"), str)
            and expiry_valid
        ):
            result.append({**data, "source": str(path), "source_hash": sha256_file(path)})
    return result


def has_exception(entry: dict[str, Any], exceptions: list[dict[str, Any]], task_paths: list[str]) -> bool:
    exception_id = entry.get("exception_id")
    if not isinstance(exception_id, str):
        return False
    return any(
        item.get("id") == exception_id
        and entry.get("key") in item.get("keys", [])
        and source_in_scope(item.get("scope", []), task_paths)
        for item in exceptions
    )


def resolve_profiles(
    root: Path,
    *,
    facts: Iterable[str] = (),
    task_paths: Iterable[str] = (),
    codex_home: Path | None = None,
    baseline: Path | None = None,
    task_profiles: Iterable[Path] = (),
    profile_mode: str = "personal-interactive",
) -> dict[str, Any]:
    root = root.resolve()
    paths = [Path(path).as_posix().lstrip("./") for path in task_paths]
    normalized_facts = normalize_facts(facts, paths)
    sources, discovery_errors, manifest_path = discover_profile_sources(
        root,
        codex_home=codex_home,
        task_paths=paths,
        baseline=baseline,
        task_profiles=task_profiles,
        profile_mode=profile_mode,
    )
    source_records: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    errors = list(discovery_errors)
    for source in sources:
        path = source["path"]
        if not path.is_file():
            if source.get("required", True):
                errors.append(f"required profile does not exist: {path}")
            continue
        if path.is_symlink():
            errors.append(f"profile sources must not be symlinks: {path}")
            continue
        digest = sha256_file(path)
        if source.get("digest") and source["digest"] != digest:
            errors.append(f"profile digest mismatch for {path}")
            continue
        try:
            profile = load_profile(path)
        except ContractError as exc:
            errors.append(str(exc))
            continue
        if profile["layer"] != source["layer"]:
            errors.append(f"{path}: declared layer {profile['layer']!r} does not match source layer {source['layer']!r}")
            continue
        source_records.append(
            {
                "id": profile["id"],
                "path": str(path),
                "hash": digest,
                "layer": profile["layer"],
                "owner": profile["owner"],
                "version": profile["version"],
                "status": profile["status"],
                "scope": source.get("scope", []),
            }
        )
        if profile["status"] not in {"trial", "active"}:
            continue
        for index, raw_entry in enumerate(profile.get("preferences", [])):
            entry = dict(raw_entry)
            applicable, reason = entry_applies(entry, normalized_facts)
            entries.append(
                {
                    **entry,
                    "profile_id": profile["id"],
                    "layer": profile["layer"],
                    "owner": profile["owner"],
                    "source": str(path),
                    "source_hash": digest,
                    "source_index": index,
                    "status": "unknown" if applicable else "inapplicable",
                    "status_reason": reason,
                }
            )
    exceptions = decision_exceptions(root)
    winners: list[dict[str, Any]] = []
    conflicts: list[dict[str, Any]] = []
    applicable_by_key: dict[str, list[dict[str, Any]]] = {}
    for entry in entries:
        if entry["status"] == "unknown":
            applicable_by_key.setdefault(entry["key"], []).append(entry)
    for key in sorted(applicable_by_key):
        candidates = applicable_by_key[key]
        candidates.sort(key=lambda item: (LAYER_ORDER[item["layer"]], item["profile_id"], item["source_index"]))
        highest_layer = max(LAYER_ORDER[item["layer"]] for item in candidates)
        highest = [item for item in candidates if LAYER_ORDER[item["layer"]] == highest_layer]
        highest_values = {canonical_json(item.get("value", item.get("outcome"))) for item in highest}
        lower_must = [
            item
            for item in candidates
            if item.get("strength") == "must"
            and canonical_json(item.get("value", item.get("outcome"))) not in highest_values
        ]
        exception_authorized = any(has_exception(item, exceptions, paths) for item in highest)
        if len(highest_values) > 1 or (lower_must and not exception_authorized):
            for item in candidates:
                item["status"] = "conflicting"
                item["status_reason"] = "same-layer disagreement or an applicable must was not explicitly excepted"
            conflicts.append(
                {
                    "key": key,
                    "reason": "same-layer disagreement" if len(highest_values) > 1 else "must conflict without authorized exception",
                    "candidates": [
                        {field: item.get(field) for field in ("profile_id", "layer", "owner", "value", "outcome", "strength", "source")}
                        for item in candidates
                    ],
                }
            )
            continue
        winner = highest[-1]
        winner["status"] = "applied"
        winner["status_reason"] = "highest applicable layer"
        for item in candidates:
            if item is not winner:
                item["status"] = "shadowed"
                item["status_reason"] = f"shadowed by {winner['profile_id']} at layer {winner['layer']}"
        winners.append({key_name: winner.get(key_name) for key_name in winner if key_name not in {"status_reason"}})
    stable_input = {
        "profile_mode": profile_mode,
        "sources": source_records,
        "facts": {key: sorted(value) for key, value in sorted(normalized_facts.items())},
        "winners": winners,
        "conflicts": conflicts,
        "exceptions": exceptions,
        "errors": errors,
    }
    fingerprint = sha256_bytes(canonical_json(stable_input).encode("utf-8"))
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "profile_mode": profile_mode,
        "repository_root": str(root),
        "manifest": str(manifest_path) if manifest_path else None,
        "facts": stable_input["facts"],
        "sources": source_records,
        "entries": entries,
        "winners": winners,
        "conflicts": conflicts,
        "exceptions": exceptions,
        "mismatches": [],
        "errors": errors,
        "fingerprint": fingerprint,
        "outcome": "blocked" if conflicts or errors else "resolved",
    }


def iter_repository_files(root: Path, *, limit: int = 20000) -> Iterable[Path]:
    count = 0
    for directory, names, filenames in os.walk(root):
        names[:] = sorted(name for name in names if name not in IGNORED_DIRECTORIES)
        base = Path(directory)
        for filename in sorted(filenames):
            path = base / filename
            if path.is_symlink():
                continue
            yield path
            count += 1
            if count >= limit:
                return


def detect_languages(root: Path, task_paths: Iterable[str] = (), inventory: Iterable[Path] | None = None) -> list[str]:
    selected = [Path(path).as_posix().lstrip("./") for path in task_paths]
    repository_files = list(inventory) if inventory is not None else list(iter_repository_files(root))
    candidates = [path for path in repository_files if path_relevant(path.relative_to(root), selected)]
    mapping = {
        ".rs": "rust",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".js": "javascript",
        ".jsx": "javascript",
        ".swift": "swift",
        ".kt": "kotlin",
        ".kts": "kotlin",
        ".py": "python",
        ".go": "go",
        ".java": "java",
        ".sql": "sql",
    }
    languages = {mapping[path.suffix.lower()] for path in candidates if path.suffix.lower() in mapping}
    manifest_languages = {
        "Cargo.toml": "rust",
        "package.json": "typescript",
        "Package.swift": "swift",
        "build.gradle": "kotlin",
        "build.gradle.kts": "kotlin",
        "pyproject.toml": "python",
        "go.mod": "go",
    }
    for filename, language in manifest_languages.items():
        if any(path.name == filename for path in candidates):
            languages.add(language)
    return sorted(languages)


def detect_frameworks(root: Path, task_paths: Iterable[str] = (), inventory: Iterable[Path] | None = None) -> list[str]:
    """Detect only framework facts backed by canonical project manifests."""
    selected = [Path(path).as_posix().lstrip("./") for path in task_paths]
    frameworks: set[str] = set()
    repository_files = list(inventory) if inventory is not None else list(iter_repository_files(root))
    for path in sorted(item for item in repository_files if item.name == "package.json"):
        relative = path.relative_to(root)
        if any(part in IGNORED_DIRECTORIES for part in relative.parts):
            continue
        if not path_relevant(relative, selected):
            continue
        try:
            package = read_json(path)
        except (OSError, json.JSONDecodeError, ContractError):
            continue
        dependencies: set[str] = set()
        for field in ("dependencies", "devDependencies", "peerDependencies"):
            table = package.get(field, {})
            if isinstance(table, dict):
                dependencies.update(str(name) for name in table)
        if "react" in dependencies or "next" in dependencies:
            frameworks.add("react")
        if "vue" in dependencies or "nuxt" in dependencies:
            frameworks.add("vue")
        if "svelte" in dependencies or "@sveltejs/kit" in dependencies:
            frameworks.add("svelte")
    return sorted(frameworks)


def discover_native_controls(
    root: Path,
    task_paths: Iterable[str] = (),
    inventory: Iterable[Path] | None = None,
) -> list[dict[str, str]]:
    patterns = {
        "compiler": ("Cargo.toml", "pyproject.toml", "go.mod", "Package.swift", "tsconfig.json"),
        "formatter": ("rustfmt.toml", ".rustfmt.toml", ".prettierrc", ".prettierrc.json", "biome.json", "ruff.toml"),
        "linter": ("clippy.toml", ".clippy.toml", "eslint.config.js", "eslint.config.mjs", ".eslintrc", "biome.json", "ruff.toml"),
        "tests": ("pytest.ini", "vitest.config.ts", "jest.config.js", "Package.swift", "Cargo.toml"),
        "ci": (".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml"),
        "security": ("deny.toml", ".semgrep.yml", ".github/dependabot.yml", ".github/codeql"),
        "commands": ("Makefile", "justfile", "Taskfile.yml", "package.json", "pyproject.toml"),
    }
    repository_files = list(inventory) if inventory is not None else list(iter_repository_files(root))
    controls: list[dict[str, str]] = []
    for kind, names in patterns.items():
        for name in names:
            direct = root / name
            candidates = [direct] if direct.is_dir() and not direct.is_symlink() else []
            candidates.extend(path for path in repository_files if path.name == Path(name).name)
            for path in sorted(set(candidates)):
                relative = path.relative_to(root)
                if any(part in IGNORED_DIRECTORIES for part in relative.parts) or not path_relevant(relative, task_paths):
                    continue
                controls.append({"kind": kind, "path": relative.as_posix()})
                break
    unique = {(item["kind"], item["path"]): item for item in controls}
    return [unique[key] for key in sorted(unique)]


def discover_agent_instructions(
    root: Path,
    task_paths: Iterable[str] = (),
    codex_home: Path | None = None,
    *,
    working_directory: Path | None = None,
) -> list[dict[str, Any]]:
    """Compatibility wrapper; Codex resolves project instructions from the effective CWD."""
    del task_paths
    return CodexHostAdapter(root, codex_home=codex_home, working_directory=working_directory).instruction_chain()


def parse_skill_frontmatter(path: Path) -> dict[str, str]:
    skill_file = path / "SKILL.md"
    if not skill_file.is_file():
        return {}
    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    _, frontmatter, _ = text.split("---", 2)
    result: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"\'')
    return result


def discover_skills(skill_roots: Iterable[Path]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for root in skill_roots:
        root = root.resolve()
        if not root.is_dir():
            continue
        for directory in sorted(root.glob("*/")):
            metadata = parse_skill_frontmatter(directory)
            name = metadata.get("name")
            if not name or (name, str(directory.resolve())) in seen:
                continue
            seen.add((name, str(directory.resolve())))
            result.append(
                {
                    "name": name,
                    "description": metadata.get("description", ""),
                    "path": str(directory.resolve()),
                    "digest": sha256_file(directory / "SKILL.md"),
                }
            )
    return result


def load_capability_registry(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if data.get("schema_version") != "1.0" or not isinstance(data.get("capabilities"), list):
        raise ContractError(f"invalid capability registry: {path}")
    seen: set[str] = set()
    for index, capability in enumerate(data["capabilities"]):
        label = f"{path}: capabilities[{index}]"
        if not isinstance(capability, dict):
            raise ContractError(f"{label} must be an object")
        capability_id = capability.get("id")
        if not isinstance(capability_id, str) or not capability_id:
            raise ContractError(f"{label}.id must be a non-empty string")
        if capability_id in seen:
            raise ContractError(f"{label}.id duplicates {capability_id!r}")
        seen.add(capability_id)
        if not isinstance(capability.get("outcome"), str) or not capability["outcome"]:
            raise ContractError(f"{label}.outcome must be a non-empty string")
        for field in ("selectors", "native_evidence", "route_names"):
            value = capability.get(field, [])
            if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
                raise ContractError(f"{label}.{field} must be a list of non-empty strings")
        for selector in capability.get("selectors", []):
            if not CONDITION_RE.fullmatch(selector):
                raise ContractError(f"{label}.selectors contains invalid selector {selector!r}")
        preferred = capability.get("preferred_route")
        if preferred is not None and preferred not in capability.get("route_names", []):
            raise ContractError(f"{label}.preferred_route must occur in route_names")
        if not isinstance(capability.get("manual_fallback"), str) or not capability["manual_fallback"]:
            raise ContractError(f"{label}.manual_fallback must be a non-empty string")
        if "contextual_review_required" in capability and not isinstance(capability["contextual_review_required"], bool):
            raise ContractError(f"{label}.contextual_review_required must be a boolean")
    return data


def load_admissions(paths: Iterable[Path]) -> tuple[list[dict[str, Any]], list[str]]:
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for path in paths:
        if not path.is_file():
            continue
        try:
            data = read_json(path)
        except (OSError, json.JSONDecodeError, ContractError) as exc:
            errors.append(f"cannot load capability admissions {path}: {exc}")
            continue
        if data.get("schema_version") != "1.0":
            errors.append(f"{path}: unsupported schema_version {data.get('schema_version')!r}")
            continue
        if not isinstance(data.get("host"), str) or not data["host"].strip():
            errors.append(f"{path}: host must be a non-empty string")
            continue
        if not data["host"].lower().startswith("codex"):
            errors.append(f"{path}: admissions target {data['host']!r}, not the active Codex host")
            continue
        if not isinstance(data.get("admissions"), list):
            errors.append(f"{path}: admissions must be a list")
            continue
        for index, record in enumerate(data.get("admissions", [])):
            if not isinstance(record, dict):
                errors.append(f"{path}: admissions[{index}] must be an object")
                continue
            if record.get("status") not in ROUTE_STATUSES:
                errors.append(f"{path}: admissions[{index}] has invalid status")
                continue
            missing = [
                field
                for field in ("skill", "owner", "reviewed_at", "recheck_trigger")
                if not isinstance(record.get(field), str) or not record[field].strip()
            ]
            capability_ids = record.get("capability_ids")
            if not isinstance(capability_ids, list) or not capability_ids or any(not isinstance(item, str) or not item for item in capability_ids):
                missing.append("capability_ids")
            if missing:
                errors.append(f"{path}: admissions[{index}] missing valid {', '.join(missing)}")
                continue
            digest = record.get("digest")
            if digest is not None and (not isinstance(digest, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)):
                errors.append(f"{path}: admissions[{index}] has invalid digest")
                continue
            try:
                reviewed_at = dt.datetime.fromisoformat(record["reviewed_at"].replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{path}: admissions[{index}] has invalid reviewed_at")
                continue
            if reviewed_at.tzinfo is None:
                errors.append(f"{path}: admissions[{index}].reviewed_at must include a timezone")
                continue
            scope = record.get("scope", [])
            if not isinstance(scope, list) or any(not isinstance(item, str) or not item for item in scope):
                errors.append(f"{path}: admissions[{index}].scope must be a list of non-empty strings")
                continue
            records.append({**record, "source": str(path), "source_hash": sha256_file(path)})
    return records, errors


def select_tier(task_type: str, risks: set[str], explicit: str | None = None) -> tuple[str, list[str]]:
    if explicit:
        if explicit not in TIERS:
            raise ContractError(f"tier must be one of {sorted(TIERS)}")
        return explicit, ["explicit-tier"]
    if risks & GOVERNED_RISKS or task_type in {"migration", "security", "release-hotfix", "rollback"}:
        return "T3", sorted({*(risks & GOVERNED_RISKS), task_type})
    if task_type in {"large-feature", "large-refactor", "dependency-change", "performance"}:
        return "T2", [task_type]
    if task_type in {"spike", "read-only-audit"}:
        return "T0", [task_type]
    return "T1", [task_type]


def capability_applies(capability: dict[str, Any], facts: dict[str, set[str]]) -> bool:
    selectors = capability.get("selectors", [])
    return not selectors or all(condition_matches(selector, facts) for selector in selectors)


def load_suppression(root: Path, fingerprint: str, tier: str) -> tuple[dict[str, Any] | None, list[str]]:
    path = root / ".dev-flow" / "suppressions.json"
    if not path.is_file():
        return None, []
    try:
        data = read_json(path)
    except (OSError, json.JSONDecodeError, ContractError) as exc:
        return None, [f"cannot load readiness suppressions {path}: {exc}"]
    if data.get("schema_version") != "1.0" or not isinstance(data.get("suppressions"), list):
        return None, [f"{path}: expected schema_version 1.0 and a suppressions list"]
    now = dt.datetime.now(dt.timezone.utc)
    for index, record in enumerate(reversed(data["suppressions"])):
        if not isinstance(record, dict) or record.get("fingerprint") != fingerprint:
            continue
        tiers = record.get("tiers", [])
        if tiers and (not isinstance(tiers, list) or tier not in tiers):
            continue
        if not all(isinstance(record.get(field), str) and record[field].strip() for field in ("owner", "reason")):
            return None, [f"{path}: matching suppression is missing owner or reason"]
        expires_at = record.get("expires_at")
        if expires_at:
            try:
                expiry = dt.datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            except ValueError:
                return None, [f"{path}: matching suppression has invalid expires_at"]
            if expiry.tzinfo is None or expiry <= now:
                continue
        return {**record, "source": str(path), "record_index_from_end": index}, []
    return None, []


def select_packet_waiver(metadata: dict[str, Any], blockers: list[str], task_paths: list[str]) -> dict[str, Any] | None:
    records = metadata.get("approvals", {}).get("waivers", [])
    if not isinstance(records, list):
        return None
    now = dt.datetime.now(dt.timezone.utc)
    for record in reversed(records):
        if not isinstance(record, dict):
            continue
        scope = record.get("scope")
        covered = record.get("blockers")
        if not isinstance(scope, list) or not scope or not source_in_scope(scope, task_paths):
            continue
        if not isinstance(covered, list) or not blockers or not all(item in covered or "*" in covered for item in blockers):
            continue
        if not all(isinstance(record.get(field), str) and record[field].strip() for field in ("by", "note", "residual_risk", "recheck_trigger")):
            continue
        try:
            expires_at = dt.datetime.fromisoformat(str(record.get("expires_at", "")).replace("Z", "+00:00"))
        except ValueError:
            continue
        if expires_at.tzinfo is None or expires_at <= now:
            continue
        return record
    return None


def evidence_matches(
    root: Path,
    patterns: Iterable[str],
    task_paths: Iterable[str] = (),
    inventory: Iterable[Path] | None = None,
    *,
    relevant_only: bool = True,
) -> list[str]:
    matches: list[str] = []
    repository_files = list(inventory) if inventory is not None else list(iter_repository_files(root))
    for pattern in patterns:
        for path in repository_files:
            relative = path.relative_to(root)
            if fnmatch.fnmatch(relative.as_posix(), pattern) and (not relevant_only or path_relevant(relative, task_paths)):
                matches.append(relative.as_posix())
    return sorted(set(matches))


def assess_context(
    root: Path,
    *,
    task_type: str,
    risks: Iterable[str] = (),
    task_paths: Iterable[str] = (),
    facts: Iterable[str] = (),
    tier: str | None = None,
    codex_home: Path | None = None,
    skill_roots: Iterable[Path] = (),
    capability_registry: Path,
    task_profiles: Iterable[Path] = (),
    packet: Path | None = None,
    profile_mode: str = "personal-interactive",
    working_directory: Path | None = None,
    detail: str = "compact",
) -> dict[str, Any]:
    root = root.resolve()
    if detail not in READINESS_DETAILS:
        raise ContractError(f"readiness detail must be one of {sorted(READINESS_DETAILS)}")
    paths = [Path(path).as_posix().lstrip("./") for path in task_paths]
    fact_values = list(facts)
    risk_set = set(risks)
    selected_tier, tier_reasons = select_tier(task_type, risk_set, tier)
    inventory = list(iter_repository_files(root, limit=20001))
    inventory_truncated = len(inventory) > 20000
    if inventory_truncated:
        inventory = inventory[:20000]
    languages = set(detect_languages(root, paths, inventory))
    frameworks = set(detect_frameworks(root, paths, inventory))
    combined_facts = [
        *fact_values,
        *(f"language={language}" for language in sorted(languages)),
        *(f"framework={framework}" for framework in sorted(frameworks)),
        *(f"risk={risk}" for risk in sorted(risk_set)),
    ]
    baseline = Path(__file__).resolve().parents[1] / "references" / "neutral-baseline.toml"
    preferences = resolve_profiles(
        root,
        facts=combined_facts,
        task_paths=paths,
        codex_home=codex_home,
        baseline=baseline,
        task_profiles=task_profiles,
        profile_mode=profile_mode,
    )
    host = CodexHostAdapter(root, codex_home=codex_home, working_directory=working_directory)
    instructions = host.instruction_chain()
    controls = discover_native_controls(root, paths, inventory)
    default_skill_roots = [Path(__file__).resolve().parents[2]]
    skills = discover_skills([*default_skill_roots, *host.skill_roots(skill_roots)])
    installed_by_name = {item["name"]: item for item in skills}
    admissions, admission_errors = load_admissions(
        [
            (codex_home or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))) / "dev-flow" / "capabilities.json",
            root / ".dev-flow" / "capabilities.json",
        ]
    )
    registry = load_capability_registry(capability_registry)
    registry_source = {
        "kind": "capability-registry",
        "path": str(capability_registry.resolve()),
        "hash": sha256_file(capability_registry),
    }
    quality_policies = [winner for winner in preferences["winners"] if winner.get("kind") == "quality-policy"]
    capability_facts = {"language": languages, "framework": frameworks, "risk": risk_set}
    routes: list[dict[str, Any]] = []
    obligations: list[dict[str, Any]] = []
    uncovered: list[dict[str, Any]] = []
    route_conflicts: list[dict[str, Any]] = []
    for capability in registry["capabilities"]:
        if not capability_applies(capability, capability_facts):
            continue
        native = evidence_matches(root, capability.get("native_evidence", []), paths, inventory, relevant_only=False)
        task_native = evidence_matches(root, capability.get("native_evidence", []), paths, inventory, relevant_only=True)
        matching_routes: list[dict[str, Any]] = []
        for route_name in capability.get("route_names", []):
            admission = next(
                (
                    item
                    for item in reversed(admissions)
                    if item.get("skill") == route_name and capability["id"] in item.get("capability_ids", [])
                    and source_in_scope(item.get("scope", []), paths)
                ),
                None,
            )
            installed = installed_by_name.get(route_name)
            status = admission.get("status") if admission else "available-unassessed" if installed else "missing"
            if admission and status in {"approved", "trial"}:
                if not installed:
                    status = "missing"
                elif admission.get("digest") and admission["digest"] != installed.get("digest"):
                    status = "stale"
            matching_routes.append(
                {
                    "capability_id": capability["id"],
                    "skill": route_name,
                    "status": status,
                    "installed": bool(installed),
                    "path": installed.get("path") if installed else None,
                    "digest": installed.get("digest") if installed else None,
                    "admission_source": admission.get("source") if admission else None,
                    "admission_source_hash": admission.get("source_hash") if admission else None,
                    "admission_reviewed_at": admission.get("reviewed_at") if admission else None,
                    "admission_recheck_trigger": admission.get("recheck_trigger") if admission else None,
                }
            )
        approved = [route for route in matching_routes if route["status"] == "approved" and route["installed"]]
        if len(approved) > 1:
            preferred = capability.get("preferred_route")
            preferred_routes = [route for route in approved if route["skill"] == preferred] if preferred else []
            if preferred_routes:
                approved = preferred_routes
            else:
                route_conflicts.append({"capability_id": capability["id"], "routes": [route["skill"] for route in approved]})
                approved = approved[:1]
        selected_route = approved[0] if approved else None
        routes.extend(matching_routes)
        policy_fallbacks = sorted(
            {
                fallback
                for policy in quality_policies
                if policy.get("layer") in {"team", "project", "component", "task"}
                if capability["id"] in policy.get("required_capabilities", [])
                for fallback in policy.get("fallbacks", [])
            }
        )
        contextual_review_required = capability.get("contextual_review_required", False)
        if native and contextual_review_required and selected_route:
            coverage = "native-plus-approved-specialist"
        elif native and contextual_review_required and policy_fallbacks:
            coverage = "native-plus-owned-policy-fallback"
        elif native and contextual_review_required:
            coverage = "uncovered"
        elif native:
            coverage = "native-control"
        elif selected_route:
            coverage = "approved-specialist"
        elif policy_fallbacks:
            coverage = "owned-policy-fallback"
        else:
            coverage = "uncovered"
        obligation = {
            "id": capability["id"],
            "outcome": capability["outcome"],
            "required_for": capability.get("required_for", "applicable-task"),
            "coverage": coverage,
            "native_evidence": native,
            "task_native_evidence": task_native,
            "task_mapping": "mapped" if task_native else "verification-required" if native else "absent",
            "selected_route": selected_route,
            "policy_fallbacks": policy_fallbacks,
            "contextual_review_required": contextual_review_required,
            "manual_fallback": capability.get("manual_fallback"),
        }
        obligations.append(obligation)
        if coverage == "uncovered":
            uncovered.append(obligation)
    obligation_by_id = {item["id"]: item for item in obligations}
    available_evidence = {
        value
        for control in controls
        for value in (control["kind"], control["path"], Path(control["path"]).name)
    }
    explicit_fact_map = normalize_facts(fact_values, paths)
    available_evidence.update(explicit_fact_map.get("evidence", set()))
    policy_assessments: list[dict[str, Any]] = []
    uncovered_policies: list[dict[str, Any]] = []
    for policy in quality_policies:
        if policy.get("layer") not in {"team", "project", "component", "task"}:
            continue
        required_evidence = policy.get("required_evidence", [])
        missing_evidence = [
            requirement
            for requirement in required_evidence
            if not any(fnmatch.fnmatch(candidate, requirement) or fnmatch.fnmatch(requirement, candidate) for candidate in available_evidence)
        ]
        required_capabilities = policy.get("required_capabilities", [])
        missing_capabilities = [
            capability_id
            for capability_id in required_capabilities
            if capability_id not in obligation_by_id or obligation_by_id[capability_id]["coverage"] == "uncovered"
        ]
        fallbacks = policy.get("fallbacks", [])
        if not missing_evidence and not missing_capabilities:
            coverage = "satisfied"
        elif fallbacks:
            coverage = "owned-policy-fallback"
        else:
            coverage = "uncovered"
        assessment = {
            "key": policy["key"],
            "strength": policy["strength"],
            "outcome": policy["outcome"],
            "layer": policy["layer"],
            "owner": policy["owner"],
            "coverage": coverage,
            "missing_evidence": missing_evidence,
            "missing_capabilities": missing_capabilities,
            "fallbacks": fallbacks,
            "source": policy["source"],
            "source_hash": policy["source_hash"],
        }
        policy_assessments.append(assessment)
        if coverage == "uncovered":
            uncovered_policies.append(assessment)
    checks: list[dict[str, Any]] = [
        {
            "dimension": "repository-identity",
            "requirement": "repository-root",
            "status": "observed" if (root / ".git").exists() else "missing",
            "evidence": [str(root)],
            "importance": "required",
        },
        {
            "dimension": "instructions",
            "requirement": "scoped-instruction-chain",
            "status": "observed" if instructions else "absent-optional",
            "evidence": [item["path"] for item in instructions],
            "importance": "advisory",
        },
        {
            "dimension": "repository-native-operations",
            "requirement": "build-test-lint-controls",
            "status": "observed" if controls else "missing",
            "evidence": [item["path"] for item in controls],
            "importance": "required" if selected_tier in {"T2", "T3"} else "advisory",
        },
        {
            "dimension": "repository-inventory",
            "requirement": "bounded-relevant-file-inventory",
            "status": "truncated" if inventory_truncated else "observed",
            "evidence": [f"files-inspected={len(inventory)}"],
            "importance": "required" if selected_tier in {"T2", "T3"} else "advisory",
        },
    ]
    blockers: list[str] = []
    recommendations: list[dict[str, Any]] = []
    if preferences["conflicts"] or preferences["errors"]:
        blockers.append("profile-conflict-or-invalid-source")
    if not controls and selected_tier != "T0":
        recommendations.append({"id": "native-operations", "action": "derive or confirm repository-native build/test/lint commands"})
    if inventory_truncated and selected_tier != "T0":
        recommendations.append({"id": "inventory-scope", "action": "narrow task paths or explicitly confirm facts beyond the 20,000-file bounded inventory"})
    governed_uncovered = [item for item in uncovered if selected_tier == "T3" and (risk_set & GOVERNED_RISKS)]
    governed_policy_uncovered = [
        item
        for item in uncovered_policies
        if selected_tier == "T3" and item["strength"] == "must"
    ]
    if governed_uncovered or governed_policy_uncovered:
        blockers.append("governed-quality-outcome-uncovered")
    elif (uncovered or uncovered_policies) and selected_tier in {"T1", "T2"}:
        recommendations.append({"id": "quality-coverage", "action": "confirm native, admitted specialist, or qualified manual coverage for applicable gaps"})
    if route_conflicts:
        blockers.append("approved-route-collision")
    waiver: dict[str, Any] | None = None
    if packet and (packet / "packet.json").is_file():
        try:
            metadata = read_json(packet / "packet.json")
            waiver = select_packet_waiver(metadata, blockers, paths)
        except (OSError, json.JSONDecodeError, ContractError):
            pass
    if selected_tier == "T0":
        blockers = []
        recommendations = []
        waiver = None
        outcome = "not_applicable"
    elif blockers and waiver:
        outcome = "waived"
    elif blockers:
        outcome = "blocked" if selected_tier == "T3" else "checkpoint"
    elif recommendations:
        outcome = "checkpoint" if selected_tier in {"T2", "T3"} else "partial_advisory"
    else:
        outcome = "not_applicable" if selected_tier == "T0" else "ready"
    stable_input = {
        "tier": selected_tier,
        "tier_reasons": tier_reasons,
        "scope": {
            "root": str(root),
            "paths": paths,
            "languages": sorted(languages),
            "frameworks": sorted(frameworks),
            "risks": sorted(risk_set),
        },
        "instructions": instructions,
        "controls": controls,
        "inventory_truncated": inventory_truncated,
        "preference_fingerprint": preferences["fingerprint"],
        "capability_registry": registry_source,
        "obligations": obligations,
        "routes": routes,
        "blockers": blockers,
        "recommendations": recommendations,
        "admission_errors": admission_errors,
    }
    fingerprint = sha256_bytes(canonical_json(stable_input).encode("utf-8"))
    suppression, suppression_errors = load_suppression(root, fingerprint, selected_tier)
    admission_errors.extend(host.errors)
    admission_errors.extend(suppression_errors)
    full_quality_coverage = {
        "obligations": obligations,
        "policies": quality_policies,
        "policy_assessments": policy_assessments,
        "routes": routes,
        "uncovered": uncovered,
        "uncovered_policies": uncovered_policies,
        "conflicts": route_conflicts,
    }
    compact_quality_coverage = {
        "obligations": [
            {
                "id": item["id"],
                "coverage": item["coverage"],
                "task_mapping": item["task_mapping"],
                "selected_skill": item["selected_route"]["skill"] if item["selected_route"] else None,
            }
            for item in obligations
        ],
        "policies": [{"key": item["key"], "coverage": item["coverage"]} for item in policy_assessments],
        "uncovered": [item["id"] for item in uncovered],
        "uncovered_policies": [item["key"] for item in uncovered_policies],
        "conflicts": route_conflicts,
    }
    result = {
        "schema_version": READINESS_SCHEMA_VERSION,
        "detail": detail,
        "host": host.summary(),
        "tier": selected_tier,
        "tier_reasons": tier_reasons,
        "outcome": outcome,
        "scope": {
            "roots": [str(root)],
            "paths": paths,
            "languages": sorted(languages),
            "frameworks": sorted(frameworks),
            "artifact_roles": [],
            "risks": sorted(risk_set),
        },
        "sources": [registry_source, *instructions, *({"kind": "profile", **item} for item in preferences["sources"])],
        "checks": checks,
        "recommendations": recommendations,
        "conflicts": [*preferences["conflicts"], *route_conflicts],
        "quality_coverage": full_quality_coverage if detail == "full" else compact_quality_coverage,
        "waiver": waiver,
        "suppression": suppression,
        "fingerprint": fingerprint,
        "recheck_triggers": ["task-tier-change", "scope-change", "profile-or-instruction-hash-change", "admission-change", "waiver-expiry"],
        "profile": {
            "mode": profile_mode,
            "fingerprint": preferences["fingerprint"],
            "outcome": preferences["outcome"],
            "winner_keys": [item["key"] for item in preferences["winners"]],
            "source_hashes": [item["hash"] for item in preferences["sources"]],
            "conflict_count": len(preferences["conflicts"]),
            "error_count": len(preferences["errors"]),
        },
        "errors": admission_errors,
        "blockers": blockers,
    }
    if detail == "full":
        result["profile_snapshot"] = preferences
    return result


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
