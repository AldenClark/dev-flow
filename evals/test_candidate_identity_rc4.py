from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from evals import candidate_identity


ROOT = Path(__file__).resolve().parents[1]


class CandidateIdentityTests(unittest.TestCase):
    def test_semantic_runtime_excludes_evidence_docs_but_includes_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            root = root.resolve()
            first = candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"]
            audit = root / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "audit.md"
            audit.write_text(audit.read_text(encoding="utf-8") + "\nEvidence only.\n", encoding="utf-8")
            self.assertEqual(first, candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"])
            skill = root / "skills" / "dev-flow" / "SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nRuntime change.\n", encoding="utf-8")
            self.assertNotEqual(first, candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"])

    def test_qualification_identity_includes_transitive_flow_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
            root = root.resolve()
            runner = root / "evals" / "run_transition_trials.py"
            catalog = root / "evals" / "flow-transition-semantic-cases.json"
            files = candidate_identity.qualification_dependency_files(root, runner, catalog)
            relative = {path.relative_to(root).as_posix() for path in files}
            self.assertIn("evals/run_transition_trials.py", relative)
            self.assertIn("skills/dev-flow/scripts/flow_metrics.py", relative)
            first = candidate_identity.hash_files(root, files)["sha256"]
            helper = root / "skills" / "dev-flow" / "scripts" / "flow_metrics.py"
            helper.write_text(helper.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
            second = candidate_identity.hash_files(
                root,
                candidate_identity.qualification_dependency_files(root, runner, catalog),
            )["sha256"]
            self.assertNotEqual(first, second)

    def test_evidence_allowlist_rejects_runtime_and_accepts_release_records(self) -> None:
        allowed, rejected = candidate_identity.evidence_only_changes(
            [
                "docs/workstreams/dev-flow-2.0-rc.4/audit.md",
                "docs/workstreams/dev-flow-2.0-rc.4/progress.md",
                "CHANGELOG.md",
            ]
        )
        self.assertTrue(allowed)
        self.assertEqual(rejected, [])
        allowed, rejected = candidate_identity.evidence_only_changes(
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md", "skills/dev-flow/SKILL.md"]
        )
        self.assertFalse(allowed)
        self.assertEqual(rejected, ["skills/dev-flow/SKILL.md"])
        allowed, rejected = candidate_identity.evidence_only_changes(
            ["CHANGELOG.md.untrusted", "docs/releasing.md.backup"]
        )
        self.assertFalse(allowed)
        self.assertEqual(rejected, ["CHANGELOG.md.untrusted", "docs/releasing.md.backup"])
        policy_paths = [
            "docs/releasing.md",
            "docs/workstreams/dev-flow-2.0-rc.4/requirements.md",
            "docs/workstreams/dev-flow-2.0-rc.4/design.md",
            "docs/workstreams/dev-flow-2.0-rc.4/decisions.md",
            "docs/workstreams/dev-flow-2.0-rc.4/implementation.md",
        ]
        allowed, rejected = candidate_identity.evidence_only_changes(policy_paths)
        self.assertFalse(allowed)
        self.assertEqual(rejected, sorted(policy_paths))

    def test_execution_policy_changes_qualification_identity(self) -> None:
        common = {
            "runner": ROOT / "evals" / "run_transition_trials.py",
            "catalog": ROOT / "evals" / "flow-transition-semantic-cases.json",
            "codex_executable_sha256": "sha256:" + "0" * 64,
            "model": "synthetic-model",
            "reasoning_effort": "high",
            "environment_policy": "inherit=none",
        }
        first = candidate_identity.build_identities(
            ROOT, **common, execution_policy={"attempts": 3, "maximum_total_tokens": 100}
        )
        second = candidate_identity.build_identities(
            ROOT, **common, execution_policy={"attempts": 3, "maximum_total_tokens": 101}
        )
        self.assertNotEqual(
            first["qualification_execution"]["sha256"],
            second["qualification_execution"]["sha256"],
        )

    def test_external_candidate_and_catalog_have_separate_identity_domains(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            candidate = base / "candidate"
            shutil.copytree(
                ROOT,
                candidate,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
            )
            catalog = base / "external-catalog.json"
            shutil.copy2(ROOT / "evals" / "flow-transition-semantic-cases.json", catalog)
            identities = candidate_identity.build_identities(
                candidate,
                runner=ROOT / "evals" / "run_transition_trials.py",
                catalog=catalog,
                codex_executable_sha256="sha256:" + "0" * 64,
                model="synthetic-model",
                reasoning_effort="high",
                environment_policy="inherit=none",
                execution_policy={"attempts": 3},
            )
        files = identities["qualification_execution"]["files"]
        self.assertIn("tool/evals/run_transition_trials.py", files)
        self.assertIn("catalog/input.json", files)

    def test_frozen_identity_verifier_requires_both_identities_and_allowlist(self) -> None:
        execution_inputs = {
            "repository_dependencies_sha256": "sha256:" + "4" * 64,
            "codex_executable_sha256": "sha256:" + "5" * 64,
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
            "environment_policy": "isolated",
            "python_implementation": "CPython",
            "python_version": "3.14.7",
            "platform": "darwin",
            "execution_policy": {},
        }
        frozen = {
            "schema": candidate_identity.IDENTITY_SCHEMA,
            "semantic_runtime": {
                "sha256": "sha256:" + "1" * 64,
                "files": ["skills/example/SKILL.md"],
                "file_count": 1,
                "total_bytes": 1,
            },
            "qualification_execution": {
                "sha256": "sha256:" + "2" * 64,
                "files": ["tool/evals/run_transition_trials.py"],
                "file_count": 1,
                "total_bytes": 1,
                "execution_inputs": execution_inputs,
            },
        }
        valid = candidate_identity.verify_frozen(
            frozen,
            frozen,
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"],
        )
        self.assertEqual(valid["status"], "valid")
        changed = {
            **frozen,
            "semantic_runtime": {
                **frozen["semantic_runtime"],
                "sha256": "sha256:" + "3" * 64,
            },
        }
        invalid = candidate_identity.verify_frozen(
            frozen, changed, ["skills/dev-flow/SKILL.md"]
        )
        self.assertEqual(invalid["status"], "invalid")
        self.assertFalse(invalid["semantic_runtime_unchanged"])
        self.assertEqual(invalid["rejected_paths"], ["skills/dev-flow/SKILL.md"])

    def test_frozen_identity_verifier_fails_closed_on_missing_or_malformed_identity(self) -> None:
        execution_inputs = {
            "repository_dependencies_sha256": "sha256:" + "4" * 64,
            "codex_executable_sha256": "sha256:" + "5" * 64,
            "model": "gpt-5.6-terra",
            "reasoning_effort": "medium",
            "environment_policy": "isolated",
            "python_implementation": "CPython",
            "python_version": "3.14.7",
            "platform": "darwin",
            "execution_policy": {},
        }
        valid = {
            "schema": candidate_identity.IDENTITY_SCHEMA,
            "semantic_runtime": {
                "sha256": "sha256:" + "1" * 64,
                "files": ["skills/example/SKILL.md"],
                "file_count": 1,
                "total_bytes": 1,
            },
            "qualification_execution": {
                "sha256": "sha256:" + "2" * 64,
                "files": ["tool/evals/run_transition_trials.py"],
                "file_count": 1,
                "total_bytes": 1,
                "execution_inputs": execution_inputs,
            },
        }
        malformed = [
            {},
            {"schema": candidate_identity.IDENTITY_SCHEMA},
            {
                "schema": "wrong",
                "semantic_runtime": valid["semantic_runtime"],
                "qualification_execution": valid["qualification_execution"],
            },
            {
                **valid,
                "semantic_runtime": {
                    **valid["semantic_runtime"],
                    "sha256": "not-a-digest",
                },
            },
            {
                "schema": candidate_identity.IDENTITY_SCHEMA,
                "semantic_runtime": {"sha256": "sha256:" + "1" * 64},
                "qualification_execution": valid["qualification_execution"],
            },
            {
                **valid,
                "qualification_execution": {
                    **valid["qualification_execution"],
                    "execution_inputs": {},
                },
            },
        ]
        both_missing = candidate_identity.verify_frozen(
            {}, {}, ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"]
        )
        self.assertEqual(both_missing["status"], "invalid")
        self.assertFalse(both_missing["semantic_runtime_unchanged"])
        self.assertFalse(both_missing["qualification_execution_unchanged"])
        for identity in malformed:
            with self.subTest(identity=identity):
                result = candidate_identity.verify_frozen(
                    identity, valid, ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"]
                )
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(result["errors"])
                result = candidate_identity.verify_frozen(
                    valid, identity, ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"]
                )
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(result["errors"])


if __name__ == "__main__":
    unittest.main()
