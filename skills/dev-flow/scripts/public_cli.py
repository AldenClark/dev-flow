#!/usr/bin/env python3
"""Supported Dev Flow 2.0 command boundary.

The implementation module still contains packet-era migration residue. This
wrapper deliberately exposes only commands with an RC.5 support contract.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

import dev_flow


PUBLIC_COMMANDS = (
    "preflight",
    "init-workstream",
    "validate-knowledge",
    "validate-profile",
    "resolve-profiles",
    "validate-methods",
    "route-task",
    "check-workstream",
    "resource-lease",
    "resource-preflight",
    "route-agent",
    "flow-metrics",
    "doctor",
    "outcomes",
    "check",
    "install-runtime",
    "uninstall-runtime",
)
PUBLIC_COMMAND_SET = frozenset(PUBLIC_COMMANDS)
INTERNAL_COMMANDS = frozenset(
    {
        "init-packet",
        "validate-packet",
        "transition",
        "record-checkpoint",
        "resume-packet",
        "bind-knowledge",
        "record-iteration",
        "record-approval",
        "record-ambiguity",
        "resolve-ambiguity",
        "audit-preferences",
        "assess-context",
        "select-methods",
        "record-methods",
        "archive-packet",
        "deactivate-packet",
    }
)


def build_parser() -> argparse.ArgumentParser:
    parser = dev_flow.build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction) and action.dest == "command"
    )
    for command in tuple(subparsers.choices):
        if command not in PUBLIC_COMMAND_SET:
            del subparsers.choices[command]
    subparsers._choices_actions = [
        action for action in subparsers._choices_actions if action.dest in PUBLIC_COMMAND_SET
    ]
    parser.description = "Dev Flow 2.0 supported personal repository-engineering commands"
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    if raw_argv and raw_argv[0] in INTERNAL_COMMANDS:
        return dev_flow.emit(
            {
                "status": "unsupported",
                "command": raw_argv[0],
                "errors": [
                    "packet-era command is internal unsupported residue; use a repository workstream or a supported 2.0 command"
                ],
                "supported_commands": list(PUBLIC_COMMANDS),
            },
            2,
        )
    normalized_argv, aliases_used, invalid = dev_flow.preprocess_route_argv(raw_argv)
    if invalid is not None:
        return dev_flow.emit(invalid, 2)
    parser = build_parser()
    args = parser.parse_args(normalized_argv)
    if args.command == "route-task":
        args.intent_alias_input = aliases_used.get("--intent")
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
