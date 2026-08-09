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


def main() -> int:
    errors: list[str] = []
    contracts = sorted((ROOT / "evals" / "contracts").glob("*.json"))
    if len(contracts) < 8:
        errors.append("at least eight representative contracts are required")
    required_contract_ids = {
        "CASE-FRONTEND-NEW-PRODUCT",
        "CASE-FRONTEND-PRESERVE-IA",
        "CASE-REPOSITORY-INSTRUCTIONS",
        "CASE-SEMANTIC-CLARIFICATION",
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
    metrics = paired.get("metrics", [])
    for required_metric in ("coverage", "restraint", "actionability", "rework", "context_cost", "unsafe_actions"):
        if required_metric not in metrics:
            errors.append(f"paired evaluation contract is missing metric {required_metric}")
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
