#!/usr/bin/env python3
"""Deterministic black-box and white-box agent dispatch tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
FLOW = SCRIPTS / "dev-flow.py"
CASES = ROOT / "evals" / "agent-dispatch-routing-cases.json"
REGISTRY = ROOT / "skills" / "dev-flow" / "references" / "agent-dispatch-profiles.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import agent_dispatch  # noqa: E402


def run_route(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(FLOW), "route-agent", *args],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


class AgentDispatchBlackBoxTests(unittest.TestCase):
    def test_risk_help_lists_canonical_tokens_and_rejects_unknown_values(self) -> None:
        help_result = run_route("--help")
        self.assertEqual(help_result.returncode, 0, help_result.stderr or help_result.stdout)
        self.assertIn("concurrency", help_result.stdout)
        self.assertIn("security", help_result.stdout)
        invalid = run_route(
            "--role", "dev-flow-worker", "--workload", "bounded-change", "--risk", "invented-risk"
        )
        self.assertEqual(invalid.returncode, 2)
        self.assertIn("invalid choice", invalid.stderr)

    def test_frozen_routing_cases(self) -> None:
        catalog = json.loads(CASES.read_text(encoding="utf-8"))
        self.assertEqual(catalog["schema_version"], "1.0")
        observed_ids: set[str] = set()
        for case in catalog["cases"]:
            with self.subTest(case=case["id"]):
                self.assertNotIn(case["id"], observed_ids)
                observed_ids.add(case["id"])
                completed = run_route(*case["args"])
                self.assertEqual(completed.returncode, case["exit"], completed.stderr or completed.stdout)
                payload = json.loads(completed.stdout)
                for key, expected in case["expected"].items():
                    self.assertEqual(payload.get(key), expected, f"{case['id']}:{key}")
                if completed.returncode == 0 and payload["delegate"]:
                    self.assertEqual(payload["fork_turns"], "none")
                    self.assertIn(payload["selection_source"], {"policy", "explicit-profile"})
                    self.assertIn("current task result", payload["runtime_fallback"])
                    self.assertNotIn("record", payload["runtime_fallback"])

    def test_same_request_is_byte_stable(self) -> None:
        args = (
            "--role",
            "dev-flow-worker",
            "--workload",
            "bounded-change",
            "--signal",
            "large-context",
            "--signal",
            "oracle-challenge",
        )
        first = run_route(*args)
        second = run_route(*args)
        self.assertEqual((first.returncode, first.stdout), (second.returncode, second.stdout))

    def test_acknowledged_exception_and_downgrade_are_explicit(self) -> None:
        exceptional = run_route(
            "--role",
            "dev-flow-worker",
            "--workload",
            "bounded-change",
            "--profile",
            "PX",
            "--acknowledge-exception",
        )
        self.assertEqual(exceptional.returncode, 0, exceptional.stderr or exceptional.stdout)
        exceptional_payload = json.loads(exceptional.stdout)
        self.assertEqual(exceptional_payload["selected_profile"], "PX")
        self.assertEqual(exceptional_payload["selection_source"], "explicit-profile")

        downgraded = run_route(
            "--role",
            "dev-flow-worker",
            "--workload",
            "bounded-change",
            "--risk",
            "security",
            "--profile",
            "P0",
            "--acknowledge-downgrade",
        )
        self.assertEqual(downgraded.returncode, 0, downgraded.stderr or downgraded.stdout)
        downgraded_payload = json.loads(downgraded.stdout)
        self.assertEqual(downgraded_payload["policy_profile"], "P5")
        self.assertEqual(downgraded_payload["selected_profile"], "P0")

    def test_sequential_and_tool_dense_work_does_not_auto_multiply_agents(self) -> None:
        sequential = run_route(
            "--role",
            "dev-flow-worker",
            "--workload",
            "broad-multi-step",
            "--task-structure",
            "sequential",
            "--parallel-units",
            "4",
            "--tool-density",
            "high",
        )
        self.assertEqual(sequential.returncode, 0, sequential.stderr or sequential.stdout)
        payload = json.loads(sequential.stdout)
        self.assertFalse(payload["delegate"])
        self.assertEqual(payload["selection_source"], "root-sequential")
        self.assertIsNone(payload["selected_profile"])
        self.assertIn("do not authorize agent multiplication", payload["upgrade_reasons"][0]["reason"])

        low = json.loads(run_route("--role", "dev-flow-worker", "--workload", "bounded-change").stdout)
        high = json.loads(
            run_route(
                "--role",
                "dev-flow-worker",
                "--workload",
                "bounded-change",
                "--tool-density",
                "high",
            ).stdout
        )
        self.assertEqual(low["selected_profile"], high["selected_profile"])


class AgentDispatchWhiteBoxTests(unittest.TestCase):
    def test_registry_is_exact_and_profiles_are_orthogonal(self) -> None:
        registry = agent_dispatch.load_registry(REGISTRY)
        profiles = {item["id"]: item for item in registry["profiles"]}
        self.assertEqual(set(profiles), {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "PX"})
        self.assertEqual((profiles["P2"]["capability"], profiles["P2"]["reasoning_effort"]), ("E", "high"))
        self.assertEqual((profiles["P3"]["capability"], profiles["P3"]["reasoning_effort"]), ("B", "medium"))
        self.assertEqual((profiles["P4"]["capability"], profiles["P4"]["reasoning_effort"]), ("B", "high"))
        self.assertTrue(profiles["PX"]["exception"])
        self.assertFalse(any(profiles[name]["exception"] for name in profiles if name != "PX"))

    def test_registry_rejects_dangling_and_duplicate_contracts(self) -> None:
        baseline = json.loads(REGISTRY.read_text(encoding="utf-8"))
        mutations = []

        unknown_profile = json.loads(json.dumps(baseline))
        unknown_profile["workloads"][0]["default_profile"] = "P404"
        mutations.append(unknown_profile)

        duplicate_role = json.loads(json.dumps(baseline))
        duplicate_role["roles"].append("root")
        mutations.append(duplicate_role)

        dangling_signal = json.loads(json.dumps(baseline))
        dangling_signal["upgrade_rules"][0]["any_signal"].append("unknown-signal")
        mutations.append(dangling_signal)

        duplicate_condition = json.loads(json.dumps(baseline))
        duplicate_condition["upgrade_rules"][0]["any_signal"].append(
            duplicate_condition["upgrade_rules"][0]["any_signal"][0]
        )
        mutations.append(duplicate_condition)

        dangling_suppression = json.loads(json.dumps(baseline))
        dangling_suppression["upgrade_rules"][-2]["unless_all_signals"].append("unknown-signal")
        mutations.append(dangling_suppression)

        duplicate_suppression = json.loads(json.dumps(baseline))
        duplicate_suppression["upgrade_rules"][-2]["unless_all_signals"].append(
            duplicate_suppression["upgrade_rules"][-2]["unless_all_signals"][0]
        )
        mutations.append(duplicate_suppression)

        for index, payload in enumerate(mutations):
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "registry.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(agent_dispatch.DispatchContractError):
                    agent_dispatch.load_registry(path)

    def test_role_configs_remain_model_neutral(self) -> None:
        role_root = ROOT / "skills" / "dev-flow" / "assets" / "agent-configs"
        for path in sorted(role_root.glob("*.toml")):
            with self.subTest(role=path.name):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("model =", text)
                self.assertNotIn("model_reasoning_effort", text)

    def test_role_configs_do_not_reintroduce_legacy_ceremony(self) -> None:
        role_root = ROOT / "skills" / "dev-flow" / "assets" / "agent-configs"
        forbidden = (
            "packet",
            "digest",
            "fingerprint",
            "AC/SC/VO",
            "resource lease",
            "frozen source",
            "frozen brief",
            "durable report",
        )
        for path in sorted(role_root.glob("*.toml")):
            with self.subTest(role=path.name):
                text = path.read_text(encoding="utf-8")
                for token in forbidden:
                    self.assertNotIn(token, text)

    def test_orchestration_routes_actual_dispatch_without_receipts(self) -> None:
        orchestration = (ROOT / "skills" / "dev-flow" / "references" / "multi-agent-v2-orchestration.md").read_text(encoding="utf-8")
        brief = (ROOT / "skills" / "dev-flow" / "templates" / "task-brief.md").read_text(encoding="utf-8")
        execution = (ROOT / "skills" / "dev-flow" / "templates" / "execution.md").read_text(encoding="utf-8")
        self.assertIn("route-agent", orchestration)
        self.assertIn("Use the returned model, reasoning effort, and fork request", orchestration)
        for token in ("requested_model", "requested_reasoning_effort", "effective_model", "fallback_reason"):
            self.assertNotIn(token, orchestration)
        for token in ("objective and expected outcome", "owned paths", "allowed verification", "expected return"):
            self.assertIn(token, orchestration)
        self.assertIn("A child final is a report", orchestration)

        # 1.x templates stay readable for existing packets but do not govern 2.0 delegation.
        self.assertIn("Dispatch profile", brief)
        self.assertIn("Dispatch profile/source", execution)


if __name__ == "__main__":
    unittest.main()
