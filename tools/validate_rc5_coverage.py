#!/usr/bin/env python3
"""Prove bidirectional RC.5 requirement/change/test traceability."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))

import validate_rc4_coverage as traceability_core  # noqa: E402


SCHEMA = "dev-flow.rc5.traceability.v1"


def validate(root: Path, *, check_worktree: bool, check_event: bool = False) -> dict[str, Any]:
    return traceability_core.validate_release(
        root,
        release_label="RC.5",
        trace_relative="governance/rc5-traceability.json",
        workstream_relative="docs/workstreams/dev-flow-2.0-rc.5",
        schema=SCHEMA,
        decision_count=8,
        check_worktree=check_worktree,
        check_event=check_event,
    )


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
