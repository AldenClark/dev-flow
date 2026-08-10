#!/usr/bin/env python3
"""Release artifact, workflow, and install lifecycle contract tests."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "tools" / "build_release.py"
FLOW = ROOT / "skills" / "dev-flow" / "scripts" / "dev-flow.py"
PYTHON = sys.executable
VERSION = "1.0.0"


def run(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=False, capture_output=True, text=True)


def current_commit() -> str:
    result = run("git", "rev-parse", "HEAD", cwd=ROOT)
    if result.returncode != 0:
        raise AssertionError(result.stderr)
    return result.stdout.strip()


class ReleaseArtifactTests(unittest.TestCase):
    def build(self, output: Path, *, version: str = VERSION) -> subprocess.CompletedProcess[str]:
        return run(
            PYTHON,
            str(BUILDER),
            "build",
            "--root",
            str(ROOT),
            "--output",
            str(output),
            "--version",
            version,
            "--commit",
            current_commit(),
        )

    def test_repeated_builds_are_byte_identical_and_verify(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first"
            second = Path(temp) / "second"
            first_result = self.build(first)
            second_result = self.build(second)
            self.assertEqual(first_result.returncode, 0, first_result.stderr or first_result.stdout)
            self.assertEqual(second_result.returncode, 0, second_result.stderr or second_result.stdout)
            first_names = sorted(path.name for path in first.iterdir())
            self.assertEqual(first_names, sorted(path.name for path in second.iterdir()))
            for name in first_names:
                self.assertEqual((first / name).read_bytes(), (second / name).read_bytes(), name)

            verify = run(
                PYTHON,
                str(BUILDER),
                "verify",
                "--artifact-dir",
                str(first),
                "--expected-version",
                VERSION,
                "--expected-commit",
                current_commit(),
            )
            self.assertEqual(verify.returncode, 0, verify.stderr or verify.stdout)
            self.assertEqual(json.loads(verify.stdout)["status"], "valid")

    def test_corrupt_archive_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "release"
            built = self.build(output)
            self.assertEqual(built.returncode, 0, built.stderr or built.stdout)
            archive = output / f"dev-flow-{VERSION}.tar.gz"
            archive.write_bytes(archive.read_bytes() + b"corruption")
            verify = run(PYTHON, str(BUILDER), "verify", "--artifact-dir", str(output))
            self.assertEqual(verify.returncode, 2, verify.stderr or verify.stdout)
            self.assertIn("does not match", verify.stderr)

    def test_nonempty_and_symlink_outputs_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            nonempty = Path(temp) / "nonempty"
            nonempty.mkdir()
            (nonempty / "keep.txt").write_text("user data\n", encoding="utf-8")
            result = self.build(nonempty)
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertEqual((nonempty / "keep.txt").read_text(encoding="utf-8"), "user data\n")

            real = Path(temp) / "real"
            real.mkdir()
            linked = Path(temp) / "linked"
            try:
                linked.symlink_to(real, target_is_directory=True)
            except OSError as error:
                self.skipTest(f"symlinks are unavailable: {error}")
            result = self.build(linked)
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("symlink", result.stderr)

    def test_wrong_version_is_rejected_without_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "release"
            result = self.build(output, version="1.0.1")
            self.assertEqual(result.returncode, 2, result.stderr or result.stdout)
            self.assertIn("does not match plugin manifest", result.stderr)
            self.assertFalse(list(output.iterdir()))

    def test_checksums_can_be_finalized_with_sbom(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "release"
            built = self.build(output)
            self.assertEqual(built.returncode, 0, built.stderr or built.stdout)
            sbom_name = f"dev-flow-{VERSION}.spdx.json"
            (output / sbom_name).write_text(
                json.dumps({"spdxVersion": "SPDX-2.3", "name": f"dev-flow-{VERSION}"}) + "\n",
                encoding="utf-8",
            )
            checksums = run(
                PYTHON,
                str(BUILDER),
                "checksums",
                "--artifact-dir",
                str(output),
                "--file",
                f"dev-flow-{VERSION}.tar.gz",
                "--file",
                "release-manifest.json",
                "--file",
                sbom_name,
            )
            self.assertEqual(checksums.returncode, 0, checksums.stderr or checksums.stdout)
            verify = run(PYTHON, str(BUILDER), "verify", "--artifact-dir", str(output))
            self.assertEqual(verify.returncode, 0, verify.stderr or verify.stdout)
            self.assertIn(sbom_name, json.loads(verify.stdout)["checksummed_files"])


class RuntimeLifecycleSmokeTests(unittest.TestCase):
    def test_fresh_install_idempotence_and_uninstall_in_isolated_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "isolated-codex" / "agents"
            install = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(install.returncode, 0, install.stderr or install.stdout)
            install_payload = json.loads(install.stdout)
            self.assertEqual(install_payload["status"], "installed")
            self.assertTrue(install_payload["restart_required"])

            repeat = run(PYTHON, str(FLOW), "install-runtime", "--destination", str(destination))
            self.assertEqual(repeat.returncode, 0, repeat.stderr or repeat.stdout)
            self.assertEqual(json.loads(repeat.stdout)["status"], "unchanged")

            uninstall = run(PYTHON, str(FLOW), "uninstall-runtime", "--destination", str(destination))
            self.assertEqual(uninstall.returncode, 0, uninstall.stderr or uninstall.stdout)
            self.assertEqual(json.loads(uninstall.stdout)["status"], "uninstalled")
            self.assertFalse(list(destination.glob("*.toml")))


class ReleaseWorkflowContractTests(unittest.TestCase):
    def test_workflow_run_scalars_do_not_embed_mapping_tokens_unquoted(self) -> None:
        workflows = ROOT / ".github" / "workflows"
        for path in sorted((*workflows.glob("*.yml"), *workflows.glob("*.yaml"))):
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                stripped = line.lstrip()
                if not stripped.startswith("run: "):
                    continue
                scalar = stripped.removeprefix("run: ")
                if scalar.startswith(("|", ">", "'", '\"')):
                    continue
                self.assertNotIn(
                    ": ",
                    scalar,
                    f"{path.relative_to(ROOT)}:{line_number} uses an invalid YAML plain run scalar",
                )

    def test_marketplace_installs_the_selected_snapshot_without_a_second_ref(self) -> None:
        marketplace = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text(encoding="utf-8"))
        plugin = next(item for item in marketplace["plugins"] if item["name"] == "dev-flow")
        self.assertEqual(plugin["source"], {"source": "local", "path": "."})

    def test_ci_uses_explicit_six_cell_matrix_and_strict_warnings(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        self.assertIn("os: [ubuntu-24.04, macos-15, windows-2025]", workflow)
        self.assertIn('python: ["3.11", "3.14"]', workflow)
        self.assertIn("python -W error::ResourceWarning -m unittest discover -s evals -v", workflow)
        self.assertIn("Record environment", workflow)
        self.assertIn("permissions:\n  contents: read", workflow)

    def test_release_workflow_is_manual_pinned_and_least_privilege(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release-candidate.yml").read_text(encoding="utf-8")
        required_tokens = (
            "  workflow_dispatch:",
            "expected_sha:",
            "cancel-in-progress: false",
            "contents: read",
            "id-token: write",
            "attestations: write",
            "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
            "actions/attest@1e69f48acb82d1966a394da916b4c1698aa569d6",
            "anchore/sbom-action@e22c389904149dbc22b58101806040fa8d37a610",
            "syft-version: v1.42.3",
            "upload-artifact: false",
            "upload-release-assets: false",
            "dependency-snapshot: false",
            "SYFT_SOURCE_SUPPLIER: Dev Flow Contributors",
            "SBOM file inventory is empty",
            "SBOM root package identity is missing",
            "retention-days: 30",
            "compression-level: 0",
            "overwrite: false",
            "git fetch --no-tags --depth=1 origin \"$GITHUB_REF\"",
            "python3 -c \"import sys; assert sys.version_info >= (3, 11)",
        )
        for token in required_tokens:
            self.assertIn(token, workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("packages: write", workflow)
        self.assertNotIn("pull_request:", workflow)
        self.assertNotIn("\n  push:", workflow)
        self.assertNotIn("softprops/action-gh-release", workflow)
        self.assertNotIn("actions/checkout@", workflow)
        self.assertNotIn("actions/setup-python@", workflow)


if __name__ == "__main__":
    unittest.main()
