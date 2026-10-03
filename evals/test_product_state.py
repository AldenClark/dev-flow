#!/usr/bin/env python3
"""Canonical product-state contract tests."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_product_state", ROOT / "tools" / "validate_product_state.py")
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)

DELIVERY_FIELDS = (
    "commit", "hosted_ci", "cross_platform", "independent_review",
    "tag", "artifact", "publication", "isolated_install",
)

# Frozen RC.9 historical record. Historical fixtures must not inherit the current
# repository's candidate, stable record, waiver decisions, or workstream paths.
HISTORICAL_RC9 = {
    "schema_version": "dev-flow.product-state.v1",
    "source": {"version": "2.0.0-rc.9", "phase": "released", "manifest": ".codex-plugin/plugin.json", "workstream": "docs/workstreams/dev-flow-2.0-rc.9"},
    "workspace": {"phase": "development", "base_published": "v2.0.0-rc.9", "workstream": "docs/workstreams/dev-flow-2.0-rc.9"},
    "published": {"latest_rc": {"version": "2.0.0-rc.9", "tag": "v2.0.0-rc.9"}, "stable": {"version": "1.1.2", "tag": "v1.1.2"}},
    "compatibility": {"public_cli": "rc5-supported-surface", "legacy_packet_cli": "internal-unsupported", "rollback_target": "v2.0.0-rc.8"},
    "delivery": {"commit": "passed", "hosted_ci": "waived", "cross_platform": "waived", "independent_review": "waived", "tag": "passed", "artifact": "passed", "publication": "passed", "isolated_install": "waived"},
}


def historical_state() -> dict[str, object]:
    return json.loads(json.dumps(HISTORICAL_RC9))


def delivery_summary(delivery: dict[str, object]) -> str:
    return "Delivery state: " + "; ".join(f"{field}={delivery[field]}" for field in DELIVERY_FIELDS) + "."


def write_fixture(
    target: Path,
    state: dict[str, object],
    *,
    include_optional_workstream_docs: bool = True,
) -> None:
    source = state["source"]
    workspace = state["workspace"]
    published = state["published"]
    compatibility = state["compatibility"]
    assert isinstance(source, dict)
    assert isinstance(workspace, dict)
    assert isinstance(published, dict)
    assert isinstance(compatibility, dict)
    latest = published["latest_rc"]
    stable = published["stable"]
    assert isinstance(latest, dict)
    assert isinstance(stable, dict)
    version = source["version"]
    phase = source["phase"]
    workstream_relative = source["workstream"]
    workspace_phase = workspace["phase"]
    workspace_base = workspace["base_published"]
    workspace_relative = workspace["workstream"]
    assert isinstance(version, str)
    assert isinstance(phase, str)
    assert isinstance(workstream_relative, str)
    assert isinstance(workspace_phase, str)
    assert isinstance(workspace_base, str)
    assert isinstance(workspace_relative, str)
    (target / "governance").mkdir(parents=True, exist_ok=True)
    (target / ".codex-plugin").mkdir(parents=True, exist_ok=True)
    (target / ".github" / "workflows").mkdir(parents=True, exist_ok=True)
    workstream = target / workstream_relative
    workstream.mkdir(parents=True, exist_ok=True)
    workspace_workstream = target / workspace_relative
    workspace_workstream.mkdir(parents=True, exist_ok=True)
    (target / "governance" / "product-state.json").write_text(json.dumps(state), encoding="utf-8")
    (target / ".codex-plugin" / "plugin.json").write_text(
        json.dumps({"version": version}), encoding="utf-8"
    )
    required_names = ("implementation.md",)
    optional_names = ("requirements.md", "design.md", "decisions.md") if include_optional_workstream_docs else ()
    for name in (*required_names, *optional_names):
        contents = (
            f"> Status: implemented in the source-candidate worktree for `{version}`\n"
            if name == "implementation.md" and phase == "source-candidate"
            else "fixture"
        )
        (workstream / name).write_text(contents, encoding="utf-8")
        (workspace_workstream / name).write_text(contents, encoding="utf-8")
    delivery = state["delivery"]
    assert isinstance(delivery, dict)
    summary = delivery_summary(delivery)
    legacy_review = (
        "| HC7 | Independent clean-context review | qualification | "
        f"{delivery['independent_review']} | fixture |\n"
        if workstream_relative == "docs/workstreams/dev-flow-2.0-rc.6"
        else (
            f"- Source candidate implementation: `{version}` is implemented in this worktree.\n"
            if phase == "source-candidate"
            else "fixture\n"
        )
    )
    (workstream / "progress.md").write_text(
        "# Progress\n\n## Current truth\n\n"
        + legacy_review
        + summary
        + "\n",
        encoding="utf-8",
    )
    if workspace_workstream != workstream:
        (workspace_workstream / "progress.md").write_text("fixture", encoding="utf-8")
    source_label = "候选源码" if phase == "source-candidate" else "已发布源码"
    release_label = "candidate" if phase == "source-candidate" else "release"
    stable_default = int(stable["version"].split(".")[0]) >= 2
    install_tag = stable["tag"] if stable_default else latest["tag"]
    stable_label = "最近已发布的稳定标签" if stable_default else "最后一个 1.x 稳定标签"
    (target / "README.md").write_text(
        f"{source_label}身份为 `{version}`\n"
        f"当前工作区处于 `{workspace_phase}` 状态，基于 `{workspace_base}`\n"
        f"`{latest['tag']}` 是最近已发布\n"
        f"`{stable['tag']}` 是{stable_label}\n"
        f"回滚目标为 `{compatibility['rollback_target']}`\n"
        f"## 版本和发布状态\n"
        + (
            f"- `{version}` 是当前候选源码身份。\n"
            f"- `{latest['tag']}` 是最近已发布且可固定安装的 RC。\n"
            if phase == "source-candidate"
            else ""
        )
        + f"\n## 安装\n\ncodex plugin marketplace add AldenClark/dev-flow --ref {install_tag}\n",
        encoding="utf-8",
    )
    (target / "docs").mkdir(exist_ok=True)
    (target / "docs" / "releasing.md").write_text(
        f"## {version} personal-assistant hardening {release_label}\n"
        f"`{latest['tag']}` is the latest public immutable RC tag\n"
        f"`{compatibility['rollback_target']}` is the rollback target for `{version}`\n"
        f"{summary}\n"
        f"--version {version}\n-f version={version}\n",
        encoding="utf-8",
    )
    (target / ".github" / "workflows" / "release-candidate.yml").write_text(
        f'default: "{version}"\n', encoding="utf-8"
    )
    (target / "docs" / "project").mkdir(exist_ok=True)
    (target / "docs" / "project" / "dev-flow-governance.md").write_text(
        f"../workstreams/{Path(workstream_relative).name}/\n", encoding="utf-8"
    )
    review_claim = (
        "Independent clean-context review passed\n"
        if delivery["independent_review"] == "passed"
        else ""
    )
    changelog_label = (
        "Current candidate source identity"
        if phase == "source-candidate"
        else "Latest published source identity"
    )
    (target / "CHANGELOG.md").write_text(
        f"{changelog_label}: `{version}`\n"
        f"Current workspace state: `{workspace_phase}` from `{workspace_base}`\n"
        f"\n## [{version}] - Fixture\n\n"
        f"{review_claim}",
        encoding="utf-8",
    )


class ProductStateTests(unittest.TestCase):
    def rc7_candidate_state(self) -> dict[str, object]:
        state = historical_state()
        state["source"].update({
            "version": "2.0.0-rc.7",
            "phase": "source-candidate",
            "workstream": "docs/workstreams/dev-flow-2.0-rc.7",
        })
        state["published"]["latest_rc"] = {
            "version": "2.0.0-rc.6",
            "tag": "v2.0.0-rc.6",
        }
        state["workspace"]["base_published"] = "v2.0.0-rc.6"
        state["workspace"]["workstream"] = "docs/workstreams/dev-flow-2.0-rc.7"
        state["compatibility"]["rollback_target"] = state["published"]["latest_rc"]["tag"]
        state["delivery"] = {key: "not-run" for key in state["delivery"]}
        return state

    def test_rc7_candidate_accepts_minimal_two_file_workstream(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(
                target,
                self.rc7_candidate_state(),
                include_optional_workstream_docs=False,
            )
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_minimal_workstream_rejects_each_missing_required_file(self) -> None:
        for missing in ("implementation.md", "progress.md"):
            with self.subTest(missing=missing), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                state = self.rc7_candidate_state()
                write_fixture(target, state, include_optional_workstream_docs=False)
                path = target / state["source"]["workstream"] / missing
                path.unlink()
                result = VALIDATOR.validate(target, check_git=False)
                self.assertIn(f"source workstream is missing {missing}", result["errors"])

    def test_rc6_legacy_workstream_keeps_hc7_projection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"].update({
                "version": "2.0.0-rc.6",
                "phase": "released",
                "workstream": "docs/workstreams/dev-flow-2.0-rc.6",
            })
            state["workspace"]["workstream"] = "docs/workstreams/dev-flow-2.0-rc.6"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.5"
            state["delivery"] = {key: "passed" for key in state["delivery"]}
            state["delivery"]["independent_review"] = "waived"
            write_fixture(target, state)
            progress = target / state["source"]["workstream"] / "progress.md"
            progress.write_text("fixture\n", encoding="utf-8")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn("progress independent review projection is stale", result["errors"])

    def test_repository_product_state_is_valid(self) -> None:
        state = json.loads((ROOT / "governance/product-state.json").read_text(encoding="utf-8"))
        result = VALIDATOR.validate(ROOT)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["source_version"], state["source"]["version"])
        self.assertEqual(result["source_phase"], state["source"]["phase"])
        self.assertEqual(result["workspace_phase"], "development")
        self.assertEqual(result["workspace_base"], state["workspace"]["base_published"])
        self.assertEqual(result["published_version"], state["published"]["latest_rc"]["version"])
        self.assertEqual(result["observations"]["published_tag"], "observed-in-checkout")
        self.assertIn(result["observations"]["workspace_base_head"], {"matches-workspace-base-tag", "diverged-from-workspace-base-tag"})
        self.assertIn("not remote publication", result["claim_limit"])
        self.assertIn("no delivery", result["claim_limit"])

    def test_candidate_current_state_surfaces_cannot_drift_independently(self) -> None:
        mutations = (
            (
                "README.md",
                "## 版本和发布状态\n"
                "- `2.0.0-rc.7` 是当前候选源码身份。\n"
                "- `v2.0.0-rc.6` 是最近已发布且可固定安装的 RC。",
                "## 版本和发布状态\n"
                "- `2.0.0-rc.7` 是当前候选源码身份。\n"
                "- `v2.0.0-rc.6` 是最近已发布且可固定安装的 RC。\n"
                "## 版本和发布状态\n"
                "- `2.0.0-rc.6` 是当前候选源码身份。\n"
                "- `v2.0.0-rc.5` 是最近已发布且可固定安装的 RC。",
                "README status section is missing or duplicated",
            ),
            (
                ".github/workflows/release-candidate.yml",
                'default: "2.0.0-rc.7"',
                'default: "2.0.0-rc.6"',
                "workflow candidate projection is stale",
            ),
            (
                "docs/releasing.md",
                "-f version=2.0.0-rc.7",
                "-f version=2.0.0-rc.6",
                "releasing workflow example projection is stale",
            ),
            (
                "docs/project/dev-flow-governance.md",
                "../workstreams/dev-flow-2.0-rc.7/",
                "../workstreams/dev-flow-2.0-rc.6/",
                "governance workstream projection is stale",
            ),
            (
                "docs/workstreams/dev-flow-2.0-rc.7/implementation.md",
                "> Status: implemented in the source-candidate worktree for `2.0.0-rc.7`",
                "> Status: implementation has not started",
                "implementation candidate projection is stale",
            ),
            (
                "docs/workstreams/dev-flow-2.0-rc.7/progress.md",
                "- Source candidate implementation: `2.0.0-rc.7` is implemented",
                "- Source candidate implementation: not started",
                "progress candidate projection is stale",
            ),
        )
        for relative, current, stale, expected in mutations:
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                write_fixture(target, self.rc7_candidate_state(), include_optional_workstream_docs=False)
                path = target / relative
                original = path.read_text(encoding="utf-8")
                self.assertIn(current, original)
                path.write_text(original.replace(current, stale, 1), encoding="utf-8")
                result = VALIDATOR.validate(target, check_git=False)
                self.assertIn(expected, result["errors"])

    def test_every_delivery_field_is_projected_to_both_current_state_surfaces(self) -> None:
        for relative, expected in (
            ("docs/releasing.md", "releasing delivery projection is stale"),
            (
                "docs/workstreams/dev-flow-2.0-rc.7/progress.md",
                "progress delivery projection is stale",
            ),
        ):
            for field in VALIDATOR.DELIVERY_ORDER:
                with (
                    self.subTest(relative=relative, field=field),
                    tempfile.TemporaryDirectory() as directory,
                ):
                    target = Path(directory)
                    write_fixture(
                        target,
                        self.rc7_candidate_state(),
                        include_optional_workstream_docs=False,
                    )
                    path = target / relative
                    original = path.read_text(encoding="utf-8")
                    current = f"{field}=not-run"
                    self.assertIn(current, original)
                    path.write_text(
                        original.replace(current, f"{field}=passed", 1),
                        encoding="utf-8",
                    )
                    result = VALIDATOR.validate(target, check_git=False)
                    self.assertIn(expected, result["errors"])

    def test_delivery_projection_accepts_crlf_checkout(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(
                target,
                self.rc7_candidate_state(),
                include_optional_workstream_docs=False,
            )
            for relative in (
                "docs/releasing.md",
                "docs/workstreams/dev-flow-2.0-rc.7/progress.md",
            ):
                path = target / relative
                lf_bytes = path.read_bytes().replace(b"\r\n", b"\n")
                path.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))

            result = VALIDATOR.validate(target, check_git=False)

            self.assertEqual(result["status"], "valid", result["errors"])

    def test_delivery_projection_rejects_hidden_historical_and_conflicting_copies(self) -> None:
        surfaces = (
            ("docs/releasing.md", "releasing delivery projection is stale"),
            (
                "docs/workstreams/dev-flow-2.0-rc.7/progress.md",
                "progress delivery projection is stale",
            ),
        )
        for relative, expected_error in surfaces:
            for camouflage in (
                "html-comment",
                "fenced-code",
                "fenced-section",
                "historical-section",
                "indented-historical-section",
                "nested-historical-section",
                "indented-nested-historical-section",
                "processing-instruction",
                "raw-html-before-nested-current",
                "raw-html-around-section",
                "conflicting-copy",
            ):
                for field in VALIDATOR.DELIVERY_ORDER:
                    with (
                        self.subTest(
                            relative=relative,
                            camouflage=camouflage,
                            field=field,
                        ),
                        tempfile.TemporaryDirectory() as directory,
                    ):
                        target = Path(directory)
                        state = self.rc7_candidate_state()
                        write_fixture(
                            target,
                            state,
                            include_optional_workstream_docs=False,
                        )
                        summary = delivery_summary(state["delivery"])
                        contradictory = summary.replace(
                            f"{field}=not-run", f"{field}=passed"
                        )
                        visible_contradiction = f"Current {field} status: passed."
                        path = target / relative
                        original = path.read_text(encoding="utf-8")
                        if camouflage == "html-comment":
                            changed = original.replace(
                                summary, visible_contradiction, 1
                            )
                            changed += f"\n<!--\n{summary}\n-->\n"
                        elif camouflage == "fenced-code":
                            changed = original.replace(
                                summary,
                                visible_contradiction
                                + f"\n\n```text\n{summary}\n```",
                                1,
                            )
                        elif camouflage == "fenced-section":
                            heading = (
                                "## 2.0.0-rc.7 personal-assistant hardening candidate"
                                if relative == "docs/releasing.md"
                                else "## Current truth"
                            )
                            changed = original.replace(
                                heading, "```text\n" + heading, 1
                            ).replace(summary, summary + "\n```", 1)
                        elif camouflage == "historical-section":
                            changed = original.replace(
                                summary, visible_contradiction, 1
                            )
                            changed += f"\n## Historical\n\n{summary}\n"
                        elif camouflage == "indented-historical-section":
                            changed = original.replace(
                                summary, visible_contradiction, 1
                            )
                            changed += f"\n   ## Historical\n\n{summary}\n"
                        elif camouflage == "nested-historical-section":
                            changed = original.replace(
                                summary,
                                visible_contradiction
                                + f"\n\n### Historical snapshot\n\n{summary}",
                                1,
                            )
                        elif camouflage == "indented-nested-historical-section":
                            changed = original.replace(
                                summary,
                                visible_contradiction
                                + f"\n\n   ### Historical snapshot\n\n{summary}",
                                1,
                            )
                        elif camouflage == "processing-instruction":
                            changed = original.replace(
                                summary,
                                visible_contradiction
                                + f"\n\n<?historical\n{summary}\n?>",
                                1,
                            )
                        elif camouflage == "raw-html-before-nested-current":
                            changed = original.replace(
                                summary,
                                "<details><summary>Historical example</summary>\n\n"
                                + summary
                                + "\n\n</details>\n\n### Current delivery state\n\n"
                                + visible_contradiction,
                                1,
                            )
                        elif camouflage == "raw-html-around-section":
                            heading = (
                                "## 2.0.0-rc.7 personal-assistant hardening candidate"
                                if relative == "docs/releasing.md"
                                else "## Current truth"
                            )
                            changed = original.replace(
                                heading,
                                "<details><summary>Historical wrapper</summary>\n\n"
                                + heading,
                                1,
                            ).replace(
                                summary,
                                summary
                                + "\n\n### Current delivery state\n\n"
                                + visible_contradiction
                                + "\n\n</details>",
                                1,
                            )
                        else:
                            changed = original.replace(
                                summary, summary + "\n" + contradictory, 1
                            )
                        path.write_text(changed, encoding="utf-8")
                        result = VALIDATOR.validate(target, check_git=False)
                        self.assertIn(expected_error, result["errors"])

    def test_manifest_drift_is_rejected_without_git(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            (target / "governance").mkdir()
            (target / ".codex-plugin").mkdir()
            (target / "docs" / "workstreams" / "dev-flow-2.0-rc.5").mkdir(parents=True)
            state = historical_state()
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
            state = historical_state()
            state["source"]["phase"] = "source-candidate"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.4", "tag": "v2.0.0-rc.4"}
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
            state = historical_state()
            state["delivery"]["independent_review"] = "not-run"
            write_fixture(target, state)
            with (target / "CHANGELOG.md").open("a", encoding="utf-8") as stream:
                stream.write("Independent clean-context review passed\n")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertIn("changelog independent review claim outruns canonical delivery state", result["errors"])

    def test_candidate_does_not_inherit_historical_review_claim(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"]["version"] = "2.0.0-rc.8"
            state["source"]["phase"] = "source-candidate"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.7", "tag": "v2.0.0-rc.7"}
            state["workspace"]["base_published"] = "v2.0.0-rc.7"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.7"
            state["delivery"] = {key: "not-run" for key in state["delivery"]}
            state["delivery"]["independent_review"] = "not-run"
            write_fixture(target, state)
            with (target / "CHANGELOG.md").open("a", encoding="utf-8") as stream:
                stream.write("\n## [2.0.0-rc.7] - 2026-09-03\n")
                stream.write("Independent clean-context review passed for RC.7.\n")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])

    def test_released_rc_keeps_previous_known_good_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"]["version"] = "2.0.0-rc.5"
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
            state["workspace"]["base_published"] = "v2.0.0-rc.5"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.4"
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
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["published_version"], "2.0.0-rc.5")

    def test_non_git_source_keeps_tag_presence_not_observed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            write_fixture(target, state)
            result = VALIDATOR.validate(target)
        self.assertEqual(result["status"], "valid", result["errors"])
        for key in ("published_tag", "latest_rc_tag", "stable_tag", "workspace_base_tag", "rollback_tag", "workspace_head", "workspace_base_head"):
            self.assertEqual(result["observations"][key], "not_observed")
        self.assertEqual(result["observations"]["git_repository"]["status"], "not-applicable")

    def test_development_workspace_can_match_its_published_base(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(target, historical_state())
            subprocess.run(["git", "init", "-q"], cwd=target, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=target, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.invalid"], cwd=target, check=True)
            subprocess.run(["git", "add", "."], cwd=target, check=True)
            subprocess.run(["git", "commit", "-qm", "fixture"], cwd=target, check=True)
            subprocess.run(["git", "tag", "v2.0.0-rc.8"], cwd=target, check=True)
            subprocess.run(["git", "tag", "v2.0.0-rc.9"], cwd=target, check=True)
            subprocess.run(["git", "tag", "v1.1.2"], cwd=target, check=True)
            result = VALIDATOR.validate(target)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["observations"]["workspace_base_head"], "matches-workspace-base-tag")

    def test_released_rc_requires_real_delivery_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"]["version"] = "2.0.0-rc.5"
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
            state["workspace"]["base_published"] = "v2.0.0-rc.5"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.4"
            state["delivery"]["hosted_ci"] = "not-run"
            state["delivery"]["cross_platform"] = "not-run"
            state["delivery"]["isolated_install"] = "not-run"
            for key in ("commit", "tag", "artifact", "publication"):
                state["delivery"][key] = "passed"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["action_gates"]["complete"]["status"], "blocked")
        self.assertEqual(set(result["action_gates"]["complete"]["missing"]), {"hosted_ci", "cross_platform", "isolated_install"})

    def test_stable_identity_is_recordable_without_claiming_independent_review_complete(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"]["version"] = "2.0.0"
            state["source"]["phase"] = "stable"
            state["published"]["stable"] = {"version": "2.0.0", "tag": "v2.0.0"}
            for key in ("commit", "hosted_ci", "cross_platform", "tag", "artifact", "publication", "isolated_install"):
                state["delivery"][key] = "passed"
            state["delivery"]["independent_review"] = "not-applicable"
            write_fixture(target, state)
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["action_gates"]["complete"]["missing"], {"independent_review": "not-applicable"})

    def test_rc_check_waivers_do_not_waive_delivery_or_stable_checks(self) -> None:
        cases = (
            ("released", "hosted_ci", "waived", False),
            ("released", "cross_platform", "waived", False),
            ("released", "isolated_install", "waived", False),
            ("released", "hosted_ci", "failed", True),
            ("released", "tag", "waived", True),
            ("released", "publication", "waived", True),
            ("stable", "hosted_ci", "waived", True),
            ("stable", "isolated_install", "waived", True),
        )
        for phase, key, disposition, incomplete in cases:
            with self.subTest(phase=phase, key=key, disposition=disposition), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                state = historical_state()
                state["source"]["phase"] = phase
                state["source"]["version"] = "2.0.0-rc.9" if phase == "released" else "2.0.0"
                state["published"]["latest_rc"] = {"version": "2.0.0-rc.9", "tag": "v2.0.0-rc.9"}
                state["workspace"]["base_published"] = "v2.0.0-rc.9"
                if phase == "stable":
                    state["published"]["stable"] = {"version": "2.0.0", "tag": "v2.0.0"}
                state["compatibility"]["rollback_target"] = "v2.0.0-rc.8"
                for action in state["delivery"]:
                    state["delivery"][action] = "passed"
                state["delivery"]["independent_review"] = "waived" if phase == "released" else "passed"
                state["delivery"][key] = disposition
                write_fixture(target, state)
                result = VALIDATOR.validate(target, check_git=False)
                self.assertEqual(result["action_gates"]["complete"]["status"] == "blocked", incomplete, result)

    def test_released_rc_requires_an_explicit_independent_review_disposition(self) -> None:
        for review_state in ("failed", "blocked", "not-run"):
            with self.subTest(review_state=review_state), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                state = historical_state()
                state["source"]["version"] = "2.0.0-rc.5"
                state["source"]["phase"] = "released"
                state["published"]["latest_rc"] = {"version": "2.0.0-rc.5", "tag": "v2.0.0-rc.5"}
                state["workspace"]["base_published"] = "v2.0.0-rc.5"
                state["compatibility"]["rollback_target"] = "v2.0.0-rc.4"
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
                state["delivery"]["independent_review"] = review_state
                write_fixture(target, state)
                result = VALIDATOR.validate(target, check_git=False)
            self.assertEqual(result["status"], "valid", result["errors"])
            self.assertIn("independent_review", result["action_gates"]["complete"]["missing"])

    def test_released_rc_rejects_self_rollback_and_stale_latest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = historical_state()
            state["source"]["version"] = "2.0.0-rc.5"
            state["source"]["phase"] = "released"
            state["published"]["latest_rc"] = {"version": "2.0.0-rc.4", "tag": "v2.0.0-rc.4"}
            state["workspace"]["base_published"] = "v2.0.0-rc.4"
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
                json.dumps(historical_state()),
                encoding="utf-8",
            )
            try:
                (target / "governance").symlink_to(outside, target_is_directory=True)
            except OSError as exc:
                self.skipTest(f"symlinks are unavailable: {exc}")
            result = VALIDATOR.validate(target, check_git=False)
        self.assertEqual(result["status"], "invalid")
        self.assertTrue(any("symlink" in error for error in result["errors"]), result["errors"])


def lifecycle_state(stage: str) -> dict[str, object]:
    state = historical_state()
    if stage == "rc9":
        return state
    state["source"].update({"version": "2.0.0", "phase": "source-candidate", "workstream": "docs/workstreams/dev-flow-2.0"})
    state["workspace"]["workstream"] = "docs/workstreams/dev-flow-2.0"
    state["compatibility"]["rollback_target"] = "v2.0.0-rc.9"
    state["delivery"] = {field: "not-run" for field in DELIVERY_FIELDS}
    if stage == "candidate":
        return state
    state["source"]["phase"] = "stable"
    state["published"]["stable"] = {"version": "2.0.0", "tag": "v2.0.0"}
    state["workspace"]["base_published"] = "v2.0.0"
    state["delivery"] = {field: "passed" for field in DELIVERY_FIELDS}
    if stage == "stable":
        return state
    state["source"].update({"version": "2.0.1-rc.1", "phase": "source-candidate"})
    state["compatibility"]["rollback_target"] = "v2.0.0"
    state["delivery"] = {field: "not-run" for field in DELIVERY_FIELDS}
    if stage == "next-candidate":
        return state
    if stage != "next-released":
        raise ValueError(stage)
    state["source"]["phase"] = "released"
    state["published"]["latest_rc"] = {"version": "2.0.1-rc.1", "tag": "v2.0.1-rc.1"}
    state["workspace"]["base_published"] = "v2.0.1-rc.1"
    state["delivery"] = {field: "passed" for field in DELIVERY_FIELDS}
    return state


def init_fixture_git(target: Path) -> None:
    for arguments in (
        ["init", "-q"], ["config", "user.name", "Fixture"],
        ["config", "user.email", "fixture@example.invalid"],
        ["add", "."], ["commit", "-qm", "historical release"],
        ["tag", "v1.1.2"], ["tag", "v2.0.0-rc.8"], ["tag", "v2.0.0-rc.9"],
    ):
        subprocess.run(["git", *arguments], cwd=target, check=True, capture_output=True)


class StableLifecycleTests(unittest.TestCase):
    def test_distribution_package_does_not_inherit_ancestor_git_identity(self) -> None:
        for forged_tags in (False, True):
            with self.subTest(forged_tags=forged_tags), tempfile.TemporaryDirectory() as directory:
                ancestor = Path(directory)
                if forged_tags:
                    (ancestor / "unrelated.txt").write_text("unrelated repository", encoding="utf-8")
                    init_fixture_git(ancestor)
                    subprocess.run(["git", "commit", "--allow-empty", "-qm", "unrelated advance"], cwd=ancestor, check=True)
                else:
                    subprocess.run(["git", "init", "-q"], cwd=ancestor, check=True)
                package = ancestor / "dist" / "dev-flow"
                write_fixture(package, historical_state())
                result = VALIDATOR.validate(package)
                self.assertEqual(result["status"], "valid", result["errors"])
                self.assertEqual(result["observations"]["git_repository"]["status"], "not-applicable")
                for field in ("latest_rc_tag", "stable_tag", "workspace_base_tag", "rollback_tag", "workspace_head", "workspace_base_head"):
                    self.assertEqual(result["observations"][field], "not_observed", field)
                # Giving the selected package its own checkout enables only its identity.
                init_fixture_git(package)
                subprocess.run(["git", "commit", "--allow-empty", "-qm", "package advance"], cwd=package, check=True)
                exact = VALIDATOR.validate(package)
                self.assertEqual(exact["status"], "valid", exact["errors"])
                self.assertEqual(exact["observations"]["git_repository"]["status"], "observed")
                self.assertEqual(exact["observations"]["latest_rc_tag"], "observed-in-checkout")
                self.assertEqual(exact["observations"]["workspace_base_head"], "diverged-from-workspace-base-tag")

    def validate_fixture(self, state: dict[str, object]) -> dict[str, object]:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(target, state)
            return VALIDATOR.validate(target, check_git=False)

    def test_full_lifecycle_has_independent_identity_and_channel_expectations(self) -> None:
        # Handwritten expectations from the product lifecycle, not validator output.
        expected = (
            ("rc9", "2.0.0-rc.9", "released", "2.0.0-rc.9", "1.1.2", "v2.0.0-rc.9", "v2.0.0-rc.9", "recorded-prerequisites-met"),
            ("candidate", "2.0.0", "source-candidate", "2.0.0-rc.9", "1.1.2", "v2.0.0-rc.9", "v2.0.0-rc.9", "blocked"),
            ("stable", "2.0.0", "stable", "2.0.0-rc.9", "2.0.0", "v2.0.0", "v2.0.0", "recorded-prerequisites-met"),
            ("next-candidate", "2.0.1-rc.1", "source-candidate", "2.0.0-rc.9", "2.0.0", "v2.0.0", "v2.0.0", "blocked"),
            ("next-released", "2.0.1-rc.1", "released", "2.0.1-rc.1", "2.0.0", "v2.0.1-rc.1", "v2.0.0", "recorded-prerequisites-met"),
        )
        for stage, source, phase, rc, stable, base, install, completion in expected:
            with self.subTest(stage=stage):
                result = self.validate_fixture(lifecycle_state(stage))
                self.assertEqual(result["status"], "valid", result["errors"])
                self.assertEqual((result["source_version"], result["source_phase"], result["published_version"], result["latest_rc_version"], result["stable_version"], result["workspace_base"], result["default_install_tag"]), (source, phase, rc, rc, stable, base, install))
                self.assertEqual(result["action_gates"]["complete"]["status"], completion)
                self.assertIn("no authorization", result["action_gates"]["publish"]["claim_limit"])

    def test_candidate_tag_success_and_failed_or_unknown_publication_are_valid_but_blocked(self) -> None:
        for publication in ("failed", "blocked"):
            with self.subTest(publication=publication):
                state = lifecycle_state("candidate")
                for field in ("commit", "hosted_ci", "cross_platform", "independent_review", "tag", "artifact"):
                    state["delivery"][field] = "passed"
                state["delivery"]["publication"] = publication
                result = self.validate_fixture(state)
                self.assertEqual(result["status"], "valid", result["errors"])
                for action in ("publish", "complete"):
                    self.assertEqual(result["action_gates"][action]["status"], "blocked")
                self.assertIn("publication-result-requires-reconciliation", result["action_gates"]["publish"]["blockers"])
                self.assertEqual(result["published_version"], "2.0.0-rc.9")

    def test_publication_identity_survives_install_and_qualification_failure(self) -> None:
        for field in ("isolated_install", "hosted_ci", "independent_review"):
            with self.subTest(field=field):
                state = lifecycle_state("stable")
                state["delivery"][field] = "failed"
                result = self.validate_fixture(state)
                self.assertEqual(result["status"], "valid", result["errors"])
                self.assertEqual(result["source_phase"], "stable")
                self.assertEqual(result["stable_version"], "2.0.0")
                self.assertEqual(result["action_gates"]["complete"]["status"], "blocked")
                if field != "isolated_install":
                    self.assertEqual(result["action_gates"]["publish"]["status"], "blocked")

    def test_publish_gate_does_not_require_future_publication_or_public_install(self) -> None:
        state = lifecycle_state("candidate")
        for field in ("commit", "hosted_ci", "cross_platform", "independent_review", "tag", "artifact"):
            state["delivery"][field] = "passed"
        result = self.validate_fixture(state)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["action_gates"]["publish"]["status"], "recorded-prerequisites-met")
        self.assertEqual(result["action_gates"]["complete"]["missing"], {"publication": "not-run", "isolated_install": "not-run"})
        self.assertIn("five-actual-stable-qualification-journeys", result["action_gates"]["publish"]["external_evidence_required"])

    def test_publish_gate_blocks_an_already_published_identity(self) -> None:
        for stage in ("rc9", "stable", "next-released"):
            with self.subTest(stage=stage):
                result = self.validate_fixture(lifecycle_state(stage))
                self.assertEqual(result["status"], "valid", result["errors"])
                self.assertEqual(result["action_gates"]["publish"]["status"], "blocked")
                self.assertIn("source-already-recorded-as-published", result["action_gates"]["publish"]["blockers"])

    def test_historical_rc_waivers_do_not_satisfy_stable_candidate_gates(self) -> None:
        state = lifecycle_state("candidate")
        state["delivery"].update(historical_state()["delivery"])
        state["delivery"].update({"publication": "not-run", "isolated_install": "not-run"})
        result = self.validate_fixture(state)
        self.assertEqual(result["status"], "valid", result["errors"])
        self.assertEqual(result["action_gates"]["publish"]["missing"], {"hosted_ci": "waived", "cross_platform": "waived", "independent_review": "waived"})
        self.assertEqual(result["action_gates"]["publish"]["waived"], [])

    def test_identity_contradictions_and_candidate_ordering_are_rejected(self) -> None:
        cases = (
            ("candidate", "delivery", "publication", "passed", "source-candidate delivery actions cannot be marked passed"),
            ("candidate", "delivery", "isolated_install", "passed", "source-candidate delivery actions cannot be marked passed"),
            ("stable", "delivery", "publication", "failed", "published source identity requires delivery.publication=passed"),
            ("stable", "delivery", "tag", "waived", "published source identity requires delivery.tag=passed"),
            ("next-candidate", "source", "version", "2.0.0-rc.10", "source candidate must be newer than every recorded published version"),
            ("candidate", "workspace", "base_published", "v2.0.1", "workspace.base_published must not identify a future unpublished version"),
            ("candidate", "compatibility", "rollback_target", "v2.0.1", "compatibility.rollback_target must not identify a future unpublished version"),
        )
        for stage, section, key, value, expected_error in cases:
            with self.subTest(stage=stage, section=section, key=key):
                state = lifecycle_state(stage)
                state[section][key] = value
                result = self.validate_fixture(state)
                self.assertEqual(result["status"], "invalid")
                self.assertTrue(any(expected_error in error for error in result["errors"]), result["errors"])
                self.assertEqual(result["action_gates"]["publish"]["status"], "blocked")

    def test_latest_rc_and_stable_are_distinct_version_channels(self) -> None:
        for key, version, error in (
            ("stable", "2.0.0-rc.9", "published.stable.version must not contain a prerelease"),
            ("latest_rc", "2.0.0", "published.latest_rc.version must identify an RC"),
        ):
            state = lifecycle_state("candidate")
            state["published"][key] = {"version": version, "tag": f"v{version}"}
            result = self.validate_fixture(state)
            self.assertIn(error, result["errors"])

    def test_stable_and_next_rc_install_reject_old_default_even_when_expected_tag_is_elsewhere(self) -> None:
        for stage in ("stable", "next-released"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                write_fixture(target, lifecycle_state(stage))
                path = target / "README.md"
                path.write_text(path.read_text().replace("--ref v2.0.0\n", "--ref v2.0.0-rc.9\n") + "\n## RC opt-in\n--ref v2.0.0\n", encoding="utf-8")
                result = VALIDATOR.validate(target, check_git=False)
                self.assertIn("README default install channel projection is stale or ambiguous", result["errors"])

    def test_changelog_missing_or_duplicate_current_heading_has_explicit_error(self) -> None:
        for duplicate in (False, True):
            with self.subTest(duplicate=duplicate), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                write_fixture(target, lifecycle_state("candidate"))
                path = target / "CHANGELOG.md"
                original = path.read_text()
                path.write_text(original + "\n## [2.0.0] - Duplicate\n" if duplicate else original.replace("## [2.0.0] - Fixture", "## [1.1.2] - History"), encoding="utf-8")
                result = VALIDATOR.validate(target, check_git=False)
                self.assertIn("changelog current source heading is missing or duplicated", result["errors"])

    def test_git_stable_base_and_legacy_rc_head_comparisons_are_separate(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(target, historical_state())
            init_fixture_git(target)
            write_fixture(target, lifecycle_state("stable"))
            subprocess.run(["git", "add", "."], cwd=target, check=True)
            subprocess.run(["git", "commit", "-qm", "stable"], cwd=target, check=True)
            subprocess.run(["git", "tag", "v2.0.0"], cwd=target, check=True)
            result = VALIDATOR.validate(target)
            self.assertEqual(result["status"], "valid", result["errors"])
            self.assertEqual(result["observations"]["workspace_base_head"], "matches-workspace-base-tag")
            self.assertEqual(result["observations"]["workspace_head"], "diverged-from-published-tag")
            for key in ("stable_tag", "workspace_base_tag", "latest_rc_tag", "rollback_tag"):
                self.assertEqual(result["observations"][key], "observed-in-checkout")
            subprocess.run(["git", "commit", "--allow-empty", "-qm", "next work"], cwd=target, check=True)
            result = VALIDATOR.validate(target)
            self.assertEqual(result["status"], "valid", result["errors"])
            self.assertEqual(result["observations"]["workspace_base_head"], "diverged-from-workspace-base-tag")
            subprocess.run(["git", "tag", "-d", "v2.0.0"], cwd=target, check=True, capture_output=True)
            result = VALIDATOR.validate(target)
            self.assertEqual(result["observations"]["stable_tag"], "missing")
            self.assertEqual(result["observations"]["workspace_base_tag"], "missing")
            self.assertIn("stable tag is not present in this Git repository: v2.0.0", result["errors"])

    def test_known_historical_base_and_rollback_are_checked_not_forced_to_latest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = lifecycle_state("candidate")
            state["workspace"]["base_published"] = "v2.0.0-rc.8"
            state["compatibility"]["rollback_target"] = "v2.0.0-rc.8"
            write_fixture(target, state)
            init_fixture_git(target)
            result = VALIDATOR.validate(target)
            self.assertEqual(result["status"], "valid", result["errors"])
            subprocess.run(["git", "tag", "-d", "v2.0.0-rc.8"], cwd=target, check=True, capture_output=True)
            result = VALIDATOR.validate(target)
            self.assertIn("workspace base tag is not present in this Git repository: v2.0.0-rc.8", result["errors"])
            self.assertIn("rollback tag is not present in this Git repository: v2.0.0-rc.8", result["errors"])

    def test_git_errors_and_timeout_cannot_become_non_git_success(self) -> None:
        for status in ("failed", "timeout", "unavailable"):
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                write_fixture(target, historical_state())
                with patch.object(VALIDATOR, "probe_worktree", return_value={"status": status, "reason": "controlled-negative"}):
                    result = VALIDATOR.validate(target)
                self.assertEqual(result["status"], "invalid")
                self.assertIn(f"Git repository observation failed: {status}", result["errors"])
                self.assertEqual(result["observations"]["latest_rc_tag"], "not_observed")

    def test_tag_lookup_execution_failure_is_not_classified_as_missing_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            write_fixture(target, historical_state())
            with patch.object(VALIDATOR, "probe_worktree", return_value={"status": "observed"}), patch.object(VALIDATOR, "run_git", side_effect=VALIDATOR.GitObservationError("timeout", "controlled-timeout")):
                result = VALIDATOR.validate(target)
            self.assertEqual(result["status"], "invalid")
            self.assertEqual(result["observations"]["stable_tag"], "timeout")
            self.assertFalse(any("not present" in error for error in result["errors"]))

    def test_cli_default_consistency_and_explicit_gate_exit_are_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            state = lifecycle_state("candidate")
            write_fixture(target, state)
            command = ["python3", str(ROOT / "tools/validate_product_state.py"), "--root", str(target), "--skip-git"]
            structural = subprocess.run(command, text=True, capture_output=True, check=False)
            gate = subprocess.run([*command, "--action", "publish"], text=True, capture_output=True, check=False)
            self.assertEqual(structural.returncode, 0, structural.stderr)
            self.assertEqual(gate.returncode, 2, gate.stderr)
            self.assertEqual(json.loads(gate.stdout)["status"], "valid")
            for field in ("commit", "hosted_ci", "cross_platform", "independent_review", "tag", "artifact"):
                state["delivery"][field] = "passed"
            write_fixture(target, state)
            gate = subprocess.run([*command, "--action", "publish"], text=True, capture_output=True, check=False)
            complete = subprocess.run([*command, "--action", "complete"], text=True, capture_output=True, check=False)
            self.assertEqual(gate.returncode, 0, gate.stderr)
            self.assertEqual(complete.returncode, 2, complete.stderr)


if __name__ == "__main__":
    unittest.main()
