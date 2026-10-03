#!/usr/bin/env python3
"""Read-only unified doctor contract tests."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
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
    def test_package_root_does_not_observe_ancestor_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            ancestor = Path(directory)
            subprocess.run(["git", "init", "-q"], cwd=ancestor, check=True)
            package = ancestor / "dist" / "dev-flow"
            package.mkdir(parents=True)
            payload = doctor._git_observation(package)
            self.assertEqual(payload["status"], "not-applicable", payload)
            self.assertEqual(payload["reason"], "selected-root-is-not-git-worktree-root")
            self.assertNotIn("head", payload)
            self.assertNotIn("exact_tags", payload)
            self.assertEqual(doctor.git_observation.probe_worktree(ancestor)["status"], "observed")

    def test_command_cannot_pass_when_git_observation_fails(self) -> None:
        for status in ("failed", "timeout", "unavailable"):
            with self.subTest(status=status):
                payload = {
                    "source": {"product_state": {"status": "valid"}, "git": {"status": status}},
                    "runtime": {"hook": {"packaging": "packaged"}},
                }
                with mock.patch.object(doctor, "diagnose", return_value=payload), mock.patch("builtins.print"):
                    code = doctor.command(argparse.Namespace())
                self.assertEqual(code, 2)

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
        def complete(command: list[str], **kwargs: object) -> subprocess.CompletedProcess:
            output = "true\n" if command[-1] == "--is-inside-work-tree" else ""
            if command[-1] == "--show-toplevel":
                output = str(Path(kwargs["cwd"]).resolve()) + "\n"
            return subprocess.CompletedProcess(command, 0, output if kwargs["text"] else b"", "")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".git").mkdir()
            with mock.patch.dict(os.environ, {
                "GIT_DIR": "/unrelated", "GIT_WORK_TREE": "/elsewhere",
                "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "core.fsmonitor",
                "GIT_CONFIG_VALUE_0": "untrusted-command", "GIT_OPTIONAL_LOCKS": "1",
            }), mock.patch.object(doctor.subprocess, "run", side_effect=complete) as run:
                payload = doctor._git_observation(root)
        self.assertEqual(payload["status"], "observed")
        self.assertEqual(run.call_count, 6)
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
            self.assertEqual(call.kwargs["env"].get("GIT_TERMINAL_PROMPT"), "0")
            self.assertEqual(call.kwargs["env"].get("GIT_PAGER"), "cat")
            self.assertEqual(call.kwargs["env"].get("LC_ALL"), "C")
            self.assertNotIn("GIT_DIR", call.kwargs["env"])
            self.assertNotIn("GIT_CONFIG_COUNT", call.kwargs["env"])
            self.assertEqual(call.kwargs["timeout"], 15)

    def test_git_observation_preserves_failures_at_discovery_and_status(self) -> None:
        probe = subprocess.CompletedProcess(["git"], 0, stdout="true\n", stderr="")
        success = subprocess.CompletedProcess(["git"], 0, stdout="", stderr="")
        failure = subprocess.CompletedProcess(["git"], 128, stdout=b"", stderr=b"fatal: permission denied\n")
        for operation in ("repository-probe", "worktree-status"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                top_level = subprocess.CompletedProcess(["git"], 0, str(Path(directory).resolve()) + "\n", "")
                responses = [failure] if operation == "repository-probe" else [probe, top_level, success, success, success, failure]
                with mock.patch.object(doctor.subprocess, "run", side_effect=responses):
                    payload = doctor._git_observation(Path(directory))
            self.assertEqual(payload["status"], "failed")
            self.assertEqual(payload["operation"], operation)
            self.assertEqual(payload["returncode"], 128)
            self.assertNotIn("permission denied", json.dumps(payload))

    def test_exact_root_binding_failure_or_timeout_cannot_become_non_git(self) -> None:
        failures = (
            (subprocess.CompletedProcess(["git"], 128, "", "fatal: permission denied\n"), "failed"),
            (subprocess.TimeoutExpired(["git"], 15), "timeout"),
            (FileNotFoundError(), "unavailable"),
            (subprocess.CompletedProcess(["git"], 0, "relative-root\n", ""), "failed"),
        )
        for failure, status in failures:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                probe = subprocess.CompletedProcess(["git"], 0, "true\n", "")
                with mock.patch.object(doctor.subprocess, "run", side_effect=[probe, failure]):
                    payload = doctor._git_observation(Path(directory))
            self.assertEqual(payload["status"], status, payload)
            self.assertEqual(payload["operation"], "repository-root")

    def test_git_observation_distinguishes_timeout_unavailable_and_non_git(self) -> None:
        for exception, status in ((subprocess.TimeoutExpired(["git"], 15), "timeout"), (FileNotFoundError(), "unavailable")):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                with mock.patch.object(doctor.subprocess, "run", side_effect=exception):
                    payload = doctor._git_observation(Path(directory))
            self.assertEqual(payload["status"], status)
        with tempfile.TemporaryDirectory() as directory:
            payload = doctor._git_observation(Path(directory))
        self.assertEqual(payload["status"], "not-applicable")

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
        self.assertEqual(payload["runtime"]["installed"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["effective"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["current_session"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["hook"]["packaging"], "packaged")
        self.assertEqual(payload["runtime"]["hook"]["activation"], "not_observed")
        self.assertFalse(payload["actions"]["cleanup_performed"])
        self.assertFalse(payload["actions"]["mutation_performed"])
        self.assertFalse(payload["local_state"]["cache"].get("group_names_exposed", False))
        self.assertIn("no live Hook", payload["claim_limit"])
        self.assertFalse(payload["recovery"]["automatic_actions_performed"])
        self.assertIn("new Codex chat", payload["recovery"]["steps"][0])

    def test_supplied_root_does_not_prove_current_session_loading(self) -> None:
        arguments = argparse.Namespace(
            plugin_root=ROOT, codex_home=None, codex_cli=None,
            loaded_plugin_root=ROOT, outcome_store=None,
            max_cache_files=20_000, skip_control_self_test=True,
        )
        with mock.patch.dict(os.environ, {}, clear=True):
            payload = doctor.diagnose(arguments)
        self.assertEqual(payload["runtime"]["loaded"]["status"], "not_observed")
        supplied = payload["runtime"]["supplied_root"]
        self.assertEqual(supplied["status"], "observed")
        self.assertEqual(supplied["source"], "explicit-supplied-path")
        self.assertTrue(supplied["matches_source_root"])
        self.assertTrue(supplied["matches_source_version"])

    def test_environment_identity_is_manifest_only_and_argument_takes_precedence(self) -> None:
        with mock.patch.dict(os.environ, {"DEV_FLOW_LOADED_PLUGIN_ROOT": str(ROOT)}):
            environment = doctor._supplied_identity(ROOT, None)
            explicit = doctor._supplied_identity(ROOT, ROOT)
        self.assertEqual(environment["source"], "environment-path")
        self.assertEqual(explicit["source"], "explicit-supplied-path")
        self.assertIn("manifest-only", environment["claim_limit"])

    def test_invalid_supplied_root_does_not_upgrade_current_session_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / ".codex-plugin"
            manifest.mkdir()
            (manifest / "plugin.json").symlink_to(ROOT / ".codex-plugin" / "plugin.json")
            identity = doctor._supplied_identity(ROOT, root)
        self.assertEqual(identity["status"], "unavailable")
        self.assertEqual(identity["source"], "explicit-supplied-path")

    def test_registry_installation_does_not_upgrade_current_session_identity(self) -> None:
        arguments = argparse.Namespace(
            plugin_root=ROOT, codex_home=None, codex_cli=Path("codex"),
            loaded_plugin_root=ROOT, outcome_store=None,
            max_cache_files=20_000, skip_control_self_test=True,
        )
        registry = {"status": "observed", "source": "operator-supplied-cli-registry", "registered": True, "entries": 1, "content": "registration-count-only"}
        with mock.patch.object(doctor, "_cli_registration", return_value=registry):
            payload = doctor.diagnose(arguments)
        self.assertTrue(payload["runtime"]["installed"]["installed"])
        self.assertEqual(payload["runtime"]["loaded"]["status"], "not_observed")
        self.assertEqual(payload["runtime"]["effective"]["status"], "not_observed")

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
            "source": "operator-supplied-cli-registry",
            "executable_trust": "not-verified",
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
