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
    if len(contracts) < 7:
        errors.append("at least seven representative contracts are required")
    required_contract_ids = {
        "CASE-FRONTEND-NEW-PRODUCT",
        "CASE-FRONTEND-PRESERVE-IA",
        "CASE-REPOSITORY-INSTRUCTIONS",
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

    for schema in (ROOT / "evals" / "schemas").glob("*.json"):
        data = json.loads(schema.read_text(encoding="utf-8"))
        if data.get("additionalProperties") is not False:
            errors.append(f"{schema.name}: top-level additionalProperties must be false")

    print(json.dumps({"status": "valid" if not errors else "invalid", "contracts": len(contracts), "errors": errors}, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
