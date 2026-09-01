#!/usr/bin/env python3
"""Read-only unified doctor contract tests."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
import sys

sys.path.insert(0, str(SCRIPTS))
import runtime_doctor as doctor  # noqa: E402


class RuntimeDoctorTests(unittest.TestCase):
    def test_product_state_never_executes_target_validator(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "tools"
            tools.mkdir()
            marker = root / "target-validator-executed"
            (tools / "validate_product_state.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n"
                "def validate(root): return {'status': 'valid'}\n",
                encoding="utf-8",
            )
            payload = doctor._product_state(root)
        self.assertFalse(marker.exists())
        self.assertNotEqual(payload["status"], "valid")

    def test_control_self_test_never_executes_nonself_target(self) -> None:
        command = 'python3 "$PLUGIN_ROOT/hooks/data_security_hook.py"'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hooks = root / "hooks"
            hooks.mkdir()
            (hooks / "data_security_hook.py").write_text("# fixture\n", encoding="utf-8")
            (hooks / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            event: [{"hooks": [{"command": command}]}]
                            for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse")
                        }
                    }
                ),
                encoding="utf-8",
            )
            scripts = root / "skills" / "company-data-security" / "scripts"
            scripts.mkdir(parents=True)
            marker = root / "target-doctor-executed"
            (scripts / "doctor.py").write_text(
                "from pathlib import Path\n"
                f"Path({str(marker)!r}).write_text('executed')\n"
                "print('{}')\n",
                encoding="utf-8",
            )
            payload = doctor._hook_observation(root, run_self_test=True)
        self.assertFalse(marker.exists())
        self.assertEqual(payload["control_self_test"], {
            "status": "not-run",
            "reason": "target root is not the executing plugin root",
        })

    def test_git_observation_disables_repository_execution_hooks(self) -> None:
        completed = mock.Mock(returncode=0, stdout=b"", stderr=b"")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            with mock.patch.object(doctor.subprocess, "run", return_value=completed) as run:
                doctor._git_observation(root)
        self.assertGreaterEqual(run.call_count, 4)
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(command[:5], [
                "git",
                "-c",
                "core.fsmonitor=false",
                "-c",
                f"core.hooksPath={os.devnull}",
            ])
            self.assertEqual(call.kwargs["env"].get("GIT_OPTIONAL_LOCKS"), "0")

    def test_bounded_json_reader_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target.json"
            target.write_text("{}", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                doctor._read_json(root, "link.json")

    def test_bounded_json_reader_rejects_parent_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "secret.json").write_text('{"value": "outside"}', encoding="utf-8")
            (root / "linked").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(ValueError):
                doctor._read_json(root, "linked/secret.json")

    def test_repository_diagnosis_is_read_only_and_claim_limited(self) -> None:
        arguments = argparse.Namespace(
            plugin_root=ROOT,
            codex_home=None,
            codex_cli=None,
            loaded_plugin_root=None,
            outcome_store=None,
            max_cache_files=20_000,
            skip_control_self_test=True,
        )
        payload = doctor.diagnose(arguments)
        self.assertEqual(payload["source"]["product_state"]["status"], "valid")
        self.assertEqual(payload["runtime"]["cache"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["registration"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["hook"]["packaging"], "packaged")
        self.assertEqual(payload["runtime"]["hook"]["activation"], "not_observed")
        self.assertFalse(payload["actions"]["cleanup_performed"])
        self.assertFalse(payload["actions"]["mutation_performed"])
        self.assertFalse(payload["local_state"]["cache"].get("group_names_exposed", False))
        self.assertIn("no live Hook", payload["claim_limit"])

    def test_loaded_identity_requires_explicit_evidence(self) -> None:
        absent = doctor._loaded_identity(ROOT, None)
        present = doctor._loaded_identity(ROOT, ROOT)
        self.assertEqual(absent["status"], "not_observed")
        self.assertTrue(present["matches_source_root"])
        self.assertTrue(present["matches_source_version"])

    def test_cache_versions_do_not_claim_registration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            codex_home = Path(directory)
            (codex_home / "plugins" / "cache" / "dev-flow" / "dev-flow" / "2.0.0-rc.5").mkdir(parents=True)
            payload = doctor._cache_versions(codex_home)
        self.assertEqual(payload, {"status": "observed", "versions": ["2.0.0-rc.5"]})

    def test_cli_registration_is_explicit_and_count_only(self) -> None:
        absent = doctor._cli_registration(None)
        self.assertEqual(absent["status"], "not_observed")
        completed = mock.Mock(returncode=0, stdout='{"installed":[{"name":"dev-flow"}]}')
        with mock.patch.object(doctor.subprocess, "run", return_value=completed) as run:
            present = doctor._cli_registration(Path("codex"))
        self.assertEqual(present, {
            "status": "observed",
            "registered": True,
            "entries": 1,
            "content": "registration-count-only",
        })
        self.assertEqual(run.call_args.args[0], ["codex", "plugin", "list", "--marketplace", "dev-flow", "--json"])

        absent_completed = mock.Mock(returncode=0, stdout='{"installed":[]}')
        with mock.patch.object(doctor.subprocess, "run", return_value=absent_completed):
            unregistered = doctor._cli_registration(Path("codex"))
        self.assertEqual(unregistered["registered"], False)
        self.assertEqual(unregistered["entries"], 0)

    def test_cache_inventory_exposes_only_ranked_aggregate_groups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            secret_group = cache / "customer-acme-private"
            secret_group.mkdir()
            (secret_group / "entry.bin").write_bytes(b"private payload")
            payload = doctor._cache_inventory(cache, limit=10)
        serialized = json.dumps(payload, sort_keys=True)
        self.assertEqual(payload["status"], "observed")
        self.assertEqual(payload["groups"][0]["group"], "group-1")
        self.assertNotIn("customer-acme-private", serialized)
        self.assertNotIn("sha256:", serialized)

    def test_cache_inventory_rejects_parent_symlink_escape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "root"
            outside = Path(directory) / "outside"
            root.mkdir()
            outside.mkdir()
            (outside / "dev-flow").mkdir()
            (outside / "dev-flow" / "private.bin").write_bytes(b"private")
            (root / ".codex").symlink_to(outside, target_is_directory=True)
            payload = doctor._cache_inventory(
                root / ".codex" / "dev-flow",
                limit=10,
                containment_root=root,
            )
        self.assertEqual(payload, {
            "status": "unavailable",
            "reason": "cache root is not contained in target root",
        })

    def test_cache_inventory_has_an_independent_directory_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            for name in ("one", "two", "three"):
                (cache / name).mkdir()
            with mock.patch.object(doctor, "MAX_CACHE_DIRECTORIES", 2):
                payload = doctor._cache_inventory(cache, limit=100)
        self.assertEqual(payload["status"], "partial")
        self.assertEqual(payload["directories"], 2)
        self.assertTrue(payload["incomplete"])

    def test_hook_packaging_requires_one_registration_per_event(self) -> None:
        command = 'python3 "$PLUGIN_ROOT/hooks/data_security_hook.py"'
        handler = {"command": command}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hooks = root / "hooks"
            hooks.mkdir()
            (hooks / "data_security_hook.py").write_text("# fixture\n", encoding="utf-8")
            (hooks / "hooks.json").write_text(
                json.dumps(
                    {
                        "hooks": {
                            "UserPromptSubmit": [{"hooks": [handler, handler]}],
                            "PreToolUse": [{"hooks": [handler]}],
                            "PostToolUse": [],
                        }
                    }
                ),
                encoding="utf-8",
            )
            payload = doctor._hook_observation(root, run_self_test=False)
        self.assertEqual(payload["packaging"], "invalid")


if __name__ == "__main__":
    unittest.main()
