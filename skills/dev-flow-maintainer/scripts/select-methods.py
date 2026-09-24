#!/usr/bin/env python3
"""Ephemeral maintainer study of the methodology pool, separate from packet CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "skills" / "dev-flow" / "scripts"))

import methodology_system  # noqa: E402


METHOD_TASK_TYPES = {
    "research": "spike",
    "diagnose": "bugfix",
    "design": "routine",
    "change": "routine",
    "review": "read-only-audit",
    "delivery": "release-hotfix",
}
INTENT_ALIASES = {"research-audit": "review"}


def emit(payload: dict[str, object], code: int = 0) -> int:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def main() -> int:
    parser = argparse.ArgumentParser(description="Select a bounded, non-persisted maintainer method study")
    parser.add_argument("--phase", required=True)
    parser.add_argument("--intent", choices=sorted(set(METHOD_TASK_TYPES) | set(INTENT_ALIASES)), required=True)
    parser.add_argument("--method-task-type", help="Optional pool task shape for an explicit maintainer study")
    parser.add_argument("--risk", action="append", default=[])
    parser.add_argument("--signal", action="append", default=[])
    parser.add_argument("--available", action="append", default=[])
    parser.add_argument("--depth", choices=("starter", "deep", "formal"), default="starter")
    parser.add_argument("--max-methods", type=int)
    parser.add_argument("--registry", type=Path)
    parser.add_argument("--root", type=Path, help="Dev Flow methodology source repository, not the target project")
    args = parser.parse_args()

    registry_path = (args.registry or PLUGIN_ROOT / "governance" / "methodology-pool.json").resolve()
    repository_root = args.root.resolve() if args.root else PLUGIN_ROOT
    intent = INTENT_ALIASES.get(args.intent, args.intent)
    method_task_type = args.method_task_type or METHOD_TASK_TYPES[intent]
    try:
        payload = methodology_system.read_registry(registry_path)
        result = methodology_system.select_methods(
            payload,
            repository_root=repository_root,
            phase=args.phase,
            task_type=method_task_type,
            risks=args.risk,
            signals=args.signal,
            available=args.available,
            depth=args.depth,
            max_methods=args.max_methods,
        )
    except (OSError, ValueError, json.JSONDecodeError, methodology_system.MethodologyContractError) as exc:
        return emit({"status": "invalid", "registry": str(registry_path), "errors": [str(exc)]}, 2)
    result["request"]["intent"] = intent
    result["request"]["intent_source"] = (
        f"legacy-intent:{args.intent}" if args.intent in INTENT_ALIASES else "explicit-intent"
    )
    result["request"]["method_task_type"] = method_task_type
    result["registry"] = str(registry_path)
    return emit(result)


if __name__ == "__main__":
    raise SystemExit(main())
