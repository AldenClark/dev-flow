#!/usr/bin/env python3
"""Validate and select Dev Flow assurance methods from explicit task facts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
OUTPUT_SCHEMA = "method.selection.v1"
ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,79}$")
SOURCE_ID_RE = re.compile(r"^SRC-[A-Z0-9-]+$")
RISK_MODEL_ID_RE = re.compile(r"^RM-[A-Z0-9-]+$")
METHOD_FIELDS = {
    "id",
    "name",
    "family",
    "summary",
    "phases",
    "owner",
    "depth",
    "selection",
    "cost",
    "risks",
    "signals",
    "negative_signals",
    "positive_trigger",
    "negative_trigger",
    "prerequisites",
    "outputs",
    "steps",
    "evidence",
    "fallback",
    "limitations",
    "source_ids",
    "guidance_ref",
}
SOURCE_FIELDS = {"id", "title", "url", "kind", "checked_at"}
RISK_MODEL_FIELDS = {
    "id",
    "name",
    "match",
    "minimum_score",
    "failure_hypothesis",
    "method_ids",
    "evidence_obligations",
    "escalation",
}
MATCH_FIELDS = {"risks", "signals", "task_types"}
NEGATIVE_RULE_FIELDS = {"id", "signals", "unless_signals", "depths", "method_ids", "reason"}
SELECTION_KINDS = {"foundation", "automatic", "specialist"}
COSTS = {"low", "medium", "high", "very-high"}
MATCH_WEIGHTS = {"risks": 1, "signals": 3, "task_types": 1}


class MethodologyContractError(ValueError):
    """Raised when the methodology registry or selection request is invalid."""


def read_registry(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise MethodologyContractError("methodology registry must be a JSON object")
    return payload


def _string_list(value: Any, label: str, *, allow_empty: bool = False) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        return [], [f"{label} must be a list of non-empty strings"]
    if not allow_empty and not value:
        errors.append(f"{label} must not be empty")
    if len(value) != len(set(value)):
        errors.append(f"{label} must contain unique values")
    return value, errors


def _nonempty_string(record: dict[str, Any], field: str, label: str, errors: list[str]) -> None:
    if not isinstance(record.get(field), str) or not record[field].strip():
        errors.append(f"{label}.{field} must be a non-empty string")


def validate_registry(payload: dict[str, Any], *, repository_root: Path | None = None) -> list[str]:
    """Return deterministic contract errors for a methodology registry."""
    errors: list[str] = []
    expected_top = {
        "schema_version",
        "title",
        "checked_at",
        "scope_note",
        "selection_contract",
        "vocabulary",
        "sources",
        "methods",
        "risk_models",
    }
    if set(payload) != expected_top:
        errors.append(
            "registry top-level fields must be exactly " + ", ".join(sorted(expected_top))
        )
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"registry schema_version must be {SCHEMA_VERSION}")
    for field in ("title", "checked_at", "scope_note"):
        _nonempty_string(payload, field, "registry", errors)

    contract = payload.get("selection_contract")
    if not isinstance(contract, dict):
        errors.append("selection_contract must be an object")
        contract = {}
    expected_contract = {
        "output_schema",
        "depths",
        "phase_order",
        "default_max_methods",
        "selection_kinds",
        "global_negative_rules",
        "rule",
        "reselection_triggers",
    }
    if set(contract) != expected_contract:
        errors.append(
            "selection_contract fields must be exactly "
            + ", ".join(sorted(expected_contract))
        )
    if contract.get("output_schema") != OUTPUT_SCHEMA:
        errors.append(f"selection_contract.output_schema must be {OUTPUT_SCHEMA}")
    depths, depth_errors = _string_list(contract.get("depths"), "selection_contract.depths")
    errors.extend(depth_errors)
    if depths != ["starter", "deep", "formal"]:
        errors.append("selection_contract.depths must be ordered starter, deep, formal")
    phases, phase_errors = _string_list(
        contract.get("phase_order"), "selection_contract.phase_order"
    )
    errors.extend(phase_errors)
    selection_kinds, kind_errors = _string_list(
        contract.get("selection_kinds"), "selection_contract.selection_kinds"
    )
    errors.extend(kind_errors)
    if set(selection_kinds) != SELECTION_KINDS:
        errors.append("selection_contract.selection_kinds has unknown or missing kinds")
    negative_rules = contract.get("global_negative_rules")
    if not isinstance(negative_rules, list) or not negative_rules:
        errors.append("selection_contract.global_negative_rules must be a non-empty list")
        negative_rules = []
    negative_rule_ids: set[str] = set()
    for index, rule in enumerate(negative_rules):
        label = f"selection_contract.global_negative_rules[{index}]"
        if not isinstance(rule, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(rule) != NEGATIVE_RULE_FIELDS:
            errors.append(f"{label} fields must be exactly {', '.join(sorted(NEGATIVE_RULE_FIELDS))}")
        for field in ("id", "reason"):
            _nonempty_string(rule, field, label, errors)
        rule_id = rule.get("id")
        if isinstance(rule_id, str):
            if not rule_id.startswith("NEG-"):
                errors.append(f"{label}.id must start with NEG-")
            if rule_id in negative_rule_ids:
                errors.append(f"duplicate global negative rule id {rule_id}")
            negative_rule_ids.add(rule_id)
        for field in ("signals", "unless_signals", "depths", "method_ids"):
            values, value_errors = _string_list(
                rule.get(field), f"{label}.{field}", allow_empty=field in {"unless_signals", "depths", "method_ids"}
            )
            errors.extend(value_errors)
            if field == "depths":
                unknown = sorted(set(values) - set(depths))
                if unknown:
                    errors.append(f"{label}.depths contains unknown depths {unknown}")
    default_max = contract.get("default_max_methods")
    if not isinstance(default_max, dict) or set(default_max) != set(depths):
        errors.append("selection_contract.default_max_methods must map every depth exactly once")
    elif any(not isinstance(value, int) or isinstance(value, bool) or value < 1 for value in default_max.values()):
        errors.append("selection_contract.default_max_methods values must be positive integers")
    _nonempty_string(contract, "rule", "selection_contract", errors)
    reselection, reselection_errors = _string_list(
        contract.get("reselection_triggers"),
        "selection_contract.reselection_triggers",
    )
    errors.extend(reselection_errors)
    if not {"phase-change", "risk-change", "premise-change"}.issubset(set(reselection)):
        errors.append("selection_contract.reselection_triggers must include phase, risk, and premise change")

    vocabulary = payload.get("vocabulary")
    expected_vocabulary = {"phases", "owners", "task_types", "risks", "signals", "prerequisites"}
    if not isinstance(vocabulary, dict):
        errors.append("vocabulary must be an object")
        vocabulary = {}
    if set(vocabulary) != expected_vocabulary:
        errors.append("vocabulary fields must be exactly " + ", ".join(sorted(expected_vocabulary)))
    vocab: dict[str, list[str]] = {}
    for field in sorted(expected_vocabulary):
        values, value_errors = _string_list(vocabulary.get(field), f"vocabulary.{field}")
        vocab[field] = values
        errors.extend(value_errors)
    if phases and vocab.get("phases") != phases:
        errors.append("vocabulary.phases must equal selection_contract.phase_order")
    for index, rule in enumerate(negative_rules):
        if not isinstance(rule, dict):
            continue
        for field in ("signals", "unless_signals"):
            values = rule.get(field, [])
            if isinstance(values, list):
                unknown = sorted(set(values) - set(vocab.get("signals", [])))
                if unknown:
                    errors.append(
                        f"selection_contract.global_negative_rules[{index}].{field} contains unknown signals {unknown}"
                    )

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        errors.append("sources must be a non-empty list")
        raw_sources = []
    source_ids: set[str] = set()
    for index, source in enumerate(raw_sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(source) != SOURCE_FIELDS:
            errors.append(f"{label} fields must be exactly {', '.join(sorted(SOURCE_FIELDS))}")
        for field in SOURCE_FIELDS:
            _nonempty_string(source, field, label, errors)
        source_id = source.get("id")
        if isinstance(source_id, str):
            if SOURCE_ID_RE.fullmatch(source_id) is None:
                errors.append(f"{label}.id must match SRC-[A-Z0-9-]+")
            if source_id in source_ids:
                errors.append(f"duplicate source id {source_id}")
            source_ids.add(source_id)
        url = source.get("url")
        if isinstance(url, str) and not url.startswith("https://"):
            errors.append(f"{label}.url must use HTTPS")

    raw_methods = payload.get("methods")
    if not isinstance(raw_methods, list) or not raw_methods:
        errors.append("methods must be a non-empty list")
        raw_methods = []
    methods: dict[str, dict[str, Any]] = {}
    phase_counts = {phase: 0 for phase in phases}
    foundation_counts = {phase: 0 for phase in phases}
    referenced_source_ids: set[str] = set()
    for index, method in enumerate(raw_methods):
        label = f"methods[{index}]"
        if not isinstance(method, dict):
            errors.append(f"{label} must be an object")
            continue
        method_id = method.get("id")
        if isinstance(method_id, str):
            label = f"method {method_id}"
        if set(method) != METHOD_FIELDS:
            errors.append(f"{label} fields must be exactly {', '.join(sorted(METHOD_FIELDS))}")
        for field in (
            "id",
            "name",
            "family",
            "summary",
            "owner",
            "depth",
            "selection",
            "cost",
            "positive_trigger",
            "negative_trigger",
            "evidence",
            "fallback",
            "limitations",
            "guidance_ref",
        ):
            _nonempty_string(method, field, label, errors)
        if isinstance(method_id, str):
            if ID_RE.fullmatch(method_id) is None:
                errors.append(f"{label}.id must be a stable lowercase kebab-case id")
            if method_id in methods:
                errors.append(f"duplicate method id {method_id}")
            methods[method_id] = method
        if method.get("owner") not in vocab.get("owners", []):
            errors.append(f"{label}.owner is not registered in vocabulary.owners")
        if method.get("depth") not in depths:
            errors.append(f"{label}.depth is not registered")
        if method.get("selection") not in SELECTION_KINDS:
            errors.append(f"{label}.selection is not registered")
        if method.get("selection") == "specialist" and method.get("depth") != "formal":
            errors.append(f"{label}: specialist methods must use formal depth")
        if method.get("cost") not in COSTS:
            errors.append(f"{label}.cost must be one of {sorted(COSTS)}")
        list_fields = {
            "phases": False,
            "risks": True,
            "signals": True,
            "negative_signals": True,
            "prerequisites": True,
            "outputs": False,
            "steps": False,
            "source_ids": False,
        }
        lists: dict[str, list[str]] = {}
        for field, allow_empty in list_fields.items():
            values, value_errors = _string_list(
                method.get(field), f"{label}.{field}", allow_empty=allow_empty
            )
            lists[field] = values
            errors.extend(value_errors)
        for phase in lists.get("phases", []):
            if phase not in phases:
                errors.append(f"{label}.phases contains unknown phase {phase!r}")
            else:
                phase_counts[phase] += 1
                if method.get("selection") == "foundation":
                    foundation_counts[phase] += 1
        for field, vocabulary_field in (
            ("risks", "risks"),
            ("signals", "signals"),
            ("negative_signals", "signals"),
            ("prerequisites", "prerequisites"),
        ):
            allowed = set(vocab.get(vocabulary_field, []))
            # A method may describe consequence affinity in `risks`, while the
            # selector still requires it as a stronger observed signal. This
            # keeps high-consequence from becoming a generic routing risk.
            if field == "risks":
                allowed.update(vocab.get("signals", []))
            unknown = sorted(set(lists.get(field, [])) - allowed)
            if unknown:
                errors.append(f"{label}.{field} contains unknown values {unknown}")
        overlap = set(lists.get("signals", [])) & set(lists.get("negative_signals", []))
        if overlap:
            errors.append(f"{label} has positive/negative signal overlap {sorted(overlap)}")
        for source_id in lists.get("source_ids", []):
            referenced_source_ids.add(source_id)
            if source_id not in source_ids:
                errors.append(f"{label}.source_ids references unknown source {source_id}")
        if len(lists.get("steps", [])) < 3:
            errors.append(f"{label}.steps must contain at least three bounded steps")
        guidance_ref = method.get("guidance_ref")
        if isinstance(guidance_ref, str):
            if guidance_ref.startswith("/") or ".." in Path(guidance_ref).parts:
                errors.append(f"{label}.guidance_ref must be a safe repository-relative path")
            elif repository_root is not None and not (repository_root / guidance_ref).is_file():
                errors.append(f"{label}.guidance_ref does not exist: {guidance_ref}")
    for phase in phases:
        if phase_counts.get(phase, 0) == 0:
            errors.append(f"method pool has no coverage for phase {phase}")
        if foundation_counts.get(phase, 0) == 0:
            errors.append(f"method pool has no foundation method for phase {phase}")
    unused_sources = sorted(source_ids - referenced_source_ids)
    if unused_sources:
        errors.append(f"source registry contains unreferenced sources {unused_sources}")

    raw_models = payload.get("risk_models")
    if not isinstance(raw_models, list) or not raw_models:
        errors.append("risk_models must be a non-empty list")
        raw_models = []
    model_ids: set[str] = set()
    methods_in_models: set[str] = set()
    for index, model in enumerate(raw_models):
        label = f"risk_models[{index}]"
        if not isinstance(model, dict):
            errors.append(f"{label} must be an object")
            continue
        model_id = model.get("id")
        if isinstance(model_id, str):
            label = f"risk model {model_id}"
        if set(model) != RISK_MODEL_FIELDS:
            errors.append(f"{label} fields must be exactly {', '.join(sorted(RISK_MODEL_FIELDS))}")
        for field in ("id", "name", "failure_hypothesis", "escalation"):
            _nonempty_string(model, field, label, errors)
        if isinstance(model_id, str):
            if RISK_MODEL_ID_RE.fullmatch(model_id) is None:
                errors.append(f"{label}.id must match RM-[A-Z0-9-]+")
            if model_id in model_ids:
                errors.append(f"duplicate risk model id {model_id}")
            model_ids.add(model_id)
        minimum_score = model.get("minimum_score")
        if not isinstance(minimum_score, int) or isinstance(minimum_score, bool) or minimum_score < 1:
            errors.append(f"{label}.minimum_score must be a positive integer")
        match = model.get("match")
        if not isinstance(match, dict):
            errors.append(f"{label}.match must be an object")
            match = {}
        if set(match) != MATCH_FIELDS:
            errors.append(f"{label}.match fields must be exactly {', '.join(sorted(MATCH_FIELDS))}")
        selectors = 0
        for field, vocabulary_field in (
            ("risks", "risks"),
            ("signals", "signals"),
            ("task_types", "task_types"),
        ):
            values, value_errors = _string_list(
                match.get(field), f"{label}.match.{field}", allow_empty=True
            )
            errors.extend(value_errors)
            selectors += len(values)
            unknown = sorted(set(values) - set(vocab.get(vocabulary_field, [])))
            if unknown:
                errors.append(f"{label}.match.{field} contains unknown values {unknown}")
        if selectors == 0:
            errors.append(f"{label}.match must contain at least one selector")
        method_ids, method_errors = _string_list(model.get("method_ids"), f"{label}.method_ids")
        errors.extend(method_errors)
        for method_id in method_ids:
            methods_in_models.add(method_id)
            method = methods.get(method_id)
            if method is None:
                errors.append(f"{label}.method_ids references unknown method {method_id}")
        obligations, obligation_errors = _string_list(
            model.get("evidence_obligations"), f"{label}.evidence_obligations"
        )
        errors.extend(obligation_errors)
        if len(obligations) < 2:
            errors.append(f"{label}.evidence_obligations must contain at least two obligations")
    unintegrated = sorted(
        method_id
        for method_id, method in methods.items()
        if method.get("selection") != "foundation" and method_id not in methods_in_models
    )
    if unintegrated:
        errors.append(f"non-foundation methods are not integrated into a risk model: {unintegrated}")
    for index, rule in enumerate(negative_rules):
        if not isinstance(rule, dict):
            continue
        unknown_methods = sorted(set(rule.get("method_ids", [])) - set(methods))
        if unknown_methods:
            errors.append(
                f"selection_contract.global_negative_rules[{index}].method_ids contains unknown methods {unknown_methods}"
            )
    return sorted(set(errors))


def _method_projection(method: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": method["id"],
        "name": method["name"],
        "summary": method["summary"],
        "family": method["family"],
        "owner": method["owner"],
        "depth": method["depth"],
        "cost": method["cost"],
        "why": method["positive_trigger"],
        "outputs": method["outputs"],
        "steps": method["steps"],
        "evidence": method["evidence"],
        "limitations": method["limitations"],
        "fallback": method["fallback"],
        "guidance_ref": method["guidance_ref"],
        "source_ids": method["source_ids"],
    }


def select_methods(
    payload: dict[str, Any],
    *,
    repository_root: Path | None = None,
    phase: str,
    task_type: str,
    risks: list[str],
    signals: list[str],
    available: list[str],
    depth: str,
    max_methods: int | None = None,
) -> dict[str, Any]:
    """Select a bounded method stack and preserve its causal reasoning trace."""
    errors = validate_registry(payload, repository_root=repository_root)
    if errors:
        raise MethodologyContractError("invalid methodology registry: " + "; ".join(errors))
    contract = payload["selection_contract"]
    vocabulary = payload["vocabulary"]
    request_errors: list[str] = []
    if phase not in vocabulary["phases"]:
        request_errors.append(f"unknown phase {phase!r}")
    if task_type not in vocabulary["task_types"]:
        request_errors.append(f"unknown task type {task_type!r}")
    if depth not in contract["depths"]:
        request_errors.append(f"unknown depth {depth!r}")
    for label, values, vocabulary_field in (
        ("risk", risks, "risks"),
        ("signal", signals, "signals"),
        ("available prerequisite", available, "prerequisites"),
    ):
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            request_errors.append(f"duplicate {label} values {duplicates}")
        unknown = sorted(set(values) - set(vocabulary[vocabulary_field]))
        if unknown:
            request_errors.append(f"unknown {label} values {unknown}")
    if max_methods is not None and (isinstance(max_methods, bool) or max_methods < 1):
        request_errors.append("max_methods must be a positive integer")
    if request_errors:
        raise MethodologyContractError("; ".join(sorted(request_errors)))

    risks_set = set(risks)
    signals_set = set(signals)
    available_set = set(available)
    depth_index = {value: index for index, value in enumerate(contract["depths"])}
    method_index = {method["id"]: index for index, method in enumerate(payload["methods"])}
    methods = {method["id"]: method for method in payload["methods"]}
    limit = max_methods or contract["default_max_methods"][depth]
    selected_ids: list[str] = []
    blocked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    candidate_status: dict[str, str] = {}

    def consider(method_id: str, *, stack_id: str, reason: str) -> dict[str, Any]:
        method = methods[method_id]
        if phase not in method["phases"]:
            return {"method_id": method_id, "status": "other-phase", "reason": f"not applicable during {phase}"}
        if depth_index[method["depth"]] > depth_index[depth]:
            entry = {
                "method_id": method_id,
                "status": "depth-excluded",
                "reason": f"requires {method['depth']} depth; request is {depth}",
                "stack_id": stack_id,
            }
            if candidate_status.get(method_id) is None:
                excluded.append(entry)
                candidate_status[method_id] = entry["status"]
            return entry
        negative = sorted(signals_set & set(method["negative_signals"]))
        global_negative = []
        for rule in contract["global_negative_rules"]:
            if not signals_set.intersection(rule["signals"]):
                continue
            if signals_set.intersection(rule["unless_signals"]):
                continue
            if rule["depths"] and method["depth"] not in rule["depths"]:
                continue
            if rule["method_ids"] and method_id not in rule["method_ids"]:
                continue
            global_negative.append(rule)
        if negative or global_negative:
            matched_rule_ids = [rule["id"] for rule in global_negative]
            reasons = [method["negative_trigger"]] if negative else []
            reasons.extend(rule["reason"] for rule in global_negative)
            entry = {
                "method_id": method_id,
                "status": "negative-triggered",
                "reason": " ".join(reasons),
                "matched_negative_signals": negative,
                "matched_global_rules": matched_rule_ids,
                "stack_id": stack_id,
            }
            if candidate_status.get(method_id) is None:
                excluded.append(entry)
                candidate_status[method_id] = entry["status"]
            return entry
        missing = sorted(set(method["prerequisites"]) - available_set)
        if missing:
            entry = {
                "method_id": method_id,
                "name": method["name"],
                "status": "prerequisite-missing",
                "missing_prerequisites": missing,
                "fallback": method["fallback"],
                "owner": method["owner"],
                "stack_id": stack_id,
            }
            if candidate_status.get(method_id) is None:
                blocked.append(entry)
                candidate_status[method_id] = entry["status"]
            return entry
        if method_id in selected_ids:
            return {"method_id": method_id, "status": "selected-shared", "reason": reason}
        if len(selected_ids) >= limit:
            entry = {
                "method_id": method_id,
                "status": "context-cap-excluded",
                "reason": f"selection cap {limit} reached; rerun at greater depth/cap only if risk justifies it",
                "stack_id": stack_id,
            }
            if candidate_status.get(method_id) is None:
                excluded.append(entry)
                candidate_status[method_id] = entry["status"]
            return entry
        selected_ids.append(method_id)
        candidate_status[method_id] = "selected"
        return {"method_id": method_id, "status": "selected", "reason": reason}

    foundations = sorted(
        (
            method
            for method in payload["methods"]
            if method["selection"] == "foundation" and phase in method["phases"]
        ),
        key=lambda method: method_index[method["id"]],
    )
    foundation_entries = [
        consider(
            method["id"],
            stack_id=f"FOUNDATION-{phase.upper()}",
            reason=f"foundation for {phase}",
        )
        for method in foundations
    ]

    stacks: list[dict[str, Any]] = []
    matched_models: list[dict[str, Any]] = []
    for model in payload["risk_models"]:
        matches = {
            "risks": sorted(risks_set & set(model["match"]["risks"])),
            "signals": sorted(signals_set & set(model["match"]["signals"])),
            "task_types": [task_type] if task_type in model["match"]["task_types"] else [],
        }
        score = sum(len(matches[field]) * MATCH_WEIGHTS[field] for field in MATCH_FIELDS)
        if score < model["minimum_score"]:
            continue
        method_entries = [
            consider(
                method_id,
                stack_id=model["id"],
                reason=f"addresses {model['failure_hypothesis']}",
            )
            for method_id in model["method_ids"]
        ]
        if not any(entry["status"] != "other-phase" for entry in method_entries):
            continue
        matched_models.append(
            {
                "id": model["id"],
                "name": model["name"],
                "score": score,
                "minimum_score": model["minimum_score"],
                "matched": matches,
            }
        )
        stacks.append(
            {
                "id": model["id"],
                "name": model["name"],
                "observations": matches,
                "failure_hypothesis": model["failure_hypothesis"],
                "methods": method_entries,
                "evidence_obligations": model["evidence_obligations"],
                "escalation": model["escalation"],
            }
        )

    selected = [_method_projection(methods[method_id]) for method_id in selected_ids]
    selected.sort(key=lambda method: method_index[method["id"]])
    blocked.sort(key=lambda entry: (method_index[entry["method_id"]], entry["stack_id"]))
    excluded.sort(key=lambda entry: (method_index[entry["method_id"]], entry["stack_id"]))
    unresolved = []
    if blocked:
        unresolved.append(
            "One or more methods lack prerequisites; apply the recorded fallback or obtain the prerequisite before claiming their assurance."
        )
    if not matched_models and (risks or signals):
        unresolved.append(
            "No risk model met its evidence threshold; verify signal classification instead of assuming the risks are covered."
        )
    if any(entry["status"] == "context-cap-excluded" for entry in excluded):
        unresolved.append(
            "The context cap excluded otherwise applicable methods; raise it only for a named residual failure class."
        )
    if not risks and not signals:
        unresolved.append(
            "Only the phase foundation was considered because no observed risk or signal was supplied."
        )
    return {
        "schema_version": OUTPUT_SCHEMA,
        "status": "selected" if not blocked else "selected-with-unresolved-prerequisites",
        "request": {
            "phase": phase,
            "task_type": task_type,
            "depth": depth,
            "risks": sorted(risks),
            "signals": sorted(signals),
            "available_prerequisites": sorted(available),
        },
        "reasoning_model": {
            "chain": "observed facts -> failure hypothesis -> proportionate method -> owned artifact -> failure-sensitive evidence",
            "match_weights": MATCH_WEIGHTS,
            "matched_risk_models": matched_models,
        },
        "foundation": foundation_entries,
        "stacks": stacks,
        "selected_methods": selected,
        "blocked_methods": blocked,
        "excluded_methods": excluded,
        "unresolved": unresolved,
        "context_budget": {
            "limit": limit,
            "selected": len(selected),
            "remaining": limit - len(selected),
            "pool_size": len(payload["methods"]),
            "full_pool_loaded_into_working_set": False,
        },
        "reselection_triggers": contract["reselection_triggers"],
        "assurance_boundary": "Method selection is guidance, not proof or authority. Existing owner Skills decide semantics and design; only executed failure-sensitive evidence closes a claim.",
    }
