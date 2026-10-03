#!/usr/bin/env python3
"""Validate Dev Flow's canonical source, published, and delivery state."""

from __future__ import annotations

import argparse
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/dev-flow/scripts"))
from git_observation import GitObservationError, probe_worktree, run_git


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
    headings = list(
        re.finditer(rf"(?m)^ {{0,3}}##\s+{re.escape(title)}\s*$", text)
    )
    if len(headings) != 1:
        return None
    heading = headings[0]
    following = re.search(r"(?m)^ {0,3}##\s+", text[heading.end() :])
    end = heading.end() + following.start() if following is not None else len(text)
    return text[heading.end() : end]


def _current_changelog_scope(text: str, source_version: str) -> str | None:
    headings = list(re.finditer(r"(?m)^## \[([^\]\n]+)\][^\n]*$", text))
    if sum(heading.group(1) == source_version for heading in headings) != 1:
        return None
    for index, heading in enumerate(headings):
        if heading.group(1) == source_version:
            return text[: headings[index + 1].start()] if index + 1 < len(headings) else text
    return None


def _visible_markdown(text: str) -> str:
    without_comments = re.sub(r"<!--[\s\S]*?-->", "", text)
    visible: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in without_comments.splitlines(keepends=True):
        stripped_line = line.rstrip("\r\n")
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", stripped_line)
        if fence_character is None:
            if marker is None:
                visible.append(line)
                continue
            fence_character = marker.group(1)[0]
            fence_length = len(marker.group(1))
            continue
        closing = re.fullmatch(
            rf" {{0,3}}{re.escape(fence_character)}{{{fence_length},}}[ \t]*",
            stripped_line,
        )
        if closing is not None:
            fence_character = None
            fence_length = 0
    return "".join(visible)


def _has_exact_delivery_projection(
    text: str,
    *,
    section_title: str,
    expected: str,
) -> bool:
    if re.search(r"<[A-Za-z!?/][^>]*>", re.sub(r"<!--[\s\S]*?-->", "", text)):
        return False
    section = _markdown_h2_section(_visible_markdown(text), section_title)
    if section is None:
        return False
    raw_section = _markdown_h2_section(text, section_title)
    if raw_section is None:
        return False
    summary_pattern = r"(?m)^(?:- )?(Delivery state: [^\r\n]+\.)\r?$"
    if re.findall(summary_pattern, raw_section) != [expected]:
        return False
    nested_heading = re.search(r"(?m)^ {0,3}#{3,6}\s+", section)
    if nested_heading is not None:
        section = section[: nested_heading.start()]
    return re.findall(summary_pattern, section) == [expected]


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


def _version_key(value: str) -> tuple[int, int, int, bool, int]:
    match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)(?:-rc\.(\d+))?", value)
    if match is None:
        raise ValueError("unsupported semantic version")
    major, minor, patch, rc = match.groups()
    return int(major), int(minor), int(patch), rc is None, int(rc or 0)


def _action_gates(
    source_version: Any, source_phase: Any, delivery: Any, errors: list[str],
) -> dict[str, Any]:
    """Assess recorded dispositions, without granting authority or inventing evidence."""
    delivery = delivery if isinstance(delivery, dict) else {}
    is_rc = isinstance(source_version, str) and "-rc." in source_version
    before_publication = ("commit", "hosted_ci", "cross_platform", "independent_review", "tag", "artifact")
    waivable = {"hosted_ci", "cross_platform", "independent_review", "isolated_install"} if is_rc else set()

    def gate(required: tuple[str, ...], *, completion: bool = False) -> dict[str, Any]:
        missing = {
            key: delivery.get(key, "not-run") for key in required
            if delivery.get(key) != "passed"
            and not (key in waivable and delivery.get(key) == "waived")
            and not (is_rc and key == "independent_review" and delivery.get(key) == "not-applicable")
        }
        blockers = []
        if errors:
            blockers.append("invalid-product-state")
        if not completion and source_phase in ("released", "stable"):
            blockers.append("source-already-recorded-as-published")
        if not completion and delivery.get("publication") in ("failed", "blocked"):
            blockers.append("publication-result-requires-reconciliation")
        if completion and source_phase not in ("released", "stable"):
            blockers.append("source-is-not-recorded-as-published")
        return {
            "status": "blocked" if missing or blockers else "recorded-prerequisites-met",
            "missing": missing,
            "blockers": blockers,
            "waived": [key for key in required if key in waivable and delivery.get(key) == "waived"],
            "external_evidence_required": [
                "final-native-regression-on-exact-candidate",
                "exact-candidate-content-and-effective-loading-identity",
                *([] if is_rc else ["cumulative-requirements-and-static-review", "five-actual-stable-qualification-journeys"]),
                "applicable-hosted-platform-artifact-and-remote-action-observations",
            ],
            "claim_limit": "recorded-dispositions-only; no authorization or independently verified external evidence",
        }

    return {
        "publish": gate(before_publication),
        "complete": gate((*before_publication, "publication", "isolated_install"), completion=True),
    }


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
    if not isinstance(source_phase, str) or source_phase not in ALLOWED_PHASES:
        errors.append(f"source.phase must be one of {sorted(ALLOWED_PHASES)}")
    if not isinstance(workspace_phase, str) or workspace_phase not in ALLOWED_WORKSPACE_PHASES:
        errors.append(f"workspace.phase must be one of {sorted(ALLOWED_WORKSPACE_PHASES)}")
    if latest and isinstance(latest.get("version"), str) and "-rc." not in latest["version"]:
        errors.append("published.latest_rc.version must identify an RC")
    if stable and isinstance(stable.get("version"), str) and "-rc." in stable["version"]:
        errors.append("published.stable.version must not contain a prerelease")
    published_versions = [
        release["version"] for release in (latest, stable)
        if isinstance(release.get("version"), str) and VERSION_RE.fullmatch(release["version"])
    ]
    newest_published = max(published_versions, key=_version_key) if published_versions else None
    if (
        isinstance(source_version, str)
        and newest_published is not None
        and VERSION_RE.fullmatch(source_version)
        and source_phase == "source-candidate"
        and _version_key(source_version) <= _version_key(newest_published)
    ):
        errors.append("source candidate must be newer than every recorded published version")

    rollback_target: Any = None
    rollback_version: str | None = None
    if compatibility_ok:
        assert isinstance(compatibility, dict)
        rollback_target = compatibility.get("rollback_target")
        if not isinstance(rollback_target, str) or not rollback_target.startswith("v") or VERSION_RE.fullmatch(rollback_target[1:]) is None:
            errors.append("compatibility.rollback_target must be a v<version> tag")
        else:
            rollback_version = rollback_target[1:]
        if rollback_version is not None and newest_published is not None and _version_key(rollback_version) > _version_key(newest_published):
            errors.append("compatibility.rollback_target must not identify a future unpublished version")
        if compatibility.get("legacy_packet_cli") != "internal-unsupported":
            errors.append("packet-era CLI must remain internal-unsupported")
    if source_phase == "released":
        if not isinstance(source_version, str) or "-rc." not in source_version:
            errors.append("released source phase must identify an RC version")
        if source_version != latest.get("version"):
            errors.append("released RC source must equal published.latest_rc.version")
    if source_phase == "stable" and source_version != stable.get("version"):
        errors.append("stable source must equal published.stable.version")
    if source_phase == "stable" and isinstance(source_version, str) and "-rc." in source_version:
        errors.append("stable source phase must identify a version without a prerelease")
    if workspace_ok:
        if not isinstance(workspace_base, str) or not workspace_base.startswith("v") or VERSION_RE.fullmatch(workspace_base[1:]) is None:
            errors.append("workspace.base_published must be a v<version> tag")
        elif newest_published is not None and _version_key(workspace_base[1:]) > _version_key(newest_published):
            errors.append("workspace.base_published must not identify a future unpublished version")
    if (
        isinstance(source_version, str)
        and rollback_version is not None
        and VERSION_RE.fullmatch(source_version)
        and _version_key(rollback_version) >= _version_key(source_version)
    ):
        errors.append("compatibility.rollback_target must be older than source.version")
    if delivery_ok:
        assert isinstance(delivery, dict)
        invalid_delivery = {key: value for key, value in delivery.items() if not isinstance(value, str) or value not in ALLOWED_DELIVERY}
        if invalid_delivery:
            errors.append(f"invalid delivery states: {invalid_delivery}")
        release_actions = ("publication", "isolated_install")
        if source_phase == "source-candidate" and any(delivery.get(key) == "passed" for key in release_actions):
            errors.append("source-candidate delivery actions cannot be marked passed in canonical source state")
        if source_phase in ("released", "stable"):
            for key in ("tag", "publication"):
                if delivery.get(key) != "passed":
                    errors.append(f"published source identity requires delivery.{key}=passed")

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
    stable_is_default = bool(stable.get("version") in published_versions and int(stable["version"].split(".")[0]) >= 2)
    default_install_tag = stable_tag if stable_is_default else latest_tag
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
        "README install": f"--ref {default_install_tag}",
        "README stable": (
            f"`{stable_tag}` 是最近已发布的稳定标签"
            if stable_is_default else f"`{stable_tag}` 是最后一个 1.x 稳定标签"
        ),
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
            f"> Status: source-candidate for `{source_version}`",
            f"> Status: implemented in the source-candidate worktree for `{source_version}`",
        )
        projections["progress candidate"] = (
            f"- Source candidate: `{source_version}`",
            f"- Source candidate implementation: `{source_version}` is implemented",
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
    install_section = _markdown_h2_section(_visible_markdown(readme), "安装")
    install_commands = re.findall(
        r"(?m)^codex plugin marketplace add AldenClark/dev-flow --ref ([^\s\\]+)\s*$",
        # Code is the actual installation instruction; remove comments, retain fences.
        re.sub(r"<!--[\s\S]*?-->", "", _markdown_h2_section(readme, "安装") or ""),
    )
    if install_section is None or not install_commands or install_commands[0] != default_install_tag:
        errors.append("README default install channel projection is stale or ambiguous")
    changelog_scope = _current_changelog_scope(_visible_markdown(changelog), source_version)
    if changelog_scope is None:
        errors.append("changelog current source heading is missing or duplicated")
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
            "changelog": changelog_scope or "",
        }[label.split()[0]]
        alternatives = token if isinstance(token, tuple) else (token,)
        if not any(alternative in target for alternative in alternatives):
            errors.append(f"{label} projection is stale")
    if (
        isinstance(delivery, dict)
        and delivery.get("independent_review") != "passed"
        and "Independent clean-context review passed"
        in (changelog_scope or "")
    ):
        errors.append("changelog independent review claim outruns canonical delivery state")

    repository = probe_worktree(root) if check_git else {"status": "not_observed", "reason": "git-check-skipped"}
    observations["git_repository"] = repository
    repository_observed = repository["status"] == "observed"
    if repository["status"] in {"failed", "timeout", "unavailable"}:
        errors.append(f"Git repository observation failed: {repository['status']}")
    commits: dict[str, str] = {}
    for observation, label, tag in (
        ("latest_rc_tag", "latest RC", latest_tag),
        ("stable_tag", "stable", stable_tag),
        ("workspace_base_tag", "workspace base", workspace_base),
        ("rollback_tag", "rollback", rollback_target),
    ):
        if not repository_observed or not isinstance(tag, str):
            observations[observation] = "not_observed"
            continue
        try:
            present = run_git(root, ["show-ref", "--verify", "--quiet", f"refs/tags/{tag}"])
            if present.returncode == 1:
                observations[observation] = "missing"
                errors.append(f"{label} tag is not present in this Git repository: {tag}")
                continue
            if present.returncode != 0:
                observations[observation] = "failed"
                errors.append(f"{label} tag observation failed: returncode {present.returncode}")
                continue
            completed = run_git(root, ["rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"])
            if completed.returncode != 0 or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", completed.stdout.strip()):
                observations[observation] = "failed"
                errors.append(f"{label} tag commit observation failed")
                continue
            observations[observation] = "observed-in-checkout"
            commits[observation] = completed.stdout.strip()
        except GitObservationError as exc:
            observations[observation] = exc.observation["status"]
            errors.append(f"{label} tag observation failed: {exc.observation['status']}")

    # Compatibility aliases retain their original latest-RC meaning.
    observations["published_tag"] = observations["latest_rc_tag"]
    observations["workspace_head"] = "not_observed"
    observations["workspace_base_head"] = "not_observed"
    if repository_observed:
        try:
            head = run_git(root, ["rev-parse", "--verify", "HEAD^{commit}"])
            if head.returncode != 0 or not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", head.stdout.strip()):
                errors.append("workspace HEAD observation failed")
            else:
                for field, tag_field, matches, diverged in (
                    ("workspace_head", "latest_rc_tag", "matches-published-tag", "diverged-from-published-tag"),
                    ("workspace_base_head", "workspace_base_tag", "matches-workspace-base-tag", "diverged-from-workspace-base-tag"),
                ):
                    if tag_field in commits:
                        observations[field] = matches if head.stdout.strip() == commits[tag_field] else diverged
        except GitObservationError as exc:
            errors.append(f"workspace HEAD observation failed: {exc.observation['status']}")

    return {
        "status": "valid" if not errors else "invalid",
        "source_version": source_version,
        "source_phase": source_phase,
        "workspace_phase": workspace_phase,
        "workspace_base": workspace_base,
        "published_version": latest.get("version"),
        "latest_rc_version": latest.get("version"),
        "stable_version": stable.get("version"),
        "default_install_tag": default_install_tag,
        "legacy_fields": {
            "published_version": "latest_rc_version",
            "observations.published_tag": "observations.latest_rc_tag",
            "observations.workspace_head": "HEAD comparison with latest RC; use workspace_base_head for actual base",
        },
        "observations": observations,
        "errors": errors,
        "action_gates": _action_gates(source_version, source_phase, delivery, errors),
        "claim_limit": (
            "product-state-structural-consistency-only; a checkout tag is not remote publication, "
            "GitHub Release, Marketplace activation, or installation evidence; no delivery or live activation is inferred"
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--skip-git", action="store_true")
    parser.add_argument("--action", choices=("publish", "complete"), help="also require the named recorded-disposition gate; this does not grant authority or verify external evidence")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = validate(args.root, check_git=not args.skip_git)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["status"] != "valid":
        return 2
    return 0 if args.action is None or result["action_gates"][args.action]["status"] == "recorded-prerequisites-met" else 2


if __name__ == "__main__":
    raise SystemExit(main())
