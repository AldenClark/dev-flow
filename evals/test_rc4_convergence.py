from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
sys.path.insert(0, str(FLOW.parent))


def run_flow(*args: object, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(FLOW), *(str(value) for value in args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )


def managed_fixture(root: Path) -> Path:
    target = root / "docs" / "workstreams" / "sample"
    target.mkdir(parents=True)
    (target / "implementation.md").write_text(
        """<!-- dev-flow-workstream-contract: v1 -->
# sample implementation

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | baseline | `docs/workstreams/sample/` | - | review | complete | D1 |
| S1 | implementation | `skills/dev-flow/`, `evals/` | `README.md` | tests | ready | D1 |
""",
        encoding="utf-8",
    )
    (target / "progress.md").write_text(
        """<!-- dev-flow-workstream-contract: v1 -->
# sample progress

## Status

- State: active
- Current slice: S1
- Terminal condition: all slices and applicable gates close

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | baseline frozen | implementation | passed | D1 |
| HC2 | final qualification | qualification | not-run | S9 |

## Active convergence checkpoint

None.
""",
        encoding="utf-8",
    )
    return target


class IncrementalRouteTests(unittest.TestCase):
    def test_route_basis_is_stable_private_and_compact_compatible(self) -> None:
        args = (
            "route-task",
            "--intent",
            "change",
            "--risk",
            "weak-tests",
            "--repo-fact",
            "framework=secret-framework",
        )
        full = run_flow(*args)
        compact = run_flow(*args, "--compact")
        self.assertEqual(full.returncode, 0, full.stderr or full.stdout)
        self.assertEqual(compact.returncode, 0, compact.stderr or compact.stdout)
        full_payload = json.loads(full.stdout)
        compact_payload = json.loads(compact.stdout)
        self.assertEqual(
            full_payload["route_basis"]["digest"],
            compact_payload["route_basis"]["digest"],
        )
        self.assertEqual(
            set(compact_payload["route_basis"]),
            {"schema", "router_semantics", "digest"},
        )
        self.assertLess(len(compact.stdout), len(full.stdout) * 0.25)
        serialized = json.dumps(compact_payload["route_basis"], sort_keys=True)
        self.assertNotIn("secret-framework", serialized)
        self.assertEqual(full_payload["route_basis"]["schema"], "dev-flow.route-basis.v1")

    def test_previous_route_reports_unchanged_and_material_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path(temporary) / "previous.json"
            first = run_flow("route-task", "--intent", "change")
            previous.write_text(first.stdout, encoding="utf-8")
            unchanged = run_flow(
                "route-task", "--intent", "change", "--compact", "--previous-route", previous
            )
            changed = run_flow(
                "route-task",
                "--intent",
                "change",
                "--need",
                "review",
                "--compact",
                "--previous-route",
                previous,
            )
        self.assertEqual(json.loads(unchanged.stdout)["recalibration"]["status"], "unchanged")
        delta = json.loads(changed.stdout)["recalibration"]
        self.assertEqual(delta["status"], "changed")
        self.assertIn("capabilities", delta["changed_dimensions"])
        self.assertIn("routes", delta["invalidated_decisions"])

    def test_compact_previous_route_is_unchanged_or_conservatively_invalidated(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path(temporary) / "compact.json"
            first = run_flow("route-task", "--intent", "change", "--compact")
            previous.write_text(first.stdout, encoding="utf-8")
            unchanged = run_flow(
                "route-task", "--intent", "change", "--compact", "--previous-route", previous
            )
            changed = run_flow(
                "route-task", "--intent", "change", "--need", "review", "--compact", "--previous-route", previous
            )
        self.assertEqual(json.loads(unchanged.stdout)["recalibration"]["status"], "unchanged")
        delta = json.loads(changed.stdout)["recalibration"]
        self.assertEqual(delta["status"], "changed-digest-only")
        self.assertEqual(delta["changed_dimensions"], [])
        self.assertIn("routes", delta["invalidated_decisions"])
        self.assertEqual(delta["next_action"], "use-complete-current-route")

    def test_previous_route_is_bounded_regular_json(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            malformed = root / "bad.json"
            malformed.write_text("not-json", encoding="utf-8")
            result = run_flow(
                "route-task", "--intent", "change", "--previous-route", malformed
            )
            self.assertEqual(result.returncode, 0)
            self.assertEqual(
                json.loads(result.stdout)["recalibration"]["status"],
                "incompatible-prior-route",
            )
            link = root / "link.json"
            link.symlink_to(malformed)
            linked = run_flow("route-task", "--intent", "change", "--previous-route", link)
            self.assertEqual(linked.returncode, 0)
            self.assertEqual(
                json.loads(linked.stdout)["recalibration"]["next_action"],
                "use-complete-current-route",
            )
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (512 * 1024 + 1))
            bounded = run_flow(
                "route-task", "--intent", "change", "--previous-route", oversized
            )
            self.assertEqual(bounded.returncode, 0)
            self.assertEqual(
                json.loads(bounded.stdout)["recalibration"]["reason"],
                "invalid-prior-route",
            )
            deeply_nested = root / "deep.json"
            deeply_nested.write_text("[" * 5000 + "]" * 5000, encoding="utf-8")
            nested = run_flow(
                "route-task", "--intent", "change", "--previous-route", deeply_nested
            )
            self.assertEqual(nested.returncode, 0)
            self.assertEqual(
                json.loads(nested.stdout)["recalibration"]["reason"],
                "invalid-prior-route",
            )

    def test_route_basis_rejects_unbounded_free_form_values(self) -> None:
        result = run_flow(
            "route-task", "--intent", "change", "--repo-fact", "context=" + "x" * 300
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "invalid")

    def test_every_route_parser_input_has_basis_treatment(self) -> None:
        import importlib.util
        import sys

        scripts = FLOW.parent
        sys.path.insert(0, str(scripts))
        spec = importlib.util.spec_from_file_location("dev_flow_rc4", scripts / "dev_flow.py")
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        import route_incremental

        parser = module.build_parser()
        route = next(action.choices["route-task"] for action in parser._actions if action.dest == "command")
        actual = {
            action.dest
            for action in route._actions
            if action.dest not in {"help", "compact", "explain", "previous_route"}
        }
        self.assertEqual(actual, set(route_incremental.ROUTE_BASIS_OPTION_DESTS))

    def test_every_route_input_mutation_changes_its_declared_basis_dimension(self) -> None:
        import route_incremental

        variants = {
            "intent": ("--intent", "review"),
            "task_type": ("--task-type", "routine"),
            "risk": ("--intent", "change", "--risk", "weak-tests"),
            "need": ("--intent", "change", "--need", "review"),
            "ui_impact": ("--intent", "change", "--ui-impact", "material"),
            "ambiguity": ("--intent", "change", "--ambiguity"),
            "material_exposure": ("--intent", "change", "--material-exposure"),
            "independent_review_authorized": ("--intent", "change", "--independent-review-authorized"),
            "repo_fact": ("--intent", "change", "--repo-fact", "language=python"),
            "effective_skill": ("--intent", "change", "--effective-skill", "test-system-engineering"),
            "method_signal": ("--intent", "change", "--method-signal", "oracle-challenge"),
            "method_prerequisite": ("--intent", "change", "--method-prerequisite", "test-oracle"),
            "method_depth": ("--intent", "change", "--method-depth", "deep"),
            "requirement_class": ("--intent", "change", "--requirement-class", "semantic-change"),
            "understanding_confirmed": ("--intent", "change", "--understanding-confirmed"),
            "waive_understanding_confirmation": ("--intent", "change", "--waive-understanding-confirmation"),
            "profile_operation": ("--intent", "change", "--profile-operation"),
            "suite_maintenance": ("--intent", "change", "--suite-maintenance"),
            "mutation": ("--intent", "change", "--mutation", "none"),
            "unknown": ("--intent", "change", "--unknown", "architecture"),
            "work_mode": ("--intent", "change", "--work-mode", "managed"),
            "multi_session": ("--intent", "change", "--multi-session"),
            "multi_slice": ("--intent", "change", "--multi-slice"),
            "cross_module": ("--intent", "change", "--cross-module"),
            "coordination": ("--intent", "change", "--coordination"),
            "material_tradeoff": ("--intent", "change", "--material-tradeoff"),
            "durable_plan": ("--intent", "change", "--durable-plan"),
            "knowledge_impact": ("--intent", "change", "--knowledge-impact", "current-truth"),
            "overlay": ("--intent", "change", "--overlay", "security"),
        }
        self.assertEqual(set(variants), set(route_incremental.ROUTE_BASIS_OPTION_DIMENSIONS))
        with tempfile.TemporaryDirectory() as temporary:
            previous = Path(temporary) / "previous.json"
            baseline = run_flow("route-task", "--intent", "change")
            self.assertEqual(baseline.returncode, 0, baseline.stderr or baseline.stdout)
            previous.write_text(baseline.stdout, encoding="utf-8")
            for option, arguments in variants.items():
                with self.subTest(option=option):
                    result = run_flow(
                        "route-task", *arguments, "--compact", "--previous-route", previous
                    )
                    self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
                    recalibration = json.loads(result.stdout)["recalibration"]
                    self.assertEqual(recalibration["status"], "changed")
                    self.assertTrue(
                        route_incremental.ROUTE_BASIS_OPTION_DIMENSIONS[option]
                        <= set(recalibration["changed_dimensions"]),
                        recalibration,
                    )


class WorkstreamContractTests(unittest.TestCase):
    def test_valid_active_workstream_and_claim_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            result = run_flow("check-workstream", "--root", root, "--path", target)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload["status"], "valid")
        self.assertEqual(payload["claim_limit"], "structural-consistency-only")

    def test_checker_rejects_gate_overclaim_and_two_in_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            implementation = target / "implementation.md"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace("| review | complete |", "| review | in-progress |").replace("| tests | ready |", "| tests | in-progress |"),
                encoding="utf-8",
            )
            progress = target / "progress.md"
            progress.write_text(
                progress.read_text(encoding="utf-8").replace("- State: active", "- State: release-qualified"),
                encoding="utf-8",
            )
            result = run_flow("check-workstream", "--root", root, "--path", target)
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        codes = {finding["code"] for finding in payload["findings"]}
        self.assertIn("multiple-in-progress", codes)
        self.assertIn("qualification-gate-open", codes)

    def test_checker_rejects_unsafe_prefix_and_pending_two_strike(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            implementation = target / "implementation.md"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace("`skills/dev-flow/`, `evals/`", "`../outside/`"),
                encoding="utf-8",
            )
            progress = target / "progress.md"
            progress.write_text(
                progress.read_text(encoding="utf-8").replace(
                    "None.",
                    "| Mechanism | Non-progress repairs | Primary progress | Disposition | Authority/decision |\n|---|---:|---|---|---|\n| grader | 2 | unchanged | pending | - |",
                ),
                encoding="utf-8",
            )
            result = run_flow("check-workstream", "--root", root, "--path", target)
        codes = {finding["code"] for finding in json.loads(result.stdout)["findings"]}
        self.assertIn("unsafe-prefix", codes)
        self.assertIn("convergence-decision-required", codes)

    def test_checker_rejects_git_metadata_and_nonportable_prefixes(self) -> None:
        for unsafe in (".git/objects/", "C:/temp/", "dir\\child/"):
            with self.subTest(prefix=unsafe), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
                target = managed_fixture(root)
                implementation = target / "implementation.md"
                implementation.write_text(
                    implementation.read_text(encoding="utf-8").replace(
                        "`skills/dev-flow/`, `evals/`", f"`{unsafe}`"
                    ),
                    encoding="utf-8",
                )
                result = run_flow("check-workstream", "--root", root, "--path", target)
                self.assertIn(
                    "unsafe-prefix",
                    {finding["code"] for finding in json.loads(result.stdout)["findings"]},
                )

    def test_checker_rejects_invalid_or_unowned_convergence_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            progress = target / "progress.md"
            checkpoint = "| Mechanism | Non-progress repairs | Primary progress | Disposition | Authority/decision |\n|---|---:|---|---|---|\n| grader | 2 | unchanged | continue-authorized | - |"
            progress.write_text(
                progress.read_text(encoding="utf-8").replace("None.", checkpoint),
                encoding="utf-8",
            )
            missing = run_flow("check-workstream", "--root", root, "--path", target)
            self.assertIn(
                "missing-convergence-decision",
                {finding["code"] for finding in json.loads(missing.stdout)["findings"]},
            )
            progress.write_text(
                progress.read_text(encoding="utf-8").replace(
                    "continue-authorized | -", "invent-new-policy | D1"
                ),
                encoding="utf-8",
            )
            invalid = run_flow("check-workstream", "--root", root, "--path", target)
            self.assertIn(
                "invalid-convergence-disposition",
                {finding["code"] for finding in json.loads(invalid.stdout)["findings"]},
            )

    def test_marker_is_symmetric_and_exact(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            progress = target / "progress.md"
            progress.write_text(
                progress.read_text(encoding="utf-8").replace(
                    "<!-- dev-flow-workstream-contract: v1 -->\n", ""
                ),
                encoding="utf-8",
            )
            result = run_flow("check-workstream", "--root", root, "--path", target)
        self.assertEqual(result.returncode, 2)
        self.assertIn(
            "invalid-contract-marker",
            {finding["code"] for finding in json.loads(result.stdout)["findings"]},
        )

    def test_worktree_reconciliation_reports_without_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            user_file = root / "user owned.txt"
            user_file.write_text("preserve", encoding="utf-8")
            result = run_flow(
                "check-workstream", "--root", root, "--path", target, "--check-worktree"
            )
            self.assertEqual(user_file.read_text(encoding="utf-8"), "preserve")
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 2)
        self.assertIn("user owned.txt", payload["worktree"]["ambiguous_paths"])

    def test_completed_slice_protection_is_historical_not_current(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            implementation = target / "implementation.md"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace(
                    "`docs/workstreams/sample/` | - | review",
                    "`docs/workstreams/sample/` | `docs/workstreams/sample/` | review",
                ),
                encoding="utf-8",
            )
            result = run_flow(
                "check-workstream", "--root", root, "--path", target, "--check-worktree"
            )
        payload = json.loads(result.stdout)
        self.assertNotIn(
            "protected-path-changed",
            {finding["code"] for finding in payload["findings"]},
        )

    def test_hidden_repository_prefix_keeps_its_leading_dot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            target = managed_fixture(root)
            implementation = target / "implementation.md"
            implementation.write_text(
                implementation.read_text(encoding="utf-8").replace(
                    "`skills/dev-flow/`, `evals/`", "`.github/`, `.codex-plugin/`"
                ),
                encoding="utf-8",
            )
            (root / ".github").mkdir()
            (root / ".github" / "ci.yml").write_text("test\n", encoding="utf-8")
            result = run_flow(
                "check-workstream", "--root", root, "--path", target, "--check-worktree"
            )
        payload = json.loads(result.stdout)
        self.assertIn(".github/", payload["worktree"]["accumulated_write_prefixes"])
        self.assertNotIn(".github/ci.yml", payload["worktree"]["ambiguous_paths"])

    def test_non_git_worktree_reconciliation_is_not_applicable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = managed_fixture(root)
            result = run_flow(
                "check-workstream", "--root", root, "--path", target, "--check-worktree"
            )
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0, payload)
        self.assertEqual(payload["status"], "not-applicable")
        self.assertEqual(payload["worktree"]["reason"], "root-is-not-a-git-worktree")


if __name__ == "__main__":
    unittest.main()
