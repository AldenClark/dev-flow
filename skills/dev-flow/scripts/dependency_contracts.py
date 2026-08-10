#!/usr/bin/env python3
"""Machine-readable dependency approval and diff-binding helpers."""

from __future__ import annotations

import hashlib
import re
import shlex
from pathlib import Path, PurePosixPath
from typing import Any


DEPENDENCY_ECOSYSTEMS = {"cargo", "npm", "github-actions", "other"}
DEPENDENCY_OPERATIONS = {"add", "update", "remove"}
DEPENDENCY_SCOPE_KEYS = {
    "ecosystem",
    "name",
    "version",
    "ref",
    "command",
    "files",
    "operations",
    "result_sha256",
}
ACTION_NAME_PATTERN = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*"
ACTION_REF_RE = re.compile(rf"^({ACTION_NAME_PATTERN})@([A-Za-z0-9._/-]+)$")
ACTION_REF_ANYWHERE_RE = re.compile(rf"(?<![A-Za-z0-9_.-])({ACTION_NAME_PATTERN})@([A-Za-z0-9._/-]+)")
USES_LINE_RE = re.compile(
    r"(?m)^\s*(?:\+\s*)?(?:-\s*)?(?:uses|['\"]uses['\"])\s*:\s*(.*?)\s*$"
)
USES_FLOW_RE = re.compile(
    r"(?:^|[,{])\s*(?:uses|'uses'|\"uses\")\s*:\s*"
    r"(\"(?:\\.|[^\"\\])*\"|'(?:''|[^'])*'|[^,}\n]+)",
    re.MULTILINE,
)
DOUBLE_QUOTED_KEY_RE = re.compile(
    r'"((?:\\[\s\S]|[^"\\])*)"\s*:\s*'
    r'(\"(?:\\[\s\S]|[^\"\\])*\"|\'(?:\'\'|[^\'])*\'|[^,}\n]+)',
    re.MULTILINE,
)
DOUBLE_QUOTED_SCALAR_RE = re.compile(r'"((?:\\[\s\S]|[^"\\])*)"')
PACKAGE_SCOPE_FLAGS = {
    "--manifest-path",
    "--path",
    "--git",
    "--prefix",
    "--cwd",
    "--dir",
    "--global",
    "--workspace",
    "--workspaces",
    "--workspace-root",
    "--include-workspace-root",
    "--package",
    "--filter",
    "-g",
    "-p",
    "-w",
    "-C",
}
DEPENDENCY_FILE_RE = re.compile(
    r"(?:^|/)(?:Cargo\.toml|Cargo\.lock|package\.json|pnpm-lock\.yaml|package-lock\.json|"
    r"yarn\.lock|bun\.lockb?|deno\.jsonc?|pyproject\.toml|requirements[^/]*\.txt|go\.mod|"
    r"Package\.swift|Podfile|build\.gradle|libs\.versions\.toml)$",
    re.IGNORECASE,
)
PACKAGE_OPERATION_MAPS = {
    "cargo": {"add": "add", "remove": "remove", "rm": "remove", "update": "update"},
    "npm": {"install": "add", "add": "add", "uninstall": "remove", "remove": "remove", "rm": "remove", "update": "update"},
    "pnpm": {"add": "add", "remove": "remove", "rm": "remove", "update": "update", "up": "update"},
    "yarn": {"add": "add", "remove": "remove", "up": "update", "upgrade": "update"},
    "bun": {"add": "add", "remove": "remove", "update": "update"},
}
PACKAGE_MUTATION_RAW_RE = re.compile(
    r"\b(?:cargo|npm|pnpm|yarn|bun)(?:\.exe|\.cmd)?\b[\s\S]{0,512}?"
    r"\b(?:add|install|remove|rm|uninstall|update|up|upgrade)\b",
    re.IGNORECASE,
)
YAML_SIMPLE_ESCAPES = {
    "0": "\0",
    "a": "\a",
    "b": "\b",
    "t": "\t",
    "n": "\n",
    "v": "\v",
    "f": "\f",
    "r": "\r",
    "e": "\x1b",
    " ": " ",
    '"': '"',
    "/": "/",
    "\\": "\\",
    "N": "\u0085",
    "_": "\u00a0",
    "L": "\u2028",
    "P": "\u2029",
}


def normalized_relative_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return None
    candidate = value.strip()
    path = PurePosixPath(candidate)
    if (
        value != candidate
        or path.as_posix() != candidate
        or path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        return None
    return path.as_posix()


def canonical_command(value: Any) -> str | None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or any(character in value for character in "\n\r;&|<>`$")
    ):
        return None
    try:
        tokens = shlex.split(value)
    except ValueError:
        return None
    if not tokens or any(token in {";", "&&", "||", "|", ">", ">>"} for token in tokens):
        return None
    return shlex.join(tokens)


def _package_spec(value: str) -> tuple[str, str] | None:
    if value.startswith("@"):
        split = value.rfind("@")
        if split <= value.find("/"):
            return None
        name, ref = value[:split], value[split + 1 :]
    elif "@" in value:
        name, ref = value.rsplit("@", 1)
    else:
        return None
    if not name or not ref or any(character.isspace() for character in name + ref):
        return None
    return name, ref


def _package_executable(value: str) -> str:
    executable = Path(value).name.lower()
    for suffix in (".exe", ".cmd"):
        if executable.endswith(suffix):
            return executable[: -len(suffix)]
    return executable


def looks_like_package_mutation(value: Any, *, _depth: int = 0) -> bool:
    """Conservatively recognize package mutations that the exact parser rejects."""
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        tokens = shlex.split(value)
    except ValueError:
        tokens = re.split(r"\s+", value.strip())
    for index, token in enumerate(tokens):
        executable = _package_executable(token)
        operations = PACKAGE_OPERATION_MAPS.get(executable)
        if operations and any(candidate.lower() in operations for candidate in tokens[index + 1 :]):
            return True
        if _depth < 4 and any(character.isspace() for character in token) and token.strip() != value.strip():
            if looks_like_package_mutation(token, _depth=_depth + 1):
                return True
    return bool(PACKAGE_MUTATION_RAW_RE.search(value))


def _has_package_scope(tokens: list[str]) -> bool:
    return any(
        token in PACKAGE_SCOPE_FLAGS
        or any(token.startswith(flag + "=") for flag in PACKAGE_SCOPE_FLAGS if flag.startswith("--"))
        or token.startswith(("-C", "-p=", "-w="))
        for token in tokens
    )


def parse_package_command(value: Any) -> dict[str, str | None] | None:
    """Parse one deliberately narrow package mutation without executing it."""
    command = canonical_command(value)
    if command is None:
        return None
    tokens = shlex.split(command)
    executable = _package_executable(tokens[0])
    if len(tokens) < 3:
        return None
    verb_index = 1
    if executable == "cargo" and tokens[verb_index].startswith("+") and len(tokens) >= 4:
        verb_index += 1
    subcommand = tokens[verb_index].lower()
    operations = PACKAGE_OPERATION_MAPS.get(executable)
    operation = operations.get(subcommand) if operations else None
    if operation is None:
        return None
    arguments = tokens[verb_index + 1 :]
    if not arguments:
        return None
    name: str
    ref: str | None
    if executable == "cargo" and operation == "update":
        if len(arguments) < 4 or arguments[0] not in {"-p", "--package"} or arguments[2] != "--precise":
            return None
        name, ref = arguments[1], arguments[3]
        tail = arguments[4:]
        if _has_package_scope(tail):
            return None
    else:
        if _has_package_scope(arguments):
            return None
        identity = arguments[0]
        tail = arguments[1:]
        parsed = _package_spec(identity)
        if operation in {"add", "update"}:
            if parsed is None:
                return None
            name, ref = parsed
        else:
            if parsed is not None:
                name, ref = parsed
            else:
                name, ref = identity, None
    if not name or any(character.isspace() for character in name):
        return None
    # Keep the grammar auditable: trailing options must be self-contained flags
    # (`--flag` or `--flag=value`), never a second package or detached value.
    if any(not token.startswith("-") for token in tail):
        return None
    return {
        "ecosystem": "cargo" if executable == "cargo" else "npm",
        "name": name,
        "ref": ref,
        "operation": operation,
        "command": command,
    }


def _decode_yaml_double_quoted(value: str) -> str | None:
    output: list[str] = []
    index = 0
    while index < len(value):
        character = value[index]
        if character != "\\":
            output.append(character)
            index += 1
            continue
        index += 1
        if index >= len(value):
            return None
        escape = value[index]
        if escape in {"x", "u", "U"}:
            width = {"x": 2, "u": 4, "U": 8}[escape]
            digits = value[index + 1 : index + 1 + width]
            if len(digits) != width or not re.fullmatch(rf"[0-9A-Fa-f]{{{width}}}", digits):
                return None
            try:
                output.append(chr(int(digits, 16)))
            except ValueError:
                return None
            index += width + 1
            continue
        if escape in {"\n", "\r"}:
            if escape == "\r" and index + 1 < len(value) and value[index + 1] == "\n":
                index += 1
            index += 1
            while index < len(value) and value[index] in {" ", "\t"}:
                index += 1
            continue
        decoded = YAML_SIMPLE_ESCAPES.get(escape)
        if decoded is None:
            return None
        output.append(decoded)
        index += 1
    return "".join(output)


def _yaml_scalar_value(value: str) -> str | None:
    candidate = value.split(" #", 1)[0].strip()
    if len(candidate) >= 2 and candidate[0] == candidate[-1] == '"':
        return _decode_yaml_double_quoted(candidate[1:-1])
    if len(candidate) >= 2 and candidate[0] == candidate[-1] == "'":
        return candidate[1:-1].replace("''", "'")
    return candidate


def action_reference_scan(text: str) -> tuple[set[tuple[str, str]], list[str]]:
    # Scan concrete external references independently of YAML key spelling. This
    # intentionally treats action-like text anywhere in a changed workflow as
    # governed, so legal aliases, complex keys, and future YAML surface syntax
    # cannot hide an executable external reference from approval checks.
    references = {(match.group(1), match.group(2)) for match in ACTION_REF_ANYWHERE_RE.finditer(text)}
    invalid: list[str] = []
    for match in DOUBLE_QUOTED_SCALAR_RE.finditer(text):
        decoded = _decode_yaml_double_quoted(match.group(1))
        if decoded is None:
            if "@" in match.group(1) or "docker:" in match.group(1):
                invalid.append("<unparseable-escaped-workflow-scalar>")
            continue
        references.update(
            (reference.group(1), reference.group(2))
            for reference in ACTION_REF_ANYWHERE_RE.finditer(decoded)
        )
    raw_values = [match.group(1) for match in USES_LINE_RE.finditer(text)]
    raw_values.extend(match.group(1) for match in USES_FLOW_RE.finditer(text))
    for match in DOUBLE_QUOTED_KEY_RE.finditer(text):
        key = _decode_yaml_double_quoted(match.group(1))
        if key is None:
            if "@" in match.group(2) or "docker:" in match.group(2):
                invalid.append("<unparseable-escaped-workflow-key>")
            continue
        if key == "uses":
            raw_values.append(match.group(2))
    for value in dict.fromkeys(raw_values):
        raw = _yaml_scalar_value(value)
        if raw is None:
            invalid.append("<unparseable-escaped-uses-value>")
            continue
        if raw.startswith("./"):
            continue
        parsed = ACTION_REF_RE.fullmatch(raw)
        if parsed is None:
            invalid.append(raw or "<empty>")
        else:
            references.add((parsed.group(1), parsed.group(2)))
    return references, invalid


def action_reference_diff(text: str) -> tuple[set[tuple[str, str]], set[tuple[str, str]], list[str]]:
    added_lines: list[str] = []
    removed_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added_lines.append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines.append(line[1:])
    added, invalid_added = action_reference_scan("\n".join(added_lines))
    removed, invalid_removed = action_reference_scan("\n".join(removed_lines))
    return added, removed, invalid_added + invalid_removed


def validate_dependency_approval(record: Any) -> list[str]:
    if not isinstance(record, dict):
        return ["dependency approval must be an object"]
    dependency = record.get("dependency")
    if not isinstance(dependency, dict):
        return ["dependency approval requires a dependency object"]
    missing = DEPENDENCY_SCOPE_KEYS - set(dependency)
    extra = set(dependency) - DEPENDENCY_SCOPE_KEYS
    if missing or extra:
        return [f"dependency scope key mismatch: missing={sorted(missing)}, extra={sorted(extra)}"]
    errors: list[str] = []
    ecosystem = dependency.get("ecosystem")
    if ecosystem not in DEPENDENCY_ECOSYSTEMS:
        errors.append(f"dependency ecosystem must be one of {sorted(DEPENDENCY_ECOSYSTEMS)}")
    for field in ("name", "version", "ref"):
        if not isinstance(dependency.get(field), str) or not dependency[field].strip():
            errors.append(f"dependency {field} must be a non-empty string")
    command = dependency.get("command")
    files = dependency.get("files")
    if not isinstance(files, list) or not files:
        errors.append("dependency files must be a non-empty list")
        normalized_files: list[str | None] = []
    else:
        normalized_files = [normalized_relative_path(item) for item in files]
        if any(item is None for item in normalized_files) or len(set(normalized_files)) != len(normalized_files):
            errors.append("dependency files must be unique normalized relative paths")
    operations = dependency.get("operations")
    if (
        not isinstance(operations, list)
        or not operations
        or any(item not in DEPENDENCY_OPERATIONS for item in operations)
        or len(set(operations)) != len(operations)
    ):
        errors.append(f"dependency operations must be unique values from {sorted(DEPENDENCY_OPERATIONS)}")
    result_sha256 = dependency.get("result_sha256")
    if not isinstance(result_sha256, dict):
        errors.append("dependency result_sha256 must be an object keyed by approved file")
    else:
        normalized_hash_paths = {normalized_relative_path(key) for key in result_sha256}
        if None in normalized_hash_paths or any(
            not isinstance(value, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", value)
            for value in result_sha256.values()
        ):
            errors.append("dependency result_sha256 requires normalized file keys and sha256:<lowercase hex> values")
        elif not normalized_hash_paths.issubset(set(normalized_files)):
            errors.append("dependency result_sha256 keys must be included in dependency files")
    if ecosystem == "github-actions":
        if not re.fullmatch(ACTION_NAME_PATTERN, str(dependency.get("name", ""))):
            errors.append("GitHub Action dependency name must be owner/repository with an optional action subpath")
        if not re.fullmatch(r"[0-9a-f]{40}", str(dependency.get("ref", ""))):
            errors.append("GitHub Action dependency ref must be a full lowercase commit SHA")
        if command is not None:
            errors.append("GitHub Action dependency command must be null")
        if any(
            not isinstance(path, str) or not re.fullmatch(r"\.github/workflows/[^/]+\.ya?ml", path)
            for path in normalized_files
        ):
            errors.append("GitHub Action dependency files must be workflow YAML paths")
    elif ecosystem in {"cargo", "npm"}:
        parsed_command = parse_package_command(command)
        if parsed_command is None:
            errors.append("package dependency command must be one supported canonical exact command")
        else:
            if command != parsed_command["command"]:
                errors.append("package dependency command must use canonical shell quoting")
            if parsed_command["ecosystem"] != ecosystem:
                errors.append("package dependency command ecosystem must match dependency ecosystem")
            if parsed_command["name"] != dependency.get("name"):
                errors.append("package dependency command name must match dependency name")
            if parsed_command["operation"] not in (operations if isinstance(operations, list) else []):
                errors.append("package dependency command operation must be approved")
            parsed_ref = parsed_command["ref"]
            if parsed_ref is not None and parsed_ref != dependency.get("ref"):
                errors.append("package dependency command ref must match dependency ref")
        if dependency.get("version") != dependency.get("ref"):
            errors.append("package dependency version and executable ref must match")
    elif command is not None:
        errors.append("non-package dependency command must be null")
    return errors


def dependency_scope(record: Any) -> dict[str, Any] | None:
    if validate_dependency_approval(record):
        return None
    return record["dependency"]


def matches_dependency_request(
    record: Any,
    *,
    ecosystem: str,
    name: str,
    ref: str | None,
    operation: str,
    file: str,
    command: str | None = None,
) -> bool:
    dependency = dependency_scope(record)
    return bool(
        dependency
        and dependency["ecosystem"] == ecosystem
        and dependency["name"] == name
        and (ref is None or dependency["ref"] == ref)
        and dependency["command"] == command
        and operation in dependency["operations"]
        and file in dependency["files"]
    )


def action_references(text: str) -> set[tuple[str, str]]:
    return action_reference_scan(text)[0]


def file_sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def approval_binds_file(record: Any, relative: str, path: Path) -> bool:
    dependency = dependency_scope(record)
    if not dependency or relative not in dependency["files"]:
        return False
    expected = dependency["result_sha256"].get(relative)
    return isinstance(expected, str) and path.is_file() and not path.is_symlink() and file_sha256(path) == expected
