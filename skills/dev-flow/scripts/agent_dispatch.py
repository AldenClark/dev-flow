#!/usr/bin/env python3
"""Deterministic Multi-Agent V2 dispatch profile selection."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import engineering_context


SCHEMA_VERSION = "1.0"
RESULT_SCHEMA_VERSION = "agent.dispatch.result.v1"
EXPECTED_PROFILES = {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "PX"}
EXPECTED_CAPABILITIES = {"E", "B", "F"}
EXPECTED_ROLES = {
    "dev-flow-explorer",
    "dev-flow-worker",
    "dev-flow-test-runner",
    "dev-flow-blue-reviewer",
    "dev-flow-red-reviewer",
    "root",
}


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
        raise DispatchContractError("dispatch registry must use the exact schema 1.0 fields")
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
    vectors: set[tuple[str, str]] = set()
    for profile_id, record in profiles.items():
        if set(record) != {"id", "capability", "reasoning_effort", "exception", "purpose"}:
            raise DispatchContractError(f"profile {profile_id} has invalid fields")
        vector = (record["capability"], record["reasoning_effort"])
        if vector[0] not in capabilities or vector[1] not in efforts or vector in vectors:
            raise DispatchContractError(f"profile {profile_id} has an invalid or duplicate vector")
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
        allowed = {"id", "any_risk", "any_signal", "minimum_capability", "minimum_effort", "reason"}
        if not set(rule).issubset(allowed) or not _nonempty(rule.get("reason")):
            raise DispatchContractError(f"upgrade rule {rule_id} has invalid fields")
        risk_values = rule.get("any_risk", [])
        signal_values = rule.get("any_signal", [])
        if not isinstance(risk_values, list) or not isinstance(signal_values, list):
            raise DispatchContractError(f"upgrade rule {rule_id} conditions must be lists")
        if len(risk_values) != len(set(risk_values)) or len(signal_values) != len(set(signal_values)):
            raise DispatchContractError(f"upgrade rule {rule_id} conditions must be unique")
        if not risk_values and not signal_values:
            raise DispatchContractError(f"upgrade rule {rule_id} requires a condition")
        if any(value not in engineering_context.RISK_TOKENS for value in risk_values):
            raise DispatchContractError(f"upgrade rule {rule_id} contains an unknown risk")
        if any(value not in signals for value in signal_values):
            raise DispatchContractError(f"upgrade rule {rule_id} contains an unknown signal")
        if "minimum_capability" in rule and rule["minimum_capability"] not in capabilities:
            raise DispatchContractError(f"upgrade rule {rule_id} has an unknown capability")
        if "minimum_effort" in rule and rule["minimum_effort"] not in efforts:
            raise DispatchContractError(f"upgrade rule {rule_id} has an unknown effort")
        if "minimum_capability" not in rule and "minimum_effort" not in rule:
            raise DispatchContractError(f"upgrade rule {rule_id} must raise capability or effort")
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


def _profile_vector(profile: dict[str, Any], registry: dict[str, Any]) -> tuple[int, int]:
    runtime = registry["runtime"]
    return (
        runtime["capabilities"][profile["capability"]]["rank"],
        runtime["efforts"][profile["reasoning_effort"]],
    )


def _least_profile(registry: dict[str, Any], minimum: tuple[int, int]) -> dict[str, Any]:
    profiles = [profile for profile in registry["profiles"] if not profile["exception"]]
    candidates = [
        profile
        for profile in profiles
        if _profile_vector(profile, registry)[0] >= minimum[0]
        and _profile_vector(profile, registry)[1] >= minimum[1]
    ]
    if not candidates:
        raise DispatchContractError(f"no non-exception profile satisfies vector {minimum}")
    return min(
        candidates,
        key=lambda profile: (
            sum(_profile_vector(profile, registry)),
            _profile_vector(profile, registry)[0],
            _profile_vector(profile, registry)[1],
            profile["id"],
        ),
    )


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
) -> dict[str, Any]:
    registry = load_registry(registry_path)
    workloads = {item["id"]: item for item in registry["workloads"]}
    profiles = {item["id"]: item for item in registry["profiles"]}
    if role not in registry["roles"]:
        raise DispatchContractError(f"unknown role {role!r}")
    if workload not in workloads:
        raise DispatchContractError(f"unknown workload {workload!r}")
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
            "fork_turns": None,
            "risks": sorted(risk_set),
            "signals": sorted(signal_set),
            "upgrade_reasons": [
                {"id": "root-only", "reason": workload_record["purpose"]}
            ],
        }

    base = profiles[workload_record["default_profile"]]
    minimum_capability, minimum_effort = _profile_vector(base, registry)
    reasons: list[dict[str, Any]] = [
        {
            "id": "workload-default",
            "reason": workload_record["purpose"],
            "profile": base["id"],
        }
    ]
    for rule in registry["upgrade_rules"]:
        matched_risks = sorted(risk_set & set(rule.get("any_risk", [])))
        matched_signals = sorted(signal_set & set(rule.get("any_signal", [])))
        if not matched_risks and not matched_signals:
            continue
        if "minimum_capability" in rule:
            minimum_capability = max(
                minimum_capability,
                registry["runtime"]["capabilities"][rule["minimum_capability"]]["rank"],
            )
        if "minimum_effort" in rule:
            minimum_effort = max(
                minimum_effort,
                registry["runtime"]["efforts"][rule["minimum_effort"]],
            )
        reasons.append(
            {
                "id": rule["id"],
                "reason": rule["reason"],
                "matched_risks": matched_risks,
                "matched_signals": matched_signals,
            }
        )
    policy_profile = _least_profile(registry, (minimum_capability, minimum_effort))
    selected = policy_profile
    source = "policy"
    if requested_profile is not None:
        if requested_profile not in profiles:
            raise DispatchContractError(f"unknown profile {requested_profile!r}")
        selected = profiles[requested_profile]
        selected_vector = _profile_vector(selected, registry)
        if selected["exception"] and not acknowledge_exception:
            raise DispatchContractError("PX requires --acknowledge-exception")
        if (
            selected_vector[0] < minimum_capability or selected_vector[1] < minimum_effort
        ) and not acknowledge_downgrade:
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
    return {
        "status": "routed",
        "schema_version": RESULT_SCHEMA_VERSION,
        "delegate": True,
        "role": role,
        "workload": workload,
        "selection_source": source,
        "default_profile": base["id"],
        "policy_profile": policy_profile["id"],
        "selected_profile": selected["id"],
        "capability": selected["capability"],
        "requested_model": capability["model"],
        "requested_reasoning_effort": selected["reasoning_effort"],
        "fork_turns": registry["runtime"]["default_fork_turns"],
        "risks": sorted(risk_set),
        "signals": sorted(signal_set),
        "upgrade_reasons": reasons,
        "runtime_fallback": "record the fallback reason and observed effective pair; inherit platform or parent selection only when safe",
    }
