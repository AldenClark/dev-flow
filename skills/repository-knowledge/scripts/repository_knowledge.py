#!/usr/bin/env python3
"""Read-only repository knowledge inventory, planning, and drift checks."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python 3.10 compatibility
    tomllib = None


SCHEMA_VERSION = "1.0"
DEFAULT_MAX_DISCOVERY_DEPTH = 5
DEFAULT_AGENTS_WARN_BYTES = 4 * 1024
DEFAULT_AGENTS_ERROR_BYTES = 16 * 1024

EXCLUDED_DIRECTORY_NAMES = frozenset(
    {
        ".build",
        ".cache",
        ".codex",
        ".codex_work",
        ".deriveddata-concurrency",
        ".git",
        ".gradle",
        ".hg",
        ".idea",
        ".next",
        ".nuxt",
        ".svn",
        ".tmp",
        ".turbo",
        ".venv",
        "DerivedData",
        "Pods",
        "__pycache__",
        "artifacts",
        "build",
        "coverage",
        "dist",
        "node_modules",
        "output",
        "outputs",
        "target",
        "third_party",
        "tmp",
        "uni_modules",
        "vendor",
        "venv",
    }
)

MANIFEST_NAMES = frozenset(
    {
        "Cargo.toml",
        "Package.swift",
        "build.gradle",
        "build.gradle.kts",
        "composer.json",
        "deno.json",
        "deno.jsonc",
        "go.mod",
        "go.work",
        "lerna.json",
        "mix.exs",
        "nx.json",
        "package.json",
        "pnpm-workspace.yaml",
        "pom.xml",
        "pyproject.toml",
        "requirements.txt",
        "settings.gradle",
        "settings.gradle.kts",
        "turbo.json",
    }
)

DOCUMENT_EXTENSIONS = frozenset({".adoc", ".md", ".mdx", ".rst"})
TEXT_SOURCE_EXTENSIONS = frozenset(
    {
        ".c",
        ".cc",
        ".cpp",
        ".cs",
        ".dart",
        ".go",
        ".h",
        ".hpp",
        ".java",
        ".js",
        ".jsx",
        ".kt",
        ".kts",
        ".m",
        ".md",
        ".mdx",
        ".mm",
        ".php",
        ".py",
        ".rb",
        ".rs",
        ".scala",
        ".sh",
        ".swift",
        ".toml",
        ".ts",
        ".tsx",
        ".vue",
        ".yaml",
        ".yml",
    }
)

LANGUAGE_EXTENSIONS = {
    ".c": "C",
    ".cc": "C++",
    ".cpp": "C++",
    ".cs": "C#",
    ".dart": "Dart",
    ".go": "Go",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".kt": "Kotlin",
    ".kts": "Kotlin",
    ".m": "Objective-C",
    ".mm": "Objective-C++",
    ".php": "PHP",
    ".py": "Python",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".scala": "Scala",
    ".sh": "Shell",
    ".swift": "Swift",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".vue": "Vue",
}

MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
GRADLE_INCLUDE_RE = re.compile(r"(?m)^\s*include(?:\s*\(|\s+)(.+)$")
TASK_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+|[\u3400-\u9fff]{2,}")
URI_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
SYMBOL_RE = re.compile(
    r"(?m)^\s*(?:(?:pub|public|private|protected|internal|open|export|async|final|sealed|static)\s+)*"
    r"(?:class|struct|enum|trait|protocol|interface|type|fn|func|def|function|fun)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
SENSITIVE_BASENAMES = frozenset(
    {
        ".env",
        ".env.local",
        "credentials",
        "credentials.json",
        "id_ed25519",
        "id_rsa",
        "secrets.json",
    }
)
SENSITIVE_DOTFILE_NAMES = frozenset(f".{stem}rc" for stem in ("net", "npm", "pypi"))
SENSITIVE_SUFFIXES = frozenset("." + suffix for suffix in ("key", "p12", "pfx", "pem"))
SENSITIVE_DIRECTORY_NAMES = frozenset("." + name for name in ("credentials", "secrets")) | {
    "secrets"
}


def _is_sensitive_relative(path: Path) -> bool:
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()
    return (
        name in SENSITIVE_BASENAMES
        or name in SENSITIVE_DOTFILE_NAMES
        or name == "auth" + ".json"
        or name.startswith("." + "env")
        or path.suffix.lower() in SENSITIVE_SUFFIXES
        or any(part in SENSITIVE_DIRECTORY_NAMES for part in lowered_parts[:-1])
        or (
            ("credential" in name or "secret" in name)
            and path.suffix.lower() in {".json", ".toml", ".yaml", ".yml"}
        )
    )


def _is_safe_repository_file(root: Path, relative: Path) -> bool:
    if relative.is_absolute() or ".." in relative.parts or _is_sensitive_relative(relative):
        return False
    root = root.resolve()
    candidate = root / relative
    try:
        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return False
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
    except (OSError, ValueError):
        return False
    return resolved.is_file()


def _bounded(values: Iterable[str], limit: int = 40) -> list[str]:
    return sorted(set(values))[:limit]


def _is_excluded(name: str) -> bool:
    return name in EXCLUDED_DIRECTORY_NAMES


def _is_git_root(path: Path) -> bool:
    return (path / ".git").exists()


def _git_toplevel(path: Path) -> Path | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    candidate = Path(result.stdout.strip())
    return candidate.resolve() if candidate.exists() else None


def discover_git_roots(target: Path, max_depth: int) -> tuple[list[Path], list[dict[str, str]]]:
    target = target.resolve()
    exclusions: list[dict[str, str]] = []
    if _is_git_root(target):
        return [target], exclusions

    owner = _git_toplevel(target)
    if owner is not None and (target == owner or owner in target.parents):
        return [owner], exclusions

    roots: list[Path] = []
    for current, directories, filenames in os.walk(target):
        current_path = Path(current)
        depth = len(current_path.relative_to(target).parts)
        if depth > max_depth:
            directories[:] = []
            continue

        for directory in list(directories):
            if _is_excluded(directory):
                exclusions.append(
                    {
                        "path": str((current_path / directory).relative_to(target)),
                        "reason": "generated-cache-vendor-or-tooling-boundary",
                    }
                )
        directories[:] = [name for name in directories if not _is_excluded(name)]

        if ".git" in filenames or (current_path / ".git").is_file():
            roots.append(current_path.resolve())
            directories[:] = []
            continue
        if (current_path / ".git").is_dir():
            roots.append(current_path.resolve())
            directories[:] = []

    return sorted(set(roots)), exclusions


def _fallback_files(root: Path) -> list[str]:
    files: list[str] = []
    for current, directories, filenames in os.walk(root):
        directories[:] = [name for name in directories if not _is_excluded(name)]
        current_path = Path(current)
        for filename in filenames:
            relative = (current_path / filename).relative_to(root)
            if not _is_safe_repository_file(root, relative):
                continue
            files.append(relative.as_posix())
    return files


def repository_files(root: Path) -> tuple[list[str], str]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "ls-files",
                "--cached",
                "--others",
                "--exclude-standard",
                "-z",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return _fallback_files(root), "filesystem-fallback"
    if result.returncode != 0:
        return _fallback_files(root), "filesystem-fallback"
    files = []
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8", errors="replace")
        relative_path = Path(relative)
        parts = relative_path.parts
        if any(_is_excluded(part) for part in parts):
            continue
        if not _is_safe_repository_file(root, relative_path):
            continue
        files.append(relative_path.as_posix())
    return sorted(set(files)), "git-index-and-untracked"


def _read_text(
    path: Path, max_bytes: int = 512 * 1024, *, root: Path | None = None
) -> str:
    if root is not None:
        try:
            relative = path.relative_to(root)
        except ValueError:
            return ""
        if not _is_safe_repository_file(root, relative):
            return ""
    try:
        with path.open("rb") as handle:
            data = handle.read(max_bytes + 1)
    except OSError:
        return ""
    if len(data) > max_bytes:
        return ""
    return data.decode("utf-8", errors="replace")


def _workspace_evidence(root: Path, files: set[str]) -> tuple[list[dict[str, Any]], list[str]]:
    evidence: list[dict[str, Any]] = []
    members: list[str] = []

    if "Cargo.toml" in files and tomllib is not None:
        try:
            cargo = tomllib.loads(_read_text(root / "Cargo.toml", root=root))
        except (ValueError, TypeError):
            cargo = {}
        workspace = cargo.get("workspace") if isinstance(cargo, dict) else None
        if isinstance(workspace, dict):
            raw_members = workspace.get("members", [])
            if isinstance(raw_members, list):
                members.extend(str(item) for item in raw_members)
            evidence.append({"source": "Cargo.toml", "kind": "cargo-workspace", "members": len(raw_members)})

    if "package.json" in files:
        try:
            package = json.loads(_read_text(root / "package.json", root=root))
        except (json.JSONDecodeError, OSError):
            package = {}
        workspaces = package.get("workspaces") if isinstance(package, dict) else None
        if isinstance(workspaces, list):
            members.extend(str(item) for item in workspaces)
            evidence.append({"source": "package.json", "kind": "package-workspaces", "members": len(workspaces)})
        elif isinstance(workspaces, dict) and isinstance(workspaces.get("packages"), list):
            raw_members = workspaces["packages"]
            members.extend(str(item) for item in raw_members)
            evidence.append({"source": "package.json", "kind": "package-workspaces", "members": len(raw_members)})

    for marker, kind in (
        ("pnpm-workspace.yaml", "pnpm-workspace"),
        ("go.work", "go-workspace"),
        ("lerna.json", "lerna-workspace"),
        ("nx.json", "nx-workspace"),
        ("turbo.json", "turbo-workspace"),
    ):
        if marker in files:
            evidence.append({"source": marker, "kind": kind, "members": None})

    if "pom.xml" in files:
        try:
            tree = ET.fromstring(_read_text(root / "pom.xml", root=root))
            modules = [node.text.strip() for node in tree.findall(".//{*}modules/{*}module") if node.text]
        except ET.ParseError:
            modules = []
        if modules:
            members.extend(modules)
            evidence.append({"source": "pom.xml", "kind": "maven-modules", "members": len(modules)})

    for marker in ("settings.gradle", "settings.gradle.kts"):
        if marker not in files:
            continue
        matches = GRADLE_INCLUDE_RE.findall(_read_text(root / marker, root=root))
        if matches:
            evidence.append({"source": marker, "kind": "gradle-modules", "members": len(matches)})

    return evidence, _bounded(members, 60)


def _document_classification(files: list[str]) -> dict[str, Any]:
    all_documents = sorted(
        item for item in files if Path(item).suffix.lower() in DOCUMENT_EXTENSIONS
    )
    repository_documents = []
    release_documents = []
    product_documents = []
    for item in all_documents:
        path = Path(item)
        lower_parts = tuple(part.lower() for part in path.parts)
        if len(path.parts) == 1 or (lower_parts and lower_parts[0] in {"doc", "docs", "documentation"}):
            repository_documents.append(item)
        if any(part in {"changelog", "release", "releases", "update-notes", "updates"} for part in lower_parts) or any(
            token in path.name.lower() for token in ("changelog", "release-note", "releasing", "whats-new")
        ):
            release_documents.append(item)
        if len(lower_parts) >= 3 and lower_parts[:3] == ("src", "content", "docs"):
            product_documents.append(item)

    def any_match(predicate: Any) -> bool:
        return any(predicate(Path(item), item.lower()) for item in all_documents)

    indexes = _bounded(
        item
        for item in repository_documents
        if item.lower() in {"docs/index.md", "docs/readme.md", "documentation/index.md", "documentation/readme.md"}
    )
    architecture = any_match(
        lambda path, lower: path.name.lower() == "architecture.md"
        or "architecture" in (part.lower() for part in path.parts)
    )
    decisions = any_match(
        lambda path, lower: any(part.lower() in {"adr", "adrs", "decisions"} for part in path.parts)
        or path.name.lower() == "decisions.md"
    )
    runbooks = any_match(
        lambda path, lower: any("runbook" in part.lower() for part in path.parts)
        or path.name.lower() in {"deploying.md", "deployment.md", "operations.md", "release.md", "releasing.md"}
    )
    forks = any_match(lambda path, lower: any(part.lower() in {"fork", "forks"} for part in path.parts))
    workstreams = any_match(lambda path, lower: "workstreams" in (part.lower() for part in path.parts))
    generated_maps = _bounded(
        item
        for item in all_documents
        if any(token in Path(item).name.lower() for token in ("repo-map", "repository-map", "code-map"))
    )
    update_documents = _bounded(
        (
            item
            for item in all_documents
            if item in release_documents
            or any(
                token in Path(item).name.lower()
                for token in ("changelog", "history", "release-note", "releases", "update", "whats-new")
            )
        ),
        80,
    )
    return {
        "document_count": len(all_documents),
        "repository_document_count": len(set(repository_documents)),
        "release_document_count": len(set(release_documents)),
        "product_document_count": len(set(product_documents)),
        "document_entries": _bounded(all_documents, 80),
        "release_documents": _bounded(release_documents, 80),
        "stable_indexes": indexes,
        "has_architecture": architecture,
        "has_decisions": decisions,
        "has_runbooks": runbooks,
        "has_fork_records": forks,
        "has_workstreams": workstreams,
        "generated_maps": generated_maps,
        "update_documents": update_documents,
    }


def _release_surfaces(files: list[str]) -> dict[str, Any]:
    workflows = _bounded(
        item
        for item in files
        if item.startswith(".github/workflows/") and Path(item).suffix.lower() in {".yaml", ".yml"}
    )
    release_workflows = _bounded(
        item
        for item in workflows
        if any(token in Path(item).name.lower() for token in ("deploy", "publish", "release", "tag"))
    )
    release_scripts = _bounded(
        item
        for item in files
        if (
            any(part.lower() in {"script", "scripts", "tools", "xtask"} for part in Path(item).parts[:-1])
            and any(token in Path(item).name.lower() for token in ("deploy", "publish", "release", "tag"))
        )
        or Path(item).name in {"Fastfile", "Makefile"}
    )
    return {
        "workflows": workflows,
        "release_workflows": release_workflows,
        "release_scripts": release_scripts,
        "has_release_automation": bool(release_workflows or release_scripts),
    }


def _language_counts(files: list[str]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for item in files:
        language = LANGUAGE_EXTENSIONS.get(Path(item).suffix.lower())
        if language:
            counts[language] += 1
    return counts


def _recommendations(repo: dict[str, Any]) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []
    knowledge = repo["knowledge"]
    documents = repo["documents"]
    if not knowledge["root_agents"]:
        recommendations.append(
            {
                "id": "add-agents-router",
                "classification": "inferred",
                "action": "Add a concise root AGENTS.md only after confirming commands and protected boundaries.",
                "reason": "No root AGENTS.md is present.",
            }
        )
    if not documents["stable_indexes"]:
        if repo["repository_type"] == "monorepo" or documents["repository_document_count"] >= 3:
            recommendations.append(
                {
                    "id": "add-stable-index",
                    "classification": "inferred",
                    "action": "Create or designate a stable documentation index and link it from README/AGENTS.md.",
                    "reason": "Several knowledge surfaces need routing but no docs index was detected.",
                }
            )
        else:
            recommendations.append(
                {
                    "id": "reuse-readme-index",
                    "classification": "owner-input-required",
                    "action": "Confirm whether README is sufficient as the stable repository index before adding docs/index.md.",
                    "reason": "The repository is small or has few maintained documents.",
                }
            )
    if repo["repository_type"] == "monorepo" and len(repo["agents_files"]) <= 1:
        recommendations.append(
            {
                "id": "assess-component-instructions",
                "classification": "owner-input-required",
                "action": "Add nested AGENTS.md only for components with materially different tooling, ownership, risk, or release boundaries.",
                "reason": "Workspace evidence exists, but component-specific instruction boundaries cannot be inferred from structure alone.",
            }
        )
    release = repo["release"]
    if release["has_release_automation"] and not documents["has_runbooks"]:
        recommendations.append(
            {
                "id": "add-release-runbook",
                "classification": "inferred",
                "action": "Add a release runbook that points to existing automation and explains authority, preflight, observation, failure, and recovery.",
                "reason": "Release automation exists but no runbook path was detected.",
            }
        )
    if len(documents["update_documents"]) > 1:
        recommendations.append(
            {
                "id": "map-update-documents",
                "classification": "owner-input-required",
                "action": "Map each update/release document to one owner and lifecycle before merging or rewriting any of them.",
                "reason": "Multiple update-oriented documents were detected.",
            }
        )
    return recommendations


def scan_repository(root: Path) -> dict[str, Any]:
    files, file_source = repository_files(root)
    file_set = set(files)
    manifests = _bounded((item for item in files if Path(item).name in MANIFEST_NAMES), 80)
    workspace_evidence, component_hints = _workspace_evidence(root, file_set)
    repository_type = "monorepo" if workspace_evidence else "single-repo"
    agents_files = _bounded((item for item in files if Path(item).name == "AGENTS.md"), 80)
    agents_bytes: dict[str, int | None] = {}
    for relative in agents_files:
        try:
            agents_bytes[relative] = (root / relative).stat().st_size
        except OSError:
            agents_bytes[relative] = None
    documents = _document_classification(files)
    release = _release_surfaces(files)
    language_counts = _language_counts(files)
    catalogs = _bounded(
        item
        for item in files
        if Path(item).name.lower() in {"backstage.yaml", "catalog-info.yaml", "catalog.toml"}
    )
    result: dict[str, Any] = {
        "name": root.name,
        "root": str(root),
        "repository_type": repository_type,
        "file_inventory_source": file_source,
        "file_count": len(files),
        "languages": [
            {"name": name, "files": count}
            for name, count in sorted(language_counts.items(), key=lambda item: (-item[1], item[0]))[:12]
        ],
        "manifests": manifests,
        "workspace_evidence": workspace_evidence,
        "component_hints": component_hints,
        "agents_files": agents_files,
        "agents_bytes": agents_bytes,
        "documents": documents,
        "release": release,
        "knowledge": {
            "root_agents": "AGENTS.md" in agents_files,
            "stable_index": bool(documents["stable_indexes"]),
            "architecture": documents["has_architecture"],
            "decisions": documents["has_decisions"],
            "runbooks": documents["has_runbooks"],
            "fork_records": documents["has_fork_records"],
            "workstreams": documents["has_workstreams"],
            "generated_map": bool(documents["generated_maps"]),
            "catalog": bool(catalogs),
        },
        "catalogs": catalogs,
    }
    result["recommendations"] = _recommendations(result)
    return result


def _unversioned_container_knowledge(container: Path, repository_roots: set[Path]) -> dict[str, Any]:
    documents: list[str] = []
    agents: list[str] = []
    container_is_document_root = container.name.lower() in {"doc", "docs", "documentation"}
    for current, directories, filenames in os.walk(container):
        current_path = Path(current).resolve()
        depth = len(current_path.relative_to(container.resolve()).parts)
        if depth > 4:
            directories[:] = []
            continue
        directories[:] = [
            name
            for name in directories
            if not _is_excluded(name) and (current_path / name).resolve() not in repository_roots
        ]
        for filename in filenames:
            relative = (current_path / filename).relative_to(container.resolve()).as_posix()
            if filename == "AGENTS.md":
                agents.append(relative)
            path = Path(relative)
            if path.suffix.lower() in DOCUMENT_EXTENSIONS and (
                container_is_document_root
                or len(path.parts) == 1
                or path.parts[0].lower() in {"doc", "docs", "documentation"}
            ):
                documents.append(relative)
    return {
        "documents": _bounded(documents, 80),
        "document_count": len(set(documents)),
        "agents_files": _bounded(agents, 20),
    }


def workspace_entries(target: Path, roots: list[Path]) -> list[dict[str, Any]]:
    if _is_git_root(target):
        return []
    entries: list[dict[str, Any]] = []
    root_set = set(roots)
    for child in sorted(item for item in target.iterdir() if item.is_dir() and not item.is_symlink()):
        if _is_excluded(child.name) or child.name.startswith("."):
            continue
        members = [root for root in roots if root == child or child in root.parents]
        if child in root_set:
            kind = "git-repository"
            knowledge = {"documents": [], "document_count": 0, "agents_files": []}
        elif len(members) > 1:
            kind = "multi-repository-container"
            knowledge = _unversioned_container_knowledge(child, set(members))
        elif len(members) == 1:
            kind = "repository-container"
            knowledge = _unversioned_container_knowledge(child, set(members))
        else:
            kind = "unversioned-directory"
            knowledge = _unversioned_container_knowledge(child, set())
        entries.append(
            {
                "path": child.relative_to(target).as_posix(),
                "kind": kind,
                "repository_count": len(members),
                "repository_paths": [root.relative_to(target).as_posix() for root in members],
                "unversioned_knowledge": knowledge,
            }
        )
    return entries


def scan(target: Path, max_depth: int = DEFAULT_MAX_DISCOVERY_DEPTH) -> dict[str, Any]:
    target = target.expanduser().resolve()
    if not target.exists() or not target.is_dir():
        raise ValueError(f"root is not a directory: {target}")
    roots, exclusions = discover_git_roots(target, max_depth)
    repositories = [scan_repository(root) for root in roots]
    target_is_subtree = len(roots) == 1 and roots[0] in target.parents
    for repository, root in zip(repositories, roots):
        repository["relative_path"] = "." if root == target or root in target.parents else root.relative_to(target).as_posix()
    entries = [] if target_is_subtree else workspace_entries(target, roots)
    if len(repositories) == 1 and (roots[0] == target or target_is_subtree):
        topology = repositories[0]["repository_type"]
    elif len(repositories) > 1:
        topology = "multi-repository-workspace"
    elif len(repositories) == 1:
        topology = "workspace-with-one-repository"
    else:
        topology = "workspace-without-repository"
    return {
        "schema_version": SCHEMA_VERSION,
        "target": str(target),
        "topology": topology,
        "repository_count": len(repositories),
        "repositories": repositories,
        "workspace_entry_count": len(entries),
        "workspace_entries": entries,
        "discovery": {
            "max_depth": max_depth,
            "excluded_directory_names": sorted(EXCLUDED_DIRECTORY_NAMES),
            "excluded_path_count": len(exclusions),
            "excluded_path_examples": exclusions[:40],
        },
        "program_hub": {
            "classification": "owner-input-required" if len(repositories) > 1 else "not-applicable",
            "question": (
                "Does this workspace own durable cross-repository architecture, contracts, operations, or coordinated delivery?"
                if len(repositories) > 1
                else None
            ),
        },
    }


def build_plan(report: dict[str, Any]) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    if report["topology"] == "multi-repository-workspace":
        actions.append(
            {
                "scope": report["target"],
                "artifact": "program-hub",
                "disposition": "owner-input-required",
                "reason": "Multiple independent Git roots are present, but directory grouping alone does not establish program authority.",
                "proposal": "If confirmed, create a versioned meta repository with a stable index, curated component catalog, cross-repository contracts, ADRs, runbooks, and orchestration entrypoints.",
            }
        )
    for entry in report["workspace_entries"]:
        scope = str(Path(report["target"]) / entry["path"])
        knowledge = entry["unversioned_knowledge"]
        if entry["kind"] == "multi-repository-container":
            actions.append(
                {
                    "scope": scope,
                    "artifact": "container-ownership",
                    "disposition": "owner-input-required",
                    "reason": "The directory contains multiple independently versioned repositories.",
                    "proposal": "Confirm whether it is a durable program boundary; if so, create a versioned meta repository, otherwise move each cross-repository fact to its owning child.",
                }
            )
        elif entry["kind"] == "repository-container":
            actions.append(
                {
                    "scope": scope,
                    "artifact": "container-ownership",
                    "disposition": "audit",
                    "reason": "The directory contains one nested Git root but is not itself versioned.",
                    "proposal": "Confirm whether parent-level source and documents belong in the child repository or justify a versioned parent boundary.",
                }
            )
        elif entry["kind"] == "unversioned-directory":
            actions.append(
                {
                    "scope": scope,
                    "artifact": "repository-ownership",
                    "disposition": "owner-input-required",
                    "reason": "No Git root was discovered in this development directory.",
                    "proposal": "Decide whether the directory is an active unversioned project, an archive, or content that belongs in another repository before generating maintained knowledge.",
                }
            )
        if knowledge["document_count"] or knowledge["agents_files"]:
            actions.append(
                {
                    "scope": scope,
                    "artifact": "unversioned-knowledge",
                    "disposition": "adopt-or-move",
                    "reason": f"The container has {knowledge['document_count']} documentation files and {len(knowledge['agents_files'])} AGENTS.md files outside an owning Git root.",
                    "proposal": "Move each durable fact into its owning repository or adopt the container as a versioned program hub; do not leave shared knowledge without versioned ownership.",
                }
            )
    for repo in report["repositories"]:
        root = repo["root"]
        if repo["knowledge"]["root_agents"]:
            actions.append(
                {
                    "scope": root,
                    "artifact": "AGENTS.md",
                    "disposition": "audit-and-keep",
                    "reason": "A root instruction file exists.",
                    "proposal": "Keep it concise and route detailed facts to canonical documents or native controls.",
                }
            )
        else:
            actions.append(
                {
                    "scope": root,
                    "artifact": "AGENTS.md",
                    "disposition": "create-after-fact-confirmation",
                    "reason": "No root AGENTS.md was detected.",
                    "proposal": "Add scope, stable knowledge entrypoint, verified golden commands, protected boundaries, and knowledge-update routing only.",
                }
            )

        if repo["documents"]["stable_indexes"]:
            actions.append(
                {
                    "scope": root,
                    "artifact": repo["documents"]["stable_indexes"][0],
                    "disposition": "audit-and-keep",
                    "reason": "A stable documentation index exists.",
                    "proposal": "Repair routing and ownership gaps instead of creating a parallel index.",
                }
            )
        elif repo["repository_type"] == "monorepo" or repo["documents"]["repository_document_count"] >= 3:
            actions.append(
                {
                    "scope": root,
                    "artifact": "docs/index.md",
                    "disposition": "create-or-designate",
                    "reason": "The repository has several components or maintained document surfaces without a detected stable docs index.",
                    "proposal": "Describe component purpose/boundaries and route architecture, contracts, decisions, runbooks, workstreams, and generated references.",
                }
            )
        else:
            actions.append(
                {
                    "scope": root,
                    "artifact": "README.md",
                    "disposition": "designate-or-repair",
                    "reason": "A small repository does not automatically justify a second index.",
                    "proposal": "Use README as the stable index unless a distinct documentation hierarchy is confirmed.",
                }
            )

        if repo["repository_type"] == "monorepo":
            actions.append(
                {
                    "scope": root,
                    "artifact": "component-routing",
                    "disposition": "owner-input-required",
                    "reason": "Workspace evidence exists, but directory structure does not prove local instruction or ownership boundaries.",
                    "proposal": "Add nested indexes or AGENTS.md only where tooling, ownership, security, verification, or release semantics differ.",
                }
            )

        if repo["release"]["has_release_automation"]:
            actions.append(
                {
                    "scope": root,
                    "artifact": "release-knowledge",
                    "disposition": "map-before-edit",
                    "reason": "Release workflows or scripts were detected.",
                    "proposal": "Map update documents and automation first; keep judgment/recovery in a runbook and repeated deterministic actions in repository commands.",
                }
            )

    return {
        "schema_version": SCHEMA_VERSION,
        "target": report["target"],
        "topology": report["topology"],
        "principles": [
            "one durable fact has one canonical owner",
            "AGENTS.md routes instead of duplicating",
            "generated maps are replaceable evidence, not policy",
            "inferred rules require owner confirmation before promotion",
        ],
        "actions": actions,
    }


def _task_tokens(task: str) -> list[str]:
    tokens: set[str] = set()
    for raw in TASK_TOKEN_RE.findall(task):
        lowered = raw.lower()
        tokens.add(lowered)
        tokens.update(part for part in lowered.split("_") if len(part) >= 2)
    return sorted(token for token in tokens if len(token) >= 2)


def _symbols(text: str) -> list[str]:
    return _bounded(SYMBOL_RE.findall(text), 20)


def build_task_map(
    report: dict[str, Any],
    task: str,
    file_budget: int = 30,
    max_scan_files: int = 10_000,
) -> dict[str, Any]:
    if file_budget <= 0 or max_scan_files <= 0:
        raise ValueError("file-budget and max-scan-files must be positive")
    tokens = _task_tokens(task)
    if not tokens:
        raise ValueError("task must contain at least one searchable word or phrase")
    candidates: list[dict[str, Any]] = []
    scanned_text_files = 0
    truncated = False
    for repo in report["repositories"]:
        root = Path(repo["root"])
        files, _ = repository_files(root)
        for relative in files:
            path = Path(relative)
            lower_path = relative.lower()
            score = 0
            reasons: list[str] = []
            path_hits = [token for token in tokens if token in lower_path]
            if path_hits:
                score += 12 * len(path_hits)
                reasons.append("path:" + ",".join(path_hits))

            is_anchor = relative in {"AGENTS.md", "README.md", "README.mdx", "docs/index.md", "docs/README.md"}
            is_manifest = path.name in MANIFEST_NAMES
            if is_anchor:
                score += 2
                reasons.append("navigation-anchor")
            elif is_manifest:
                score += 1
                reasons.append("manifest")

            text = ""
            content_hits: list[str] = []
            if path.suffix.lower() in TEXT_SOURCE_EXTENSIONS:
                if scanned_text_files >= max_scan_files:
                    truncated = True
                else:
                    scanned_text_files += 1
                    text = _read_text(
                        root / relative, max_bytes=1024 * 1024, root=root
                    )
                    lower_text = text.lower()
                    for token in tokens:
                        count = lower_text.count(token)
                        if count:
                            score += min(count, 8) * 3
                            content_hits.append(token)
                    if content_hits:
                        reasons.append("content:" + ",".join(content_hits))

            if score <= 0:
                continue
            if any(part.lower() in {"test", "tests", "testing"} for part in path.parts) and (path_hits or content_hits):
                score += 2
                reasons.append("test-evidence")
            candidates.append(
                {
                    "repository": repo["relative_path"],
                    "path": relative,
                    "score": score,
                    "reasons": reasons,
                    "symbols": _symbols(text) if text else [],
                }
            )

    selected = sorted(candidates, key=lambda item: (-item["score"], item["repository"], item["path"]))[
        :file_budget
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "derived_evidence": True,
        "target": report["target"],
        "task": task,
        "tokens": tokens,
        "file_budget": file_budget,
        "max_scan_files": max_scan_files,
        "scanned_text_files": scanned_text_files,
        "scan_truncated": truncated,
        "selected_files": selected,
        "limitations": [
            "Ranking is lexical and path-based; it does not prove call-graph or runtime relevance.",
            "Selected symbols are regex-derived hints and must be verified in source.",
            "The map is replaceable task evidence, not repository policy.",
        ],
    }


def _markdown_files(root: Path) -> list[str]:
    files, _ = repository_files(root)
    return sorted(item for item in files if Path(item).suffix.lower() in {".md", ".mdx"})


def _check_links(root: Path, repo: dict[str, Any]) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    observed: set[tuple[str, str, str]] = set()
    for relative in _markdown_files(root):
        source = root / relative
        text = _read_text(source, max_bytes=2 * 1024 * 1024, root=root)
        if not text:
            continue
        text = re.sub(r"(?ms)^\s*(```|~~~).*?^\s*\1\s*$", "", text)
        for raw_target in MARKDOWN_LINK_RE.findall(text):
            stripped_target = raw_target.strip()
            if stripped_target.startswith("<") and ">" in stripped_target:
                target = stripped_target[1 : stripped_target.index(">")]
            else:
                target = stripped_target.split(maxsplit=1)[0]
            if not target or target.startswith("#"):
                continue
            if any(token in target for token in ("{", "}", "$", "*")):
                continue
            decoded = unquote(target.split("#", 1)[0].split("?", 1)[0])
            if not decoded or decoded.startswith("/"):
                continue
            if WINDOWS_ABSOLUTE_RE.match(decoded):
                key = ("nonportable-local-link", relative, "drive-path")
                if key not in observed:
                    observed.add(key)
                    findings.append(
                        {
                            "severity": "error",
                            "code": "nonportable-local-link",
                            "path": relative,
                            "message": "Document contains a non-portable machine-local link target.",
                        }
                    )
                continue
            if URI_SCHEME_RE.match(decoded):
                continue
            if "/" not in decoded and "\\" not in decoded and "." not in decoded:
                continue
            resolved = (source.parent / decoded).resolve()
            try:
                resolved.relative_to(root.resolve())
            except ValueError:
                key = ("link-escapes-repository", relative, target)
                if key not in observed:
                    observed.add(key)
                    findings.append(
                        {
                            "severity": "error",
                            "code": "link-escapes-repository",
                            "path": relative,
                            "message": f"Relative link escapes repository: {target}",
                        }
                    )
                continue
            if not resolved.exists():
                key = ("broken-relative-link", relative, target)
                if key not in observed:
                    observed.add(key)
                    findings.append(
                        {
                            "severity": "error",
                            "code": "broken-relative-link",
                            "path": relative,
                            "message": f"Missing relative link target: {target}",
                        }
                    )
    return findings


def check_report(
    report: dict[str, Any],
    agents_warn_bytes: int = DEFAULT_AGENTS_WARN_BYTES,
    agents_error_bytes: int = DEFAULT_AGENTS_ERROR_BYTES,
) -> dict[str, Any]:
    findings: list[dict[str, str]] = []
    for repo in report["repositories"]:
        root = Path(repo["root"])
        if not repo["knowledge"]["root_agents"]:
            findings.append(
                {
                    "severity": "warning",
                    "code": "missing-root-agents",
                    "path": str(root),
                    "message": "No root AGENTS.md was detected; confirm whether repository-specific routing is needed.",
                }
            )
        for relative, size in repo["agents_bytes"].items():
            if size is None:
                continue
            if size > agents_error_bytes:
                severity = "error"
            elif size > agents_warn_bytes:
                severity = "warning"
            else:
                continue
            findings.append(
                {
                    "severity": severity,
                    "code": "agents-context-budget",
                    "path": str(root / relative),
                    "message": f"AGENTS.md is {size} bytes; prefer a concise router and progressive disclosure.",
                }
            )
        if not repo["knowledge"]["stable_index"] and (
            repo["repository_type"] == "monorepo" or repo["documents"]["repository_document_count"] >= 3
        ):
            findings.append(
                {
                    "severity": "warning",
                    "code": "missing-stable-doc-index",
                    "path": str(root),
                    "message": "Several knowledge surfaces exist but no docs index was detected.",
                }
            )
        findings.extend(_check_links(root, repo))
    counts = Counter(item["severity"] for item in findings)
    return {
        "schema_version": SCHEMA_VERSION,
        "target": report["target"],
        "topology": report["topology"],
        "status": "failed" if counts["error"] else "passed-with-warnings" if counts["warning"] else "passed",
        "counts": {"errors": counts["error"], "warnings": counts["warning"]},
        "findings": findings,
    }


def _repo_languages(repo: dict[str, Any]) -> str:
    names = [item["name"] for item in repo["languages"][:4]]
    return ", ".join(names) if names else "not detected"


def scan_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Repository knowledge inventory",
        "",
        f"- Target: `{report['target']}`",
        f"- Topology: `{report['topology']}`",
        f"- Git repositories: {report['repository_count']}",
        f"- Excluded generated/cache/vendor paths observed: {report['discovery']['excluded_path_count']}",
        "",
    ]
    if report["workspace_entries"]:
        lines.extend(
            [
                "## Development directories",
                "",
                "| Directory | Kind | Git repositories | Unversioned docs |",
                "|---|---|---:|---:|",
            ]
        )
        for entry in report["workspace_entries"]:
            lines.append(
                f"| {entry['path']} | {entry['kind']} | {entry['repository_count']} | {entry['unversioned_knowledge']['document_count']} |"
            )
        lines.append("")
        lines.append("## Git repositories")
        lines.append("")
    if report["repositories"]:
        lines.extend(
            [
                "| Repository | Shape | Languages | AGENTS | Docs | Index | Release automation |",
                "|---|---|---|---:|---:|---|---|",
            ]
        )
        for repo in report["repositories"]:
            lines.append(
                "| {name} | {shape} | {languages} | {agents} | {docs} | {index} | {release} |".format(
                    name=repo["relative_path"],
                    shape=repo["repository_type"],
                    languages=_repo_languages(repo),
                    agents=len(repo["agents_files"]),
                    docs=repo["documents"]["document_count"],
                    index="yes" if repo["knowledge"]["stable_index"] else "no",
                    release="yes" if repo["release"]["has_release_automation"] else "no",
                )
            )
        lines.append("")
    for repo in report["repositories"]:
        if not repo["recommendations"]:
            continue
        lines.extend([f"## {repo['relative_path']}", ""])
        for recommendation in repo["recommendations"]:
            lines.append(
                f"- `{recommendation['classification']}` — {recommendation['action']} ({recommendation['reason']})"
            )
        lines.append("")
    if report["topology"] == "multi-repository-workspace":
        lines.extend(
            [
                "## Program boundary",
                "",
                "`owner-input-required`: confirm that this directory owns durable cross-repository architecture, contracts, operations, or coordinated delivery before creating a meta repository or shared catalog.",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Repository knowledge plan",
        "",
        f"- Target: `{plan['target']}`",
        f"- Topology: `{plan['topology']}`",
        "",
        "| Scope | Artifact | Disposition | Reason |",
        "|---|---|---|---|",
    ]
    for action in plan["actions"]:
        lines.append(
            f"| {action['scope']} | `{action['artifact']}` | `{action['disposition']}` | {action['reason']} |"
        )
    lines.extend(["", "## Proposed outcomes", ""])
    for action in plan["actions"]:
        lines.append(f"- `{action['artifact']}`: {action['proposal']}")
    return "\n".join(lines).rstrip() + "\n"


def map_markdown(task_map: dict[str, Any]) -> str:
    lines = [
        "# Task-specific repository map",
        "",
        f"- Target: `{task_map['target']}`",
        f"- Task: {task_map['task']}",
        f"- Search tokens: {', '.join(task_map['tokens'])}",
        f"- Selected files: {len(task_map['selected_files'])} / budget {task_map['file_budget']}",
        f"- Text files inspected locally: {task_map['scanned_text_files']}",
        f"- Scan truncated: {'yes' if task_map['scan_truncated'] else 'no'}",
        "",
        "| Score | Repository | Path | Why selected | Symbols |",
        "|---:|---|---|---|---|",
    ]
    for item in task_map["selected_files"]:
        symbols = ", ".join(item["symbols"][:8]) or "—"
        lines.append(
            f"| {item['score']} | {item['repository']} | `{item['path']}` | {', '.join(item['reasons'])} | {symbols} |"
        )
    lines.extend(["", "This is derived retrieval evidence. Verify the selected source before deciding or editing."])
    return "\n".join(lines).rstrip() + "\n"


def check_markdown(result: dict[str, Any]) -> str:
    lines = [
        "# Repository knowledge check",
        "",
        f"- Target: `{result['target']}`",
        f"- Status: `{result['status']}`",
        f"- Errors: {result['counts']['errors']}",
        f"- Warnings: {result['counts']['warnings']}",
        "",
    ]
    for finding in result["findings"]:
        lines.append(
            f"- **{finding['severity'].upper()}** `{finding['code']}` `{finding['path']}` — {finding['message']}"
        )
    if not result["findings"]:
        lines.append("No deterministic knowledge findings.")
    return "\n".join(lines).rstrip() + "\n"


def _emit(value: dict[str, Any], output_format: str, mode: str) -> None:
    if output_format == "json":
        print(json.dumps(value, indent=2, ensure_ascii=False, sort_keys=True))
        return
    if mode == "scan":
        print(scan_markdown(value), end="")
    elif mode == "plan":
        print(plan_markdown(value), end="")
    elif mode == "map":
        print(map_markdown(value), end="")
    else:
        print(check_markdown(value), end="")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("scan", "plan", "map", "check"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--root", required=True, help="Repository or workspace path")
        subparser.add_argument(
            "--format",
            choices=("json", "markdown"),
            default="json",
            dest="output_format",
        )
        subparser.add_argument(
            "--max-depth",
            type=int,
            default=DEFAULT_MAX_DISCOVERY_DEPTH,
            help="Maximum workspace depth used to discover Git roots",
        )
    map_parser = subparsers.choices["map"]
    map_parser.add_argument("--task", required=True, help="Task description used only for local relevance ranking")
    map_parser.add_argument("--file-budget", type=int, default=30)
    map_parser.add_argument("--max-scan-files", type=int, default=10_000)
    check_parser = subparsers.choices["check"]
    check_parser.add_argument("--strict", action="store_true", help="Return non-zero for warnings as well as errors")
    check_parser.add_argument("--agents-warn-bytes", type=int, default=DEFAULT_AGENTS_WARN_BYTES)
    check_parser.add_argument("--agents-error-bytes", type=int, default=DEFAULT_AGENTS_ERROR_BYTES)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        report = scan(Path(args.root), max_depth=args.max_depth)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    if args.command == "scan":
        _emit(report, args.output_format, "scan")
        return 0
    if args.command == "plan":
        plan = build_plan(report)
        _emit(plan, args.output_format, "plan")
        return 0
    if args.command == "map":
        try:
            task_map = build_task_map(
                report,
                args.task,
                file_budget=args.file_budget,
                max_scan_files=args.max_scan_files,
            )
        except ValueError as error:
            print(str(error), file=sys.stderr)
            return 2
        _emit(task_map, args.output_format, "map")
        return 0

    result = check_report(
        report,
        agents_warn_bytes=args.agents_warn_bytes,
        agents_error_bytes=args.agents_error_bytes,
    )
    _emit(result, args.output_format, "check")
    if result["counts"]["errors"]:
        return 1
    if args.strict and result["counts"]["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
