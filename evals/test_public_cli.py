#!/usr/bin/env python3
"""Supported RC.5 CLI boundary tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
FLOW = SCRIPTS / "dev-flow.py"
LEGACY = SCRIPTS / "dev_flow.py"
SPEC = importlib.util.spec_from_file_location("public_cli", SCRIPTS / "public_cli.py")
assert SPEC is not None and SPEC.loader is not None
sys.path.insert(0, str(SCRIPTS))
PUBLIC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PUBLIC)


def run(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


class PublicCliTests(unittest.TestCase):
    def test_help_contains_exact_supported_inventory(self) -> None:
        parser = PUBLIC.build_parser()
        subparsers = next(action for action in parser._actions if action.dest == "command")
        self.assertEqual(set(subparsers.choices), set(PUBLIC.PUBLIC_COMMANDS))
        internal_parser = PUBLIC.dev_flow.build_parser()
        internal_subparsers = next(
            action for action in internal_parser._actions if action.dest == "command"
        )
        self.assertEqual(
            set(internal_subparsers.choices),
            set(PUBLIC.PUBLIC_COMMANDS) | set(PUBLIC.INTERNAL_COMMANDS),
        )
        help_result = run(FLOW, "--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr)
        for command in PUBLIC.INTERNAL_COMMANDS:
            self.assertNotIn(command, help_result.stdout)

    def test_packet_command_is_structurally_unsupported_but_internal_regression_remains(self) -> None:
        public = run(FLOW, "init-packet")
        self.assertEqual(public.returncode, 2)
        payload = json.loads(public.stdout)
        self.assertEqual(payload["status"], "unsupported")
        self.assertNotIn("init-packet", payload["supported_commands"])
        internal = run(LEGACY, "--help")
        self.assertEqual(internal.returncode, 0)
        self.assertIn("init-packet", internal.stdout)

    def test_supported_route_uses_compact_rc7_contract(self) -> None:
        result = run(FLOW, "route-task", "--intent", "change", "--compact")
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(set(payload["route_basis"]), {"schema", "router_semantics", "digest"})
        self.assertEqual(payload["route_basis"]["router_semantics"], "dev-flow.route-semantics.rc7.v1")
        self.assertEqual(set(payload["method"]), {"action", "status", "selected", "blocked"})

    def test_explain_is_the_explicit_full_form_and_conflicts_with_compact(self) -> None:
        default = run(FLOW, "route-task", "--intent", "change")
        explained = run(FLOW, "route-task", "--intent", "change", "--explain")
        conflict = run(
            FLOW, "route-task", "--intent", "change", "--compact", "--explain"
        )
        self.assertEqual(default.returncode, 0, default.stderr or default.stdout)
        self.assertEqual(explained.returncode, 0, explained.stderr or explained.stdout)
        self.assertEqual(json.loads(default.stdout), json.loads(explained.stdout))
        self.assertEqual(conflict.returncode, 2)
        self.assertIn("not allowed with argument", conflict.stderr)


if __name__ == "__main__":
    unittest.main()
