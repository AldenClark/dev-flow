#!/usr/bin/env python3
"""Static safety, syntax, link, identity, and route-drift scan for RC.4."""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


CURRENT_TRUTH_CONTRACT = {
    "docs/workstreams/dev-flow-2.0-rc.4/requirements.md": {
        "required": ("Current implementation and evidence status is owned by `progress.md`",),
        "forbidden": ("The current runner does not yet implement",),
    },
    "docs/workstreams/dev-flow-2.0-rc.4/implementation.md": {
        "required": ("Current execution evidence is owned by `progress.md`",),
        "forbidden": ("No RC.4 source behavior, test, host lease",),
    },
    "docs/workstreams/dev-flow-2.0-rc.4/progress.md": {
        "required": ("607/607 tests passed", "Independent implementation-byte review passed"),
        "forbidden": ("No model-semantic, independent-review, cross-platform lease",),
    },
}


def current_truth_findings(root: Path) -> list[str]:
    findings: list[str] = []
    for relative, contract in CURRENT_TRUTH_CONTRACT.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            findings.append(f"{relative}: current-truth document is unreadable: {exc}")
            continue
        for anchor in contract["required"]:
            if anchor not in text:
                findings.append(f"{relative}: current-truth anchor is missing: {anchor}")
        for stale in contract["forbidden"]:
            if stale in text:
                findings.append(f"{relative}: stale planning claim escaped into current truth: {stale}")
    return findings


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def scan(root: Path, *, check_event: bool = False) -> dict[str, Any]:
    errors: list[str] = []
    errors.extend(current_truth_findings(root))
    coverage = _load(root / "tools" / "validate_rc4_coverage.py", "rc4_static_coverage")
    try:
        if check_event:
            event_path = os.environ.get("GITHUB_EVENT_PATH")
            if not event_path:
                raise RuntimeError("GITHUB_EVENT_PATH is unavailable")
            changed = coverage.event_changed_paths(
                root, os.environ.get("GITHUB_EVENT_NAME", ""), Path(event_path)
            )
        else:
            changed = coverage.worktree_changed_paths(root)
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return {"status": "invalid", "errors": [str(exc)]}
    python_files = 0
    json_files = 0
    markdown_files = 0
    forbidden_calls = {"eval", "exec", "os.system", "subprocess.call"}
    for relative in changed:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_number, line in enumerate(text.splitlines(), 1):
            if line.rstrip() != line:
                errors.append(f"{relative}:{line_number}: trailing whitespace")
            if re.match(r"^(?:<<<<<<< |=======\s*$|>>>>>>> )", line):
                errors.append(f"{relative}:{line_number}: merge-conflict marker")
        if path.suffix == ".md" and re.search(r"\b(?:TODO|TBD|FIXME)\b", text):
            errors.append(f"{relative}: unresolved placeholder")
        if path.suffix == ".py":
            python_files += 1
            try:
                tree = ast.parse(text, filename=relative)
            except SyntaxError as exc:
                errors.append(f"{relative}:{exc.lineno}: Python syntax error: {exc.msg}")
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                name = ""
                if isinstance(node.func, ast.Name):
                    name = node.func.id
                elif isinstance(node.func, ast.Attribute) and isinstance(node.func.value, ast.Name):
                    name = f"{node.func.value.id}.{node.func.attr}"
                if name in forbidden_calls:
                    errors.append(f"{relative}:{node.lineno}: forbidden dynamic/shell call {name}")
                if name in {"subprocess.run", "subprocess.Popen"}:
                    for keyword in node.keywords:
                        if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            errors.append(f"{relative}:{node.lineno}: subprocess shell=True is forbidden")
                if name == "tempfile.mktemp":
                    errors.append(f"{relative}:{node.lineno}: insecure tempfile.mktemp is forbidden")
        elif path.suffix == ".json":
            json_files += 1
            try:
                json.loads(text)
            except json.JSONDecodeError as exc:
                errors.append(f"{relative}:{exc.lineno}: invalid JSON: {exc.msg}")
        elif path.suffix == ".md":
            markdown_files += 1
            for target in re.findall(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)", text):
                if "://" in target or target.startswith("/"):
                    continue
                if not (path.parent / target).resolve().exists():
                    errors.append(f"{relative}: broken local Markdown link {target}")

    scripts = root / "skills" / "dev-flow" / "scripts"
    sys.path.insert(0, str(scripts))
    dev_flow = _load(scripts / "dev_flow.py", "rc4_static_dev_flow")
    route_incremental = _load(scripts / "route_incremental.py", "rc4_static_route_incremental")
    parser = dev_flow.build_parser()
    route = next(action.choices["route-task"] for action in parser._actions if action.dest == "command")
    actual_route_inputs = {
        action.dest
        for action in route._actions
        if action.dest not in {"help", "compact", "previous_route"}
    }
    declared_route_inputs = set(route_incremental.ROUTE_BASIS_OPTION_DESTS)
    if actual_route_inputs != declared_route_inputs:
        errors.append(
            f"route-basis drift: missing={sorted(actual_route_inputs - declared_route_inputs)}, extra={sorted(declared_route_inputs - actual_route_inputs)}"
        )
    if declared_route_inputs != set(route_incremental.ROUTE_BASIS_OPTION_DIMENSIONS):
        errors.append("route-basis option/dimension table drift")
    invalid_dimensions = {
        dimension
        for dimensions in route_incremental.ROUTE_BASIS_OPTION_DIMENSIONS.values()
        for dimension in dimensions
        if dimension not in route_incremental.INVALIDATIONS
    }
    if invalid_dimensions:
        errors.append(f"route-basis table names unknown dimensions: {sorted(invalid_dimensions)}")

    required_guidance = {
        "skills/dev-flow/SKILL.md": ("--previous-route", "check-workstream"),
        "skills/dev-flow/references/core-lifecycle.md": ("Incremental route continuity", "structural-consistency"),
        "skills/verification/references/test-environments.md": ("resource-lease acquire", "resource-preflight"),
        "skills/test-system-engineering/SKILL.md": ("all six obligations", "negative control"),
    }
    for relative, anchors in required_guidance.items():
        guidance = (root / relative).read_text(encoding="utf-8")
        missing = [anchor for anchor in anchors if anchor not in guidance]
        if missing:
            errors.append(f"RC.4 workflow guidance drift in {relative}: missing {missing}")

    candidate_identity = _load(root / "evals" / "candidate_identity.py", "rc4_static_candidate_identity")
    dependencies = {
        path.relative_to(root.resolve()).as_posix()
        for path in candidate_identity.qualification_dependency_files(
            root,
            root / "evals" / "run_transition_trials.py",
            root / "evals" / "flow-transition-semantic-cases.json",
        )
    }
    if "skills/dev-flow/scripts/flow_metrics.py" not in dependencies:
        errors.append("qualification dependency closure omits flow_metrics.py")

    coverage_result = coverage.validate(
        root, check_worktree=not check_event, check_event=check_event
    )
    if coverage_result.get("status") != "valid":
        errors.extend(f"coverage: {error}" for error in coverage_result.get("errors", []))
    return {
        "status": "valid" if not errors else "invalid",
        "changed_paths": len(changed),
        "python_ast_files": python_files,
        "json_files": json_files,
        "markdown_files": markdown_files,
        "route_inputs_covered": len(actual_route_inputs),
        "qualification_dependency_files": len(dependencies),
        "traceability_coverage_percent": coverage_result.get("coverage_percent"),
        "drift_findings": len(errors),
        "errors": errors,
        "claim_limit": "static-scan-does-not-replace-runtime-or-cross-platform-evidence",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--check-event", action="store_true")
    args = parser.parse_args()
    result = scan(args.root.resolve(), check_event=args.check_event)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
