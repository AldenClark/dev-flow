#!/usr/bin/env python3
"""Thin structural validation for Dev Flow project knowledge.

The validator deliberately checks only mechanical contracts.  It does not score
document quality, infer meaning, generate files, promote knowledge, or mutate a
repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any
from urllib.parse import unquote


SCHEMA_VERSION = "1.0"
DEFAULT_PROJECT_ROOT = "docs/project"
DEFAULT_CHANGES_ROOT = "docs/changes"
DEFAULT_CONVENTION_PATH = ".dev-flow/knowledge.json"
RUNTIME_ROOT = ".codex/dev-flow"
RUNTIME_IGNORE_PATTERNS = {
    ".codex/",
    ".codex/**",
    ".codex/*",
    ".codex/dev-flow",
    ".codex/dev-flow/",
    ".codex/dev-flow/**",
    ".codex/dev-flow/*",
}

SAFE_CHANGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]{0,80}$")
KNOWLEDGE_ID = re.compile(r"^KT-[A-Z0-9][A-Z0-9._-]{0,40}$")
ID_PATTERNS = {
    "acceptance_criteria": re.compile(r"^AC-[1-9][0-9]*$"),
    "scope": re.compile(r"^SC-(?:D|I|C|P|O|L)[1-9][0-9]*$"),
    "verification_obligations": re.compile(r"^VO-[1-9][0-9]*$"),
}
DIGEST_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")
NORMATIVE_ID = re.compile(
    r"^\s*(?:[-*+]\s+|\|\s*)"
    r"(?P<id>AC-[1-9][0-9]*|SC-(?:D|I|C|P|O|L)[1-9][0-9]*|VO-[1-9][0-9]*)"
    r"\s*(?:[:：]|\|)"
)

PLACEHOLDER_PATTERNS = (
    re.compile(r"\{\{[^{}\n]+\}\}"),
    re.compile(r"(?im)^\s*(?:[-*]\s*)?(?:TODO|TBD|TBC|FIXME)(?:\([^)]+\))?\s*[:：-]"),
    re.compile(r"[\"'](?:TODO|TBD|TBC|FIXME)[\"']", re.IGNORECASE),
    re.compile(r"\?\?\?"),
)
ANGLE_PLACEHOLDER = re.compile(r"<(?!(?:https?|mailto):)(?P<value>[A-Za-z][^<>\n]{0,100})>")
ANGLE_PLACEHOLDER_TERMS = {
    "acceptance",
    "actor",
    "artifact",
    "authority",
    "base-git-state",
    "change-id",
    "command",
    "criterion",
    "digest",
    "environment",
    "evidence",
    "exact",
    "implementation",
    "knowledge-id",
    "objective",
    "observable",
    "owner",
    "path",
    "repository-root",
    "repository-roots",
    "requirement",
    "result",
    "revision",
    "scope",
    "source",
    "status",
    "verification",
}
HTML_TAGS = {
    "a",
    "abbr",
    "address",
    "area",
    "article",
    "aside",
    "audio",
    "b",
    "base",
    "bdi",
    "bdo",
    "blockquote",
    "body",
    "br",
    "button",
    "canvas",
    "caption",
    "cite",
    "code",
    "col",
    "colgroup",
    "data",
    "datalist",
    "dd",
    "del",
    "details",
    "dfn",
    "dialog",
    "div",
    "dl",
    "dt",
    "em",
    "embed",
    "fieldset",
    "figcaption",
    "figure",
    "footer",
    "form",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "head",
    "header",
    "hgroup",
    "hr",
    "html",
    "i",
    "iframe",
    "img",
    "input",
    "ins",
    "kbd",
    "label",
    "legend",
    "li",
    "link",
    "main",
    "map",
    "mark",
    "menu",
    "meta",
    "meter",
    "nav",
    "noscript",
    "object",
    "ol",
    "optgroup",
    "option",
    "output",
    "p",
    "picture",
    "pre",
    "progress",
    "q",
    "rp",
    "rt",
    "ruby",
    "s",
    "samp",
    "script",
    "search",
    "section",
    "select",
    "slot",
    "small",
    "source",
    "span",
    "strong",
    "style",
    "sub",
    "summary",
    "sup",
    "table",
    "tbody",
    "td",
    "template",
    "textarea",
    "tfoot",
    "th",
    "thead",
    "time",
    "title",
    "tr",
    "track",
    "u",
    "ul",
    "var",
    "video",
    "wbr",
}
MARKDOWN_FENCED_CODE = re.compile(r"(?ms)^(?: {0,3})(`{3,}|~{3,}).*?^ {0,3}\1\s*$")
MARKDOWN_INDENTED_CODE = re.compile(r"(?m)^(?: {4}|\t).*$")
MARKDOWN_CODE_SPAN = re.compile(r"(?P<ticks>`+)(?!`)(?P<body>[^\n]*?)(?P=ticks)(?!`)")
ABSOLUTE_LOCAL_PATH_PATTERNS = (
    re.compile(r"\bfile://", re.IGNORECASE),
    re.compile(
        r"(?<![A-Za-z0-9])/(?:Applications|Library|System|Users|bin|boot|data|dev|etc|home|lib|lib64|"
        r"media|mnt|nix|opt|private|proc|root|run|sbin|srv|sys|tmp|usr|var|workspace|Volumes)/"
        r"[^\s)`\]}>]+"
    ),
    re.compile(r"(?<![A-Za-z0-9])~/[^\s)`\]}>]+"),
    re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s)`\]}>]+"),
    re.compile(r"\\\\[^\\\s]+\\[^\s)`\]}>]+"),
)
SENSITIVE_PATTERNS = (
    ("private key", re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("provider token", re.compile(r"\b(?:sk-|ghp_|github_pat_)[A-Za-z0-9_-]{20,}\b")),
    ("bearer credential", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}", re.IGNORECASE)),
    (
        "credential assignment",
        re.compile(
            r"\b(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)"
            r"\s*[:=]\s*[\"']?(?!(?:redacted|masked|none|null|example|placeholder)\b)"
            r"[A-Za-z0-9._~+/=-]{8,}",
            re.IGNORECASE,
        ),
    ),
    ("credential-bearing URL", re.compile(r"\bhttps?://[^\s/:@]+:[^\s/@]+@", re.IGNORECASE)),
)
MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\((?P<body><[^>]+>|[^)]+)\)")

CHANGE_STATUSES = {
    "draft",
    "discovering",
    "awaiting-approval",
    "approved",
    "implementing",
    "verifying",
    "accepted",
    "blocked",
    "superseded",
    "abandoned",
}
TERMINAL_ACCEPTED_STATUSES = {"accepted", "superseded"}
KNOWLEDGE_IMPACTS = {"none", "add", "update", "deprecate"}
KNOWLEDGE_DISPOSITIONS = {"not-applicable", "pending", "promoted", "deferred"}
TEST_STATUSES = {"planned", "passed", "failed", "blocked", "not-applicable"}
EXPECTED_DOCUMENTS = {
    "single": {"change": "change.md"},
    "governed": {
        "requirements": "requirements.md",
        "design": "design.md",
        "execution": "execution.md",
        "verification": "verification.md",
    },
}


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_within(path: Path, owner: Path) -> bool:
    return path == owner or path.is_relative_to(owner)


def _existing_symlink(path: Path, owner: Path) -> Path | None:
    """Return the first existing symlink from owner through path."""
    if owner.is_symlink():
        return owner
    if not _is_within(path, owner):
        return None
    current = owner
    for part in path.relative_to(owner).parts:
        current /= part
        if current.is_symlink():
            return current
    return None


def _relative_path(
    owner: Path,
    value: object,
    *,
    label: str,
    boundary: Path | None = None,
    allow_parent: bool = False,
) -> tuple[Path | None, str | None]:
    if not isinstance(value, str) or not value.strip():
        return None, f"{label} must be a non-empty POSIX relative path"
    if "\\" in value or PureWindowsPath(value).is_absolute():
        return None, f"{label} must not be an absolute or Windows-style path: {value}"
    pure = PurePosixPath(value)
    if pure.is_absolute():
        return None, f"{label} must be relative: {value}"
    if any(part in {"", "."} for part in pure.parts):
        return None, f"{label} contains a forbidden path component: {value}"
    if not allow_parent and ".." in pure.parts:
        return None, f"{label} contains traversal: {value}"
    candidate = Path(os.path.abspath(owner.joinpath(*pure.parts)))
    allowed = Path(os.path.abspath(boundary or owner))
    if not _is_within(candidate, allowed):
        return None, f"{label} escapes {allowed}: {value}"
    symlink = _existing_symlink(candidate, allowed)
    if symlink is not None:
        return None, f"{label} must not traverse a symlink: {symlink}"
    resolved_owner = allowed.resolve()
    resolved = candidate.resolve(strict=False)
    if not _is_within(resolved, resolved_owner):
        return None, f"{label} resolves outside {resolved_owner}: {value}"
    return candidate, None


def _load_json(path: Path, label: str, errors: list[str]) -> dict[str, Any] | None:
    if path.is_symlink():
        errors.append(f"{label} must not be a symlink: {path}")
        return None
    if not path.is_file():
        errors.append(f"{label} is missing or is not a regular file: {path}")
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(f"{label} is not readable JSON: {path}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object: {path}")
        return None
    return value


def _text_issues(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    def mask(match: re.Match[str]) -> str:
        return "".join("\n" if character == "\n" else " " for character in match.group(0))

    placeholder_text = MARKDOWN_FENCED_CODE.sub(mask, text)
    placeholder_text = MARKDOWN_INDENTED_CODE.sub(mask, placeholder_text)
    placeholder_text = MARKDOWN_CODE_SPAN.sub(mask, placeholder_text)
    for pattern in PLACEHOLDER_PATTERNS:
        for match in pattern.finditer(placeholder_text):
            issues.append(
                f"unresolved placeholder in {path}:{_line_number(text, match.start())}: {match.group(0)!r}"
            )
    for match in ANGLE_PLACEHOLDER.finditer(placeholder_text):
        value = match.group("value").strip().lower()
        tag_match = re.match(r"/?([a-z][a-z0-9-]*)\b", value)
        if tag_match is not None and tag_match.group(1) in HTML_TAGS:
            continue
        words = set(re.findall(r"[a-z][a-z0-9-]*", value))
        if words.isdisjoint(ANGLE_PLACEHOLDER_TERMS):
            continue
        issues.append(
            f"unresolved placeholder in {path}:{_line_number(text, match.start())}: {match.group(0)!r}"
        )
    for pattern in ABSOLUTE_LOCAL_PATH_PATTERNS:
        for match in pattern.finditer(text):
            issues.append(
                f"absolute local path in {path}:{_line_number(text, match.start())}: {match.group(0)!r}"
            )
    for name, pattern in SENSITIVE_PATTERNS:
        for match in pattern.finditer(text):
            issues.append(f"secret-like {name} content in {path}:{_line_number(text, match.start())}")
    return issues


def _inventory_regular_files(root: Path, *, label: str, errors: list[str]) -> set[Path]:
    """Inventory a tracked plane without following symlinks."""
    files: set[Path] = set()
    def record_walk_error(error: OSError) -> None:
        errors.append(f"cannot inventory {label}: {error}")

    for directory, directory_names, file_names in os.walk(
        root,
        followlinks=False,
        onerror=record_walk_error,
    ):
        parent = Path(directory)
        for name in directory_names:
            child = parent / name
            if child.is_symlink():
                errors.append(f"{label} contains a symlink: {child}")
        for name in file_names:
            child = parent / name
            if child.is_symlink():
                errors.append(f"{label} contains a symlink: {child}")
            elif not child.is_file():
                errors.append(f"{label} contains a non-regular file: {child}")
            else:
                files.add(Path(os.path.abspath(child)))
    return files


def _validate_inventory(
    root: Path,
    *,
    label: str,
    expected: set[Path],
    repo_root: Path,
    errors: list[str],
) -> None:
    actual = _inventory_regular_files(root, label=label, errors=errors)
    normalized_expected = {Path(os.path.abspath(path)) for path in expected}
    for path in sorted(actual - normalized_expected):
        errors.append(f"undeclared file in {label}: {path}")
        _read_and_validate_text(path, repo_root=repo_root, errors=errors)


def _markdown_link_target(body: str) -> str:
    body = body.strip()
    if body.startswith("<") and body.endswith(">"):
        return body[1:-1].strip()
    # Markdown's optional title begins after whitespace. Paths containing spaces
    # must use angle brackets, which keeps this parser deterministic.
    return body.split(maxsplit=1)[0]


def _validate_markdown_links(
    path: Path,
    text: str,
    *,
    repo_root: Path,
    required_backlink: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    resolved_targets: set[Path] = set()
    for match in MARKDOWN_LINK.finditer(text):
        target = _markdown_link_target(match.group("body"))
        if not target or target.startswith("#"):
            continue
        lower = target.lower()
        if lower.startswith(("https://", "http://", "mailto:")):
            continue
        if "://" in target or lower.startswith("file:"):
            errors.append(f"unsupported or local URI in {path}: {target}")
            continue
        local = unquote(target.split("#", 1)[0].split("?", 1)[0])
        candidate, error = _relative_path(
            path.parent,
            local,
            label=f"link in {path}",
            boundary=repo_root,
            allow_parent=True,
        )
        if error:
            errors.append(error)
            continue
        assert candidate is not None
        if not candidate.exists():
            errors.append(f"broken local link in {path}: {target}")
            continue
        resolved_targets.add(candidate.resolve())
    if required_backlink is not None and required_backlink.resolve() not in resolved_targets:
        errors.append(f"missing backlink from {path} to {required_backlink.name}")
    return errors


def _read_and_validate_text(
    path: Path,
    *,
    repo_root: Path,
    errors: list[str],
    required_backlink: Path | None = None,
) -> str | None:
    if path.is_symlink():
        errors.append(f"knowledge document must not be a symlink: {path}")
        return None
    if not path.is_file():
        errors.append(f"knowledge document is missing or not a regular file: {path}")
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        errors.append(f"knowledge document is not readable UTF-8: {path}: {exc}")
        return None
    errors.extend(_text_issues(path, text))
    if path.suffix.lower() in {".md", ".markdown"}:
        errors.extend(
            _validate_markdown_links(
                path,
                text,
                repo_root=repo_root,
                required_backlink=required_backlink,
            )
        )
    return text


def _git_runtime_ignore_source(repo_root: Path) -> tuple[Path, str] | None:
    """Return Git's repository-owned exclude file and this root's pattern prefix."""
    try:
        exclude_result = subprocess.run(
            ["git", "rev-parse", "--git-path", "info/exclude"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
        top_result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=repo_root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if exclude_result.returncode or top_result.returncode:
        return None
    raw_exclude = exclude_result.stdout.strip()
    raw_top = top_result.stdout.strip()
    if not raw_exclude or not raw_top:
        return None
    exclude = Path(raw_exclude)
    if not exclude.is_absolute():
        exclude = repo_root / exclude
    try:
        relative = repo_root.resolve().relative_to(Path(raw_top).resolve())
    except (OSError, ValueError):
        return None
    prefix = relative.as_posix().rstrip("/") if relative.parts else ""
    return exclude, prefix


def _validate_runtime_ignore(repo_root: Path, errors: list[str]) -> None:
    """Require a repository-local rule that keeps raw runtime state untracked."""
    sources: list[tuple[Path, str]] = [(repo_root / ".gitignore", "")]
    git_source = _git_runtime_ignore_source(repo_root)
    if git_source is not None and git_source not in sources:
        sources.append(git_source)
    ignored = False
    explicitly_unignored = False
    for source, prefix in sources:
        if source.is_symlink():
            errors.append(f"runtime ignore source must not be a symlink: {source}")
            continue
        if not source.is_file():
            continue
        try:
            lines = source.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError) as exc:
            errors.append(f"runtime ignore source is not readable UTF-8: {source}: {exc}")
            continue
        for raw in lines:
            value = raw.strip()
            if not value or value.startswith("#"):
                continue
            negative = value.startswith("!")
            normalized = value.removeprefix("!").removeprefix("/")
            expected = {
                f"{prefix + '/' if prefix else ''}{pattern}"
                for pattern in RUNTIME_IGNORE_PATTERNS
            }
            runtime_prefix = f"{prefix + '/' if prefix else ''}.codex/dev-flow"
            codex_prefixes = {
                f"{prefix + '/' if prefix else ''}.codex/",
                f"{prefix + '/' if prefix else ''}.codex/**",
                f"{prefix + '/' if prefix else ''}.codex/*",
            }
            if negative and (
                normalized.startswith(runtime_prefix)
                or normalized in codex_prefixes
            ):
                explicitly_unignored = True
            elif not negative and normalized in expected:
                ignored = True
    if not ignored or explicitly_unignored:
        errors.append(
            "runtime evidence root .codex/dev-flow must be covered by a repository-local ignore rule"
        )


def _resolve_roots(
    repo_root: Path,
    *,
    project_root: str | None,
    changes_root: str | None,
    convention_path: str,
    errors: list[str],
) -> tuple[Path | None, Path | None]:
    convention: dict[str, Any] = {}
    if project_root is None or changes_root is None:
        convention_file, error = _relative_path(
            repo_root,
            convention_path,
            label="knowledge convention path",
            boundary=repo_root,
        )
        if error:
            errors.append(error)
        elif convention_file is not None and convention_file.exists():
            loaded = _load_json(convention_file, "knowledge convention", errors)
            if loaded is not None:
                if loaded.get("schema_version") != SCHEMA_VERSION:
                    errors.append("knowledge convention schema_version must be 1.0")
                convention = loaded

    project_value = (
        project_root
        if project_root is not None
        else convention.get("project_root", DEFAULT_PROJECT_ROOT)
    )
    changes_value = (
        changes_root
        if changes_root is not None
        else convention.get("changes_root", DEFAULT_CHANGES_ROOT)
    )
    project, project_error = _relative_path(
        repo_root, project_value, label="project knowledge root", boundary=repo_root
    )
    changes, changes_error = _relative_path(
        repo_root, changes_value, label="change dossier root", boundary=repo_root
    )
    if project_error:
        errors.append(project_error)
    if changes_error:
        errors.append(changes_error)
    if project is None or changes is None:
        return project, changes

    runtime, runtime_error = _relative_path(
        repo_root, RUNTIME_ROOT, label="runtime evidence root", boundary=repo_root
    )
    if runtime_error:
        errors.append(runtime_error)
    if project == changes or _is_within(project, changes) or _is_within(changes, project):
        errors.append("project knowledge root and change dossier root must be disjoint")
    if runtime is not None and (
        _is_within(project, runtime)
        or _is_within(runtime, project)
        or _is_within(changes, runtime)
        or _is_within(runtime, changes)
    ):
        errors.append("tracked knowledge roots must be disjoint from .codex/dev-flow runtime evidence")
    for label, root in (("project knowledge root", project), ("change dossier root", changes)):
        if root.is_symlink():
            errors.append(f"{label} must not be a symlink: {root}")
        elif not root.is_dir():
            errors.append(f"{label} is missing or is not a directory: {root}")
    return project, changes


def _validate_project_catalog(repo_root: Path, project_root: Path, errors: list[str]) -> set[Path]:
    catalog_path = project_root / "catalog.json"
    catalog = _load_json(catalog_path, "project knowledge catalog", errors)
    if catalog is None:
        return set()
    errors.extend(_text_issues(catalog_path, catalog_path.read_text(encoding="utf-8")))
    if catalog.get("schema_version") != SCHEMA_VERSION:
        errors.append("project knowledge catalog schema_version must be 1.0")
    documents = catalog.get("documents")
    if not isinstance(documents, list) or not documents:
        errors.append("project knowledge catalog documents must be a non-empty array")
        return set()
    ids: set[str] = set()
    paths: set[Path] = set()
    declared_paths: set[Path] = {catalog_path}
    for index, entry in enumerate(documents):
        label = f"project knowledge catalog documents[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        knowledge_id = entry.get("knowledge_id")
        if not isinstance(knowledge_id, str) or not KNOWLEDGE_ID.fullmatch(knowledge_id):
            errors.append(f"{label}.knowledge_id must match KT-[A-Z0-9._-]+")
        elif knowledge_id in ids:
            errors.append(f"duplicate current knowledge_id: {knowledge_id}")
        else:
            ids.add(knowledge_id)
        if entry.get("status") != "current":
            errors.append(f"{label}.status must be current; history belongs in Git and change dossiers")
        document, error = _relative_path(
            project_root,
            entry.get("path"),
            label=f"{label}.path",
            boundary=project_root,
        )
        if error:
            errors.append(error)
            continue
        assert document is not None
        resolved = document.resolve(strict=False)
        if resolved in paths:
            errors.append(f"duplicate project knowledge path: {entry.get('path')}")
            continue
        paths.add(resolved)
        declared_paths.add(document)
        _read_and_validate_text(
            document,
            repo_root=repo_root,
            errors=errors,
            required_backlink=catalog_path,
        )
    _validate_inventory(
        project_root,
        label="project knowledge root",
        expected=declared_paths,
        repo_root=repo_root,
        errors=errors,
    )
    return paths


def _validate_id_list(
    value: object,
    name: str,
    errors: list[str],
    *,
    label: str = "traceability",
) -> set[str] | None:
    pattern = ID_PATTERNS[name]
    if not isinstance(value, list) or not value:
        errors.append(f"{label}.{name} must be a non-empty array")
        return None
    seen: set[str] = set()
    valid = True
    for item in value:
        if not isinstance(item, str) or not pattern.fullmatch(item):
            errors.append(f"{label}.{name} contains an invalid ID: {item!r}")
            valid = False
        elif item in seen:
            errors.append(f"{label}.{name} contains duplicate ID: {item}")
            valid = False
        else:
            seen.add(item)
    return seen if valid else None


def _normative_id_declarations(
    text: str,
    *,
    path: Path,
    errors: list[str],
) -> dict[str, set[str]]:
    """Extract explicit Markdown ID definitions, not incidental prose mentions."""
    declarations = {name: set() for name in ID_PATTERNS}
    for line_number, raw in enumerate(text.splitlines(), start=1):
        normalized = raw.replace("**", "").replace("__", "").replace("`", "")
        match = NORMATIVE_ID.match(normalized)
        if match is None:
            continue
        identifier = match.group("id")
        if identifier.startswith("AC-"):
            family = "acceptance_criteria"
        elif identifier.startswith("SC-"):
            family = "scope"
        else:
            family = "verification_obligations"
        if identifier in declarations[family]:
            errors.append(
                f"duplicate normative {family} declaration in {path}:{line_number}: {identifier}"
            )
        declarations[family].add(identifier)
    return declarations


def _validate_authority_binding(
    manifest: dict[str, Any],
    manifest_path: Path,
    errors: list[str],
) -> None:
    """Validate an explicitly opted-in exact-byte change-authority binding."""
    binding = manifest.get("authority_binding")
    if binding is None:
        # Compatibility boundary: old dossiers remain readable and are never
        # silently migrated into a contract they did not declare.
        return
    if not isinstance(binding, dict):
        errors.append(f"{manifest_path}: authority_binding must be an object")
        return
    expected_binding_keys = {
        "schema_version",
        "change_id",
        "requirements",
        "design",
        "identifier_sets",
    }
    if set(binding) != expected_binding_keys:
        errors.append(
            f"{manifest_path}: authority_binding fields must exactly equal "
            f"{sorted(expected_binding_keys)}"
        )
    if binding.get("schema_version") != "1.0":
        errors.append(f"{manifest_path}: authority_binding.schema_version must be 1.0")
    if binding.get("change_id") != manifest.get("change_id"):
        errors.append(f"{manifest_path}: authority_binding.change_id must equal manifest change_id")

    dossier_format = manifest.get("format")
    documents = manifest.get("documents")
    expected_paths: dict[str, object] = {}
    if isinstance(documents, dict):
        if dossier_format == "governed":
            expected_paths = {
                "requirements": documents.get("requirements"),
                "design": documents.get("design"),
            }
        elif dossier_format == "single":
            expected_paths = {
                "requirements": documents.get("change"),
                "design": documents.get("change"),
            }

    bound_text: dict[str, str] = {}
    for role in ("requirements", "design"):
        record = binding.get(role)
        label = f"{manifest_path}: authority_binding.{role}"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object with path and sha256")
            continue
        if set(record) != {"path", "sha256"}:
            errors.append(f"{label} fields must exactly equal ['path', 'sha256']")
        expected_path = expected_paths.get(role)
        if record.get("path") != expected_path:
            errors.append(f"{label}.path must equal the authoritative documents.{role if dossier_format == 'governed' else 'change'} path")
            continue
        document, path_error = _relative_path(
            manifest_path.parent,
            record.get("path"),
            label=f"{label}.path",
            boundary=manifest_path.parent,
        )
        if path_error:
            errors.append(path_error)
            continue
        assert document is not None
        if document.is_symlink() or not document.is_file():
            errors.append(f"{label}.path is missing or is not a regular non-symlink file: {document}")
            continue
        try:
            raw = document.read_bytes()
            text = raw.decode("utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{label}.path is not readable UTF-8: {document}: {exc}")
            continue
        digest = record.get("sha256")
        if not isinstance(digest, str) or not DIGEST_PATTERN.fullmatch(digest):
            errors.append(f"{label} sha256 must match sha256:<64 lowercase hex>")
        else:
            actual = "sha256:" + hashlib.sha256(raw).hexdigest()
            if digest != actual:
                errors.append(f"{label} sha256 does not match exact file bytes")
        bound_text[role] = text

    identifier_sets = binding.get("identifier_sets")
    bound_sets: dict[str, set[str] | None] = {}
    traceability = manifest.get("traceability")
    if not isinstance(identifier_sets, dict):
        errors.append(f"{manifest_path}: authority_binding.identifier_sets must be an object")
    else:
        if set(identifier_sets) != set(ID_PATTERNS):
            errors.append(
                f"{manifest_path}: authority_binding.identifier_sets fields must exactly equal "
                f"{sorted(ID_PATTERNS)}"
            )
        for family in ID_PATTERNS:
            bound = _validate_id_list(
                identifier_sets.get(family),
                family,
                errors,
                label="authority_binding.identifier_sets",
            )
            bound_sets[family] = bound
            if bound is not None and isinstance(traceability, dict):
                declared = traceability.get(family)
                if isinstance(declared, list) and set(declared) != bound:
                    errors.append(
                        f"{manifest_path}: authority_binding.identifier_sets.{family} "
                        f"must exactly equal traceability.{family}"
                    )

    source_roles = {
        "acceptance_criteria": "requirements",
        "scope": "design",
        "verification_obligations": "design",
    }
    declarations_by_role = {
        role: _normative_id_declarations(text, path=manifest_path.parent / str(expected_paths.get(role)), errors=errors)
        for role, text in bound_text.items()
    }
    if dossier_format == "governed":
        allowed_families = {
            "requirements": {"acceptance_criteria"},
            "design": {"scope", "verification_obligations"},
        }
        for role, declarations in declarations_by_role.items():
            for family, identifiers in declarations.items():
                if family not in allowed_families[role] and identifiers:
                    errors.append(
                        f"{manifest_path}: governed authority_binding.{role}.path must not declare "
                        f"normative {family} IDs: {sorted(identifiers)}"
                    )

        requirements_declarations = declarations_by_role.get("requirements")
        design_declarations = declarations_by_role.get("design")
        if requirements_declarations is not None and design_declarations is not None:
            for family in ID_PATTERNS:
                duplicates = requirements_declarations[family] & design_declarations[family]
                for identifier in sorted(duplicates):
                    errors.append(
                        f"{manifest_path}: normative ID must be globally unique across governed "
                        f"authority documents: {identifier} appears in requirements and design"
                    )
    for family, role in source_roles.items():
        expected = bound_sets.get(family)
        declarations = declarations_by_role.get(role)
        if expected is None or declarations is None:
            continue
        actual = declarations[family]
        if actual != expected:
            errors.append(
                f"{manifest_path}: normative {family} declarations in authority_binding.{role}.path "
                "must exactly equal authority_binding.identifier_sets"
            )


def _validate_test_accounting(manifest: dict[str, Any], errors: list[str]) -> None:
    tests = manifest.get("tests")
    if not isinstance(tests, dict):
        errors.append("tests must be an object with black_box and white_box accounting")
        return
    accepted = manifest.get("status") in TERMINAL_ACCEPTED_STATUSES
    for family in ("black_box", "white_box"):
        record = tests.get(family)
        if not isinstance(record, dict):
            errors.append(f"tests.{family} accounting is required")
            continue
        status = record.get("status")
        if status not in TEST_STATUSES:
            errors.append(f"tests.{family}.status must be one of {sorted(TEST_STATUSES)}")
        rationale = record.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"tests.{family}.rationale must be non-empty")
        evidence = record.get("evidence")
        if not isinstance(evidence, list) or any(not isinstance(item, str) or not item.strip() for item in evidence):
            errors.append(f"tests.{family}.evidence must be an array of non-empty strings")
        elif status == "passed" and not evidence:
            errors.append(f"tests.{family}.evidence is required when status is passed")
        if accepted and status not in {"passed", "not-applicable"}:
            errors.append(f"accepted dossier requires passed or not-applicable tests.{family}")


def _validate_change_manifest(
    repo_root: Path,
    project_root: Path,
    changes_root: Path,
    manifest_path: Path,
    catalog_paths: set[Path],
    errors: list[str],
) -> str | None:
    manifest = _load_json(manifest_path, "change dossier manifest", errors)
    if manifest is None:
        return None
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    errors.extend(_text_issues(manifest_path, manifest_text))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{manifest_path}: schema_version must be 1.0")

    change_id = manifest.get("change_id")
    if not isinstance(change_id, str) or not SAFE_CHANGE_ID.fullmatch(change_id):
        errors.append(f"{manifest_path}: change_id must use lowercase safe characters")
        change_id = None
    elif manifest_path.parent.name != change_id:
        errors.append(f"{manifest_path}: directory name must equal change_id {change_id}")

    status = manifest.get("status")
    if status not in CHANGE_STATUSES:
        errors.append(f"{manifest_path}: status must be one of {sorted(CHANGE_STATUSES)}")
    dossier_format = manifest.get("format")
    if dossier_format not in EXPECTED_DOCUMENTS:
        errors.append(f"{manifest_path}: format must be single or governed")

    documents = manifest.get("documents")
    resolved_documents: set[Path] = set()
    declared_documents: set[Path] = {manifest_path}
    if not isinstance(documents, dict) or not documents:
        errors.append(f"{manifest_path}: documents must be a non-empty role-to-path object")
    else:
        expected_documents = EXPECTED_DOCUMENTS.get(dossier_format)
        if expected_documents is not None and documents != expected_documents:
            errors.append(
                f"{manifest_path}: {dossier_format} documents must equal {expected_documents}"
            )
        for role, value in documents.items():
            if not isinstance(role, str) or not role.strip():
                errors.append(f"{manifest_path}: document role names must be non-empty strings")
                continue
            document, error = _relative_path(
                manifest_path.parent,
                value,
                label=f"{manifest_path} documents.{role}",
                boundary=manifest_path.parent,
            )
            if error:
                errors.append(error)
                continue
            assert document is not None
            resolved = document.resolve(strict=False)
            if resolved in resolved_documents:
                errors.append(f"{manifest_path}: duplicate document path {value}")
                continue
            resolved_documents.add(resolved)
            declared_documents.add(document)
            _read_and_validate_text(
                document,
                repo_root=repo_root,
                errors=errors,
                required_backlink=manifest_path,
            )

    _validate_inventory(
        manifest_path.parent,
        label=f"change dossier {manifest_path.parent.name}",
        expected=declared_documents,
        repo_root=repo_root,
        errors=errors,
    )

    traceability = manifest.get("traceability")
    if not isinstance(traceability, dict):
        errors.append(f"{manifest_path}: traceability must be an object")
    else:
        for name in ID_PATTERNS:
            _validate_id_list(traceability.get(name), name, errors)

    _validate_authority_binding(manifest, manifest_path, errors)

    _validate_test_accounting(manifest, errors)

    knowledge = manifest.get("knowledge")
    if not isinstance(knowledge, dict):
        errors.append(f"{manifest_path}: knowledge impact and disposition are required")
    else:
        impact = knowledge.get("impact")
        disposition = knowledge.get("disposition")
        rationale = knowledge.get("rationale")
        promotion_links = knowledge.get("promotion_links")
        if impact not in KNOWLEDGE_IMPACTS:
            errors.append(f"{manifest_path}: knowledge.impact must be one of {sorted(KNOWLEDGE_IMPACTS)}")
        if disposition not in KNOWLEDGE_DISPOSITIONS:
            errors.append(
                f"{manifest_path}: knowledge.disposition must be one of {sorted(KNOWLEDGE_DISPOSITIONS)}"
            )
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append(f"{manifest_path}: knowledge.rationale must be non-empty")
        if not isinstance(promotion_links, list) or any(
            not isinstance(item, str) or not item.strip() for item in promotion_links
        ):
            errors.append(f"{manifest_path}: knowledge.promotion_links must be an array of relative links")
            promotion_links = []
        if impact == "none" and disposition != "not-applicable":
            errors.append(f"{manifest_path}: impact none requires disposition not-applicable")
        if impact == "none" and promotion_links:
            errors.append(f"{manifest_path}: impact none must not declare promotion links")
        if impact in KNOWLEDGE_IMPACTS - {"none"} and disposition == "not-applicable":
            errors.append(f"{manifest_path}: material knowledge impact cannot be not-applicable")
        if status in TERMINAL_ACCEPTED_STATUSES and impact != "none" and disposition == "pending":
            errors.append(f"{manifest_path}: accepted knowledge impact cannot remain pending")
        if disposition == "promoted" and not promotion_links:
            errors.append(f"{manifest_path}: promoted knowledge requires at least one promotion link")
        if disposition == "promoted" and status not in TERMINAL_ACCEPTED_STATUSES:
            errors.append(f"{manifest_path}: promoted knowledge requires accepted or superseded status")
        for index, link in enumerate(promotion_links):
            target, error = _relative_path(
                manifest_path.parent,
                link.split("#", 1)[0],
                label=f"{manifest_path} knowledge.promotion_links[{index}]",
                boundary=project_root,
                allow_parent=True,
            )
            if error:
                errors.append(error)
                continue
            assert target is not None
            if not target.is_file():
                errors.append(f"{manifest_path}: broken promotion link {link}")
            elif target.resolve() not in catalog_paths:
                errors.append(f"{manifest_path}: promotion link is not a current catalog document: {link}")

    related = manifest.get("related_changes", [])
    if not isinstance(related, list) or any(not isinstance(item, str) or not item.strip() for item in related):
        errors.append(f"{manifest_path}: related_changes must be an array of relative manifest links")
    else:
        for index, link in enumerate(related):
            target, error = _relative_path(
                manifest_path.parent,
                link,
                label=f"{manifest_path} related_changes[{index}]",
                boundary=changes_root,
                allow_parent=True,
            )
            if error:
                errors.append(error)
            elif target is not None:
                if target.resolve(strict=False) == manifest_path.resolve():
                    errors.append(f"{manifest_path}: related change crosslink must not reference itself")
                elif target.name != "manifest.json" or not target.is_file():
                    errors.append(f"{manifest_path}: broken related change crosslink {link}")
    return change_id


def validate_knowledge_system(
    repo_root: str | Path,
    *,
    project_root: str | None = None,
    changes_root: str | None = None,
    convention_path: str = DEFAULT_CONVENTION_PATH,
    change_id: str | None = None,
) -> dict[str, Any]:
    """Return a deterministic validation report without modifying the repository."""
    root = Path(os.path.abspath(repo_root))
    errors: list[str] = []
    if root.is_symlink():
        errors.append(f"repository root must not be a symlink: {root}")
    if not root.is_dir():
        errors.append(f"repository root is missing or is not a directory: {root}")
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "invalid",
            "repo_root": str(root),
            "roots": {},
            "changes_checked": [],
            "errors": errors,
        }

    project, changes = _resolve_roots(
        root,
        project_root=project_root,
        changes_root=changes_root,
        convention_path=convention_path,
        errors=errors,
    )
    _validate_runtime_ignore(root, errors)
    roots = {
        "project": project.relative_to(root).as_posix()
        if project is not None and _is_within(project, root)
        else None,
        "changes": changes.relative_to(root).as_posix()
        if changes is not None and _is_within(changes, root)
        else None,
        "runtime": RUNTIME_ROOT,
    }
    checked: list[str] = []
    if project is not None and changes is not None and project.is_dir() and changes.is_dir():
        catalog_paths = _validate_project_catalog(root, project, errors)
        manifest_paths: list[Path] = []
        if change_id is not None:
            if not SAFE_CHANGE_ID.fullmatch(change_id):
                errors.append("requested change_id must use lowercase safe characters")
            else:
                requested, error = _relative_path(
                    changes,
                    f"{change_id}/manifest.json",
                    label="requested change manifest",
                    boundary=changes,
                )
                if error:
                    errors.append(error)
                elif requested is not None:
                    manifest_paths.append(requested)
        else:
            for child in sorted(changes.iterdir(), key=lambda item: item.name):
                if child.is_symlink():
                    errors.append(f"change dossier root contains a symlink: {child}")
                elif child.is_dir():
                    manifest_paths.append(child / "manifest.json")
                else:
                    errors.append(f"unexpected non-directory entry in change dossier root: {child}")
        for manifest_path in manifest_paths:
            before = len(errors)
            validated_id = _validate_change_manifest(
                root,
                project,
                changes,
                manifest_path,
                catalog_paths,
                errors,
            )
            checked.append(validated_id or manifest_path.parent.name)
            if len(errors) == before and manifest_path.parent.is_symlink():
                errors.append(f"change dossier must not be a symlink: {manifest_path.parent}")

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "valid" if not errors else "invalid",
        "repo_root": str(root),
        "roots": roots,
        "changes_checked": checked,
        "errors": sorted(set(errors)),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="repository root")
    parser.add_argument("--project-root", help="explicit relative current-truth root")
    parser.add_argument("--changes-root", help="explicit relative change-dossier root")
    parser.add_argument("--convention-path", default=DEFAULT_CONVENTION_PATH)
    parser.add_argument("--change-id", help="validate only one change dossier")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    report = validate_knowledge_system(
        args.repo_root,
        project_root=args.project_root,
        changes_root=args.changes_root,
        convention_path=args.convention_path,
        change_id=args.change_id,
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "valid" else 2


if __name__ == "__main__":
    sys.exit(main())
