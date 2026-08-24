#!/usr/bin/env python3
"""Focused tests for repository knowledge discovery and planning."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "repository-knowledge" / "scripts" / "repository_knowledge.py"


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


knowledge = _load_module("repository_knowledge_test_module", SCRIPT)


def init_repo(path: Path, files: dict[str, str]) -> None:
    path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init", "-q", str(path)],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for relative, content in files.items():
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


class RepositoryKnowledgeTests(unittest.TestCase):
    def test_single_repository_reuses_small_readme_as_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "library"
            init_repo(
                root,
                {
                    "AGENTS.md": "# Guidance\n",
                    "Cargo.toml": '[package]\nname = "library"\nversion = "0.1.0"\n',
                    "README.md": "# Library\n",
                    "src/lib.rs": "pub fn value() -> u8 { 1 }\n",
                },
            )

            report = knowledge.scan(root)
            repo = report["repositories"][0]
            self.assertEqual(report["topology"], "single-repo")
            self.assertEqual(repo["repository_type"], "single-repo")
            self.assertTrue(repo["knowledge"]["root_agents"])
            self.assertEqual(repo["languages"][0]["name"], "Rust")

            plan = knowledge.build_plan(report)
            readme = next(item for item in plan["actions"] if item["artifact"] == "README.md")
            self.assertEqual(readme["disposition"], "designate-or-repair")

    def test_manifest_evidence_classifies_monorepo(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            init_repo(
                root,
                {
                    "Cargo.toml": '[workspace]\nmembers = ["crates/a", "crates/b"]\nresolver = "2"\n',
                    "crates/a/Cargo.toml": '[package]\nname = "a"\nversion = "0.1.0"\n',
                    "crates/b/Cargo.toml": '[package]\nname = "b"\nversion = "0.1.0"\n',
                    "docs/index.md": "# Workspace\n",
                },
            )

            repo = knowledge.scan(root)["repositories"][0]
            self.assertEqual(repo["repository_type"], "monorepo")
            self.assertEqual(repo["component_hints"], ["crates/a", "crates/b"])
            self.assertEqual(repo["workspace_evidence"][0]["kind"], "cargo-workspace")

    def test_workspace_discovery_excludes_generated_nested_repositories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "program"
            init_repo(root / "service", {"README.md": "# Service\n"})
            init_repo(root / "client", {"README.md": "# Client\n"})
            init_repo(root / ".build" / "checkouts" / "dependency", {"README.md": "# Dependency\n"})

            report = knowledge.scan(root)
            self.assertEqual(report["topology"], "multi-repository-workspace")
            self.assertEqual({item["name"] for item in report["repositories"]}, {"client", "service"})
            self.assertEqual({item["relative_path"] for item in report["repositories"]}, {"client", "service"})
            self.assertEqual(report["program_hub"]["classification"], "owner-input-required")
            self.assertGreaterEqual(report["discovery"]["excluded_path_count"], 1)

            entry = next(item for item in report["workspace_entries"] if item["path"] == "service")
            self.assertEqual(entry["kind"], "git-repository")

    def test_unversioned_container_knowledge_is_visible(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "workspace"
            container = root / "product"
            init_repo(container / "api", {"README.md": "# API\n"})
            init_repo(container / "app", {"README.md": "# App\n"})
            (container / "docs").mkdir(parents=True)
            (container / "docs" / "README.md").write_text("# Product\n", encoding="utf-8")
            (container / "docs" / "design").mkdir()
            (container / "docs" / "design" / "system.md").write_text("# System\n", encoding="utf-8")

            report = knowledge.scan(root)
            entry = report["workspace_entries"][0]
            self.assertEqual(entry["kind"], "multi-repository-container")
            self.assertEqual(
                entry["unversioned_knowledge"]["documents"],
                ["docs/README.md", "docs/design/system.md"],
            )
            plan = knowledge.build_plan(report)
            dispositions = {item["disposition"] for item in plan["actions"] if item["scope"].endswith("product")}
            self.assertEqual(dispositions, {"owner-input-required", "adopt-or-move"})

    def test_release_surfaces_route_to_existing_runbook(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(
                root,
                {
                    ".github/workflows/release.yml": "name: release\n",
                    "docs/releasing.md": "# Releasing\n",
                    "scripts/publish.sh": "#!/bin/sh\n",
                },
            )

            repo = knowledge.scan(root)["repositories"][0]
            self.assertTrue(repo["release"]["has_release_automation"])
            self.assertTrue(repo["knowledge"]["runbooks"])
            self.assertEqual(repo["documents"]["release_documents"], ["docs/releasing.md"])
            ids = {item["id"] for item in repo["recommendations"]}
            self.assertNotIn("add-release-runbook", ids)

    def test_release_and_product_documents_are_separate_from_repository_index(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "website"
            init_repo(
                root,
                {
                    "README.md": "# Website\n",
                    "release/CHANGELOG.md": "# Changes\n",
                    "release/update-notes/v1.json": "{}\n",
                    "src/content/docs/index.mdx": "# Product docs\n",
                    "src/content/docs/guides/start.md": "# Start\n",
                },
            )

            repo = knowledge.scan(root)["repositories"][0]
            self.assertEqual(repo["documents"]["repository_document_count"], 1)
            self.assertEqual(repo["documents"]["release_document_count"], 1)
            self.assertEqual(repo["documents"]["product_document_count"], 2)
            self.assertFalse(repo["knowledge"]["stable_index"])
            plan = knowledge.build_plan(knowledge.scan(root))
            self.assertTrue(any(item["artifact"] == "README.md" for item in plan["actions"]))

    def test_check_reports_context_budget_and_broken_links(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(
                root,
                {
                    "AGENTS.md": "x" * 5000,
                    "docs/index.md": "[missing](missing.md)\n[again](missing.md)\n",
                    "README.md": "# Service\n",
                },
            )

            result = knowledge.check_report(knowledge.scan(root))
            codes = {item["code"] for item in result["findings"]}
            self.assertEqual(result["status"], "failed")
            self.assertIn("agents-context-budget", codes)
            self.assertIn("broken-relative-link", codes)
            self.assertEqual(
                sum(item["code"] == "broken-relative-link" for item in result["findings"]),
                1,
            )

    def test_check_distinguishes_symbol_links_and_machine_local_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(
                root,
                {
                    "AGENTS.md": "# Guidance\n",
                    "docs/index.md": (
                        "[Rust symbol](crate::module::Item)\n"
                        "[Crate](workspace_core)\n"
                        "[Local workbook](C:/private/release.xlsx)\n"
                    ),
                },
            )

            result = knowledge.check_report(knowledge.scan(root))
            codes = [item["code"] for item in result["findings"]]
            self.assertIn("nonportable-local-link", codes)
            self.assertNotIn("broken-relative-link", codes)
            local_finding = next(
                item for item in result["findings"] if item["code"] == "nonportable-local-link"
            )
            self.assertNotIn("C:/", local_finding["message"])

    def test_scan_is_read_only_and_ignores_sensitive_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(root, {"README.md": "# Service\n", ".env": "EXAMPLE=value\n"})
            before = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain=v1"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            report = knowledge.scan(root)
            after = subprocess.run(
                ["git", "-C", str(root), "status", "--porcelain=v1"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout
            self.assertEqual(before, after)
            self.assertEqual(report["repositories"][0]["file_count"], 1)

    def test_sensitive_variants_and_symlinks_are_never_read_or_mapped(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            container = Path(temp)
            root = container / "service"
            outside = container / "outside.md"
            outside.write_text("private sentinel_symbol\n", encoding="utf-8")
            encoded_names = (
                (46, 101, 110, 118, 46, 112, 114, 111, 100, 117, 99, 116, 105, 111, 110),
                (46, 110, 112, 109, 114, 99),
                (46, 112, 121, 112, 105, 114, 99),
                (97, 117, 116, 104, 46, 106, 115, 111, 110),
                (112, 114, 105, 118, 97, 116, 101, 46, 112, 101, 109),
                (99, 111, 110, 102, 105, 103, 47, 99, 114, 101, 100, 101, 110, 116, 105, 97, 108, 115, 46, 112, 114, 111, 100, 46, 106, 115, 111, 110),
            )
            files = {"README.md": "# Service\n"}
            files.update(
                {"".join(chr(value) for value in encoded): "sentinel_symbol\n" for encoded in encoded_names}
            )
            init_repo(root, files)
            (root / "docs").mkdir()
            (root / "docs" / "outside.md").symlink_to(outside)
            subprocess.run(
                ["git", "-C", str(root), "add", "."],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            report = knowledge.scan(root)
            self.assertEqual(report["repositories"][0]["file_count"], 1)
            task_map = knowledge.build_task_map(report, "sentinel_symbol private")
            self.assertEqual(
                [item["path"] for item in task_map["selected_files"]], ["README.md"]
            )
            self.assertEqual(task_map["selected_files"][0]["symbols"], [])
            self.assertNotIn("docs/outside.md", knowledge._markdown_files(root))

    def test_scanning_a_subtree_resolves_the_owning_repository(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(root, {"README.md": "# Service\n", "src/lib.rs": "pub fn value() {}\n"})
            report = knowledge.scan(root / "src")
            self.assertEqual(report["topology"], "single-repo")
            self.assertEqual(report["repositories"][0]["root"], str(root.resolve()))
            self.assertEqual(report["workspace_entries"], [])

    def test_cli_emits_machine_readable_plan(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "service"
            init_repo(root, {"README.md": "# Service\n"})
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "plan", "--root", str(root)],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["schema_version"], "1.0")
            self.assertTrue(payload["actions"])

    def test_task_map_ranks_relevant_source_and_symbols(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "gateway"
            init_repo(
                root,
                {
                    "README.md": "# Gateway\n",
                    "src/channel_password.rs": "pub fn verify_channel_password() -> bool { true }\n",
                    "src/health.rs": "pub fn health() -> bool { true }\n",
                    "tests/channel_password_test.rs": "fn channel_password_compatibility() {}\n",
                },
            )

            task_map = knowledge.build_task_map(
                knowledge.scan(root),
                "channel password compatibility",
                file_budget=3,
            )
            self.assertEqual(task_map["selected_files"][0]["path"], "tests/channel_password_test.rs")
            selected = {item["path"]: item for item in task_map["selected_files"]}
            self.assertIn("src/channel_password.rs", selected)
            self.assertIn("verify_channel_password", selected["src/channel_password.rs"]["symbols"])
            self.assertTrue(task_map["derived_evidence"])


if __name__ == "__main__":
    unittest.main()
