#!/usr/bin/env python3
"""Prove bidirectional RC.4 requirement/change/test traceability without drift."""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


SCHEMA = "dev-flow.rc4.traceability.v1"
REQUIREMENT_PATTERN = re.compile(r"<!-- requirement: (RC4-[A-Z-]+) -->")
DECISION_PATTERN = re.compile(r"^## (D[1-9][0-9]*):", re.MULTILINE)
IMPLEMENTATION_DECISION_PATTERN = re.compile(r"\bD(?:[1-9]|1[0-4])\b")


def matches(path: str, declaration: str) -> bool:
    if declaration.endswith("/"):
        return path.startswith(declaration)
    return path == declaration


def source_requirement_ids(text: str) -> list[str]:
    return REQUIREMENT_PATTERN.findall(text)


def source_decision_ids(text: str) -> list[str]:
    return DECISION_PATTERN.findall(text)


def implementation_decision_ids(text: str) -> set[str]:
    return set(IMPLEMENTATION_DECISION_PATTERN.findall(text))


def python_test_symbols(path: Path) -> set[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, UnicodeDecodeError, SyntaxError):
        return set()

    def meaningful(node: ast.AST) -> bool:
        for child in ast.walk(node):
            if isinstance(child, ast.Assert):
                return True
            if isinstance(child, ast.Call):
                function = child.func
                if isinstance(function, ast.Attribute) and function.attr.startswith(("assert", "fail")):
                    return True
        return False

    symbols: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name.startswith("test_") and meaningful(node):
                symbols.add(node.name)
        elif isinstance(node, ast.ClassDef):
            methods = [
                child
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                and child.name.startswith("test_")
                and meaningful(child)
            ]
            if methods:
                symbols.add(node.name)
                symbols.update(method.name for method in methods)
                symbols.update(f"{node.name}.{method.name}" for method in methods)
    return symbols


def json_case_ids(path: Path) -> set[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return set()
    identifiers: set[str] = set()

    def visit(value: Any) -> None:
        if isinstance(value, dict):
            if isinstance(value.get("id"), str):
                identifiers.add(value["id"])
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(payload)
    return identifiers


def _git_paths(root: Path, *args: str) -> list[str]:
    completed = subprocess.run(
        ["git", *args], cwd=root, capture_output=True, check=False
    )
    if completed.returncode != 0:
        raise RuntimeError("cannot enumerate changed Git paths")
    return sorted(
        entry.decode("utf-8", "surrogateescape")
        for entry in completed.stdout.split(b"\0")
        if entry
    )


def worktree_changed_paths(root: Path) -> list[str]:
    tracked = _git_paths(
        root,
        "diff",
        "--name-only",
        "--diff-filter=ACMRDTUXB",
        "-z",
        "HEAD",
    )
    untracked = _git_paths(
        root, "ls-files", "-o", "--exclude-standard", "-z"
    )
    return sorted(set(tracked) | set(untracked))


def event_changed_paths(root: Path, event_name: str, event_path: Path) -> list[str]:
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    if event_name == "pull_request":
        base = payload["pull_request"]["base"]["sha"]
        head = payload["pull_request"]["head"]["sha"]
        return _git_paths(root, "diff", "--name-only", "--diff-filter=ACMRDTUXB", "-z", f"{base}...{head}")
    if event_name == "push":
        base = payload.get("before")
        head = payload.get("after")
        if not isinstance(head, str) or not head:
            raise ValueError("push event does not contain an after SHA")
        if not isinstance(base, str) or not base or base == "0" * 40:
            return _git_paths(root, "ls-tree", "-r", "--name-only", "-z", head)
        return _git_paths(root, "diff", "--name-only", "--diff-filter=ACMRDTUXB", "-z", f"{base}..{head}")
    raise ValueError(f"unsupported GitHub event: {event_name or '<missing>'}")


def validate(root: Path, *, check_worktree: bool, check_event: bool = False) -> dict[str, Any]:
    trace_path = root / "governance" / "rc4-traceability.json"
    errors: list[str] = []
    try:
        payload = json.loads(trace_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "coverage_percent": 0, "errors": [str(exc)]}
    if set(payload) != {"schema_version", "required_requirement_ids", "requirements"} or payload.get("schema_version") != SCHEMA:
        errors.append("traceability must use the exact RC.4 schema")
    requirements = payload.get("requirements")
    required = payload.get("required_requirement_ids")
    if not isinstance(requirements, list) or not isinstance(required, list):
        return {"status": "invalid", "coverage_percent": 0, "errors": [*errors, "requirements and required ids must be lists"]}
    requirements_text = (root / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "requirements.md").read_text(encoding="utf-8")
    decisions_text = (root / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "decisions.md").read_text(encoding="utf-8")
    implementation_text = (root / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "implementation.md").read_text(encoding="utf-8")
    source_requirements = source_requirement_ids(requirements_text)
    source_decisions = source_decision_ids(decisions_text)
    if len(source_requirements) != len(set(source_requirements)):
        errors.append("requirements.md contains duplicate RC.4 requirement ids")
    if sorted(source_requirements) != sorted(required):
        errors.append(
            f"requirements source/trace drift: source={sorted(source_requirements)}, trace={sorted(required)}"
        )
    observed: list[str] = []
    decisions: set[str] = set()
    declarations: set[str] = set()
    complete: set[str] = set()
    for item in requirements:
        if not isinstance(item, dict) or set(item) != {"id", "decisions", "implementation", "tests"}:
            errors.append("every requirement must use the exact id/decisions/implementation/tests schema")
            continue
        requirement_id = item["id"]
        observed.append(requirement_id)
        if not all(isinstance(item[field], list) and item[field] and all(isinstance(value, str) and value for value in item[field]) for field in ("decisions", "implementation", "tests")):
            errors.append(f"{requirement_id}: decisions, implementation, and tests must be non-empty string lists")
            continue
        decisions.update(item["decisions"])
        requirement_complete = True
        for declaration in item["implementation"]:
            declarations.add(declaration)
            path = root / declaration.rstrip("/")
            if not path.exists():
                errors.append(f"{requirement_id}: implementation path is missing: {declaration}")
                requirement_complete = False
        for reference in item["tests"]:
            path_text, separator, symbol = reference.partition("::")
            declarations.add(path_text)
            path = root / path_text
            if not separator or not path.is_file():
                errors.append(f"{requirement_id}: invalid test reference: {reference}")
                requirement_complete = False
                continue
            symbols = python_test_symbols(path) if path.suffix == ".py" else json_case_ids(path) if path.suffix == ".json" else set()
            if symbol not in symbols:
                errors.append(f"{requirement_id}: test symbol is missing: {reference}")
                requirement_complete = False
        if requirement_complete:
            complete.add(requirement_id)
    if len(observed) != len(set(observed)):
        errors.append("requirement ids must be unique")
    if sorted(observed) != sorted(required):
        errors.append(f"required/observed requirement drift: required={sorted(required)}, observed={sorted(observed)}")
    expected_decisions = set(source_decisions)
    if expected_decisions != {f"D{index}" for index in range(1, 15)}:
        errors.append(f"decisions.md D1-D14 source drift: {sorted(expected_decisions)}")
    implementation_decisions = implementation_decision_ids(implementation_text)
    if implementation_decisions != expected_decisions:
        errors.append(
            f"implementation decision drift: missing={sorted(expected_decisions - implementation_decisions)}, extra={sorted(implementation_decisions - expected_decisions)}"
        )
    if decisions != expected_decisions:
        errors.append(f"decision coverage drift: missing={sorted(expected_decisions - decisions)}, extra={sorted(decisions - expected_decisions)}")
    changed: list[str] = []
    uncovered: list[str] = []
    if check_worktree or check_event:
        try:
            if check_event:
                event_name = os.environ.get("GITHUB_EVENT_NAME", "")
                event_file = os.environ.get("GITHUB_EVENT_PATH")
                if not event_file:
                    raise ValueError("GITHUB_EVENT_PATH is unavailable")
                changed = event_changed_paths(root, event_name, Path(event_file))
            else:
                changed = worktree_changed_paths(root)
            uncovered = [path for path in changed if not any(matches(path, declaration) for declaration in declarations)]
            if uncovered:
                errors.append(f"changed paths lack RC.4 ownership: {uncovered}")
        except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            errors.append(f"cannot enumerate changed paths: {exc}")
    coverage = 100 if required and set(required) == complete else round(100 * len(complete) / max(1, len(required)), 2)
    return {
        "status": "valid" if not errors and coverage == 100 else "invalid",
        "schema_version": SCHEMA,
        "coverage_percent": coverage,
        "requirements": len(required),
        "decisions_covered": len(decisions),
        "changed_paths_checked": len(changed),
        "uncovered_changed_paths": uncovered,
        "errors": errors,
        "claim_limit": "static-bidirectional-traceability-not-runtime-correctness",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--check-worktree", action="store_true")
    source.add_argument("--check-event", action="store_true")
    args = parser.parse_args()
    result = validate(
        args.root.resolve(),
        check_worktree=args.check_worktree,
        check_event=args.check_event,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
