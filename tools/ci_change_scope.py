#!/usr/bin/env python3
"""Decide whether a change needs the cross-platform compatibility matrix."""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Iterable


INVENTORY_SCHEMA = "dev-flow.compatibility-surfaces.v1"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = REPOSITORY_ROOT / "governance" / "compatibility-surfaces.json"
ZERO_SHA = "0" * 40


def load_patterns(path: Path = DEFAULT_INVENTORY) -> tuple[str, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != {"schema_version", "patterns"} or payload.get("schema_version") != INVENTORY_SCHEMA:
        raise ValueError("compatibility inventory must use the exact supported schema")
    patterns = payload.get("patterns")
    if (
        not isinstance(patterns, list)
        or not patterns
        or any(not isinstance(item, str) or not item.strip() for item in patterns)
        or len(patterns) != len(set(patterns))
    ):
        raise ValueError("compatibility inventory patterns must be unique non-empty strings")
    return tuple(patterns)


COMPATIBILITY_PATTERNS = load_patterns()


def normalize_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    return normalized[2:] if normalized.startswith("./") else normalized


def matches_pattern(path: str, pattern: str) -> bool:
    normalized = normalize_path(path)
    if pattern.endswith("/**"):
        return normalized.startswith(pattern[:-3] + "/")
    return fnmatch.fnmatchcase(normalized, pattern)


def requires_compatibility(
    paths: Iterable[str], *, patterns: Iterable[str] = COMPATIBILITY_PATTERNS
) -> tuple[bool, list[str]]:
    pattern_set = tuple(patterns)
    matched = sorted(
        {
            normalize_path(path)
            for path in paths
            if any(matches_pattern(path, pattern) for pattern in pattern_set)
        }
    )
    return bool(matched), matched


def git_paths(*args: str) -> list[str]:
    completed = subprocess.run(
        ["git", *args],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip() or completed.stdout.strip() or "git path query failed")
    return [line for line in completed.stdout.splitlines() if line]


def event_paths(event_name: str, event_path: Path) -> tuple[list[str], str]:
    payload = json.loads(event_path.read_text(encoding="utf-8"))
    if event_name == "pull_request":
        base = payload["pull_request"]["base"]["sha"]
        head = payload["pull_request"]["head"]["sha"]
        return git_paths("diff", "--name-only", "--diff-filter=ACMRDTUXB", f"{base}...{head}"), f"{base}...{head}"
    if event_name == "push":
        base = payload.get("before")
        head = payload.get("after")
        if not isinstance(head, str) or not head:
            raise ValueError("push event does not contain an after SHA")
        if not isinstance(base, str) or not base or base == ZERO_SHA:
            return git_paths("ls-tree", "-r", "--name-only", head), head
        return git_paths("diff", "--name-only", "--diff-filter=ACMRDTUXB", base, head), f"{base}..{head}"
    raise ValueError(f"unsupported GitHub event: {event_name or '<missing>'}")


def write_github_output(required: bool) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"compatibility={'true' if required else 'false'}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", action="append", default=[], help="Evaluate an explicit changed path")
    parser.add_argument("--event-name", default=os.environ.get("GITHUB_EVENT_NAME"))
    parser.add_argument("--event-path", type=Path, default=os.environ.get("GITHUB_EVENT_PATH"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.path:
            paths, source = args.path, "explicit-paths"
        elif args.event_name and args.event_path:
            paths, source = event_paths(args.event_name, args.event_path)
        else:
            raise ValueError("provide --path or GitHub event environment variables")
        required, matched = requires_compatibility(paths)
    except (OSError, RuntimeError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ci_change_scope: {exc}", file=sys.stderr)
        return 2
    write_github_output(required)
    print(
        json.dumps(
            {
                "compatibility": required,
                "source": source,
                "changed_paths": sorted(set(paths)),
                "matched_paths": matched,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
