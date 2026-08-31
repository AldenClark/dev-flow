#!/usr/bin/env python3
"""Canonical product-state contract tests."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_product_state", ROOT / "tools" / "validate_product_state.py")
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def write_fixture(target: Path, state: dict[str, object]) -> None:
    source = state["source"]
    published = state["published"]
    compatibility = state["compatibility"]
    assert isinstance(source, dict)
    assert isinstance(published, dict)
    assert isinstance(compatibility, dict)
    latest = published["latest_rc"]
    stable = published["stable"]
    assert isinstance(latest, dict)
    assert isinstance(stable, dict)
    version = source["version"]
    phase = source["phase"]
    workstream_relative = source["workstream"]
    assert isinstance(version, str)
    assert isinstance(phase, str)
    assert isinstance(workstream_relative, str)
    (target / "governance").mkdir(parents=True, exist_ok=True)
    (target / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    workstream = target / workstream_relative
    workstream.mkdir(parents=True, exist_ok=True)
    (target / "governance" / "product-state.json").write_text(json.dumps(state), encoding="utf-8")
    (target / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"version": version}), encoding="utf-8"
    )
    for name in ("requirements.md", "design.md", "implementation.md", "decisions.md"):
        (workstream / name).write_text("fixture", encoding="utf-8")
    delivery = state["delivery"]
    assert isinstance(delivery, dict)
    (workstream / "progress.md").write_text(
        "| HC7 | Independent clean-context review | qualification | "
        f"{delivery['independent_review']} | fixture |\n",
        encoding="utf-8",
    )
    source_label = "候选" if phase == "source-candidate" else "发布"
    release_label = "candidate" if phase == "source-candidate" else "release"
    (target / "README.md").write_text(
        f"当前源码{source_label}身份为 `{version}`\n"
        f"`{latest['tag']}` 是最近已发布\n"
        f"--ref {latest['tag']}\n"
        f"`{stable['tag']}` 是最后一个 1.x 稳定标签\n"
        f"回滚目标为 `{compatibility['rollback_target']}`\n",
        encoding="utf-8",
    )
    (target / "docs").mkdir(exist_ok=True)
    (target / "docs" / "releasing.md").write_text(
        f"## {version} personal-assistant hardening {release_label}\n"
        f"`{latest['tag']}` is the latest public immutable RC tag\n"
        f"`{compatibility['rollback_target']}` is the rollback target for `{version}`\n",
        encoding="utf-8",
    )
    review_claim = (
        "Independent clean-context review passed\n"
        if delivery["independent_review"] == "passed"
        else ""
    )
    (target / "CHANGELOG.md").write_text(
        f"Current source identity: `{version}`\n{review_claim}", encoding="utf-8"
    )


class ProductStateTests(unittest.TestCase):
    def test_repository_product_state_is_valid(self) -> None:
        result = VALIDATOR.validate(ROOT)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["source_version"], "2.0.0-rc.5")
        self.assertEqual(result["published_version"], "2.0.0-rc.4")
        self.assertEqual(result["observations"]["published_tag"], "observed-in-checkout")
        self.assertIn("not remote publication", result["claim_limit"])
        self.assertIn("no delivery", result["claim_limit"])

    def test_manifest_drift_is_rejected_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "governance").mkdir()
            (target / ".codex-plugin").mkdir()
            (target / "docs" / "workstreams" / "dev-flow-2.0-rc.5").mkdir(parents=True)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            (target / "governance" / "product-state.json").write_text(json.dumps(state), encoding="utf-8")
            (target / ".codex-plugin" / "plugin.json").write_text('{"version":"2.0.0-rc.4"}', encoding="utf-8")
            for name in ("requirements.md", "design.md", "implementation.md", "progress.md", "decisions.md"):
                (target / "docs" / "workstreams" / "dev-flow-2.0-rc.5" / name).write_text("fixture", encoding="utf-8")
            (target / "README.md").write_text("fixture", encoding="utf-8")
            (target / "docs" / "releasing.md").write_text("fixture", encoding="utf-8")
            (target / "CHANGELOG.md").write_text("fixture", encoding="utf-8")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("plugin manifest version does not match source.version", result["errors"])

    def test_candidate_cannot_claim_completed_delivery(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "governance").mkdir()
            (target / ".codex-plugin").mkdir()
            workstream = target / "docs" / "workstreams" / "dev-flow-2.0-rc.5"
            workstream.mkdir(parents=True)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["delivery"]["publication"] = "passed"
            (target / "governance" / "product-state.json").write_text(json.dumps(state), encoding="utf-8")
            (target / ".codex-plugin" / "plugin.json").write_text('{"version":"2.0.0-rc.5"}', encoding="utf-8")
            for name in ("requirements.md", "design.md", "implementation.md", "progress.md", "decisions.md"):
                (workstream / name).write_text("fixture", encoding="utf-8")
            (target / "README.md").write_text("fixture", encoding="utf-8")
            (target / "docs" / "releasing.md").write_text("fixture", encoding="utf-8")
            (target / "CHANGELOG.md").write_text("fixture", encoding="utf-8")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn("source-candidate delivery actions cannot be marked passed in canonical source state", result["errors"])

    def test_review_prose_cannot_outpace_canonical_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["delivery"]["independent_review"] = "not-run"
            write_fixture(target, state)
            with (target / "CHANGELOG.md").open("a", encoding="utf-8") as stream:
                stream.write("Independent clean-context review passed\n")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn("changelog independent review claim outruns canonical delivery state", result["errors"])

    def test_released_rc_keeps_previous_known_good_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
            for key in (
                "commit",
                "hosted_ci",
                "cross_platform",
                "tag",
                "artifact",
                "publication",
                "isolated_install",
            ):
                state["delivery"][key] = "passed"
            state["delivery"]["independent_review"] = "not-applicable"
            state["delivery"]["model_qualification"] = "not-applicable"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["published_version"], "2.0.0-rc.5")

    def test_non_git_source_keeps_tag_presence_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            write_fixture(target, state)
            result = VALIDATOR.validate(target)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["observations"], {
            "published_tag": "not_observed",
            "rollback_tag": "not_observed",
        })

    def test_released_rc_requires_an_explicit_qualification_disposition(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
            for key in ("commit", "tag", "artifact", "publication"):
                state["delivery"][key] = "passed"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertTrue(
            any("released source is missing passed delivery actions" in error for error in result["errors"]),
            result["errors"],
        )
        self.assertIn(
            "released RC requires passed, waived, or not-applicable model_qualification",
            result["errors"],
        )

    def test_stable_release_cannot_skip_independent_review_or_model_qualification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["source"]["version"] = "2.0.0"
            state["source"]["phase"] = "stable"
            state["published"]["stable"] = {"version": "2.0.0", "tag": "v2.0.0"}
            for key in ("commit", "hosted_ci", "cross_platform", "tag", "artifact", "publication", "isolated_install"):
                state["delivery"][key] = "passed"
            state["delivery"]["independent_review"] = "not-applicable"
            state["delivery"]["model_qualification"] = "not-applicable"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertTrue(
            any("independent_review" in error for error in result["errors"]), result["errors"]
        )
        self.assertIn("stable source requires passed or waived model_qualification", result["errors"])

    def test_released_rc_cannot_ignore_a_failed_optional_independent_review(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
            for key in ("commit", "hosted_ci", "cross_platform", "tag", "artifact", "publication", "isolated_install"):
                state["delivery"][key] = "passed"
            state["delivery"]["independent_review"] = "failed"
            state["delivery"]["model_qualification"] = "not-applicable"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn(
            "released RC cannot ignore a failed or blocked independent_review",
            result["errors"],
        )

    def test_released_rc_rejects_self_rollback_and_stale_latest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = json.loads((ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"))
            state["source"]["phase"] = "released"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.5"
            for key in ("commit", "tag", "artifact", "publication"):
                state["delivery"][key] = "passed"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn("released RC source must equal published.latest_rc.version", result["errors"])
        self.assertIn("compatibility.rollback_target must be older than source.version", result["errors"])

    def test_product_state_rejects_parent_directory_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "repo"
            outside = base / "outside"
            target.mkdir()
            outside.mkdir()
            (outside / "product-state.json").write_text(
                (ROOT / "governance" / "product-state.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            try:
                (target / "governance").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("symlink" in error for error in result["errors"]), result["errors"])


if __name__ == "__main__":
    unittest.main()
