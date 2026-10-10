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

    def test_deterministic_routing_cases(self) -> None:
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

    def test_host_inventory_controls_dispatch_readiness(self) -> None:
        base = ("--role", "dev-flow-worker", "--workload", "bounded-change")
        unchecked = json.loads(run_route(*base).stdout)
        available = json.loads(run_route(*base, "--host-capability", "gpt-6-luna:high").stdout)
        limited = json.loads(run_route(*base, "--host-capability", "gpt-6-luna:medium").stdout)
        self.assertFalse(unchecked["dispatch_ready"])
        self.assertFalse(unchecked["delegate"])
        self.assertTrue(available["dispatch_ready"])
        self.assertTrue(available["delegate"])
        self.assertFalse(limited["dispatch_ready"])
        self.assertFalse(limited["delegate"])

    def test_future_inventory_entries_do_not_block_supported_selection(self) -> None:
        result = run_route(
            "--role", "dev-flow-blue-reviewer", "--workload", "routine-review",
            "--host-capability", "gpt-6.1-sol:medium",
            "--host-capability", "gpt-6.1-sol:ultra",
            "--host-capability", "future-model:future-effort",
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["dispatch_ready"])
        self.assertEqual(payload["requested_reasoning_effort"], "medium")
        inventory = payload["host_capability"]["unsupported_inventory"]
        self.assertEqual(
            {(item["model"], item["reasoning_effort"]) for item in inventory},
            {("gpt-6.1-sol", "ultra"), ("future-model", "future-effort")},
        )
        self.assertEqual(payload["host_capability"]["provenance"], "caller-reported host inventory")

    def test_future_inventory_only_is_not_selection_support(self) -> None:
        result = run_route(
            "--role", "dev-flow-blue-reviewer", "--workload", "routine-review",
            "--host-capability", "gpt-6.1-sol:ultra",
            "--host-capability", "future-model:medium",
        )
        self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["dispatch_ready"])
        self.assertIsNone(payload["host_capability"]["suggested_profile"])
        unsupported_selection = run_route(
            "--role", "dev-flow-blue-reviewer", "--workload", "routine-review",
            "--profile", "ultra", "--host-capability", "gpt-6.1-sol:ultra",
        )
        self.assertEqual(unsupported_selection.returncode, 2)
        self.assertIn("unknown profile", unsupported_selection.stdout)

    def test_malformed_inventory_tokens_are_rejected(self) -> None:
        for value in ("gpt-6.1-sol", "gpt-6.1-sol:", ":medium", " :medium", "gpt-6.1-sol: medium", "a:b:c"):
            with self.subTest(value=value):
                result = run_route(
                    "--role", "dev-flow-blue-reviewer", "--workload", "routine-review",
                    "--host-capability", "gpt-6.1-sol:medium", "--host-capability", value,
                )
                self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
                self.assertEqual(json.loads(result.stdout)["status"], "invalid")

    def test_total_independent_units_can_exceed_simultaneous_slots(self) -> None:
        result = run_route(
            "--role", "dev-flow-worker", "--workload", "bounded-change",
            "--parallel-units", "29", "--host-capability", "gpt-6-luna:high",
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["dispatch_precondition"]["parallel_units"], 29)
        self.assertTrue(payload["dispatch_ready"])
        self.assertNotIn("active_children", payload["dispatch_precondition"])
        for value in ("0", "-1"):
            with self.subTest(value=value):
                invalid = run_route(
                    "--role", "dev-flow-worker", "--workload", "bounded-change",
                    "--parallel-units", value,
                )
                self.assertEqual(invalid.returncode, 2)

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

    def test_current_sol_host_is_required_without_previous_sol_fallback(self) -> None:
        for workload, profile, effort in (
            ("routine-review", "P4", "medium"),
            ("high-risk-review", "P4", "medium"),
            ("high-risk-review", "P5", "xhigh"),
        ):
            with self.subTest(profile=profile):
                base = ("--role", "dev-flow-blue-reviewer", "--workload", workload)
                if profile == "P5":
                    base += ("--signal", "deep-unresolved")
                current = run_route(*base, "--host-capability", f"gpt-6.1-sol:{effort}")
                self.assertEqual(current.returncode, 0, current.stderr or current.stdout)
                result = json.loads(current.stdout)
                self.assertEqual(result["selected_profile"], profile)
                self.assertEqual(result["requested_model"], "gpt-6.1-sol")
                self.assertTrue(result["delegate"])
                self.assertTrue(result["dispatch_ready"])

                previous = run_route(*base, "--host-capability", f"gpt-6-sol:{effort}")
                self.assertEqual(previous.returncode, 2, previous.stderr or previous.stdout)
                limited = json.loads(previous.stdout)
                self.assertEqual(limited["status"], "capability_limit")
                self.assertEqual(limited["requested_model"], "gpt-6.1-sol")
                self.assertFalse(limited["delegate"])
                self.assertFalse(limited["dispatch_ready"])
                self.assertIsNone(limited["host_capability"]["suggested_profile"])

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
            "--signal",
            "deep-unresolved",
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
    def test_inventory_types_and_total_types_remain_strict(self) -> None:
        base = {"role": "dev-flow-worker", "workload": "bounded-change"}
        for inventory in ([("gpt-6-luna", None)], [(None, "high")], [("gpt-6-luna", [])], [["gpt-6-luna", "high"]], "gpt-6-luna:high", 4):
            with self.subTest(inventory=inventory), self.assertRaises(agent_dispatch.DispatchContractError):
                agent_dispatch.route_agent(**base, host_capabilities=inventory)
        for value in (True, 1.5, "9", None, 0, -1):
            with self.subTest(value=value), self.assertRaises(agent_dispatch.DispatchContractError):
                agent_dispatch.route_agent(**base, parallel_units=value)
        with self.assertRaises(agent_dispatch.DispatchContractError):
            agent_dispatch.route_agent(**base, task_structure="sequential", host_capabilities=[("gpt-6-luna", "")])

    def test_readme_dispatch_summary_matches_registry(self) -> None:
        registry = agent_dispatch.load_registry(REGISTRY)
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        summary = next(line for line in readme.splitlines() if line.startswith("子任务模型以"))
        models = {
            name: f"{details['model'].rsplit('-', 1)[0].upper()} {details['model'].rsplit('-', 1)[1].capitalize()}"
            for name, details in registry["runtime"]["capabilities"].items()
        }
        for profile in registry["profiles"]:
            expected = f"{profile['id']}={models[profile['capability']]} {profile['reasoning_effort']}"
            with self.subTest(profile=profile["id"]):
                self.assertIn(expected, summary)

    def test_registry_is_exact_and_profiles_are_orthogonal(self) -> None:
        registry = agent_dispatch.load_registry(REGISTRY)
        profiles = {item["id"]: item for item in registry["profiles"]}
        self.assertEqual(set(profiles), {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "PX"})
        self.assertEqual((profiles["P2"]["capability"], profiles["P2"]["reasoning_effort"]), ("E", "high"))
        self.assertEqual((profiles["P3"]["capability"], profiles["P3"]["reasoning_effort"]), ("E", "xhigh"))
        self.assertEqual((profiles["P4"]["capability"], profiles["P4"]["reasoning_effort"]), ("B", "medium"))
        self.assertEqual((profiles["P5"]["capability"], profiles["P5"]["reasoning_effort"]), ("B", "xhigh"))
        self.assertEqual((profiles["P6"]["capability"], profiles["P6"]["reasoning_effort"]), ("F", "xhigh"))
        self.assertEqual(
            {capability["model"] for capability in registry["runtime"]["capabilities"].values()},
            {"gpt-6-luna", "gpt-6.1-sol", "gpt-6-astra"},
        )
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

        dangling_compound = json.loads(json.dumps(baseline))
        dangling_compound["upgrade_rules"][-2]["all_signals"].append("unknown-signal")
        mutations.append(dangling_compound)

        duplicate_compound = json.loads(json.dumps(baseline))
        duplicate_compound["upgrade_rules"][-2]["all_signals"].append(
            duplicate_compound["upgrade_rules"][-2]["all_signals"][0]
        )
        mutations.append(duplicate_compound)

        invalid_minimum = json.loads(json.dumps(baseline))
        invalid_minimum["upgrade_rules"][0]["minimum_profile"] = "PX"
        mutations.append(invalid_minimum)

        risk_promotion = json.loads(json.dumps(baseline))
        risk_promotion["upgrade_rules"][0]["any_risk"] = ["ffi"]
        mutations.append(risk_promotion)

        legacy_model = json.loads(json.dumps(baseline))
        legacy_model["runtime"]["capabilities"]["E"]["model"] = "gpt-5.6-luna"
        mutations.append(legacy_model)

        previous_sol = json.loads(json.dumps(baseline))
        previous_sol["runtime"]["capabilities"]["B"]["model"] = "gpt-6-sol"
        mutations.append(previous_sol)

        swapped_profiles = json.loads(json.dumps(baseline))
        swapped_profiles["profiles"][0]["capability"] = "F"
        swapped_profiles["profiles"][0]["reasoning_effort"] = "low"
        mutations.append(swapped_profiles)

        for index, payload in enumerate(mutations):
            with self.subTest(mutation=index), tempfile.TemporaryDirectory() as temp:
                path = Path(temp) / "registry.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(agent_dispatch.DispatchContractError):
                    agent_dispatch.load_registry(path)

    def test_compound_p6_negative_control_detects_missing_boundary(self) -> None:
        baseline = agent_dispatch.route_agent(
            role="dev-flow-worker",
            workload="bounded-change",
            signals=["deep-unresolved", "interacting-unknowns"],
        )
        self.assertEqual(baseline["selected_profile"], "P5")
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        case = next(rule for rule in registry["upgrade_rules"] if rule["id"] == "compound-frontier-reasoning")
        case["all_signals"].remove("cross-boundary-impact")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            path.write_text(json.dumps(registry), encoding="utf-8")
            result = agent_dispatch.route_agent(
                role="dev-flow-worker",
                workload="bounded-change",
                signals=["deep-unresolved", "interacting-unknowns"],
                registry_path=path,
            )
        self.assertEqual(result["selected_profile"], "P6")

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


class AgentCalibrationTests(unittest.TestCase):
    def test_single_uncertainty_stays_at_ordinary_judgment(self) -> None:
        for signal in ("oracle-challenge", "nondeterminism", "conflicting-evidence"):
            with self.subTest(signal=signal):
                payload = json.loads(run_route(
                    "--role", "dev-flow-explorer", "--workload", "causal-debugging",
                    "--signal", signal, "--host-capability", "gpt-6.1-sol:medium",
                ).stdout)
                self.assertEqual(payload["selected_profile"], "P4")
                self.assertTrue(payload["dispatch_ready"])

    def test_cross_component_and_risk_review_do_not_imply_deep_reasoning(self) -> None:
        for role, workload in (
            ("dev-flow-worker", "cross-component-change"),
            ("dev-flow-red-reviewer", "high-risk-review"),
        ):
            with self.subTest(workload=workload):
                payload = json.loads(run_route(
                    "--role", role, "--workload", workload,
                    "--risk", "security", "--risk", "data-deletion",
                    "--signal", "irreversible", "--signal", "high-risk-acceptance",
                ).stdout)
                self.assertEqual(payload["selected_profile"], "P4")
                self.assertEqual(payload["risks"], ["data-deletion", "security"])

    def test_adaptive_verification_uses_judgment_not_exact_command_profile(self) -> None:
        result = run_route(
            "--role", "dev-flow-test-runner", "--workload", "adaptive-verification",
            "--risk", "device", "--host-capability", "gpt-6.1-sol:medium",
        )
        self.assertEqual(result.returncode, 0, result.stdout or result.stderr)
        self.assertEqual(json.loads(result.stdout)["selected_profile"], "P4")

    def test_explicit_high_promotion_requires_caller_reason_not_user_approval(self) -> None:
        base = ("--role", "dev-flow-worker", "--workload", "bounded-change", "--profile", "P5")
        missing = run_route(*base)
        self.assertEqual(missing.returncode, 2)
        self.assertIn("--selection-reason", missing.stdout)
        reason = "Two valid recovery authorities disagree on ownership after the observed crash."
        explained = run_route(*base, "--selection-reason", reason,
                              "--host-capability", "gpt-6.1-sol:xhigh")
        self.assertEqual(explained.returncode, 0, explained.stdout or explained.stderr)
        payload = json.loads(explained.stdout)
        self.assertEqual((payload["policy_profile"], payload["selected_profile"]), ("P2", "P5"))
        self.assertTrue(payload["dispatch_ready"])
        self.assertEqual(payload["upgrade_reasons"][-1]["selection_reason"], reason)

    def test_complex_contract_keeps_depth_but_settled_followup_deescalates(self) -> None:
        complex_args = ("--role", "dev-flow-worker", "--workload", "cross-component-change",
                        "--signal", "ambiguity", "--signal", "interacting-unknowns",
                        "--signal", "cross-boundary-impact")
        self.assertEqual(json.loads(run_route(*complex_args).stdout)["selected_profile"], "P5")
        settled = run_route("--role", "dev-flow-worker", "--workload", "bounded-change",
                            "--signal", "confirmed-semantics", "--signal", "deterministic-oracle")
        self.assertEqual(json.loads(settled.stdout)["selected_profile"], "P2")
        command = run_route("--role", "dev-flow-test-runner", "--workload", "exact-verification")
        self.assertEqual(json.loads(command.stdout)["selected_profile"], "P0")

    def test_disputed_oracle_and_deep_reasoning_are_not_capped(self) -> None:
        for signals, expected in (
            (["conflicting-evidence", "oracle-challenge"], "P5"),
            (["deep-unresolved"], "P5"),
            (["failed-sol-discrimination"], "P5"),
            (["ambiguity", "interacting-unknowns", "high-risk-acceptance"], "P5"),
            (["deep-unresolved", "interacting-unknowns", "cross-boundary-impact"], "P6"),
        ):
            with self.subTest(signals=signals):
                args = ["--role", "dev-flow-worker", "--workload", "bounded-change"]
                for signal in signals:
                    args.extend(("--signal", signal))
                self.assertEqual(json.loads(run_route(*args).stdout)["selected_profile"], expected)

    def test_selection_reason_does_not_bypass_host_or_authority_boundaries(self) -> None:
        base = ("--role", "dev-flow-worker", "--workload", "bounded-change", "--profile", "P6")
        self.assertEqual(run_route(*base).returncode, 2)
        explained = run_route(*base, "--selection-reason", "Interacting unresolved recovery authorities.",
                              "--host-capability", "gpt-6.1-sol:medium")
        payload = json.loads(explained.stdout)
        self.assertEqual(explained.returncode, 2)
        self.assertEqual(payload["status"], "capability_limit")
        self.assertFalse(payload["dispatch_ready"])
        for flags in (
            ("--role", "root", "--workload", "root-decision"),
            ("--role", "dev-flow-worker", "--workload", "bounded-change", "--task-structure", "coupled"),
        ):
            with self.subTest(flags=flags):
                self.assertEqual(run_route(*flags, "--profile", "P5",
                                          "--selection-reason", "Unresolved causes.").returncode, 2)

    def test_matching_policy_and_ordinary_profiles_need_no_new_explanation(self) -> None:
        for profile, signals in (("P4", []), ("P5", ["deep-unresolved"])):
            args = ["--role", "dev-flow-blue-reviewer", "--workload", "routine-review",
                    "--profile", profile]
            for signal in signals:
                args += ["--signal", signal]
            with self.subTest(profile=profile):
                self.assertEqual(run_route(*args).returncode, 0)

    def test_selection_reason_contract_rejects_empty_or_unbound_values(self) -> None:
        base = {"role": "dev-flow-worker", "workload": "bounded-change", "requested_profile": "P5"}
        for reason in ("", "  ", True, 4, [], "x" * 1001):
            with self.subTest(reason=type(reason).__name__), self.assertRaises(agent_dispatch.DispatchContractError):
                agent_dispatch.route_agent(**base, selection_reason=reason)
        with self.assertRaises(agent_dispatch.DispatchContractError):
            agent_dispatch.route_agent(role="dev-flow-worker", workload="bounded-change",
                                       selection_reason="No explicit choice.")

    def test_single_signal_negative_control_detects_blanket_promotion(self) -> None:
        registry = json.loads(REGISTRY.read_text())
        ordinary = next(rule for rule in registry["upgrade_rules"] if rule["id"] == "ordinary-judgment")
        ordinary["minimum_profile"] = "P5"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "registry.json"
            path.write_text(json.dumps(registry))
            result = agent_dispatch.route_agent(
                role="dev-flow-explorer", workload="causal-debugging",
                signals=["nondeterminism"], registry_path=path,
            )
        self.assertNotEqual(result["selected_profile"], "P4")
        self.assertEqual(result["selected_profile"], "P5")


if __name__ == "__main__":
    unittest.main()
