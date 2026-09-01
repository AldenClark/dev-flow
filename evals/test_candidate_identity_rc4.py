from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from evals import candidate_identity


ROOT = Path(__file__).resolve().parents[1]
COPY_IGNORE = shutil.ignore_patterns(".git", ".codex", "tmp", "__pycache__", "*.pyc")


class CandidateIdentityTests(unittest.TestCase):
    def test_semantic_runtime_excludes_evidence_docs_but_includes_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(ROOT, root, ignore=COPY_IGNORE)
            root = root.resolve()
            first = candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"]
            audit = root / "docs" / "workstreams" / "dev-flow-2.0-rc.4" / "audit.md"
            audit.write_text(audit.read_text(encoding="utf-8") + "\nEvidence only.\n", encoding="utf-8")
            self.assertEqual(first, candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"])
            skill = root / "skills" / "dev-flow" / "SKILL.md"
            skill.write_text(skill.read_text(encoding="utf-8") + "\nRuntime change.\n", encoding="utf-8")
            self.assertNotEqual(first, candidate_identity.hash_files(root, candidate_identity.semantic_runtime_files(root))["sha256"])

    def test_qualification_identity_includes_transitive_bench_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            shutil.copytree(ROOT, root, ignore=COPY_IGNORE)
            root = root.resolve()
            runner = root / "benchmarks" / "dev_flow_bench_executor.py"
            catalog = root / "benchmarks" / "cases" / "dev-flow-cases.json"
            files = candidate_identity.qualification_dependency_files(root, runner, catalog)
            relative = {path.relative_to(root).as_posix() for path in files}
            self.assertIn("benchmarks/dev_flow_bench_executor.py", relative)
            self.assertIn("benchmarks/dev_flow_bench_fixture_mcp.py", relative)
            self.assertIn("benchmarks/dev_flow_bench_contracts.py", relative)
            first = candidate_identity.hash_files(root, files)["sha256"]
            helper = root / "benchmarks" / "dev_flow_bench_contracts.py"
            helper.write_text(helper.read_text(encoding="utf-8") + "\n# changed\n", encoding="utf-8")
            second = candidate_identity.hash_files(
                root,
                candidate_identity.qualification_dependency_files(root, runner, catalog),
            )["sha256"]
            self.assertNotEqual(first, second)
            fixture = root / "benchmarks" / "dev_flow_bench_fixture_mcp.py"
            fixture.write_text(
                fixture.read_text(encoding="utf-8") + "\n# fixture changed\n",
                encoding="utf-8",
            )
            third = candidate_identity.hash_files(
                root,
                candidate_identity.qualification_dependency_files(root, runner, catalog),
            )["sha256"]
            self.assertNotEqual(second, third)

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
            "runner": ROOT / "benchmarks" / "dev_flow_bench_executor.py",
            "catalog": ROOT / "benchmarks" / "cases" / "dev-flow-cases.json",
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
                ignore=COPY_IGNORE,
            )
            catalog = base / "external-catalog.json"
            shutil.copy2(ROOT / "benchmarks" / "cases" / "dev-flow-cases.json", catalog)
            identities = candidate_identity.build_identities(
                candidate,
                runner=ROOT / "benchmarks" / "dev_flow_bench_executor.py",
                catalog=catalog,
                codex_executable_sha256="sha256:" + "0" * 64,
                model="synthetic-model",
                reasoning_effort="high",
                environment_policy="inherit=none",
                execution_policy={"attempts": 3},
            )
        files = identities["qualification_execution"]["files"]
        self.assertIn("tool/benchmarks/dev_flow_bench_executor.py", files)
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
        execution_sha = "sha256:" + candidate_identity.hashlib.sha256(
            candidate_identity.json.dumps(
                execution_inputs, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        frozen = {
            "schema": candidate_identity.IDENTITY_SCHEMA,
            "semantic_runtime": {
                "sha256": "sha256:" + "1" * 64,
                "files": ["skills/example/SKILL.md"],
                "file_count": 1,
                "total_bytes": 1,
            },
            "qualification_execution": {
                "sha256": execution_sha,
                "files": ["tool/benchmarks/dev_flow_bench_executor.py"],
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
        execution_sha = "sha256:" + candidate_identity.hashlib.sha256(
            candidate_identity.json.dumps(
                execution_inputs, sort_keys=True, separators=(",", ":")
            ).encode("utf-8")
        ).hexdigest()
        valid = {
            "schema": candidate_identity.IDENTITY_SCHEMA,
            "semantic_runtime": {
                "sha256": "sha256:" + "1" * 64,
                "files": ["skills/example/SKILL.md"],
                "file_count": 1,
                "total_bytes": 1,
            },
            "qualification_execution": {
                "sha256": execution_sha,
                "files": ["tool/benchmarks/dev_flow_bench_executor.py"],
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

    def test_frozen_identity_verifier_rejects_structural_tampering_with_stale_digest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            runner = root / "benchmarks" / "dev_flow_bench_executor.py"
            helper = root / "benchmarks" / "dev_flow_bench_contracts.py"
            catalog = root / "catalog.json"
            semantic = root / "skills" / "example" / "SKILL.md"
            runner.parent.mkdir(parents=True)
            helper.parent.mkdir(parents=True, exist_ok=True)
            semantic.parent.mkdir(parents=True)
            runner.write_text("import dev_flow_bench_contracts\n", encoding="utf-8")
            helper.write_text("VALUE = 1\n", encoding="utf-8")
            catalog.write_text("{}\n", encoding="utf-8")
            semantic.write_text("# Example\n", encoding="utf-8")
            (root / ".codex-plugin").mkdir()
            (root / ".codex-plugin" / "plugin.json").write_text("{}\n", encoding="utf-8")
            (root / "hooks").mkdir()
            (root / "governance").mkdir()
            valid = candidate_identity.build_identities(
                root,
                runner=runner,
                catalog=catalog,
                codex_executable_sha256="sha256:" + "c" * 64,
                model="gpt-test",
                reasoning_effort="medium",
                environment_policy="isolated",
                execution_policy={"attempts": 3},
            )
        stale_execution = candidate_identity.json.loads(
            candidate_identity.json.dumps(valid)
        )
        stale_execution["qualification_execution"]["execution_inputs"]["model"] = "tampered"
        result = candidate_identity.verify_frozen(
            valid,
            stale_execution,
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"],
        )
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["qualification_execution_unchanged"])
        stale_manifest = candidate_identity.json.loads(candidate_identity.json.dumps(valid))
        stale_manifest["semantic_runtime"]["files"][0] = "skills/tampered/SKILL.md"
        result = candidate_identity.verify_frozen(
            valid,
            stale_manifest,
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"],
        )
        self.assertEqual(result["status"], "invalid")
        self.assertFalse(result["semantic_runtime_unchanged"])
if __name__ == "__main__":
    unittest.main()
