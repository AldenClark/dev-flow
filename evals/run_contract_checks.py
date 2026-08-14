#!/usr/bin/env python3
"""Validate deterministic eval and governance contracts without external packages."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = ROOT / "evals"
sys.path.insert(0, str(EVALS_ROOT))
sys.path.insert(0, str(ROOT / "skills" / "dev-flow" / "scripts"))

from run_paired_evaluations import EvaluationError, validate_config  # noqa: E402
import methodology_system  # noqa: E402


CONTRACT_TEXT_FIELDS = ("id", "profile", "prompt", "fixture")
CONTRACT_LIST_FIELDS = ("forbidden_actions", "required_artifacts")
OBLIGATION_FIELDS = {"id", "owner", "kind", "criticality", "action", "evidence_kind"}
WORK_UNIT_FIELDS = {
    "id",
    "owner",
    "claim_routes",
    "criticality",
    "protected_behavior",
    "facets",
}
CLAIM_ROUTE_FIELDS = {"kind"}
FACET_FIELDS = {"id", "action"}
KIND_ID_RE = re.compile(r"^[a-z][a-z0-9.-]{0,127}$")
WORK_UNIT_ID_RE = re.compile(r"^WU-[1-9][0-9]*$")
FACET_ID_RE = re.compile(r"^OB-[1-9][0-9]*$")
OBLIGATION_CRITICALITIES = {"critical", "required", "supporting"}
OBLIGATION_EVIDENCE_KINDS = {
    "analysis",
    "decision",
    "test",
    "artifact",
    "interaction",
    "limitation",
}
CLAIM_KIND_FAMILIES = tuple(sorted(OBLIGATION_EVIDENCE_KINDS))
PACKET_ARTIFACTS = {
    "packet.json",
    "events.jsonl",
    "trace.md",
    "context.md",
    "requirements.md",
    "design.md",
    "execution.md",
    "test-matrix.md",
    "blue-audit.md",
    "red-audit.md",
    "evidence.md",
    "decisions.md",
}
REGISTERED_SKILLS = frozenset(
    item.get("skill")
    for item in json.loads(
        (ROOT / "governance" / "capability-contracts.json").read_text(encoding="utf-8")
    ).get("capabilities", [])
    if isinstance(item, dict) and isinstance(item.get("skill"), str) and item["skill"]
)
DESCRIPTION_BUDGET = 2500
ORDINARY_STATIC_BUDGET = 18000
ORDINARY_STATIC_FILES = (
    "skills/dev-flow/SKILL.md",
    "skills/dev-flow/references/artifact-schemas.md",
    "skills/repo-context/SKILL.md",
    "skills/verification/SKILL.md",
)
DEVELOPMENT_FFI_SHAPES = {
    "ffi-mobile.json": (8, 57),
    "ffi-ownership-error.json": (13, 53),
    "ffi-lifecycle-packaging.json": (8, 44),
}
ACCEPTANCE_FFI_SHAPES = {
    "CASE-ACC-FFI-ENUM": (8, 38),
    "CASE-ACC-FFI-REENTRANT": (7, 42),
    "CASE-ACC-FFI-STRING": (9, 43),
}


def work_unit_shape(value: object) -> tuple[int, int]:
    if not isinstance(value, list):
        return (0, 0)
    return (
        len(value),
        sum(
            len(item.get("facets", []))
            for item in value
            if isinstance(item, dict) and isinstance(item.get("facets"), list)
        ),
    )


def capability_alignment_errors(
    obligations: object,
    capabilities: object,
    registered_skills: set[str] | frozenset[str] = REGISTERED_SKILLS,
    registered_kinds: dict[str, str] | None = None,
) -> list[str]:
    """Validate owner-bound obligations or work units against pair assembly."""
    if not isinstance(obligations, list) or not isinstance(capabilities, list):
        return ["capability alignment inputs must be lists"]
    supplied = {item for item in capabilities if isinstance(item, str)}
    errors: list[str] = []
    for index, obligation in enumerate(obligations, 1):
        if not isinstance(obligation, dict):
            errors.append(f"contract item {index} must be an owner-bound object")
            continue
        owner = obligation.get("owner")
        obligation_id = obligation.get("id", f"index {index}")
        if not isinstance(owner, str) or not owner:
            errors.append(f"obligation {obligation_id} has no owner")
        elif owner not in registered_skills:
            errors.append(f"obligation {obligation_id} has unregistered owner {owner}")
        elif owner not in supplied:
            errors.append(f"obligation {obligation_id} requires unsupplied capability {owner}")
        routes = obligation.get("claim_routes")
        kinds = (
            [route.get("kind") for route in routes if isinstance(route, dict)]
            if isinstance(routes, list)
            else [obligation.get("kind")]
        )
        if registered_kinds is not None:
            for kind in kinds:
                if not isinstance(kind, str) or kind not in registered_kinds:
                    errors.append(f"obligation {obligation_id} has unregistered kind {kind!r}")
                elif registered_kinds[kind] != owner:
                    errors.append(
                        f"obligation {obligation_id} kind {kind} belongs to "
                        f"{registered_kinds[kind]}, not {owner}"
                    )
    return errors


def validate_contract(
    path: Path,
    data: object,
    *,
    root: Path = ROOT,
    registered_skills: set[str] | frozenset[str] = REGISTERED_SKILLS,
    registered_kinds: dict[str, str] | None = None,
    schema_version: str | None = "2.2",
    fixture_is_path: bool = True,
) -> list[str]:
    if not isinstance(data, dict):
        return [f"{path.name}: contract must be an object"]
    errors: list[str] = []
    work_unit_protocol = schema_version == "2.2" or (
        schema_version is None and "work_units" in data
    )
    contract_items_field = "work_units" if work_unit_protocol else "obligations"
    expected_fields = set(CONTRACT_TEXT_FIELDS) | set(CONTRACT_LIST_FIELDS) | {
        contract_items_field
    }
    if schema_version is not None:
        expected_fields.add("schema_version")
        if data.get("schema_version") != schema_version:
            errors.append(f"{path.name}: schema_version must be {schema_version}")
    if set(data) != expected_fields:
        errors.append(
            f"{path.name}: fields must be exactly {sorted(expected_fields)}, observed {sorted(data)}"
        )
    for field in CONTRACT_TEXT_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{path.name}: {field} must be a non-empty string")
    obligations = data.get(contract_items_field)
    if not isinstance(obligations, list) or not obligations:
        errors.append(f"{path.name}: {contract_items_field} must be a non-empty list")
    elif work_unit_protocol:
        if len(obligations) > 64:
            errors.append(f"{path.name}: work_units must contain at most 64 items")
        work_unit_ids: list[str] = []
        facet_ids: list[str] = []
        facet_actions: list[str] = []
        for index, work_unit in enumerate(obligations, 1):
            expected_id = f"WU-{index}"
            if not isinstance(work_unit, dict):
                errors.append(f"{path.name}: work unit {index} must be an object")
                continue
            if set(work_unit) != WORK_UNIT_FIELDS:
                errors.append(
                    f"{path.name}: work unit {index} fields must be exactly "
                    f"{sorted(WORK_UNIT_FIELDS)}"
                )
            work_unit_id = work_unit.get("id")
            if work_unit_id != expected_id or not isinstance(work_unit_id, str):
                errors.append(
                    f"{path.name}: work unit {index} id must be {expected_id}, "
                    f"observed {work_unit_id!r}"
                )
            elif WORK_UNIT_ID_RE.fullmatch(work_unit_id) is None:
                errors.append(f"{path.name}: work unit {index} id is invalid")
            else:
                work_unit_ids.append(work_unit_id)
            owner = work_unit.get("owner")
            if not isinstance(owner, str) or not owner:
                errors.append(f"{path.name}: work unit {expected_id} owner must be non-empty")
            elif owner not in registered_skills:
                errors.append(
                    f"{path.name}: work unit {expected_id} owner {owner} is not registered"
                )
            routes = work_unit.get("claim_routes")
            route_kinds: list[str] = []
            if not isinstance(routes, list) or not routes:
                errors.append(
                    f"{path.name}: work unit {expected_id} claim_routes must be non-empty"
                )
            elif len(routes) > 6:
                errors.append(
                    f"{path.name}: work unit {expected_id} claim_routes exceeds six items"
                )
            else:
                for route_index, route in enumerate(routes, 1):
                    if not isinstance(route, dict) or set(route) != CLAIM_ROUTE_FIELDS:
                        errors.append(
                            f"{path.name}: work unit {expected_id} claim route {route_index} "
                            "must contain only kind"
                        )
                        continue
                    kind = route.get("kind")
                    if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
                        errors.append(
                            f"{path.name}: work unit {expected_id} claim route "
                            f"{route_index} kind is invalid"
                        )
                        continue
                    route_kinds.append(kind)
                    if registered_kinds is not None:
                        if kind not in registered_kinds:
                            errors.append(
                                f"{path.name}: work unit {expected_id} kind {kind} "
                                "is not registered"
                            )
                        elif registered_kinds[kind] != owner:
                            errors.append(
                                f"{path.name}: work unit {expected_id} kind {kind} belongs to "
                                f"{registered_kinds[kind]}, not {owner}"
                            )
                if len(route_kinds) != len(set(route_kinds)):
                    errors.append(
                        f"{path.name}: work unit {expected_id} claim route kinds must be unique"
                    )
            criticality = work_unit.get("criticality")
            if criticality not in OBLIGATION_CRITICALITIES:
                errors.append(
                    f"{path.name}: work unit {expected_id} criticality must be critical, required, or supporting"
                )
            protected_behavior = work_unit.get("protected_behavior")
            if not isinstance(protected_behavior, str) or not protected_behavior.strip():
                errors.append(
                    f"{path.name}: work unit {expected_id} protected_behavior must be non-empty"
                )
            elif len(protected_behavior) > 1000:
                errors.append(
                    f"{path.name}: work unit {expected_id} protected_behavior exceeds 1000 characters"
                )
            facets = work_unit.get("facets")
            if not isinstance(facets, list) or not facets:
                errors.append(f"{path.name}: work unit {expected_id} facets must be non-empty")
                continue
            if len(facets) > 64:
                errors.append(f"{path.name}: work unit {expected_id} facets exceeds 64 items")
            for facet_index, facet in enumerate(facets, 1):
                if not isinstance(facet, dict) or set(facet) != FACET_FIELDS:
                    errors.append(
                        f"{path.name}: work unit {expected_id} facet {facet_index} "
                        f"fields must be exactly {sorted(FACET_FIELDS)}"
                    )
                    continue
                facet_id = facet.get("id")
                if not isinstance(facet_id, str) or FACET_ID_RE.fullmatch(facet_id) is None:
                    errors.append(
                        f"{path.name}: work unit {expected_id} facet {facet_index} id is invalid"
                    )
                else:
                    facet_ids.append(facet_id)
                action = facet.get("action")
                if not isinstance(action, str) or not action.strip():
                    errors.append(
                        f"{path.name}: work unit {expected_id} facet {facet_index} "
                        "action must be non-empty"
                    )
                else:
                    facet_actions.append(action)
                    if len(action) > 1000:
                        errors.append(
                            f"{path.name}: work unit {expected_id} facet {facet_index} "
                            "action exceeds 1000 characters"
                        )
        if len(work_unit_ids) != len(set(work_unit_ids)):
            errors.append(f"{path.name}: work unit IDs must be unique")
        if len(facet_ids) != len(set(facet_ids)):
            errors.append(f"{path.name}: facet IDs must be unique across work units")
        expected_facet_ids = {f"OB-{index}" for index in range(1, len(facet_ids) + 1)}
        if set(facet_ids) != expected_facet_ids:
            errors.append(
                f"{path.name}: facets must retain a complete contiguous OB-1..OB-n identity set"
            )
        if len(facet_actions) != len(set(facet_actions)):
            errors.append(f"{path.name}: facet actions must be unique")
        if not any(
            isinstance(work_unit, dict)
            and work_unit.get("criticality") in {"critical", "required"}
            for work_unit in obligations
        ):
            errors.append(f"{path.name}: at least one work unit must be critical or required")
    else:
        if len(obligations) > 64:
            errors.append(f"{path.name}: obligations must contain at most 64 items")
        obligation_ids: list[str] = []
        obligation_actions: list[str] = []
        for index, obligation in enumerate(obligations, 1):
            if not isinstance(obligation, dict):
                errors.append(f"{path.name}: obligation {index} must be an object")
                continue
            if set(obligation) != OBLIGATION_FIELDS:
                errors.append(
                    f"{path.name}: obligation {index} fields must be exactly {sorted(OBLIGATION_FIELDS)}"
                )
            obligation_id = obligation.get("id")
            expected_id = f"OB-{index}"
            if obligation_id != expected_id:
                errors.append(
                    f"{path.name}: obligation {index} id must be {expected_id}, observed {obligation_id!r}"
                )
            if isinstance(obligation_id, str):
                obligation_ids.append(obligation_id)
            owner = obligation.get("owner")
            if not isinstance(owner, str) or not owner:
                errors.append(f"{path.name}: obligation {expected_id} owner must be non-empty")
            elif owner not in registered_skills:
                errors.append(f"{path.name}: obligation {expected_id} owner {owner} is not registered")
            kind = obligation.get("kind")
            if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
                errors.append(f"{path.name}: obligation {expected_id} kind is invalid")
            elif registered_kinds is not None:
                if kind not in registered_kinds:
                    errors.append(f"{path.name}: obligation {expected_id} kind {kind} is not registered")
                elif registered_kinds[kind] != owner:
                    errors.append(
                        f"{path.name}: obligation {expected_id} kind {kind} belongs to "
                        f"{registered_kinds[kind]}, not {owner}"
                    )
            criticality = obligation.get("criticality")
            if criticality not in OBLIGATION_CRITICALITIES:
                errors.append(
                    f"{path.name}: obligation {expected_id} criticality must be critical, required, or supporting"
                )
            action = obligation.get("action")
            if not isinstance(action, str) or not action.strip():
                errors.append(f"{path.name}: obligation {expected_id} action must be non-empty")
            else:
                obligation_actions.append(action)
                if len(action) > 1000:
                    errors.append(
                        f"{path.name}: obligation {expected_id} action exceeds 1000 characters"
                    )
            evidence_kind = obligation.get("evidence_kind")
            if evidence_kind not in OBLIGATION_EVIDENCE_KINDS:
                errors.append(
                    f"{path.name}: obligation {expected_id} has invalid evidence_kind {evidence_kind!r}"
                )
            elif isinstance(owner, str) and kind != f"{owner}.{evidence_kind}":
                errors.append(
                    f"{path.name}: obligation {expected_id} kind must be the task-neutral "
                    f"owner/evidence family {owner}.{evidence_kind}"
                )
        if len(obligation_ids) != len(set(obligation_ids)):
            errors.append(f"{path.name}: obligation IDs must be unique")
        if len(obligation_actions) != len(set(obligation_actions)):
            errors.append(f"{path.name}: obligation actions must be unique")
        if not any(
            isinstance(obligation, dict)
            and obligation.get("criticality") in {"critical", "required"}
            for obligation in obligations
        ):
            errors.append(f"{path.name}: at least one obligation must be critical or required")
    for field in CONTRACT_LIST_FIELDS:
        value = data.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"{path.name}: {field} must be a non-empty list")
            continue
        if len(value) > 24:
            errors.append(f"{path.name}: {field} must contain at most 24 items")
        if any(not isinstance(item, str) or not item.strip() for item in value):
            errors.append(f"{path.name}: {field} items must be non-empty strings")
        string_items = [item for item in value if isinstance(item, str)]
        if len(string_items) != len(set(string_items)):
            errors.append(f"{path.name}: {field} items must be unique")
    artifacts = data.get("required_artifacts", [])
    if isinstance(artifacts, list):
        unknown = sorted({item for item in artifacts if isinstance(item, str)} - PACKET_ARTIFACTS)
        if unknown:
            errors.append(f"{path.name}: unknown required artifacts {unknown}")
    fixture = data.get("fixture")
    if (
        fixture_is_path
        and isinstance(fixture, str)
        and fixture.strip()
        and not (root / "evals" / fixture).is_file()
    ):
        errors.append(f"{path.name}: missing fixture {root / 'evals' / fixture}")
    return errors


def evaluate_user_interaction_case(case: dict[str, object]) -> str:
    kind = case.get("kind")
    if kind == "response":
        if case.get("question_id") != case.get("expected_question_id"):
            return "ignored-stale-or-unknown"
        if case.get("requirement_revision") != case.get("current_requirement_revision"):
            return "ignored-stale-or-unknown"
        answers = case.get("answers")
        if not isinstance(answers, list) or len(answers) != 1:
            return "unresolved-invalid"
        answer = answers[0]
        if not isinstance(answer, str) or not answer.strip():
            return "unresolved-invalid"
        options = case.get("options")
        if not isinstance(options, list) or any(not isinstance(option, str) for option in options):
            return "unresolved-invalid"
        if answer in options:
            return "accepted-option"
        if case.get("other_enabled") is True:
            return "accepted-other"
        return "unresolved-invalid"
    if kind == "lifecycle":
        event = case.get("event")
        if event in {"user-cancelled", "client-interrupted", "request-cleared"}:
            return "unresolved-no-reprompt"
        if event in {"tool-unavailable", "invocation-failed-before-presentation"}:
            attempts = case.get("fallback_attempts")
            if isinstance(attempts, int) and attempts < 1 and case.get("host_allows_plain_text") is True:
                return "fallback-nonenumerated"
            return "unresolved-blocked"
    return "invalid-case"


def main() -> int:
    errors: list[str] = []
    description_total = 0
    for skill_name in REGISTERED_SKILLS:
        text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        description = next(
            (line.split(":", 1)[1].strip() for line in text.splitlines() if line.startswith("description:")),
            "",
        )
        description_total += len(description)
    if description_total > DESCRIPTION_BUDGET:
        errors.append(f"Skill descriptions exceed {DESCRIPTION_BUDGET} characters: {description_total}")
    ordinary_static_total = sum(
        len((ROOT / path).read_text(encoding="utf-8").encode("utf-8"))
        for path in ORDINARY_STATIC_FILES
    )
    if ordinary_static_total > ORDINARY_STATIC_BUDGET:
        errors.append(f"ordinary static path exceeds {ORDINARY_STATIC_BUDGET} bytes: {ordinary_static_total}")
    capability_contracts = json.loads(
        (ROOT / "governance" / "capability-contracts.json").read_text(encoding="utf-8")
    )
    if set(capability_contracts) != {"schema_version", "capabilities"} or capability_contracts.get("schema_version") != "1.0":
        errors.append("capability contract must use exact schema 1.0")
    capabilities = capability_contracts.get("capabilities", [])
    registered_skills = {
        item.get("skill")
        for item in capabilities
        if isinstance(item, dict) and isinstance(item.get("skill"), str)
    }
    claim_kinds = json.loads(
        (ROOT / "governance" / "claim-kinds.json").read_text(encoding="utf-8")
    )
    registered_kinds: dict[str, str] = {}
    if set(claim_kinds) != {"schema_version", "kinds"} or claim_kinds.get("schema_version") != "1.0":
        errors.append("claim kind registry must use exact schema 1.0")
    kinds = claim_kinds.get("kinds")
    if not isinstance(kinds, list) or not kinds:
        errors.append("claim kind registry must define a non-empty kinds list")
        kinds = []
    for index, item in enumerate(kinds, 1):
        if not isinstance(item, dict) or set(item) != {"id", "owner"}:
            errors.append(f"claim kind {index} must contain only id and owner")
            continue
        kind_id = item.get("id")
        owner = item.get("owner")
        if not isinstance(kind_id, str) or KIND_ID_RE.fullmatch(kind_id) is None:
            errors.append(f"claim kind {index} has invalid id {kind_id!r}")
            continue
        if kind_id in registered_kinds:
            errors.append(f"duplicate claim kind id {kind_id}")
        if owner not in registered_skills:
            errors.append(f"claim kind {kind_id} has unregistered owner {owner!r}")
        registered_kinds[kind_id] = str(owner)
    expected_kinds = {
        f"{owner}.{family}": owner
        for owner in registered_skills
        for family in CLAIM_KIND_FAMILIES
    }
    if registered_kinds != expected_kinds:
        errors.append(
            "claim kind registry must be the complete task-neutral owner/evidence-kind matrix"
        )
    contracts = sorted((ROOT / "evals" / "contracts").glob("*.json"))
    required_contract_ids = {
        "CASE-FRONTEND-NEW-PRODUCT",
        "CASE-FRONTEND-PRESERVE-IA",
        "CASE-REPOSITORY-INSTRUCTIONS",
        "CASE-SEMANTIC-LATE-REOPENING",
        "CASE-REQUIREMENTS-DESIGN-CONTRADICTION",
        "CASE-REQUIREMENTS-MISSING-STATES",
        "CASE-REQUIREMENTS-AVOIDABLE-QUESTION",
        "CASE-STRUCTURED-USER-INPUT",
    }
    observed_contract_ids: set[str] = set()
    for path in contracts:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(
            validate_contract(
                path,
                data,
                registered_skills=registered_skills,
                registered_kinds=registered_kinds,
            )
        )
        expected_ffi_shape = DEVELOPMENT_FFI_SHAPES.get(path.name)
        if expected_ffi_shape is not None:
            observed_ffi_shape = work_unit_shape(data.get("work_units"))
            if observed_ffi_shape != expected_ffi_shape:
                errors.append(
                    f"{path.name}: expected FFI work-unit/facet shape "
                    f"{expected_ffi_shape}, observed {observed_ffi_shape}"
                )
            supporting = [
                item
                for item in data.get("work_units", [])
                if isinstance(item, dict) and item.get("criticality") == "supporting"
            ]
            expected_review_routes = [
                {"kind": "change-review.limitation"},
                {"kind": "change-review.analysis"},
            ]
            if (
                len(supporting) != 1
                or supporting[0].get("claim_routes") != expected_review_routes
                or len(supporting[0].get("facets", [])) != 11
            ):
                errors.append(
                    f"{path.name}: FFI review must be one 11-facet supporting stateful work unit"
                )
        contract_id = data.get("id") if isinstance(data, dict) else None
        if isinstance(contract_id, str) and contract_id in observed_contract_ids:
            errors.append(f"{path.name}: duplicate contract id {contract_id}")
        elif isinstance(contract_id, str):
            observed_contract_ids.add(contract_id)
    if required_contract_ids - observed_contract_ids:
        errors.append(f"missing workflow contracts: {sorted(required_contract_ids - observed_contract_ids)}")

    coverage = json.loads((ROOT / "evals" / "structural-coverage.json").read_text(encoding="utf-8"))
    expected_roles = {"root", "dev-flow-explorer", "dev-flow-worker", "dev-flow-test-runner", "dev-flow-blue-reviewer", "dev-flow-red-reviewer"}
    if set(coverage.get("roles", {})) != expected_roles:
        errors.append("structural coverage role set is incomplete")
    if ["child", "child"] not in coverage.get("forbidden_edges", []):
        errors.append("child-to-child delegation must be forbidden by default")
    child_result_invariant = (
        "every child has one written brief and one native result; "
        "a durable report is optional and brief-bound"
    )
    invariants = coverage.get("global_invariants", [])
    if child_result_invariant not in invariants:
        errors.append("structural coverage must require a brief-bound native child result")
    if "every child has one written brief and one report" in invariants:
        errors.append("structural coverage must not require a durable report from every child")

    practices = json.loads((ROOT / "governance" / "industry-practices.json").read_text(encoding="utf-8"))
    practice_by_id: dict[str, dict[str, object]] = {}
    for practice in practices.get("practices", []):
        if isinstance(practice, dict) and isinstance(practice.get("id"), str):
            practice_by_id[practice["id"]] = practice
        for field in ("id", "source", "checked_at", "decision", "adaptation", "complexity_limit", "evaluation", "review_after"):
            if not practice.get(field):
                errors.append(f"industry practice {practice.get('id')}: missing {field}")
    eval_practice = practice_by_id.get("IND-ANTHROPIC-AGENT-EVALS", {})
    evaluation_adaptation = str(eval_practice.get("adaptation", ""))
    for principle in (
        "affected-category",
        "three independent first attempts",
        "explicitly budgeted release comparison",
    ):
        if principle not in evaluation_adaptation:
            errors.append(
                f"industry-practice evaluation adaptation must retain {principle!r}"
            )

    methodology_registry = methodology_system.read_registry(
        ROOT / "governance" / "methodology-pool.json"
    )
    errors.extend(
        f"methodology registry: {error}"
        for error in methodology_system.validate_registry(
            methodology_registry,
            repository_root=ROOT,
        )
    )

    observed_skills = {item.get("skill") for item in capabilities if isinstance(item, dict)}
    filesystem_skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if observed_skills != filesystem_skills or len(capabilities) != len(observed_skills):
        errors.append("capability contract must define every repository Skill exactly once")
    output_owners: dict[str, str] = {}
    for item in capabilities:
        if not isinstance(item, dict):
            errors.append("capability contract entries must be objects")
            continue
        for field in ("skill", "direct_trigger", "negative_trigger", "owner"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"capability {item.get('skill')}: missing {field}")
        for field in ("primary_outputs", "consumes", "stops", "orchestrated_conditions"):
            value = item.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(entry, str) or not entry for entry in value):
                errors.append(f"capability {item.get('skill')}: invalid {field}")
        handoff = item.get("handoff_to")
        if not isinstance(handoff, list) or any(
            not isinstance(entry, str) or entry not in registered_skills for entry in handoff
        ):
            errors.append(f"capability {item.get('skill')}: invalid handoff_to")
        for output in item.get("primary_outputs", []):
            if output in output_owners:
                errors.append(f"primary output {output} has multiple owners: {output_owners[output]} and {item.get('skill')}")
            output_owners[output] = str(item.get("skill"))
    conditions_by_skill = {
        item.get("skill"): set(item.get("orchestrated_conditions", []))
        for item in capabilities
        if isinstance(item, dict)
    }
    if "non-micro-mutation" in conditions_by_skill.get("change-review", set()):
        errors.append("ordinary mutation must not automatically route change-review")
    if "mutating-task" in conditions_by_skill.get("delivery-readiness", set()):
        errors.append("ordinary mutation must not automatically route delivery-readiness")

    interaction = json.loads((ROOT / "governance" / "user-interaction-contract.json").read_text(encoding="utf-8"))
    if interaction.get("schema_version") != "1.0":
        errors.append("user interaction contract schema_version must be 1.0")
    mode_policy = interaction.get("mode_policy", {})
    if mode_policy.get("required_mode") != "Default":
        errors.append("user interaction must remain in Default mode")
    if mode_policy.get("switch_to_plan_for_interaction") != "forbidden":
        errors.append("Plan-mode switching for interaction must be forbidden")
    host_adapter = interaction.get("host_adapter", {})
    expected_adapter = {
        "tool": "request_user_input",
        "app_server_request": "item/tool/requestUserInput",
        "raw_protocol_frames": "forbidden",
        "feature_detection": "effective current-turn tool surface",
        "global_config_mutation": "forbidden",
    }
    for field, expected in expected_adapter.items():
        if host_adapter.get(field) != expected:
            errors.append(f"user interaction host adapter {field} must be {expected!r}")
    if host_adapter.get("protocol_lifecycle_owner") != "Codex App Server and client":
        errors.append("Codex App Server and client must own request lifecycle")
    if host_adapter.get("protocol_maturity") != "experimental":
        errors.append("request_user_input protocol maturity must remain explicit")
    if interaction.get("question_policy", {}).get("maximum_batch_size") != 3:
        errors.append("structured user input must limit a batch to three questions")
    expected_routes = {
        "bounded-choice-native": ("available", "request_user_input", "item/tool/requestUserInput"),
        "bounded-choice-fallback": ("unavailable-or-failed", "one focused non-enumerated Default-mode question or explicit blocker", "normal conversation"),
        "open-ended": ("irrelevant", "normal conversation", "normal conversation"),
        "command-or-file-approval": ("irrelevant", "host native approval surface", "host owned"),
        "secret": ("secure-surface-dependent", "host-approved secure input including request_user_input secret mode, or stop", "host owned"),
    }
    observed_routes: dict[str, tuple[object, object, object]] = {}
    for route in interaction.get("routes", []):
        if not isinstance(route, dict) or not isinstance(route.get("id"), str):
            errors.append("user interaction route must be an object with an id")
            continue
        route_id = route["id"]
        if route_id in observed_routes:
            errors.append(f"duplicate user interaction route {route_id}")
        observed_routes[route_id] = (
            route.get("tool_availability"),
            route.get("route"),
            route.get("transport"),
        )
    if observed_routes != expected_routes:
        errors.append("user interaction routes do not match the approved capability-safe matrix")
    response_policy = interaction.get("response_policy", {})
    expected_response_policy = {
        "option_answer": "accept exactly one presented non-empty option",
        "other_answer": "accept exactly one non-empty free-form answer only when Other is enabled",
        "unknown_question_or_stale_revision": "ignore and leave unresolved",
        "multiple_or_conflicting_answers": "leave unresolved as invalid",
        "cancel_or_interrupt": "leave unresolved without immediate re-prompt",
        "empty_omitted_or_malformed": "leave unresolved",
        "tool_unavailable_or_invocation_failed": "allow at most one focused non-enumerated Default-mode fallback when the host permits, otherwise block",
    }
    for field, expected in expected_response_policy.items():
        if response_policy.get(field) != expected:
            errors.append(f"user interaction response policy {field} must be {expected!r}")
    if response_policy.get("fallback_attempt_limit") != 1:
        errors.append("user interaction text fallback must be limited to one attempt")
    if response_policy.get("silent_recommendation_default") != "forbidden":
        errors.append("structured interaction must forbid silent recommendation defaults")
    for field in ("validate_question_ids", "validate_answer_values", "record_semantic_scope"):
        if response_policy.get(field) is not True:
            errors.append(f"user interaction response policy {field} must be true")

    interaction_reference = ROOT / "skills" / "requirements-design" / "references" / "user-interaction.md"
    reference_text = interaction_reference.read_text(encoding="utf-8") if interaction_reference.is_file() else ""
    for token in ("Default mode", "request_user_input", "item/tool/requestUserInput", "isBlocking", "isSecret", "None of these outcomes select the recommendation"):
        if token not in reference_text:
            errors.append(f"user interaction reference is missing {token}")
    for skill_name in registered_skills:
        skill_text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
        if "user-interaction.md" not in skill_text or "Default mode" not in skill_text:
            errors.append(f"{skill_name}: missing suite interaction invariant")
    context_template = (ROOT / "skills" / "dev-flow" / "templates" / "context.md").read_text(encoding="utf-8")
    if "Interaction route:" not in context_template:
        errors.append("context template must record the selected user interaction route")

    interaction_cases = json.loads((ROOT / "evals" / "user-interaction-cases.json").read_text(encoding="utf-8"))
    if interaction_cases.get("schema_version") != "1.0":
        errors.append("user interaction cases schema_version must be 1.0")
    observed_case_ids: set[str] = set()
    for case in interaction_cases.get("cases", []):
        if not isinstance(case, dict) or not isinstance(case.get("id"), str):
            errors.append("user interaction case must be an object with an id")
            continue
        case_id = case["id"]
        if case_id in observed_case_ids:
            errors.append(f"duplicate user interaction case {case_id}")
        observed_case_ids.add(case_id)
        actual = evaluate_user_interaction_case(case)
        if actual != case.get("expected"):
            errors.append(f"user interaction case {case_id}: expected {case.get('expected')!r}, observed {actual!r}")
    required_case_ids = {
        "valid-option",
        "valid-other",
        "outside-option-without-other",
        "empty-answer",
        "conflicting-answers",
        "unknown-question",
        "stale-revision",
        "user-cancelled",
        "client-interrupted",
        "request-cleared",
        "tool-unavailable-fallback",
        "invocation-failed-fallback",
        "fallback-exhausted",
        "plain-text-disallowed",
    }
    if observed_case_ids != required_case_ids:
        errors.append("user interaction response/lifecycle cases are incomplete")

    migration = json.loads((ROOT / "governance" / "content-migration-v1.json").read_text(encoding="utf-8"))
    if migration.get("status") != "complete" or not migration.get("records"):
        errors.append("content migration ledger must be complete and non-empty")
    for index, record in enumerate(migration.get("records", [])):
        if not isinstance(record, dict):
            errors.append(f"content migration record {index} must be an object")
            continue
        for field in ("source", "disposition", "reason"):
            if not isinstance(record.get(field), str) or not record[field]:
                errors.append(f"content migration record {index}: missing {field}")
        targets = record.get("targets")
        if not isinstance(targets, list) or not targets:
            errors.append(f"content migration record {index}: targets must be non-empty")
            continue
        for target in targets:
            if not isinstance(target, str) or not (ROOT / target).exists():
                errors.append(f"content migration record {index}: missing target {target}")

    routing = json.loads((ROOT / "evals" / "skill-routing-cases.json").read_text(encoding="utf-8"))
    routing_ids: set[str] = set()
    routing_cases = routing.get("cases", [])
    if not isinstance(routing_cases, list):
        errors.append("routing fixture cases must be a list")
        routing_cases = []
    for case in routing_cases:
        case_id = case.get("id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id:
            errors.append("routing case is missing an id")
            continue
        if case_id in routing_ids:
            errors.append(f"duplicate routing case id {case_id}")
        routing_ids.add(case_id)
        for field in ("args", "expected", "required", "forbidden"):
            if not isinstance(case.get(field), list):
                errors.append(f"routing case {case_id}: {field} must be a list")
        if case.get("work_mode") not in {"direct", "traced", "governed"}:
            errors.append(f"routing case {case_id}: invalid work_mode {case.get('work_mode')!r}")
        unknown = (
            set(case.get("expected", []))
            | set(case.get("required", []))
            | set(case.get("forbidden", []))
        ) - registered_skills
        if unknown:
            errors.append(f"routing case {case_id}: unknown Skills {sorted(unknown)}")
        args = case.get("args", [])
        declared_unresolved = case.get("unresolved_dimensions", [])
        if not isinstance(declared_unresolved, list) or any(
            not isinstance(dimension, str) or not dimension
            for dimension in declared_unresolved
        ):
            errors.append(
                f"routing case {case_id}: unresolved_dimensions must be a string list"
            )
        elif isinstance(args, list):
            argument_unresolved = sorted(
                str(args[index + 1])
                for index, argument in enumerate(args[:-1])
                if argument == "--unknown"
            )
            if sorted(declared_unresolved) != argument_unresolved:
                errors.append(
                    f"routing case {case_id}: unresolved_dimensions must exactly mirror --unknown arguments"
                )
        workflow = case.get("workflow")
        if workflow is not None:
            if not isinstance(workflow, dict) or set(workflow) != {
                "artifact_flow",
                "final_evidence",
                "forbidden_backfill",
            }:
                errors.append(f"routing case {case_id}: workflow shape is invalid")
                continue
            flow = workflow.get("artifact_flow")
            if not isinstance(flow, list) or not flow:
                errors.append(f"routing case {case_id}: workflow artifact_flow is empty")
                continue
            flow_skills: list[str] = []
            flow_outputs: list[str] = []
            for item in flow:
                if not isinstance(item, dict) or set(item) != {"skill", "output"}:
                    errors.append(f"routing case {case_id}: workflow artifact shape is invalid")
                    continue
                skill = item.get("skill")
                output = item.get("output")
                if output_owners.get(output) != skill:
                    errors.append(
                        f"routing case {case_id}: {output!r} is not owned by {skill!r}"
                    )
                flow_skills.append(str(skill))
                flow_outputs.append(str(output))
            routed_flow_skills = [skill for skill in flow_skills if skill != "dev-flow"]
            if routed_flow_skills != case.get("expected"):
                errors.append(
                    f"routing case {case_id}: workflow artifact order must match routed owners"
                )
            if "verification" in flow_skills:
                change_indexes = [
                    index
                    for index, output in enumerate(flow_outputs)
                    if output == "change-set.v1"
                ]
                if len(change_indexes) != 1:
                    errors.append(
                        f"routing case {case_id}: mutating workflow must contain one change-set.v1"
                    )
                elif change_indexes[0] != flow_skills.index("verification") - 1:
                    errors.append(
                        f"routing case {case_id}: change-set.v1 must immediately precede verification"
                    )
            if flow_outputs and workflow.get("final_evidence") != flow_outputs[-1]:
                errors.append(f"routing case {case_id}: final evidence must close artifact_flow")
            boundaries = workflow.get("forbidden_backfill")
            if not isinstance(boundaries, list) or not boundaries:
                errors.append(f"routing case {case_id}: forbidden_backfill must be non-empty")
                continue
            for boundary in boundaries:
                if not isinstance(boundary, dict) or set(boundary) != {"consumer", "output"}:
                    errors.append(f"routing case {case_id}: backfill boundary shape is invalid")
                    continue
                consumer = boundary.get("consumer")
                owner = output_owners.get(boundary.get("output"))
                if owner == consumer or owner not in flow_skills or consumer not in flow_skills:
                    errors.append(f"routing case {case_id}: backfill boundary owner is invalid")
                elif flow_skills.index(owner) >= flow_skills.index(consumer):
                    errors.append(
                        f"routing case {case_id}: {consumer} cannot backfill later-owned {boundary.get('output')}"
                    )
        overlap = set(case.get("required", [])) & set(case.get("forbidden", []))
        if overlap:
            errors.append(f"routing case {case_id}: required/forbidden overlap {sorted(overlap)}")

    # capability-contracts.json is the ownership/condition inventory. The route
    # fixture plus route-task implementation remain the executable routing policy;
    # this check prevents a registry owner from becoming unreachable without
    # pretending every natural-language condition can be compiled mechanically.
    explicit_only_owners = {
        item.get("skill")
        for item in capabilities
        if isinstance(item, dict)
        and isinstance(item.get("orchestrated_conditions"), list)
        and item["orchestrated_conditions"]
        and all(
            isinstance(condition, str) and condition.startswith("explicit-")
            for condition in item["orchestrated_conditions"]
        )
    }
    fixture_routed_owners = registered_skills - {
        "dev-flow",
        "repo-context",
    } - explicit_only_owners
    positive_owners = {
        skill
        for case in routing_cases
        if isinstance(case, dict)
        for skill in case.get("expected", [])
        if isinstance(skill, str)
    }
    negative_owners = {
        skill
        for case in routing_cases
        if isinstance(case, dict)
        for skill in case.get("forbidden", [])
        if isinstance(skill, str)
    }
    missing_positive = sorted(fixture_routed_owners - positive_owners)
    if missing_positive:
        errors.append(
            "capability ownership inventory has no positive routing fixture for "
            f"{missing_positive}"
        )
    missing_negative = sorted(fixture_routed_owners - negative_owners)
    if missing_negative:
        errors.append(
            "capability ownership inventory has no negative routing fixture for "
            f"{missing_negative}"
        )

    development_path = EVALS_ROOT / "paired-evaluations.json"
    acceptance_path = EVALS_ROOT / "paired-evaluations-acceptance.json"
    raw_configs = {
        "development": json.loads(development_path.read_text(encoding="utf-8")),
        "acceptance": json.loads(acceptance_path.read_text(encoding="utf-8")),
    }
    paired_configs: dict[str, dict[str, object]] = {}
    for role, raw_config in raw_configs.items():
        try:
            paired_configs[role] = validate_config(raw_config)
        except EvaluationError as exc:
            errors.append(f"{role} paired evaluation config is invalid: {exc}")
    paired = paired_configs.get("development", raw_configs["development"])
    acceptance = paired_configs.get("acceptance", raw_configs["acceptance"])
    for role, config in (("development", paired), ("acceptance", acceptance)):
        expected_config_version = "1.8" if role == "development" else "1.6"
        if config.get("schema_version") != expected_config_version:
            errors.append(
                f"{role} paired evaluation config must use schema {expected_config_version}"
            )
        if config.get("dataset_role") != role:
            errors.append(f"{role} paired evaluation config must declare dataset_role {role}")
        expected_case_contract = {
            "source_kind": "contract" if role == "development" else "catalog",
            "schema_version": "2.2" if role == "development" else "1.3",
            "obligations": "work-unit-facets-v3",
            "owner_registry": "governance/capability-contracts.json",
            "kind_registry": "governance/claim-kinds.json",
        }
        if config.get("case_contract") != expected_case_contract:
            errors.append(
                f"{role} paired evaluation case_contract must bind {expected_case_contract}"
            )
        if config.get("default_trials", 0) < 3:
            errors.append(f"{role} paired evaluation default_trials must be at least three")
    acceptance_evaluators = acceptance.get("release_evaluators")
    if (
        not isinstance(acceptance_evaluators, dict)
        or acceptance_evaluators.get("result_schema_version") != "1.3"
    ):
        errors.append("acceptance release evaluator result schema must be 1.3")
    if not (ROOT / "evals" / "run_paired_evaluations.py").is_file():
        errors.append("paired evaluation runner is missing")
    if not (ROOT / "evals" / "schemas" / "paired-evaluation-report.json").is_file():
        errors.append("paired evaluation report schema is missing")
    if not (ROOT / "evals" / "schemas" / "paired-evaluation-config.json").is_file():
        errors.append("paired evaluation config schema is missing")
    expected_metrics = [
        "requirement_fidelity",
        "coverage",
        "restraint",
        "ordinary_defect_retention",
        "actionability",
        "rework",
        "context_cost",
        "unsafe_actions",
        "reminder_rate",
        "false_block_rate",
    ]
    for role, config in (("development", paired), ("acceptance", acceptance)):
        if config.get("metrics") != expected_metrics:
            errors.append(f"{role} paired evaluation metrics must match the executable metric order")
    expected_thresholds = {
        "minimum_candidate_pass_rate",
        "minimum_candidate_requirement_fidelity",
        "minimum_candidate_ordinary_defect_retention",
        "maximum_candidate_unsafe_actions",
        "maximum_candidate_false_block_rate",
        "minimum_requirement_fidelity_delta",
        "minimum_ordinary_defect_retention_delta",
        "maximum_context_cost_ratio",
    }
    expected_release_keys = {"pair_ids", "category_ids", "minimum_cases_per_category", "trials_per_pair"}
    category_counts_by_role: dict[str, dict[str, int]] = {}
    pair_ids_by_role: dict[str, set[str]] = {}
    configured_contracts: set[str] = set()
    observed_catalog_cases: set[tuple[str, str]] = set()
    observed_catalog_case_ids: set[str] = set()
    configured_catalog_cases: set[tuple[str, str]] = set()
    case_prompts: dict[str, str] = {}
    case_fixtures: dict[str, str] = {}
    case_semantics: list[tuple[str, str, set[str]]] = []
    criticality_counts = {"critical": 0, "required": 0, "supporting": 0}
    critical_tasks_by_category: dict[str, int] = {}
    for role, config in (("development", paired), ("acceptance", acceptance)):
        expected_trials = 12 if role == "acceptance" else 5
        configured_pair_ids = [
            pair.get("id") for pair in config.get("pairs", []) if isinstance(pair, dict)
        ]
        pair_ids_by_role[role] = {
            pair_id for pair_id in configured_pair_ids if isinstance(pair_id, str)
        }
        release_plan = config.get("release_plan")
        if not isinstance(release_plan, dict) or set(release_plan) != expected_release_keys:
            errors.append(
                f"{role} paired evaluation release plan must bind pair IDs, category IDs, category size, and trials"
            )
        elif (
            release_plan.get("pair_ids") != configured_pair_ids
            or release_plan.get("trials_per_pair") != expected_trials
            or release_plan.get("minimum_cases_per_category") != 3
        ):
            errors.append(
                f"{role} paired evaluation plan must bind all pairs, three cases per category, "
                f"and {expected_trials} trials"
            )
        thresholds = config.get("release_thresholds")
        if not isinstance(thresholds, dict) or set(thresholds) != expected_thresholds:
            errors.append(f"{role} release thresholds do not match the executable gate contract")
        category_ids: list[str] = []
        category_counts: dict[str, int] = {}
        catalogs: dict[str, dict[str, dict[str, object]]] = {}
        for pair in config.get("pairs", []):
            if not isinstance(pair, dict):
                errors.append(f"{role} paired evaluation contains a non-object pair")
                continue
            pair_id = pair.get("id")
            category = pair.get("category")
            if isinstance(category, str) and category:
                if category not in category_counts:
                    category_ids.append(category)
                    category_counts[category] = 0
                category_counts[category] += 1
            unknown = set(pair.get("capabilities", [])) - registered_skills
            if unknown:
                errors.append(f"paired evaluation {pair_id}: unknown Skills {sorted(unknown)}")
            pair_capabilities = pair.get("capabilities")
            capability_context = pair.get("capability_context")
            if not isinstance(pair_capabilities, list) or not isinstance(capability_context, dict):
                errors.append(f"paired evaluation {pair_id}: invalid capability assembly")
            elif set(capability_context) != set(pair_capabilities):
                errors.append(
                    f"paired evaluation {pair_id}: capability_context keys must exactly match capabilities"
                )
            else:
                for capability in pair_capabilities:
                    references = capability_context.get(capability)
                    if not isinstance(references, list) or any(
                        not isinstance(reference, str) or not reference for reference in references
                    ):
                        errors.append(
                            f"paired evaluation {pair_id}: capability_context.{capability} must be a string list"
                        )
                        continue
                    if len(references) != len(set(references)):
                        errors.append(
                            f"paired evaluation {pair_id}: capability_context.{capability} must be unique"
                        )
                    for reference in references:
                        reference_path = ROOT / "skills" / capability / reference
                        if not reference_path.is_file():
                            errors.append(
                                f"paired evaluation {pair_id}: missing capability reference "
                                f"skills/{capability}/{reference}"
                            )
            if role == "development":
                fixture = pair.get("fixture")
                contract = pair.get("contract")
                if isinstance(contract, str):
                    configured_contracts.add(contract)
                    contract_data = json.loads((EVALS_ROOT / contract).read_text(encoding="utf-8"))
                    prompt = contract_data.get("prompt")
                    obligations = contract_data.get("work_units")
                else:
                    prompt = None
                    obligations = None
                fixture_text = (
                    (EVALS_ROOT / fixture).read_text(encoding="utf-8").strip()
                    if isinstance(fixture, str) and (EVALS_ROOT / fixture).is_file()
                    else None
                )
            else:
                source = pair.get("case_source")
                case_id = pair.get("case_id")
                if isinstance(source, str) and source not in catalogs:
                    catalog_data = json.loads((EVALS_ROOT / source).read_text(encoding="utf-8"))
                    if catalog_data.get("schema_version") != "1.3":
                        errors.append(f"{source}: acceptance catalog schema_version must be 1.3")
                    catalog_cases = catalog_data.get("cases")
                    if not isinstance(catalog_cases, list) or not catalog_cases:
                        errors.append(f"{source}: acceptance catalog cases must be a non-empty list")
                        catalog_cases = []
                    catalog_map: dict[str, dict[str, object]] = {}
                    for catalog_index, catalog_case in enumerate(catalog_cases, 1):
                        if not isinstance(catalog_case, dict):
                            errors.append(f"{source}: case {catalog_index} must be an object")
                            continue
                        catalog_id = catalog_case.get("id")
                        if not isinstance(catalog_id, str) or not catalog_id:
                            errors.append(f"{source}: case {catalog_index} must have an id")
                            continue
                        catalog_key = (source, catalog_id)
                        if catalog_key in observed_catalog_cases:
                            errors.append(f"{source}: duplicate case id {catalog_id}")
                        observed_catalog_cases.add(catalog_key)
                        if catalog_id in observed_catalog_case_ids:
                            errors.append(f"acceptance catalogs reuse case id {catalog_id}")
                        observed_catalog_case_ids.add(catalog_id)
                        errors.extend(
                            validate_contract(
                                Path(f"{source}:{catalog_id}"),
                                catalog_case,
                                registered_skills=registered_skills,
                                registered_kinds=registered_kinds,
                                schema_version=None,
                                fixture_is_path=False,
                            )
                        )
                        expected_ffi_shape = ACCEPTANCE_FFI_SHAPES.get(catalog_id)
                        if expected_ffi_shape is not None:
                            observed_ffi_shape = work_unit_shape(catalog_case.get("work_units"))
                            if observed_ffi_shape != expected_ffi_shape:
                                errors.append(
                                    f"{source}:{catalog_id}: expected FFI work-unit/facet shape "
                                    f"{expected_ffi_shape}, observed {observed_ffi_shape}"
                                )
                            supporting = [
                                item
                                for item in catalog_case.get("work_units", [])
                                if isinstance(item, dict)
                                and item.get("criticality") == "supporting"
                            ]
                            expected_review_routes = [
                                {"kind": "change-review.limitation"},
                                {"kind": "change-review.analysis"},
                            ]
                            if (
                                len(supporting) != 1
                                or supporting[0].get("claim_routes") != expected_review_routes
                            ):
                                errors.append(
                                    f"{source}:{catalog_id}: FFI review must be one supporting "
                                    "stateful work unit"
                                )
                        catalog_map[catalog_id] = catalog_case
                    catalogs[source] = catalog_map
                case = catalogs.get(source, {}).get(case_id) if isinstance(source, str) else None
                if isinstance(source, str) and isinstance(case_id, str):
                    configured_catalog_cases.add((source, case_id))
                prompt = case.get("prompt") if isinstance(case, dict) else None
                fixture_text = case.get("fixture", "").strip() if isinstance(case, dict) else None
                obligations = case.get("work_units") if isinstance(case, dict) else None
            for alignment_error in capability_alignment_errors(
                obligations,
                pair.get("capabilities"),
                registered_skills,
                registered_kinds,
            ):
                errors.append(f"paired evaluation {pair_id}: {alignment_error}")
            if isinstance(obligations, list):
                levels = {
                    item.get("criticality")
                    for item in obligations
                    if isinstance(item, dict)
                }
                for item in obligations:
                    if isinstance(item, dict) and item.get("criticality") in criticality_counts:
                        criticality_counts[item["criticality"]] += 1
                if isinstance(category, str) and "critical" in levels:
                    critical_tasks_by_category[category] = (
                        critical_tasks_by_category.get(category, 0) + 1
                    )
            if isinstance(prompt, str):
                previous = case_prompts.setdefault(prompt.strip(), str(pair_id))
                if previous != pair_id:
                    errors.append(f"paired cases {previous} and {pair_id} reuse the same prompt")
            if isinstance(fixture_text, str):
                previous = case_fixtures.setdefault(fixture_text, str(pair_id))
                if previous != pair_id:
                    errors.append(f"paired cases {previous} and {pair_id} reuse the same fixture")
            if isinstance(category, str) and isinstance(prompt, str) and isinstance(fixture_text, str):
                tokens = set(re.findall(r"[a-z0-9]+", f"{prompt} {fixture_text}".lower()))
                case_semantics.append((category, str(pair_id), tokens))
        category_counts_by_role[role] = category_counts
        if isinstance(release_plan, dict) and release_plan.get("category_ids") != category_ids:
            errors.append(f"{role} release category IDs must match first appearance order")

    development_counts = category_counts_by_role.get("development", {})
    acceptance_counts = category_counts_by_role.get("acceptance", {})
    for role, counts, config in (
        ("development", development_counts, paired),
        ("acceptance", acceptance_counts, acceptance),
    ):
        minimum_cases = config.get("release_plan", {}).get("minimum_cases_per_category", 3)
        if not counts or not isinstance(minimum_cases, int) or any(
            count < minimum_cases for count in counts.values()
        ):
            errors.append(
                f"{role} evaluation bank must cover every declared category with its bounded minimum: {counts}"
            )
    if not set(development_counts).issubset(acceptance_counts):
        errors.append("acceptance categories must cover every development category")
    acceptance_pass_floor = acceptance.get("release_thresholds", {}).get("minimum_candidate_pass_rate")
    if not isinstance(acceptance_pass_floor, (int, float)) or acceptance_pass_floor < 0.9:
        errors.append("acceptance minimum candidate pass rate must be at least 0.9")
    required_new_categories = {
        "CAT-ARCHITECTURE",
        "CAT-SECURITY-PRIVACY",
        "CAT-PERFORMANCE-RESOURCES",
        "CAT-CONCURRENCY-RECOVERY",
    }
    if not required_new_categories.issubset(acceptance_counts):
        errors.append(
            "acceptance evaluation bank is missing high-risk categories "
            f"{sorted(required_new_categories - acceptance_counts.keys())}"
        )
    total_work_units = sum(criticality_counts.values())
    if (
        total_work_units == 0
        or criticality_counts["critical"] / total_work_units >= 0.3
        or criticality_counts["required"] <= criticality_counts["critical"]
        or criticality_counts["supporting"] == 0
    ):
        errors.append(
            "evaluation work units must separate a minority safety-critical tier from the "
            f"larger required-completeness tier: {criticality_counts}"
        )
    high_consequence_categories = {
        "CAT-CONCURRENCY-RECOVERY",
        "CAT-DELIVERY",
        "CAT-DEPENDENCY",
        "CAT-FFI",
        "CAT-INTERACTION",
        "CAT-MIGRATION",
        "CAT-REVIEW",
        "CAT-SECURITY-PRIVACY",
    }
    missing_critical_categories = high_consequence_categories - critical_tasks_by_category.keys()
    if missing_critical_categories:
        errors.append(
            "high-consequence categories must retain explicit critical work units: "
            f"{sorted(missing_critical_categories)}"
        )
    if not pair_ids_by_role.get("development", set()).isdisjoint(pair_ids_by_role.get("acceptance", set())):
        errors.append("development and acceptance pair IDs must be disjoint")
    for index, (category, pair_id, tokens) in enumerate(case_semantics):
        for other_category, other_pair_id, other_tokens in case_semantics[index + 1 :]:
            if category != other_category:
                continue
            union = tokens | other_tokens
            similarity = len(tokens & other_tokens) / len(union) if union else 1.0
            if similarity >= 0.65:
                errors.append(
                    f"paired cases {pair_id} and {other_pair_id} are insufficiently distinct "
                    f"within {category}: token_jaccard={similarity:.3f}"
                )
    expected_contract_paths = {path.relative_to(ROOT / "evals").as_posix() for path in contracts}
    if configured_contracts != expected_contract_paths:
        errors.append("development paired evaluation must consume every active structured contract exactly once")
    if configured_catalog_cases != observed_catalog_cases:
        errors.append("acceptance paired evaluation must consume every active frozen catalog case exactly once")

    for schema in (ROOT / "evals" / "schemas").glob("*.json"):
        data = json.loads(schema.read_text(encoding="utf-8"))
        if schema.name == "assembler-request.json" and "oneOf" in data:
            branches = data["oneOf"]
            if not isinstance(branches, list) or not branches or any(
                not isinstance(branch, dict) or branch.get("additionalProperties") is not False
                for branch in branches
            ):
                errors.append("assembler-request.json: every versioned branch must set additionalProperties false")
        elif data.get("additionalProperties") is not False:
            errors.append(f"{schema.name}: top-level additionalProperties must be false")

    print(json.dumps({"status": "valid" if not errors else "invalid", "contracts": len(contracts), "errors": errors}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
