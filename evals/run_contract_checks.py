#!/usr/bin/env python3
"""Validate deterministic eval and governance contracts without external packages."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_TEXT_FIELDS = ("id", "profile", "prompt", "fixture")
CONTRACT_LIST_FIELDS = ("expected_actions", "forbidden_actions", "required_artifacts")
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
EXPECTED_SKILLS = {
    "architecture-decisions",
    "change-review",
    "delivery-readiness",
    "dependency-decisions",
    "dev-flow",
    "dev-flow-maintainer",
    "manage-engineering-profiles",
    "product-ux-discovery",
    "repo-context",
    "requirements-design",
    "systematic-debugging",
    "verification",
}
DESCRIPTION_BUDGET = 2500
ORDINARY_STATIC_BUDGET = 15000
ORDINARY_STATIC_FILES = (
    "skills/dev-flow/SKILL.md",
    "skills/dev-flow/references/artifact-schemas.md",
    "skills/repo-context/SKILL.md",
    "skills/verification/SKILL.md",
)


def validate_contract(path: Path, data: object, *, root: Path = ROOT) -> list[str]:
    if not isinstance(data, dict):
        return [f"{path.name}: contract must be an object"]
    errors: list[str] = []
    for field in CONTRACT_TEXT_FIELDS:
        if not isinstance(data.get(field), str) or not data[field].strip():
            errors.append(f"{path.name}: {field} must be a non-empty string")
    for field in CONTRACT_LIST_FIELDS:
        value = data.get(field)
        if not isinstance(value, list) or not value:
            errors.append(f"{path.name}: {field} must be a non-empty list")
            continue
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
    if isinstance(fixture, str) and fixture.strip() and not (root / "evals" / fixture).is_file():
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
    for skill_name in EXPECTED_SKILLS:
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
    contracts = sorted((ROOT / "evals" / "contracts").glob("*.json"))
    if len(contracts) < 9:
        errors.append("at least nine representative contracts are required")
    required_contract_ids = {
        "CASE-FRONTEND-NEW-PRODUCT",
        "CASE-FRONTEND-PRESERVE-IA",
        "CASE-REPOSITORY-INSTRUCTIONS",
        "CASE-SEMANTIC-CLARIFICATION",
        "CASE-STRUCTURED-USER-INPUT",
    }
    observed_contract_ids: set[str] = set()
    for path in contracts:
        data = json.loads(path.read_text(encoding="utf-8"))
        errors.extend(validate_contract(path, data))
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

    practices = json.loads((ROOT / "governance" / "industry-practices.json").read_text(encoding="utf-8"))
    for practice in practices.get("practices", []):
        for field in ("id", "source", "checked_at", "decision", "adaptation", "complexity_limit", "evaluation", "review_after"):
            if not practice.get(field):
                errors.append(f"industry practice {practice.get('id')}: missing {field}")

    capability_contracts = json.loads((ROOT / "governance" / "capability-contracts.json").read_text(encoding="utf-8"))
    capabilities = capability_contracts.get("capabilities", [])
    observed_skills = {item.get("skill") for item in capabilities if isinstance(item, dict)}
    if observed_skills != EXPECTED_SKILLS or len(capabilities) != len(EXPECTED_SKILLS):
        errors.append("capability contract must define each of the 12 Skills exactly once")
    output_owners: dict[str, str] = {}
    for item in capabilities:
        if not isinstance(item, dict):
            errors.append("capability contract entries must be objects")
            continue
        for field in ("skill", "direct_trigger", "negative_trigger", "owner"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"capability {item.get('skill')}: missing {field}")
        for field in ("primary_outputs", "orchestrated_conditions"):
            value = item.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(entry, str) or not entry for entry in value):
                errors.append(f"capability {item.get('skill')}: invalid {field}")
        for output in item.get("primary_outputs", []):
            if output in output_owners:
                errors.append(f"primary output {output} has multiple owners: {output_owners[output]} and {item.get('skill')}")
            output_owners[output] = str(item.get("skill"))

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
    for skill_name in EXPECTED_SKILLS:
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
    for case in routing.get("cases", []):
        case_id = case.get("id") if isinstance(case, dict) else None
        if not isinstance(case_id, str) or not case_id:
            errors.append("routing case is missing an id")
            continue
        if case_id in routing_ids:
            errors.append(f"duplicate routing case id {case_id}")
        routing_ids.add(case_id)
        for field in ("args", "required", "forbidden"):
            if not isinstance(case.get(field), list):
                errors.append(f"routing case {case_id}: {field} must be a list")
        unknown = (set(case.get("required", [])) | set(case.get("forbidden", []))) - EXPECTED_SKILLS
        if unknown:
            errors.append(f"routing case {case_id}: unknown Skills {sorted(unknown)}")
        overlap = set(case.get("required", [])) & set(case.get("forbidden", []))
        if overlap:
            errors.append(f"routing case {case_id}: required/forbidden overlap {sorted(overlap)}")

    paired = json.loads((ROOT / "evals" / "paired-evaluations.json").read_text(encoding="utf-8"))
    if paired.get("default_trials", 0) < 3:
        errors.append("paired evaluation default_trials must be at least three")
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
    if paired.get("metrics") != expected_metrics:
        errors.append("paired evaluation metric contract must exactly match the executable metric order")
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
    thresholds = paired.get("release_thresholds")
    if not isinstance(thresholds, dict) or set(thresholds) != expected_thresholds:
        errors.append("paired evaluation release thresholds do not match the executable gate contract")
    configured_pair_ids = [pair.get("id") for pair in paired.get("pairs", []) if isinstance(pair, dict)]
    release_plan = paired.get("release_plan")
    if not isinstance(release_plan, dict) or set(release_plan) != {"pair_ids", "trials_per_pair"}:
        errors.append("paired evaluation release plan must define only pair_ids and trials_per_pair")
    elif release_plan.get("pair_ids") != configured_pair_ids or release_plan.get("trials_per_pair") != 5:
        errors.append("paired evaluation release plan must bind all configured pairs and five trials")
    for pair in paired.get("pairs", []):
        fixture = pair.get("fixture") if isinstance(pair, dict) else None
        if not isinstance(fixture, str) or not (ROOT / "evals" / fixture).is_file():
            errors.append(f"paired evaluation {pair.get('id')}: missing fixture {fixture}")
        unknown = set(pair.get("capabilities", [])) - EXPECTED_SKILLS
        if unknown:
            errors.append(f"paired evaluation {pair.get('id')}: unknown Skills {sorted(unknown)}")

    for schema in (ROOT / "evals" / "schemas").glob("*.json"):
        data = json.loads(schema.read_text(encoding="utf-8"))
        if data.get("additionalProperties") is not False:
            errors.append(f"{schema.name}: top-level additionalProperties must be false")

    print(json.dumps({"status": "valid" if not errors else "invalid", "contracts": len(contracts), "errors": errors}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
