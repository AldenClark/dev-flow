#!/usr/bin/env python3
"""Non-spending contract tests for the opt-in transition trial runner."""

from __future__ import annotations

import json
import importlib.util
import io
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "evals" / "run_transition_trials.py"


def load_runner_module():
    spec = importlib.util.spec_from_file_location("run_transition_trials", RUNNER)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load transition runner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TransitionRunnerTests(unittest.TestCase):
    def test_every_codex_lineage_disables_shell_environment_inheritance(self) -> None:
        runner = load_runner_module()
        commands: list[list[str]] = []
        environments: list[dict[str, str]] = []

        def fake_run(command, **kwargs):
            commands.append(command)
            environments.append(kwargs["env"])
            output_index = command.index("--output-last-message") + 1
            Path(command[output_index]).write_text("bounded response", encoding="utf-8")
            kwargs["stdout"].write('{"thread_id":"trial-session"}\n')
            return SimpleNamespace(returncode=0, stderr="")

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repository = root / "repository"
            repository.mkdir()
            with (
                mock.patch.dict(
                    runner.os.environ, {"DEV_FLOW_TEST_SECRET": "must-not-cross"}
                ),
                mock.patch.object(runner, "run_bounded_process", side_effect=fake_run),
            ):
                for index, (session_id, fork) in enumerate(
                    ((None, False), ("trial-session", False), ("trial-session", True)),
                    1,
                ):
                    runner.run_codex_turn(
                        codex="codex",
                        codex_home=root / "codex-home",
                        repository=repository,
                        model="test-model",
                        effort="low",
                        prompt="bounded task",
                        session_id=session_id,
                        fork=fork,
                        events=root / f"events-{index}.jsonl",
                        last_message=root / f"message-{index}.txt",
                        token_limit=12_345,
                        timeout_seconds=60,
                    )

        self.assertEqual(len(commands), 3)
        for command in commands:
            self.assertIn("shell_environment_policy.inherit=\"none\"", command)
            self.assertIn("features.rollout_budget.enabled=true", command)
            self.assertIn("features.rollout_budget.limit_tokens=12345", command)
            self.assertIn(
                "features.rollout_budget.reminder_at_remaining_tokens=[]", command
            )
            self.assertIn("sandbox_workspace_write.network_access=false", command)
        self.assertTrue(
            all("DEV_FLOW_TEST_SECRET" not in environment for environment in environments)
        )
        for command in commands:
            for setting in (
                'web_search="disabled"',
                "features.image_generation=false",
                "features.remote_plugin=false",
                "features.skill_mcp_dependency_install=false",
                "features.network_proxy=false",
                "features.enable_mcp_apps=false",
                "features.multi_agent_v2.enabled=true",
                "agents.max_concurrent_threads_per_session=2",
                "features.multi_agent_v2.max_concurrent_threads_per_session=2",
            ):
                self.assertIn(setting, command)

    def test_runner_exposes_only_candidate_execution_inputs(self) -> None:
        runner = load_runner_module()
        args = runner.parse_args([])
        self.assertEqual(
            set(vars(args)),
            {
                "catalog",
                "case_ids",
                "attempts",
                "model",
                "reasoning_effort",
                "codex",
                "plugin_root",
                "output_dir",
                "max_total_tokens",
                "per_call_token_limit",
                "per_call_timeout_seconds",
                "qualification",
                "execute",
                "acknowledge_model_spend",
            },
        )

    def test_timeout_terminates_the_entire_posix_process_group(self) -> None:
        runner = load_runner_module()
        if runner.os.name != "posix":
            self.skipTest("POSIX process-group contract")
        process = mock.Mock()
        process.pid = 43210
        process.poll.side_effect = (0, 0)
        process.communicate.side_effect = subprocess.TimeoutExpired(["codex"], 1)
        process.wait.return_value = 0
        with (
            mock.patch.object(runner.subprocess, "Popen", return_value=process),
            mock.patch.object(runner.os, "killpg") as killpg,
            self.assertRaises(subprocess.TimeoutExpired),
        ):
            runner.run_bounded_process(
                ["codex"], timeout=1, capture_output=True, text=True
            )
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(43210, runner.signal.SIGTERM),
                mock.call(43210, runner.signal.SIGKILL),
            ],
        )
        process.wait.assert_called_once_with(timeout=2)

    def test_success_also_cleans_the_posix_process_group(self) -> None:
        runner = load_runner_module()
        if runner.os.name != "posix":
            self.skipTest("POSIX process-group contract")
        process = mock.Mock()
        process.pid = 43211
        process.returncode = 0
        process.poll.return_value = 0
        process.communicate.return_value = (None, None)
        process.wait.return_value = 0
        with (
            mock.patch.object(runner.subprocess, "Popen", return_value=process),
            mock.patch.object(runner.os, "killpg") as killpg,
        ):
            completed = runner.run_bounded_process(
                ["codex"], timeout=1, capture_output=True, text=True
            )
        self.assertEqual(completed.returncode, 0)
        self.assertEqual(
            killpg.call_args_list,
            [
                mock.call(43211, runner.signal.SIGTERM),
                mock.call(43211, runner.signal.SIGKILL),
            ],
        )

    def test_capture_output_is_bounded_without_pipes(self) -> None:
        runner = load_runner_module()
        with (
            mock.patch.object(runner, "MAX_CAPTURE_BYTES", 4),
            self.assertRaises(runner.TrialError),
        ):
            runner.run_bounded_process(
                [sys.executable, "-c", "print('12345')"],
                timeout=10,
                capture_output=True,
                text=True,
            )

    def test_default_is_non_spending_dry_run(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr or completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "planned")
        self.assertFalse(result["executes_model"])
        self.assertFalse(result["raw_transcripts_retained"])
        self.assertFalse(result["self_grading"])
        self.assertTrue(result["first_attempt_responses_retained"])
        self.assertEqual(result["assessment"], "manual-observation-manifest")
        self.assertEqual(
            result["token_budget"],
            {
                "maximum_total_tokens": None,
                "per_call_token_limit": None,
                "per_call_timeout_seconds": None,
            },
        )
        self.assertGreaterEqual(len(result["cases"]), 8)

    def test_attempt_preserves_bounded_evidence_without_classifying_it(self) -> None:
        runner = load_runner_module()

        def fake_turn(**kwargs):
            kwargs["events"].write_text(
                json.dumps({"type": "thread.started", "thread_id": "session-1"})
                + "\n"
                + json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 10,
                            "output_tokens": 5,
                            "total_tokens": 15,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            kwargs["last_message"].write_text("bounded response", encoding="utf-8")
            return "session-1"

        case = {
            "id": "CASE",
            "lineage": "resume",
            "repository": {"README.md": "synthetic\n"},
            "turns": [
                {
                    "prompt": "Inspect only.",
                    "expected": [],
                    "forbidden": [],
                    "mutation": "none",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                mock.patch.object(runner, "install_candidate"),
                mock.patch.object(runner, "run_codex_turn", side_effect=fake_turn),
            ):
                evidence, usage = runner.run_attempt(
                    cases=[case],
                    codex="codex",
                    plugin_root=ROOT,
                    model="test-model",
                    effort="low",
                    maximum_tokens=100,
                    per_call_token_limit=100,
                    per_call_timeout_seconds=60,
                    usage_checkpoint=root / "usage-in-progress.json",
                    evidence_checkpoint=root / "evidence-in-progress.json",
                )
        self.assertEqual(
            evidence["schema_version"], "flow.transition.first-attempt-evidence.v1"
        )
        turn = evidence["cases"][0]["turns"][0]
        self.assertEqual(turn["response_text"], "bounded response")
        self.assertNotIn("observed", turn)
        self.assertNotIn("expected", turn)
        self.assertEqual(usage["consumed_tokens"], 15)
        self.assertEqual([item["role"] for item in usage["records"]], ["candidate"])

    def test_attempt_isolates_and_cleans_codex_home_per_case(self) -> None:
        runner = load_runner_module()
        observed_homes: list[Path] = []

        def fake_install(codex, codex_home, plugin_root):
            if observed_homes:
                self.assertFalse(observed_homes[-1].exists())
            observed_homes.append(codex_home)

        def fake_turn(**kwargs):
            kwargs["events"].write_text(
                json.dumps({"type": "thread.started", "thread_id": "session-1"})
                + "\n"
                + json.dumps(
                    {"type": "turn.completed", "usage": {"total_tokens": 1}}
                )
                + "\n",
                encoding="utf-8",
            )
            kwargs["last_message"].write_text("bounded response", encoding="utf-8")
            return "session-1"

        cases = [
            {
                "id": f"CASE-{index}",
                "lineage": "resume",
                "repository": {"README.md": "synthetic\n"},
                "turns": [
                    {
                        "prompt": "Inspect only.",
                        "expected": [],
                        "forbidden": [],
                        "mutation": "none",
                    }
                ],
            }
            for index in (1, 2)
        ]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (
                mock.patch.object(runner, "install_candidate", side_effect=fake_install),
                mock.patch.object(runner, "run_codex_turn", side_effect=fake_turn),
            ):
                runner.run_attempt(
                    cases=cases,
                    codex="codex",
                    plugin_root=ROOT,
                    model="test-model",
                    effort="low",
                    maximum_tokens=10,
                    per_call_token_limit=10,
                    per_call_timeout_seconds=60,
                    usage_checkpoint=root / "usage-in-progress.json",
                    evidence_checkpoint=root / "evidence-in-progress.json",
                )
        self.assertEqual(len(observed_homes), 2)
        self.assertNotEqual(observed_homes[0], observed_homes[1])

    def test_hard_gate_failure_preserves_bounded_first_attempt_evidence(self) -> None:
        runner = load_runner_module()

        def mutating_turn(**kwargs):
            (kwargs["repository"] / "README.md").write_text(
                "changed despite read-only turn\n", encoding="utf-8"
            )
            kwargs["events"].write_text(
                json.dumps({"type": "thread.started", "thread_id": "session-1"})
                + "\n"
                + json.dumps(
                    {"type": "turn.completed", "usage": {"total_tokens": 15}}
                )
                + "\n",
                encoding="utf-8",
            )
            kwargs["last_message"].write_text("I changed it.", encoding="utf-8")
            return "session-1"

        case = {
            "id": "CASE",
            "lineage": "resume",
            "repository": {"README.md": "synthetic\n"},
            "turns": [
                {
                    "prompt": "Inspect only.",
                    "expected": [],
                    "forbidden": [],
                    "mutation": "none",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            evidence_path = root / "evidence-in-progress.json"
            with (
                mock.patch.object(runner, "install_candidate"),
                mock.patch.object(runner, "run_codex_turn", side_effect=mutating_turn),
                self.assertRaisesRegex(runner.TrialError, "changed repository bytes"),
            ):
                runner.run_attempt(
                    cases=[case],
                    codex="codex",
                    plugin_root=ROOT,
                    model="test-model",
                    effort="low",
                    maximum_tokens=100,
                    per_call_token_limit=100,
                    per_call_timeout_seconds=60,
                    usage_checkpoint=root / "usage-in-progress.json",
                    evidence_checkpoint=evidence_path,
                )
            preserved = json.loads(evidence_path.read_text(encoding="utf-8"))
        turn = preserved["cases"][0]["turns"][0]
        self.assertEqual(turn["response_text"], "I changed it.")
        self.assertEqual([item["path"] for item in turn["repository_delta"]], ["README.md"])

    def test_execute_requires_explicit_model_budget_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--execute",
                    "--output-dir",
                    temporary,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--acknowledge-model-spend", completed.stdout)

    def test_unknown_case_is_rejected_before_execution(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(RUNNER), "--case", "NOT-A-CASE"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("unknown --case", completed.stdout)

    def test_execute_rejects_missing_token_budget_after_other_authority(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--execute",
                    "--acknowledge-model-spend",
                    "--model",
                    "test-model",
                    "--reasoning-effort",
                    "low",
                    "--output-dir",
                    temporary,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("--max-total-tokens, --per-call-token-limit", completed.stdout)

    def test_usage_parser_is_fail_closed(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events = root / "events.jsonl"
            events.write_text(
                "not-json\n"
                + json.dumps(
                    {
                        "type": "turn.completed",
                        "usage": {
                            "input_tokens": 10,
                            "cached_input_tokens": 2,
                            "output_tokens": 5,
                            "reasoning_output_tokens": 3,
                            "total_tokens": 15,
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(runner.total_tokens(runner.usage_breakdown(events), "test"), 15)
            self.assertEqual(runner.checked_tokens({"total_tokens": 15}, "test", 15), 15)
            with self.assertRaises(runner.TrialError):
                runner.checked_tokens({"total_tokens": 16}, "test", 15)


    def test_lineage_semantics_fail_closed(self) -> None:
        runner = load_runner_module()
        runner.validate_lineage_transition(
            case_id="CASE", turn=1, lineage="resume", previous=None, current="one"
        )
        runner.validate_lineage_transition(
            case_id="CASE", turn=2, lineage="resume", previous="one", current="one"
        )
        runner.validate_lineage_transition(
            case_id="CASE", turn=2, lineage="fork", previous="one", current="two"
        )
        with self.assertRaises(runner.TrialError):
            runner.validate_lineage_transition(
                case_id="CASE", turn=2, lineage="resume", previous="one", current="two"
            )
        with self.assertRaises(runner.TrialError):
            runner.validate_lineage_transition(
                case_id="CASE", turn=2, lineage="fork", previous="one", current="one"
            )

    def test_trajectory_and_repository_delta_are_bounded_assessment_evidence(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            events = root / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "command_execution",
                            "command": "git status --short",
                            "status": "completed",
                            "exit_code": 0,
                            "aggregated_output": "private output is not forwarded",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            self.assertEqual(
                runner.sanitized_trajectory(events),
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "status": "completed",
                        "exit_code": 0,
                        "command": "git status --short",
                    }
                ],
            )
            before = {"a.txt": {"sha256": runner.sha256_text("old"), "text": "old"}}
            after = {"a.txt": {"sha256": runner.sha256_text("new"), "text": "new"}}
            self.assertEqual(runner.repository_delta(before, after)[0]["after_text"], "new")
            events.write_text(
                json.dumps(
                    {"type": "image_generation_begin", "item": {"type": "image_generation"}}
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(runner.TrialError):
                runner.sanitized_trajectory(events)
            events.write_text(
                json.dumps(
                    {
                        "type": "collab_agent_spawn_end",
                        "new_thread_id": "child-1",
                        "prompt": "Inspect owned.py read-only; do not delegate.",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            collab = runner.sanitized_trajectory(events)
            self.assertEqual(collab[0]["event_type"], "collab_agent_spawn_end")
            self.assertIn("child_identity_sha256", collab[0])
            self.assertNotIn("Inspect owned.py", json.dumps(collab))
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "collab_agent_tool_call",
                            "name": "spawn_agent",
                            "status": "completed",
                            "agent_thread_id": "child-2",
                            "prompt": "private delegated scope",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            public_collab = runner.sanitized_trajectory(events)
            self.assertEqual(public_collab[0]["item_type"], "collab_agent_tool_call")
            self.assertIn("child_identity_sha256", public_collab[0])
            self.assertNotIn("private delegated scope", json.dumps(public_collab))
            with self.assertRaises(runner.TrialError):
                runner.enforce_trajectory_contract(
                    case_id="CASE",
                    expected=["child-scope-subset"],
                    trajectory=[],
                )

    def test_unknown_public_tool_failure_exposes_only_bounded_event_identity(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            events = Path(temporary) / "events.jsonl"
            events.write_text(
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "type": "mystery_tool_call",
                            "name": "private-tool-name with spaces",
                            "prompt": "private payload must not enter the error",
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(runner.TrialError) as raised:
                runner.sanitized_trajectory(events)
            message = str(raised.exception)
            self.assertIn("event_type=item.completed", message)
            self.assertIn("item_type=mystery_tool_call", message)
            self.assertNotIn("private-tool-name", message)
            self.assertNotIn("private payload", message)

    def test_isolated_rollout_recovers_hidden_delegation_without_transcript_text(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            sessions = codex_home / "sessions" / "2026" / "08" / "24"
            sessions.mkdir(parents=True)
            parent = sessions / "rollout-parent-parent-session.jsonl"
            child = sessions / "rollout-child-child-session.jsonl"
            parent.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "type": "event_msg",
                                "payload": {
                                    "type": "item_completed",
                                    "turn_id": "turn-1",
                                    "item": {
                                        "type": "SubAgentActivity",
                                        "kind": "started",
                                        "agent_thread_id": "child-session",
                                        "agent_path": "/root/inspect_owned",
                                    },
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "agent_message",
                                    "author": "/root/inspect_owned",
                                    "recipient": "/root",
                                    "internal_chat_message_metadata_passthrough": {
                                        "turn_id": "turn-1"
                                    },
                                    "content": [
                                        {
                                            "type": "input_text",
                                            "text": "synthetic private child result VALUE = 1",
                                        }
                                    ],
                                },
                            }
                        ),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            child.write_text(
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {"type": "output_text", "text": "VALUE = 1"}
                            ],
                        },
                    }
                )
                + "\n",
                encoding="utf-8",
            )

            trajectory = runner.sanitized_rollout_collaboration(
                codex_home, "parent-session"
            )

        self.assertEqual(
            [entry["event_type"] for entry in trajectory],
            ["collab_agent_spawn", "collab_agent_result"],
        )
        self.assertEqual(
            trajectory[0]["child_path_sha256"],
            trajectory[1]["child_path_sha256"],
        )
        self.assertIn("child_identity_sha256", trajectory[0])
        self.assertIn("content_sha256", trajectory[1])
        self.assertNotIn("synthetic private child result", json.dumps(trajectory))
        runner.enforce_trajectory_contract(
            case_id="CASE",
            expected=["child-scope-subset", "read-only-child", "no-redelegation"],
            trajectory=trajectory,
        )

    def test_rollout_delegation_fails_closed_on_missing_result_or_nested_spawn(self) -> None:
        runner = load_runner_module()
        spawn = {
            "event_type": "collab_agent_spawn",
            "child_identity_sha256": runner.sha256_text("child-session"),
            "child_path_sha256": runner.sha256_text("/root/inspect_owned"),
        }
        with self.assertRaises(runner.TrialError):
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["child-scope-subset"],
                trajectory=[spawn],
            )
        with self.assertRaises(runner.TrialError):
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["child-scope-subset", "no-redelegation"],
                trajectory=[
                    spawn,
                    {
                        "event_type": "collab_agent_result",
                        "child_path_sha256": spawn["child_path_sha256"],
                        "content_sha256": runner.sha256_text("result"),
                    },
                    {
                        "event_type": "collab_nested_spawn",
                        "child_identity_sha256": spawn["child_identity_sha256"],
                    },
                ],
            )

    def test_rollout_delegation_rejects_child_write_and_stale_turn_evidence(self) -> None:
        runner = load_runner_module()
        spawn = {
            "event_type": "collab_agent_spawn",
            "child_identity_sha256": runner.sha256_text("child-session"),
            "child_path_sha256": runner.sha256_text("/root/inspect_owned"),
        }
        result = {
            "event_type": "collab_agent_result",
            "child_path_sha256": spawn["child_path_sha256"],
            "content_sha256": runner.sha256_text("result"),
        }
        with self.assertRaises(runner.TrialError):
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["child-scope-subset", "read-only-child"],
                trajectory=[
                    spawn,
                    result,
                    {
                        "event_type": "collab_child_file_change",
                        "child_path_sha256": spawn["child_path_sha256"],
                    },
                ],
            )

        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            sessions = codex_home / "sessions" / "2026" / "08" / "24"
            sessions.mkdir(parents=True)
            parent = sessions / "rollout-parent-parent-session.jsonl"
            child = sessions / "rollout-child-child-session.jsonl"
            parent.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "type": "event_msg",
                                "payload": {
                                    "turn_id": "old-turn",
                                    "item": {
                                        "type": "SubAgentActivity",
                                        "kind": "started",
                                        "agent_thread_id": "child-session",
                                        "agent_path": "/root/inspect_owned",
                                    },
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "response_item",
                                "payload": {
                                    "type": "agent_message",
                                    "author": "/root/inspect_owned",
                                    "recipient": "/root",
                                    "internal_chat_message_metadata_passthrough": {
                                        "turn_id": "old-turn"
                                    },
                                    "content": [
                                        {"type": "input_text", "text": "old result"}
                                    ],
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "event_msg",
                                "payload": {
                                    "turn_id": "current-turn",
                                    "item": {"type": "TaskStarted"},
                                },
                            }
                        ),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            child.write_text("{}\n", encoding="utf-8")
            self.assertEqual(
                runner.sanitized_rollout_collaboration(
                    codex_home, "parent-session"
                ),
                [],
            )

    def test_rollout_lookup_fails_closed_on_ambiguous_or_malformed_evidence(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            codex_home = Path(temporary)
            sessions = codex_home / "sessions" / "one"
            sessions.mkdir(parents=True)
            first = sessions / "rollout-one-parent-session.jsonl"
            first.write_text("not-json\n", encoding="utf-8")
            with self.assertRaises(runner.TrialError):
                runner.sanitized_rollout_collaboration(
                    codex_home, "parent-session"
                )
            second_dir = codex_home / "sessions" / "two"
            second_dir.mkdir()
            (second_dir / "rollout-two-parent-session.jsonl").write_text(
                "{}\n", encoding="utf-8"
            )
            with self.assertRaises(runner.TrialError):
                runner.session_rollout_path(codex_home, "parent-session")

    def test_runner_owned_fixture_delta_requires_one_real_retry_command(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            delta = runner.apply_pre_turn_fixture(
                repository,
                {"tools/deep_scanner.py": "print('scanner-ready')\n"},
            )
            self.assertEqual([entry["path"] for entry in delta], ["tools/deep_scanner.py"])
            trajectory = [
                {
                    "event_type": "item.started",
                    "item_type": "command_execution",
                    "command": "python3 tools/deep_scanner.py",
                    "status": "in_progress",
                },
                {
                    "event_type": "item.completed",
                    "item_type": "command_execution",
                    "command": "python3 tools/deep_scanner.py",
                    "status": "completed",
                    "exit_code": 0,
                }
            ]
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["one-justified-retry"],
                trajectory=trajectory,
                fixture_delta=delta,
            )
            wrapped_trajectory = [
                {
                    **entry,
                    "command": "/bin/zsh -lc 'python3 tools/deep_scanner.py'",
                }
                for entry in trajectory
            ]
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["one-justified-retry"],
                trajectory=wrapped_trajectory,
                fixture_delta=delta,
            )
            for invalid in ([], [*trajectory, trajectory[-1]]):
                with self.subTest(invalid=invalid), self.assertRaises(runner.TrialError):
                    runner.enforce_trajectory_contract(
                        case_id="CASE",
                        expected=["one-justified-retry"],
                        trajectory=invalid,
                        fixture_delta=delta,
                    )
            bypasses = (
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "python3 -c \"print('tools/deep_scanner.py')\"",
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "/tmp/zsh -lc 'python3 tools/deep_scanner.py'",
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "tools/bash -c 'python3 tools/deep_scanner.py'",
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": (
                            "/bin/zsh -lc "
                            "'python3 tools/deep_scanner.py && echo extra'"
                        ),
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.started",
                        "item_type": "command_execution",
                        "command": "python3 tools/deep_scanner.py",
                        "status": "in_progress",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "python3 'tools/deep_scanner.py",
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "python3 tools/deep_scanner.py",
                        "status": "failed",
                        "exit_code": 1,
                    },
                    trajectory[-1],
                ],
                [
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "python3 tools/deep_scanner.py",
                        "status": "unexpected",
                        "exit_code": 0,
                    },
                    trajectory[-1],
                ],
            )
            for bypass in bypasses:
                with self.subTest(bypass=bypass), self.assertRaises(runner.TrialError):
                    runner.enforce_trajectory_contract(
                        case_id="CASE",
                        expected=["one-justified-retry"],
                        trajectory=bypass,
                        fixture_delta=delta,
                    )
            with self.assertRaises(runner.TrialError):
                runner.apply_pre_turn_fixture(repository, {"../escape": "unsafe"})
            with self.assertRaises(runner.TrialError):
                runner.enforce_trajectory_contract(
                    case_id="CASE",
                    expected=["one-justified-retry"],
                    trajectory=[
                        {
                            "event_type": "item.completed",
                            "item_type": "command_execution",
                            "command": "/bin/zsh -lc 'python3 tools/$X.py'",
                            "status": "completed",
                            "exit_code": 0,
                        }
                    ],
                    fixture_delta=[{"path": "tools/$X.py"}],
                )

    def test_bounded_file_read_rejects_growth_after_initial_metadata(self) -> None:
        runner = load_runner_module()
        path = mock.MagicMock()
        metadata = SimpleNamespace(
            st_mode=runner.stat.S_IFREG,
            st_size=1,
            st_dev=1,
            st_ino=2,
        )
        with (
            mock.patch.object(runner.os, "open", return_value=42),
            mock.patch.object(runner.os, "lstat", return_value=metadata),
            mock.patch.object(runner.os, "fstat", return_value=metadata),
            mock.patch.object(
                runner.os,
                "fdopen",
                return_value=io.BytesIO(b"x" * 11),
            ),
            self.assertRaisesRegex(runner.TrialError, "bounded file size"),
        ):
            runner.bounded_file_bytes(path, 10, "growing input")

    def test_bounded_file_read_rejects_symlink_without_nofollow_support(self) -> None:
        runner = load_runner_module()

        class StalePrecheckPath:
            def __init__(self, path: Path) -> None:
                self.path = path

            def __fspath__(self) -> str:
                return str(self.path)

            def is_symlink(self) -> bool:
                return False

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "target.txt"
            target.write_bytes(b"secret")
            link = root / "link.txt"
            link.symlink_to(target)
            with (
                mock.patch.object(runner.os, "O_NOFOLLOW", 0),
                self.assertRaisesRegex(runner.TrialError, "regular file"),
            ):
                runner.bounded_file_bytes(StalePrecheckPath(link), 10, "symlink input")

    def test_candidate_identity_excludes_ignored_runtime_and_bounds_source(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            subprocess.run(["git", "init", "--quiet"], cwd=root, check=True)
            (root / ".gitignore").write_text(".ignored-runtime/\n", encoding="utf-8")
            (root / "source.txt").write_text("source", encoding="utf-8")
            subprocess.run(
                ["git", "add", ".gitignore", "source.txt"], cwd=root, check=True
            )
            ignored = root / ".ignored-runtime"
            ignored.mkdir()
            runtime = ignored / "session.bin"
            runtime.write_bytes(b"first")
            original = runner.candidate_source_sha256(root)
            runtime.write_bytes(b"changed ignored runtime")
            self.assertEqual(runner.candidate_source_sha256(root), original)
            (root / "admitted.txt").write_text("new source", encoding="utf-8")
            self.assertNotEqual(runner.candidate_source_sha256(root), original)
            with (
                mock.patch.object(runner, "MAX_CANDIDATE_FILE_BYTES", 4),
                self.assertRaises(runner.TrialError),
            ):
                runner.candidate_source_sha256(root)

    def test_repository_digest_rejects_oversized_fixture_before_identity(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "large.txt").write_bytes(b"12345")
            with (
                mock.patch.object(runner, "MAX_REPOSITORY_FILE_BYTES", 4),
                self.assertRaises(runner.TrialError),
            ):
                runner.repository_sha256(root)

    def test_known_python_runtime_caches_do_not_count_as_source_mutation(self) -> None:
        runner = load_runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "service.py").write_text("VALUE = 1\n", encoding="utf-8")
            baseline_state = runner.repository_state(root)
            baseline_sha = runner.repository_sha256(root)
            cache = root / "__pycache__"
            cache.mkdir()
            (cache / "service.cpython-314.pyc").write_bytes(b"derived")
            pytest_cache = root / ".pytest_cache"
            pytest_cache.mkdir()
            (pytest_cache / "README.md").write_text("derived\n", encoding="utf-8")
            self.assertEqual(runner.repository_state(root), baseline_state)
            self.assertEqual(runner.repository_sha256(root), baseline_sha)

            (cache / "not-a-bytecode-source.txt").write_text(
                "must remain visible\n", encoding="utf-8"
            )
            delta = runner.repository_delta(baseline_state, runner.repository_state(root))
            self.assertEqual(
                [item["path"] for item in delta],
                ["__pycache__/not-a-bytecode-source.txt"],
            )

    def test_fixture_git_head_is_deterministic_and_host_config_isolated(self) -> None:
        runner = load_runner_module()
        fixture = {"README.md": "fixed\n"}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first"
            second = root / "second"
            with mock.patch.dict(
                runner.os.environ,
                {
                    "GIT_CONFIG_COUNT": "1",
                    "GIT_CONFIG_KEY_0": "commit.gpgsign",
                    "GIT_CONFIG_VALUE_0": "true",
                },
                clear=False,
            ):
                runner.write_fixture(first, fixture)
                runner.write_fixture(second, fixture)
            self.assertEqual(runner.git_head(first), runner.git_head(second))
            self.assertEqual(
                runner.repository_sha256(first), runner.repository_sha256(second)
            )
            self.assertEqual(
                runner.command_output(
                    ["git", "branch", "--show-current"], "fixture branch", first
                ),
                "main",
            )

    def test_initial_repository_fixture_is_rejected_before_any_write(self) -> None:
        runner = load_runner_module()
        invalid_fixtures = {
            "git-metadata": {".GIT./config": "[filter \"unsafe\"]\n"},
            "oversized-file": {
                "large.txt": "x" * (runner.MAX_REPOSITORY_FILE_BYTES + 1)
            },
            "too-many-files": {
                f"file-{index}.txt": "x"
                for index in range(runner.MAX_REPOSITORY_FILES + 1)
            },
            "oversized-total": {
                f"file-{index}.txt": "x" * runner.MAX_REPOSITORY_FILE_BYTES
                for index in range(
                    runner.MAX_REPOSITORY_TOTAL_BYTES
                    // runner.MAX_REPOSITORY_FILE_BYTES
                    + 1
                )
            },
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for name, fixture in invalid_fixtures.items():
                repository = root / name
                with self.subTest(name=name), self.assertRaisesRegex(
                    runner.TrialError, "initial repository fixture"
                ):
                    runner.write_fixture(repository, fixture)
                self.assertFalse(repository.exists())

    def test_catalog_rejects_unsafe_or_unbounded_initial_repository(self) -> None:
        runner = load_runner_module()
        catalog_path = ROOT / "evals" / "flow-transition-semantic-cases.json"
        base = json.loads(catalog_path.read_text(encoding="utf-8"))
        invalid_repositories = (
            {".git/config": "unsafe"},
            {"large.txt": "x" * (runner.MAX_REPOSITORY_FILE_BYTES + 1)},
            {
                f"file-{index}.txt": "x"
                for index in range(runner.MAX_REPOSITORY_FILES + 1)
            },
        )
        for repository in invalid_repositories:
            catalog = json.loads(json.dumps(base))
            catalog["cases"][0]["repository"] = repository
            with self.subTest(paths=list(repository)[:2]), self.assertRaisesRegex(
                runner.ActivationContractError, "initial repository fixture"
            ):
                runner.validate_transition_catalog(catalog)

    def test_focused_coverage_evaluates_only_selected_case(self) -> None:
        runner = load_runner_module()
        catalog_path = ROOT / "evals" / "flow-transition-semantic-cases.json"
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        case = catalog["cases"][0]
        repository_version = 0
        turns = []
        for number, turn in enumerate(case["turns"], 1):
            if turn["mutation"] == "repository":
                repository_version += 1
            turns.append(
                {
                    "turn": number,
                    "observed": turn["expected"],
                    "evidence": ["sanitized"],
                    "evidence_sha256": runner.sha256_text(f"evidence-{number}"),
                    "repository_sha256": runner.sha256_text(
                        f"repository-{repository_version}"
                    ),
                    "unmet_prerequisites": [],
                    "authority_violations": [],
                }
            )
        observations = {
            "schema_version": "flow.transition.observations.v1",
            "cases": [
                {
                    "id": case["id"],
                    "lineage_id": "lineage",
                    "initial_git_head_sha256": runner.sha256_text("git-head"),
                    "initial_repository_sha256": runner.sha256_text("repository-0"),
                    "turns": turns,
                }
            ],
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "observations.json"
            path.write_text(json.dumps(observations), encoding="utf-8")
            result = runner.run_transition_catalog(
                catalog_path, path, {case["id"]}
            )
        self.assertEqual(result["status"], "matched")
        self.assertEqual(result["cases"], 1)

    def test_qualification_requires_full_catalog_and_three_attempts(self) -> None:
        too_few = subprocess.run(
            [sys.executable, str(RUNNER), "--qualification", "--attempts", "2"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(too_few.returncode, 2)
        self.assertIn("at least 3 independent first attempts", too_few.stdout)

        partial = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "--qualification",
                "--attempts",
                "3",
                "--case",
                "TRANSITION-EVIDENCE-FRESHNESS",
            ],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(partial.returncode, 2)
        self.assertIn("requires the complete catalog", partial.stdout)

        planned = subprocess.run(
            [sys.executable, str(RUNNER), "--qualification", "--attempts", "3"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(planned.returncode, 0, planned.stderr or planned.stdout)
        result = json.loads(planned.stdout)
        self.assertTrue(result["qualification_requested"])
        self.assertTrue(result["qualification_eligible"])
        self.assertEqual(len(result["category_coverage"]), 9)
        self.assertTrue(all(count >= 3 for count in result["category_coverage"].values()))

    def test_catalog_with_underfilled_category_is_rejected(self) -> None:
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        category = "failure-isolation"
        kept = 0
        for case in catalog["cases"]:
            if category in case["categories"]:
                kept += 1
                if kept > 2:
                    case["categories"].remove(category)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "underfilled.json"
            path.write_text(json.dumps(catalog), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(RUNNER), "--catalog", str(path)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(completed.returncode, 2)
        self.assertIn("require at least 3 cases", completed.stdout)

    def test_readiness_change_label_requires_runner_owned_fixture_change(self) -> None:
        runner = load_runner_module()
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][2].pop("pre_turn_fixture")
        with self.assertRaisesRegex(
            runner.ActivationContractError, "runner-owned pre_turn_fixture"
        ):
            runner.validate_transition_catalog(catalog)

    def test_retry_label_requires_runner_owned_fixture_change(self) -> None:
        runner = load_runner_module()
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        turn = capability["turns"][2]
        turn.pop("pre_turn_fixture")
        turn["expected"].remove("readiness-fact-changed")
        with self.assertRaisesRegex(
            runner.ActivationContractError, "one-justified-retry"
        ):
            runner.validate_transition_catalog(catalog)

    def test_expected_unmet_requires_a_semantically_entailing_label(self) -> None:
        runner = load_runner_module()
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][0]["expected"].remove("blocked-claim")
        with self.assertRaisesRegex(
            runner.ActivationContractError, "expected_unmet requires"
        ):
            runner.validate_transition_catalog(catalog)

    def test_repository_mutation_requires_unique_existing_mutation_paths(self) -> None:
        runner = load_runner_module()
        catalog_path = ROOT / "evals" / "flow-transition-semantic-cases.json"
        for mutation in ("missing", "unknown", "none-with-paths"):
            with self.subTest(mutation=mutation):
                catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                turn = catalog["cases"][0]["turns"][1]
                if mutation == "missing":
                    turn.pop("mutation_paths")
                elif mutation == "unknown":
                    turn["mutation_paths"] = ["unknown.py"]
                else:
                    turn["mutation"] = "none"
                with self.assertRaisesRegex(
                    runner.ActivationContractError, "mutation_paths"
                ):
                    runner.validate_transition_catalog(catalog)

    def test_runtime_mutation_contract_requires_the_exact_path_set(self) -> None:
        runner = load_runner_module()
        exact_delta = [{"path": "target.py"}]
        runner.enforce_mutation_contract(
            case_id="CASE",
            turn_number=1,
            mutation="repository",
            mutation_paths=["target.py"],
            delta=exact_delta,
        )
        for delta in ([], exact_delta + [{"path": "extra.py"}]):
            with self.subTest(delta=delta), self.assertRaisesRegex(
                runner.TrialError, "exact contract"
            ):
                runner.enforce_mutation_contract(
                    case_id="CASE",
                    turn_number=1,
                    mutation="repository",
                    mutation_paths=["target.py"],
                    delta=delta,
                )
        with self.assertRaisesRegex(runner.TrialError, "changed repository bytes"):
            runner.enforce_mutation_contract(
                case_id="CASE",
                turn_number=1,
                mutation="none",
                mutation_paths=(),
                delta=exact_delta,
            )

    def test_unmet_entailing_label_requires_expected_unmet(self) -> None:
        runner = load_runner_module()
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][0]["expected_unmet"] = False
        with self.assertRaisesRegex(
            runner.ActivationContractError,
            "unmet-implying expected label requires expected_unmet",
        ):
            runner.validate_transition_catalog(catalog)

    def test_catalog_rejects_aggregate_pre_turn_fixture_over_runtime_bound(self) -> None:
        runner = load_runner_module()
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][2]["pre_turn_fixture"] = {
            f"tools/scanner-{index}.py": "x" * (60 * 1024)
            for index in range(5)
        }
        with self.assertRaisesRegex(
            runner.ActivationContractError, "assessment evidence byte bound"
        ):
            runner.validate_transition_catalog(catalog)

    def test_catalog_and_runtime_reject_serialized_fixture_delta_over_bound(self) -> None:
        runner = load_runner_module()
        fixture = {
            f"tools/scanner-{index}.py": "x" * (64 * 1024)
            for index in range(4)
        }
        catalog = json.loads(
            (ROOT / "evals" / "flow-transition-semantic-cases.json").read_text(
                encoding="utf-8"
            )
        )
        capability = next(
            case
            for case in catalog["cases"]
            if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
        )
        capability["turns"][2]["pre_turn_fixture"] = fixture
        with self.assertRaisesRegex(
            runner.ActivationContractError, "assessment evidence byte bound"
        ):
            runner.validate_transition_catalog(catalog)
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            with self.assertRaisesRegex(runner.TrialError, "assessment evidence byte bound"):
                runner.apply_pre_turn_fixture(repository, fixture)
            self.assertEqual(list(repository.iterdir()), [])

    def test_catalog_and_runtime_reject_shell_metacharacter_fixture_paths(self) -> None:
        runner = load_runner_module()
        for unsafe_path in (
            "-V",
            "--version",
            ".",
            "./tools/scanner.py",
            ".GIT/config",
            ".Git/HEAD",
            "tools/.GIT/x.py",
            ".git./config",
            "tools/$SCANNER.py",
            "tools/`scanner`.py",
            "tools/*.py",
            "tools/scanner\nnext.py",
            "tools/scanner>out.py",
            "tools/scanner path.py",
        ):
            with self.subTest(unsafe_path=unsafe_path):
                catalog = json.loads(
                    (
                        ROOT / "evals" / "flow-transition-semantic-cases.json"
                    ).read_text(encoding="utf-8")
                )
                capability = next(
                    case
                    for case in catalog["cases"]
                    if case["id"] == "TRANSITION-OPTIONAL-CAPABILITY-FAILURE"
                )
                capability["turns"][2]["pre_turn_fixture"] = {
                    unsafe_path: "print('unsafe path')\n"
                }
                with self.assertRaisesRegex(
                    runner.ActivationContractError, "pre_turn_fixture is invalid"
                ):
                    runner.validate_transition_catalog(catalog)
                with tempfile.TemporaryDirectory() as temporary:
                    repository = Path(temporary)
                    with self.assertRaisesRegex(runner.TrialError, "unsafe"):
                        runner.apply_pre_turn_fixture(
                            repository,
                            {unsafe_path: "print('unsafe path')\n"},
                        )
                    self.assertEqual(list(repository.iterdir()), [])

    def test_trajectory_rejects_python_option_in_place_of_fixture_execution(self) -> None:
        runner = load_runner_module()
        with self.assertRaises(runner.TrialError):
            runner.enforce_trajectory_contract(
                case_id="CASE",
                expected=["one-justified-retry"],
                trajectory=[
                    {
                        "event_type": "item.completed",
                        "item_type": "command_execution",
                        "command": "python3 -V",
                        "status": "completed",
                        "exit_code": 0,
                    }
                ],
                fixture_delta=[{"path": "-V"}],
            )


if __name__ == "__main__":
    unittest.main()
