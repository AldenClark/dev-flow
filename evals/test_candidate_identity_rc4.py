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
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md", "CHANGELOG.md"]
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
        frozen = {
            "semantic_runtime": {"sha256": "sha256:semantic"},
            "qualification_execution": {"sha256": "sha256:execution"},
        }
        valid = candidate_identity.verify_frozen(
            frozen,
            frozen,
            ["docs/workstreams/dev-flow-2.0-rc.4/audit.md"],
        )
        self.assertEqual(valid["status"], "valid")
        changed = {
            "semantic_runtime": {"sha256": "sha256:changed"},
            "qualification_execution": {"sha256": "sha256:execution"},
        }
        invalid = candidate_identity.verify_frozen(
            frozen, changed, ["skills/dev-flow/SKILL.md"]
        )
        self.assertEqual(invalid["status"], "invalid")
        self.assertFalse(invalid["semantic_runtime_unchanged"])
        self.assertEqual(invalid["rejected_paths"], ["skills/dev-flow/SKILL.md"])


if __name__ == "__main__":
    unittest.main()
