#!/usr/bin/env python3
"""Deterministic tests for the bounded Codex model adapter."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

import codex_model_adapter as adapter  # noqa: E402


class CodexModelAdapterTests(unittest.TestCase):
    def test_usage_parser_uses_latest_complete_turn(self) -> None:
        events = "\n".join(
            (
                json.dumps({"type": "turn.completed", "usage": {"input_tokens": 10, "output_tokens": 5}}),
                "not-json",
                json.dumps({"type": "turn.completed", "usage": {"total_tokens": 42}}),
            )
        )
        self.assertEqual(adapter.usage_tokens(events), 42)

    def test_tool_event_summary_is_redacted_and_detects_every_prohibited_category(self) -> None:
        events = "\n".join(
            (
                json.dumps({"type": "item.completed", "item": {"type": "command_execution", "command": "secret"}}),
                json.dumps({"type": "item.started", "item": {"type": "web_search", "query": "private"}}),
                json.dumps({"type": "item.completed", "item": {"type": "computer_tool_call"}}),
                json.dumps({"type": "item.completed", "item": {"type": "mcp_tool_call", "name": "private-server"}}),
            )
        )
        summary = adapter.tool_event_summary(events)
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["invalid_jsonl_lines"], 0)
        self.assertEqual(set(summary["categories"]), {"shell", "browser", "computer", "apps_or_other"})
        self.assertNotIn("secret", json.dumps(summary))
        self.assertNotIn("private-server", json.dumps(summary))

        malformed = adapter.tool_event_summary("not-json\n[]\n")
        self.assertEqual(malformed["invalid_jsonl_lines"], 2)

    def test_executor_prompt_blinds_condition_labels_and_embeds_source(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            prompt = adapter.executor_prompt(
                {
                    "case_id": "PAIR-PROFILE-PRECEDENCE",
                    "fixture": "ordinary repository instructions",
                    "condition": "with-capabilities",
                    "capabilities": ["repo-context"],
                    "capability_sources": {"repo-context": "---\nname: repo-context\n---\nBounded source."},
                },
                Path(temp) / "artifacts",
            )
        self.assertIn("name: repo-context", prompt)
        self.assertNotIn("with-capabilities", prompt)
        self.assertIn("do not mention capability names", prompt)
        self.assertIn("do not mark it blocked", prompt)

    def test_capability_material_uses_only_the_supplied_snapshot(self) -> None:
        material = adapter.capability_material(
            {"capabilities": ["repo-context"], "capability_sources": {"repo-context": "IMMUTABLE\n"}}
        )
        self.assertIn("IMMUTABLE", material)
        with self.assertRaisesRegex(adapter.AdapterError, "exactly match"):
            adapter.capability_material(
                {"capabilities": ["repo-context"], "capability_sources": {"other": "wrong"}}
            )

    def test_normalize_owns_identity_artifact_and_observed_usage(self) -> None:
        result = {
            "case_id": "wrong",
            "attempt": 9,
            "artifact_root": "/wrong",
            "claimed_outcome": "completed",
            "actions": ["inspect"],
            "evidence": ["fixture"],
            "interactions": {"user_questions": 0, "user_corrections": 0, "reminders": 0, "blocks": 0},
            "usage": {"tokens": None, "elapsed_seconds": None, "cost": None},
        }
        normalized = adapter.normalize(
            "executor",
            result,
            {"case_id": "PAIR-1"},
            Path("/bounded/artifacts"),
            1.25,
            42,
        )
        self.assertEqual(normalized["case_id"], "PAIR-1")
        self.assertEqual(normalized["attempt"], 1)
        self.assertEqual(normalized["artifact_root"], str(Path("/bounded/artifacts")))
        self.assertEqual(normalized["usage"], {"tokens": 42, "elapsed_seconds": 1.25, "cost": None})

    @mock.patch("codex_model_adapter.shutil.which", return_value="/usr/local/bin/codex")
    def test_command_disables_mutating_or_context_leaking_surfaces(self, _which: mock.Mock) -> None:
        command = adapter.codex_command("grader", "gpt-5.6-sol", "medium", Path("/tmp/result.json"))
        rendered = " ".join(command)
        for token in adapter.DISABLED_FEATURES:
            self.assertIn(token, command)
        self.assertIn("read-only", command)
        self.assertIn("--ephemeral", command)
        self.assertIn("--ignore-user-config", command)
        self.assertIn('model_reasoning_effort="medium"', command)
        self.assertNotIn("dangerously-bypass", rendered)

    def test_usage_receipt_is_minimal_and_records_unavailable_cost(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / adapter.USAGE_RECEIPT
            adapter.write_usage_receipt(
                path,
                role="grader",
                model="gpt-5.6-sol",
                effort="medium",
                tokens=123,
                elapsed=1.5,
                exit_code=0,
                tool_events={
                    "policy": "fail-on-any-tool-event",
                    "total": 0,
                    "categories": {},
                    "invalid_jsonl_lines": 0,
                },
            )
            receipt = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(receipt["tokens"], 123)
        self.assertIsNone(receipt["monetary_cost"])
        self.assertEqual(receipt["tool_events"]["total"], 0)
        self.assertNotIn("prompt", receipt)
        self.assertNotIn("response", receipt)

    def test_environment_is_allowlisted_and_uses_private_temp(self) -> None:
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(
            adapter.os.environ,
            {"PATH": "/bin", "CODEX_HOME": "/auth", "UNRELATED_SECRET": "must-not-pass"},
            clear=True,
        ):
            environment = adapter.codex_environment(Path(temp))
        self.assertEqual(environment["PATH"], "/bin")
        self.assertEqual(environment["CODEX_HOME"], "/auth")
        self.assertNotIn("UNRELATED_SECRET", environment)
        self.assertTrue(environment["TMPDIR"].endswith(".codex-eval-tmp"))


if __name__ == "__main__":
    unittest.main()
