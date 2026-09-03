#!/usr/bin/env python3
"""Validate Dev Flow's canonical source, published, and delivery state."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any


STATE_PATH = Path("governance/product-state.json")
ALLOWED_PHASES = {"source-candidate", "released", "stable"}
ALLOWED_WORKSPACE_PHASES = {"development"}
ALLOWED_DELIVERY = {"not-run", "not-applicable", "passed", "failed", "blocked", "waived"}
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+(?:-rc\.\d+)?$")
SCHEMA_KEYS = {"schema_version", "source", "workspace", "published", "compatibility", "delivery"}
SOURCE_KEYS = {"version", "phase", "manifest", "workstream"}
WORKSPACE_KEYS = {"phase", "base_published", "workstream"}
PUBLISHED_KEYS = {"latest_rc", "stable"}
RELEASE_KEYS = {"version", "tag"}
COMPATIBILITY_KEYS = {"public_cli", "legacy_packet_cli", "rollback_target"}
DELIVERY_KEYS = {
    "commit",
    "hosted_ci",
    "cross_platform",
    "independent_review",
    "tag",
    "artifact",
    "publication",
    "isolated_install",
}
DELIVERY_ORDER = (
    "commit",
    "hosted_ci",
    "cross_platform",
    "independent_review",
    "tag",
    "artifact",
    "publication",
    "isolated_install",
)


def _delivery_summary(delivery: dict[str, Any]) -> str:
    return "Delivery state: " + "; ".join(
        f"{key}={delivery.get(key)}" for key in DELIVERY_ORDER
    ) + "."


def _read_root_bytes(
    root: Path,
    relative: Path | str,
    *,
    max_bytes: int,
) -> bytes:
    root = root.resolve(strict=True)
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("input must be a repository-relative file")
    current = root
    for part in relative.parts:
        current = current / part
        metadata = current.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise ValueError("input path must not contain symlinks")
    resolved = current.resolve(strict=True)
    if not resolved.is_relative_to(root) or not stat.S_ISREG(current.lstat().st_mode):
        raise ValueError("input is not a rooted regular file")
    raw = current.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(f"input exceeds {max_bytes} bytes")
    return raw


def _read_json(root: Path, relative: Path | str, *, max_bytes: int = 262_144) -> Any:
    raw = _read_root_bytes(root, relative, max_bytes=max_bytes)
    return json.loads(raw.decode("utf-8"))


def _exact_keys(value: Any, keys: set[str], label: str, errors: list[str]) -> bool:
    if not isinstance(value, dict):
        errors.append(f"{label} must be an object")
        return False
    observed = set(value)
    if observed != keys:
        errors.append(f"{label} keys must be exactly {sorted(keys)}; observed {sorted(observed)}")
        return False
    return True


def _read_text(root: Path, relative: str, errors: list[str]) -> str:
    try:
        return _read_root_bytes(root, relative, max_bytes=2_097_152).decode("utf-8")
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        errors.append(f"{relative}: {exc}")
        return ""


def _markdown_h2_section(text: str, title: str) -> str | None:
    headings = list(re.finditer(rf"(?m)^##\s+{re.escape(title)}\s*$", text))
    if len(headings) != 1:
        return None
    heading = headings[0]
    following = re.search(r"(?m)^##\s+", text[heading.end() :])
    end = heading.end() + following.start() if following is not None else len(text)
    return text[heading.end() : end]


def _visible_markdown(text: str) -> str:
    return re.sub(r"<!--[\s\S]*?-->", "", text)


def _has_exact_delivery_projection(
    text: str,
    *,
    section_title: str,
    expected: str,
) -> bool:
    section = _markdown_h2_section(_visible_markdown(text), section_title)
    if section is None:
        return False
    summaries = re.findall(r"(?m)^(?:- )?(Delivery state: [^\n]+\.)$", section)
    return summaries == [expected]


def _repository_path(root: Path, relative: Any, label: str, errors: list[str]) -> Path | None:
    if not isinstance(relative, str) or not relative.strip():
        errors.append(f"{label} must be a repository-relative path")
        return None
    raw = Path(relative)
    if raw.is_absolute() or ".." in raw.parts:
        errors.append(f"{label} must stay inside the repository")
        return None
    try:
        current = root.resolve(strict=True)
        for part in raw.parts:
            current = current / part
            if current.is_symlink():
                errors.append(f"{label} must not contain symlinks")
                return None
        resolved = current.resolve()
    except OSError as exc:
        errors.append(f"{label}: {exc}")
        return None
    if not resolved.is_relative_to(root):
        errors.append(f"{label} must stay inside the repository")
        return None
    return resolved


def _version_key(value: str) -> tuple[int, int, int, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?", value)
    if match is None:
        raise ValueError("unsupported semantic version")
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), int(rc) if rc is not None else 1_000_000_000


def validate(root: Path, *, check_git: bool = True) -> dict[str, Any]:
    root = root.resolve()
    errors: list[str] = []
    observations: dict[str, Any] = {}
    try:
        state = _read_json(root, STATE_PATH)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return {
            "status": "invalid",
            "errors": [f"{STATE_PATH}: {exc}"],
            "claim_limit": "product-state-structural-consistency-only",
        }

    if not _exact_keys(state, SCHEMA_KEYS, "product state", errors):
        state = state if isinstance(state, dict) else {}
    if state.get("schema_version") != "dev-flow.product-state.v1":
        errors.append("unsupported product-state schema")

    source = state.get("source")
    workspace = state.get("workspace")
    published = state.get("published")
    compatibility = state.get("compatibility")
    delivery = state.get("delivery")
    source_ok = _exact_keys(source, SOURCE_KEYS, "source", errors)
    workspace_ok = _exact_keys(workspace, WORKSPACE_KEYS, "workspace", errors)
    published_ok = _exact_keys(published, PUBLISHED_KEYS, "published", errors)
    compatibility_ok = _exact_keys(compatibility, COMPATIBILITY_KEYS, "compatibility", errors)
    delivery_ok = _exact_keys(delivery, DELIVERY_KEYS, "delivery", errors)

    latest: dict[str, Any] = {}
    stable: dict[str, Any] = {}
    if published_ok:
        assert isinstance(published, dict)
        if _exact_keys(published.get("latest_rc"), RELEASE_KEYS, "published.latest_rc", errors):
            latest = published["latest_rc"]
        if _exact_keys(published.get("stable"), RELEASE_KEYS, "published.stable", errors):
            stable = published["stable"]

    source_version = source.get("version") if source_ok else None
    source_phase = source.get("phase") if source_ok else None
    workspace_phase = workspace.get("phase") if workspace_ok else None
    workspace_base = workspace.get("base_published") if workspace_ok else None
    for label, version in (
        ("source.version", source_version),
        ("published.latest_rc.version", latest.get("version")),
        ("published.stable.version", stable.get("version")),
    ):
        if not isinstance(version, str) or VERSION_RE.fullmatch(version) is None:
            errors.append(f"{label} is not a supported semantic version")
    for label, release in (("published.latest_rc", latest), ("published.stable", stable)):
        if release and release.get("tag") != f"v{release.get('version')}":
            errors.append(f"{label}.tag must be v<version>")
    if source_phase not in ALLOWED_PHASES:
        errors.append(f"source.phase must be one of {sorted(ALLOWED_PHASES)}")
    if workspace_phase not in ALLOWED_WORKSPACE_PHASES:
        errors.append(f"workspace.phase must be one of {sorted(ALLOWED_WORKSPACE_PHASES)}")
    if isinstance(source_version, str) and source_phase == "source-candidate" and "-rc." not in source_version:
        errors.append("a source-candidate version must be an RC")
    if (
        isinstance(source_version, str)
        and isinstance(latest.get("version"), str)
        and VERSION_RE.fullmatch(source_version)
        and VERSION_RE.fullmatch(latest["version"])
        and source_phase == "source-candidate"
        and _version_key(source_version) <= _version_key(latest["version"])
    ):
        errors.append("source candidate must be newer than published.latest_rc.version")

    rollback_target: Any = None
    rollback_version: str | None = None
    if compatibility_ok:
        assert isinstance(compatibility, dict)
        rollback_target = compatibility.get("rollback_target")
        if not isinstance(rollback_target, str) or not rollback_target.startswith("v") or VERSION_RE.fullmatch(rollback_target[1:]) is None:
            errors.append("compatibility.rollback_target must be a v<version> tag")
        else:
            rollback_version = rollback_target[1:]
        if source_phase == "source-candidate" and rollback_target != latest.get("tag"):
            errors.append("a source candidate must roll back to published.latest_rc.tag")
        if compatibility.get("legacy_packet_cli") != "internal-unsupported":
            errors.append("packet-era CLI must remain internal-unsupported")
    if source_phase == "released":
        if not isinstance(source_version, str) or "-rc." not in source_version:
            errors.append("released source phase must identify an RC version")
        if source_version != latest.get("version"):
            errors.append("released RC source must equal published.latest_rc.version")
    if source_phase == "stable" and source_version != stable.get("version"):
        errors.append("stable source must equal published.stable.version")
    if workspace_ok and workspace_base != latest.get("tag"):
        errors.append("workspace.base_published must equal published.latest_rc.tag")
    if (
        isinstance(source_version, str)
        and rollback_version is not None
        and VERSION_RE.fullmatch(source_version)
        and _version_key(rollback_version) >= _version_key(source_version)
    ):
        errors.append("compatibility.rollback_target must be older than source.version")
    if delivery_ok:
        assert isinstance(delivery, dict)
        invalid_delivery = {key: value for key, value in delivery.items() if value not in ALLOWED_DELIVERY}
        if invalid_delivery:
            errors.append(f"invalid delivery states: {invalid_delivery}")
        release_actions = ("tag", "publication", "isolated_install")
        if source_phase == "source-candidate" and any(delivery.get(key) == "passed" for key in release_actions):
            errors.append("source-candidate delivery actions cannot be marked passed in canonical source state")
        if source_phase in {"released", "stable"}:
            required_delivery = (
                "commit",
                "hosted_ci",
                "cross_platform",
                "tag",
                "artifact",
                "publication",
                "isolated_install",
            )
            incomplete = [key for key in required_delivery if delivery.get(key) != "passed"]
            if incomplete:
                errors.append(f"released source is missing passed delivery actions: {incomplete}")
            if delivery.get("independent_review") not in {
                "passed",
                "waived",
                "not-applicable",
            }:
                errors.append(
                    "released source requires an explicit independent_review disposition"
                )

    manifest_relative = source.get("manifest") if source_ok else None
    manifest_path = _repository_path(root, manifest_relative, "source.manifest", errors)
    if manifest_path is not None:
        try:
            manifest = _read_json(root, manifest_relative)
            if not isinstance(manifest, dict) or manifest.get("version") != source_version:
                errors.append("plugin manifest version does not match source.version")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{manifest_relative}: {exc}")

    workstream_relative = source.get("workstream") if source_ok else None
    workstream = _repository_path(root, workstream_relative, "source.workstream", errors)
    if workstream is not None:
        for name in ("implementation.md", "progress.md"):
            if (workstream / name).is_symlink() or not (workstream / name).is_file():
                errors.append(f"source workstream is missing {name}")

    workspace_relative = workspace.get("workstream") if workspace_ok else None
    workspace_workstream = _repository_path(root, workspace_relative, "workspace.workstream", errors)
    if workspace_workstream is not None:
        for name in ("implementation.md", "progress.md"):
            if (workspace_workstream / name).is_symlink() or not (workspace_workstream / name).is_file():
                errors.append(f"workspace workstream is missing {name}")

    readme = _read_text(root, "README.md", errors)
    releasing = _read_text(root, "docs/releasing.md", errors)
    changelog = _read_text(root, "CHANGELOG.md", errors)
    progress = _read_text(root, f"{workstream_relative}/progress.md", errors) if isinstance(workstream_relative, str) else ""
    implementation = _read_text(root, f"{workstream_relative}/implementation.md", errors) if isinstance(workstream_relative, str) else ""
    release_workflow = _read_text(root, ".github/workflows/release-candidate.yml", errors)
    governance_doc = _read_text(root, "docs/project/dev-flow-governance.md", errors)
    latest_tag = latest.get("tag")
    stable_tag = stable.get("tag")
    source_label = "候选源码" if source_phase == "source-candidate" else "已发布源码"
    changelog_label = (
        "Current candidate source identity"
        if source_phase == "source-candidate"
        else "Latest published source identity"
    )
    release_label = "candidate" if source_phase == "source-candidate" else "release"
    projections = {
        "README source": f"{source_label}身份为 `{source_version}`",
        "README workspace": f"当前工作区处于 `{workspace_phase}` 状态，基于 `{workspace_base}`",
        "README published": f"`{latest_tag}` 是最近已发布",
        "README install": f"--ref {latest_tag}",
        "README stable": f"`{stable_tag}` 是最后一个 1.x 稳定标签",
        "README rollback": f"回滚目标为 `{rollback_target}`",
        "releasing source": f"## {source_version} personal-assistant hardening {release_label}",
        "releasing published": f"`{latest_tag}` is the latest public immutable RC tag",
        "releasing rollback": f"`{rollback_target}` is the rollback target for `{source_version}`",
        "releasing build example": f"--version {source_version}",
        "releasing workflow example": f"-f version={source_version}",
        "changelog source": f"{changelog_label}: `{source_version}`",
        "changelog workspace": f"Current workspace state: `{workspace_phase}` from `{workspace_base}`",
        "workflow candidate": f'default: "{source_version}"',
        "governance workstream": (
            f"../workstreams/{Path(workstream_relative).name}/"
            if isinstance(workstream_relative, str)
            else ""
        ),
    }
    if source_phase == "source-candidate":
        projections["implementation candidate"] = (
            f"> Status: implemented in the source-candidate worktree for `{source_version}`"
        )
        projections["progress candidate"] = (
            f"- Source candidate implementation: `{source_version}` is implemented"
        )
        status_section = _markdown_h2_section(readme, "版本和发布状态")
        if status_section is None:
            errors.append("README status section is missing or duplicated")
        else:
            candidate_versions = re.findall(
                r"(?m)^- `([^`]+)` 是当前候选源码身份", status_section
            )
            published_tags = re.findall(
                r"(?m)^- `([^`]+)` 是最近已发布", status_section
            )
            if candidate_versions != [source_version]:
                errors.append("README status candidate projection is stale or ambiguous")
            if published_tags != [latest_tag]:
                errors.append("README status published projection is stale or ambiguous")
    if workstream_relative == "docs/workstreams/dev-flow-2.0-rc.6":
        projections["progress independent review"] = (
            f"| HC7 | Independent clean-context review | qualification | "
            f"{delivery.get('independent_review') if isinstance(delivery, dict) else None} |"
        )
    if isinstance(delivery, dict) and delivery.get("independent_review") == "passed":
        projections["changelog independent review"] = "Independent clean-context review passed"
    if isinstance(delivery, dict):
        delivery_summary = _delivery_summary(delivery)
        if not _has_exact_delivery_projection(
            releasing,
            section_title=f"{source_version} personal-assistant hardening {release_label}",
            expected=delivery_summary,
        ):
            errors.append("releasing delivery projection is stale")
        if not _has_exact_delivery_projection(
            progress,
            section_title="Current truth",
            expected=delivery_summary,
        ):
            errors.append("progress delivery projection is stale")
    for label, token in projections.items():
        target = {
            "README": readme,
            "releasing": releasing,
            "progress": progress,
            "implementation": implementation,
            "workflow": release_workflow,
            "governance": governance_doc,
            "changelog": changelog,
        }[label.split()[0]]
        if token not in target:
            errors.append(f"{label} projection is stale")
    if (
        isinstance(delivery, dict)
        and delivery.get("independent_review") != "passed"
        and "Independent clean-context review passed" in changelog
    ):
        errors.append("changelog independent review claim outruns canonical delivery state")

    repository_observed = False
    if check_git and isinstance(latest_tag, str):
        git_environment = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        git_environment.update({"GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat", "GIT_TERMINAL_PROMPT": "0"})
        git_prefix = ["git", "-c", "core.fsmonitor=false", "-c", f"core.hooksPath={os.devnull}"]
        repository = subprocess.run(
            [*git_prefix, "rev-parse", "--is-inside-work-tree"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            env=git_environment,
        )
        if repository.returncode == 0 and repository.stdout.strip() == "true":
            repository_observed = True
    published_commit: str | None = None
    for observation, label, tag in (
        ("published_tag", "published", latest_tag),
        ("rollback_tag", "rollback", rollback_target),
    ):
        if not repository_observed or not isinstance(tag, str):
            observations[observation] = "not_observed"
            continue
        completed = subprocess.run(
            [*git_prefix, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            env=git_environment,
        )
        observations[observation] = "observed-in-checkout" if completed.returncode == 0 else "missing"
        if observation == "published_tag" and completed.returncode == 0:
            published_commit = completed.stdout.strip()
        if completed.returncode != 0:
            errors.append(f"{label} tag is not present in this Git repository: {tag}")

    if repository_observed and published_commit is not None:
        head = subprocess.run(
            [*git_prefix, "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            env=git_environment,
        )
        if head.returncode == 0:
            observations["workspace_head"] = (
                "matches-published-tag"
                if head.stdout.strip() == published_commit
                else "diverged-from-published-tag"
            )
            if workspace_phase == "development" and head.stdout.strip() == published_commit:
                errors.append("development workspace must diverge from its published base tag")
        else:
            observations["workspace_head"] = "not_observed"
    else:
        observations["workspace_head"] = "not_observed"

    return {
        "status": "valid" if not errors else "invalid",
        "source_version": source_version,
        "source_phase": source_phase,
        "workspace_phase": workspace_phase,
        "workspace_base": workspace_base,
        "published_version": latest.get("version"),
        "stable_version": stable.get("version"),
        "observations": observations,
        "errors": errors,
        "claim_limit": (
            "product-state-structural-consistency-only; a checkout tag is not remote publication, "
            "GitHub Release, Marketplace activation, or installation evidence; no delivery or live activation is inferred"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skip-git", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = validate(args.root, check_git=not args.skip_git)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
