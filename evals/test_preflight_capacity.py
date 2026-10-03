#!/usr/bin/env python3
"""Public preflight capacity and capability provenance regressions."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"


class PreflightCapacityTests(unittest.TestCase):
    def run_preflight(
        self, *extra: str, version: str = "codex-cli 0.147.0",
        multi_agent: bool = True, configured_limit: int | None = 9,
    ) -> tuple[subprocess.CompletedProcess[str], dict]:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            features = root / "features.txt"
            features.write_text(f"multi_agent stable {str(multi_agent).lower()}\nhooks stable true\n", encoding="utf-8")
            args = [
                sys.executable, str(FLOW), "preflight", "--version-output", version,
                "--features-output-file", str(features),
            ]
            if configured_limit is None:
                args.append("--skip-config")
            else:
                config = root / "config.toml"
                config.write_text(f"[agents]\nmax_concurrent_threads_per_session = {configured_limit}\n", encoding="utf-8")
                args.extend(("--config", str(config)))
            completed = subprocess.run(args + list(extra), cwd=ROOT, capture_output=True, text=True, check=False)
        self.assertEqual(completed.stderr, "", completed.stderr)
        return completed, json.loads(completed.stdout)

    def test_old_cli_does_not_override_reported_current_capability(self) -> None:
        completed, payload = self.run_preflight(
            "--effective-capability", "delegation", "--require-delegation",
            version="codex-cli 0.146.9", multi_agent=False,
        )
        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["status"], "ready")
        self.assertTrue(payload["capabilities"]["delegation"])
        self.assertEqual(payload["cli_compatibility"]["status"], "incompatible")
        self.assertFalse(payload["cli_compatibility"]["determines_current_turn_capability"])
        self.assertEqual(payload["cli_compatibility"]["version_source"], "--version-output")
        observation = payload["capability_observation"]
        self.assertEqual(observation["authority"], "caller-reported current-turn callable surface")
        self.assertFalse(observation["callability_verified_by_preflight"])

    def test_positive_cli_flags_do_not_supply_missing_current_capability(self) -> None:
        completed, payload = self.run_preflight("--require-delegation")
        self.assertEqual(completed.returncode, 2, payload)
        self.assertEqual(payload["cli_compatibility"]["status"], "compatible")
        self.assertFalse(payload["capabilities"]["delegation"])
        self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], 0)

    def test_unknown_capacity_has_a_bounded_advisory(self) -> None:
        completed, payload = self.run_preflight(
            "--tool-surface-confirmed", "--initial-active-child-target", "8", configured_limit=None,
        )
        self.assertEqual(completed.returncode, 0, payload)
        capacity = payload["delegation_capacity"]
        self.assertIsNone(capacity["configured_ceiling"])
        self.assertIsNone(capacity["governed_active_child_ceiling"])
        self.assertEqual(capacity["recommended_additional_children"], 1)
        self.assertEqual(capacity["recommendation_status"], "advisory-bounded")
        self.assertFalse(capacity["recommendation_is_admission_authority"])
        self.assertIsNone(capacity["recommended_ramp_step"])

    def test_configuration_is_neither_effective_slots_nor_a_universal_six_ceiling(self) -> None:
        completed, payload = self.run_preflight("--tool-surface-confirmed")
        self.assertEqual(completed.returncode, 0, payload)
        capacity = payload["delegation_capacity"]
        self.assertEqual(capacity["configured_ceiling"], 9)
        self.assertEqual(capacity["governed_active_child_ceiling"], 9)
        self.assertFalse(capacity["configured_ceiling_is_effective_capacity"])
        self.assertEqual(capacity["effective_capacity_status"], "not-observed")
        self.assertEqual(capacity["recommended_additional_children"], 1)
        self.assertIsNone(capacity["capacity_inputs"]["remaining_child_slots"])

    @staticmethod
    def reported_capacity(**changes: int) -> list[str]:
        values = {
            "host-active-child-limit": 9, "remaining-child-slots": 9, "active-children": 0,
            "user-active-child-budget": 9, "ready-independent-units": 20,
            "integration-child-allowance": 9,
        }
        values.update(changes)
        return [value for name, count in values.items() for value in (f"--{name}", str(count))]

    def test_reported_width_is_not_capped_at_six_or_three(self) -> None:
        completed, payload = self.run_preflight("--tool-surface-confirmed", *self.reported_capacity())
        self.assertEqual(completed.returncode, 0, payload)
        capacity = payload["delegation_capacity"]
        self.assertEqual(capacity["recommended_additional_children"], 9)
        self.assertEqual(capacity["recommended_initial_active_children"], 9)
        self.assertEqual(capacity["effective_capacity_status"], "caller-reported")
        self.assertEqual(capacity["capacity_input_provenance"], "caller-reported; not measured by preflight")
        self.assertEqual(capacity["missing_capacity_inputs"], [])

    def test_every_reported_admission_constraint_limits_new_work(self) -> None:
        for name in (
            "host-active-child-limit", "remaining-child-slots", "user-active-child-budget",
            "ready-independent-units", "integration-child-allowance",
        ):
            with self.subTest(bound=name):
                completed, payload = self.run_preflight(
                    "--tool-surface-confirmed", *self.reported_capacity(**{name: 2}),
                )
                self.assertEqual(completed.returncode, 0, payload)
                self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], 2)
        completed, payload = self.run_preflight(
            "--tool-surface-confirmed", *self.reported_capacity(), configured_limit=2,
        )
        self.assertEqual(completed.returncode, 0, payload)
        self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], 2)

    def test_active_work_consumes_budget_and_remaining_slots_are_separate(self) -> None:
        completed, payload = self.run_preflight(
            "--tool-surface-confirmed",
            *self.reported_capacity(**{"active-children": 4, "remaining-child-slots": 5, "user-active-child-budget": 7}),
        )
        self.assertEqual(completed.returncode, 0, payload)
        capacity = payload["delegation_capacity"]
        self.assertEqual(capacity["effective_active_children"], 4)
        self.assertEqual(capacity["capacity_inputs"]["remaining_child_slots"], 5)
        self.assertEqual(capacity["recommended_additional_children"], 3)
        self.assertEqual(capacity["recommended_initial_active_children"], 7)

    def test_zero_capacity_prevents_admission_without_erasing_callability(self) -> None:
        for name in ("host-active-child-limit", "remaining-child-slots", "user-active-child-budget", "ready-independent-units", "integration-child-allowance"):
            with self.subTest(bound=name):
                completed, payload = self.run_preflight(
                    "--tool-surface-confirmed", "--require-delegation", f"--{name}", "0",
                )
                self.assertEqual(completed.returncode, 0, payload)
                self.assertTrue(payload["capabilities"]["delegation"])
                self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], 0)

    def test_soft_target_is_adjustable_and_host_bound_remains_hard(self) -> None:
        for target, expected in ((4, 4), (12, 9)):
            with self.subTest(target=target):
                completed, payload = self.run_preflight(
                    "--tool-surface-confirmed", *self.reported_capacity(),
                    "--initial-active-child-target", str(target),
                )
                self.assertEqual(completed.returncode, 0, payload)
                self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], expected)

    def test_malformed_capacity_inputs_are_rejected(self) -> None:
        for name, value in (("remaining-child-slots", -1), ("active-children", -1), ("initial-active-child-target", 0)):
            with self.subTest(name=name):
                completed, payload = self.run_preflight("--tool-surface-confirmed", f"--{name}", str(value))
                self.assertEqual(completed.returncode, 2, payload)
                self.assertEqual(payload["delegation_capacity"]["recommended_additional_children"], 0)


if __name__ == "__main__":
    unittest.main()
