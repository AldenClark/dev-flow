from __future__ import annotations

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

import knowledge_system as ks  # noqa: E402


SCRIPT = SCRIPTS / "knowledge_system.py"
DEV_FLOW_SCRIPT = SCRIPTS / "dev_flow.py"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def valid_manifest(change_id: str, *, dossier_format: str = "single") -> dict[str, object]:
    documents = {"change": "change.md"}
    if dossier_format == "governed":
        documents = {
            "requirements": "requirements.md",
            "design": "design.md",
            "execution": "execution.md",
            "verification": "verification.md",
        }
    return {
        "schema_version": "1.0",
        "change_id": change_id,
        "status": "accepted",
        "format": dossier_format,
        "documents": documents,
        "traceability": {
            "acceptance_criteria": ["AC-1"],
            "scope": ["SC-D1", "SC-P1", "SC-L1"],
            "verification_obligations": ["VO-1"],
        },
        "tests": {
            "black_box": {
                "status": "passed",
                "rationale": "Public behavior was exercised at the command boundary.",
                "evidence": ["black-box invocation returned the expected result"],
            },
            "white_box": {
                "status": "passed",
                "rationale": "Branch and error-state behavior were exercised directly.",
                "evidence": ["branch and error-path unit checks passed"],
            },
        },
        "knowledge": {
            "impact": "update",
            "disposition": "promoted",
            "rationale": "The verified reusable contract changed.",
            "promotion_links": ["../../project/truth.md"],
        },
        "related_changes": [],
    }


def make_valid_repository(
    root: Path,
    *,
    project_root: str = "docs/project",
    changes_root: str = "docs/changes",
    change_id: str = "safe-change",
    dossier_format: str = "single",
) -> tuple[Path, Path, Path]:
    project = root / project_root
    changes = root / changes_root
    dossier = changes / change_id
    project.mkdir(parents=True)
    dossier.mkdir(parents=True)
    (root / ".gitignore").write_text(".codex/dev-flow/\n", encoding="utf-8")
    write_json(
        project / "catalog.json",
        {
            "schema_version": "1.0",
            "documents": [
                {"knowledge_id": "KT-RUNTIME", "path": "truth.md", "status": "current"}
            ],
        },
    )
    (project / "truth.md").write_text(
        "# Current runtime truth\n\n[Knowledge catalog](./catalog.json)\n\n"
        "The command boundary owns the verified runtime contract.\n",
        encoding="utf-8",
    )
    manifest = valid_manifest(change_id, dossier_format=dossier_format)
    # Promotion paths are relative to the dossier and depend on root depth.
    relative_truth = Path(os.path.relpath(project / "truth.md", start=dossier)).as_posix()
    manifest["knowledge"]["promotion_links"] = [relative_truth]
    write_json(dossier / "manifest.json", manifest)
    if dossier_format == "single":
        (dossier / "change.md").write_text(
            "# Safe change\n\n[Manifest](./manifest.json)\n\n"
            f"[Promoted current truth]({relative_truth})\n\n"
            "AC-1, SC-D1, SC-P1, SC-L1, and VO-1 are closed by fresh evidence.\n",
            encoding="utf-8",
        )
    else:
        for role in ("requirements", "design", "execution", "verification"):
            (dossier / f"{role}.md").write_text(
                f"# {role.title()}\n\n[Manifest](./manifest.json)\n\n"
                "The accepted record retains its concrete decision and evidence.\n",
                encoding="utf-8",
            )
    return project, changes, dossier


def bind_governed_authority(dossier: Path) -> None:
    """Opt a governed fixture into exact-byte and identifier authority binding."""
    requirements = dossier / "requirements.md"
    design = dossier / "design.md"
    requirements.write_text(
        "# Requirements\n\n[Manifest](./manifest.json)\n\n"
        "- AC-1: The observable command contract remains stable.\n",
        encoding="utf-8",
    )
    design.write_text(
        "# Design\n\n[Manifest](./manifest.json)\n\n"
        "- SC-D1: Change the direct implementation.\n"
        "- SC-P1: Preserve unrelated behavior.\n"
        "- SC-L1: Do not perform delivery actions.\n"
        "- VO-1: Exercise the observable and internal oracles.\n",
        encoding="utf-8",
    )
    manifest_path = dossier / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["authority_binding"] = {
        "schema_version": "1.0",
        "change_id": manifest["change_id"],
        "requirements": {
            "path": "requirements.md",
            "sha256": "sha256:" + hashlib.sha256(requirements.read_bytes()).hexdigest(),
        },
        "design": {
            "path": "design.md",
            "sha256": "sha256:" + hashlib.sha256(design.read_bytes()).hexdigest(),
        },
        "identifier_sets": dict(manifest["traceability"]),
    }
    write_json(manifest_path, manifest)


class KnowledgeSystemTests(unittest.TestCase):
    def assert_invalid(self, report: dict[str, object], token: str) -> None:
        self.assertEqual(report["status"], "invalid", report)
        self.assertIn(token, "\n".join(report["errors"]))

    def test_valid_default_single_dossier_and_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_valid_repository(root)
            report = ks.validate_knowledge_system(root)
            self.assertEqual(report["status"], "valid", report)
            self.assertEqual(report["changes_checked"], ["safe-change"])

            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--repo-root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            self.assertEqual(json.loads(result.stdout)["status"], "valid")

    def test_valid_governed_dossier_and_custom_convention(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_valid_repository(
                root,
                project_root="engineering/knowledge",
                changes_root="engineering/changes",
                dossier_format="governed",
            )
            write_json(
                root / ".dev-flow" / "knowledge.json",
                {
                    "schema_version": "1.0",
                    "project_root": "engineering/knowledge",
                    "changes_root": "engineering/changes",
                },
            )
            report = ks.validate_knowledge_system(root)
            self.assertEqual(report["status"], "valid", report)
            self.assertEqual(report["roots"]["project"], "engineering/knowledge")
            self.assertEqual(report["roots"]["changes"], "engineering/changes")

    def test_explicit_relative_roots_override_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_valid_repository(root, project_root="knowledge/current", changes_root="knowledge/history")
            report = ks.validate_knowledge_system(
                root,
                project_root="knowledge/current",
                changes_root="knowledge/history",
            )
            self.assertEqual(report["status"], "valid", report)

    def test_traversal_and_absolute_roots_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_valid_repository(root)
            report = ks.validate_knowledge_system(root, project_root="../outside")
            self.assert_invalid(report, "traversal")
            report = ks.validate_knowledge_system(root, project_root=str(root / "docs" / "project"))
            self.assert_invalid(report, "must be relative")

            report = ks.validate_knowledge_system(root, project_root="")
            self.assert_invalid(report, "non-empty POSIX relative path")

    def test_runtime_evidence_must_be_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            make_valid_repository(root)
            (root / ".gitignore").write_text("dist/\n", encoding="utf-8")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "repository-local ignore rule")

    def test_linked_worktree_accepts_the_exact_local_exclude_written_by_init_packet(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            container = Path(temp)
            primary = container / "primary"
            linked = container / "linked"
            primary.mkdir()
            make_valid_repository(primary)
            for command in (
                ["git", "init", "-q"],
                ["git", "config", "user.email", "dev-flow@example.invalid"],
                ["git", "config", "user.name", "Dev Flow Test"],
                ["git", "add", "."],
                ["git", "commit", "-qm", "fixture"],
                ["git", "worktree", "add", "-qb", "linked-fixture", str(linked)],
            ):
                result = subprocess.run(command, cwd=primary, check=False, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

            # The linked checkout must rely only on the Git-owned exclude that
            # init-packet resolves through `git rev-parse --git-path`.
            (linked / ".gitignore").unlink()
            initialized = subprocess.run(
                [
                    sys.executable,
                    str(DEV_FLOW_SCRIPT),
                    "init-packet",
                    "--root",
                    str(linked),
                    "--change-id",
                    "linked-ignore",
                    "--task-type",
                    "routine",
                    "--objective",
                    "Verify linked worktree ignore discovery",
                    "--work-mode",
                    "traced",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(initialized.returncode, 0, initialized.stderr or initialized.stdout)
            exclude_result = subprocess.run(
                ["git", "rev-parse", "--git-path", "info/exclude"],
                cwd=linked,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(exclude_result.returncode, 0, exclude_result.stderr)
            exclude = Path(exclude_result.stdout.strip())
            if not exclude.is_absolute():
                exclude = linked / exclude
            self.assertIn(".codex/dev-flow/", exclude.read_text(encoding="utf-8").splitlines())

            report = ks.validate_knowledge_system(linked)
            self.assertEqual(report["status"], "valid", report)

    def test_opted_in_authority_binding_validates_exact_bytes_and_identifier_sets(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root, dossier_format="governed")
            bind_governed_authority(dossier)
            report = ks.validate_knowledge_system(root)
            self.assertEqual(report["status"], "valid", report)

    def test_single_dossier_may_bind_one_document_as_both_requirement_and_design(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            change = dossier / "change.md"
            change.write_text(
                "# Safe change\n\n[Manifest](./manifest.json)\n\n"
                "- AC-1: The observable command contract remains stable.\n"
                "- SC-D1: Change the direct implementation.\n"
                "- SC-P1: Preserve unrelated behavior.\n"
                "- SC-L1: Do not perform delivery actions.\n"
                "- VO-1: Exercise the observable and internal oracles.\n",
                encoding="utf-8",
            )
            manifest_path = dossier / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            digest = "sha256:" + hashlib.sha256(change.read_bytes()).hexdigest()
            manifest["authority_binding"] = {
                "schema_version": "1.0",
                "change_id": manifest["change_id"],
                "requirements": {"path": "change.md", "sha256": digest},
                "design": {"path": "change.md", "sha256": digest},
                "identifier_sets": dict(manifest["traceability"]),
            }
            write_json(manifest_path, manifest)
            report = ks.validate_knowledge_system(root)
            self.assertEqual(report["status"], "valid", report)

    def test_authority_binding_rejects_requirement_or_design_byte_drift(self) -> None:
        for document in ("requirements.md", "design.md"):
            with self.subTest(document=document), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, dossier = make_valid_repository(root, dossier_format="governed")
                bind_governed_authority(dossier)
                with (dossier / document).open("a", encoding="utf-8") as handle:
                    handle.write("\nA later unbound edit changes the authoritative bytes.\n")
                report = ks.validate_knowledge_system(root)
                self.assert_invalid(report, f"authority_binding.{document.removesuffix('.md')} sha256")

    def test_authority_binding_rejects_redefined_or_missing_normative_ids(self) -> None:
        mutations = (
            ("requirements.md", "AC-1:", "AC-2:", "acceptance_criteria"),
            ("design.md", "SC-D1:", "SC-D2:", "scope"),
            ("design.md", "- VO-1: Exercise the observable and internal oracles.\n", "", "verification_obligations"),
        )
        for document, before, after, family in mutations:
            with self.subTest(document=document, family=family), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, dossier = make_valid_repository(root, dossier_format="governed")
                bind_governed_authority(dossier)
                path = dossier / document
                path.write_text(path.read_text(encoding="utf-8").replace(before, after), encoding="utf-8")
                manifest_path = dossier / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                role = document.removesuffix(".md")
                # Even when an editor refreshes the whole-file digest, a stable
                # ID cannot disappear or be reassigned without reopening the binding.
                manifest["authority_binding"][role]["sha256"] = (
                    "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
                )
                write_json(manifest_path, manifest)
                report = ks.validate_knowledge_system(root)
                self.assert_invalid(report, f"normative {family} declarations")

    def test_authority_binding_rejects_manifest_traceability_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root, dossier_format="governed")
            bind_governed_authority(dossier)
            manifest_path = dossier / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authority_binding"]["identifier_sets"]["scope"] = ["SC-D1"]
            write_json(manifest_path, manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "authority_binding.identifier_sets.scope must exactly equal traceability.scope")

    def test_authority_binding_rejects_duplicate_normative_id_declaration(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root, dossier_format="governed")
            bind_governed_authority(dossier)
            requirements = dossier / "requirements.md"
            with requirements.open("a", encoding="utf-8") as handle:
                handle.write("- **AC-1:** A second meaning must not reuse the stable identifier.\n")
            manifest_path = dossier / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authority_binding"]["requirements"]["sha256"] = (
                "sha256:" + hashlib.sha256(requirements.read_bytes()).hexdigest()
            )
            write_json(manifest_path, manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "duplicate normative acceptance_criteria declaration")

    def test_governed_authority_binding_rejects_cross_role_normative_definitions(self) -> None:
        mutations = (
            (
                "design.md",
                "- AC-1: A contradictory design-side meaning reuses the requirement ID.\n",
                "must not declare normative acceptance_criteria",
            ),
            (
                "design.md",
                "- AC-2: A design document cannot introduce a different acceptance ID.\n",
                "must not declare normative acceptance_criteria",
            ),
            (
                "requirements.md",
                "- SC-D1: A contradictory requirement-side meaning reuses the design scope ID.\n",
                "must not declare normative scope",
            ),
            (
                "requirements.md",
                "- SC-D2: A requirements document cannot introduce a different scope ID.\n",
                "must not declare normative scope",
            ),
            (
                "requirements.md",
                "- VO-1: A contradictory requirement-side meaning reuses the design verification ID.\n",
                "must not declare normative verification_obligations",
            ),
            (
                "requirements.md",
                "- VO-2: A requirements document cannot introduce a different verification ID.\n",
                "must not declare normative verification_obligations",
            ),
        )
        for document, declaration, error_token in mutations:
            with self.subTest(document=document, declaration=declaration), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, dossier = make_valid_repository(root, dossier_format="governed")
                bind_governed_authority(dossier)
                path = dossier / document
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(declaration)
                manifest_path = dossier / "manifest.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                role = document.removesuffix(".md")
                manifest["authority_binding"][role]["sha256"] = (
                    "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
                )
                write_json(manifest_path, manifest)
                report = ks.validate_knowledge_system(root)
                self.assert_invalid(report, error_token)

    def test_authority_binding_is_opt_in_for_legacy_dossiers_but_fail_closed_when_declared(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root, dossier_format="governed")
            legacy = ks.validate_knowledge_system(root)
            self.assertEqual(legacy["status"], "valid", legacy)

            manifest_path = dossier / "manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authority_binding"] = {"schema_version": "1.0"}
            write_json(manifest_path, manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "authority_binding.change_id")

    def test_document_traversal_and_symlink_escape_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
            manifest["documents"]["change"] = "../escape.md"
            write_json(dossier / "manifest.json", manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "contains traversal")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, _, _ = make_valid_repository(root)
            outside = root / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (project / "truth.md").unlink()
            try:
                (project / "truth.md").symlink_to(outside)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "symlink")

    def test_unlisted_file_and_nested_symlink_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            (dossier / "raw.md").write_text("api_key=supersecretvalue\n", encoding="utf-8")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "undeclared file")
            self.assert_invalid(report, "secret-like")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, _, _ = make_valid_repository(root)
            (project / "unreviewed.md").write_text("TODO: curate this claim.\n", encoding="utf-8")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "undeclared file in project knowledge root")
            self.assert_invalid(report, "unresolved placeholder")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, _, _ = make_valid_repository(root)
            outside = root / "outside"
            outside.mkdir()
            try:
                (project / "nested").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks unavailable: {exc}")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "contains a symlink")

    def test_dossier_document_contract_rejects_wrong_filename_and_manifest_self_reference(self) -> None:
        for replacement in ("record.md", "manifest.json"):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, dossier = make_valid_repository(root)
                manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
                manifest["documents"] = {"change": replacement}
                if replacement == "record.md":
                    (dossier / "change.md").rename(dossier / replacement)
                else:
                    (dossier / "change.md").unlink()
                write_json(dossier / "manifest.json", manifest)
                report = ks.validate_knowledge_system(root)
                self.assert_invalid(report, "documents must equal")

    def test_promoted_disposition_requires_completed_lifecycle(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
            manifest["status"] = "draft"
            for family in ("black_box", "white_box"):
                manifest["tests"][family] = {
                    "status": "planned",
                    "rationale": "The test is designed but has not run.",
                    "evidence": [],
                }
            write_json(dossier / "manifest.json", manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "promoted knowledge requires accepted or superseded status")

    def test_missing_knowledge_disposition_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
            del manifest["knowledge"]["disposition"]
            write_json(dossier / "manifest.json", manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "knowledge.disposition")

    def test_unresolved_placeholder_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, _, _ = make_valid_repository(root)
            with (project / "truth.md").open("a", encoding="utf-8") as handle:
                handle.write("\nTODO: replace this before acceptance.\n")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "unresolved placeholder")

    def test_markdown_html_is_not_misclassified_as_a_placeholder(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project, _, _ = make_valid_repository(root)
            with (project / "truth.md").open("a", encoding="utf-8") as handle:
                handle.write(
                    "\n<details><summary>Evidence</summary>Closed record.</details>\n"
                    "<picture><source srcset=\"hero.png\"><img src=\"hero.png\"></picture>\n"
                    "The API returns `Result<T, E>` or ``Vec<Owner>``.\n"
                    "XML may use <record><value>ok</value></record>.\n"
                    "\n    Vec<Owner>\n"
                )
            report = ks.validate_knowledge_system(root)
            self.assertEqual(report["status"], "valid", report)

    def test_absolute_local_path_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            with (dossier / "change.md").open("a", encoding="utf-8") as handle:
                handle.write("\nEvidence was copied from /Users/alice/private/output.log.\n")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "absolute local path")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            with (dossier / "change.md").open("a", encoding="utf-8") as handle:
                handle.write("\nEvidence was copied from /srv/build/output.log.\n")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "absolute local path")

    def test_secret_like_content_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            with (dossier / "change.md").open("a", encoding="utf-8") as handle:
                handle.write("\napi_key=supersecretvalue\n")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "secret-like")

    def test_missing_black_and_white_box_accounting_fail_closed(self) -> None:
        for family in ("black_box", "white_box"):
            with self.subTest(family=family), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                _, _, dossier = make_valid_repository(root)
                manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
                del manifest["tests"][family]
                write_json(dossier / "manifest.json", manifest)
                report = ks.validate_knowledge_system(root)
                self.assert_invalid(report, f"tests.{family} accounting is required")

    def test_broken_local_link_missing_backlink_and_crosslink_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            with (dossier / "change.md").open("a", encoding="utf-8") as handle:
                handle.write("\n[Missing evidence](./missing.md)\n")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "broken local link")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            (dossier / "change.md").write_text("# No manifest backlink\n", encoding="utf-8")
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "missing backlink")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
            manifest["related_changes"] = ["../missing-change/manifest.json"]
            write_json(dossier / "manifest.json", manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "broken related change crosslink")

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            _, _, dossier = make_valid_repository(root)
            manifest = json.loads((dossier / "manifest.json").read_text(encoding="utf-8"))
            manifest["related_changes"] = ["manifest.json"]
            write_json(dossier / "manifest.json", manifest)
            report = ks.validate_knowledge_system(root)
            self.assert_invalid(report, "must not reference itself")


if __name__ == "__main__":
    unittest.main()
