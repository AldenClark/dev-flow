#!/usr/bin/env python3
"""Validate deterministic eval and governance contracts without external packages."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors: list[str] = []
    contracts = sorted((ROOT / "evals" / "contracts").glob("*.json"))
    if len(contracts) < 4:
        errors.append("at least four representative contracts are required")
    for path in contracts:
        data = json.loads(path.read_text(encoding="utf-8"))
        for field in ("id", "profile", "prompt", "fixture", "expected_actions", "forbidden_actions", "required_artifacts"):
            if not data.get(field):
                errors.append(f"{path.name}: missing {field}")
        fixture = ROOT / "evals" / str(data.get("fixture", ""))
        if not fixture.is_file():
            errors.append(f"{path.name}: missing fixture {fixture}")

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
