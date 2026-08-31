#!/usr/bin/env python3
"""Privacy and integrity tests for opt-in local outcome observations."""

from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
FLOW = SCRIPTS / "dev-flow.py"

sys.path.insert(0, str(SCRIPTS))
import outcome_observation as outcomes  # noqa: E402


def record_args(**overrides: object) -> argparse.Namespace:
    values: dict[str, object] = {
        "condition": "dev-flow",
        "task_shape": "bounded",
        "outcome": "completed",
        "verification": "passed",
        "first_valid_patch": "yes",
        **{field: 0 for field in outcomes.COUNTER_FIELDS},
        **{field: None for field in outcomes.OPTIONAL_FIELDS},
    }
    values.update(overrides)
    return argparse.Namespace(**values)


class OutcomeObservationTests(unittest.TestCase):
    def test_private_append_and_summary_store_no_content_or_score(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "private" / "outcomes.jsonl"
            record = outcomes.build_record(record_args(corrections=1, route_calls=2))
            outcomes.append_record(store, record)
            observed = outcomes.read_records(store)
            summary = outcomes.summarize(observed)
            mode = stat.S_IMODE(store.stat().st_mode) if os.name != "nt" else 0o600
        self.assertEqual(mode, 0o600)
        self.assertEqual(summary["records"], 1)
        self.assertEqual(summary["counter_totals"]["corrections"], 1)
        self.assertNotIn("score", summary)
        serialized = json.dumps(observed)
        for forbidden in ("prompt", "title", "path", "session", "user", "agent", "note", "source"):
            self.assertNotIn(f'"{forbidden}"', serialized)

    def test_unknown_free_form_fields_and_broad_permissions_are_rejected(self) -> None:
        record = outcomes.build_record(record_args())
        record["note"] = "free form is forbidden"
        with self.assertRaisesRegex(outcomes.OutcomeError, "unknown or missing"):
            outcomes.validate_record(record)
        if os.name != "nt":
            with tempfile.TemporaryDirectory() as directory:
                store = Path(directory) / "outcomes.jsonl"
                store.write_text("", encoding="utf-8")
                store.chmod(0o644)
                with self.assertRaisesRegex(outcomes.OutcomeError, "0600"):
                    outcomes.read_records(store)

    def test_cli_rejects_final_symlink_and_does_not_mutate_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.jsonl"
            target.touch(mode=0o600)
            link = root / "link.jsonl"
            try:
                link.symlink_to(target)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(FLOW),
                    "outcomes",
                    "--store",
                    str(link),
                    "record",
                    "--condition",
                    "dev-flow",
                    "--task-shape",
                    "bounded",
                    "--outcome",
                    "completed",
                    "--verification",
                    "passed",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            target_size = target.stat().st_size
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(target_size, 0)

    def test_default_store_rejects_repository_symlink_ancestor(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            try:
                (root / ".codex").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            completed = subprocess.run(
                [
                    sys.executable,
                    str(FLOW),
                    "outcomes",
                    "record",
                    "--condition",
                    "dev-flow",
                    "--task-shape",
                    "bounded",
                    "--outcome",
                    "completed",
                    "--verification",
                    "passed",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            escaped = outside / "dev-flow" / "outcomes-v1.jsonl"
        self.assertEqual(completed.returncode, 2)
        self.assertFalse(escaped.exists())

    def test_append_rejects_an_existing_invalid_store(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "outcomes.jsonl"
            store.write_text("not-json\n", encoding="utf-8")
            store.chmod(0o600)
            with self.assertRaisesRegex(outcomes.OutcomeError, "existing line 1"):
                outcomes.append_record(store, outcomes.build_record(record_args()))

    def test_missing_summary_is_empty_and_does_not_create_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "missing.jsonl"
            records = outcomes.read_records(store, missing_ok=True)
            summary = outcomes.summarize(records)
            self.assertFalse(store.exists())
        self.assertEqual(summary["records"], 0)
        self.assertEqual(summary["distributions"]["outcome"], {})

    def test_concurrent_process_appends_remain_complete_records(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "outcomes.jsonl"
            command = [
                sys.executable,
                str(FLOW),
                "outcomes",
                "--store",
                str(store),
                "record",
                "--condition",
                "dev-flow",
                "--task-shape",
                "bounded",
                "--outcome",
                "completed",
                "--verification",
                "passed",
            ]
            processes = [
                subprocess.Popen(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                for _ in range(8)
            ]
            completed = [process.communicate(timeout=20) + (process.returncode,) for process in processes]
            records = outcomes.read_records(store)
        self.assertTrue(all(code == 0 for _, _, code in completed), completed)
        self.assertEqual(len(records), 8)

    def test_append_cannot_cross_store_size_bound(self) -> None:
        record = outcomes.build_record(record_args())
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "outcomes.jsonl"
            with mock.patch.object(outcomes, "MAX_FILE_BYTES", 1):
                with self.assertRaisesRegex(outcomes.OutcomeError, "would exceed"):
                    outcomes.append_record(store, record)
            self.assertEqual(store.stat().st_size, 0)

    def test_append_cannot_cross_record_count_bound(self) -> None:
        record = outcomes.build_record(record_args())
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "outcomes.jsonl"
            with mock.patch.object(outcomes, "MAX_RECORDS", 1):
                outcomes.append_record(store, record)
                with self.assertRaisesRegex(outcomes.OutcomeError, "record count"):
                    outcomes.append_record(store, record)
            self.assertEqual(len(outcomes.read_records(store)), 1)


if __name__ == "__main__":
    unittest.main()
