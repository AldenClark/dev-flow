#!/usr/bin/env python3
"""Supported Dev Flow 2.0 command boundary.

The implementation module still contains packet-era migration residue. This
wrapper builds only supported commands; direct legacy parser use remains an
internal regression surface until a separately bounded removal.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Iterable

import agent_dispatch
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


def route_agent_command(args: argparse.Namespace) -> int:
    """Resolve a route against an optional observed host model/effort inventory."""
    try:
        host_capabilities = None
        if args.host_capability is not None:
            host_capabilities = []
            for value in args.host_capability:
                if ":" not in value:
                    raise agent_dispatch.DispatchContractError("host capability must be MODEL:EFFORT")
                model, effort = value.rsplit(":", 1)
                host_capabilities.append((model, effort))
        result = agent_dispatch.route_agent(
            role=args.role,
            workload=args.workload,
            risks=args.risk,
            signals=args.signal,
            requested_profile=args.profile,
            acknowledge_exception=args.acknowledge_exception,
            acknowledge_downgrade=args.acknowledge_downgrade,
            registry_path=args.registry,
            task_structure=args.task_structure,
            parallel_units=args.parallel_units,
            tool_density=args.tool_density,
            host_capabilities=host_capabilities,
        )
    except ValueError as exc:
        return dev_flow.emit({"status": "invalid", "errors": [str(exc)]}, 2)
    return dev_flow.emit(result, 2 if result["status"] == "capability_limit" else 0)


def build_parser() -> argparse.ArgumentParser:
    parser = dev_flow.build_parser(supported_only=True)
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction) and action.dest == "command"
    )
    if set(subparsers.choices) != PUBLIC_COMMAND_SET:
        raise RuntimeError("supported parser inventory differs from public command contract")
    agent_route = subparsers.choices["route-agent"]
    agent_route.add_argument(
        "--host-capability",
        action="append",
        metavar="MODEL:EFFORT",
        help="Observed dispatch-host model/effort pair; repeat for the host inventory. Omit only when the host is not yet checked.",
    )
    agent_route.set_defaults(func=route_agent_command)
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
