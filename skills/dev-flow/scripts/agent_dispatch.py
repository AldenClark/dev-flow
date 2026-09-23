#!/usr/bin/env python3
"""Deterministic Multi-Agent V2 dispatch profile selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import engineering_context


SCHEMA_VERSION = "1.1"
RESULT_SCHEMA_VERSION = "agent.dispatch.result.v1"
EXPECTED_PROFILES = {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "PX"}
EXPECTED_CAPABILITIES = {"E", "B", "F"}
EXPECTED_MODELS = {"E": "gpt-6-luna", "B": "gpt-6-sol", "F": "gpt-6-astra"}
ORDERED_PROFILES = ("P0", "P1", "P2", "P3", "P4", "P5", "P6", "PX")
EXPECTED_PROFILE_VECTORS = {
    "P0": ("E", "low"),
    "P1": ("E", "medium"),
    "P2": ("E", "high"),
    "P3": ("E", "xhigh"),
    "P4": ("B", "medium"),
    "P5": ("B", "xhigh"),
    "P6": ("F", "xhigh"),
    "PX": ("F", "max"),
}
EXPECTED_ROLES = {
    "dev-flow-explorer",
    "dev-flow-worker",
    "dev-flow-test-runner",
    "dev-flow-blue-reviewer",
    "dev-flow-red-reviewer",
    "root",
}
TASK_STRUCTURES = {"independent", "sequential", "coupled"}
TOOL_DENSITIES = {"low", "high"}


class DispatchContractError(ValueError):
    """Raised when the dispatch registry or request is invalid."""


def default_registry_path() -> Path:
    return Path(__file__).resolve().parents[1] / "references" / "agent-dispatch-profiles.json"


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _unique_records(records: Any, *, field: str, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list) or not records:
        raise DispatchContractError(f"{label} must be a non-empty list")
    indexed: dict[str, dict[str, Any]] = {}
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not _nonempty(record.get(field)):
            raise DispatchContractError(f"{label}[{index}] requires non-empty {field}")
        key = record[field]
        if key in indexed:
            raise DispatchContractError(f"duplicate {label} {key}")
        indexed[key] = record
    return indexed


def validate_registry(registry: Any) -> dict[str, Any]:
    if not isinstance(registry, dict) or set(registry) != {
        "schema_version",
        "policy",
        "runtime",
        "profiles",
        "roles",
        "workloads",
        "signal_vocabulary",
        "upgrade_rules",
    }:
        raise DispatchContractError("dispatch registry must use the exact schema 1.1 fields")
    if registry.get("schema_version") != SCHEMA_VERSION or not _nonempty(registry.get("policy")):
        raise DispatchContractError("dispatch registry has invalid schema_version or policy")

    runtime = registry.get("runtime")
    if not isinstance(runtime, dict) or set(runtime) != {
        "minimum_codex",
        "default_fork_turns",
        "capabilities",
        "efforts",
    }:
        raise DispatchContractError("runtime must define minimum_codex, default_fork_turns, capabilities, and efforts")
    if not _nonempty(runtime.get("minimum_codex")) or runtime.get("default_fork_turns") != "none":
        raise DispatchContractError("runtime requires a minimum Codex version and default fork_turns=none")
    capabilities = runtime.get("capabilities")
    if not isinstance(capabilities, dict) or set(capabilities) != EXPECTED_CAPABILITIES:
        raise DispatchContractError("runtime capabilities must be exactly E, B, and F")
    capability_ranks: set[int] = set()
    models: set[str] = set()
    for capability, record in capabilities.items():
        if not isinstance(record, dict) or set(record) != {"rank", "model", "purpose"}:
            raise DispatchContractError(f"capability {capability} has invalid fields")
        if not isinstance(record["rank"], int) or record["rank"] < 0:
            raise DispatchContractError(f"capability {capability} rank must be a non-negative integer")
        if record["rank"] in capability_ranks or not _nonempty(record["model"]) or record["model"] in models:
            raise DispatchContractError("capability ranks and models must be unique")
        if not _nonempty(record["purpose"]):
            raise DispatchContractError(f"capability {capability} purpose must be non-empty")
        if record["model"] != EXPECTED_MODELS[capability]:
            raise DispatchContractError(f"capability {capability} must use the active GPT-6 model")
        capability_ranks.add(record["rank"])
        models.add(record["model"])
    if capability_ranks != {0, 1, 2}:
        raise DispatchContractError("capability ranks must be exactly 0, 1, and 2")

    efforts = runtime.get("efforts")
    if not isinstance(efforts, dict) or set(efforts) != {"low", "medium", "high", "xhigh", "max"}:
        raise DispatchContractError("runtime efforts must be exactly low, medium, high, xhigh, and max")
    if set(efforts.values()) != {0, 1, 2, 3, 4} or any(not isinstance(value, int) for value in efforts.values()):
        raise DispatchContractError("runtime effort ranks must be unique integers 0 through 4")

    profiles = _unique_records(registry.get("profiles"), field="id", label="profiles")
    if set(profiles) != EXPECTED_PROFILES:
        raise DispatchContractError("profiles must be exactly P0 through P6 plus PX")
    if [profile["id"] for profile in registry["profiles"]] != list(ORDERED_PROFILES):
        raise DispatchContractError("profiles must be ordered P0 through P6 plus PX")
    vectors: set[tuple[str, str]] = set()
    for profile_id, record in profiles.items():
        if set(record) != {"id", "capability", "reasoning_effort", "exception", "purpose"}:
            raise DispatchContractError(f"profile {profile_id} has invalid fields")
        vector = (record["capability"], record["reasoning_effort"])
        if vector[0] not in capabilities or vector[1] not in efforts or vector in vectors:
            raise DispatchContractError(f"profile {profile_id} has an invalid or duplicate vector")
        if vector != EXPECTED_PROFILE_VECTORS[profile_id]:
            raise DispatchContractError(f"profile {profile_id} must use its active GPT-6 capability/effort vector")
        if not isinstance(record["exception"], bool) or not _nonempty(record["purpose"]):
            raise DispatchContractError(f"profile {profile_id} has invalid exception or purpose")
        if record["exception"] != (profile_id == "PX"):
            raise DispatchContractError("PX must be the only exception profile")
        vectors.add(vector)

    roles = registry.get("roles")
    if not isinstance(roles, list) or set(roles) != EXPECTED_ROLES or len(roles) != len(EXPECTED_ROLES):
        raise DispatchContractError("roles must define every supported role exactly once")
    workloads = _unique_records(registry.get("workloads"), field="id", label="workloads")
    for workload_id, record in workloads.items():
        if set(record) != {"id", "roles", "delegate", "default_profile", "purpose"}:
            raise DispatchContractError(f"workload {workload_id} has invalid fields")
        workload_roles = record["roles"]
        if not isinstance(workload_roles, list) or not workload_roles or len(workload_roles) != len(set(workload_roles)):
            raise DispatchContractError(f"workload {workload_id} roles must be a unique non-empty list")
        if any(role not in EXPECTED_ROLES for role in workload_roles) or not isinstance(record["delegate"], bool):
            raise DispatchContractError(f"workload {workload_id} has invalid roles or delegate flag")
        if record["delegate"]:
            if record["default_profile"] not in profiles or profiles[record["default_profile"]]["exception"]:
                raise DispatchContractError(f"workload {workload_id} requires a non-exception default profile")
            if "root" in workload_roles:
                raise DispatchContractError("delegated workloads cannot use the root role")
        elif workload_roles != ["root"] or record["default_profile"] is not None:
            raise DispatchContractError("non-delegated workload must be root-only with no profile")
        if not _nonempty(record["purpose"]):
            raise DispatchContractError(f"workload {workload_id} purpose must be non-empty")

    signals = registry.get("signal_vocabulary")
    if not isinstance(signals, list) or not signals or len(signals) != len(set(signals)) or any(not _nonempty(item) for item in signals):
        raise DispatchContractError("signal_vocabulary must be a unique non-empty string list")
    rules = _unique_records(registry.get("upgrade_rules"), field="id", label="upgrade_rules")
    for rule_id, rule in rules.items():
        allowed = {
            "id",
            "any_signal",
            "all_signals",
            "minimum_profile",
            "reason",
        }
        if not set(rule).issubset(allowed) or not _nonempty(rule.get("reason")):
            raise DispatchContractError(f"upgrade rule {rule_id} has invalid fields")
        any_signals = rule.get("any_signal")
        all_signals = rule.get("all_signals")
        if (any_signals is None) == (all_signals is None):
            raise DispatchContractError(f"upgrade rule {rule_id} needs exactly one signal condition")
        condition = any_signals if any_signals is not None else all_signals
        if not isinstance(condition, list) or not condition or len(condition) != len(set(condition)):
            raise DispatchContractError(f"upgrade rule {rule_id} conditions must be unique non-empty lists")
        if any(value not in signals for value in condition):
            raise DispatchContractError(f"upgrade rule {rule_id} contains an unknown signal")
        if rule.get("minimum_profile") not in profiles or rule["minimum_profile"] == "PX":
            raise DispatchContractError(f"upgrade rule {rule_id} needs a non-exception minimum profile")
        if rule["minimum_profile"] == "P6" and (
            all_signals is None or len(all_signals) < 2 or "deep-unresolved" not in all_signals
        ):
            raise DispatchContractError(f"upgrade rule {rule_id} requires compound unresolved reasoning for P6")
    return registry


def load_registry(path: Path | None = None) -> dict[str, Any]:
    target = (path or default_registry_path()).resolve()
    if not target.is_file() or target.is_symlink():
        raise DispatchContractError(f"dispatch registry must be a regular file: {target}")
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatchContractError(f"cannot read dispatch registry: {exc}") from exc
    return validate_registry(payload)


def _profile_rank(profile_id: str) -> int:
    return ORDERED_PROFILES.index(profile_id)


def _host_capability_result(
    registry: dict[str, Any], selected: dict[str, Any], host_capabilities: Iterable[tuple[str, str]] | None
) -> dict[str, Any]:
    if host_capabilities is None:
        return {
            "status": "not_checked",
            "reason": "check the actual host model and effort before dispatch",
            "suggested_profile": None,
        }
    try:
        available = set(host_capabilities)
    except TypeError as exc:
        raise DispatchContractError("host capabilities require MODEL:EFFORT pairs") from exc
    efforts = registry["runtime"]["efforts"]
    for pair in available:
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise DispatchContractError("host capabilities require MODEL:EFFORT pairs")
        model, effort = pair
        if not _nonempty(model) or effort not in efforts:
            raise DispatchContractError("host capabilities require MODEL:EFFORT with a supported effort")
    capabilities = registry["runtime"]["capabilities"]
    requested = (capabilities[selected["capability"]]["model"], selected["reasoning_effort"])
    if requested in available:
        return {"status": "available", "reason": "requested model and effort observed on host", "suggested_profile": None}
    alternatives = [
        profile for profile in registry["profiles"]
        if not profile["exception"]
        and _profile_rank(profile["id"]) >= _profile_rank(selected["id"])
        and (capabilities[profile["capability"]]["model"], profile["reasoning_effort"]) in available
    ]
    suggested = min(alternatives, key=lambda item: _profile_rank(item["id"])) if alternatives else None
    return {
        "status": "capability_limit",
        "reason": "requested model or effort is unavailable on the observed host; do not dispatch this route",
        "suggested_profile": suggested["id"] if suggested else None,
        "suggested_model": capabilities[suggested["capability"]]["model"] if suggested else None,
        "suggested_reasoning_effort": suggested["reasoning_effort"] if suggested else None,
    }


def route_agent(
    *,
    role: str,
    workload: str,
    risks: Iterable[str] = (),
    signals: Iterable[str] = (),
    requested_profile: str | None = None,
    acknowledge_exception: bool = False,
    acknowledge_downgrade: bool = False,
    registry_path: Path | None = None,
    task_structure: str = "independent",
    parallel_units: int = 1,
    tool_density: str = "low",
    host_capabilities: Iterable[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    workloads = {item["id"]: item for item in registry["workloads"]}
    profiles = {item["id"]: item for item in registry["profiles"]}
    if role not in registry["roles"]:
        raise DispatchContractError(f"unknown role {role!r}")
    if workload not in workloads:
        raise DispatchContractError(f"unknown workload {workload!r}")
    if task_structure not in TASK_STRUCTURES:
        raise DispatchContractError(f"unknown task structure {task_structure!r}")
    if tool_density not in TOOL_DENSITIES:
        raise DispatchContractError(f"unknown tool density {tool_density!r}")
    if isinstance(parallel_units, bool) or not isinstance(parallel_units, int) or not 1 <= parallel_units <= 8:
        raise DispatchContractError("parallel units must be an integer from 1 to 8")
    workload_record = workloads[workload]
    if role not in workload_record["roles"]:
        raise DispatchContractError(f"role {role!r} is incompatible with workload {workload!r}")
    risk_set = engineering_context.canonical_risks(risks)
    signal_set = set(signals)
    unknown_signals = sorted(signal_set - set(registry["signal_vocabulary"]))
    if unknown_signals:
        raise DispatchContractError(f"unknown dispatch signal(s): {', '.join(unknown_signals)}")
    if not workload_record["delegate"]:
        if requested_profile is not None or acknowledge_exception or acknowledge_downgrade:
            raise DispatchContractError("root-only decisions cannot request a child dispatch profile")
        return {
            "status": "routed",
            "schema_version": RESULT_SCHEMA_VERSION,
            "delegate": False,
            "role": role,
            "workload": workload,
            "selection_source": "root-only",
            "default_profile": None,
            "selected_profile": None,
            "requested_model": None,
            "requested_reasoning_effort": None,
            "dispatch_ready": False,
            "fork_turns": None,
            "risks": sorted(risk_set),
            "signals": sorted(signal_set),
            "dispatch_precondition": {
                "task_structure": task_structure,
                "parallel_units": parallel_units,
                "tool_density": tool_density,
                "qualified": False,
                "reason": "root-owned decision",
            },
            "upgrade_reasons": [
                {"id": "root-only", "reason": workload_record["purpose"]}
            ],
        }

    if task_structure in {"sequential", "coupled"}:
        if requested_profile is not None or acknowledge_exception or acknowledge_downgrade:
            raise DispatchContractError("non-delegated sequential/coupled work cannot request a child profile")
        return {
            "status": "routed",
            "schema_version": RESULT_SCHEMA_VERSION,
            "delegate": False,
            "role": role,
            "workload": workload,
            "selection_source": "root-sequential" if task_structure == "sequential" else "root-coupled",
            "default_profile": workload_record["default_profile"],
            "selected_profile": None,
            "requested_model": None,
            "requested_reasoning_effort": None,
            "dispatch_ready": False,
            "fork_turns": None,
            "risks": sorted(risk_set),
            "signals": sorted(signal_set),
            "dispatch_precondition": {
                "task_structure": task_structure,
                "parallel_units": parallel_units,
                "tool_density": tool_density,
                "qualified": False,
                "reason": "sequential or coupled steps do not form an independently useful child unit",
            },
            "upgrade_reasons": [
                {
                    "id": "single-owner-structure",
                    "reason": "task shape requires one owner; size and tool density do not authorize agent multiplication",
                }
            ],
        }

    base = profiles[workload_record["default_profile"]]
    minimum_profile = base["id"]
    reasons: list[dict[str, Any]] = [
        {
            "id": "workload-default",
            "reason": workload_record["purpose"],
            "profile": base["id"],
        }
    ]
    for rule in registry["upgrade_rules"]:
        any_signals = set(rule.get("any_signal", []))
        all_signals = set(rule.get("all_signals", []))
        matched_signals = sorted(signal_set & (any_signals or all_signals))
        if any_signals and not matched_signals:
            continue
        if all_signals and not all_signals.issubset(signal_set):
            continue
        if _profile_rank(rule["minimum_profile"]) > _profile_rank(minimum_profile):
            minimum_profile = rule["minimum_profile"]
        reasons.append(
            {
                "id": rule["id"],
                "reason": rule["reason"],
                "matched_signals": matched_signals,
            }
        )
    policy_profile = profiles[minimum_profile]
    selected = policy_profile
    source = "policy"
    if requested_profile is not None:
        if requested_profile not in profiles:
            raise DispatchContractError(f"unknown profile {requested_profile!r}")
        selected = profiles[requested_profile]
        if selected["exception"] and not acknowledge_exception:
            raise DispatchContractError("PX requires --acknowledge-exception")
        if _profile_rank(requested_profile) < _profile_rank(minimum_profile) and not acknowledge_downgrade:
            raise DispatchContractError(
                f"requested profile {requested_profile} is below policy profile {policy_profile['id']}; "
                "use --acknowledge-downgrade to make the downgrade explicit"
            )
        source = "explicit-profile"
        reasons.append(
            {
                "id": "explicit-profile",
                "reason": "explicit profile request overrides the policy result with required acknowledgements",
                "profile": requested_profile,
                "policy_profile": policy_profile["id"],
            }
        )
    capability = registry["runtime"]["capabilities"][selected["capability"]]
    host_capability = _host_capability_result(registry, selected, host_capabilities)
    return {
        "status": "capability_limit" if host_capability["status"] == "capability_limit" else "routed",
        "schema_version": RESULT_SCHEMA_VERSION,
        "delegate": host_capability["status"] == "available",
        "role": role,
        "workload": workload,
        "selection_source": source,
        "default_profile": base["id"],
        "policy_profile": policy_profile["id"],
        "selected_profile": selected["id"],
        "capability": selected["capability"],
        "requested_model": capability["model"],
        "requested_reasoning_effort": selected["reasoning_effort"],
        "dispatch_ready": host_capability["status"] == "available",
        "fork_turns": registry["runtime"]["default_fork_turns"],
        "risks": sorted(risk_set),
        "signals": sorted(signal_set),
        "host_capability": host_capability,
        "dispatch_precondition": {
            "task_structure": task_structure,
            "parallel_units": parallel_units,
            "tool_density": tool_density,
            "qualified": True,
            "reason": "caller identified an independently useful child unit",
        },
        "upgrade_reasons": reasons,
        "runtime_fallback": "verify model and effort on the actual host before dispatch; if unavailable, report the capability limit in the current task result without silent substitution",
    }
