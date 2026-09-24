#!/usr/bin/env python3
"""Stdlib-only runtime for Dev Flow."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any, Iterable

import agent_dispatch
import engineering_context
import flow_metrics
import knowledge_system
import methodology_system
import outcome_observation
import resource_coordination
import route_incremental
import runtime_doctor
import workstream_contract
from path_contracts import PathContractError, atomic_write_text, contained_path


MIN_CODEX = (0, 147, 0)
GOVERNED_MAX_ACTIVE_CHILDREN = 6
DEFAULT_INITIAL_ACTIVE_CHILDREN = 2
READ_ONLY_BREADTH_INITIAL_ACTIVE_CHILDREN = 3
ORDINARY_ACTIVE_CHILD_SOFT_LIMIT = 3
DEFAULT_CAPACITY_RAMP_STEP = 1
EXECUTION_MODES = {"direct", "managed"}
TASK_INTENTS = {"research", "diagnose", "design", "change", "review", "delivery"}
LEGACY_INTENT_ALIASES = {"research-audit": "review"}
ACCEPTED_TASK_INTENTS = TASK_INTENTS | set(LEGACY_INTENT_ALIASES)
ROUTE_INTENT_ALIASES = {"diagnosis": "diagnose"}
LEGACY_TASK_INTENTS = {
    "micro": "change",
    "routine": "change",
    "bugfix": "change",
    "large-feature": "change",
    "large-refactor": "change",
    "migration": "change",
    "security": "change",
    "performance": "change",
    "release-hotfix": "delivery",
    "read-only-audit": "review",
    "spike": "design",
    "dependency-change": "change",
    "rollback": "delivery",
}
INTENT_METHOD_TASK_TYPES = {
    "research": "spike",
    "diagnose": "bugfix",
    "design": "routine",
    "change": "routine",
    "review": "read-only-audit",
    "delivery": "release-hotfix",
}
ROUTE_KNOWLEDGE_IMPACTS = {"none", "current-truth", "change-record"}
ROUTE_UNKNOWNS = {
    "architecture",
    "compatibility",
    "data",
    "delivery",
    "dependency",
    "diagnosis",
    "review",
    "security",
    "ui",
}
ROUTE_OVERLAYS = {
    "external-system",
    "irreversible",
    "migration",
    "release",
    "security",
    "ui-product",
}
REQUIREMENT_CLASSES = {
    "semantic-change",
    "structural-adjustment",
    "defect-correction",
    "mechanical",
    "read-only",
}
REQUIREMENT_CLASS_ALIASES = {
    "U1": "semantic-change",
    "U2": "structural-adjustment",
    "U3": "defect-correction",
    "U4": "mechanical",
    "U5": "read-only",
}
ROUTE_NEEDS = {
    "requirements",
    "knowledge",
    "architecture",
    "dependency",
    "diagnosis",
    "verification",
    "review",
    "test-system",
    "delivery",
}
ROUTE_NEED_ALIASES = {
    "requirements-design": "requirements",
    "repository-knowledge": "knowledge",
    "architecture-decisions": "architecture",
    "dependency-decisions": "dependency",
    "systematic-debugging": "diagnosis",
    "change-review": "review",
    "test-system-engineering": "test-system",
    "delivery-readiness": "delivery",
}
UI_IMPACTS = {"none", "preserve", "material"}
TASK_TYPES = {
    "micro",
    "routine",
    "bugfix",
    "large-feature",
    "large-refactor",
    "migration",
    "security",
    "performance",
    "release-hotfix",
    "read-only-audit",
    "spike",
    "dependency-change",
    "rollback",
}
ARCHITECTURE_ROUTING_RISKS = {
    "abi",
    "architecture",
    "backpressure",
    "cancellation",
    "compatibility",
    "concurrency",
    "distributed-state",
    "ffi",
    "idempotency",
    "memory",
    "migration",
    "native-packaging",
    "ordering",
    "performance",
    "persisted-data",
    "platform-lifecycle",
    "protocol",
    "public-api",
    "recovery",
    "resource-limits",
    "schema",
    "unsafe",
    "version-compatibility",
}
DIAGNOSIS_ROUTING_RISKS = {"flaky-baseline", "incomplete-reproduction"}
METHOD_ACTIVATION_RISKS = {
    "abi",
    "authorization",
    "concurrency",
    "data-deletion",
    "distributed-state",
    "ffi",
    "migration",
    "ordering",
    "persisted-data",
    "privacy",
    "protocol",
    "public-api",
    "regulated",
    "rollback",
    "schema",
    "security",
    "unsafe",
    "version-compatibility",
    "weak-tests",
}
METHOD_ACTIVATION_SIGNALS = {
    "complex-rules",
    "conflicting-evidence",
    "cross-participant-flow",
    "model-evaluation",
    "multi-version-coexistence",
    "oracle-challenge",
    "repeated-failure",
    "state-lifecycle",
    "trust-boundary",
}
METHOD_SIGNAL_TRANSLATIONS = {
    "complex-rules": "interacting-features",
    "conflicting-evidence": "ambiguity",
    "cross-participant-flow": "multi-user-state",
    "model-evaluation": "model-evaluation",
    "multi-version-coexistence": "multi-version-coexistence",
    "oracle-challenge": "weak-oracle",
    "repeated-failure": "debugging-unknown-cause",
    "state-lifecycle": "protocol-state",
    "trust-boundary": "cross-boundary-identity",
}
METHOD_SIGNAL_ALIASES: dict[str, tuple[str, ...]] = {
    "concurrent-state-lifecycle": ("state-lifecycle",),
    "concurrency-ordering": ("state-lifecycle",),
    "cross-boundary-state": ("cross-participant-flow",),
    "distributed-state": ("cross-participant-flow", "state-lifecycle"),
    "migration-rollback": ("multi-version-coexistence",),
    "ordering-sensitive-concurrency": ("state-lifecycle",),
}
ROUTE_RISK_ALIASES: dict[str, tuple[str, ...]] = {
    "data-loss": ("persisted-data",),
    "external-system": ("external-write",),
}
METHOD_RISK_DERIVED_SIGNALS: dict[str, tuple[str, ...]] = {
    "authorization": ("trust-boundary",),
    "concurrency": ("state-lifecycle",),
    "data-deletion": ("state-lifecycle",),
    "distributed-state": ("cross-participant-flow",),
    "migration": ("multi-version-coexistence",),
    "ordering": ("state-lifecycle",),
    "persisted-data": ("state-lifecycle",),
    "privacy": ("trust-boundary",),
    "protocol": ("trust-boundary",),
    "public-api": ("trust-boundary",),
    "recovery": ("state-lifecycle",),
    "rollback": ("multi-version-coexistence",),
    "security": ("trust-boundary",),
    "version-compatibility": ("multi-version-coexistence",),
    "weak-tests": ("oracle-challenge",),
}
PRIVACY_METHOD_IDS = {"linddun-privacy-model"}
AGENT_MEMORY_METHOD_IDS = {"agent-memory-lifecycle-governance"}
MULTI_AGENT_METHOD_IDS = {"contract-net-task-allocation", "multi-agent-topology-ownership"}
METHOD_SIGNAL_PREFERRED_PHASE = {
    "complex-rules": "requirements",
    "conflicting-evidence": "diagnosis",
    "cross-participant-flow": "requirements",
    "model-evaluation": "verification",
    "multi-version-coexistence": "design",
    "oracle-challenge": "verification",
    "repeated-failure": "diagnosis",
    "state-lifecycle": "design",
    "trust-boundary": "design",
}
METHOD_COST_RANK = {"low": 0, "medium": 1, "high": 2}
CAPABILITY_REGISTRY = (
    Path(__file__).resolve().parents[2]
    / "dev-flow-maintainer"
    / "references"
    / "capability-registry.json"
)
VERSION_RE = re.compile(r"(?:codex-cli\s+)?(\d+)\.(\d+)\.(\d+)(?:[-+][^\s]+)?")
FEATURE_RE = re.compile(r"^([a-z][a-z0-9_]*)\s+\S+\s+(true|false)\s*$", re.MULTILINE)


class MethodSignalContractError(ValueError):
    """Describe an invalid task-facing method signal without losing correction context."""

    def __init__(self, unknown: list[str]) -> None:
        known = sorted(METHOD_ACTIVATION_SIGNALS | set(METHOD_SIGNAL_ALIASES))
        self.unknown = sorted(set(unknown))
        self.suggestions = {
            value: difflib.get_close_matches(value, known, n=1, cutoff=0.45)
            for value in self.unknown
        }
        rendered = ", ".join(self.unknown)
        super().__init__(f"unknown method activation signal(s): {rendered}")


class RouteRiskContractError(ValueError):
    """Describe an invalid task-facing risk without losing correction context."""

    def __init__(self, unknown: list[str]) -> None:
        known = sorted(engineering_context.RISK_TOKENS | set(ROUTE_RISK_ALIASES))
        self.unknown = sorted(set(unknown))
        self.suggestions = {
            value: difflib.get_close_matches(value, known, n=1, cutoff=0.45)
            for value in self.unknown
        }
        rendered = ", ".join(self.unknown)
        super().__init__(f"unknown route risk(s): {rendered}")


class RouteNeedContractError(ValueError):
    """Describe an invalid capability need without losing correction context."""

    def __init__(self, unknown: list[str]) -> None:
        known = sorted(ROUTE_NEEDS | set(ROUTE_NEED_ALIASES))
        self.unknown = sorted(set(unknown))
        self.suggestions = {
            value: difflib.get_close_matches(value, known, n=1, cutoff=0.45)
            for value in self.unknown
        }
        rendered = ", ".join(self.unknown)
        super().__init__(f"unknown route need(s): {rendered}")


def normalize_requirement_class(value: str) -> str:
    """Accept task-facing U1-U5 aliases while retaining one canonical output vocabulary."""
    return REQUIREMENT_CLASS_ALIASES.get(value.upper(), value)


def route_value_contracts() -> dict[str, tuple[set[str], dict[str, str]]]:
    """Return documented route-task value options handled before argparse choices."""
    return {
        "--intent": (ACCEPTED_TASK_INTENTS, ROUTE_INTENT_ALIASES),
        "--requirement-class": (REQUIREMENT_CLASSES, REQUIREMENT_CLASS_ALIASES),
        "--ui-impact": (UI_IMPACTS, {}),
        "--method-depth": ({"starter", "deep"}, {}),
        "--mutation": ({"none", "persistent"}, {}),
        "--unknown": (ROUTE_UNKNOWNS, {}),
        "--work-mode": ({"auto", *EXECUTION_MODES}, {}),
        "--knowledge-impact": (ROUTE_KNOWLEDGE_IMPACTS, {}),
        "--overlay": (ROUTE_OVERLAYS, {}),
    }


def portable_route_command(argv: Iterable[str]) -> str:
    command = [
        sys.executable,
        str(Path(__file__).resolve().with_name("dev-flow.py")),
        *argv,
    ]
    return subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)


def preprocess_route_argv(
    argv: list[str],
) -> tuple[list[str], dict[str, str], dict[str, Any] | None]:
    """Normalize allowlisted aliases and structure invalid documented values."""
    if not argv or argv[0] != "route-task":
        return argv, {}, None
    contracts = route_value_contracts()
    value_options = set(contracts) | {
        "--task-type",
        "--risk",
        "--need",
        "--repo-fact",
        "--repository-fact",
        "--repository-facts",
        "--effective-skill",
        "--method-signal",
        "--method-prerequisite",
    }
    flag_options = {
        "--ambiguity",
        "--material-exposure",
        "--independent-review-authorized",
        "--understanding-confirmed",
        "--waive-understanding-confirmation",
        "--profile-operation",
        "--suite-maintenance",
        "--multi-session",
        "--multi-slice",
        "--cross-module",
        "--coordination",
        "--material-tradeoff",
        "--durable-plan",
        "--compact",
    }
    known_options = value_options | flag_options
    syntax_error = False
    route_kinds: set[str] = set()
    scan = 1
    while scan < len(argv) and not syntax_error:
        token = argv[scan]
        if not token.startswith("--"):
            syntax_error = True
            break
        option, separator, _ = token.partition("=")
        if option in {"--intent", "--task-type"}:
            route_kinds.add(option)
            syntax_error = len(route_kinds) > 1
            if syntax_error:
                break
        if option not in known_options or option in flag_options and separator:
            syntax_error = True
            break
        if option in value_options and not separator:
            if scan + 1 >= len(argv) or argv[scan + 1].startswith("--"):
                syntax_error = True
                break
            scan += 2
        else:
            scan += 1
    if syntax_error:
        return argv, {}, None
    normalized = list(argv)
    aliases_used: dict[str, str] = {}
    invalid: list[dict[str, Any]] = []
    index = 1
    while index < len(normalized):
        token = normalized[index]
        option, separator, inline_value = token.partition("=")
        contract = contracts.get(option)
        if contract is None:
            index += 1
            continue
        if separator:
            value = inline_value
            value_index = index
        else:
            if index + 1 >= len(normalized) or normalized[index + 1].startswith("--"):
                index += 1
                continue
            value = normalized[index + 1]
            value_index = index + 1
        allowed, aliases = contract
        canonical = aliases.get(value, aliases.get(value.upper(), value))
        if canonical in allowed:
            if canonical != value:
                aliases_used[option] = value
                normalized[value_index] = f"{option}={canonical}" if separator else canonical
            index += 1 if separator else 2
            continue
        candidates = sorted(allowed | set(aliases))
        matches = difflib.get_close_matches(value, candidates, n=2, cutoff=0.45)
        suggestions = list(
            dict.fromkeys(aliases.get(match, aliases.get(match.upper(), match)) for match in matches)
        )
        invalid.append(
            {
                "field": option[2:].replace("-", "_"),
                "option": option,
                "input": value,
                "allowed_values": sorted(allowed),
                "suggestions": suggestions,
                "value_index": value_index,
                "inline": bool(separator),
            }
        )
        index += 1 if separator else 2
    if not invalid:
        return normalized, aliases_used, None
    corrected = list(normalized)
    replayable = all(len(item["suggestions"]) == 1 for item in invalid)
    if replayable:
        for item in invalid:
            replacement = item["suggestions"][0]
            corrected[item["value_index"]] = (
                f"{item['option']}={replacement}" if item["inline"] else replacement
            )
    first = invalid[0]
    payload: dict[str, Any] = {
        "status": "invalid",
        "errors": [
            f"unknown {item['field'].replace('_', '-')} value: {item['input']}"
            for item in invalid
        ],
        "field": first["field"],
        "input": first["input"],
        "allowed_values": first["allowed_values"],
        "suggestions": {item["input"]: item["suggestions"] for item in invalid},
        "invalid_values": [
            {
                key: item[key]
                for key in ("field", "input", "allowed_values", "suggestions")
            }
            for item in invalid
        ],
        "corrected_command": portable_route_command(corrected) if replayable else None,
    }
    return normalized, aliases_used, payload


def normalize_route_needs(values: Iterable[str]) -> tuple[list[str], list[dict[str, str]]]:
    """Accept specialist Skill names as task-facing aliases for route needs."""
    inputs = sorted(set(values))
    unknown = sorted(
        value for value in inputs if value not in ROUTE_NEEDS and value not in ROUTE_NEED_ALIASES
    )
    if unknown:
        raise RouteNeedContractError(unknown)
    normalized: set[str] = set()
    translations: list[dict[str, str]] = []
    for value in inputs:
        target = ROUTE_NEED_ALIASES.get(value, value)
        normalized.add(target)
        translations.append(
            {
                "input": value,
                "canonical": target,
                "kind": "alias" if value in ROUTE_NEED_ALIASES else "canonical",
            }
        )
    return sorted(normalized), translations


def normalize_route_risks(values: Iterable[str]) -> tuple[list[str], list[dict[str, Any]]]:
    """Accept bounded task-facing risk aliases while preserving canonical downstream values."""
    inputs = sorted(set(values))
    unknown = sorted(
        value
        for value in inputs
        if value not in engineering_context.RISK_TOKENS and value not in ROUTE_RISK_ALIASES
    )
    if unknown:
        raise RouteRiskContractError(unknown)
    normalized: set[str] = set()
    translations: list[dict[str, Any]] = []
    for value in inputs:
        targets = ROUTE_RISK_ALIASES.get(value, (value,))
        normalized.update(targets)
        translations.append(
            {
                "input": value,
                "canonical": sorted(targets),
                "kind": "alias" if value in ROUTE_RISK_ALIASES else "canonical",
            }
        )
    return sorted(normalized), translations


def normalize_method_activation_signals(
    values: Iterable[str],
    *,
    risks: set[str],
) -> tuple[list[str], list[dict[str, Any]], list[str]]:
    """Normalize public aliases and supplement them with uncovered risk foundations."""
    inputs = sorted(set(values))
    unknown = sorted(
        value
        for value in inputs
        if value not in METHOD_ACTIVATION_SIGNALS and value not in METHOD_SIGNAL_ALIASES
    )
    if unknown:
        raise MethodSignalContractError(unknown)
    normalized: set[str] = set()
    translations: list[dict[str, Any]] = []
    for value in inputs:
        targets = METHOD_SIGNAL_ALIASES.get(value, (value,))
        normalized.update(targets)
        translations.append(
            {
                "input": value,
                "canonical": sorted(targets),
                "kind": "alias" if value in METHOD_SIGNAL_ALIASES else "canonical",
            }
        )
    risk_foundations: set[str] = set()
    for risk in sorted(risks):
        risk_foundations.update(METHOD_RISK_DERIVED_SIGNALS.get(risk, ()))
    derived = risk_foundations - normalized
    normalized.update(derived)
    return sorted(normalized), translations, sorted(derived)


def corrected_route_command(
    args: argparse.Namespace,
    *,
    risk_suggestions: dict[str, list[str]] | None = None,
    signal_suggestions: dict[str, list[str]] | None = None,
    need_suggestions: dict[str, list[str]] | None = None,
    fact_replacements: dict[str, str] | None = None,
) -> str | None:
    """Replay a corrected route with the original task semantics from any working directory."""
    risk_suggestions = risk_suggestions or {}
    signal_suggestions = signal_suggestions or {}
    need_suggestions = need_suggestions or {}
    fact_replacements = fact_replacements or {}
    if any(
        not matches
        for matches in (
            *risk_suggestions.values(),
            *signal_suggestions.values(),
            *need_suggestions.values(),
        )
    ):
        return None
    risk_replacements = {value: matches[0] for value, matches in risk_suggestions.items()}
    signal_replacements = {value: matches[0] for value, matches in signal_suggestions.items()}
    need_replacements = {value: matches[0] for value, matches in need_suggestions.items()}
    if (
        not risk_replacements
        and not signal_replacements
        and not need_replacements
        and not fact_replacements
    ):
        return None
    command = [
        sys.executable,
        str(Path(__file__).resolve().with_name("dev-flow.py")),
        "route-task",
    ]
    if args.intent is not None:
        command.extend(("--intent", args.intent))
    else:
        command.extend(("--task-type", args.task_type))
    if args.target_revision is not None:
        command.extend(("--target-revision", args.target_revision))
    for risk in args.risk:
        command.extend(("--risk", risk_replacements.get(risk, risk)))
    for need in args.need:
        command.extend(("--need", need_replacements.get(need, need)))
    if args.ui_impact != "none":
        command.extend(("--ui-impact", args.ui_impact))
    if args.ambiguity:
        command.append("--ambiguity")
    if args.material_exposure:
        command.append("--material-exposure")
    if args.independent_review_authorized:
        command.append("--independent-review-authorized")
    for fact in args.repo_fact:
        command.extend(("--repo-fact", fact_replacements.get(fact, fact)))
    for skill in args.effective_skill:
        command.extend(("--effective-skill", skill))
    for signal in args.method_signal:
        command.extend(("--method-signal", signal_replacements.get(signal, signal)))
    for prerequisite in args.method_prerequisite:
        command.extend(("--method-prerequisite", prerequisite))
    if args.method_depth is not None:
        command.extend(("--method-depth", args.method_depth))
    if args.requirement_class is not None:
        command.extend(("--requirement-class", args.requirement_class))
    if args.understanding_confirmed:
        command.append("--understanding-confirmed")
    if args.waive_understanding_confirmation:
        command.append("--waive-understanding-confirmation")
    if args.user_choice_open:
        command.append("--user-choice-open")
    if args.profile_operation:
        command.append("--profile-operation")
    if args.suite_maintenance:
        command.append("--suite-maintenance")
    if args.mutation is not None:
        command.extend(("--mutation", args.mutation))
    for unknown in args.unknown:
        command.extend(("--unknown", unknown))
    if args.work_mode != "auto":
        command.extend(("--work-mode", args.work_mode))
    for active, option in (
        (args.multi_session, "--multi-session"),
        (args.multi_slice, "--multi-slice"),
        (args.cross_module, "--cross-module"),
        (args.coordination, "--coordination"),
        (args.material_tradeoff, "--material-tradeoff"),
        (args.durable_plan, "--durable-plan"),
    ):
        if active:
            command.append(option)
    for impact in args.knowledge_impact:
        command.extend(("--knowledge-impact", impact))
    for overlay in args.overlay:
        command.extend(("--overlay", overlay))
    if args.previous_route is not None:
        command.extend(("--previous-route", str(args.previous_route)))
    if args.compact:
        command.append("--compact")
    return subprocess.list2cmdline(command) if os.name == "nt" else shlex.join(command)


def validate_method_domain_gate_ids(payload: dict[str, Any]) -> None:
    """Fail closed when a hard-coded domain gate drifts from the method registry."""
    registered = {method["id"] for method in payload["methods"]}
    configured = PRIVACY_METHOD_IDS | AGENT_MEMORY_METHOD_IDS | MULTI_AGENT_METHOD_IDS
    missing = sorted(configured - registered)
    if missing:
        raise methodology_system.MethodologyContractError(
            f"task-facing method domain gate references unknown method(s): {', '.join(missing)}"
        )


def method_domain_gate_reason(
    method_id: str,
    *,
    risks: set[str],
    repository_facts: set[str],
    available_prerequisites: set[str],
) -> str | None:
    """Keep specialist domains out of broad task-facing method projections."""
    if method_id in PRIVACY_METHOD_IDS and "privacy" not in risks:
        return "privacy method requires an observed privacy risk"
    if method_id in AGENT_MEMORY_METHOD_IDS and not (
        "memory-store-inventory" in available_prerequisites
        and repository_facts
        & {
            "agentic-system=true",
            "feature=persistent-agent-memory",
            "system=agentic",
        }
    ):
        return "agent-memory method requires an agentic-system fact and memory-store inventory"
    if method_id in MULTI_AGENT_METHOD_IDS and not repository_facts & {
        "delegation=active",
        "delegation=planned",
        "multi-agent-work=true",
    }:
        return "multi-agent method requires actual planned or active delegation"
    return None


def task_facing_method_phase(
    *,
    default_phase: str,
    payload: dict[str, Any],
    risks: set[str],
    method_signals: set[str],
    translated_signals: set[str],
    repository_facts: set[str],
    available_prerequisites: set[str],
    depth: str,
    task_type: str,
) -> tuple[str, str]:
    """Use an adjacent owner when its methods better cover an explicit reasoning shape."""
    if not method_signals:
        return default_phase, "intent"
    normalized_risks, _, _ = methodology_system.normalize_risks(
        payload["vocabulary"], sorted(risks)
    )
    canonical_risks = set(normalized_risks)
    matched_method_ids: set[str] = set()
    for model in payload["risk_models"]:
        matches = {
            "risks": canonical_risks & set(model["match"]["risks"]),
            "signals": translated_signals & set(model["match"]["signals"]),
            "task_types": {task_type} & set(model["match"]["task_types"]),
        }
        score = sum(
            len(matches[field]) * methodology_system.MATCH_WEIGHTS[field]
            for field in methodology_system.MATCH_FIELDS
        )
        if score >= model["minimum_score"]:
            matched_method_ids.update(model["method_ids"])
    depth_index = {
        value: index for index, value in enumerate(payload["selection_contract"]["depths"])
    }

    def direct_strength(phase: str) -> tuple[int, int]:
        applicable = [
            method
            for method in payload["methods"]
            if method["id"] in matched_method_ids
            and phase in method["phases"]
            and depth_index[method["depth"]] <= depth_index[depth]
            and method_domain_gate_reason(
                method["id"],
                risks=risks,
                repository_facts=repository_facts,
                available_prerequisites=available_prerequisites,
            )
            is None
        ]
        return (
            len(
                set().union(
                    *(set(method["signals"]) & translated_signals for method in applicable)
                )
            ),
            len(
                set().union(
                    *(set(method["risks"]) & canonical_risks for method in applicable)
                )
            ),
        )

    def ready_profile(phase: str) -> tuple[bool, int]:
        ready = [
            method
            for method in payload["methods"]
            if method["id"] in matched_method_ids
            and phase in method["phases"]
            and depth_index[method["depth"]] <= depth_index[depth]
            and set(method["prerequisites"]).issubset(available_prerequisites)
            and (
                set(method["signals"]) & translated_signals
                or set(method["risks"]) & canonical_risks
            )
            and method_domain_gate_reason(
                method["id"],
                risks=risks,
                repository_facts=repository_facts,
                available_prerequisites=available_prerequisites,
            )
            is None
        ]
        if not ready:
            return False, -len(METHOD_COST_RANK)
        return True, -min(METHOD_COST_RANK[method["cost"]] for method in ready)

    if (
        default_phase in {"implementation", "review"}
        and "model-evaluation" in method_signals
        and direct_strength("verification") > (0, 0)
    ):
        return "verification", "signal-adjacent-owner"

    if default_phase == "review":
        verification_ready = ready_profile("verification")
        review_ready = ready_profile("review")
        if (
            "oracle-challenge" in method_signals
            and (
                verification_ready > review_ready
                or (
                    not review_ready[0]
                    and direct_strength("verification")[0]
                    >= direct_strength("review")[0]
                )
            )
        ):
            return "verification", "signal-adjacent-owner"
        return default_phase, "intent"
    if default_phase != "implementation":
        return default_phase, "intent"

    default_strength = direct_strength(default_phase)
    preferred = [
        phase
        for phase in ("requirements", "diagnosis", "design", "verification")
        if any(METHOD_SIGNAL_PREFERRED_PHASE[signal] == phase for signal in method_signals)
    ]
    preferred_strengths = [(direct_strength(phase), phase) for phase in preferred]
    best_preferred_strength, best_preferred_phase = max(
        preferred_strengths,
        key=lambda item: item[0],
        default=((0, 0), default_phase),
    )
    if best_preferred_strength[0] > default_strength[0]:
        return best_preferred_phase, "signal-adjacent-owner"
    if default_strength > (0, 0):
        return default_phase, "intent-direct-match"
    for phase in preferred:
        if direct_strength(phase) > (0, 0):
            return phase, "signal-adjacent-owner"
    return default_phase, "intent-no-adjacent-match"


def route_intent(args: argparse.Namespace) -> tuple[str, str]:
    """Resolve the primary work intent while retaining the 1.x task vocabulary."""
    if args.intent is not None:
        alias_input = getattr(args, "intent_alias_input", None)
        if alias_input is not None:
            return args.intent, f"alias-intent:{alias_input}"
        if args.intent in LEGACY_INTENT_ALIASES:
            return LEGACY_INTENT_ALIASES[args.intent], f"legacy-intent:{args.intent}"
        return args.intent, "explicit-intent"
    task_type = args.task_type
    if task_type not in LEGACY_TASK_INTENTS:
        raise ValueError("route-task requires --intent or the compatible --task-type")
    return LEGACY_TASK_INTENTS[task_type], f"legacy-task-type:{task_type}"


def select_execution_mode(args: argparse.Namespace) -> tuple[str, list[str]]:
    """Select 2.0 continuity mode independently from engineering risk."""
    signals = {
        "multi-session": bool(args.multi_session),
        "multi-slice": bool(args.multi_slice),
        "cross-module": bool(args.cross_module),
        "coordination": bool(args.coordination),
        "material-tradeoff": bool(args.material_tradeoff),
        "durable-plan": bool(args.durable_plan),
    }
    reasons = [name for name, active in signals.items() if active]
    if args.task_type in {"large-feature", "large-refactor", "migration"}:
        reasons.append(args.task_type)
    automatic = "managed" if reasons else "direct"
    if args.work_mode == "auto":
        return automatic, reasons or ["bounded-work"]
    return args.work_mode, ["explicit-work-mode", *(reasons or ["bounded-work"])]


def route_knowledge(args: argparse.Namespace, work_mode: str) -> dict[str, Any]:
    """Describe repository knowledge consequences without creating workflow state."""
    requested = list(dict.fromkeys(args.knowledge_impact))
    if "none" in requested and len(requested) > 1:
        raise ValueError("knowledge impact 'none' cannot be combined with another impact")

    superseded: list[str] = []
    if work_mode == "managed":
        impacts = ["workstream"]
        for impact in requested:
            if impact == "none":
                continue
            if impact == "change-record":
                superseded.append("change-record:managed-workstream")
                continue
            if impact not in impacts:
                impacts.append(impact)
    else:
        impacts = requested or ["none"]

    return {
        "disposition": impacts,
        "default_change_record_path": "docs/change-notes/<slug>.md" if "change-record" in impacts else None,
        "superseded": superseded,
        "rules": [
            "update the canonical repository owner before adding a separate record",
            "use a change record only when existing owners cannot carry cross-session, cross-owner, or independently sliced continuation",
            "do not copy commands, logs, hashes, agent activity, or file-by-file history",
        ],
        "recheck_on": ["scope-or-design-change", "new-durable-impact", "before-close"],
        "artifact_created": False,
    }


def route_requirement_understanding(
    args: argparse.Namespace,
    *,
    intent: str,
    work_mode: str,
) -> dict[str, Any]:
    """Classify semantic depth and the Default-mode confirmation boundary."""
    if args.understanding_confirmed and args.waive_understanding_confirmation:
        raise ValueError(
            "--understanding-confirmed and --waive-understanding-confirmation are mutually exclusive"
        )

    explicit = args.requirement_class
    if explicit is not None:
        requirement_class = explicit
        source = "explicit"
    elif intent in {"research", "review", "delivery"}:
        requirement_class = "read-only"
        source = f"intent:{intent}"
    elif args.task_type == "micro":
        requirement_class = "mechanical"
        source = "legacy-task-type:micro"
    elif intent == "diagnose" or args.task_type == "bugfix":
        requirement_class = "defect-correction"
        source = "diagnosis-or-bugfix"
    elif (
        intent == "design"
        or args.task_type in {"large-feature", "migration"}
        or args.ambiguity
        or args.material_tradeoff
        or args.ui_impact == "material"
    ):
        requirement_class = "semantic-change"
        source = "semantic-signal"
    else:
        requirement_class = "structural-adjustment"
        source = "bounded-change-default"

    if requirement_class == "defect-correction" and args.ambiguity:
        requirement_class = "semantic-change"
        source = "ambiguous-defect-upgrade"
    if args.user_choice_open and requirement_class != "semantic-change":
        requirement_class = "semantic-change"
        source = "unresolved-user-choice-upgrade"

    confirmation_required = requirement_class == "semantic-change" and args.user_choice_open
    if args.understanding_confirmed:
        confirmation = "confirmed"
    elif args.waive_understanding_confirmation:
        confirmation = "waived"
    elif confirmation_required:
        confirmation = "required"
    else:
        confirmation = "not-required"
    design_allowed = not confirmation_required or confirmation in {"confirmed", "waived"}

    return {
        "class": requirement_class,
        "class_source": source,
        "detailed_output": requirement_class in {"semantic-change", "structural-adjustment"},
        "confirmation_required": confirmation_required,
        "confirmation": confirmation,
        "design_allowed": design_allowed,
        "next_action": (
            "publish-detailed-understanding-and-stop"
            if confirmation_required and not design_allowed
            else "publish-understanding-and-continue"
            if requirement_class == "semantic-change" and confirmation == "not-required"
            else "continue"
        ),
        "stop_before": "technical-design" if confirmation_required and not design_allowed else None,
        "durable_requirement_source": work_mode == "managed" and requirement_class == "semantic-change",
        "rules": [
            "remain in Default mode",
            "resolve repository facts before asking the user",
            "stop only for an unresolved user-owned choice that changes the outcome",
            "a correction requires a complete revised understanding",
            "confirmation does not authorize dependencies, delivery, or destructive/external action",
        ],
    }


def route_capability_activation(
    args: argparse.Namespace,
    *,
    intent: str,
    risks: set[str],
    needs: set[str],
    risk_translations: list[dict[str, Any]],
    understanding: dict[str, Any],
) -> dict[str, Any]:
    """Return a non-persisted advanced-capability posture for the current route."""
    normalized_method_signals, signal_translations, derived_method_signals = (
        normalize_method_activation_signals(args.method_signal, risks=risks)
    )
    method_signals = set(normalized_method_signals)
    method_risks = sorted(risks & METHOD_ACTIVATION_RISKS)
    method_reasons = [
        *(f"risk:{value}" for value in method_risks),
        *(f"signal:{value}" for value in sorted(method_signals)),
    ]
    review_reasons: list[str] = []
    if args.material_exposure:
        review_reasons.append("material-exposure")
    if "review" in needs:
        review_reasons.append("explicit-review-need")
    for risk in sorted(risks & {"data-deletion", "rollback", "version-compatibility"}):
        review_reasons.append(f"risk:{risk}")
    if "persisted-data" in risks and risks & {
        "backpressure",
        "distributed-state",
        "external-write",
        "idempotency",
    }:
        review_reasons.append("cross-system-durability")
    repository_facts = set(args.repo_fact)
    repository_facts.update(f"risk={risk}" for risk in risks)
    invalid_facts = sorted(value for value in repository_facts if "=" not in value)
    if invalid_facts:
        raise ValueError(f"repository facts must use key=value: {', '.join(invalid_facts)}")
    effective_skills = set(args.effective_skill)
    registry = engineering_context.load_capability_registry(CAPABILITY_REGISTRY)
    specialist_matches: list[dict[str, Any]] = []
    for capability in registry["capabilities"]:
        selectors = capability.get("selectors", [])
        if not selectors or not set(selectors).issubset(repository_facts):
            continue
        candidates = [
            name
            for name in capability.get("route_names", [])
            if any(skill == name or skill.rsplit(":", 1)[-1] == name for skill in effective_skills)
        ]
        specialist_matches.append(
            {
                "capability": capability["id"],
                "selectors": selectors,
                "route": candidates[0] if candidates else None,
                "status": "effective-skill" if candidates else "qualified-fallback",
                "fallback": None if candidates else capability["manual_fallback"],
            }
        )
    method_selection: dict[str, Any] | None = None
    if method_reasons:
        default_method_phase = {
            "research": "requirements",
            "diagnose": "diagnosis",
            "design": "design",
            "change": "implementation",
            "review": "review",
            "delivery": "delivery",
        }[intent]
        method_task_type = args.task_type or INTENT_METHOD_TASK_TYPES[intent]
        method_depth = args.method_depth or (
            "deep"
            if risks
            & {
                "abi",
                "authorization",
                "concurrency",
                "data-deletion",
                "distributed-state",
                "ffi",
                "migration",
                "ordering",
                "persisted-data",
                "privacy",
                "recovery",
                "rollback",
                "security",
                "unsafe",
                "version-compatibility",
                "weak-tests",
            }
            else "starter"
        )
        method_payload = methodology_system.read_registry(methodology_registry_path())
        validate_method_domain_gate_ids(method_payload)
        translated_signals = {METHOD_SIGNAL_TRANSLATIONS[value] for value in method_signals}
        supplied_prerequisites = set(args.method_prerequisite)
        inferred_prerequisites: set[str] = set()
        if repository_facts:
            inferred_prerequisites.add("repository-facts")
        if understanding["class"] != "semantic-change" or understanding["confirmation"] in {"confirmed", "waived"}:
            inferred_prerequisites.add("requirement-baseline")
        available_prerequisites = supplied_prerequisites | inferred_prerequisites
        method_phase, method_phase_source = task_facing_method_phase(
            default_phase=default_method_phase,
            payload=method_payload,
            risks=risks,
            method_signals=method_signals,
            translated_signals=translated_signals,
            repository_facts=repository_facts,
            available_prerequisites=available_prerequisites,
            depth=method_depth,
            task_type=method_task_type,
        )
        selected = methodology_system.select_methods(
            method_payload,
            repository_root=plugin_root(),
            phase=method_phase,
            task_type=method_task_type,
            risks=sorted(risks),
            signals=sorted(METHOD_SIGNAL_TRANSLATIONS[value] for value in method_signals),
            available=sorted(available_prerequisites),
            depth=method_depth,
            # The task-facing projection below owns the three-method context cap.
            # Avoid letting registry order hide a later ready, directly relevant method.
            max_methods=len(method_payload["methods"]),
        )
        method_by_id = {method["id"]: method for method in method_payload["methods"]}
        method_order = {method["id"]: index for index, method in enumerate(method_payload["methods"])}
        canonical_method_risks = set(selected["request"]["risks"])
        blocked_by_id = {item["method_id"]: item for item in selected["blocked_methods"]}
        ready_ids = [method["id"] for method in selected["selected_methods"]]
        blocked_ids = [item["method_id"] for item in selected["blocked_methods"]]
        method_model_order: dict[str, tuple[int, int]] = {}
        for stack_index, stack in enumerate(selected["stacks"]):
            for stack_method_index, entry in enumerate(stack["methods"]):
                method_model_order.setdefault(
                    entry["method_id"], (stack_index, stack_method_index)
                )

        def activation_relevance(method_id: str) -> tuple[int, int, int, int, int, int]:
            method = method_by_id[method_id]
            direct_signals = len(set(method["signals"]) & translated_signals)
            direct_risks = len(set(method["risks"]) & canonical_method_risks)
            stack_index, stack_method_index = method_model_order.get(
                method_id, (len(selected["stacks"]), len(method_payload["methods"]))
            )
            return (
                direct_signals,
                direct_risks,
                -METHOD_COST_RANK[method["cost"]],
                -stack_index,
                -stack_method_index,
                -method_order[method_id],
            )

        def directly_relevant(method_id: str) -> bool:
            direct_signals, direct_risks, *_ = activation_relevance(method_id)
            return direct_signals > 0 or direct_risks > 0

        gated_ready = [
            method_id
            for method_id in ready_ids
            if method_domain_gate_reason(
                method_id,
                risks=risks,
                repository_facts=repository_facts,
                available_prerequisites=available_prerequisites,
            )
            is None
            and directly_relevant(method_id)
        ]
        gated_blocked = [
            method_id
            for method_id in blocked_ids
            if method_domain_gate_reason(
                method_id,
                risks=risks,
                repository_facts=repository_facts,
                available_prerequisites=available_prerequisites,
            )
            is None
            and directly_relevant(method_id)
        ]
        bounded_selected = sorted(gated_ready, key=activation_relevance, reverse=True)[:3]
        ranked_blocked = sorted(gated_blocked, key=activation_relevance, reverse=True)
        bounded_blocked_ids: list[str] = []
        # Preserve both the observed reasoning shape and the affected consequence
        # when they identify different blocked methods; two variants of one axis
        # must not hide the other.
        for component in (0, 1):
            candidate = next(
                (
                    method_id
                    for method_id in ranked_blocked
                    if method_id not in bounded_blocked_ids
                    and activation_relevance(method_id)[component] > 0
                ),
                None,
            )
            if candidate is not None:
                bounded_blocked_ids.append(candidate)
        for method_id in ranked_blocked:
            if len(bounded_blocked_ids) >= 2:
                break
            if method_id not in bounded_blocked_ids:
                bounded_blocked_ids.append(method_id)
        bounded_blocked = [blocked_by_id[method_id] for method_id in bounded_blocked_ids]
        if not bounded_selected and not bounded_blocked:
            # A phase foundation remains a bounded fallback only when the observed
            # facts did not make any risk-model method actionable.
            bounded_selected = [
                method_id
                for method_id in ready_ids
                if method_by_id[method_id]["selection"] == "foundation"
                and method_domain_gate_reason(
                    method_id,
                    risks=risks,
                    repository_facts=repository_facts,
                    available_prerequisites=available_prerequisites,
                )
                is None
            ][:1]
        selection_status = (
            "selected"
            if bounded_selected
            else "selected-with-unresolved-prerequisites"
            if bounded_blocked
            else "no-actionable-match"
        )
        method_selection = {
            "status": selection_status,
            "phase": method_phase,
            "phase_source": method_phase_source,
            "depth": method_depth,
            "selected": bounded_selected,
            "available_prerequisites": sorted(available_prerequisites),
            "inferred_prerequisites": sorted(inferred_prerequisites),
            "guidance": [
                {
                    "method": method_id,
                    "disposition": "ready",
                    "owner": method_by_id[method_id]["owner"],
                    "why": method_by_id[method_id]["positive_trigger"],
                    "avoid_when": method_by_id[method_id]["negative_trigger"],
                    "required_prerequisites": method_by_id[method_id]["prerequisites"],
                    "cost": method_by_id[method_id]["cost"],
                    "expected_outputs": method_by_id[method_id]["outputs"],
                    "minimum_action": method_by_id[method_id]["steps"][0],
                    "steps": method_by_id[method_id]["steps"],
                    "evidence": method_by_id[method_id]["evidence"],
                    "fallback": method_by_id[method_id]["fallback"],
                    "limitations": method_by_id[method_id]["limitations"],
                }
                for method_id in bounded_selected
            ],
            "blocked": [
                {
                    "method": item["method_id"],
                    "disposition": "blocked",
                    "owner": method_by_id[item["method_id"]]["owner"],
                    "why": method_by_id[item["method_id"]]["positive_trigger"],
                    "avoid_when": method_by_id[item["method_id"]]["negative_trigger"],
                    "cost": method_by_id[item["method_id"]]["cost"],
                    "expected_outputs": method_by_id[item["method_id"]]["outputs"],
                    "missing_prerequisites": item["missing_prerequisites"],
                    "fallback": item["fallback"],
                    "evidence": method_by_id[item["method_id"]]["evidence"],
                    "limitations": method_by_id[item["method_id"]]["limitations"],
                }
                for item in bounded_blocked
            ],
            "matched_risk_models": [
                item["id"] for item in selected["reasoning_model"]["matched_risk_models"]
            ],
            "fallback": (
                None
                if bounded_selected or bounded_blocked
                else "Use the owning specialist's established procedure and state that no bounded methodology match was actionable."
            ),
            "actionable": bool(bounded_selected or bounded_blocked),
            "disposition_options": [
                "execute-ready-method",
                "execute-blocked-fallback-with-limitation",
                "reasoned-abstention-when-owner-procedure-is-sufficient",
            ],
            "realization_required": (
                "change an owner test/oracle, counterexample, model, review attack surface, "
                "evidence matrix, or explicit claim limitation"
            ),
            "selection_count_is_quality": False,
            "persisted": False,
        }
    independent_review_required = bool(review_reasons)
    return {
        "artifact": None,
        "passes": ["after-repository-discovery", "after-material-requirement-confirmation"],
        "specialist": {
            "source": "effective-current-turn-skill-surface",
            "decision": "smallest-applicable-owner-with-positive-value",
            "fallback": "repository-native-or-qualified-manual-control",
            "repository_facts": sorted(repository_facts),
            "matches": specialist_matches,
            "persisted": False,
        },
        "method": {
            "active_match_required": bool(method_reasons),
            "reasons": method_reasons,
            "signal_normalization": {
                "input": sorted(set(args.method_signal)),
                "canonical": sorted(method_signals),
                "translations": signal_translations,
                "derived_from_risks": derived_method_signals,
            },
            "risk_normalization": {
                "canonical": sorted(risks),
                "translations": risk_translations,
            },
            "action": (
                "use-specialist-method-or-bounded-select"
                if method_reasons
                else "ordinary-specialist-or-repository-practice"
            ),
            "selection": method_selection,
            "maximum_loaded_methods": 3,
            "persisted": False,
        },
        "independent_review": {
            "required": independent_review_required,
            "reasons": sorted(set(review_reasons)),
            "blue_red_are_lenses": True,
            "same_context_is_independent": False,
            "evidence_required": {
                "reviewer_identity": "non-empty-dispatched-reviewer-or-receiver-id",
                "completed_result": True,
            },
            "empty_wait_is_independent": False,
            "delegation_authorized": True,
            "delegation_authority_source": "internal-work-allocation-no-user-authorization-required",
            "authorization_from_route": False,
            "wait_precondition": "successful-dispatch-with-non-empty-reviewer-identity",
            "execution": (
                "route-agent" if independent_review_required else "not-required"
            ),
            "route_agent": (
                {
                    "role": "dev-flow-red-reviewer",
                    "workload": "high-risk-review",
                    "signal": "independent-review",
                }
                if independent_review_required
                else None
            ),
            "downgrade": (
                {
                    "allowed_when": "clean-context capability is unavailable, resource-conflicted, or the work is not independently decomposable",
                    "required_report": "common-mode-risk",
                    "claim": "same-context-review",
                }
                if independent_review_required
                else None
            ),
        },
        "child_route": {
            "when": "only after delegation has positive isolation or parallel value",
            "resolver": "route-agent",
            "persisted": False,
        },
        "recheck_on": [
            "scope-or-design-change",
            "new-boundary-or-dependency",
            "first-surprising-failure",
            "repeated-failed-hypothesis",
            "final-diff-exposure",
            "delivery-or-irreversibility",
        ],
    }


def risk_overlays(
    task_type: str,
    risks: set[str],
    needs: set[str],
    ui_impact: str,
    requested: Iterable[str],
    original_risks: Iterable[str] = (),
) -> list[dict[str, Any]]:
    """Return orthogonal risk controls without changing continuity mode."""
    reasons: dict[str, set[str]] = {value: {"explicit"} for value in requested}

    def add(name: str, values: Iterable[str]) -> None:
        selected = {value for value in values if value}
        if selected:
            reasons.setdefault(name, set()).update(selected)

    security = risks & {
        "authentication",
        "authorization",
        "privacy",
        "regulated",
        "secrets",
        "security",
        "untrusted-input",
    }
    migration = risks & {
        "compatibility",
        "data-deletion",
        "migration",
        "rollback",
        "schema",
        "version-compatibility",
    }
    if "data-loss" in original_risks:
        migration.add("data-loss")
    external = risks & {
        "distributed-state",
        "external-write",
        "idempotency",
        "protocol",
    }
    release = risks & {"deployment", "production-config", "release", "signing"}
    irreversible = risks & {"data-deletion"}
    add("security", security | ({task_type} if task_type == "security" else set()))
    add("migration", migration | ({task_type} if task_type == "migration" else set()))
    add("external-system", external)
    add(
        "release",
        release
        | ({task_type} if task_type in {"release-hotfix", "rollback"} else set())
        | ({"delivery"} if "delivery" in needs else set()),
    )
    add("irreversible", irreversible)
    add("ui-product", {ui_impact} if ui_impact == "material" else set())
    return [
        {"overlay": name, "reasons": sorted(values)}
        for name, values in sorted(reasons.items())
    ]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def emit(payload: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def skill_root() -> Path:
    return Path(__file__).resolve().parents[1]


def plugin_root() -> Path:
    return Path(__file__).resolve().parents[3]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def run(command: list[str], cwd: Path | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True, timeout=timeout)


def parse_version(text: str) -> tuple[int, int, int]:
    match = VERSION_RE.search(text.strip())
    if not match:
        raise ValueError(f"cannot parse Codex version from {text.strip()!r}")
    return tuple(int(part) for part in match.groups())


def codex_preflight(args: argparse.Namespace) -> int:
    capability_issues: list[str] = []
    warnings: list[str] = []
    dispatch_registry_ready = False
    configured_ceiling: int | None = None
    binary = args.codex or shutil.which("codex")
    version_text = args.version_output
    features_text: str | None = None

    try:
        if args.features_output_file:
            features_text = args.features_output_file.read_text(encoding="utf-8")
        if version_text is None:
            if not binary:
                raise RuntimeError("Codex CLI was not found on PATH")
            result = run([binary, "--version"])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            version_text = result.stdout
        if features_text is None:
            if not binary:
                raise RuntimeError("Codex CLI was not found on PATH")
            result = run([binary, "features", "list"])
            if result.returncode:
                raise RuntimeError(result.stderr.strip() or result.stdout.strip())
            features_text = result.stdout
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        capability_issues.append(str(exc))

    actual: tuple[int, int, int] | None = None
    try:
        actual = parse_version(version_text or "")
        if actual < MIN_CODEX:
            capability_issues.append(f"Codex {'.'.join(map(str, actual))} is below delegation-tested 0.147.0")
    except ValueError as exc:
        capability_issues.append(str(exc))

    features = dict(FEATURE_RE.findall(features_text or ""))
    observed_capabilities = set(args.effective_capability)
    if args.tool_surface_confirmed:
        # Compatibility alias retained for callers that only confirm delegation.
        observed_capabilities.add("delegation")
    if features.get("multi_agent") != "true":
        capability_issues.append("Codex effective feature multi_agent is not enabled")
    if features.get("hooks") != "true":
        warnings.append("Codex effective feature hooks is unavailable; Dev Flow continues without hook automation")

    try:
        agent_dispatch.load_registry()
        dispatch_registry_ready = True
    except (OSError, json.JSONDecodeError, agent_dispatch.DispatchContractError) as exc:
        capability_issues.append(f"agent dispatch registry is invalid: {exc}")

    config_path = args.config or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "config.toml"
    effective: dict[str, Any] = {}
    if not args.skip_config:
        try:
            effective = tomllib.loads(config_path.read_text(encoding="utf-8"))
            feature_config = effective.get("features", {})
            if not isinstance(feature_config, dict):
                raise ValueError("config [features] must be a table")
            if feature_config.get("multi_agent") is False:
                warnings.append("config explicitly disables multi_agent even though the effective feature list is authoritative")
            if feature_config.get("hooks") is False:
                warnings.append("config explicitly disables hooks; hook automation remains optional")
            agent_config = effective.get("agents", {})
            if not isinstance(agent_config, dict):
                raise ValueError("config [agents] must be a table")
            limit = agent_config.get("max_concurrent_threads_per_session")
            if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit < 1):
                capability_issues.append("configured [agents].max_concurrent_threads_per_session must be a positive integer")
            elif limit is not None:
                configured_ceiling = limit
                if limit > GOVERNED_MAX_ACTIVE_CHILDREN:
                    warnings.append(
                        f"configured agent ceiling {limit} exceeds the governed active-child ceiling "
                        f"{GOVERNED_MAX_ACTIVE_CHILDREN}; Dev Flow will schedule at most "
                        f"{GOVERNED_MAX_ACTIVE_CHILDREN} active children"
                    )
            if isinstance(feature_config.get("multi_agent_v2"), dict):
                warnings.append("obsolete [features.multi_agent_v2] is ignored; the current runtime uses multi_agent")
        except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
            capability_issues.append(f"cannot read Codex config {config_path}: {exc}")

    if "delegation" not in observed_capabilities:
        capability_issues.append("The active root must confirm the collaboration tools before delegation")

    errors = capability_issues if args.require_delegation else []
    if not args.require_delegation:
        warnings.extend(capability_issues)
    delegation_available = not capability_issues
    status = "blocked" if errors else "ready" if delegation_available else "degraded"
    governed_ceiling = (
        min(configured_ceiling, GOVERNED_MAX_ACTIVE_CHILDREN)
        if configured_ceiling is not None
        else None
    )
    if delegation_available and governed_ceiling is not None:
        ordinary_soft_limit: int | None = min(
            governed_ceiling,
            ORDINARY_ACTIVE_CHILD_SOFT_LIMIT,
        )
        recommended_initial: int | None = min(governed_ceiling, 1)
        initial_profiles: dict[str, int | None] = {
            "uncertain_or_tightly_coupled": min(governed_ceiling, 1),
            "isolated_implementation": min(
                governed_ceiling,
                DEFAULT_INITIAL_ACTIVE_CHILDREN,
            ),
            "read_only_breadth": min(
                governed_ceiling,
                READ_ONLY_BREADTH_INITIAL_ACTIVE_CHILDREN,
            ),
        }
        ramp_step: int | None = DEFAULT_CAPACITY_RAMP_STEP
    elif delegation_available:
        ordinary_soft_limit = None
        recommended_initial = None
        initial_profiles = {
            "uncertain_or_tightly_coupled": None,
            "isolated_implementation": None,
            "read_only_breadth": None,
        }
        ramp_step = None
    else:
        ordinary_soft_limit = 0
        recommended_initial = 0
        initial_profiles = {
            "uncertain_or_tightly_coupled": 0,
            "isolated_implementation": 0,
            "read_only_breadth": 0,
        }
        ramp_step = 0

    return emit(
        {
            "status": status,
            "codex_binary": binary,
            "actual_version": ".".join(map(str, actual)) if actual else None,
            "features": {
                name: features.get(name)
                for name in (
                    "multi_agent",
                    "multi_agent_v2",
                    "hooks",
                    "goals",
                    "browser_use",
                    "in_app_browser",
                    "computer_use",
                    "apps",
                )
            },
            "config": str(config_path),
            "capabilities": {
                "core_workflow": True,
                "delegation": delegation_available,
                "agent_dispatch": dispatch_registry_ready,
                "governed_hooks": features.get("hooks") == "true",
                "goal_bridge": True if "goal-bridge" in observed_capabilities else None,
                "browser_or_device": True if "browser-or-device" in observed_capabilities else None,
                "external_context": True if "external-context" in observed_capabilities else None,
            },
            "capability_observation": {
                "authority": "effective current-turn callable surface",
                "observed": sorted(observed_capabilities),
                "feature_flags_are_capability_evidence": False,
                "unobserved_optional_capability": None,
            },
            "interaction_contract": {
                "required_mode": "Default",
                "plan_mode_allowed": False,
                "requirement_confirmation_uses": "normal turn boundary and user reply",
            },
            "delegation_capacity": {
                "configured_ceiling": configured_ceiling,
                "configured_ceiling_is_effective_capacity": False,
                "governed_active_child_ceiling": governed_ceiling,
                "ordinary_active_child_soft_limit": ordinary_soft_limit,
                "recommended_initial_active_children": recommended_initial,
                "recommended_initial_active_children_is_task_shaped": False,
                "initial_active_child_profiles": initial_profiles,
                "recommended_ramp_step": ramp_step,
                "effective_active_children": None,
                "effective_capacity_status": "not-observed",
                "productive_active_children": None,
                "productive_capacity_status": "not-observed",
                "admission_policy": (
                    "Bound active children by configured/governed ceilings, ready-task width, isolated "
                    "ownership and resource slots, and root reconciliation capacity; expand one slot "
                    "only after accepted critical-path progress without growing integration backlog, "
                    "conflicts, rework, or disproportionate cost."
                ),
                "saturation_backoff": (
                    "On HTTP 429 or scheduler saturation, stop new dispatches, reconcile active work, "
                    "and reduce the session's observed active-child allowance by at least one before "
                    "retrying unstarted work. Pause admission while terminal results await reconciliation."
                ),
            },
            "required_capability": "delegation" if args.require_delegation else "core-workflow",
            "errors": errors,
            "warnings": warnings,
        },
        0 if not errors else 2,
    )


def flow_metrics_command(args: argparse.Namespace) -> int:
    """Run compatibility-named Flow Activation Coverage without effect scoring."""
    repository = Path(__file__).resolve().parents[3]
    catalog = args.catalog or repository / "evals" / (
        "flow-activation-semantic-cases.json"
        if args.lane == "semantic"
        else "flow-activation-cases.json"
    )
    try:
        if args.lane == "semantic":
            if args.observations is None:
                raise flow_metrics.ActivationContractError(
                    "semantic lane requires --observations from actual first attempts"
                )
            result = flow_metrics.run_semantic_catalog(catalog.resolve(), args.observations.resolve())
        else:
            if args.observations is not None:
                raise flow_metrics.ActivationContractError(
                    "--observations is only valid for the semantic lane"
                )
            result = flow_metrics.run_catalog(catalog.resolve(), Path(__file__).resolve())
    except (OSError, json.JSONDecodeError, flow_metrics.ActivationContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    return emit(result, 0 if result["status"] == "matched" else 1)


def replace_tokens(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace(f"<{key}>", value)
    return text


def init_workstream(args: argparse.Namespace) -> int:
    """Create concise repository-tracked continuity documents for managed work."""
    root = args.root.resolve()
    if not root.is_dir():
        return emit({"status": "error", "errors": [f"repository root does not exist: {root}"]}, 2)
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,80}", args.slug):
        return emit({"status": "error", "errors": ["workstream slug must use 3-81 lowercase safe characters"]}, 2)
    relative = Path(args.path) if args.path else Path("docs") / "workstreams" / args.slug
    try:
        target = contained_path(
            root,
            relative,
            label="workstream path",
            require_relative=True,
            reject_symlinks=True,
        )
    except PathContractError as exc:
        return emit({"status": "error", "errors": [str(exc)]}, 2)

    filenames = ["implementation.md", "progress.md"]
    if args.with_requirements:
        filenames.insert(0, "requirements.md")
    if args.with_design:
        filenames.insert(1 if args.with_requirements else 0, "design.md")
    if args.with_decisions:
        filenames.append("decisions.md")
    if target.exists():
        if not args.reuse or not target.is_dir() or target.is_symlink():
            return emit({"status": "error", "errors": [f"workstream path already exists: {target}"]}, 2)
        invalid = [name for name in filenames if not (target / name).is_file() or (target / name).is_symlink()]
        if invalid:
            return emit(
                {"status": "error", "errors": [f"existing workstream is missing regular files: {', '.join(invalid)}"]},
                2,
            )
        return emit(
            {
                "status": "reused",
                "mode": "managed",
                "workstream": str(target),
                "artifacts": filenames,
            }
        )

    templates = skill_root() / "templates" / "workstream"
    missing = [name for name in filenames if not (templates / name).is_file()]
    if missing:
        return emit({"status": "error", "errors": [f"workstream templates are missing: {', '.join(missing)}"]}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{args.slug}-", dir=target.parent))
    try:
        values = {
            "workstream": args.slug,
            "objective": args.objective.strip(),
            "updated": utc_now(),
        }
        for name in filenames:
            content = replace_tokens((templates / name).read_text(encoding="utf-8"), values)
            atomic_write_text(temporary / name, content)
        temporary.replace(target)
    except (OSError, PathContractError) as exc:
        shutil.rmtree(temporary, ignore_errors=True)
        return emit({"status": "error", "errors": [f"cannot create workstream: {exc}"]}, 2)
    return emit(
        {
            "status": "created",
            "mode": "managed",
            "workstream": str(target),
            "artifacts": filenames,
            "packet": None,
        }
    )


def validate_knowledge_command(args: argparse.Namespace) -> int:
    report = knowledge_system.validate_knowledge_system(
        args.root.resolve(),
        project_root=args.project_root,
        changes_root=args.changes_root,
        convention_path=args.convention_path,
        change_id=args.change_id,
    )
    return emit(report, 0 if report.get("status") == "valid" else 2)


def validate_profile_command(args: argparse.Namespace) -> int:
    try:
        data = engineering_context.read_toml(args.profile.resolve())
    except (OSError, tomllib.TOMLDecodeError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "profile": str(args.profile), "errors": [str(exc)]}, 2)
    errors = engineering_context.validate_profile_data(data, source=str(args.profile.resolve()))
    return emit(
        {"status": "valid" if not errors else "invalid", "profile": str(args.profile.resolve()), "errors": errors},
        0 if not errors else 2,
    )


def resolve_profiles_command(args: argparse.Namespace) -> int:
    try:
        snapshot = engineering_context.resolve_profiles(
            args.root.resolve(),
            facts=args.fact,
            task_paths=args.path,
            codex_home=args.codex_home,
            baseline=skill_root() / "references" / "neutral-baseline.toml",
            task_profiles=args.task_profile,
            profile_mode=args.profile_mode,
        )
    except (OSError, ValueError, tomllib.TOMLDecodeError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if args.output:
        engineering_context.write_json(args.output.resolve(), snapshot)
    code = 2 if snapshot["outcome"] == "blocked" else 0
    return emit({"status": snapshot["outcome"], "output": str(args.output.resolve()) if args.output else None, "snapshot": snapshot}, code)


def methodology_registry_path(path: Path | None = None) -> Path:
    return path.resolve() if path is not None else plugin_root() / "governance" / "methodology-pool.json"


def validate_methods_command(args: argparse.Namespace) -> int:
    """Validate the source, method, and risk-model contracts as one graph."""
    registry_path = methodology_registry_path(args.registry)
    repository_root = args.root.resolve() if args.root else plugin_root()
    try:
        payload = methodology_system.read_registry(registry_path)
        errors = methodology_system.validate_registry(payload, repository_root=repository_root)
    except (OSError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": [str(exc)]}, 2)
    if errors:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": errors}, 2)
    method_risks = set(payload["vocabulary"]["risks"])
    alias_targets = {
        target
        for targets in methodology_system.ENGINEERING_RISK_ALIASES.values()
        for target in targets
    }
    expected_aliases = engineering_context.RISK_TOKENS - method_risks
    unexpected_aliases = sorted(
        set(methodology_system.ENGINEERING_RISK_ALIASES) - expected_aliases
    )
    uncovered_engineering_risks = sorted(
        engineering_context.RISK_TOKENS
        - method_risks
        - set(methodology_system.ENGINEERING_RISK_ALIASES)
    )
    invalid_alias_targets = sorted(alias_targets - method_risks)
    if uncovered_engineering_risks or invalid_alias_targets or unexpected_aliases:
        coverage_errors = []
        if uncovered_engineering_risks:
            coverage_errors.append(
                f"engineering risks lack methodology translation {uncovered_engineering_risks}"
            )
        if invalid_alias_targets:
            coverage_errors.append(
                f"methodology risk aliases target unknown risks {invalid_alias_targets}"
            )
        if unexpected_aliases:
            coverage_errors.append(
                f"methodology risk aliases are not routing-only engineering risks {unexpected_aliases}"
            )
        return emit(
            {"status": "invalid", "registry": str(registry_path), "errors": coverage_errors},
            2,
        )
    return emit(
        {
            "status": "valid",
            "registry": str(registry_path),
            "schema_version": payload["schema_version"],
            "sources": len(payload["sources"]),
            "methods": len(payload["methods"]),
            "risk_models": len(payload["risk_models"]),
            "engineering_risks_covered": len(engineering_context.RISK_TOKENS),
            "risk_aliases": len(methodology_system.ENGINEERING_RISK_ALIASES),
            "phases": payload["selection_contract"]["phase_order"],
        }
    )


def route_task(args: argparse.Namespace) -> int:
    routes: list[str] = ["repo-context"]
    reasons: dict[str, list[str]] = {"repo-context": ["repository facts and task-relative readiness"]}

    def add(skill: str, reason: str) -> None:
        if skill not in routes:
            routes.append(skill)
        reasons.setdefault(skill, []).append(reason)

    try:
        normalized_needs, need_translations = normalize_route_needs(args.need)
    except RouteNeedContractError as exc:
        return emit(
            {
                "status": "invalid",
                "errors": [str(exc)],
                "allowed_needs": sorted(ROUTE_NEEDS),
                "need_aliases": dict(sorted(ROUTE_NEED_ALIASES.items())),
                "suggestions": exc.suggestions,
                "corrected_command": corrected_route_command(
                    args,
                    need_suggestions=exc.suggestions,
                ),
            },
            2,
        )
    needs = set(normalized_needs)
    unknowns = set(args.unknown)
    # An unresolved delivery dimension is not delivery intent or authority.
    needs.update(value for value in unknowns if value in {"architecture", "dependency", "diagnosis", "review"})
    try:
        intent, intent_source = route_intent(args)
    except ValueError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if intent == "delivery":
        needs.add("delivery")
    if args.mutation is not None:
        mutation_intent = args.mutation
    elif args.task_type is not None:
        mutation_intent = "none" if args.task_type == "read-only-audit" else "persistent"
    else:
        mutation_intent = "persistent" if intent == "change" else "none"
    if intent in {"research", "review"} and mutation_intent != "none":
        return emit(
            {
                "status": "invalid",
                "errors": [
                    f"{intent} intent cannot declare persistent mutation; "
                    "use change with --need review for review-and-fix work"
                ],
            },
            2,
        )
    decision_work = intent in {"diagnose", "design", "change"}
    mutating = decision_work and mutation_intent == "persistent"
    input_risks = list(args.risk)
    input_risks.extend(
        {
            "security": "security",
            "data": "persisted-data",
            "compatibility": "compatibility",
            "dependency": "dependency",
        }[value]
        for value in sorted(unknowns & {"security", "data", "compatibility", "dependency"})
    )
    try:
        conservative_risks, risk_translations = normalize_route_risks(input_risks)
        risks = engineering_context.canonical_risks(conservative_risks)
        work_mode, mode_reasons = select_execution_mode(args)
        knowledge = route_knowledge(args, work_mode)
        understanding = route_requirement_understanding(
            args,
            intent=intent,
            work_mode=work_mode,
        )
        capability_activation = route_capability_activation(
            args,
            intent=intent,
            risks=risks,
            needs=needs,
            risk_translations=risk_translations,
            understanding=understanding,
        )
    except RouteRiskContractError as exc:
        known_method_signals = sorted(METHOD_ACTIVATION_SIGNALS | set(METHOD_SIGNAL_ALIASES))
        invalid_method_signals = sorted(
            value
            for value in set(args.method_signal)
            if value not in METHOD_ACTIVATION_SIGNALS and value not in METHOD_SIGNAL_ALIASES
        )
        method_signal_suggestions = {
            value: difflib.get_close_matches(value, known_method_signals, n=1, cutoff=0.45)
            for value in invalid_method_signals
        }
        return emit(
            {
                "status": "invalid",
                "errors": [
                    str(exc),
                    *(
                        [
                            "unknown method activation signal(s): "
                            + ", ".join(invalid_method_signals)
                        ]
                        if invalid_method_signals
                        else []
                    ),
                ],
                "allowed_risks": sorted(engineering_context.RISK_TOKENS),
                "risk_aliases": {
                    key: list(value) for key, value in sorted(ROUTE_RISK_ALIASES.items())
                },
                "suggestions": exc.suggestions,
                "allowed_method_signals": sorted(METHOD_ACTIVATION_SIGNALS),
                "method_signal_aliases": {
                    key: list(value) for key, value in sorted(METHOD_SIGNAL_ALIASES.items())
                },
                "method_signal_suggestions": method_signal_suggestions,
                "corrected_command": corrected_route_command(
                    args,
                    risk_suggestions=exc.suggestions,
                    signal_suggestions=method_signal_suggestions,
                ),
                "risk_signal_guidance": (
                    "Use --risk for an affected engineering consequence; use --method-signal "
                    "for an observed reasoning shape. Do not translate workflow labels into risks."
                ),
            },
            2,
        )
    except MethodSignalContractError as exc:
        return emit(
            {
                "status": "invalid",
                "errors": [str(exc)],
                "allowed_method_signals": sorted(METHOD_ACTIVATION_SIGNALS),
                "method_signal_aliases": {
                    key: list(value) for key, value in sorted(METHOD_SIGNAL_ALIASES.items())
                },
                "suggestions": exc.suggestions,
                "corrected_command": corrected_route_command(
                    args,
                    signal_suggestions=exc.suggestions,
                ),
                "risk_signal_guidance": (
                    "Use --risk for an affected engineering consequence such as concurrency, "
                    "migration, or data-loss; use --method-signal for an observed reasoning "
                    "shape such as state-lifecycle or multi-version-coexistence."
                ),
            },
            2,
        )
    except ValueError as exc:
        invalid_facts = [value for value in args.repo_fact if "=" not in value]
        payload: dict[str, Any] = {"status": "invalid", "errors": [str(exc)]}
        if invalid_facts:
            payload["corrected_command"] = corrected_route_command(
                args,
                fact_replacements={value: f"context={value}" for value in invalid_facts},
            )
            payload["repository_fact_guidance"] = (
                "Use repeatable --repo-fact key=value inputs; context=<bounded prose> "
                "preserves an otherwise unstructured observation without inventing a selector."
            )
        return emit(payload, 2)
    if args.profile_operation:
        add("manage-engineering-profiles", "explicit profile or instruction lifecycle operation")
    if "knowledge" in needs:
        add(
            "repository-knowledge",
            "missing or conflicting canonical owner, chat-only handoff, durable navigation, or knowledge-topology decision",
        )
    if args.ui_impact in {"preserve", "material"} or "ui" in unknowns:
        add(
            "product-ux-discovery",
            "material or unresolved UI intent and UX Ready baseline"
            if args.ui_impact == "material" or "ui" in unknowns
            else "existing UI intent and protected behavior",
        )
    if (
        "requirements" in needs
        or understanding["class"] == "semantic-change"
        or intent == "design"
        or args.ambiguity
        or args.ui_impact == "material"
        or unknowns & {"compatibility", "data", "security", "ui"}
    ):
        add("requirements-design", "material or unresolved product, data, security, or compatibility semantics")
    if intent == "diagnose" or args.task_type == "bugfix" or "diagnosis" in needs or risks & DIAGNOSIS_ROUTING_RISKS:
        add("systematic-debugging", "failure reproduction and causal diagnosis")
    effective_skill_names = {
        value.rsplit(":", 1)[-1] for value in args.effective_skill
    }
    if "test-system" in needs or (
        "weak-tests" in risks and "test-system-engineering" in effective_skill_names
    ):
        add(
            "test-system-engineering",
            "explicit harness-integrity need or observed weak-test mechanism",
        )
    if (
        "architecture" in needs
        or args.task_type in {"large-feature", "large-refactor", "migration", "performance"}
        or intent in {"diagnose", "design", "change", "review"}
        and risks & ARCHITECTURE_ROUTING_RISKS
    ):
        add("architecture-decisions", "material boundary, ownership, state, compatibility, or resource decision")
    if "dependency" in needs or args.task_type == "dependency-change" or decision_work and "dependency" in risks:
        add("dependency-decisions", "dependency, tool, service, plugin, or feature decision")
    if args.suite_maintenance:
        add("dev-flow-maintainer", "explicit Dev Flow suite maintenance")
    if mutating or intent == "delivery" or "verification" in needs:
        add("verification", "risk-based fresh evidence")
    if intent == "review":
        add("verification", "review intent needs current native evidence")
    overlays = risk_overlays(
        args.task_type or "",
        risks,
        needs,
        args.ui_impact,
        args.overlay,
        original_risks=input_risks,
    )
    if (
        intent == "review"
        or "review" in needs
        or capability_activation["independent_review"]["required"]
    ):
        add("change-review", "material exposure, consequential trade-off, evidence conflict, or policy requires independent review")
    if intent == "delivery" or "delivery" in needs:
        add("delivery-readiness", "acceptance, rollback, and delivery authority accounting")
    payload = {
            "status": "routed",
            "kernel": "dev-flow",
            "intent": intent,
            "intent_source": intent_source,
            "legacy_task_type": args.task_type,
            "mutation_intent": mutation_intent,
            "work_mode": work_mode,
            "work_mode_reasons": mode_reasons,
            "risk_overlays": overlays,
            "need_normalization": need_translations,
            "requirement_understanding": understanding,
            "capability_activation": capability_activation,
            "routes": [{"skill": skill, "reasons": reasons[skill]} for skill in routes],
            "unresolved_dimensions": sorted(unknowns),
            "continuity": {
                "documents_required": work_mode == "managed",
                "default_path": "docs/workstreams/<slug>" if work_mode == "managed" else None,
                "artifacts": ["implementation.md", "progress.md"] if work_mode == "managed" else [],
                "conditional_artifacts": ["requirements.md", "design.md", "decisions.md"]
                if work_mode == "managed"
                else [],
                "conditional_artifact_rules": {
                    "requirements.md": "only-confirmed-complex-semantics-not-an-unknown-baseline",
                    "design.md": "only-real-technical-tradeoffs-after-required-semantic-confirmation",
                    "decisions.md": "only-durable-decisions-without-a-repository-native-home",
                }
                if work_mode == "managed"
                else {},
                "update_on": [
                    "scope-or-design-change",
                    "coherent-slice-completion",
                    "new-boundary",
                    "assumption-breaking-first-failure",
                    "blocker",
                    "interruption-or-handoff",
                    "closure",
                ]
                if work_mode == "managed"
                else [],
                "resume": [
                    "read-current-workstream",
                    "verify-git-root-branch-head-and-worktree",
                    "reconcile-changed-paths-and-parallel-changes",
                    "continue-smallest-ready-slice",
                ]
                if work_mode == "managed"
                else [],
                "interruption_handoff": [
                    "done",
                    "current",
                    "next",
                    "blockers-or-unrun-gates",
                    "worktree-and-parallel-change-state",
                ]
                if work_mode == "managed"
                else [],
                "terminal_reconciliation": [
                    "user-outcome",
                    "authoritative-source-and-contract",
                    "final-diff",
                    "last-applicable-oracle",
                    "unrun-environments-and-delivery-boundary",
                ],
                "scope_change": [
                    "retain-unaffected-evidence",
                    "invalidate-affected-plan-and-checks",
                    "mark-stale-descendant-results",
                    "continue-current-slice",
                ],
            },
            "knowledge": knowledge,
            "quality_calibration": {
                "artifact": None,
                "scan": [
                    "business-semantics",
                    "trust-and-data",
                    "compatibility-and-public-contracts",
                    "dependencies-and-external-systems",
                    "operations-delivery-and-irreversibility",
                    "ui-and-accessibility",
                ],
                "recheck_on": [
                    "scope-or-design-change",
                    "new-boundary-or-dependency",
                    "first-surprising-failure",
                    "repeated-failed-hypothesis",
                    "delivery-or-irreversibility",
                ],
            },
            "delegation": "when a child is actually dispatched, use route-agent and do not persist the route",
            "excluded": {
                "manage-engineering-profiles": "ordinary profile consumption does not activate management" if not args.profile_operation else None,
                "dev-flow-maintainer": "explicit-only" if not args.suite_maintenance else None,
                "legacy-packets": "unsupported 1.x internals; never created, loaded, or activated by 2.0 routing",
            },
        }
    try:
        route_basis = route_incremental.build_basis(
            args,
            {
                "intent": intent,
                "intent_source": intent_source,
                "mutation_intent": mutation_intent,
                "work_mode": work_mode,
                "understanding": understanding,
                "needs": needs,
                "risks": risks,
                "knowledge": knowledge,
                "capability_activation": capability_activation,
            },
        )
    except route_incremental.RouteBasisError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    payload["route_basis"] = route_basis
    recalibration: dict[str, Any] | None = None
    if args.previous_route is not None:
        try:
            previous = route_incremental.load_previous(args.previous_route)
        except route_incremental.RouteBasisError:
            previous = {"compatible": False, "reason": "invalid-prior-route"}
        recalibration = route_incremental.compare(route_basis, previous)
        payload["recalibration"] = recalibration
    if args.compact:
        method_selection = capability_activation["method"].get("selection")
        selected_methods = []
        blocked_methods = []
        selection_status = "not-selected"
        if isinstance(method_selection, dict):
            selection_status = str(method_selection.get("status") or "unknown")
            selected_methods = [
                str(value) for value in method_selection.get("selected", []) if isinstance(value, str)
            ]
            blocked_methods = [
                str(item.get("method"))
                for item in method_selection.get("blocked", [])
                if isinstance(item, dict) and isinstance(item.get("method"), str)
            ]
        review = capability_activation["independent_review"]
        payload = {
            "status": payload["status"],
            "intent": payload["intent"],
            "work_mode": payload["work_mode"],
            "requirement_understanding": {
                key: payload["requirement_understanding"][key]
                for key in ("class", "next_action")
            },
            "routes": [item["skill"] for item in payload["routes"]],
            "risk_overlays": [item["overlay"] for item in payload["risk_overlays"]],
            "method": {
                "action": capability_activation["method"].get("action"),
                "status": selection_status,
                "selected": selected_methods,
                "blocked": blocked_methods,
            },
            "independent_review": {
                "required": bool(review.get("required")),
                "execution": review.get("execution"),
                "common_mode_risk": review.get("execution") == "explicit-downgrade",
                "route_agent": review.get("route_agent"),
            },
            "knowledge": payload["knowledge"]["disposition"],
            "route_basis": route_incremental.compact_basis(route_basis),
        }
        if recalibration is not None:
            payload["recalibration"] = recalibration
    return emit(payload)


def check_workstream_command(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    target = args.path if args.path.is_absolute() else root / args.path
    try:
        target = target.resolve()
        if not target.is_relative_to(root):
            raise workstream_contract.WorkstreamContractError(
                "workstream path escaped the repository root"
            )
        payload, code = workstream_contract.check(
            root,
            target,
            check_worktree=args.check_worktree,
            strict=args.strict,
        )
    except (OSError, workstream_contract.WorkstreamContractError) as exc:
        return emit(
            {
                "status": "invalid",
                "claim_limit": "structural-consistency-only",
                "findings": [
                    {"code": "workstream-boundary", "line": 1, "message": str(exc)}
                ],
            },
            2,
        )
    return emit(payload, code)


def resource_lease_command(args: argparse.Namespace) -> int:
    root = args.runtime_root or resource_coordination.default_runtime_root()
    try:
        if args.lease_action == "acquire":
            payload = resource_coordination.acquire(
                root, args.kind, args.resource, args.ttl_seconds, args.owner
            )
        elif args.lease_action == "inspect":
            payload = resource_coordination.inspect(root, args.kind, args.resource)
        elif args.lease_action == "renew":
            payload = resource_coordination.renew(
                root, args.kind, args.resource, args.token, args.ttl_seconds
            )
        else:
            payload = resource_coordination.release(
                root, args.kind, args.resource, args.token
            )
    except resource_coordination.ResourceInputError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    except resource_coordination.ResourceCoordinationError as exc:
        return emit({"status": "unavailable", "errors": [str(exc)]}, 2)
    successful_statuses = {
        "acquire": {"acquired", "expired-recovered"},
        "inspect": {"available", "leased", "expired"},
        "renew": {"renewed"},
        "release": {"released", "available"},
    }
    return emit(
        payload,
        0 if payload.get("status") in successful_statuses[args.lease_action] else 2,
    )


def resource_preflight_command(args: argparse.Namespace) -> int:
    try:
        payload = resource_coordination.preflight(
            args.path,
            args.estimated_growth_bytes,
            args.reserve_bytes,
            args.require_writable,
        )
    except resource_coordination.ResourceInputError as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    except resource_coordination.ResourceCoordinationError as exc:
        return emit({"status": "unavailable", "errors": [str(exc)]}, 2)
    return emit(payload, 0 if payload["status"] in {"observed", "passed"} else 2)


def route_agent_command(args: argparse.Namespace) -> int:
    """Resolve a child role/workload to a concrete Multi-Agent V2 request."""
    try:
        result = agent_dispatch.route_agent(
            role=args.role,
            workload=args.workload,
            risks=args.risk,
            signals=args.signal,
            requested_profile=args.profile,
            acknowledge_exception=args.acknowledge_exception,
            acknowledge_downgrade=args.acknowledge_downgrade,
            registry_path=args.registry,
            task_structure=args.task_structure,
            parallel_units=args.parallel_units,
            tool_density=args.tool_density,
        )
    except (agent_dispatch.DispatchContractError, engineering_context.ContractError) as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    return emit(result)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("unterminated YAML frontmatter")
    result: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if ":" in line and not line.startswith(" "):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def validate_skill(path: Path) -> list[str]:
    errors: list[str] = []
    skill_file = path / "SKILL.md"
    try:
        frontmatter = parse_frontmatter(skill_file)
        if frontmatter.get("name") != path.name:
            errors.append(f"{path.name}: frontmatter name must equal directory name")
        if not frontmatter.get("description"):
            errors.append(f"{path.name}: missing description")
    except (OSError, ValueError) as exc:
        return [f"{path.name}: {exc}"]
    text = skill_file.read_text(encoding="utf-8")
    for reference in re.findall(r"`((?:references|templates|scripts|assets)/[^`]+)`", text):
        if any(char in reference for char in "*<>"):
            continue
        if not (path / reference).exists():
            errors.append(f"{path.name}: broken resource reference {reference}")
    yaml_path = path / "agents" / "openai.yaml"
    if not yaml_path.is_file() or f"${path.name}" not in yaml_path.read_text(encoding="utf-8"):
        errors.append(f"{path.name}: agents/openai.yaml default prompt must mention ${path.name}")
    return errors


def check_plugin(args: argparse.Namespace) -> int:
    root = (args.plugin_root or plugin_root()).resolve()
    errors: list[str] = []
    warnings: list[str] = []
    manifest: dict[str, Any] = {}
    try:
        manifest = read_json(root / ".codex-plugin" / "plugin.json")
        if manifest.get("name") != "dev-flow":
            errors.append("plugin name must be dev-flow")
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", str(manifest.get("version", ""))):
            errors.append("plugin version is not valid semver")
        if manifest.get("license") != "MIT":
            errors.append("plugin license must be MIT")
        for field in ("homepage", "repository"):
            if not str(manifest.get(field, "")).startswith("https://"):
                errors.append(f"plugin {field} must be an absolute HTTPS URL")
        author = manifest.get("author", {})
        if not isinstance(author, dict) or not author.get("name") or not str(author.get("url", "")).startswith("https://"):
            errors.append("plugin author must include a name and absolute HTTPS URL")
        if not isinstance(manifest.get("keywords"), list) or not manifest["keywords"]:
            errors.append("plugin keywords must be a non-empty list")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid plugin manifest: {exc}")

    for required_document in (
        "LICENSE",
        "README.md",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "SECURITY.md",
        ".agents/plugins/marketplace.json",
    ):
        if not (root / required_document).is_file():
            errors.append(f"missing public repository document: {required_document}")

    try:
        marketplace = read_json(root / ".agents" / "plugins" / "marketplace.json")
        entries = marketplace.get("plugins", [])
        matching = [entry for entry in entries if isinstance(entry, dict) and entry.get("name") == manifest.get("name")]
        if len(matching) != 1:
            errors.append("marketplace must contain exactly one dev-flow entry")
        else:
            source = matching[0].get("source", {})
            if source != {"source": "local", "path": "."}:
                errors.append("marketplace plugin source must be the current immutable marketplace snapshot")
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid marketplace manifest: {exc}")

    try:
        capabilities = read_json(root / "governance" / "capability-contracts.json").get("capabilities", [])
        expected_skills = {
            item.get("skill")
            for item in capabilities
            if isinstance(item, dict) and isinstance(item.get("skill"), str) and item["skill"]
        }
    except (OSError, json.JSONDecodeError, AttributeError) as exc:
        errors.append(f"invalid capability registry: {exc}")
        expected_skills = set()
    observed_skills = {path.name for path in (root / "skills").glob("*/") if path.is_dir()}
    if observed_skills != expected_skills:
        errors.append(f"skill inventory mismatch: expected {sorted(expected_skills)}, observed {sorted(observed_skills)}")
    for path in sorted((root / "skills").glob("*/")):
        errors.extend(validate_skill(path))
        skill_lines = (path / "SKILL.md").read_text(encoding="utf-8").count("\n") + 1
        if skill_lines > 500:
            errors.append(f"{path.name}: SKILL.md exceeds the 500-line progressive-disclosure envelope")

    for json_path in sorted(root.rglob("*.json")):
        if "/.git/" in str(json_path):
            continue
        try:
            json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid JSON {json_path.relative_to(root)}: {exc}")

    for toml_path in sorted(root.rglob("*.toml")):
        try:
            tomllib.loads(toml_path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as exc:
            errors.append(f"invalid TOML {toml_path.relative_to(root)}: {exc}")

    hooks = root / "hooks" / "hooks.json"
    if not hooks.is_file():
        errors.append("missing plugin hooks/hooks.json")
    for required in (
        root / "skills" / "dev-flow" / "references" / "neutral-baseline.toml",
        root / "skills" / "architecture-decisions" / "references" / "neutral-policy-registry.json",
        root / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json",
        root / "governance" / "industry-practices.json",
        root / "governance" / "methodology-pool.json",
        root / "evals" / "structural-coverage.json",
    ):
        if not required.is_file():
            errors.append(f"missing required governance file: {required.relative_to(root)}")

    try:
        baseline = engineering_context.read_toml(root / "skills" / "dev-flow" / "references" / "neutral-baseline.toml")
        errors.extend(engineering_context.validate_profile_data(baseline, source="neutral-baseline.toml"))
        engineering_context.load_capability_registry(
            root / "skills" / "dev-flow-maintainer" / "references" / "capability-registry.json"
        )
    except (OSError, tomllib.TOMLDecodeError, json.JSONDecodeError, engineering_context.ContractError) as exc:
        errors.append(f"invalid engineering context governance: {exc}")

    try:
        agent_dispatch.load_registry(
            root / "skills" / "dev-flow" / "references" / "agent-dispatch-profiles.json"
        )
    except (OSError, json.JSONDecodeError, agent_dispatch.DispatchContractError) as exc:
        errors.append(f"invalid agent dispatch registry: {exc}")

    try:
        methodology_registry = methodology_system.read_registry(
            root / "governance" / "methodology-pool.json"
        )
        errors.extend(
            f"methodology registry: {error}"
            for error in methodology_system.validate_registry(
                methodology_registry,
                repository_root=root,
            )
        )
    except (OSError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        errors.append(f"invalid methodology registry: {exc}")

    return emit({"status": "valid" if not errors else "invalid", "plugin": str(root), "errors": errors, "warnings": warnings}, 0 if not errors else 2)


def runtime_config_paths(destination: Path) -> tuple[list[Path], list[Path]]:
    source = skill_root() / "assets" / "agent-configs"
    configs = sorted(source.glob("*.toml"))
    return configs, [destination / config.name for config in configs]


def same_file_contents(left: Path, right: Path) -> bool:
    try:
        if left.stat().st_size != right.stat().st_size:
            return False
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def atomic_copy(source: Path, target: Path) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(prefix=".dev-flow-", dir=target.parent, delete=False) as handle:
            temporary = Path(handle.name)
        shutil.copy2(source, temporary)
        os.replace(temporary, target)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def runtime_destination(args: argparse.Namespace) -> Path:
    configured = args.destination or Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "agents"
    return configured.expanduser()


def install_runtime(args: argparse.Namespace) -> int:
    destination = runtime_destination(args)
    if destination.is_symlink():
        return emit({"status": "blocked", "errors": [f"runtime destination is a symlink: {destination}"]}, 2)
    if destination.exists() and not destination.is_dir():
        return emit({"status": "blocked", "errors": [f"runtime destination is not a directory: {destination}"]}, 2)
    destination.mkdir(parents=True, exist_ok=True)
    configs, targets = runtime_config_paths(destination)
    unchanged: list[str] = []
    to_install: list[tuple[Path, Path]] = []
    conflicts: list[dict[str, str]] = []
    unsafe: list[dict[str, str]] = []

    for config, target in zip(configs, targets, strict=True):
        if target.is_symlink():
            unsafe.append({"path": str(target), "reason": "symlink target is never overwritten"})
        elif not target.exists():
            to_install.append((config, target))
        elif not target.is_file():
            unsafe.append({"path": str(target), "reason": "target exists and is not a regular file"})
        elif same_file_contents(config, target):
            unchanged.append(str(target))
        else:
            conflicts.append({"path": str(target), "reason": "existing file differs from bundled config"})

    if unsafe or (conflicts and not args.force):
        return emit(
            {
                "status": "blocked",
                "installed": [],
                "unchanged": unchanged,
                "conflicts": [*unsafe, *conflicts],
                "hint": "Inspect the conflicts. Use --force only to replace differing regular files after backups are created.",
            },
            2,
        )

    backups: list[dict[str, str]] = []
    if conflicts:
        backup_root = destination / ".dev-flow-backups"
        if backup_root.is_symlink():
            return emit({"status": "blocked", "errors": [f"backup root is a symlink: {backup_root}"]}, 2)
        if backup_root.exists() and not backup_root.is_dir():
            return emit({"status": "blocked", "errors": [f"backup root is not a directory: {backup_root}"]}, 2)
        timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup_dir = backup_root / timestamp
        backup_dir.mkdir(parents=True, exist_ok=False)
        conflict_paths = {entry["path"] for entry in conflicts}
        for config, target in zip(configs, targets, strict=True):
            if str(target) not in conflict_paths:
                continue
            backup = backup_dir / target.name
            shutil.copy2(target, backup)
            backups.append({"source": str(target), "backup": str(backup)})
            to_install.append((config, target))

    installed: list[str] = []
    for config, target in to_install:
        atomic_copy(config, target)
        installed.append(str(target))
    status = "installed" if installed else "unchanged"
    return emit(
        {
            "status": status,
            "installed": installed,
            "unchanged": unchanged,
            "backups": backups,
            "restart_required": bool(installed),
        }
    )


def uninstall_runtime(args: argparse.Namespace) -> int:
    destination = runtime_destination(args)
    if destination.is_symlink():
        return emit({"status": "blocked", "errors": [f"runtime destination is a symlink: {destination}"]}, 2)
    if destination.exists() and not destination.is_dir():
        return emit({"status": "blocked", "errors": [f"runtime destination is not a directory: {destination}"]}, 2)
    configs, targets = runtime_config_paths(destination)
    removable: list[Path] = []
    missing: list[str] = []
    conflicts: list[dict[str, str]] = []

    for config, target in zip(configs, targets, strict=True):
        if target.is_symlink():
            conflicts.append({"path": str(target), "reason": "symlink target is never removed"})
        elif not target.exists():
            missing.append(str(target))
        elif not target.is_file():
            conflicts.append({"path": str(target), "reason": "target exists and is not a regular file"})
        elif same_file_contents(config, target):
            removable.append(target)
        else:
            conflicts.append({"path": str(target), "reason": "file was modified or is not owned by this plugin version"})

    if conflicts:
        return emit(
            {
                "status": "blocked",
                "removed": [],
                "missing": missing,
                "conflicts": conflicts,
                "hint": "No files were removed. Resolve modified or unsafe targets manually, then retry.",
            },
            2,
        )

    for target in removable:
        target.unlink()
    return emit({"status": "uninstalled" if removable else "unchanged", "removed": [str(path) for path in removable], "missing": missing})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    preflight = sub.add_parser("preflight")
    preflight.add_argument("--codex")
    preflight.add_argument("--version-output")
    preflight.add_argument("--features-output-file", type=Path)
    preflight.add_argument("--config", type=Path)
    preflight.add_argument("--skip-config", action="store_true")
    preflight.add_argument("--tool-surface-confirmed", action="store_true")
    preflight.add_argument(
        "--effective-capability",
        action="append",
        choices=("delegation", "goal-bridge", "browser-or-device", "external-context"),
        default=[],
        help="Repeat for a capability actually callable on the current turn; feature flags alone are not evidence",
    )
    preflight.add_argument("--require-delegation", action="store_true")
    preflight.set_defaults(func=codex_preflight)

    workstream = sub.add_parser(
        "init-workstream",
        help="Create concise repository-tracked continuity documents for managed work",
    )
    workstream.add_argument("--root", type=Path, required=True)
    workstream.add_argument("--slug", required=True)
    workstream.add_argument("--objective", required=True)
    workstream.add_argument("--path", help="repository-relative workstream directory")
    workstream.add_argument(
        "--with-requirements",
        action="store_true",
        help=(
            "Add only when confirmed complex semantics already exist; unknown baselines or "
            "unanswered questions stay in implementation/progress"
        ),
    )
    workstream.add_argument("--with-design", action="store_true")
    workstream.add_argument("--with-decisions", action="store_true")
    workstream.add_argument("--reuse", action="store_true")
    workstream.set_defaults(func=init_workstream)

    knowledge = sub.add_parser("validate-knowledge", help="Validate tracked project truth and change dossiers")
    knowledge.add_argument("--root", type=Path, required=True)
    knowledge.add_argument("--project-root")
    knowledge.add_argument("--changes-root")
    knowledge.add_argument("--convention-path", default=knowledge_system.DEFAULT_CONVENTION_PATH)
    knowledge.add_argument("--change-id")
    knowledge.set_defaults(func=validate_knowledge_command)

    profile = sub.add_parser("validate-profile", help="Validate one engineering profile TOML file")
    profile.add_argument("profile", type=Path)
    profile.set_defaults(func=validate_profile_command)

    resolve = sub.add_parser("resolve-profiles", help="Resolve layered engineering profiles for a task")
    resolve.add_argument("--root", type=Path, required=True)
    resolve.add_argument("--output", type=Path)
    resolve.add_argument("--path", action="append", default=[])
    resolve.add_argument("--fact", action="append", default=[])
    resolve.add_argument("--task-profile", type=Path, action="append", default=[])
    resolve.add_argument("--codex-home", type=Path)
    resolve.add_argument("--profile-mode", choices=sorted(engineering_context.PROFILE_MODES), default="personal-interactive")
    resolve.set_defaults(func=resolve_profiles_command)

    validate_methods = sub.add_parser(
        "validate-methods",
        help="Validate the assurance methodology pool, sources, references, and risk models",
    )
    validate_methods.add_argument("--registry", type=Path)
    validate_methods.add_argument("--root", type=Path)
    validate_methods.set_defaults(func=validate_methods_command)

    route = sub.add_parser("route-task", help="Select the minimal built-in Skill composition for a classified task")
    route_kind = route.add_mutually_exclusive_group(required=True)
    route_kind.add_argument("--intent", choices=sorted(ACCEPTED_TASK_INTENTS))
    route_kind.add_argument(
        "--task-type",
        choices=sorted(TASK_TYPES),
        help="Unsupported 1.x parser residue; 2.0 callers use --intent",
    )
    route.add_argument(
        "--risk",
        action="append",
        default=[],
        help="Affected engineering consequence; repeat as needed and use structured invalid output for canonical values",
    )
    route.add_argument(
        "--target-revision",
        help="Optional opaque target/scope epoch; change it after a material objective, path, or authority correction",
    )
    route.add_argument(
        "--need",
        action="append",
        default=[],
        help=(
            "Required capability; canonical short names and corresponding specialist Skill "
            "names are accepted, and invalid values return a structured correction"
        ),
    )
    route.add_argument("--ui-impact", choices=sorted(UI_IMPACTS), default="none")
    route.add_argument("--ambiguity", action="store_true")
    route.add_argument("--material-exposure", action="store_true")
    route.add_argument(
        "--independent-review-authorized",
        action="store_true",
        help=(
            "Deprecated compatibility input; reviewer dispatch is internal work allocation and this flag has no routing effect"
        ),
    )
    route.add_argument(
        "--repo-fact",
        "--repository-fact",
        "--repository-facts",
        dest="repo_fact",
        action="append",
        default=[],
        help="Observed repository fact as key=value; repeat for language/framework facts",
    )
    route.add_argument(
        "--effective-skill",
        action="append",
        default=[],
        help="Skill exposed on the current turn; plugin-prefixed names are accepted",
    )
    route.add_argument(
        "--method-signal",
        action="append",
        default=[],
        help="Observed high-leverage reasoning shape; model-evaluation is explicit and weak-tests derives the cheaper oracle challenge",
    )
    route.add_argument(
        "--method-prerequisite",
        action="append",
        default=[],
        help="Observed methodology prerequisite; repeat and never invent unavailable evidence",
    )
    route.add_argument(
        "--method-depth",
        choices=("starter", "deep"),
        help="Bounded method depth override; formal methods remain an explicit separate choice",
    )
    route.add_argument(
        "--requirement-class",
        type=normalize_requirement_class,
        choices=sorted(REQUIREMENT_CLASSES),
        help="Semantic understanding depth; U1-U5 aliases are accepted and output remains canonical",
    )
    route_confirmation = route.add_mutually_exclusive_group()
    route_confirmation.add_argument(
        "--understanding-confirmed",
        action="store_true",
        help="The complete U1 understanding was explicitly confirmed; retain semantic-change and continue",
    )
    route_confirmation.add_argument(
        "--waive-understanding-confirmation",
        action="store_true",
        help="The request explicitly waives U1 reconfirmation; retain semantic-change and continue",
    )
    route_confirmation.add_argument(
        "--user-choice-open",
        action="store_true",
        help="A surviving user-owned semantic choice changes the result; publish U1 understanding and pause",
    )
    route.add_argument("--profile-operation", action="store_true")
    route.add_argument("--suite-maintenance", action="store_true")
    route.add_argument(
        "--mutation",
        choices=("none", "persistent"),
        help="Repository mutation intent; external delivery authority remains separate",
    )
    route.add_argument(
        "--unknown",
        choices=sorted(ROUTE_UNKNOWNS),
        action="append",
        default=[],
        help="Unresolved risk dimension; route conservatively until repository evidence closes it",
    )
    route.add_argument("--work-mode", choices=("auto", *sorted(EXECUTION_MODES)), default="auto")
    route.add_argument("--multi-session", action="store_true")
    route.add_argument("--multi-slice", action="store_true")
    route.add_argument("--cross-module", action="store_true")
    route.add_argument("--coordination", action="store_true")
    route.add_argument("--material-tradeoff", action="store_true")
    route.add_argument("--durable-plan", action="store_true")
    route.add_argument(
        "--knowledge-impact",
        choices=sorted(ROUTE_KNOWLEDGE_IMPACTS),
        action="append",
        default=[],
        help="Repository knowledge consequence; re-evaluate after discovery and before close",
    )
    route.add_argument(
        "--overlay",
        choices=sorted(ROUTE_OVERLAYS),
        action="append",
        default=[],
    )
    route.add_argument(
        "--previous-route",
        type=Path,
        help="Caller-owned bounded prior compatible route JSON for stateless recalibration",
    )
    route_output = route.add_mutually_exclusive_group()
    route_output.add_argument(
        "--compact",
        action="store_true",
        help="Emit only decisions, method ids, review disposition, and a digest-only route identity",
    )
    route_output.add_argument(
        "--explain",
        action="store_true",
        help="Emit the complete explanatory route envelope (the default)",
    )
    route.set_defaults(func=route_task)

    workstream_check = sub.add_parser(
        "check-workstream",
        help="Check an opted-in managed workstream for structural consistency",
    )
    workstream_check.add_argument("--root", type=Path, required=True)
    workstream_check.add_argument("--path", type=Path, required=True)
    workstream_check.add_argument("--check-worktree", action="store_true")
    workstream_check.add_argument("--strict", action="store_true")
    workstream_check.set_defaults(func=check_workstream_command)

    lease = sub.add_parser(
        "resource-lease",
        help="Coordinate an allowlisted single-host resource among cooperating tasks",
    )
    lease.add_argument("--runtime-root", type=Path)
    lease_sub = lease.add_subparsers(dest="lease_action", required=True)
    for action in ("acquire", "inspect", "renew", "release"):
        lease_action = lease_sub.add_parser(action)
        lease_action.add_argument(
            "--kind",
            required=True,
            help=f"allowlisted resource kind: {', '.join(sorted(resource_coordination.KINDS))}",
        )
        lease_action.add_argument("--resource", required=True)
        if action in {"acquire", "renew"}:
            lease_action.add_argument("--ttl-seconds", type=int, required=True)
        if action == "acquire":
            lease_action.add_argument("--owner")
        if action in {"renew", "release"}:
            lease_action.add_argument("--token", required=True)
        lease_action.set_defaults(func=resource_lease_command)

    resource_preflight = sub.add_parser(
        "resource-preflight",
        help="Measure capacity and optional writability without choosing cleanup policy",
    )
    resource_preflight.add_argument("--path", type=Path, required=True)
    resource_preflight.add_argument("--estimated-growth-bytes", type=int)
    resource_preflight.add_argument("--reserve-bytes", type=int)
    resource_preflight.add_argument("--require-writable", action="store_true")
    resource_preflight.set_defaults(func=resource_preflight_command)

    agent_route = sub.add_parser(
        "route-agent",
        help="Select a deterministic Multi-Agent V2 dispatch profile for one child workload",
    )
    agent_route.add_argument("--role", required=True)
    agent_route.add_argument("--workload", required=True)
    agent_route.add_argument(
        "--risk",
        action="append",
        choices=sorted(engineering_context.RISK_TOKENS),
        default=[],
        help="Observed engineering risk; repeat as needed",
    )
    agent_route.add_argument("--signal", action="append", default=[])
    agent_route.add_argument("--profile")
    agent_route.add_argument(
        "--task-structure",
        choices=sorted(agent_dispatch.TASK_STRUCTURES),
        default="independent",
        help="Only an independently useful unit qualifies for child dispatch",
    )
    agent_route.add_argument(
        "--parallel-units",
        type=int,
        default=1,
        help="Observed independent units, not an agent-count request",
    )
    agent_route.add_argument(
        "--tool-density",
        choices=sorted(agent_dispatch.TOOL_DENSITIES),
        default="low",
        help="Diagnostic only; high tool volume never justifies delegation",
    )
    agent_route.add_argument(
        "--acknowledge-exception",
        action="store_true",
        help="Required for the explicit PX exceptional profile",
    )
    agent_route.add_argument(
        "--acknowledge-downgrade",
        action="store_true",
        help="Allow an explicit profile below the policy minimum without hiding the downgrade",
    )
    agent_route.add_argument("--registry", type=Path)
    agent_route.set_defaults(func=route_agent_command)

    activation = sub.add_parser(
        "flow-metrics",
        help="Run Flow Activation Coverage; this compatibility name never measures effect or productivity",
    )
    activation.add_argument("--catalog", type=Path)
    activation.add_argument(
        "--lane",
        choices=("deterministic", "semantic"),
        default="deterministic",
    )
    activation.add_argument("--observations", type=Path)
    activation.set_defaults(func=flow_metrics_command)

    runtime_doctor.add_parser(sub, default_root=Path(__file__).resolve().parents[3])
    outcome_observation.add_parser(sub)

    check = sub.add_parser("check")
    check.add_argument("--plugin-root", type=Path)
    check.set_defaults(func=check_plugin)

    install = sub.add_parser("install-runtime", help="Install bundled Codex agent configs without silent overwrite")
    install.add_argument("--destination", type=Path)
    install.add_argument("--force", action="store_true", help="Back up and replace differing regular files")
    install.set_defaults(func=install_runtime)

    uninstall = sub.add_parser("uninstall-runtime", help="Remove only unmodified bundled Codex agent configs")
    uninstall.add_argument("--destination", type=Path)
    uninstall.set_defaults(func=uninstall_runtime)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    normalized_argv, aliases_used, invalid = preprocess_route_argv(raw_argv)
    if invalid is not None:
        return emit(invalid, 2)
    parser = build_parser()
    args = parser.parse_args(normalized_argv)
    if args.command == "route-task":
        args.intent_alias_input = aliases_used.get("--intent")
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
