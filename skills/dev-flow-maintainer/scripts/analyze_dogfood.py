#!/usr/bin/env python3
"""Aggregate privacy-minimized Dev Flow dogfood observations."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


INPUT_SCHEMA = "dev-flow.dogfood.observations.v1"
OUTPUT_SCHEMA = "dev-flow.dogfood.aggregate.v1"
INPUT_SCHEMA_V2 = "dev-flow.dogfood.observations.v2"
OUTPUT_SCHEMA_V2 = "dev-flow.dogfood.aggregate.v2"
MAX_OBSERVATIONS = 10_000
TASK_SHAPES = {
    "audit",
    "cross-task-synthesis",
    "design",
    "diagnosis",
    "implementation",
    "long-process",
    "ordinary-conversation",
    "repository-knowledge",
    "review",
    "verification",
}
TRANSITIONS = {
    "none",
    "blocked-to-ready",
    "fork",
    "intent-change",
    "new-platform",
    "resume",
    "review-to-verification",
    "scope-recalibration",
}
CORRECTIONS = {
    "none",
    "adjacent-work-deferred",
    "changed-path-restored",
    "method-fallback-added",
    "method-realization-added",
    "platform-boundary-restored",
    "reference-not-requirement",
    "scope-narrowed",
}
SCOPE_MODES = {"closed", "bounded", "open", "not-applicable"}
READINESS = {"not-applicable", "ready", "blocked"}
DISPOSITIONS = {"not-applicable", "execute-ready", "fallback", "abstain"}
EVIDENCE_EFFECTS = {
    "not-observed",
    "claim-limited",
    "decision-changed",
    "oracle-changed",
}
PREFLIGHT_RESULTS = {"not-run", "observed", "passed", "blocked", "unavailable"}
LEASE_RESULTS = {"none", "acquired", "conflict", "unavailable"}
WORKSTREAM_RESULTS = {"not-applicable", "passed", "failed"}
WORKSTREAM_CONTRADICTIONS = {
    "ambiguous-worktree-path",
    "convergence-decision-required",
    "duplicate-id",
    "invalid-state",
    "missing-marker",
    "open-hard-condition",
    "protected-path-changed",
    "unsafe-prefix",
}
NEGATIVE_CONTROL_RESULTS = {
    "not-run",
    "failed-as-expected",
    "unexpected-pass",
    "unavailable",
}
EVIDENCE_STATUSES = {"passed", "failed", "flaky", "blocked", "not-run", "waived"}


class DogfoodContractError(ValueError):
    """Raised when sanitized dogfood input violates its bounded schema."""


def require_bool(value: Any, label: str) -> bool:
    if not isinstance(value, bool):
        raise DogfoodContractError(f"{label} must be boolean")
    return value


def require_enum(value: Any, allowed: set[str], label: str) -> str:
    if not isinstance(value, str) or value not in allowed:
        raise DogfoodContractError(f"{label} must be one of {sorted(allowed)}")
    return value


def require_enum_list(value: Any, allowed: set[str], label: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or item not in allowed for item in value)
        or len(value) != len(set(value))
    ):
        raise DogfoodContractError(
            f"{label} must be a unique non-empty list from {sorted(allowed)}"
        )
    return value


def require_count(value: Any, label: str, *, maximum: int = 1000) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0 or value > maximum:
        raise DogfoodContractError(f"{label} must be an integer from 0 to {maximum}")
    return value


def validate_method(value: Any, label: str) -> dict[str, Any]:
    fields = {
        "eligible",
        "activated",
        "selected",
        "readiness",
        "disposition",
        "realized",
        "evidence_effect",
    }
    if not isinstance(value, dict) or set(value) != fields:
        raise DogfoodContractError(f"{label} must use the exact sanitized method schema")
    eligible = require_bool(value["eligible"], f"{label}.eligible")
    activated = require_bool(value["activated"], f"{label}.activated")
    selected = require_bool(value["selected"], f"{label}.selected")
    readiness = require_enum(value["readiness"], READINESS, f"{label}.readiness")
    disposition = require_enum(
        value["disposition"], DISPOSITIONS, f"{label}.disposition"
    )
    realized = require_bool(value["realized"], f"{label}.realized")
    effect = require_enum(
        value["evidence_effect"], EVIDENCE_EFFECTS, f"{label}.evidence_effect"
    )
    if not eligible and (
        activated
        or selected
        or readiness != "not-applicable"
        or disposition != "not-applicable"
        or realized
        or effect != "not-observed"
    ):
        raise DogfoodContractError(f"{label}: ineligible methods must remain inactive")
    if selected and not activated:
        raise DogfoodContractError(f"{label}: selection requires activation")
    if not selected and readiness != "not-applicable":
        raise DogfoodContractError(f"{label}: readiness requires a selected candidate")
    if selected and readiness == "not-applicable":
        raise DogfoodContractError(f"{label}: selected candidate requires ready or blocked")
    if disposition == "execute-ready" and readiness != "ready":
        raise DogfoodContractError(f"{label}: execute-ready requires ready")
    if disposition == "fallback" and readiness != "blocked":
        raise DogfoodContractError(f"{label}: fallback requires blocked")
    if disposition == "abstain" and (not activated or selected):
        raise DogfoodContractError(
            f"{label}: abstention requires activation without candidate selection"
        )
    if realized and disposition not in {"execute-ready", "fallback"}:
        raise DogfoodContractError(f"{label}: realization requires execution or fallback")
    if realized != (effect != "not-observed"):
        raise DogfoodContractError(
            f"{label}: realization and evidence_effect must change together"
        )
    return value


def validate_payload(payload: Any) -> tuple[str, list[dict[str, Any]]]:
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "observations"}:
        raise DogfoodContractError(
            "input must contain only schema_version and observations; raw transcripts, ids, paths, scores, and free-form notes are forbidden"
        )
    schema = payload["schema_version"]
    if schema not in {INPUT_SCHEMA, INPUT_SCHEMA_V2}:
        raise DogfoodContractError(
            f"schema_version must be {INPUT_SCHEMA} or {INPUT_SCHEMA_V2}"
        )
    observations = payload["observations"]
    if (
        not isinstance(observations, list)
        or not observations
        or len(observations) > MAX_OBSERVATIONS
    ):
        raise DogfoodContractError(
            f"observations must contain 1-{MAX_OBSERVATIONS} aggregate-safe entries"
        )
    expected_fields = {
        "task_shape",
        "dev_flow_expected",
        "transitions",
        "corrections",
        "scope",
        "method",
    }
    if schema == INPUT_SCHEMA_V2:
        expected_fields.add("rc4")
    for index, observation in enumerate(observations):
        label = f"observations[{index}]"
        if not isinstance(observation, dict) or set(observation) != expected_fields:
            raise DogfoodContractError(
                f"{label} must use the exact aggregate-safe schema; raw content and stable identifiers are forbidden"
            )
        shape = require_enum(observation["task_shape"], TASK_SHAPES, f"{label}.task_shape")
        expected = require_bool(
            observation["dev_flow_expected"], f"{label}.dev_flow_expected"
        )
        require_enum_list(observation["transitions"], TRANSITIONS, f"{label}.transitions")
        require_enum_list(observation["corrections"], CORRECTIONS, f"{label}.corrections")
        scope = observation["scope"]
        if not isinstance(scope, dict) or set(scope) != {"mode", "conformed"}:
            raise DogfoodContractError(f"{label}.scope must contain mode and conformed")
        mode = require_enum(scope["mode"], SCOPE_MODES, f"{label}.scope.mode")
        require_bool(scope["conformed"], f"{label}.scope.conformed")
        validate_method(observation["method"], f"{label}.method")
        if schema == INPUT_SCHEMA_V2:
            rc4 = observation["rc4"]
            rc4_fields = {"route", "convergence", "resource", "workstream", "test_system", "evidence_status"}
            if not isinstance(rc4, dict) or set(rc4) != rc4_fields:
                raise DogfoodContractError(
                    f"{label}.rc4 must use the exact aggregate-safe v2 schema"
                )
            route = rc4["route"]
            if not isinstance(route, dict) or set(route) != {"initial", "material_transitions", "delta_routes", "unchanged_routes"}:
                raise DogfoodContractError(f"{label}.rc4.route must use the exact bounded count schema")
            initial = require_count(route["initial"], f"{label}.rc4.route.initial", maximum=1)
            transitions = require_count(route["material_transitions"], f"{label}.rc4.route.material_transitions")
            delta = require_count(route["delta_routes"], f"{label}.rc4.route.delta_routes")
            unchanged = require_count(route["unchanged_routes"], f"{label}.rc4.route.unchanged_routes")
            if delta + unchanged > initial + transitions:
                raise DogfoodContractError(f"{label}.rc4.route outcomes exceed available route events")
            convergence = rc4["convergence"]
            if not isinstance(convergence, dict) or set(convergence) != {"checkpoint_required", "checkpoint_resolved", "third_tweak"}:
                raise DogfoodContractError(f"{label}.rc4.convergence must use the exact boolean schema")
            for field in convergence:
                require_bool(convergence[field], f"{label}.rc4.convergence.{field}")
            if convergence["checkpoint_resolved"] and not convergence["checkpoint_required"]:
                raise DogfoodContractError(f"{label}.rc4.convergence cannot resolve an unrequired checkpoint")
            resource = rc4["resource"]
            if not isinstance(resource, dict) or set(resource) != {"preflight", "lease"}:
                raise DogfoodContractError(f"{label}.rc4.resource must use preflight and lease")
            require_enum(resource["preflight"], PREFLIGHT_RESULTS, f"{label}.rc4.resource.preflight")
            require_enum(resource["lease"], LEASE_RESULTS, f"{label}.rc4.resource.lease")
            workstream = rc4["workstream"]
            if not isinstance(workstream, dict) or set(workstream) != {"check", "contradictions"}:
                raise DogfoodContractError(f"{label}.rc4.workstream must use check and contradictions")
            check = require_enum(workstream["check"], WORKSTREAM_RESULTS, f"{label}.rc4.workstream.check")
            contradictions = workstream["contradictions"]
            if not isinstance(contradictions, list) or len(contradictions) != len(set(contradictions)) or any(item not in WORKSTREAM_CONTRADICTIONS for item in contradictions):
                raise DogfoodContractError(f"{label}.rc4.workstream.contradictions must be a bounded unique enum list")
            if (check == "failed") != bool(contradictions):
                raise DogfoodContractError(f"{label}.rc4.workstream failed status and contradictions must agree")
            test_system = rc4["test_system"]
            if not isinstance(test_system, dict) or set(test_system) != {"eligible", "activated", "negative_control"}:
                raise DogfoodContractError(f"{label}.rc4.test_system must use the exact integrity schema")
            eligible = require_bool(test_system["eligible"], f"{label}.rc4.test_system.eligible")
            activated = require_bool(test_system["activated"], f"{label}.rc4.test_system.activated")
            negative = require_enum(test_system["negative_control"], NEGATIVE_CONTROL_RESULTS, f"{label}.rc4.test_system.negative_control")
            if activated and not eligible:
                raise DogfoodContractError(f"{label}.rc4.test_system activation requires eligibility")
            if not activated and negative != "not-run":
                raise DogfoodContractError(f"{label}.rc4.test_system negative control requires activation")
            require_enum(
                rc4["evidence_status"],
                EVIDENCE_STATUSES,
                f"{label}.rc4.evidence_status",
            )
        if shape == "ordinary-conversation" and (expected or mode != "not-applicable"):
            raise DogfoodContractError(
                f"{label}: ordinary conversation must remain a negative control"
            )
    return schema, observations


def count_values(observations: list[dict[str, Any]], field: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for observation in observations:
        counts.update(observation[field])
    return dict(sorted(counts.items()))


def analyze(payload: Any) -> dict[str, Any]:
    schema, observations = validate_payload(payload)
    shape_counts = Counter(item["task_shape"] for item in observations)
    mode_counts = Counter(item["scope"]["mode"] for item in observations)
    methods = [item["method"] for item in observations]
    method_funnel = {
        "eligible": sum(item["eligible"] for item in methods),
        "activated": sum(item["activated"] for item in methods),
        "selected": sum(item["selected"] for item in methods),
        "ready": sum(item["readiness"] == "ready" for item in methods),
        "blocked": sum(item["readiness"] == "blocked" for item in methods),
        "execute_ready": sum(item["disposition"] == "execute-ready" for item in methods),
        "fallback": sum(item["disposition"] == "fallback" for item in methods),
        "abstain": sum(item["disposition"] == "abstain" for item in methods),
        "missing_disposition": sum(
            item["selected"] and item["disposition"] == "not-applicable"
            for item in methods
        ),
        "realized": sum(item["realized"] for item in methods),
        "evidence_effects": dict(
            sorted(Counter(item["evidence_effect"] for item in methods).items())
        ),
    }
    result = {
        "status": "analyzed",
        "schema_version": OUTPUT_SCHEMA if schema == INPUT_SCHEMA else OUTPUT_SCHEMA_V2,
        "purpose": "privacy-minimized behavior diagnostics only",
        "privacy": {
            "raw_content_retained": False,
            "stable_identifiers_retained": False,
            "personal_or_repository_score": False,
        },
        "totals": {
            "observations": len(observations),
            "dev_flow_expected": sum(item["dev_flow_expected"] for item in observations),
            "negative_controls": sum(
                not item["dev_flow_expected"] for item in observations
            ),
        },
        "task_shapes": dict(sorted(shape_counts.items())),
        "transitions": count_values(observations, "transitions"),
        "corrections": count_values(observations, "corrections"),
        "scope": {
            "modes": dict(sorted(mode_counts.items())),
            "conformed": sum(item["scope"]["conformed"] for item in observations),
            "violations": sum(not item["scope"]["conformed"] for item in observations),
        },
        "method_funnel": method_funnel,
        "aggregate_score": None,
        "limitations": [
            "selected authorized observations are not a population sample",
            "visible artifacts cannot reveal unrecorded internal reasoning",
            "counts do not establish productivity or causal method value",
        ],
    }
    if schema == INPUT_SCHEMA_V2:
        rc4 = [item["rc4"] for item in observations]
        result["rc4"] = {
            "route": {
                field: sum(item["route"][field] for item in rc4)
                for field in ("initial", "material_transitions", "delta_routes", "unchanged_routes")
            },
            "convergence": {
                field: sum(item["convergence"][field] for item in rc4)
                for field in ("checkpoint_required", "checkpoint_resolved", "third_tweak")
            },
            "resource": {
                field: dict(sorted(Counter(item["resource"][field] for item in rc4).items()))
                for field in ("preflight", "lease")
            },
            "workstream": {
                "checks": dict(sorted(Counter(item["workstream"]["check"] for item in rc4).items())),
                "contradictions": dict(sorted(Counter(value for item in rc4 for value in item["workstream"]["contradictions"]).items())),
            },
            "test_system": {
                "eligible": sum(item["test_system"]["eligible"] for item in rc4),
                "activated": sum(item["test_system"]["activated"] for item in rc4),
                "negative_controls": dict(sorted(Counter(item["test_system"]["negative_control"] for item in rc4).items())),
            },
            "evidence_status": dict(sorted(Counter(item["evidence_status"] for item in rc4).items())),
        }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="sanitized observation JSON")
    args = parser.parse_args(argv)
    try:
        result = analyze(json.loads(args.input.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, DogfoodContractError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
