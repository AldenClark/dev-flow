#!/usr/bin/env python3
"""Review-first lifecycle tool for Dev Flow engineering profiles."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable


DEV_FLOW_SCRIPTS = Path(__file__).resolve().parents[2] / "dev-flow" / "scripts"
sys.path.insert(0, str(DEV_FLOW_SCRIPTS))

import engineering_context  # noqa: E402


def emit(value: dict[str, Any], code: int = 0) -> int:
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return code


def validate(args: argparse.Namespace) -> int:
    try:
        data = engineering_context.read_toml(args.profile.resolve())
    except Exception as exc:
        return emit({"status": "invalid", "profile": str(args.profile), "errors": [str(exc)]}, 2)
    errors = engineering_context.validate_profile_data(data, source=str(args.profile.resolve()))
    return emit({"status": "valid" if not errors else "invalid", "profile": str(args.profile.resolve()), "errors": errors}, 0 if not errors else 2)


def explain(args: argparse.Namespace) -> int:
    try:
        snapshot = engineering_context.resolve_profiles(
            args.root.resolve(),
            facts=args.fact,
            task_paths=args.path,
            codex_home=args.codex_home,
            baseline=DEV_FLOW_SCRIPTS.parent / "references" / "neutral-baseline.toml",
            task_profiles=args.task_profile,
        )
    except Exception as exc:
        return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if args.output:
        engineering_context.write_json(args.output.resolve(), snapshot)
    return emit({"status": snapshot["outcome"], "snapshot": snapshot}, 2 if snapshot["outcome"] == "blocked" else 0)


def profile_template(
    profile_id: str,
    layer: str,
    owner: str,
    status: str,
    *,
    scope: list[str],
    expires_at: str | None,
) -> str:
    governance = ""
    if layer == "personal":
        rendered_scope = ", ".join(json.dumps(item) for item in scope)
        governance = f'''provenance = "explicit-user"
scope = [{rendered_scope}]
expires_at = "{expires_at}"
correction_policy = "edit-or-retire-profile"
deletion_policy = "delete-profile-file"
'''
    return f'''schema_version = "1.0"
id = "{profile_id}"
layer = "{layer}"
owner = "{owner}"
version = "1.0"
status = "{status}"
{governance}

# Add reviewed [[preferences]] records. Keep observed repository facts in native
# manifests and CI; keep volatile ecosystem claims in a sourced snapshot.
'''


def scaffold(args: argparse.Namespace) -> int:
    if not engineering_context.SAFE_NAME_RE.fullmatch(args.id):
        return emit({"status": "invalid", "errors": ["id contains unsupported characters"]}, 2)
    if args.layer == "personal":
        if not args.scope or any(not item.strip() for item in args.scope) or not args.expires_at:
            return emit(
                {
                    "status": "invalid",
                    "errors": ["personal profiles require explicit --scope and --expires-at governance"],
                },
                2,
            )
        try:
            expiry = dt.datetime.fromisoformat(args.expires_at.replace("Z", "+00:00"))
        except ValueError:
            return emit({"status": "invalid", "errors": ["--expires-at must be a timezone-aware ISO timestamp"]}, 2)
        if expiry.tzinfo is None or expiry <= dt.datetime.now(dt.timezone.utc):
            return emit({"status": "invalid", "errors": ["--expires-at must be a future timezone-aware timestamp"]}, 2)
    content = profile_template(
        args.id,
        args.layer,
        args.owner,
        args.status,
        scope=args.scope,
        expires_at=args.expires_at,
    )
    proposal = {
        "status": "proposal",
        "classification": "owner-input-required",
        "target": str(args.output.resolve()) if args.output else None,
        "content": content,
        "write_requested": bool(args.write),
    }
    if not args.write:
        return emit(proposal)
    if not args.output:
        return emit({"status": "invalid", "errors": ["--output is required with --write"]}, 2)
    target = args.output.resolve()
    if target.exists() and not args.force:
        return emit({"status": "blocked", "errors": [f"target exists: {target}; use --force only after reviewing the replacement"]}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return emit({**proposal, "status": "written", "target": str(target)})


def manifest_template(profile_path: str, profile_id: str, layer: str, include_personal: bool) -> str:
    return f'''schema_version = "1.0"
include_personal = {str(include_personal).lower()}

[[profile_sources]]
id = "{profile_id}"
path = "{profile_path}"
layer = "{layer}"
scope = ["**"]
required = true
'''


def scaffold_manifest(args: argparse.Namespace) -> int:
    raw_path = Path(args.profile_path)
    if raw_path.is_absolute() or ".." in raw_path.parts or not engineering_context.SAFE_NAME_RE.fullmatch(args.profile_id):
        return emit({"status": "invalid", "errors": ["profile path must stay relative to .dev-flow and profile id must be safe"]}, 2)
    content = manifest_template(args.profile_path, args.profile_id, args.layer, args.include_personal)
    target = (args.root.resolve() / ".dev-flow" / "preferences.toml")
    if not args.write:
        return emit({"status": "proposal", "target": str(target), "content": content, "classification": "owner-input-required"})
    if target.exists() and not args.force:
        return emit({"status": "blocked", "errors": [f"target exists: {target}"]}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return emit({"status": "written", "target": str(target)})


def agents_projection(args: argparse.Namespace) -> int:
    content = """## Dev Flow configuration

- Preference manifest: `.dev-flow/preferences.toml`.
- Use repository-native commands and observed contracts; do not infer them from a personal profile.
- Ask before adding dependencies or changing public protocols, schemas, persisted data, releases, deployments, or external systems.
"""
    target = args.output.resolve() if args.output else args.root.resolve() / "AGENTS.md"
    if not args.write:
        return emit({"status": "proposal", "target": str(target), "content": content, "classification": "owner-input-required"})
    if target.exists() and not args.append:
        return emit({"status": "blocked", "errors": [f"target exists: {target}; review and use --append for a deliberate additive projection"]}, 2)
    target.parent.mkdir(parents=True, exist_ok=True)
    existing = target.read_text(encoding="utf-8") if target.exists() else ""
    if content.strip() in existing:
        return emit({"status": "unchanged", "target": str(target)})
    separator = "\n" if existing and not existing.endswith("\n") else ""
    target.write_text(existing + separator + content, encoding="utf-8")
    return emit({"status": "written", "target": str(target)})


def diff_profiles(args: argparse.Namespace) -> int:
    before = args.before.read_text(encoding="utf-8").splitlines(keepends=True)
    after = args.after.read_text(encoding="utf-8").splitlines(keepends=True)
    patch = "".join(difflib.unified_diff(before, after, fromfile=str(args.before), tofile=str(args.after)))
    return emit({"status": "different" if patch else "unchanged", "diff": patch})


def set_status(args: argparse.Namespace) -> int:
    path = args.profile.resolve()
    try:
        data = engineering_context.read_toml(path)
    except Exception as exc:
        return emit({"status": "invalid", "profile": str(path), "errors": [str(exc)]}, 2)
    errors = engineering_context.validate_profile_data(data, source=str(path))
    if errors:
        return emit({"status": "invalid", "profile": str(path), "errors": errors}, 2)
    text = path.read_text(encoding="utf-8")
    updated, count = re.subn(r'(?m)^status\s*=\s*"[^"]+"\s*$', f'status = "{args.status}"', text, count=1)
    if count != 1:
        return emit({"status": "invalid", "errors": ["profile must contain exactly one top-level status field"]}, 2)
    if not args.write:
        return emit({"status": "proposal", "profile": str(path), "target_status": args.status, "content": updated})
    path.write_text(updated, encoding="utf-8")
    return emit({"status": "updated", "profile": str(path), "target_status": args.status})


def record_waiver(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"PREF-[A-Za-z0-9._-]+", args.id):
        return emit({"status": "invalid", "errors": ["waiver id must use PREF-<safe-id>"]}, 2)
    try:
        expiry = dt.datetime.fromisoformat(args.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return emit({"status": "invalid", "errors": ["--expires-at must be a timezone-aware ISO timestamp"]}, 2)
    if expiry.tzinfo is None or expiry <= dt.datetime.now(dt.timezone.utc):
        return emit({"status": "invalid", "errors": ["--expires-at must be a future timezone-aware timestamp"]}, 2)
    record = {
        "schema_version": "1.0",
        "id": args.id,
        "status": "active",
        "approved_by": args.approved_by,
        "keys": args.key,
        "scope": args.scope,
        "reason": args.reason,
        "residual_risk": args.residual_risk,
        "expires_at": args.expires_at,
    }
    target = args.output.resolve()
    if not args.write:
        return emit({"status": "proposal", "target": str(target), "record": record})
    if target.exists():
        return emit({"status": "blocked", "errors": [f"decision record already exists: {target}"]}, 2)
    engineering_context.write_json(target, record)
    return emit({"status": "written", "target": str(target), "record": record})


def record_suppression(args: argparse.Namespace) -> int:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", args.fingerprint):
        return emit({"status": "invalid", "errors": ["fingerprint must be sha256:<64 lowercase hex characters>"]}, 2)
    record = {
        "fingerprint": args.fingerprint,
        "owner": args.owner,
        "reason": args.reason,
        "tiers": args.tier,
        "expires_at": args.expires_at,
    }
    target = args.output.resolve()
    existing: dict[str, Any] = {"schema_version": "1.0", "suppressions": []}
    if target.is_file():
        try:
            existing = engineering_context.read_json(target)
        except Exception as exc:
            return emit({"status": "invalid", "errors": [str(exc)]}, 2)
    if existing.get("schema_version") != "1.0" or not isinstance(existing.get("suppressions"), list):
        return emit({"status": "invalid", "errors": ["suppression ledger must use schema_version 1.0 and a suppressions list"]}, 2)
    proposed = {**existing, "suppressions": [*existing["suppressions"], record]}
    if not args.write:
        return emit({"status": "proposal", "target": str(target), "record": record, "ledger": proposed})
    engineering_context.write_json(target, proposed)
    return emit({"status": "written", "target": str(target), "record": record})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    validate_parser = sub.add_parser("validate")
    validate_parser.add_argument("profile", type=Path)
    validate_parser.set_defaults(func=validate)

    explain_parser = sub.add_parser("explain")
    explain_parser.add_argument("--root", type=Path, required=True)
    explain_parser.add_argument("--path", action="append", default=[])
    explain_parser.add_argument("--fact", action="append", default=[])
    explain_parser.add_argument("--task-profile", type=Path, action="append", default=[])
    explain_parser.add_argument("--codex-home", type=Path)
    explain_parser.add_argument("--output", type=Path)
    explain_parser.set_defaults(func=explain)

    scaffold_parser = sub.add_parser("scaffold")
    scaffold_parser.add_argument("--id", required=True)
    scaffold_parser.add_argument("--layer", choices=engineering_context.LAYERS[1:], required=True)
    scaffold_parser.add_argument("--owner", required=True)
    scaffold_parser.add_argument("--status", choices=sorted(engineering_context.PROFILE_STATUSES), default="draft")
    scaffold_parser.add_argument("--scope", action="append", default=[])
    scaffold_parser.add_argument("--expires-at")
    scaffold_parser.add_argument("--output", type=Path)
    scaffold_parser.add_argument("--write", action="store_true")
    scaffold_parser.add_argument("--force", action="store_true")
    scaffold_parser.set_defaults(func=scaffold)

    manifest_parser = sub.add_parser("scaffold-manifest")
    manifest_parser.add_argument("--root", type=Path, required=True)
    manifest_parser.add_argument("--profile-path", required=True)
    manifest_parser.add_argument("--profile-id", required=True)
    manifest_parser.add_argument("--layer", choices=("team", "project", "component"), required=True)
    manifest_parser.add_argument("--include-personal", action=argparse.BooleanOptionalAction, default=True)
    manifest_parser.add_argument("--write", action="store_true")
    manifest_parser.add_argument("--force", action="store_true")
    manifest_parser.set_defaults(func=scaffold_manifest)

    agents_parser = sub.add_parser("agents-projection")
    agents_parser.add_argument("--root", type=Path, required=True)
    agents_parser.add_argument("--output", type=Path)
    agents_parser.add_argument("--write", action="store_true")
    agents_parser.add_argument("--append", action="store_true")
    agents_parser.set_defaults(func=agents_projection)

    diff_parser = sub.add_parser("diff")
    diff_parser.add_argument("before", type=Path)
    diff_parser.add_argument("after", type=Path)
    diff_parser.set_defaults(func=diff_profiles)

    for name, target_status in (("promote", "active"), ("retire", "retired")):
        status_parser = sub.add_parser(name)
        status_parser.add_argument("profile", type=Path)
        status_parser.add_argument("--write", action="store_true")
        status_parser.set_defaults(func=set_status, status=target_status)

    waiver_parser = sub.add_parser("waive")
    waiver_parser.add_argument("--id", required=True)
    waiver_parser.add_argument("--approved-by", required=True)
    waiver_parser.add_argument("--key", action="append", required=True)
    waiver_parser.add_argument("--scope", action="append", required=True)
    waiver_parser.add_argument("--reason", required=True)
    waiver_parser.add_argument("--residual-risk", required=True)
    waiver_parser.add_argument("--expires-at", required=True)
    waiver_parser.add_argument("--output", type=Path, required=True)
    waiver_parser.add_argument("--write", action="store_true")
    waiver_parser.set_defaults(func=record_waiver)

    suppress_parser = sub.add_parser("suppress")
    suppress_parser.add_argument("--fingerprint", required=True)
    suppress_parser.add_argument("--owner", required=True)
    suppress_parser.add_argument("--reason", required=True)
    suppress_parser.add_argument("--tier", action="append", choices=sorted(engineering_context.TIERS), default=[])
    suppress_parser.add_argument("--expires-at")
    suppress_parser.add_argument("--output", type=Path, required=True)
    suppress_parser.add_argument("--write", action="store_true")
    suppress_parser.set_defaults(func=record_suppression)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
