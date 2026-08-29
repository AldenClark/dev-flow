from __future__ import annotations

import itertools
import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"

import sys

sys.path.insert(0, str(SCRIPTS))

import resource_coordination
import workstream_contract


def write_workstream(
    target: Path,
    *,
    state: str,
    slice_status: str,
    implementation_gate: str,
    qualification_gate: str,
) -> None:
    target.mkdir(parents=True, exist_ok=True)
    (target / "implementation.md").write_text(
        """<!-- dev-flow-workstream-contract: v1 -->
# model

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | model | `evals/` | - | model check | %s | D1 |
""" % slice_status,
        encoding="utf-8",
    )
    (target / "progress.md").write_text(
        """<!-- dev-flow-workstream-contract: v1 -->
# model

- State: %s
- Current slice: S0
- Terminal condition: all required gates and slices agree

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | implementation | implementation | %s | D1 |
| HC2 | qualification | qualification | %s | D1 |

## Active convergence checkpoint

None.
""" % (state, implementation_gate, qualification_gate),
        encoding="utf-8",
    )


class WorkstreamStateModelCheckingTests(unittest.TestCase):
    def test_exhaustive_state_slice_and_gate_lattice(self) -> None:
        terminal = {"implementation-complete", "release-qualified", "closed"}
        fully_qualified = {"release-qualified", "closed"}
        closed_gate = {"passed", "waived"}
        selectable_slice = {"ready", "in-progress", "blocked"}
        terminal_slice = {"complete", "deferred"}

        combinations = itertools.product(
            sorted(workstream_contract.WORKSTREAM_STATES),
            sorted(workstream_contract.SLICE_STATUSES),
            sorted(workstream_contract.GATE_STATUSES),
            sorted(workstream_contract.GATE_STATUSES),
        )
        checked = 0
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "workstream"
            for state, slice_status, implementation_gate, qualification_gate in combinations:
                write_workstream(
                    target,
                    state=state,
                    slice_status=slice_status,
                    implementation_gate=implementation_gate,
                    qualification_gate=qualification_gate,
                )
                result, _ = workstream_contract.check(
                    Path(temporary), target, check_worktree=False, strict=True
                )
                expected_valid = (
                    slice_status in (terminal_slice if state in terminal else selectable_slice)
                    and (
                        state not in terminal
                        or implementation_gate in closed_gate
                    )
                    and (
                        state not in fully_qualified
                        or qualification_gate in closed_gate
                    )
                )
                self.assertEqual(
                    result["status"] == "valid",
                    expected_valid,
                    (state, slice_status, implementation_gate, qualification_gate, result),
                )
                checked += 1
        self.assertEqual(checked, 1764)


class ResourceLeaseModelCheckingTests(unittest.TestCase):
    ACTIONS = (
        "acquire",
        "renew-valid",
        "renew-wrong",
        "release-valid",
        "release-wrong",
        "expire",
    )

    def test_bounded_lease_transition_sequences_refine_the_model(self) -> None:
        checked = 0
        for sequence in itertools.product(self.ACTIONS, repeat=3):
            with self.subTest(sequence=sequence), tempfile.TemporaryDirectory() as temporary:
                runtime = Path(temporary) / "runtime"
                now = 100.0
                active = False
                expires_at = 0.0
                generation = 0
                token: str | None = None

                for action in sequence:
                    if action == "expire":
                        now = max(now, expires_at) + 1.0
                        continue
                    if action == "acquire":
                        result = resource_coordination.acquire(
                            runtime, "port", "model", 10, "owner", now=now
                        )
                        if active and now < expires_at:
                            self.assertEqual(result["status"], "conflict")
                        else:
                            expected = "expired-recovered" if active else "acquired"
                            self.assertEqual(result["status"], expected)
                            generation = generation + 1 if active else 1
                            self.assertEqual(result["generation"], generation)
                            token = result["token"]
                            active = True
                            expires_at = now + 10
                    elif action.startswith("renew"):
                        supplied = token if action == "renew-valid" and token else "wrong"
                        result = resource_coordination.renew(
                            runtime, "port", "model", supplied, 10, now=now
                        )
                        if not active or now >= expires_at:
                            self.assertEqual(result["status"], "expired")
                        elif action == "renew-wrong":
                            self.assertEqual(result["status"], "forbidden")
                        else:
                            self.assertEqual(result["status"], "renewed")
                            generation += 1
                            self.assertEqual(result["generation"], generation)
                            expires_at = now + 10
                    else:
                        supplied = token if action == "release-valid" and token else "wrong"
                        result = resource_coordination.release(
                            runtime, "port", "model", supplied, now=now
                        )
                        if not active:
                            self.assertEqual(result["status"], "available")
                        elif now >= expires_at:
                            self.assertEqual(result["status"], "expired")
                        elif action == "release-wrong":
                            self.assertEqual(result["status"], "forbidden")
                        else:
                            self.assertEqual(result["status"], "released")
                            self.assertEqual(result["generation"], generation + 1)
                            active = False
                            generation = 0
                            token = None
                observed = resource_coordination.inspect(
                    runtime, "port", "model", now=now
                )
                expected_observation = (
                    "leased" if active and now < expires_at else "expired" if active else "available"
                )
                self.assertEqual(observed["status"], expected_observation)
                checked += 1
        self.assertEqual(checked, 216)


class CurrentTruthModelTests(unittest.TestCase):
    def test_current_truth_rejects_unqualified_planning_claims(self) -> None:
        current_truth = {
            "requirements.md": (
                ROOT / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "requirements.md"
            ).read_text(encoding="utf-8"),
            "implementation.md": (
                ROOT / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "implementation.md"
            ).read_text(encoding="utf-8"),
            "progress.md": (
                ROOT / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "progress.md"
            ).read_text(encoding="utf-8"),
        }
        self.assertNotIn(
            "The current runner does not yet implement",
            current_truth["requirements.md"],
        )
        self.assertNotIn(
            "No RC.4 source behavior, test, host lease",
            current_truth["implementation.md"],
        )
        self.assertIn("607/607 tests passed", current_truth["progress.md"])
        self.assertIn("Independent implementation-byte review passed", current_truth["progress.md"])

        scanner_path = ROOT / "tools" / "static_scan_rc4.py"
        spec = importlib.util.spec_from_file_location("rc4_truth_scanner", scanner_path)
        assert spec and spec.loader
        scanner = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scanner)
        self.assertEqual(scanner.current_truth_findings(ROOT), [])


if __name__ == "__main__":
    unittest.main()
