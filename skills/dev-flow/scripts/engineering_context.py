#!/usr/bin/env python3
"""Deterministic engineering-profile resolution and risk vocabulary for Dev Flow."""

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

from path_contracts import PathContractError, contained_path


PROFILE_SCHEMA_VERSION = "1.0"
PROFILE_MODES = {"personal-interactive", "team-reproducible", "ci"}
LAYERS = ("baseline", "personal", "team", "project", "component", "task")
LAYER_ORDER = {name: index for index, name in enumerate(LAYERS)}
PROFILE_KINDS = {"constraint", "preference", "quality-policy"}
STRENGTHS = {"must", "should", "may"}
PROFILE_STATUSES = {"draft", "trial", "active", "deprecated", "retired"}
PERSONAL_PROFILE_PROVENANCE = "explicit-user"
PERSONAL_CORRECTION_POLICY = "edit-or-retire-profile"
PERSONAL_DELETION_POLICY = "delete-profile-file"
RISK_TOKENS = {
    "abi",
    "accessibility",
    "architecture",
    "authentication",
    "authorization",
    "backpressure",
    "battery",
    "binary-size",
    "browser",
    "cancellation",
    "ci-cd",
    "compatibility",
    "concurrency",
    "data-deletion",
    "dependency",
    "deployment",
    "device",
    "distributed-state",
    "entitlement",
    "external-write",
    "ffi",
    "flaky-baseline",
    "idempotency",
    "incomplete-reproduction",
    "large-blast-radius",
    "memory",
    "migration",
    "native-packaging",
    "ordering",
    "os",
    "performance",
    "persisted-data",
    "platform-lifecycle",
    "privacy",
    "production-config",
    "protocol",
    "public-api",
    "recovery",
    "regulated",
    "release",
    "resource-limits",
    "rollback",
    "schema",
    "secrets",
    "security",
    "signing",
    "simulator",
    "slo",
    "startup",
    "toolchain",
    "unfamiliar-subsystem",
    "unsafe",
    "untrusted-input",
    "version-compatibility",
    "weak-tests",
}
CONDITION_RE = re.compile(r"^([a-z][a-z0-9_.-]*)(!?=)(.+)$")
SAFE_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,127}$")


class ContractError(ValueError):
    """Raised when a profile or manifest contract is invalid."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(value: bytes) -> str:
    return "sha256:" + hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


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
    match = CONDITION_RE.fullmatch(condition)
    if not match or match.group(3).startswith("="):
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
    if data.get("layer") == "personal":
        if data.get("provenance") != PERSONAL_PROFILE_PROVENANCE:
            errors.append(
                f"{source}.provenance must be {PERSONAL_PROFILE_PROVENANCE!r}; inferred or imported preferences cannot be durable personal policy"
            )
        require_text_list(data.get("scope"), f"{source}.scope", errors, allow_empty=False)
        require_text(data.get("expires_at"), f"{source}.expires_at", errors)
        expires_at = data.get("expires_at")
        if isinstance(expires_at, str) and expires_at.strip():
            try:
                expiry = dt.datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"{source}.expires_at must be a timezone-aware ISO timestamp")
            else:
                if expiry.tzinfo is None or expiry <= dt.datetime.now(dt.timezone.utc):
                    errors.append(f"{source}.expires_at must be a future timezone-aware timestamp")
        if data.get("correction_policy") != PERSONAL_CORRECTION_POLICY:
            errors.append(f"{source}.correction_policy must be {PERSONAL_CORRECTION_POLICY!r}")
        if data.get("deletion_policy") != PERSONAL_DELETION_POLICY:
            errors.append(f"{source}.deletion_policy must be {PERSONAL_DELETION_POLICY!r}")
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


def safe_repository_source(root: Path, raw_path: str) -> Path:
    base = root / ".dev-flow"
    try:
        return contained_path(
            base,
            raw_path,
            label="profile source",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        raise ContractError(str(exc)) from exc


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
        sources.append(
            {
                "path": baseline.resolve(),
                "layer": "baseline",
                "scope": [],
                "required": True,
                "provenance": "public-baseline",
            }
        )
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
        if personal_dir.is_symlink():
            errors.append(f"personal profile directory must not be a symlink: {personal_dir}")
        elif personal_dir.is_dir():
            for path in sorted(personal_dir.glob("*.toml")):
                if path.is_file() and not path.is_symlink():
                    sources.append(
                        {
                            "path": path.resolve(),
                            "layer": "personal",
                            "scope": [],
                            "required": False,
                            "provenance": PERSONAL_PROFILE_PROVENANCE,
                        }
                    )
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
                        "provenance": "repository-manifest",
                    }
                )
    try:
        implicit_project = contained_path(
            root / ".dev-flow",
            "profiles/project.toml",
            label="implicit project profile",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        errors.append(str(exc))
    else:
        if implicit_project.is_file() and all(source["path"] != implicit_project for source in sources):
            sources.append(
                {
                    "path": implicit_project,
                    "layer": "project",
                    "scope": [],
                    "required": False,
                    "provenance": "repository-implicit",
                }
            )
    for path in task_profiles:
        sources.append(
            {
                "path": path.resolve(),
                "layer": "task",
                "scope": paths,
                "required": True,
                "provenance": "explicit-task-profile",
            }
        )
    return sources, errors, manifest_path if manifest_path.is_file() else None


def normalize_facts(values: Iterable[str], paths: Iterable[str]) -> dict[str, set[str]]:
    facts: dict[str, set[str]] = {"path": {Path(path).as_posix().lstrip("./") for path in paths}}
    for raw in values:
        match = CONDITION_RE.fullmatch(raw)
        if not match or match.group(2) != "=" or match.group(3).startswith("="):
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
        effective_scope = list(profile.get("scope", [])) if profile["layer"] == "personal" else list(source.get("scope", []))
        effective_provenance = (
            PERSONAL_PROFILE_PROVENANCE
            if profile["layer"] == "personal"
            else str(source.get("provenance", "unknown"))
        )
        in_scope = source_in_scope(effective_scope, paths)
        source_records.append(
            {
                "id": profile["id"],
                "path": str(path),
                "hash": digest,
                "layer": profile["layer"],
                "owner": profile["owner"],
                "version": profile["version"],
                "status": profile["status"],
                "scope": effective_scope,
                "provenance": effective_provenance,
                "expires_at": profile.get("expires_at"),
                "correction_policy": profile.get("correction_policy"),
                "deletion_policy": profile.get("deletion_policy"),
                "resolution_status": "eligible" if in_scope else "out-of-scope",
            }
        )
        if profile["status"] not in {"trial", "active"} or not in_scope:
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
                    "provenance": effective_provenance,
                    "profile_scope": effective_scope,
                    "expires_at": profile.get("expires_at"),
                    "correction_policy": profile.get("correction_policy"),
                    "deletion_policy": profile.get("deletion_policy"),
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
            match = CONDITION_RE.fullmatch(selector)
            if not match or match.group(3).startswith("="):
                raise ContractError(f"{label}.selectors contains invalid selector {selector!r}")
        preferred = capability.get("preferred_route")
        if preferred is not None and preferred not in capability.get("route_names", []):
            raise ContractError(f"{label}.preferred_route must occur in route_names")
        if not isinstance(capability.get("manual_fallback"), str) or not capability["manual_fallback"]:
            raise ContractError(f"{label}.manual_fallback must be a non-empty string")
        if "contextual_review_required" in capability and not isinstance(capability["contextual_review_required"], bool):
            raise ContractError(f"{label}.contextual_review_required must be a boolean")
    return data


def canonical_risks(risks: Iterable[str]) -> set[str]:
    values = set(risks)
    invalid = sorted(value for value in values if value not in RISK_TOKENS)
    if invalid:
        raise ContractError(
            f"unknown risk token(s): {', '.join(invalid)}; use canonical values from the risk contract"
        )
    return values


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
