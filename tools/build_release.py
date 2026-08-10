#!/usr/bin/env python3
"""Build and verify deterministic Dev Flow source release artifacts."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path, PurePosixPath


SEMVER = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
HEX_OBJECT_ID = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
MANIFEST_NAME = "release-manifest.json"
CHECKSUMS_NAME = "SHA256SUMS"
REQUIRED_FILES = {
    ".codex-plugin/plugin.json",
    "LICENSE",
    "README.md",
    "CHANGELOG.md",
}


class ReleaseError(RuntimeError):
    """A controlled release-contract failure."""


def run_git(root: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=not binary,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", "replace") if binary else result.stderr
        raise ReleaseError(f"git {' '.join(args)} failed: {stderr.strip()}")
    return result.stdout


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_bytes_atomic(path: Path, content: bytes) -> None:
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def ensure_clean_output(path: Path) -> None:
    if path.is_symlink():
        raise ReleaseError(f"output directory must not be a symlink: {path}")
    if path.exists() and not path.is_dir():
        raise ReleaseError(f"output path is not a directory: {path}")
    if path.exists() and any(path.iterdir()):
        raise ReleaseError(f"output directory must be empty: {path}")
    path.mkdir(parents=True, exist_ok=True)


def canonical_commit(root: Path, revision: str) -> str:
    resolved = str(run_git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")).strip()
    if not HEX_OBJECT_ID.fullmatch(resolved):
        raise ReleaseError(f"unexpected Git object id: {resolved!r}")
    return resolved


def plugin_version_at(root: Path, commit: str) -> str:
    raw = str(run_git(root, "show", f"{commit}:.codex-plugin/plugin.json"))
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ReleaseError(f"plugin manifest is not valid JSON: {error}") from error
    version = data.get("version") if isinstance(data, dict) else None
    if not isinstance(version, str):
        raise ReleaseError("plugin manifest version is missing")
    return version


def write_checksums(directory: Path, names: list[str]) -> Path:
    if not names:
        raise ReleaseError("at least one checksum input is required")
    unique = sorted(set(names))
    if len(unique) != len(names):
        raise ReleaseError("checksum input names must be unique")
    lines: list[str] = []
    for name in unique:
        if Path(name).name != name or name == CHECKSUMS_NAME:
            raise ReleaseError(f"unsafe checksum input name: {name!r}")
        path = directory / name
        if path.is_symlink() or not path.is_file():
            raise ReleaseError(f"checksum input must be a regular file: {path}")
        lines.append(f"{sha256(path)}  {name}\n")
    destination = directory / CHECKSUMS_NAME
    write_bytes_atomic(destination, "".join(lines).encode("utf-8"))
    return destination


def build(root: Path, output: Path, version: str, revision: str) -> dict[str, object]:
    root = root.resolve()
    if not SEMVER.fullmatch(version):
        raise ReleaseError(f"version is not valid SemVer: {version!r}")
    if not (root / ".git").exists():
        raise ReleaseError(f"repository root does not contain .git: {root}")
    ensure_clean_output(output)

    commit = canonical_commit(root, revision)
    declared_version = plugin_version_at(root, commit)
    if declared_version != version:
        raise ReleaseError(
            f"requested version {version!r} does not match plugin manifest {declared_version!r} at {commit}"
        )
    tree = str(run_git(root, "rev-parse", f"{commit}^{{tree}}")).strip()
    epoch_text = str(run_git(root, "show", "-s", "--format=%ct", commit)).strip()
    try:
        source_date_epoch = int(epoch_text)
    except ValueError as error:
        raise ReleaseError(f"invalid commit timestamp: {epoch_text!r}") from error

    archive_name = f"dev-flow-{version}.tar.gz"
    prefix = f"dev-flow-{version}/"
    tar_bytes = run_git(
        root,
        "archive",
        "--format=tar",
        f"--prefix={prefix}",
        commit,
        binary=True,
    )
    assert isinstance(tar_bytes, bytes)
    compressed = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=compressed, compresslevel=9, mtime=0) as handle:
        handle.write(tar_bytes)
    archive_path = output / archive_name
    write_bytes_atomic(archive_path, compressed.getvalue())

    manifest = {
        "schema_version": "1.0",
        "artifact_type": "codex-plugin-source",
        "name": "dev-flow",
        "version": version,
        "git_commit": commit,
        "git_tree": tree,
        "source_date_epoch": source_date_epoch,
        "archive": {
            "name": archive_name,
            "format": "tar+gzip",
            "root": prefix,
            "sha256": sha256(archive_path),
            "size": archive_path.stat().st_size,
        },
    }
    manifest_path = output / MANIFEST_NAME
    write_bytes_atomic(
        manifest_path,
        (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    checksum_path = write_checksums(output, [archive_name, MANIFEST_NAME])
    return {
        "status": "built",
        "output": str(output.resolve()),
        "archive": archive_name,
        "manifest": MANIFEST_NAME,
        "checksums": checksum_path.name,
        "commit": commit,
        "sha256": manifest["archive"]["sha256"],
    }


def normalized_parts(path: PurePosixPath) -> list[str] | None:
    parts: list[str] = []
    for part in path.parts:
        if part in {"", "."}:
            continue
        if part == "..":
            if not parts:
                return None
            parts.pop()
        else:
            parts.append(part)
    return parts


def validate_archive(archive: Path, version: str) -> None:
    root_name = f"dev-flow-{version}"
    observed: set[str] = set()
    plugin_data: dict[str, object] | None = None
    try:
        with tarfile.open(archive, mode="r:gz") as bundle:
            for member in bundle.getmembers():
                member_path = PurePosixPath(member.name)
                if member_path.is_absolute():
                    raise ReleaseError(f"archive contains an absolute path: {member.name!r}")
                parts = normalized_parts(member_path)
                if not parts or parts[0] != root_name or ".." in member_path.parts:
                    raise ReleaseError(f"archive member escapes the release root: {member.name!r}")
                normalized_name = "/".join(parts)
                if normalized_name in observed:
                    raise ReleaseError(f"archive contains duplicate member: {normalized_name!r}")
                observed.add(normalized_name)
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise ReleaseError(f"archive contains an unsupported member type: {member.name!r}")
                if member.issym() or member.islnk():
                    target = PurePosixPath(member.linkname)
                    if target.is_absolute():
                        raise ReleaseError(f"archive link has an absolute target: {member.name!r}")
                    base = PurePosixPath(*parts[:-1]) if member.issym() else PurePosixPath()
                    target_parts = normalized_parts(base / target)
                    if not target_parts or target_parts[0] != root_name:
                        raise ReleaseError(f"archive link escapes the release root: {member.name!r}")
                relative_name = "/".join(parts[1:])
                if relative_name == ".codex-plugin/plugin.json":
                    extracted = bundle.extractfile(member)
                    if extracted is None:
                        raise ReleaseError("plugin manifest is not a regular archive member")
                    plugin_data = json.loads(extracted.read().decode("utf-8"))
    except (tarfile.TarError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReleaseError(f"invalid release archive: {error}") from error
    missing = sorted(
        path for path in REQUIRED_FILES if f"{root_name}/{path}" not in observed
    )
    if missing:
        raise ReleaseError(f"archive is missing required files: {missing}")
    if not isinstance(plugin_data, dict) or plugin_data.get("version") != version:
        raise ReleaseError("archived plugin version does not match the release version")


def parse_checksums(directory: Path) -> dict[str, str]:
    path = directory / CHECKSUMS_NAME
    if path.is_symlink() or not path.is_file():
        raise ReleaseError(f"missing regular checksum file: {path}")
    entries: dict[str, str] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", line)
        if not match:
            raise ReleaseError(f"invalid checksum line {line_number}")
        digest, name = match.groups()
        if name in entries or name == CHECKSUMS_NAME:
            raise ReleaseError(f"invalid duplicate or recursive checksum entry: {name!r}")
        entries[name] = digest
    if not entries:
        raise ReleaseError("checksum file is empty")
    for name, expected in entries.items():
        candidate = directory / name
        if candidate.is_symlink() or not candidate.is_file():
            raise ReleaseError(f"checksummed file is missing or not regular: {candidate}")
        actual = sha256(candidate)
        if actual != expected:
            raise ReleaseError(f"checksum mismatch for {name}: expected {expected}, observed {actual}")
    return entries


def verify(directory: Path, expected_version: str | None, expected_commit: str | None) -> dict[str, object]:
    if directory.is_symlink() or not directory.is_dir():
        raise ReleaseError(f"artifact directory must be a real directory: {directory}")
    manifest_path = directory / MANIFEST_NAME
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise ReleaseError(f"missing regular release manifest: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ReleaseError(f"invalid release manifest: {error}") from error
    expected_keys = {
        "schema_version",
        "artifact_type",
        "name",
        "version",
        "git_commit",
        "git_tree",
        "source_date_epoch",
        "archive",
    }
    if not isinstance(manifest, dict) or set(manifest) != expected_keys:
        raise ReleaseError("release manifest fields do not match schema 1.0")
    version = manifest.get("version")
    commit = manifest.get("git_commit")
    tree = manifest.get("git_tree")
    if (
        manifest.get("schema_version") != "1.0"
        or manifest.get("artifact_type") != "codex-plugin-source"
        or manifest.get("name") != "dev-flow"
        or not isinstance(version, str)
        or not SEMVER.fullmatch(version)
        or not isinstance(commit, str)
        or not HEX_OBJECT_ID.fullmatch(commit)
        or not isinstance(tree, str)
        or not HEX_OBJECT_ID.fullmatch(tree)
        or not isinstance(manifest.get("source_date_epoch"), int)
        or manifest["source_date_epoch"] < 0
    ):
        raise ReleaseError("release manifest contains invalid identity fields")
    if expected_version is not None and version != expected_version:
        raise ReleaseError(f"release version mismatch: expected {expected_version}, observed {version}")
    if expected_commit is not None and commit != expected_commit:
        raise ReleaseError(f"release commit mismatch: expected {expected_commit}, observed {commit}")
    archive_info = manifest.get("archive")
    archive_name = f"dev-flow-{version}.tar.gz"
    expected_archive = {
        "name": archive_name,
        "format": "tar+gzip",
        "root": f"dev-flow-{version}/",
        "sha256": archive_info.get("sha256") if isinstance(archive_info, dict) else None,
        "size": archive_info.get("size") if isinstance(archive_info, dict) else None,
    }
    if not isinstance(archive_info, dict) or archive_info != expected_archive:
        raise ReleaseError("release manifest archive fields do not match schema 1.0")
    if not isinstance(archive_info["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", archive_info["sha256"]):
        raise ReleaseError("release archive digest is invalid")
    if not isinstance(archive_info["size"], int) or archive_info["size"] < 1:
        raise ReleaseError("release archive size is invalid")
    archive_path = directory / archive_name
    if archive_path.is_symlink() or not archive_path.is_file():
        raise ReleaseError(f"missing regular release archive: {archive_path}")
    if archive_path.stat().st_size != archive_info["size"] or sha256(archive_path) != archive_info["sha256"]:
        raise ReleaseError("release archive does not match its manifest")
    checksum_entries = parse_checksums(directory)
    for required in (archive_name, MANIFEST_NAME):
        if required not in checksum_entries:
            raise ReleaseError(f"checksum file is missing required entry: {required}")
    validate_archive(archive_path, version)
    return {
        "status": "valid",
        "artifact_directory": str(directory.resolve()),
        "version": version,
        "commit": commit,
        "archive": archive_name,
        "checksummed_files": sorted(checksum_entries),
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    build_command = subcommands.add_parser("build", help="Build a deterministic source archive from a Git commit")
    build_command.add_argument("--root", type=Path, default=Path.cwd())
    build_command.add_argument("--output", type=Path, required=True)
    build_command.add_argument("--version", required=True)
    build_command.add_argument("--commit", default="HEAD")
    checksum_command = subcommands.add_parser("checksums", help="Rewrite SHA256SUMS for named artifact files")
    checksum_command.add_argument("--artifact-dir", type=Path, required=True)
    checksum_command.add_argument("--file", action="append", dest="files", required=True)
    verify_command = subcommands.add_parser("verify", help="Verify release identity, hashes, and archive safety")
    verify_command.add_argument("--artifact-dir", type=Path, required=True)
    verify_command.add_argument("--expected-version")
    verify_command.add_argument("--expected-commit")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "build":
            result = build(args.root, args.output, args.version, args.commit)
        elif args.command == "checksums":
            directory = args.artifact_dir
            if directory.is_symlink() or not directory.is_dir():
                raise ReleaseError(f"artifact directory must be a real directory: {directory}")
            path = write_checksums(directory, args.files)
            result = {"status": "written", "checksums": str(path.resolve()), "files": sorted(args.files)}
        else:
            result = verify(args.artifact_dir, args.expected_version, args.expected_commit)
    except ReleaseError as error:
        print(json.dumps({"status": "invalid", "error": str(error)}, indent=2), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
