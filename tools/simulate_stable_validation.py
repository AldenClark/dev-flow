#!/usr/bin/env python3
"""Simulate Dev Flow's stable validation without publishing or calling a model."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Any


ACTIVE_POLICY_FILES = (
    "README.md",
    "docs/releasing.md",
    "docs/evaluation-suite.md",
    "docs/workstreams/dev-flow-2.0/design.md",
    "skills/delivery-readiness/SKILL.md",
    "skills/dev-flow-maintainer/references/maintenance-contract.md",
)
FORBIDDEN_RELEASE_RULES = (
    "| R4 model-semantic |",
    "complete repeated R4 is reserved for stable",
    "Complete repeated R4 is reserved for stable",
    "stable-release R4",
    "R4 still requires",
)
STATIC_METHODS = (
    "traceability-v-model",
    "change-impact-graph",
    "specification-by-example",
    "feature-interaction-analysis",
    "black-white-oracle-accounting",
    "assumption-mapping-premortem",
)
FUNCTIONAL_JOURNEYS = (
    "ordinary bounded bugfix",
    "material semantic change with requirement confirmation",
    "diagnose then fix then verify",
    "local Codex and unrelated MCP boundary",
    "continuation without inferred delivery authority",
)


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.fsmonitor=false", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git command failed"
        raise ValueError(detail[:512])
    return completed.stdout.strip()


def simulate(root: Path, baseline: str, current: str) -> dict[str, Any]:
    root = root.resolve(strict=True)
    if not (root / ".git").exists():
        raise ValueError("--root must be a Git working tree")
    baseline_commit = _git(root, "rev-parse", "--verify", f"{baseline}^{{commit}}")
    worktree_mode = current == "WORKTREE"
    current_ref = "HEAD" if worktree_mode else current
    current_commit = _git(root, "rev-parse", "--verify", f"{current_ref}^{{commit}}")
    diff_target = None if worktree_mode else current_commit
    diff_args = ("diff", "--name-only", "-z", baseline_commit)
    shortstat_args = ("diff", "--shortstat", baseline_commit)
    if diff_target is not None:
        diff_args = (*diff_args, diff_target)
        shortstat_args = (*shortstat_args, diff_target)
    names = [name for name in _git(root, *diff_args).split("\0") if name]
    untracked: list[str] = []
    if worktree_mode:
        untracked = [
            line
            for line in _git(root, "ls-files", "--others", "--exclude-standard", "-z").split("\0")
            if line
        ]
        names = sorted(set(names) | set(untracked))
    shortstat = _git(root, *shortstat_args)
    if untracked:
        shortstat = f"{shortstat}; {len(untracked)} untracked files" if shortstat else f"{len(untracked)} untracked files"
    commit_count = int(_git(root, "rev-list", "--count", f"{baseline_commit}..{current_commit}"))
    policy_errors: list[str] = []
    for relative in ACTIVE_POLICY_FILES:
        path = root / relative
        if not path.is_file():
            policy_errors.append(f"missing active policy file: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_RELEASE_RULES:
            if token.lower() in text.lower():
                policy_errors.append(f"{relative}: obsolete stable R4 rule: {token}")
    groups = {
        "runtime_and_guidance": [],
        "requirements_and_decisions": [],
        "verification": [],
        "release_and_tooling": [],
    }
    for name in names:
        if name.startswith(("skills/", "hooks/", "commands/")):
            groups["runtime_and_guidance"].append(name)
        elif "workstream" in name or name.startswith(("governance/", "methods/")):
            groups["requirements_and_decisions"].append(name)
        elif name.startswith("evals/") or "test" in name:
            groups["verification"].append(name)
        else:
            groups["release_and_tooling"].append(name)
    return {
        "status": "ready" if not policy_errors else "blocked",
        "schema_version": "dev-flow.stable-validation-simulation.v1",
        "mode": "simulation-only",
        "baseline": {"ref": baseline, "commit": baseline_commit},
        "candidate": {
            "ref": current,
            "commit": current_commit,
            "includes_worktree": worktree_mode,
            "untracked_files": len(untracked),
        },
        "delta": {
            "commits": commit_count,
            "changed_files": len(names),
            "shortstat": shortstat,
            "groups": {key: len(value) for key, value in groups.items()},
        },
        "semantic_review": {
            "scope": "every maintained requirement and behavior change since the previous public stable",
            "path_groups": groups,
            "checks": [
                "reconcile requirements, decisions, implementation, tests, and current documentation",
                "look for dropped, contradicted, or only partially implemented behavior",
                "consolidate all findings before repair instead of rerunning a broad gate after each fix",
            ],
        },
        "static_review": {
            "methods": list(STATIC_METHODS),
            "execution": "one consolidated pass, plus at most two risk-specific methods when the diff justifies them",
        },
        "functional_acceptance": {
            "journeys": list(FUNCTIONAL_JOURNEYS),
            "execution": "one bounded first attempt per journey; rerun only failed or newly affected journeys",
            "model_execution_in_this_simulation": False,
        },
        "deterministic_regression": "one complete local suite after focused repair checks pass",
        "policy_errors": policy_errors,
        "actions": {
            "model_calls": False,
            "commit": False,
            "tag": False,
            "push": False,
            "publication": False,
            "primary_install": False,
            "product_state_mutation": False,
        },
        "claim_limit": "process simulation and cumulative-delta inventory only; not a stable release or live functional-acceptance pass",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--baseline", default="v1.1.2")
    parser.add_argument("--current", default="WORKTREE", help="Git ref or WORKTREE (default)")
    args = parser.parse_args()
    try:
        result = simulate(args.root, args.baseline, args.current)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        result = {
            "status": "blocked",
            "schema_version": "dev-flow.stable-validation-simulation.v1",
            "errors": [str(exc)],
            "actions": {"model_calls": False, "publication": False},
        }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
