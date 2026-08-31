#!/usr/bin/env python3
"""Validate the registered Dev Flow owner topology and cutover invariants."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
HISTORICAL_FILES = {"CHANGELOG.md", "content-migration-v1.json"}
DESCRIPTION_BUDGET = 2660
ORDINARY_STATIC_BUDGET = 18000
DESCRIPTION_TARGET = 2128
ORDINARY_STATIC_TARGET = 14400
DESCRIPTION_WARNING = 1995
ORDINARY_STATIC_WARNING = 13500
ORDINARY_STATIC_FILES = (
    "skills/dev-flow/SKILL.md",
    "skills/repo-context/SKILL.md",
    "skills/verification/SKILL.md",
)
ROUTE_REQUIRED_CASES = {
    "ROUTE-READONLY",
    "ROUTE-READONLY-SECURITY",
    "ROUTE-ROUTINE",
    "ROUTE-SECURITY-OVERLAY",
    "ROUTE-DELIVERY",
    "ROUTE-MATERIAL-UI",
    "ROUTE-MAINTAINER",
    "ROUTE-TEST-SYSTEM-EXPLICIT",
    "ROUTE-TEST-SYSTEM-FALLBACK",
    "ROUTE-TEST-SYSTEM-EFFECTIVE",
}
DISPATCH_REQUIRED_CASES = {
    "DISPATCH-EXACT-LOOKUP",
    "DISPATCH-BOUNDED-DEPTH",
    "DISPATCH-BROAD-CAPABILITY",
    "DISPATCH-BROAD-AND-DEEP",
    "DISPATCH-CRITICAL-RISK",
    "DISPATCH-CRITICAL-ACCEPTANCE",
    "DISPATCH-ROOT-ONLY",
    "DISPATCH-ROLE-MISMATCH",
    "DISPATCH-PX-GUARD",
    "DISPATCH-DOWNGRADE-GUARD",
    "DISPATCH-SEQUENTIAL-ROOT",
}


def validate_routes(registered: set[str]) -> list[str]:
    errors: list[str] = []
    case_path = ROOT / "evals" / "skill-routing-cases.json"
    try:
        payload = json.loads(case_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid routing cases: {exc}"]
    cases = payload.get("cases") if isinstance(payload, dict) else None
    if not isinstance(cases, list):
        return ["routing cases must define a cases list"]
    observed_ids = {case.get("id") for case in cases if isinstance(case, dict)}
    missing = ROUTE_REQUIRED_CASES - observed_ids
    if missing:
        errors.append(f"routing cases omit responsibility-boundary cases: {sorted(missing)}")
    flow = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
    for case in cases:
        if not isinstance(case, dict):
            errors.append("routing case must be an object")
            continue
        case_id = str(case.get("id"))
        args = case.get("args")
        expected = case.get("expected")
        if not isinstance(args, list) or any(not isinstance(value, str) for value in args):
            errors.append(f"{case_id}: args must be a string list")
            continue
        if not isinstance(expected, list) or any(route not in registered for route in expected):
            errors.append(f"{case_id}: expected must contain known Skills")
            continue
        completed = subprocess.run(
            [sys.executable, str(flow), "route-task", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            errors.append(f"{case_id}: router did not emit JSON")
            continue
        actual = [entry.get("skill") for entry in result.get("routes", []) if isinstance(entry, dict)]
        if completed.returncode != 0 or actual != expected or result.get("work_mode") != case.get("work_mode"):
            errors.append(
                f"{case_id}: exact route/mode drift; expected {expected}/{case.get('work_mode')}, "
                f"observed {actual}/{result.get('work_mode')}"
            )
            continue
        positions = {route: index for index, route in enumerate(actual)}
        ordered_edges = (
            ("repo-context", "product-ux-discovery"),
            ("repo-context", "requirements-design"),
            ("product-ux-discovery", "requirements-design"),
            ("requirements-design", "architecture-decisions"),
            ("requirements-design", "dependency-decisions"),
            ("systematic-debugging", "architecture-decisions"),
            ("architecture-decisions", "dev-flow-maintainer"),
            ("dev-flow-maintainer", "verification"),
            ("architecture-decisions", "verification"),
            ("dependency-decisions", "verification"),
            ("verification", "change-review"),
            ("change-review", "delivery-readiness"),
            ("verification", "delivery-readiness"),
        )
        for upstream, downstream in ordered_edges:
            if upstream in positions and downstream in positions and positions[upstream] >= positions[downstream]:
                errors.append(f"{case_id}: {upstream} must precede {downstream}")
        task_type = args[args.index("--task-type") + 1] if "--task-type" in args else None
        intent = args[args.index("--intent") + 1] if "--intent" in args else None
        explicit_delivery = intent == "delivery" or (
            "--need" in args
            and any(
                args[index + 1] == "delivery"
                for index, value in enumerate(args[:-1])
                if value == "--need"
            )
        )
        if "delivery-readiness" in positions and not explicit_delivery and task_type not in {"release-hotfix", "rollback"}:
            errors.append(f"{case_id}: delivery-readiness requires explicit delivery intent")
    return errors


def validate_agent_dispatch() -> tuple[list[str], int]:
    errors: list[str] = []
    case_path = ROOT / "evals" / "agent-dispatch-routing-cases.json"
    try:
        payload = json.loads(case_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid agent dispatch cases: {exc}"], 0
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "cases"} or payload.get("schema_version") != "1.0":
        return ["agent dispatch cases must use exact schema 1.0"], 0
    cases = payload.get("cases")
    if not isinstance(cases, list):
        return ["agent dispatch cases must define a cases list"], 0
    observed_ids = {case.get("id") for case in cases if isinstance(case, dict)}
    missing = DISPATCH_REQUIRED_CASES - observed_ids
    if missing:
        errors.append(f"agent dispatch cases omit required boundaries: {sorted(missing)}")
    flow = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "args", "exit", "expected"}:
            errors.append("agent dispatch case must define id, args, exit, and expected")
            continue
        case_id = case["id"]
        args = case["args"]
        expected = case["expected"]
        if not isinstance(case_id, str) or not case_id or not isinstance(args, list) or any(not isinstance(value, str) for value in args):
            errors.append(f"{case_id}: invalid id or args")
            continue
        if not isinstance(case["exit"], int) or not isinstance(expected, dict):
            errors.append(f"{case_id}: invalid exit or expected contract")
            continue
        completed = subprocess.run(
            [sys.executable, str(flow), "route-agent", *args],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        try:
            result = json.loads(completed.stdout)
        except json.JSONDecodeError:
            errors.append(f"{case_id}: dispatch router did not emit JSON")
            continue
        if completed.returncode != case["exit"]:
            errors.append(f"{case_id}: expected exit {case['exit']}, observed {completed.returncode}")
            continue
        for key, value in expected.items():
            if result.get(key) != value:
                errors.append(f"{case_id}: expected {key}={value!r}, observed {result.get(key)!r}")
    return errors, len(cases)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    contract_path = ROOT / "governance" / "capability-contracts.json"
    try:
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid capability contract: {exc}")
        contract = {}
    capabilities = contract.get("capabilities")
    if not isinstance(capabilities, list):
        capabilities = []
    registered = {
        item.get("skill")
        for item in capabilities
        if isinstance(item, dict) and isinstance(item.get("skill"), str) and item["skill"]
    }
    skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if skills != registered:
        errors.append(f"Skill inventory must match the capability registry: registered {sorted(registered)}, observed {sorted(skills)}")
    names: set[str] = set()
    description_total = 0
    for directory in sorted((ROOT / "skills").iterdir()):
        if not directory.is_dir():
            continue
        skill = directory / "SKILL.md"
        text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
        if not match or match.group(1) != directory.name:
            errors.append(f"{directory.name}: invalid or mismatched Skill name")
        if match and match.group(1) in names:
            errors.append(f"duplicate Skill name: {match.group(1)}")
        if match:
            names.add(match.group(1))
        description = re.search(r"(?m)^description:\s*(.+)\s*$", text)
        if not description:
            errors.append(f"{directory.name}: missing one-line Skill description")
        else:
            description_total += len(description.group(1).strip())
        if text.count("\n") + 1 > 500:
            errors.append(f"{directory.name}: SKILL.md exceeds 500 lines")
        if "TODO" in text or "[TODO" in text:
            errors.append(f"{directory.name}: unresolved scaffold placeholder")
        metadata = directory / "agents" / "openai.yaml"
        if not metadata.is_file() or f"${directory.name}" not in metadata.read_text(encoding="utf-8"):
            errors.append(f"{directory.name}: stale agents/openai.yaml")
    if description_total > DESCRIPTION_BUDGET:
        errors.append(f"Skill descriptions exceed {DESCRIPTION_BUDGET} characters: {description_total}")
    elif description_total > DESCRIPTION_WARNING:
        warnings.append(
            f"Skill descriptions exceed the 75% early-warning level {DESCRIPTION_WARNING}: {description_total}"
        )
    ordinary_static_total = sum(
        len((ROOT / path).read_text(encoding="utf-8").encode("utf-8"))
        for path in ORDINARY_STATIC_FILES
    )
    if ordinary_static_total > ORDINARY_STATIC_BUDGET:
        errors.append(f"ordinary static path exceeds {ORDINARY_STATIC_BUDGET} bytes: {ordinary_static_total}")
    elif ordinary_static_total > ORDINARY_STATIC_WARNING:
        warnings.append(
            f"ordinary static path exceeds the 75% early-warning level {ORDINARY_STATIC_WARNING}: {ordinary_static_total}"
        )
    maintainer_metadata = (ROOT / "skills" / "dev-flow-maintainer" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "allow_implicit_invocation: false" not in maintainer_metadata:
        errors.append("dev-flow-maintainer must remain explicit-only")
    if set(contract) != {"schema_version", "capabilities"} or contract.get("schema_version") != "1.0":
        errors.append("capability contract must use exact schema 1.0")
    if not isinstance(contract.get("capabilities"), list):
        errors.append("capability contract must define a capabilities list")
    observed = [item.get("skill") for item in capabilities if isinstance(item, dict)]
    if len(observed) != len(registered):
        errors.append("capability contract must define every registered Skill exactly once")
    output_owners: dict[str, str] = {}
    legacy_active_terms = ("packet", "digest", "checkpoint", "change-set.v1", "flow.state.v1")
    for item in capabilities:
        if not isinstance(item, dict):
            errors.append("capability contract entry must be an object")
            continue
        skill_name = item.get("skill")
        for field in ("direct_trigger", "negative_trigger", "owner"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                errors.append(f"capability {skill_name}: missing {field}")
        for field in ("primary_outputs", "consumes", "stops", "orchestrated_conditions"):
            value = item.get(field)
            if not isinstance(value, list) or not value or any(not isinstance(entry, str) or not entry for entry in value):
                errors.append(f"capability {skill_name}: invalid {field}")
        handoff = item.get("handoff_to")
        if not isinstance(handoff, list) or any(entry not in registered for entry in handoff):
            errors.append(f"capability {skill_name}: invalid handoff_to")
        for output in item.get("primary_outputs", []):
            if output in output_owners:
                errors.append(f"primary output {output} has multiple owners")
            output_owners[output] = str(skill_name)
        active_semantics = json.dumps(
            {field: item.get(field) for field in ("primary_outputs", "consumes", "stops")},
            ensure_ascii=False,
        ).lower()
        if any(term in active_semantics for term in legacy_active_terms):
            errors.append(f"capability {skill_name}: active semantics contain legacy packet-era terms")
        # The capability registry is the single machine-readable owner topology.
        # Task-facing Skills describe only decisions and procedure; duplicating the
        # registry's consumes/stops/handoff fields in every entrypoint creates drift.
    conditions = {
        item.get("skill"): set(item.get("orchestrated_conditions", []))
        for item in capabilities
        if isinstance(item, dict)
    }
    if "non-micro-mutation" in conditions.get("change-review", set()):
        errors.append("ordinary mutation must not automatically route change-review")
    if "mutating-task" in conditions.get("delivery-readiness", set()):
        errors.append("ordinary mutation must not automatically route delivery-readiness")
    if "delivery-risk" in conditions.get("delivery-readiness", set()):
        errors.append("risk alone must not automatically route delivery-readiness")
    errors.extend(validate_routes(registered))
    dispatch_errors, dispatch_cases = validate_agent_dispatch()
    errors.extend(dispatch_errors)
    legacy = "engineering-" + "preferences"
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".codex", "__pycache__"} for part in path.parts):
            continue
        if path.name in HISTORICAL_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if legacy in text:
            errors.append(f"live legacy Skill reference remains: {path.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "status": "valid" if not errors else "invalid",
                "skills": len(skills),
                "description_characters": description_total,
                "description_target": DESCRIPTION_TARGET,
                "description_target_met": description_total <= DESCRIPTION_TARGET,
                "ordinary_static_bytes": ordinary_static_total,
                "ordinary_static_target": ORDINARY_STATIC_TARGET,
                "ordinary_static_target_met": ordinary_static_total <= ORDINARY_STATIC_TARGET,
                "agent_dispatch_cases": dispatch_cases,
                "warnings": warnings,
                "errors": errors,
            },
            indent=2,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
