#!/usr/bin/env python3
"""Verify packaged confidentiality controls and report external manual gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROTOCOL_SOURCE = "https://learn.chatgpt.com/docs/hooks"
PROTOCOL_CHECKED_AT = "2026-08-14"
BASELINE_PATH = "skills/company-data-security/references/control-baseline.json"
PROTECTED_PATHS = (
    "hooks/data_security_hook.py",
    "skills/company-data-security/SKILL.md",
    "skills/company-data-security/agents/openai.yaml",
    "skills/company-data-security/references/data-handling-policy.md",
    "skills/company-data-security/references/surface-playbooks.md",
    "skills/company-data-security/assets/codex-agents-baseline.md",
    "skills/company-data-security/assets/chatgpt-work-instructions.md",
    "skills/company-data-security/assets/ordinary-chat-instructions.md",
    "skills/company-data-security/scripts/data_security.py",
    "skills/company-data-security/scripts/doctor.py",
)
EXPECTED_HOOK_COMMAND = 'python3 "$PLUGIN_ROOT/hooks/data_security_hook.py"'
EXPECTED_WINDOWS_COMMAND = 'py -3 "%PLUGIN_ROOT%\\hooks\\data_security_hook.py"'


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    detail: str
    required: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.check_id,
            "status": self.status,
            "required": self.required,
            "detail": self.detail,
        }


def _read_json(path: Path, *, max_bytes: int = 262_144) -> Any:
    raw = path.read_bytes()
    if len(raw) > max_bytes:
        raise ValueError(f"{path.name} exceeds the doctor input limit")
    return json.loads(raw.decode("utf-8"))


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _contained_regular_file(root: Path, relative: str) -> tuple[Path | None, str | None]:
    candidate = root / relative
    cursor = candidate
    while cursor != root:
        if cursor.is_symlink():
            return None, "symlinked control path"
        cursor = cursor.parent
    try:
        resolved = candidate.resolve(strict=True)
    except OSError:
        return None, "missing control file"
    if not resolved.is_relative_to(root) or not resolved.is_file():
        return None, "control path escapes plugin root or is not a regular file"
    return resolved, None


def build_baseline(root: Path) -> dict[str, Any]:
    root = root.resolve()
    files: dict[str, str] = {}
    for relative in PROTECTED_PATHS:
        path, error = _contained_regular_file(root, relative)
        if error or path is None:
            raise ValueError(f"{relative}: {error}")
        files[relative] = _sha256(path)
    return {
        "schema_version": "1.0",
        "hook_protocol": {"source": PROTOCOL_SOURCE, "checked_at": PROTOCOL_CHECKED_AT},
        "files": files,
    }


def _integrity_checks(root: Path) -> list[Check]:
    baseline_file, error = _contained_regular_file(root, BASELINE_PATH)
    if error or baseline_file is None:
        return [Check("integrity.baseline", "fail", error or "missing baseline")]
    try:
        baseline = _read_json(baseline_file)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return [Check("integrity.baseline", "fail", "baseline is unreadable or invalid")]
    checks: list[Check] = []
    expected_keys = {"schema_version", "hook_protocol", "files"}
    if not isinstance(baseline, dict) or set(baseline) != expected_keys or baseline.get("schema_version") != "1.0":
        return [Check("integrity.baseline", "fail", "baseline schema or keys drifted")]
    protocol = baseline.get("hook_protocol")
    if protocol != {"source": PROTOCOL_SOURCE, "checked_at": PROTOCOL_CHECKED_AT}:
        checks.append(Check("integrity.protocol-baseline", "fail", "Hook protocol source/date drifted"))
    else:
        checks.append(Check("integrity.protocol-baseline", "pass", "official Hook protocol baseline matches"))
    files = baseline.get("files")
    if not isinstance(files, dict) or set(files) != set(PROTECTED_PATHS):
        checks.append(Check("integrity.inventory", "fail", "protected file inventory drifted"))
        return checks
    checks.append(Check("integrity.inventory", "pass", f"{len(PROTECTED_PATHS)} protected files declared"))
    for relative in PROTECTED_PATHS:
        expected = files.get(relative)
        path, file_error = _contained_regular_file(root, relative)
        if file_error or path is None:
            checks.append(Check(f"integrity.file.{relative}", "fail", file_error or "missing"))
            continue
        if not isinstance(expected, str) or re.fullmatch(r"sha256:[0-9a-f]{64}", expected) is None:
            checks.append(Check(f"integrity.file.{relative}", "fail", "baseline digest is invalid"))
        elif _sha256(path) != expected:
            checks.append(Check(f"integrity.file.{relative}", "fail", "file bytes drifted"))
        else:
            checks.append(Check(f"integrity.file.{relative}", "pass", "digest matches"))
    return checks


def _hook_checks(root: Path) -> list[Check]:
    # hooks.json is shared plugin composition. Validate this Skill's three exact
    # semantic registrations instead of byte-attesting unrelated Hook changes.
    try:
        config = _read_json(root / "hooks" / "hooks.json")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return [Check("hook.schema", "fail", "hooks.json is unreadable or invalid")]
    hooks = config.get("hooks") if isinstance(config, dict) else None
    if not isinstance(hooks, dict):
        return [Check("hook.schema", "fail", "hooks.json lacks a hooks object")]
    checks: list[Check] = []
    for event in ("UserPromptSubmit", "PreToolUse", "PostToolUse"):
        entries = hooks.get(event)
        matches: list[tuple[dict[str, Any], dict[str, Any]]] = []
        if isinstance(entries, list):
            for entry in entries:
                if not isinstance(entry, dict) or not isinstance(entry.get("hooks"), list):
                    continue
                for handler in entry["hooks"]:
                    if isinstance(handler, dict) and handler.get("command") == EXPECTED_HOOK_COMMAND:
                        matches.append((entry, handler))
        if len(matches) != 1:
            checks.append(Check(f"hook.{event}", "fail", "expected exactly one data-security handler"))
            continue
        entry, handler = matches[0]
        valid = (
            handler.get("type") == "command"
            and handler.get("commandWindows") == EXPECTED_WINDOWS_COMMAND
            and isinstance(handler.get("timeout"), int)
            and 1 <= handler["timeout"] <= 10
            and handler.get("async") is not True
            and (event == "UserPromptSubmit" or entry.get("matcher") == "*")
        )
        checks.append(
            Check(
                f"hook.{event}",
                "pass" if valid else "fail",
                "synchronous documented handler matches" if valid else "handler options or matcher drifted",
            )
        )
    return checks


def _capability_checks(root: Path) -> list[Check]:
    try:
        contract = _read_json(root / "governance" / "capability-contracts.json")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return [Check("capability.registration", "fail", "capability registry is unreadable or invalid")]
    capabilities = contract.get("capabilities") if isinstance(contract, dict) else None
    matching = [
        item for item in capabilities or []
        if isinstance(item, dict) and item.get("skill") == "company-data-security"
    ]
    valid = (
        len(matching) == 1
        and matching[0].get("primary_outputs") == ["confidentiality.work-plan.v1"]
        and bool(matching[0].get("direct_trigger"))
        and bool(matching[0].get("negative_trigger"))
    )
    checks = [
        Check(
            "capability.registration",
            "pass" if valid else "fail",
            "first-class Skill owner is registered" if valid else "Skill owner registration drifted",
        )
    ]
    try:
        claim_registry = _read_json(root / "governance" / "claim-kinds.json")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        checks.append(Check("capability.claim-kinds", "fail", "claim-kind registry is unreadable or invalid"))
        return checks
    kinds = claim_registry.get("kinds") if isinstance(claim_registry, dict) else None
    observed = {
        item.get("id")
        for item in kinds or []
        if isinstance(item, dict) and item.get("owner") == "company-data-security"
    }
    expected = {
        f"company-data-security.{family}"
        for family in ("analysis", "artifact", "decision", "interaction", "limitation", "test")
    }
    valid_kinds = observed == expected
    checks.append(
        Check(
            "capability.claim-kinds",
            "pass" if valid_kinds else "fail",
            "task-neutral claim kinds are registered" if valid_kinds else "claim-kind registration drifted",
        )
    )
    return checks


def _self_test_checks(root: Path) -> list[Check]:
    hook_path = root / "hooks" / "data_security_hook.py"
    token = "gh" + "p_" + ("A7b9" * 9)

    def invoke(event: dict[str, Any]) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, str(hook_path)],
            input=json.dumps(event).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=10,
            check=False,
        )

    base = {
        "session_id": "doctor-synthetic",
        "turn_id": "doctor-synthetic",
        "cwd": str(root),
    }
    try:
        safe = invoke({**base, "hook_event_name": "UserPromptSubmit", "prompt": "public schema question"})
        blocked = invoke({**base, "hook_event_name": "UserPromptSubmit", "prompt": "inspect " + token})
        post = invoke(
            {
                **base,
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash",
                "tool_input": {"command": "synthetic"},
                "tool_response": {"credential": token, "state": "failed"},
            }
        )
        blocked_json = json.loads(blocked.stdout.decode("utf-8"))
        post_json = json.loads(post.stdout.decode("utf-8"))
        leak = any(token.encode("utf-8") in value for value in (safe.stdout, safe.stderr, blocked.stdout, blocked.stderr, post.stdout, post.stderr))
        safe_ok = safe.returncode == 0 and safe.stdout == b"" and safe.stderr == b""
        block_ok = blocked.returncode == 0 and blocked_json.get("decision") == "block"
        post_ok = (
            post.returncode == 0
            and post_json.get("continue") is False
            and "{{DLP:SECRET:" in post_json.get("hookSpecificOutput", {}).get("additionalContext", "")
        )
    except (OSError, subprocess.SubprocessError, UnicodeDecodeError, json.JSONDecodeError):
        safe_ok = block_ok = post_ok = False
        leak = False
    return [
        Check("self-test.safe-pass", "pass" if safe_ok else "fail", "safe synthetic prompt passes quietly" if safe_ok else "safe prompt self-test failed"),
        Check("self-test.prompt-block", "pass" if block_ok else "fail", "synthetic secret prompt is blocked" if block_ok else "secret prompt self-test failed"),
        Check("self-test.post-redaction", "pass" if post_ok else "fail", "synthetic tool result is replaced" if post_ok else "tool-output self-test failed"),
        Check("self-test.no-raw-leak", "fail" if leak else "pass", "synthetic value appeared in Hook output" if leak else "synthetic value absent from stdout and stderr"),
    ]


def _template_checks(root: Path) -> list[Check]:
    checks: list[Check] = []
    yaml_text = (root / "skills" / "company-data-security" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    yaml_ok = "$company-data-security" in yaml_text and "allow_implicit_invocation: true" in yaml_text
    checks.append(Check("skill.metadata", "pass" if yaml_ok else "fail", "Skill invocation metadata matches" if yaml_ok else "Skill metadata drifted"))
    required_phrases = {
        "chatgpt_work": (
            "skills/company-data-security/assets/chatgpt-work-instructions.md",
            "do not provide a deterministic pre-send Hook",
        ),
        "ordinary_chat": (
            "skills/company-data-security/assets/ordinary-chat-instructions.md",
            "not a deterministic pre-send interception layer",
        ),
    }
    for surface, (relative, phrase) in required_phrases.items():
        try:
            text = (root / relative).read_text(encoding="utf-8")
        except OSError:
            text = ""
        valid = phrase in text
        checks.append(Check(f"template.{surface}", "pass" if valid else "fail", "explicit guidance-only boundary present" if valid else "surface limitation text drifted"))
    return checks


def _attestation_checks(path: Path | None) -> list[Check]:
    surfaces = {
        "codex": ("hook_trust_reviewed",),
        "chatgpt_work": ("instructions_reviewed", "synthetic_self_test_passed"),
        "ordinary_chat": ("instructions_reviewed", "synthetic_self_test_passed"),
    }
    if path is None:
        return [
            Check(f"surface.{surface}.{field}", "not_observed", "live state requires manual evidence", required=False)
            for surface, fields in surfaces.items()
            for field in fields
        ]
    try:
        value = _read_json(path, max_bytes=65_536)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError):
        return [Check("surface.attestation", "fail", "attestation is unreadable or invalid")]
    if not isinstance(value, dict) or value.get("schema_version") != "1.0":
        return [Check("surface.attestation", "fail", "attestation schema drifted")]
    checks: list[Check] = []
    for surface, fields in surfaces.items():
        entry = value.get(surface)
        for field in fields:
            observed = isinstance(entry, dict) and entry.get(field) is True
            checks.append(
                Check(
                    f"surface.{surface}.{field}",
                    "self_attested" if observed else "not_observed",
                    "explicit self-attestation supplied; independently verify for high assurance" if observed else "live state not attested",
                    required=False,
                )
            )
    return checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check confidentiality-control packaging and activation evidence")
    parser.add_argument("--plugin-root", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--attestation", type=Path, help="optional bounded self-attestation JSON")
    parser.add_argument("--print-baseline", action="store_true", help="print expected protected-file digests without writing files")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = args.plugin_root.expanduser().resolve()
    if args.print_baseline:
        try:
            print(json.dumps(build_baseline(root), indent=2, sort_keys=True))
        except (OSError, ValueError) as exc:
            print(json.dumps({"status": "invalid", "error": str(exc)}, sort_keys=True))
            return 2
        return 0
    checks = [
        *_integrity_checks(root),
        *_hook_checks(root),
        *_capability_checks(root),
        *_template_checks(root),
        *_self_test_checks(root),
        *_attestation_checks(args.attestation),
    ]
    self_test_passed = all(
        item.status == "pass" for item in checks if item.check_id.startswith("self-test.")
    )
    checks.append(
        Check(
            "surface.codex.synthetic_self_test_passed",
            "pass" if self_test_passed else "fail",
            "doctor executed the installed Hook bytes with synthetic inputs" if self_test_passed else "installed Hook self-test failed",
        )
    )
    required_failures = [item for item in checks if item.required and item.status != "pass"]
    manual = [item for item in checks if not item.required and item.status in {"not_observed", "self_attested"}]
    status = "invalid" if required_failures else "valid_with_manual_gates" if manual else "valid"
    print(
        json.dumps(
            {
                "status": status,
                "plugin_root": str(root),
                "required_failures": len(required_failures),
                "manual_gates": len(manual),
                "checks": [item.as_dict() for item in checks],
                "claim_limit": "This proves packaged state at check time, not central immutability or live account policy.",
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 2 if required_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
