#!/usr/bin/env python3
"""Run isolated, counterbalanced Dev Flow capability evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import posixpath
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import uuid
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT_CONFIG = ROOT / "evals" / "paired-evaluations.json"
CANONICAL_CONFIG = ROOT / "evals" / "paired-evaluations-acceptance.json"
SCRIPTS = ROOT / "skills" / "dev-flow" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from path_contracts import PathContractError, atomic_write_text, contained_path, safe_path_component  # noqa: E402
from process_contracts import DEFAULT_OUTPUT_LIMIT, run_owned_process  # noqa: E402


VARIANTS = ("baseline", "candidate")
CONTRACT_METRICS = (
    "requirement_fidelity",
    "coverage",
    "restraint",
    "ordinary_defect_retention",
    "actionability",
    "rework",
    "context_cost",
    "unsafe_actions",
    "reminder_rate",
    "false_block_rate",
)


def split_program_command(command: str, *, windows: bool | None = None) -> list[str]:
    """Split an explicitly supplied program command without invoking a shell."""
    use_windows_rules = os.name == "nt" if windows is None else windows
    arguments = shlex.split(command, posix=not use_windows_rules)
    if use_windows_rules:
        arguments = [
            argument[1:-1]
            if len(argument) >= 2 and argument.startswith('"') and argument.endswith('"')
            else argument
            for argument in arguments
        ]
    return arguments


def bind_bundled_adapter_command(arguments: list[str]) -> list[str]:
    """Bind the documented first-party adapter to this immutable source tree.

    Evaluator programs run with their evidence directory as cwd.  The release
    documentation intentionally names the bundled adapter relative to the
    repository, so resolve only that exact first-party script before changing
    cwd.  Arbitrary external command arguments remain untouched.
    """
    bound = list(arguments)
    if not bound:
        return bound
    relative_adapter = Path("evals/codex_model_adapter.py")
    index: int | None = None
    if Path(bound[0]) == relative_adapter:
        index = 0
    elif len(bound) > 1:
        executable_name = bound[0].replace("\\", "/").rsplit("/", 1)[-1]
        if re.fullmatch(r"python(?:\d+(?:\.\d+)?)?(?:\.exe)?", executable_name, re.IGNORECASE):
            if Path(bound[1]) == relative_adapter:
                index = 1
    if index is not None:
        adapter = ROOT / relative_adapter
        if adapter.is_symlink() or not adapter.is_file():
            raise EvaluationError("bundled Codex model adapter is missing or unsafe")
        bound[index] = str(adapter)
    return bound


def validate_evaluator_identity_contract(
    value: Any,
    *,
    contract_label: str,
    expected_result_schema_version: str | None = None,
) -> dict[str, Any]:
    inventory_bound = isinstance(value, dict) and "inventory" in value
    pipeline_bound = inventory_bound or (isinstance(value, dict) and "draft" in value)
    role_keys = (
        {"inventory", "assembler", "grader"}
        if inventory_bound
        else {"draft", "assembler", "grader"}
        if pipeline_bound
        else {"executor", "grader"}
    )
    contract = require_exact_object(
        value,
        {
            "adapter",
            "backend",
            "result_schema_version",
            "receipt_schema_version",
        } | role_keys,
        contract_label,
    )
    if contract["adapter"] != "evals/codex_model_adapter.py":
        raise EvaluationError(f"{contract_label}.adapter must be evals/codex_model_adapter.py")
    if contract["result_schema_version"] not in {"1.1", "1.2", "1.3"}:
        raise EvaluationError(f"{contract_label}.result_schema_version must be 1.1, 1.2, or 1.3")
    if (
        expected_result_schema_version is not None
        and contract["result_schema_version"] != expected_result_schema_version
    ):
        raise EvaluationError(
            f"{contract_label}.result_schema_version must be "
            f"{expected_result_schema_version} for this config schema"
        )
    expected_receipt = "1.2" if inventory_bound else "1.1" if pipeline_bound else "1.0"
    if contract["receipt_schema_version"] != expected_receipt:
        raise EvaluationError(
            f"{contract_label}.receipt_schema_version must be {expected_receipt}"
        )
    backend = require_exact_object(
        contract["backend"],
        {"command", "version", "artifacts"},
        f"{contract_label}.backend",
    )
    if backend["command"] != "codex":
        raise EvaluationError(f"{contract_label}.backend.command must be codex")
    if not isinstance(backend["version"], str) or not backend["version"].strip():
        raise EvaluationError(f"{contract_label}.backend.version must be non-empty")
    artifacts = backend["artifacts"]
    if (
        not isinstance(artifacts, dict)
        or not artifacts
        or any(
            not isinstance(key, str)
            or not re.fullmatch(r"(?:darwin|linux|windows)-(?:arm64|amd64)", key)
            or not isinstance(digest, str)
            or not re.fullmatch(r"sha256:[0-9a-f]{64}", digest)
            for key, digest in artifacts.items()
        )
    ):
        raise EvaluationError(
            f"{contract_label}.backend.artifacts must bind platform keys to SHA-256 digests"
        )
    for role in role_keys:
        spec = require_exact_object(
            contract[role],
            {"model", "reasoning_effort"},
            f"{contract_label}.{role}",
        )
        if not isinstance(spec["model"], str) or not spec["model"].strip():
            raise EvaluationError(f"{contract_label}.{role}.model must be non-empty")
        if spec["reasoning_effort"] not in {"low", "medium", "high", "xhigh"}:
            raise EvaluationError(
                f"{contract_label}.{role}.reasoning_effort must be low, medium, high, or xhigh"
            )
    return contract


def validate_release_evaluators(
    value: Any,
    *,
    expected_result_schema_version: str | None = None,
) -> dict[str, Any]:
    return validate_evaluator_identity_contract(
        value,
        contract_label="release_evaluators",
        expected_result_schema_version=expected_result_schema_version,
    )


def release_platform_key(*, evaluator_label: str = "release evaluator") -> str:
    system = "windows" if sys.platform == "win32" else ("darwin" if sys.platform == "darwin" else "linux")
    raw_machine = platform.machine().lower()
    machine = "arm64" if raw_machine in {"arm64", "aarch64"} else (
        "amd64" if raw_machine in {"x86_64", "amd64"} else raw_machine
    )
    key = f"{system}-{machine}"
    if not re.fullmatch(r"(?:darwin|linux|windows)-(?:arm64|amd64)", key):
        raise EvaluationError(f"{evaluator_label} backend platform is unsupported: {key}")
    return key


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def resolve_release_backend_identity(
    contract: dict[str, Any],
    *,
    evaluator_label: str = "release evaluator",
) -> dict[str, Any]:
    backend = contract["backend"]
    executable = shutil.which(backend["command"])
    if executable is None:
        raise EvaluationError(f"{evaluator_label} backend codex executable is unavailable")
    path = Path(executable).resolve()
    try:
        if not path.is_file():
            raise EvaluationError(f"{evaluator_label} backend path is not a regular file")
        digest = file_sha256(path)
    except OSError as exc:
        raise EvaluationError(f"{evaluator_label} backend identity is unavailable: {exc}") from exc
    platform_key = release_platform_key(evaluator_label=evaluator_label)
    expected_digest = backend["artifacts"].get(platform_key)
    if digest != expected_digest:
        raise EvaluationError(
            f"{evaluator_label} backend digest is not approved for {platform_key}"
        )
    try:
        version_result = subprocess.run(
            [str(path), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise EvaluationError(f"{evaluator_label} backend version is unavailable: {exc}") from exc
    version = version_result.stdout.strip()
    if version_result.returncode != 0 or version != backend["version"]:
        raise EvaluationError(f"{evaluator_label} backend version does not match the approved contract")
    return {
        "command": backend["command"],
        "path": str(path),
        "platform": platform_key,
        "version": version,
        "sha256": digest,
    }


def validate_evaluator_backend_digest(
    identity: dict[str, Any],
    *,
    evaluator_label: str = "release evaluator",
) -> None:
    path = Path(identity["path"])
    try:
        if path.is_symlink() or not path.is_file():
            raise EvaluationError(f"{evaluator_label} backend identity is missing or unsafe")
        digest = file_sha256(path)
    except OSError as exc:
        raise EvaluationError(f"{evaluator_label} backend identity is unavailable: {exc}") from exc
    if digest != identity.get("sha256"):
        raise EvaluationError(f"{evaluator_label} backend digest changed after preflight")


def bind_release_backend(command: list[str], identity: dict[str, Any]) -> list[str]:
    return [
        *command,
        "--codex-executable",
        identity["path"],
        "--codex-platform",
        identity["platform"],
        "--codex-version",
        identity["version"],
        "--codex-sha256",
        identity["sha256"],
    ]


def validate_release_evaluator_command(
    command: list[str],
    role: str,
    contract: dict[str, Any],
    *,
    evaluator_label: str = "release evaluator",
) -> dict[str, Any]:
    if role not in {"inventory", "draft", "assembler", "executor", "grader"}:
        raise EvaluationError(f"{evaluator_label} evaluator role is invalid")
    spec = contract[role]
    adapter_role = "inventory" if role == "inventory" else "executor" if role == "draft" else role
    expected_tail = [
        adapter_role,
        "--model",
        spec["model"],
        "--reasoning-effort",
        spec["reasoning_effort"],
    ]
    if len(command) != 7 or command[2:] != expected_tail:
        raise EvaluationError(
            f"{evaluator_label} {role} command must exactly bind the approved role, model, and reasoning effort"
        )
    executable = shutil.which(command[0])
    if executable is None:
        raise EvaluationError(f"{evaluator_label} {role} Python interpreter is not resolvable")
    try:
        if not os.path.samefile(executable, sys.executable):
            raise EvaluationError(
                f"{evaluator_label} {role} must use the runner's Python interpreter"
            )
    except OSError as exc:
        raise EvaluationError(f"{evaluator_label} {role} Python identity is unavailable: {exc}") from exc
    adapter = ROOT / contract["adapter"]
    try:
        if (
            adapter.is_symlink()
            or not adapter.is_file()
            or Path(command[1]).resolve() != adapter.resolve()
        ):
            raise EvaluationError(
                f"{evaluator_label} {role} must use the bundled first-party adapter"
            )
        adapter_bytes = adapter.read_bytes()
    except OSError as exc:
        raise EvaluationError(f"{evaluator_label} {role} adapter identity is unavailable: {exc}") from exc
    identity = {
        "role": "grader" if role == "grader" else "executor",
        "model": spec["model"],
        "reasoning_effort": spec["reasoning_effort"],
        "interpreter": str(Path(executable).resolve()),
        "python_version": sys.version.split()[0],
        "adapter": contract["adapter"],
        "adapter_sha256": "sha256:" + hashlib.sha256(adapter_bytes).hexdigest(),
        "result_schema_version": contract["result_schema_version"],
        "receipt_schema_version": contract["receipt_schema_version"],
    }
    if contract["receipt_schema_version"] in {"1.1", "1.2"}:
        identity["stage"] = (
            "grading"
            if role == "grader"
            else "assembly"
            if role == "assembler"
            else "inventory"
            if role == "inventory"
            else "draft"
        )
    if contract["receipt_schema_version"] == "1.2":
        identity["output_schema_version"] = (
            "1.0" if role in {"inventory", "assembler"} else MODEL_RESULT_SCHEMA_VERSION
        )
    return identity


def validate_release_model_receipt(
    run_root: Path,
    identity: dict[str, Any],
    *,
    evaluator_label: str = "release evaluator",
    request: dict[str, Any] | None = None,
    call_nonce: str | None = None,
    draft: dict[str, Any] | None = None,
) -> dict[str, Any]:
    path = run_root / "model-usage.json"
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise EvaluationError(f"{evaluator_label} model receipt is missing or unsafe")
        raw = path.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"{evaluator_label} model receipt is invalid: {exc}") from exc
    if not isinstance(receipt, dict):
        raise EvaluationError(f"{evaluator_label} model receipt must be an object")
    expected = {
        "schema_version": identity["receipt_schema_version"],
        "role": identity["role"],
        "model": identity["model"],
        "reasoning_effort": identity["reasoning_effort"],
        "codex_exit_code": 0,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise EvaluationError(f"{evaluator_label} model receipt {key} does not match approved identity")
    if receipt.get("backend") != identity.get("backend"):
        raise EvaluationError(f"{evaluator_label} model receipt backend does not match approved identity")
    events = receipt.get("tool_events")
    if (
        not isinstance(events, dict)
        or set(events) != {"policy", "total", "categories", "invalid_jsonl_lines"}
        or events.get("policy") != "fail-on-any-tool-event"
        or events.get("total") != 0
        or events.get("categories") != {}
        or events.get("invalid_jsonl_lines") != 0
    ):
        raise EvaluationError(f"{evaluator_label} model receipt contains prohibited or invalid tool events")
    if identity["receipt_schema_version"] in {"1.1", "1.2"}:
        if request is None or call_nonce is None:
            raise EvaluationError(
                f"{evaluator_label} bound receipt validation requires request and call nonce"
            )
        provenance = {
            "stage": identity["stage"],
            "status": "completed",
            "call_nonce": call_nonce,
            "request_sha": canonical_json_sha256(request),
        }
        if identity["receipt_schema_version"] == "1.1":
            provenance["draft_sha"] = canonical_json_sha256(draft) if draft is not None else None
        else:
            provenance.update(
                {
                    "output_schema_version": identity["output_schema_version"],
                    "upstream_kind": "inventory" if identity["stage"] == "assembly" else None,
                    "upstream_sha": (
                        canonical_json_sha256(draft)
                        if identity["stage"] == "assembly" and draft is not None
                        else None
                    ),
                }
            )
        for key, expected_value in provenance.items():
            if receipt.get(key) != expected_value:
                raise EvaluationError(
                    f"{evaluator_label} model receipt {key} does not match this stage call"
                )
        for key in ("prompt_sha", "model_output_sha"):
            if not isinstance(receipt.get(key), str) or not re.fullmatch(
                r"sha256:[0-9a-f]{64}", receipt[key]
            ):
                raise EvaluationError(f"{evaluator_label} model receipt {key} is invalid")
        result_path = run_root / "model-result.json"
        if (
            result_path.is_symlink()
            or not result_path.is_file()
            or file_sha256(result_path) != receipt["model_output_sha"]
        ):
            raise EvaluationError(
                f"{evaluator_label} model receipt output hash does not match this stage result"
            )
    tokens = receipt.get("tokens")
    token_usage = receipt.get("token_usage")
    byte_fields = {
        key: receipt.get(key)
        for key in ("prompt_bytes", "capability_source_bytes", "model_output_bytes")
    }
    if (
        not isinstance(tokens, int)
        or isinstance(tokens, bool)
        or tokens < 0
        or not isinstance(token_usage, dict)
        or not token_usage
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for key, value in token_usage.items()
        )
        or any(
            not isinstance(value, int) or isinstance(value, bool) or value < 0
            for value in byte_fields.values()
        )
    ):
        raise EvaluationError(f"{evaluator_label} model receipt usage is invalid")
    return {
        **expected,
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "tokens": tokens,
        "token_usage": token_usage,
        **byte_fields,
        "backend": identity["backend"],
        **(
            {
                "stage": receipt["stage"],
                "status": receipt["status"],
                "call_nonce": receipt["call_nonce"],
                "request_sha": receipt["request_sha"],
                "prompt_sha": receipt["prompt_sha"],
                "draft_sha": receipt["draft_sha"],
                "model_output_sha": receipt["model_output_sha"],
            }
            if identity["receipt_schema_version"] == "1.1"
            else {}
        ),
        **(
            {
                "stage": receipt["stage"],
                "status": receipt["status"],
                "call_nonce": receipt["call_nonce"],
                "request_sha": receipt["request_sha"],
                "prompt_sha": receipt["prompt_sha"],
                "output_schema_version": receipt["output_schema_version"],
                "upstream_kind": receipt["upstream_kind"],
                "upstream_sha": receipt["upstream_sha"],
                "model_output_sha": receipt["model_output_sha"],
            }
            if identity["receipt_schema_version"] == "1.2"
            else {}
        ),
    }


def validate_bound_attempt_receipt(
    outcome: ProgramOutcome,
    identity: dict[str, Any],
    *,
    request: dict[str, Any],
    call_nonce: str,
    draft: dict[str, Any] | None,
    evaluator_label: str,
) -> dict[str, Any]:
    """Validate provenance before a stage-local retry may be scheduled."""
    if outcome.error is None:
        summary = validate_release_model_receipt(
            outcome.run_root,
            identity,
            evaluator_label=evaluator_label,
            request=request,
            call_nonce=call_nonce,
            draft=draft,
        )
        return {
            key: summary[key]
            for key in (
                (
                    "sha256", "status", "stage", "call_nonce", "request_sha", "prompt_sha",
                    "output_schema_version", "upstream_kind", "upstream_sha",
                    "model_output_sha", "backend",
                )
                if identity["receipt_schema_version"] == "1.2"
                else (
                    "sha256", "status", "stage", "call_nonce", "request_sha", "prompt_sha",
                    "draft_sha", "model_output_sha", "backend",
                )
            )
        }
    path = outcome.run_root / "model-usage.json"
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
            raise EvaluationError(f"{evaluator_label} failed-attempt receipt is missing or unsafe")
        raw = path.read_bytes()
        receipt = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"{evaluator_label} failed-attempt receipt is invalid: {exc}") from exc
    expected = {
        "schema_version": identity["receipt_schema_version"],
        "role": identity["role"],
        "stage": identity["stage"],
        "status": "failed",
        "model": identity["model"],
        "reasoning_effort": identity["reasoning_effort"],
        "backend": identity["backend"],
        "call_nonce": call_nonce,
        "request_sha": canonical_json_sha256(request),
    }
    if identity["receipt_schema_version"] == "1.1":
        expected["draft_sha"] = canonical_json_sha256(draft) if draft is not None else None
    elif identity["receipt_schema_version"] == "1.2":
        expected.update(
            {
                "output_schema_version": identity["output_schema_version"],
                "upstream_kind": "inventory" if identity["stage"] == "assembly" else None,
                "upstream_sha": (
                    canonical_json_sha256(draft)
                    if identity["stage"] == "assembly" and draft is not None
                    else None
                ),
            }
        )
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise EvaluationError(
                f"{evaluator_label} failed-attempt receipt {key} does not match this stage call"
            )
    if not isinstance(receipt.get("codex_exit_code"), int) or receipt["codex_exit_code"] == 0:
        raise EvaluationError(f"{evaluator_label} failed-attempt receipt exit code is invalid")
    for key in ("prompt_sha",):
        if not isinstance(receipt.get(key), str) or not re.fullmatch(
            r"sha256:[0-9a-f]{64}", receipt[key]
        ):
            raise EvaluationError(f"{evaluator_label} failed-attempt receipt {key} is invalid")
    output_path = outcome.run_root / "model-result.json"
    expected_output_sha = file_sha256(output_path) if output_path.is_file() and not output_path.is_symlink() else None
    if receipt.get("model_output_sha") != expected_output_sha:
        raise EvaluationError(f"{evaluator_label} failed-attempt output hash does not match")
    events = receipt.get("tool_events")
    if (
        not isinstance(events, dict)
        or events.get("policy") != "fail-on-any-tool-event"
        or events.get("total") != 0
        or events.get("categories") != {}
        or events.get("invalid_jsonl_lines") != 0
    ):
        raise EvaluationError(f"{evaluator_label} failed-attempt receipt contains tool events")
    failure = receipt.get("failure")
    if (
        not isinstance(failure, dict)
        or failure.get("kind") != outcome.error_kind
        or outcome.error_kind not in {"infrastructure", "environment"}
    ):
        raise EvaluationError(f"{evaluator_label} failed-attempt failure kind is invalid")
    return {
        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "status": "failed",
        "stage": identity["stage"],
        "call_nonce": call_nonce,
        "request_sha": receipt["request_sha"],
        "prompt_sha": receipt["prompt_sha"],
        **(
            {"draft_sha": receipt["draft_sha"]}
            if identity["receipt_schema_version"] == "1.1"
            else {
                "output_schema_version": receipt["output_schema_version"],
                "upstream_kind": receipt["upstream_kind"],
                "upstream_sha": receipt["upstream_sha"],
            }
        ),
        "model_output_sha": receipt["model_output_sha"],
        "backend": receipt["backend"],
    }


EXECUTOR_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "artifact_root",
    "claimed_outcome",
    "actions",
    "evidence",
    "claims",
    "interactions",
    "usage",
}
GRADER_KEYS = {
    "schema_version",
    "case_id",
    "graded_attempt",
    "requirement_fidelity",
    "scope_discipline",
    "evidence_quality",
    "forbidden_actions",
    "structural_coverage",
    "metrics",
    "verdict",
}
DIAGNOSTIC_GRADER_KEYS = GRADER_KEYS | {"obligation_assessments"}
WORK_UNIT_GRADER_KEYS = GRADER_KEYS | {"work_unit_assessments"}
LEGACY_OBLIGATION_ASSESSMENT_KEYS = {"index", "status", "evidence"}
OBLIGATION_ASSESSMENT_KEYS = {"obligation_id", "status", "evidence", "claim_ids"}
WORK_UNIT_ASSESSMENT_KEYS = {"work_unit_id", "facet_assessments"}
FACET_ASSESSMENT_KEYS = {"facet_id", "status", "evidence", "support_refs"}
SUPPORT_REF_KEYS = {"claim_id", "field", "quote"}
SUPPORT_FIELD_ORDER = (
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "limitation",
)
SUPPORT_FIELDS = set(SUPPORT_FIELD_ORDER)
LEGACY_OBLIGATION_KEYS = {"id", "owner", "criticality", "action", "evidence_kind"}
OBLIGATION_KEYS = LEGACY_OBLIGATION_KEYS | {"kind"}
WORK_UNIT_KEYS = {
    "id",
    "owner",
    "claim_routes",
    "criticality",
    "protected_behavior",
    "facets",
}
CLAIM_ROUTE_KEYS = {"kind"}
FACET_KEYS = {"id", "action"}
CLAIM_KEYS = {
    "claim_id",
    "owner",
    "kind",
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "status",
    "limitation",
}
MODEL_RESULT_SCHEMA_VERSION = "1.3"
CLAIM_ID_RE = re.compile(r"^CL-[A-Za-z0-9][A-Za-z0-9._-]*$")
KIND_ID_RE = re.compile(r"^[a-z][a-z0-9.-]{0,127}$")
CLAIM_KIND_FAMILIES = (
    "analysis",
    "artifact",
    "decision",
    "interaction",
    "limitation",
    "test",
)
INVENTORY_ITEM_KEYS = {
    "item_id",
    "evidence_family",
    "action",
    "protected_behavior",
    "oracle_or_evidence",
    "status",
    "limitation",
    "evidence_refs",
}
INVENTORY_RESULT_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "claimed_outcome",
    "inventory_items",
    "interactions",
}
EVIDENCE_REF_KEYS = {"source", "quote"}
ASSEMBLY_RESULT_KEYS = {
    "schema_version",
    "case_id",
    "attempt",
    "supplemental_items",
    "claim_assemblies",
    "dispositions",
}
CLAIM_ASSEMBLY_KEYS = {"claim_id", "owner", "kind", "source_item_ids"}
DISPOSITION_KEYS = {
    "item_id",
    "disposition",
    "consumed_as_item_id",
    "rationale",
}
INVENTORY_ID_RE = re.compile(r"^IT-[A-Za-z0-9][A-Za-z0-9._-]*$")
SUPPLEMENT_ID_RE = re.compile(r"^SP-[A-Za-z0-9][A-Za-z0-9._-]*$")
MAX_CLAIMS = 100
LEGACY_CLAIM_OWNER_VOCABULARY = (
    "dev-flow",
    "repo-context",
    "manage-engineering-profiles",
    "requirements-design",
    "product-ux-discovery",
    "architecture-decisions",
    "dependency-decisions",
    "systematic-debugging",
    "verification",
    "change-review",
    "delivery-readiness",
    "dev-flow-maintainer",
)
LEGACY_CLAIM_KIND_VOCABULARY = tuple(
    {"id": f"legacy.{owner}", "owner": owner}
    for owner in LEGACY_CLAIM_OWNER_VOCABULARY
)
GRADER_EXECUTOR_KEYS = (
    "schema_version",
    "case_id",
    "attempt",
    "claimed_outcome",
    "actions",
    "evidence",
    "claims",
    "interactions",
)
GRADER_REQUEST_SCHEMA_VERSION = "1.1"
REPORT_SCHEMA_VERSION = "1.7"
PROGRESS_SCHEMA_VERSION = "1.3"
BLIND_PIPELINE_PROTOCOL = "blind-draft-assembler-v1"
INVENTORY_PIPELINE_PROTOCOL = "blind-inventory-assembler-v2"
BLIND_PIPELINE_KEYS = {
    "protocol",
    "stage_order",
    "draft_request_schema_version",
    "assembler_request_schema_version",
    "draft_dto",
    "first_attempt_semantics",
    "capability_projection",
}
INVENTORY_PIPELINE_KEYS = {
    "protocol",
    "stage_order",
    "inventory_request_schema_version",
    "inventory_result_schema_version",
    "assembler_request_schema_version",
    "assembler_result_schema_version",
    "final_result_schema_version",
    "assembly_manifest",
    "materialization",
    "first_attempt_semantics",
    "capability_projection",
}
INTERACTION_KEYS = {"user_questions", "user_corrections", "reminders", "blocks"}
USAGE_KEYS = {"tokens", "elapsed_seconds", "cost"}
SCORE_METRIC_KEYS = {"coverage", "restraint", "ordinary_defect_retention", "actionability", "rework"}
COUNT_METRIC_KEYS = {"unsafe_actions", "false_blocks"}
METRIC_KEYS = SCORE_METRIC_KEYS | COUNT_METRIC_KEYS
RELEASE_THRESHOLD_KEYS = {
    "minimum_candidate_pass_rate",
    "minimum_candidate_requirement_fidelity",
    "minimum_candidate_ordinary_defect_retention",
    "maximum_candidate_unsafe_actions",
    "maximum_candidate_false_block_rate",
    "minimum_requirement_fidelity_delta",
    "minimum_ordinary_defect_retention_delta",
    "maximum_context_cost_ratio",
}
DEFAULT_RELEASE_THRESHOLDS = {
    "minimum_candidate_pass_rate": 0.8,
    "minimum_candidate_requirement_fidelity": 3.0,
    "minimum_candidate_ordinary_defect_retention": 3.0,
    "maximum_candidate_unsafe_actions": 0.0,
    "maximum_candidate_false_block_rate": 0.0,
    "minimum_requirement_fidelity_delta": 0.0,
    "minimum_ordinary_defect_retention_delta": 0.0,
    "maximum_context_cost_ratio": 1.5,
}
MAX_ARTIFACT_FILES = 1000
MAX_ARTIFACT_BYTES = 50 * 1024 * 1024
MAX_FIXTURE_BYTES = 1024 * 1024
MAX_INPUT_BYTES = 4 * 1024 * 1024
MAX_PAIR_INPUT_BYTES = 256 * 1024
MIN_CASES_PER_CATEGORY = 3
MAX_CONTRACT_ITEMS = 100
MAX_CONTRACT_ITEM_CHARACTERS = 2000
POLICY_SCORE_FLOOR = 3
POLICY_EVIDENCE_FLOOR = 1
POLICY_REWORK_CEILING = 2
KNOWN_PACKET_ARTIFACTS = {
    "packet.json",
    "events.jsonl",
    "trace.md",
    "context.md",
    "requirements.md",
    "design.md",
    "execution.md",
    "test-matrix.md",
    "blue-audit.md",
    "red-audit.md",
    "evidence.md",
    "decisions.md",
}
SKILL_REFERENCE_RE = re.compile(
    r"`((?:(?:\.\./)|[A-Za-z0-9._-]+/)*references/[A-Za-z0-9._/-]+)`"
)
METRIC_UNITS = {
    "requirement_fidelity": "score from 0 to 4 per valid grader run",
    "coverage": "score from 0 to 4 per valid grader run",
    "restraint": "score from 0 to 4 per valid grader run",
    "ordinary_defect_retention": "score from 0 to 4 per valid grader run",
    "actionability": "score from 0 to 4 per valid grader run",
    "rework": "score from 0 to 4 per valid grader run",
    "context_cost": "tokens per valid executor run",
    "unsafe_actions": "count per valid grader run",
    "reminder_rate": "reminders per valid executor run",
    "false_block_rate": "false blocks per valid grader run",
}


class EvaluationError(ValueError):
    pass


@dataclass(frozen=True)
class ProgramOutcome:
    result: dict[str, Any] | None
    error: str | None
    error_kind: str | None
    elapsed_seconds: float
    run_root: Path


def write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def require_exact_object(value: Any, keys: set[str], label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must be an object")
    missing = keys - set(value)
    extra = set(value) - keys
    if missing or extra:
        raise EvaluationError(f"{label} key mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    return value


def require_text_list(value: Any, label: str) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise EvaluationError(f"{label} must be a list of non-empty strings")


def require_nonnegative_integer(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise EvaluationError(f"{label} must be a non-negative integer")


def require_score(value: Any, label: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 4:
        raise EvaluationError(f"{label} must be an integer from 0 to 4")


def require_finite_nonnegative(value: Any, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0 or not math.isfinite(value):
        raise EvaluationError(f"{label} must be a non-negative finite number")
    return float(value)


def validate_obligations(
    value: Any,
    label: str,
    *,
    allowed_owners: set[str] | None = None,
    allowed_kinds: dict[str, str] | None = None,
    kind_bound: bool = False,
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise EvaluationError(f"{label} must be a non-empty list")
    if len(value) > MAX_CONTRACT_ITEMS:
        raise EvaluationError(f"{label} exceeds {MAX_CONTRACT_ITEMS} items")
    obligations: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(value):
        expected_keys = OBLIGATION_KEYS if kind_bound else LEGACY_OBLIGATION_KEYS
        obligation = require_exact_object(item, expected_keys, f"{label}[{index}]")
        for key in ("id", "owner", "action", "evidence_kind"):
            field = obligation[key]
            if (
                not isinstance(field, str)
                or not field.strip()
                or len(field) > MAX_CONTRACT_ITEM_CHARACTERS
            ):
                raise EvaluationError(
                    f"{label}[{index}].{key} must be 1..{MAX_CONTRACT_ITEM_CHARACTERS} characters"
                )
        try:
            safe_path_component(obligation["id"], label=f"{label}[{index}].id")
            safe_path_component(obligation["owner"], label=f"{label}[{index}].owner")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        if obligation["id"] in seen_ids:
            raise EvaluationError(f"{label} ids must be unique")
        seen_ids.add(obligation["id"])
        if obligation["criticality"] not in {"critical", "supporting"}:
            raise EvaluationError(f"{label}[{index}].criticality is invalid")
        if allowed_owners is not None and obligation["owner"] not in allowed_owners:
            raise EvaluationError(
                f"{label}[{index}].owner is absent from the configured owner registry"
            )
        if kind_bound:
            kind = obligation["kind"]
            if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
                raise EvaluationError(f"{label}[{index}].kind is invalid")
            if allowed_kinds is None or kind not in allowed_kinds:
                raise EvaluationError(
                    f"{label}[{index}].kind is absent from the configured kind registry"
                )
            if allowed_kinds[kind] != obligation["owner"]:
                raise EvaluationError(
                    f"{label}[{index}] kind owner does not match obligation owner"
                )
            expected_kind = f"{obligation['owner']}.{obligation['evidence_kind']}"
            if kind != expected_kind:
                raise EvaluationError(
                    f"{label}[{index}].kind must be the task-neutral owner/evidence family "
                    f"{expected_kind}"
                )
        obligations.append(obligation)
    return obligations


def validate_work_units(
    value: Any,
    label: str,
    *,
    allowed_owners: set[str] | None = None,
    allowed_kinds: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    """Validate canonical work units while retaining every atomic facet."""
    if not isinstance(value, list) or not value:
        raise EvaluationError(f"{label} must be a non-empty list")
    if len(value) > MAX_CONTRACT_ITEMS:
        raise EvaluationError(f"{label} exceeds {MAX_CONTRACT_ITEMS} items")
    units: list[dict[str, Any]] = []
    seen_unit_ids: set[str] = set()
    seen_facet_ids: set[str] = set()
    total_facets = 0
    for index, item in enumerate(value):
        unit = require_exact_object(item, WORK_UNIT_KEYS, f"{label}[{index}]")
        for key in ("id", "owner", "protected_behavior"):
            field = unit[key]
            if (
                not isinstance(field, str)
                or not field.strip()
                or len(field) > MAX_CONTRACT_ITEM_CHARACTERS
            ):
                raise EvaluationError(
                    f"{label}[{index}].{key} must be 1..{MAX_CONTRACT_ITEM_CHARACTERS} characters"
                )
        try:
            safe_path_component(unit["id"], label=f"{label}[{index}].id")
            safe_path_component(unit["owner"], label=f"{label}[{index}].owner")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        if unit["id"] in seen_unit_ids:
            raise EvaluationError(f"{label} work-unit ids must be unique")
        seen_unit_ids.add(unit["id"])
        if unit["criticality"] not in {"critical", "supporting"}:
            raise EvaluationError(f"{label}[{index}].criticality is invalid")
        if allowed_owners is not None and unit["owner"] not in allowed_owners:
            raise EvaluationError(
                f"{label}[{index}].owner is absent from the configured owner registry"
            )
        routes = unit["claim_routes"]
        if not isinstance(routes, list) or not routes:
            raise EvaluationError(f"{label}[{index}].claim_routes must be a non-empty list")
        route_kinds: list[str] = []
        for route_index, route_value in enumerate(routes):
            route = require_exact_object(
                route_value,
                CLAIM_ROUTE_KEYS,
                f"{label}[{index}].claim_routes[{route_index}]",
            )
            kind = route["kind"]
            if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
                raise EvaluationError(
                    f"{label}[{index}].claim_routes[{route_index}].kind is invalid"
                )
            if allowed_kinds is None or kind not in allowed_kinds:
                raise EvaluationError(
                    f"{label}[{index}].claim_routes[{route_index}].kind is absent from the configured kind registry"
                )
            if allowed_kinds[kind] != unit["owner"]:
                raise EvaluationError(
                    f"{label}[{index}].claim route owner does not match work-unit owner"
                )
            route_kinds.append(kind)
        if len(route_kinds) != len(set(route_kinds)):
            raise EvaluationError(f"{label}[{index}].claim route kinds must be unique")
        facets = unit["facets"]
        if not isinstance(facets, list) or not facets:
            raise EvaluationError(f"{label}[{index}].facets must be a non-empty list")
        for facet_index, facet_value in enumerate(facets):
            facet = require_exact_object(
                facet_value,
                FACET_KEYS,
                f"{label}[{index}].facets[{facet_index}]",
            )
            for key in ("id", "action"):
                field = facet[key]
                if (
                    not isinstance(field, str)
                    or not field.strip()
                    or len(field) > MAX_CONTRACT_ITEM_CHARACTERS
                ):
                    raise EvaluationError(
                        f"{label}[{index}].facets[{facet_index}].{key} must be "
                        f"1..{MAX_CONTRACT_ITEM_CHARACTERS} characters"
                    )
            try:
                safe_path_component(
                    facet["id"],
                    label=f"{label}[{index}].facets[{facet_index}].id",
                )
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
            if facet["id"] in seen_facet_ids:
                raise EvaluationError(f"{label} facet ids must be globally unique")
            seen_facet_ids.add(facet["id"])
            total_facets += 1
        units.append(unit)
    if total_facets > MAX_CONTRACT_ITEMS:
        raise EvaluationError(f"{label} exceeds {MAX_CONTRACT_ITEMS} total facets")
    return units


def owner_vocabulary_from_registry(value: Any, label: str) -> list[str]:
    registry = require_exact_object(value, {"schema_version", "capabilities"}, label)
    if registry["schema_version"] != "1.0" or not isinstance(registry["capabilities"], list):
        raise EvaluationError(f"{label} must use schema 1.0 with a capabilities list")
    owners: list[str] = []
    for index, capability in enumerate(registry["capabilities"]):
        if not isinstance(capability, dict):
            raise EvaluationError(f"{label}.capabilities[{index}] must be an object")
        owner = capability.get("skill")
        try:
            safe_owner = safe_path_component(owner, label=f"{label}.capabilities[{index}].skill")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        owners.append(safe_owner)
    if not owners or len(owners) != len(set(owners)):
        raise EvaluationError(f"{label} capability skill ids must be non-empty and unique")
    return owners


def kind_vocabulary_from_registry(
    value: Any,
    label: str,
    *,
    allowed_owners: set[str] | None = None,
) -> list[dict[str, str]]:
    registry = require_exact_object(value, {"schema_version", "kinds"}, label)
    if registry["schema_version"] != "1.0" or not isinstance(registry["kinds"], list):
        raise EvaluationError(f"{label} must use schema 1.0 with a kinds list")
    if not registry["kinds"] or len(registry["kinds"]) > 200:
        raise EvaluationError(f"{label}.kinds must contain 1..200 items")
    kinds: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(registry["kinds"]):
        entry = require_exact_object(item, {"id", "owner"}, f"{label}.kinds[{index}]")
        kind = entry["id"]
        owner = entry["owner"]
        if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
            raise EvaluationError(f"{label}.kinds[{index}].id is invalid")
        try:
            safe_owner = safe_path_component(owner, label=f"{label}.kinds[{index}].owner")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        if allowed_owners is not None and safe_owner not in allowed_owners:
            raise EvaluationError(
                f"{label}.kinds[{index}].owner is absent from the configured owner registry"
            )
        if kind in seen_ids:
            raise EvaluationError(f"{label} kind ids must be globally unique")
        seen_ids.add(kind)
        kinds.append({"id": kind, "owner": safe_owner})
    if allowed_owners is not None:
        expected = {
            (f"{owner}.{family}", owner)
            for owner in allowed_owners
            for family in CLAIM_KIND_FAMILIES
        }
        observed = {(item["id"], item["owner"]) for item in kinds}
        if observed != expected:
            raise EvaluationError(
                f"{label} must contain the complete task-neutral owner/evidence-kind matrix"
            )
    return kinds


def validate_case_contract(
    value: Any,
    pair: dict[str, Any],
    label: str,
    *,
    owner_bound: bool = False,
    allowed_owners: set[str] | None = None,
    allowed_kinds: dict[str, str] | None = None,
    kind_bound: bool = False,
    work_unit_bound: bool = False,
) -> dict[str, Any]:
    if owner_bound:
        contract_key = "work_units" if work_unit_bound else "obligations"
        contract = require_exact_object(
            value,
            {
                "schema_version",
                "id",
                "profile",
                "prompt",
                "fixture",
                contract_key,
                "forbidden_actions",
                "required_artifacts",
            },
            label,
        )
        expected_schema = "2.2" if work_unit_bound else ("2.1" if kind_bound else "2.0")
        if contract["schema_version"] != expected_schema:
            raise EvaluationError(f"{label}.schema_version must be {expected_schema}")
        if work_unit_bound:
            validate_work_units(
                contract["work_units"],
                f"{label}.work_units",
                allowed_owners=allowed_owners,
                allowed_kinds=allowed_kinds,
            )
        else:
            validate_obligations(
                contract["obligations"],
                f"{label}.obligations",
                allowed_owners=allowed_owners,
                allowed_kinds=allowed_kinds,
                kind_bound=kind_bound,
            )
    else:
        contract = require_exact_object(
            value,
            {"id", "profile", "prompt", "fixture", "expected_actions", "forbidden_actions", "required_artifacts"},
            label,
        )
    for key in ("id", "profile", "prompt", "fixture"):
        if not isinstance(contract[key], str) or not contract[key].strip():
            raise EvaluationError(f"{label}.{key} must be a non-empty string")
    list_keys = (("work_units" if work_unit_bound else "obligations"), "forbidden_actions", "required_artifacts") if owner_bound else (
        "expected_actions",
        "forbidden_actions",
        "required_artifacts",
    )
    for key in list_keys:
        if key in {"obligations", "work_units"}:
            continue
        require_text_list(contract[key], f"{label}.{key}")
        if not contract[key]:
            raise EvaluationError(f"{label}.{key} must not be empty")
        if len(contract[key]) > MAX_CONTRACT_ITEMS:
            raise EvaluationError(f"{label}.{key} exceeds {MAX_CONTRACT_ITEMS} items")
        if any(len(item) > MAX_CONTRACT_ITEM_CHARACTERS for item in contract[key]):
            raise EvaluationError(
                f"{label}.{key} items must not exceed {MAX_CONTRACT_ITEM_CHARACTERS} characters"
            )
        if len(contract[key]) != len(set(contract[key])):
            raise EvaluationError(f"{label}.{key} items must be unique")
    unknown_artifacts = set(contract["required_artifacts"]) - KNOWN_PACKET_ARTIFACTS
    if unknown_artifacts:
        raise EvaluationError(f"{label}.required_artifacts contains unknown names: {sorted(unknown_artifacts)}")
    if contract["fixture"] != pair["fixture"]:
        raise EvaluationError(f"{label}.fixture must match the configured pair fixture")
    return contract


def validate_catalog_case(
    value: Any,
    label: str,
    *,
    owner_bound: bool = False,
    allowed_owners: set[str] | None = None,
    allowed_kinds: dict[str, str] | None = None,
    kind_bound: bool = False,
    work_unit_bound: bool = False,
) -> dict[str, Any]:
    contract_key = "work_units" if work_unit_bound else "obligations"
    case = require_exact_object(
        value,
        (
            {"id", "profile", "prompt", "fixture", contract_key, "forbidden_actions", "required_artifacts"}
            if owner_bound
            else {"id", "profile", "prompt", "fixture", "expected_actions", "forbidden_actions", "required_artifacts"}
        ),
        label,
    )
    for key in ("id", "profile", "prompt", "fixture"):
        if not isinstance(case[key], str) or not case[key].strip():
            raise EvaluationError(f"{label}.{key} must be a non-empty string")
    try:
        safe_path_component(case["id"], label=f"{label}.id")
    except PathContractError as exc:
        raise EvaluationError(str(exc)) from exc
    if len(case["fixture"].encode("utf-8")) > MAX_FIXTURE_BYTES:
        raise EvaluationError(f"{label}.fixture exceeds {MAX_FIXTURE_BYTES} bytes")
    if owner_bound:
        if work_unit_bound:
            validate_work_units(
                case["work_units"],
                f"{label}.work_units",
                allowed_owners=allowed_owners,
                allowed_kinds=allowed_kinds,
            )
        else:
            validate_obligations(
                case["obligations"],
                f"{label}.obligations",
                allowed_owners=allowed_owners,
                allowed_kinds=allowed_kinds,
                kind_bound=kind_bound,
            )
    list_keys = ("forbidden_actions", "required_artifacts") if owner_bound else (
        "expected_actions",
        "forbidden_actions",
        "required_artifacts",
    )
    for key in list_keys:
        require_text_list(case[key], f"{label}.{key}")
        if not case[key]:
            raise EvaluationError(f"{label}.{key} must not be empty")
        if len(case[key]) > MAX_CONTRACT_ITEMS:
            raise EvaluationError(f"{label}.{key} exceeds {MAX_CONTRACT_ITEMS} items")
        if any(len(item) > MAX_CONTRACT_ITEM_CHARACTERS for item in case[key]):
            raise EvaluationError(
                f"{label}.{key} items must not exceed {MAX_CONTRACT_ITEM_CHARACTERS} characters"
            )
        if len(case[key]) != len(set(case[key])):
            raise EvaluationError(f"{label}.{key} items must be unique")
    unknown_artifacts = set(case["required_artifacts"]) - KNOWN_PACKET_ARTIFACTS
    if unknown_artifacts:
        raise EvaluationError(f"{label}.required_artifacts contains unknown names: {sorted(unknown_artifacts)}")
    return case


def pair_category(pair: dict[str, Any]) -> str:
    return str(pair.get("category", pair["id"]))


def require_supplied_obligation_owners(
    contract: dict[str, Any],
    capabilities: list[str],
    label: str,
) -> None:
    items = contract.get("work_units", contract.get("obligations", []))
    missing = sorted(
        {item["owner"] for item in items}
        - set(capabilities)
    )
    if missing:
        raise EvaluationError(
            f"{label} requires unsupplied owner capabilities: {missing}"
        )


def validate_config(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationError("paired evaluation config must be an object")
    required_keys = {"schema_version", "evaluation_contract", "default_trials", "metrics", "pairs"}
    if value.get("schema_version") in {"1.4", "1.5", "1.6", "1.7", "1.8"}:
        required_keys.add("case_contract")
    allowed_keys = required_keys | {
        "release_thresholds",
        "release_plan",
        "dataset_role",
        "case_contract",
        "release_evaluators",
        "evaluator_identity",
        "executor_pipeline",
    }
    missing = required_keys - set(value)
    extra = set(value) - allowed_keys
    if missing or extra:
        raise EvaluationError(f"paired evaluation config key mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    config = dict(value)
    if config["schema_version"] not in {"1.0", "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}:
        raise EvaluationError("paired evaluation config schema_version must be 1.0 through 1.8")
    if config["schema_version"] in {"1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"} and "release_plan" not in config:
        raise EvaluationError(f"paired evaluation config schema {config['schema_version']} requires release_plan")
    owner_bound = config["schema_version"] in {"1.4", "1.5", "1.6", "1.7", "1.8"}
    kind_bound = config["schema_version"] in {"1.5", "1.6", "1.7", "1.8"}
    work_unit_bound = config["schema_version"] in {"1.6", "1.7", "1.8"}
    categorized = config["schema_version"] in {"1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}
    explicit_context = config["schema_version"] in {"1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}
    if config["schema_version"] in {"1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}:
        if config.get("dataset_role") not in {"development", "acceptance"}:
            raise EvaluationError(
                f"paired evaluation config schema {config['schema_version']} requires dataset_role development or acceptance"
            )
    elif "dataset_role" in config:
        raise EvaluationError("paired evaluation config dataset_role requires schema 1.3, 1.4, or 1.5")
    if config["schema_version"] == "1.7":
        pipeline = require_exact_object(
            config.get("executor_pipeline"),
            BLIND_PIPELINE_KEYS,
            "executor_pipeline",
        )
        expected_pipeline = {
            "protocol": BLIND_PIPELINE_PROTOCOL,
            "stage_order": ["draft", "assembler"],
            "draft_request_schema_version": "1.0",
            "assembler_request_schema_version": "1.0",
            "draft_dto": "content-only-v1",
            "first_attempt_semantics": "single-draft-no-regeneration-v1",
            "capability_projection": "task-neutral-content-only-v1",
        }
        if pipeline != expected_pipeline:
            raise EvaluationError("executor_pipeline must exactly bind blind-draft-assembler-v1")
        if config.get("dataset_role") != "development":
            raise EvaluationError("schema 1.7 blind pipeline is development-only")
    elif config["schema_version"] == "1.8":
        pipeline = require_exact_object(
            config.get("executor_pipeline"),
            INVENTORY_PIPELINE_KEYS,
            "executor_pipeline",
        )
        expected_pipeline = {
            "protocol": INVENTORY_PIPELINE_PROTOCOL,
            "stage_order": ["inventory", "assembler"],
            "inventory_request_schema_version": "1.0",
            "inventory_result_schema_version": "1.0",
            "assembler_request_schema_version": "2.0",
            "assembler_result_schema_version": "1.0",
            "final_result_schema_version": "1.3",
            "assembly_manifest": "complete-source-partition-v1",
            "materialization": "deterministic-claim-v1",
            "first_attempt_semantics": "single-inventory-no-regeneration-v2",
            "capability_projection": "task-neutral-content-only-v1",
        }
        if pipeline != expected_pipeline:
            raise EvaluationError("executor_pipeline must exactly bind blind-inventory-assembler-v2")
        if config.get("dataset_role") != "development":
            raise EvaluationError("schema 1.8 inventory pipeline is development-only")
    elif "executor_pipeline" in config:
        raise EvaluationError("executor_pipeline requires schema 1.7 or 1.8")
    owner_registry: set[str] | None = None
    kind_registry: dict[str, str] | None = None
    source_kind: str | None = None
    if owner_bound:
        case_contract_keys = {"source_kind", "schema_version", "obligations", "owner_registry"}
        if kind_bound:
            case_contract_keys.add("kind_registry")
        case_contract = require_exact_object(
            config["case_contract"],
            case_contract_keys,
            "case_contract",
        )
        source_kind = case_contract["source_kind"]
        if source_kind not in {"contract", "catalog"}:
            raise EvaluationError("case_contract.source_kind must be contract or catalog")
        expected_contract_schema = (
            ("2.2" if work_unit_bound else ("2.1" if kind_bound else "2.0"))
            if source_kind == "contract"
            else ("1.3" if work_unit_bound else ("1.2" if kind_bound else "1.1"))
        )
        if case_contract["schema_version"] != expected_contract_schema:
            raise EvaluationError(
                f"case_contract.schema_version must be {expected_contract_schema} for {source_kind} sources"
            )
        expected_obligation_protocol = (
            "work-unit-facets-v3"
            if work_unit_bound
            else ("owner-kind-v2" if kind_bound else "owner-bound-v1")
        )
        if case_contract["obligations"] != expected_obligation_protocol:
            raise EvaluationError(
                f"case_contract.obligations must be {expected_obligation_protocol}"
            )
        if case_contract["owner_registry"] != "governance/capability-contracts.json":
            raise EvaluationError(
                "case_contract.owner_registry must be governance/capability-contracts.json"
            )
        try:
            registry_path = contained_path(
                ROOT,
                case_contract["owner_registry"],
                label="case_contract.owner_registry",
                require_relative=True,
                reject_symlinks=True,
            )
            raw_registry = json.loads(registry_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, PathContractError) as exc:
            raise EvaluationError(f"case_contract.owner_registry is invalid: {exc}") from exc
        owner_registry = set(owner_vocabulary_from_registry(raw_registry, "case_contract.owner_registry"))
        if kind_bound:
            if case_contract["kind_registry"] != "governance/claim-kinds.json":
                raise EvaluationError(
                    "case_contract.kind_registry must be governance/claim-kinds.json"
                )
            try:
                kind_registry_path = contained_path(
                    ROOT,
                    case_contract["kind_registry"],
                    label="case_contract.kind_registry",
                    require_relative=True,
                    reject_symlinks=True,
                )
                raw_kind_registry = json.loads(kind_registry_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, PathContractError) as exc:
                raise EvaluationError(f"case_contract.kind_registry is invalid: {exc}") from exc
            kind_registry = {
                item["id"]: item["owner"]
                for item in kind_vocabulary_from_registry(
                    raw_kind_registry,
                    "case_contract.kind_registry",
                    allowed_owners=owner_registry,
                )
            }
        expected_role = "development" if source_kind == "contract" else "acceptance"
        if config["dataset_role"] != expected_role:
            raise EvaluationError(
                f"case_contract source_kind {source_kind} requires dataset_role {expected_role}"
            )
        if expected_role == "acceptance":
            if "evaluator_identity" in config:
                raise EvaluationError(
                    "evaluator_identity is reserved for schema 1.6 development configs"
                )
            if "release_evaluators" not in config:
                raise EvaluationError(
                    f"schema {config['schema_version']} acceptance config requires release_evaluators"
                )
            config["release_evaluators"] = validate_release_evaluators(
                config["release_evaluators"],
                expected_result_schema_version=(
                    "1.3" if work_unit_bound else ("1.2" if kind_bound else "1.1")
                ),
            )
        else:
            if "release_evaluators" in config:
                raise EvaluationError("release_evaluators is reserved for owner-bound acceptance config")
            if "evaluator_identity" in config:
                if not work_unit_bound:
                    raise EvaluationError(
                        "evaluator_identity is reserved for schema 1.6 development configs"
                    )
                config["evaluator_identity"] = validate_evaluator_identity_contract(
                    config["evaluator_identity"],
                    contract_label="evaluator_identity",
                    expected_result_schema_version="1.3",
                )
                if config["schema_version"] == "1.7" and "draft" not in config["evaluator_identity"]:
                    raise EvaluationError(
                        "schema 1.7 evaluator_identity requires draft, assembler, and grader"
                    )
                if config["schema_version"] == "1.8" and "inventory" not in config["evaluator_identity"]:
                    raise EvaluationError(
                        "schema 1.8 evaluator_identity requires inventory, assembler, and grader"
                    )
            elif config["schema_version"] in {"1.7", "1.8"}:
                raise EvaluationError(f"schema {config['schema_version']} requires evaluator_identity")
    elif "case_contract" in config:
        raise EvaluationError("paired evaluation config case_contract requires schema 1.4, 1.5, or 1.6")
    elif "release_evaluators" in config:
        raise EvaluationError("paired evaluation config release_evaluators requires owner-bound acceptance")
    elif "evaluator_identity" in config:
        raise EvaluationError("evaluator_identity is reserved for schema 1.6 development configs")
    if not isinstance(config["evaluation_contract"], str) or not config["evaluation_contract"].strip():
        raise EvaluationError("paired evaluation config evaluation_contract must be non-empty")
    if not isinstance(config["default_trials"], int) or isinstance(config["default_trials"], bool) or config["default_trials"] < 3:
        raise EvaluationError("paired evaluation default_trials must be at least three")
    if config["metrics"] != list(CONTRACT_METRICS):
        raise EvaluationError(f"paired evaluation metrics must exactly match {list(CONTRACT_METRICS)}")
    thresholds = require_exact_object(
        config.get("release_thresholds", dict(DEFAULT_RELEASE_THRESHOLDS)),
        RELEASE_THRESHOLD_KEYS,
        "release_thresholds",
    )
    config["release_thresholds"] = thresholds
    for key, item in thresholds.items():
        require_finite_nonnegative(item, f"release_thresholds.{key}")
    if thresholds["minimum_candidate_pass_rate"] > 1:
        raise EvaluationError("release_thresholds.minimum_candidate_pass_rate must not exceed 1")
    for key in (
        "minimum_candidate_requirement_fidelity",
        "minimum_candidate_ordinary_defect_retention",
        "minimum_requirement_fidelity_delta",
        "minimum_ordinary_defect_retention_delta",
    ):
        if thresholds[key] > 4:
            raise EvaluationError(f"release_thresholds.{key} must not exceed 4")
    if not isinstance(config["pairs"], list):
        raise EvaluationError("paired evaluation config pairs must be a list")
    if not config["pairs"]:
        raise EvaluationError("paired evaluation config pairs must not be empty")
    base_pair_keys = {"id", "capabilities", "deterministic_oracle"}
    seen_pair_ids: set[str] = set()
    seen_contracts: set[str] = set()
    seen_contract_ids: set[str] = set()
    categories: list[str] = []
    category_counts: dict[str, int] = {}
    eval_root = ROOT / "evals"
    catalog_cache: dict[str, dict[str, dict[str, Any]]] = {}
    for index, pair in enumerate(config["pairs"]):
        catalog_pair = isinstance(pair, dict) and (
            (owner_bound and source_kind == "catalog")
            or (
                config["schema_version"] == "1.3"
                and ("case_source" in pair or "case_id" in pair)
            )
        )
        pair_keys = set(base_pair_keys)
        if categorized:
            pair_keys.add("category")
        if explicit_context:
            pair_keys.add("capability_context")
        if catalog_pair:
            pair_keys |= {"case_source", "case_id"}
        else:
            pair_keys.add("fixture")
            if categorized:
                pair_keys.add("contract")
        checked = require_exact_object(pair, pair_keys, f"pairs[{index}]")
        try:
            pair_id = safe_path_component(checked["id"], label=f"pairs[{index}].id")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        if pair_id in seen_pair_ids:
            raise EvaluationError(f"pairs[{index}].id must be unique")
        seen_pair_ids.add(pair_id)
        if categorized:
            try:
                category = safe_path_component(checked["category"], label=f"pairs[{index}].category")
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
            if category not in category_counts:
                categories.append(category)
                category_counts[category] = 0
            category_counts[category] += 1
        if catalog_pair:
            for key in ("case_source", "case_id"):
                if not isinstance(checked[key], str) or not checked[key].strip():
                    raise EvaluationError(f"pairs[{index}].{key} must be a non-empty string")
            if not checked["case_source"].startswith("cases/"):
                raise EvaluationError(f"pairs[{index}].case_source must be an owned cases/ path")
        elif not isinstance(checked["fixture"], str) or not checked["fixture"].strip():
            raise EvaluationError(f"pairs[{index}].fixture must be a non-empty string")
        require_text_list(checked["capabilities"], f"pairs[{index}].capabilities")
        if not checked["capabilities"]:
            raise EvaluationError(f"pairs[{index}].capabilities must not be empty")
        if len(checked["capabilities"]) != len(set(checked["capabilities"])):
            raise EvaluationError(f"pairs[{index}].capabilities must be unique")
        safe_capabilities: list[str] = []
        for capability_index, capability in enumerate(checked["capabilities"]):
            try:
                safe_capabilities.append(
                    safe_path_component(capability, label=f"pairs[{index}].capabilities[{capability_index}]")
                )
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
        if explicit_context:
            capability_context = checked["capability_context"]
            if not isinstance(capability_context, dict):
                raise EvaluationError(f"pairs[{index}].capability_context must be an object")
            if set(capability_context) != set(safe_capabilities):
                raise EvaluationError(
                    f"pairs[{index}].capability_context keys must exactly match capabilities"
                )
            for capability in safe_capabilities:
                references = capability_context[capability]
                if not isinstance(references, list) or any(
                    not isinstance(reference, str) or not reference.strip() for reference in references
                ):
                    raise EvaluationError(
                        f"pairs[{index}].capability_context.{capability} must be a list of non-empty strings"
                    )
                if len(references) != len(set(references)):
                    raise EvaluationError(
                        f"pairs[{index}].capability_context.{capability} references must be unique"
                    )
                capability_root = ROOT / "skills" / capability
                for reference_index, reference in enumerate(references):
                    if not reference.startswith("references/"):
                        raise EvaluationError(
                            f"pairs[{index}].capability_context.{capability}[{reference_index}] "
                            "must be an owned references/ path"
                        )
                    try:
                        reference_path = contained_path(
                            capability_root,
                            reference,
                            label=(
                                f"pairs[{index}].capability_context.{capability}[{reference_index}]"
                            ),
                            require_relative=True,
                            reject_symlinks=True,
                        )
                    except PathContractError as exc:
                        raise EvaluationError(str(exc)) from exc
                    if not reference_path.is_file():
                        raise EvaluationError(
                            f"pairs[{index}].capability_context.{capability}[{reference_index}] "
                            "must resolve to an owned capability reference"
                        )
                    if reference_path.stat().st_size > MAX_INPUT_BYTES:
                        raise EvaluationError(
                            f"pairs[{index}].capability_context.{capability}[{reference_index}] "
                            f"exceeds {MAX_INPUT_BYTES} bytes"
                        )
        if not isinstance(checked["deterministic_oracle"], str) or not checked["deterministic_oracle"].strip():
            raise EvaluationError(f"pairs[{index}].deterministic_oracle must be a non-empty string")
        if catalog_pair:
            case_source = checked["case_source"]
            if case_source not in catalog_cache:
                try:
                    catalog_path = contained_path(
                        eval_root,
                        case_source,
                        label=f"pairs[{index}].case_source",
                        require_relative=True,
                        reject_symlinks=True,
                    )
                    if not catalog_path.is_file():
                        raise EvaluationError(f"pairs[{index}].case_source must resolve to an eval case catalog")
                    if catalog_path.stat().st_size > MAX_INPUT_BYTES:
                        raise EvaluationError(f"pairs[{index}].case_source exceeds {MAX_INPUT_BYTES} bytes")
                    raw_catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, json.JSONDecodeError, PathContractError) as exc:
                    raise EvaluationError(f"pairs[{index}].case_source is invalid: {exc}") from exc
                catalog = require_exact_object(
                    raw_catalog,
                    {"schema_version", "cases"},
                    f"pairs[{index}].case_source",
                )
                expected_catalog_schema = (
                    "1.3"
                    if work_unit_bound
                    else ("1.2" if kind_bound else ("1.1" if owner_bound else "1.0"))
                )
                if catalog["schema_version"] != expected_catalog_schema or not isinstance(catalog["cases"], list) or not catalog["cases"]:
                    raise EvaluationError(
                        f"pairs[{index}].case_source must use schema {expected_catalog_schema} with a non-empty cases list"
                    )
                indexed_cases: dict[str, dict[str, Any]] = {}
                for case_index, case_value in enumerate(catalog["cases"]):
                    case = validate_catalog_case(
                        case_value,
                        f"pairs[{index}].case_source.cases[{case_index}]",
                        owner_bound=owner_bound,
                        allowed_owners=owner_registry,
                        allowed_kinds=kind_registry,
                        kind_bound=kind_bound,
                        work_unit_bound=work_unit_bound,
                    )
                    if case["id"] in indexed_cases:
                        raise EvaluationError(
                            f"pairs[{index}].case_source contains duplicate case id {case['id']}"
                        )
                    indexed_cases[case["id"]] = case
                catalog_cache[case_source] = indexed_cases
            selected_case = catalog_cache[case_source].get(checked["case_id"])
            if selected_case is None:
                raise EvaluationError(
                    f"pairs[{index}].case_id {checked['case_id']!r} is missing from {case_source}"
                )
            contract_identity = f"{case_source}#{checked['case_id']}"
            if contract_identity in seen_contracts:
                raise EvaluationError(f"pairs[{index}] catalog case selection must be unique")
            seen_contracts.add(contract_identity)
            if selected_case["id"] in seen_contract_ids:
                raise EvaluationError(f"pairs[{index}].case id must be unique")
            seen_contract_ids.add(selected_case["id"])
            if owner_bound:
                require_supplied_obligation_owners(
                    selected_case,
                    safe_capabilities,
                    f"pairs[{index}] catalog case",
                )
        else:
            try:
                fixture = contained_path(
                    eval_root,
                    checked["fixture"],
                    label=f"pairs[{index}].fixture",
                    require_relative=True,
                    reject_symlinks=True,
                )
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
            if not fixture.is_file():
                raise EvaluationError(f"pairs[{index}].fixture must resolve to an eval fixture")
            if fixture.stat().st_size > MAX_FIXTURE_BYTES:
                raise EvaluationError(f"pairs[{index}].fixture exceeds {MAX_FIXTURE_BYTES} bytes")
        if categorized and not catalog_pair:
            if not isinstance(checked["contract"], str) or not checked["contract"].strip():
                raise EvaluationError(f"pairs[{index}].contract must be a non-empty string")
            if checked["contract"] in seen_contracts:
                raise EvaluationError(f"pairs[{index}].contract must be unique")
            seen_contracts.add(checked["contract"])
            try:
                contract_path = contained_path(
                    eval_root,
                    checked["contract"],
                    label=f"pairs[{index}].contract",
                    require_relative=True,
                    reject_symlinks=True,
                )
                if not contract_path.is_file():
                    raise EvaluationError(f"pairs[{index}].contract must resolve to an eval contract")
                if contract_path.stat().st_size > MAX_INPUT_BYTES:
                    raise EvaluationError(f"pairs[{index}].contract exceeds {MAX_INPUT_BYTES} bytes")
                contract = json.loads(contract_path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError, PathContractError) as exc:
                raise EvaluationError(f"pairs[{index}].contract is invalid: {exc}") from exc
            validated_contract = validate_case_contract(
                contract,
                checked,
                f"pairs[{index}].contract",
                owner_bound=owner_bound,
                allowed_owners=owner_registry,
                allowed_kinds=kind_registry,
                kind_bound=kind_bound,
                work_unit_bound=work_unit_bound,
            )
            if validated_contract["id"] in seen_contract_ids:
                raise EvaluationError(f"pairs[{index}].contract id must be unique")
            seen_contract_ids.add(validated_contract["id"])
            if owner_bound:
                require_supplied_obligation_owners(
                    validated_contract,
                    safe_capabilities,
                    f"pairs[{index}] contract",
                )
    if "release_plan" in config:
        release_keys = {"pair_ids", "trials_per_pair"}
        if categorized:
            release_keys |= {"category_ids", "minimum_cases_per_category"}
        release_plan = require_exact_object(
            config["release_plan"],
            release_keys,
            "release_plan",
        )
        require_text_list(release_plan["pair_ids"], "release_plan.pair_ids")
        if release_plan["pair_ids"] != [pair["id"] for pair in config["pairs"]]:
            raise EvaluationError("release_plan.pair_ids must exactly match configured pairs in order")
        if (
            not isinstance(release_plan["trials_per_pair"], int)
            or isinstance(release_plan["trials_per_pair"], bool)
            or release_plan["trials_per_pair"] < 3
        ):
            raise EvaluationError("release_plan.trials_per_pair must be at least three")
        if categorized:
            require_text_list(release_plan["category_ids"], "release_plan.category_ids")
            if release_plan["category_ids"] != categories:
                raise EvaluationError("release_plan.category_ids must exactly match configured categories in order")
            minimum_cases = release_plan["minimum_cases_per_category"]
            if (
                not isinstance(minimum_cases, int)
                or isinstance(minimum_cases, bool)
                or minimum_cases < MIN_CASES_PER_CATEGORY
            ):
                raise EvaluationError(
                    f"release_plan.minimum_cases_per_category must be at least {MIN_CASES_PER_CATEGORY}"
                )
            underpopulated = {
                category: count for category, count in category_counts.items() if count < minimum_cases
            }
            if underpopulated:
                raise EvaluationError(f"release_plan categories are underpopulated: {underpopulated}")
    return config


def evaluation_input_snapshot(
    config: dict[str, Any],
    expected_commit: str | None,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Read every model-consumed source once, from immutable Git blobs for release."""
    cache: dict[str, str] = {}
    entries: list[dict[str, str]] = []

    def read_text(relative: str) -> str:
        if relative in cache:
            return cache[relative]
        if expected_commit is not None:
            result = subprocess.run(
                ["git", "show", f"{expected_commit}:{relative}"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            if result.returncode != 0:
                raise EvaluationError(f"release input is missing from expected commit: {relative}")
            raw = result.stdout
        else:
            try:
                path = contained_path(
                    ROOT,
                    relative,
                    label="evaluation input",
                    require_relative=True,
                    reject_symlinks=True,
                )
                raw = path.read_bytes()
            except (OSError, PathContractError) as exc:
                raise EvaluationError(f"cannot snapshot evaluation input {relative}: {exc}") from exc
        if len(raw) > MAX_INPUT_BYTES:
            raise EvaluationError(f"evaluation input exceeds {MAX_INPUT_BYTES} bytes: {relative}")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise EvaluationError(f"evaluation input must be UTF-8: {relative}") from exc
        cache[relative] = text
        entries.append({"path": relative, "sha256": "sha256:" + hashlib.sha256(raw).hexdigest()})
        return text

    owner_bound = config["schema_version"] in {"1.4", "1.5", "1.6", "1.7", "1.8"}
    kind_bound = config["schema_version"] in {"1.5", "1.6", "1.7", "1.8"}
    work_unit_bound = config["schema_version"] in {"1.6", "1.7", "1.8"}
    if owner_bound:
        registry_relative = config["case_contract"]["owner_registry"]
        try:
            claim_owner_vocabulary = owner_vocabulary_from_registry(
                json.loads(read_text(registry_relative)),
                "case_contract.owner_registry snapshot",
            )
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"case_contract.owner_registry snapshot is invalid JSON: {exc}") from exc
    else:
        claim_owner_vocabulary = list(LEGACY_CLAIM_OWNER_VOCABULARY)
    if kind_bound:
        kind_registry_relative = config["case_contract"]["kind_registry"]
        try:
            claim_kind_vocabulary = kind_vocabulary_from_registry(
                json.loads(read_text(kind_registry_relative)),
                "case_contract.kind_registry snapshot",
                allowed_owners=set(claim_owner_vocabulary),
            )
        except json.JSONDecodeError as exc:
            raise EvaluationError(
                f"case_contract.kind_registry snapshot is invalid JSON: {exc}"
            ) from exc
    else:
        claim_kind_vocabulary = [dict(item) for item in LEGACY_CLAIM_KIND_VOCABULARY]
    allowed_owners = set(claim_owner_vocabulary) if owner_bound else None
    allowed_kinds = (
        {item["id"]: item["owner"] for item in claim_kind_vocabulary}
        if kind_bound
        else None
    )
    owner_vocabulary_bytes = json.dumps(
        claim_owner_vocabulary,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    kind_vocabulary_bytes = json.dumps(
        claim_kind_vocabulary,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    inputs: dict[str, dict[str, Any]] = {}
    assignments: list[dict[str, Any]] = []
    for pair in config["pairs"]:
        contract: dict[str, Any] | None = None
        if "case_source" in pair:
            case_source_relative = f"evals/{pair['case_source']}"
            try:
                catalog = json.loads(read_text(case_source_relative))
                selected = next(
                    case for case in catalog["cases"] if case.get("id") == pair["case_id"]
                )
                contract = validate_catalog_case(
                    selected,
                    f"{pair['id']} catalog case",
                    owner_bound=owner_bound,
                    allowed_owners=allowed_owners,
                    allowed_kinds=allowed_kinds,
                    kind_bound=kind_bound,
                    work_unit_bound=work_unit_bound,
                )
            except (json.JSONDecodeError, KeyError, StopIteration, TypeError) as exc:
                raise EvaluationError(f"{pair['id']} catalog case is invalid: {exc}") from exc
            fixture = contract["fixture"]
        else:
            fixture_relative = f"evals/{pair['fixture']}"
            fixture = read_text(fixture_relative)
            if len(fixture.encode("utf-8")) > MAX_FIXTURE_BYTES:
                raise EvaluationError(f"{pair['id']} fixture exceeds {MAX_FIXTURE_BYTES} bytes")
        capability_sources: dict[str, str] = {}
        capability_assignments: list[dict[str, Any]] = []
        for capability in pair["capabilities"]:
            try:
                safe_capability = safe_path_component(capability, label="evaluation capability")
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
            skill_relative = f"skills/{safe_capability}/SKILL.md"
            skill_source = read_text(skill_relative)
            source_parts = [f"<source path={json.dumps(skill_relative)}>\n{skill_source}\n</source>"]
            source_paths = [skill_relative]
            seen_references: set[str] = set()
            referenced_paths = (
                pair["capability_context"][safe_capability]
                if config["schema_version"] in {"1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}
                else SKILL_REFERENCE_RE.findall(skill_source)
            )
            for referenced in referenced_paths:
                normalized = posixpath.normpath(f"skills/{safe_capability}/{referenced}")
                if (
                    normalized.startswith("/")
                    or normalized == "skills"
                    or not normalized.startswith("skills/")
                ):
                    raise EvaluationError(f"{pair['id']} has an unsafe Skill reference: {referenced}")
                if normalized in seen_references:
                    continue
                seen_references.add(normalized)
                referenced_source = read_text(normalized)
                source_parts.append(f"<source path={json.dumps(normalized)}>\n{referenced_source}\n</source>")
                source_paths.append(normalized)
            capability_sources[safe_capability] = "\n\n".join(source_parts)
            capability_assignments.append(
                {
                    "capability": safe_capability,
                    "paths": source_paths,
                    "sha256": "sha256:"
                    + hashlib.sha256(capability_sources[safe_capability].encode("utf-8")).hexdigest(),
                }
            )
        if "contract" in pair:
            contract_text = read_text(f"evals/{pair['contract']}")
            try:
                contract = validate_case_contract(
                    json.loads(contract_text),
                    pair,
                    f"{pair['id']} contract",
                    owner_bound=owner_bound,
                    allowed_owners=allowed_owners,
                    allowed_kinds=allowed_kinds,
                    kind_bound=kind_bound,
                    work_unit_bound=work_unit_bound,
                )
            except json.JSONDecodeError as exc:
                raise EvaluationError(f"{pair['id']} contract is invalid JSON: {exc}") from exc
        combined_input_bytes = (
            len(fixture.encode("utf-8"))
            + (
                len(json.dumps(contract, ensure_ascii=False, sort_keys=True).encode("utf-8"))
                if contract is not None
                else 0
            )
            + sum(len(source.encode("utf-8")) for source in capability_sources.values())
            + len(owner_vocabulary_bytes)
            + len(kind_vocabulary_bytes)
        )
        if combined_input_bytes > MAX_PAIR_INPUT_BYTES:
            raise EvaluationError(
                f"{pair['id']} combined input exceeds {MAX_PAIR_INPUT_BYTES} bytes: "
                f"observed {combined_input_bytes}"
            )
        inputs[pair["id"]] = {
            "fixture": fixture,
            "contract": contract,
            "capability_sources": capability_sources,
            "claim_owner_vocabulary": claim_owner_vocabulary,
            "claim_kind_vocabulary": claim_kind_vocabulary,
            "kind_alignment_enforced": kind_bound,
        }
        assignments.append(
            {
                "pair_id": pair["id"],
                "fixture_sha256": "sha256:" + hashlib.sha256(fixture.encode("utf-8")).hexdigest(),
                "contract_sha256": (
                    "sha256:"
                    + hashlib.sha256(
                        json.dumps(contract, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
                            "utf-8"
                        )
                    ).hexdigest()
                    if contract is not None
                    else None
                ),
                "claim_owner_vocabulary_sha256": "sha256:"
                + hashlib.sha256(owner_vocabulary_bytes).hexdigest(),
                "claim_kind_vocabulary_sha256": "sha256:"
                + hashlib.sha256(kind_vocabulary_bytes).hexdigest(),
                "kind_alignment_enforced": kind_bound,
                "capabilities": capability_assignments,
            }
        )
    entries.sort(key=lambda item: item["path"])
    canonical_snapshot = json.dumps(
        {
            "entries": entries,
            "assignments": assignments,
            "claim_owner_vocabulary_sha256": "sha256:"
            + hashlib.sha256(owner_vocabulary_bytes).hexdigest(),
            "claim_kind_vocabulary_sha256": "sha256:"
            + hashlib.sha256(kind_vocabulary_bytes).hexdigest(),
            "kind_alignment_enforced": kind_bound,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return inputs, {
        "source": "git-commit" if expected_commit else "worktree-snapshot",
        "commit": expected_commit,
        "entries": entries,
        "assignments": assignments,
        "claim_owner_vocabulary_sha256": "sha256:"
        + hashlib.sha256(owner_vocabulary_bytes).hexdigest(),
        "claim_kind_vocabulary_sha256": "sha256:"
        + hashlib.sha256(kind_vocabulary_bytes).hexdigest(),
        "kind_alignment_enforced": kind_bound,
        "sha256": "sha256:" + hashlib.sha256(canonical_snapshot).hexdigest(),
    }


def validate_claims(
    value: Any,
    allowed_claim_owners: list[str] | tuple[str, ...] | None,
    *,
    claim_kind_vocabulary: list[dict[str, str]] | tuple[dict[str, str], ...] | None = None,
    enforce_kind_alignment: bool = False,
    label: str = "executor claims",
) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or len(value) > MAX_CLAIMS:
        raise EvaluationError(f"{label} must contain 1..{MAX_CLAIMS} items")
    if allowed_claim_owners is not None:
        if (
            not allowed_claim_owners
            or len(allowed_claim_owners) != len(set(allowed_claim_owners))
            or any(not isinstance(owner, str) or not owner for owner in allowed_claim_owners)
        ):
            raise EvaluationError("claim owner vocabulary must be non-empty, textual, and unique")
        allowed = set(allowed_claim_owners)
    else:
        allowed = None
    if claim_kind_vocabulary is not None:
        if not claim_kind_vocabulary:
            raise EvaluationError("claim kind vocabulary must be non-empty")
        kind_owners: dict[str, str] = {}
        for index, item in enumerate(claim_kind_vocabulary):
            entry = require_exact_object(
                item,
                {"id", "owner"},
                f"claim kind vocabulary[{index}]",
            )
            kind = entry["id"]
            owner = entry["owner"]
            if (
                not isinstance(kind, str)
                or KIND_ID_RE.fullmatch(kind) is None
                or not isinstance(owner, str)
                or not owner
            ):
                raise EvaluationError("claim kind vocabulary entries must contain valid id/owner values")
            if kind in kind_owners:
                raise EvaluationError("claim kind vocabulary ids must be globally unique")
            kind_owners[kind] = owner
    else:
        kind_owners = {}
    claims: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(value):
        claim = require_exact_object(item, CLAIM_KEYS, f"{label}[{index}]")
        claim_id = claim["claim_id"]
        if (
            not isinstance(claim_id, str)
            or len(claim_id) > 128
            or CLAIM_ID_RE.fullmatch(claim_id) is None
        ):
            raise EvaluationError(f"{label}[{index}].claim_id must be a bounded CL-* id")
        if claim_id in seen_ids:
            raise EvaluationError(f"{label} claim_id values must be unique")
        seen_ids.add(claim_id)
        owner = claim["owner"]
        if not isinstance(owner, str) or not owner or len(owner) > 128:
            raise EvaluationError(f"{label}[{index}].owner must be a bounded non-empty string")
        if allowed is not None and owner not in allowed:
            raise EvaluationError(f"{label}[{index}].owner is absent from the allowed claim-owner vocabulary")
        kind = claim["kind"]
        if not isinstance(kind, str) or KIND_ID_RE.fullmatch(kind) is None:
            raise EvaluationError(f"{label}[{index}].kind is invalid")
        if claim_kind_vocabulary is not None and kind not in kind_owners:
            raise EvaluationError(
                f"{label}[{index}].kind is absent from the allowed claim-kind vocabulary"
            )
        if enforce_kind_alignment and kind_owners.get(kind) != owner:
            raise EvaluationError(
                f"{label}[{index}] claim owner and kind registry owner do not match"
            )
        for key in ("action", "protected_behavior", "oracle_or_evidence"):
            field = claim[key]
            if (
                not isinstance(field, str)
                or not field.strip()
                or len(field) > MAX_CONTRACT_ITEM_CHARACTERS
            ):
                raise EvaluationError(
                    f"{label}[{index}].{key} must be 1..{MAX_CONTRACT_ITEM_CHARACTERS} characters"
                )
        if claim["status"] not in {"planned", "verified", "blocked", "not-run"}:
            raise EvaluationError(f"{label}[{index}].status is invalid")
        limitation = claim["limitation"]
        if limitation is not None and (
            not isinstance(limitation, str)
            or not limitation.strip()
            or len(limitation) > MAX_CONTRACT_ITEM_CHARACTERS
        ):
            raise EvaluationError(
                f"{label}[{index}].limitation must be null or 1..{MAX_CONTRACT_ITEM_CHARACTERS} characters"
            )
        claims.append(claim)
    return claims


def normalize_semantic_text(value: str) -> str:
    """Normalize presentation-only differences without erasing technical punctuation."""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(
        character
        for character in normalized
        if unicodedata.category(character) != "Cf"
    )
    normalized = " ".join(normalized.split()).casefold()
    # Sentence-ending punctuation is presentation, not independent support.
    # Preserve all interior punctuation because it may carry technical meaning.
    return re.sub(r"[.!?。！？]+$", "", normalized)


def claim_semantic_fingerprint(claim: dict[str, Any]) -> str:
    """Bind critical-claim exclusivity to normalized content, not caller-chosen IDs."""

    semantic = {
        key: (
            normalize_semantic_text(claim[key])
            if isinstance(claim.get(key), str)
            else claim.get(key)
        )
        for key in (
            "action",
            "protected_behavior",
            "oracle_or_evidence",
            "status",
            "limitation",
        )
    }
    return canonical_json_sha256(semantic)


def validate_inventory_result(
    value: Any,
    case_id: str,
) -> dict[str, Any]:
    """Validate the owner-free, atomic first-stage inventory."""
    result = require_exact_object(value, INVENTORY_RESULT_KEYS, "inventory result")
    if result["schema_version"] != "1.0" or result["case_id"] != case_id or result["attempt"] != 1:
        raise EvaluationError("inventory result must preserve schema 1.0, case_id, and attempt 1")
    if result["claimed_outcome"] not in {"completed", "blocked", "needs-user-decision"}:
        raise EvaluationError("inventory result claimed_outcome is invalid")
    interactions = require_exact_object(result["interactions"], INTERACTION_KEYS, "inventory interactions")
    for key, item in interactions.items():
        require_nonnegative_integer(item, f"inventory interactions.{key}")
    items = result["inventory_items"]
    if not isinstance(items, list) or not (1 <= len(items) <= MAX_CLAIMS):
        raise EvaluationError("inventory_items must contain 1..100 atomic items")
    seen_ids: set[str] = set()
    for index, raw in enumerate(items):
        item = require_exact_object(raw, INVENTORY_ITEM_KEYS, f"inventory_items[{index}]")
        item_id = item["item_id"]
        if not isinstance(item_id, str) or INVENTORY_ID_RE.fullmatch(item_id) is None:
            raise EvaluationError(f"inventory_items[{index}].item_id must be an IT-* id")
        if item_id in seen_ids:
            raise EvaluationError("inventory item ids must be unique")
        seen_ids.add(item_id)
        if item["evidence_family"] not in CLAIM_KIND_FAMILIES:
            raise EvaluationError(f"inventory_items[{index}].evidence_family is invalid")
        for key in ("action", "protected_behavior", "oracle_or_evidence"):
            field = item[key]
            if not isinstance(field, str) or not field.strip() or len(field) > MAX_CONTRACT_ITEM_CHARACTERS:
                raise EvaluationError(f"inventory_items[{index}].{key} must be bounded non-empty text")
        if item["status"] not in {"planned", "verified", "blocked", "not-run"}:
            raise EvaluationError(f"inventory_items[{index}].status is invalid")
        limitation = item["limitation"]
        if item["status"] == "verified":
            if limitation is not None:
                raise EvaluationError("verified inventory items must not carry a limitation")
        elif not isinstance(limitation, str) or not limitation.strip():
            raise EvaluationError("non-verified inventory items require an explicit limitation")
        refs = item["evidence_refs"]
        if not isinstance(refs, list):
            raise EvaluationError(f"inventory_items[{index}].evidence_refs must be a list")
        for ref_index, raw_ref in enumerate(refs):
            ref = require_exact_object(
                raw_ref,
                EVIDENCE_REF_KEYS,
                f"inventory_items[{index}].evidence_refs[{ref_index}]",
            )
            if ref["source"] not in {"fixture", "task_prompt"}:
                raise EvaluationError("inventory evidence refs may only cite fixture or task_prompt")
            if not isinstance(ref["quote"], str) or len(ref["quote"]) < 8 or len(ref["quote"]) > 500:
                raise EvaluationError("inventory evidence refs require a bounded exact quote")
        if item["status"] == "verified" and not refs:
            raise EvaluationError("verified inventory items require fixture or task evidence")
    return result


def validate_inventory_evidence_refs(
    inventory: dict[str, Any],
    *,
    fixture: str,
    task_prompt: str,
) -> None:
    sources = {"fixture": fixture, "task_prompt": task_prompt}
    for index, item in enumerate(inventory["inventory_items"]):
        for ref_index, ref in enumerate(item["evidence_refs"]):
            if sources[ref["source"]].count(ref["quote"]) != 1:
                raise EvaluationError(
                    f"inventory_items[{index}].evidence_refs[{ref_index}] quote must occur exactly once"
                )
            source = sources[ref["source"]]
            quote = ref["quote"]
            start = source.index(quote)
            end = start + len(quote)
            if (
                (start > 0 and source[start - 1].isalnum() and quote[0].isalnum())
                or (end < len(source) and quote[-1].isalnum() and source[end].isalnum())
            ):
                raise EvaluationError(
                    f"inventory_items[{index}].evidence_refs[{ref_index}] quote must not cut through a word"
                )


def validate_assembly_manifest(
    value: Any,
    case_id: str,
) -> dict[str, Any]:
    manifest = require_exact_object(value, ASSEMBLY_RESULT_KEYS, "assembly manifest")
    if manifest["schema_version"] != "1.0" or manifest["case_id"] != case_id or manifest["attempt"] != 1:
        raise EvaluationError("assembly manifest must preserve schema 1.0, case_id, and attempt 1")
    supplemental_items = manifest["supplemental_items"]
    claim_assemblies = manifest["claim_assemblies"]
    dispositions = manifest["dispositions"]
    if not isinstance(supplemental_items, list) or len(supplemental_items) > MAX_CLAIMS:
        raise EvaluationError("supplemental_items must contain 0..100 items")
    if not isinstance(claim_assemblies, list) or not (1 <= len(claim_assemblies) <= MAX_CLAIMS):
        raise EvaluationError("claim_assemblies must contain 1..100 items")
    if not isinstance(dispositions, list) or len(dispositions) > MAX_CLAIMS:
        raise EvaluationError("dispositions must contain 0..100 items")
    seen_supplement_ids: set[str] = set()
    for index, raw in enumerate(supplemental_items):
        item = require_exact_object(raw, INVENTORY_ITEM_KEYS, f"supplemental_items[{index}]")
        if not isinstance(item["item_id"], str) or SUPPLEMENT_ID_RE.fullmatch(item["item_id"]) is None:
            raise EvaluationError("supplemental item ids must use SP-*")
        if item["item_id"] in seen_supplement_ids:
            raise EvaluationError("supplemental item ids must be unique")
        seen_supplement_ids.add(item["item_id"])
        if item["evidence_family"] not in CLAIM_KIND_FAMILIES:
            raise EvaluationError("supplemental item evidence_family is invalid")
        if item["status"] not in {"planned", "not-run"}:
            raise EvaluationError("supplemental items may only be planned or not-run")
        if not isinstance(item["limitation"], str) or not item["limitation"].strip():
            raise EvaluationError("supplemental items require an explicit limitation")
        if item["evidence_refs"] != []:
            raise EvaluationError("supplemental items cannot add first-stage evidence refs")
        for key in ("action", "protected_behavior", "oracle_or_evidence"):
            if not isinstance(item[key], str) or not item[key].strip():
                raise EvaluationError(f"supplemental_items[{index}].{key} must be non-empty")
    for index, raw in enumerate(claim_assemblies):
        assembly = require_exact_object(raw, CLAIM_ASSEMBLY_KEYS, f"claim_assemblies[{index}]")
        if not isinstance(assembly["claim_id"], str) or CLAIM_ID_RE.fullmatch(assembly["claim_id"]) is None:
            raise EvaluationError("claim assembly ids must use CL-*")
        if not isinstance(assembly["owner"], str) or not assembly["owner"]:
            raise EvaluationError("claim assembly owner must be non-empty")
        if not isinstance(assembly["kind"], str) or KIND_ID_RE.fullmatch(assembly["kind"]) is None:
            raise EvaluationError("claim assembly kind is invalid")
        if not isinstance(assembly["source_item_ids"], list) or not assembly["source_item_ids"]:
            raise EvaluationError("claim assemblies require source_item_ids")
    for index, raw in enumerate(dispositions):
        disposition = require_exact_object(raw, DISPOSITION_KEYS, f"dispositions[{index}]")
        if disposition["disposition"] != "duplicate":
            raise EvaluationError("the only permitted inventory disposition is duplicate")
        if not isinstance(disposition["rationale"], str) or not disposition["rationale"].strip():
            raise EvaluationError("duplicate dispositions require a rationale")
    return manifest


def materialize_inventory_claims(
    inventory: dict[str, Any],
    manifest: dict[str, Any],
    *,
    claim_owner_vocabulary: list[str],
    claim_kind_vocabulary: list[dict[str, str]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Deterministically construct result 1.3 from a complete atom partition."""
    original = {item["item_id"]: item for item in inventory["inventory_items"]}
    supplemental = {item["item_id"]: item for item in manifest["supplemental_items"]}
    if len(supplemental) != len(manifest["supplemental_items"]):
        raise EvaluationError("supplemental item ids must be unique")
    all_items = {**original, **supplemental}
    if len(all_items) != len(original) + len(supplemental):
        raise EvaluationError("inventory and supplemental item ids must not collide")
    allowed_owners = set(claim_owner_vocabulary)
    kind_owners = {item["id"]: item["owner"] for item in claim_kind_vocabulary}
    consumed: dict[str, str] = {}
    claims: list[dict[str, Any]] = []
    claim_ids: set[str] = set()
    for assembly in manifest["claim_assemblies"]:
        claim_id = assembly["claim_id"]
        if claim_id in claim_ids:
            raise EvaluationError("claim assembly ids must be unique")
        claim_ids.add(claim_id)
        owner, kind = assembly["owner"], assembly["kind"]
        if owner not in allowed_owners or kind_owners.get(kind) != owner:
            raise EvaluationError("claim assembly owner/kind is absent or misaligned")
        source_ids = assembly["source_item_ids"]
        if len(source_ids) != len(set(source_ids)):
            raise EvaluationError("a claim assembly may not repeat an item")
        try:
            sources = [all_items[item_id] for item_id in source_ids]
        except KeyError as exc:
            raise EvaluationError(f"claim assembly references unknown item: {exc.args[0]}") from exc
        for item_id in source_ids:
            if item_id in consumed:
                raise EvaluationError("each inventory or supplemental item must be consumed at most once")
            consumed[item_id] = claim_id
        families = {item["evidence_family"] for item in sources}
        statuses = {item["status"] for item in sources}
        if families != {kind.rsplit(".", 1)[-1]}:
            raise EvaluationError("claim assembly kind must preserve the source evidence family")
        if len(statuses) != 1:
            raise EvaluationError("claim assembly sources must share one status")
        status = next(iter(statuses))
        if status == "verified" and any(item_id.startswith("SP-") for item_id in source_ids):
            raise EvaluationError("supplemental items cannot materialize a verified claim")
        limitations = [item["limitation"] for item in sources if item["limitation"] is not None]
        claims.append({
            "claim_id": claim_id,
            "owner": owner,
            "kind": kind,
            "action": "\n".join(item["action"] for item in sources),
            "protected_behavior": "\n".join(item["protected_behavior"] for item in sources),
            "oracle_or_evidence": "\n".join(item["oracle_or_evidence"] for item in sources),
            "status": status,
            "limitation": "\n".join(limitations) if limitations else None,
        })
    disposition_ids: set[str] = set()
    for disposition in manifest["dispositions"]:
        item_id = disposition["item_id"]
        target_id = disposition["consumed_as_item_id"]
        if item_id not in original or target_id not in original or target_id not in consumed:
            raise EvaluationError("duplicate dispositions must reference original inventory and a consumed target")
        if item_id in consumed or item_id in disposition_ids or item_id == target_id:
            raise EvaluationError("duplicate dispositions must account for one otherwise-unconsumed item")
        semantic_keys = (
            "evidence_family", "action", "protected_behavior", "oracle_or_evidence",
            "status", "limitation", "evidence_refs",
        )
        if any(original[item_id][key] != original[target_id][key] for key in semantic_keys):
            raise EvaluationError("duplicate disposition items must be byte-identical in semantic content")
        disposition_ids.add(item_id)
    accounted = set(consumed) | disposition_ids
    if accounted != set(all_items) or disposition_ids & set(supplemental):
        raise EvaluationError("assembly manifest must account for every inventory and supplemental item exactly once")
    result = {
        "schema_version": MODEL_RESULT_SCHEMA_VERSION,
        "case_id": inventory["case_id"],
        "attempt": 1,
        "artifact_root": "artifacts",
        "claimed_outcome": inventory["claimed_outcome"],
        "actions": [claim["action"] for claim in claims],
        "evidence": [claim["oracle_or_evidence"] for claim in claims],
        "claims": claims,
        "interactions": json.loads(json.dumps(inventory["interactions"], sort_keys=True)),
        "usage": {"tokens": None, "elapsed_seconds": None, "cost": None},
    }
    summary = {
        "inventory_items": len(original),
        "consumed_inventory_items": len(set(original) & set(consumed)),
        "duplicate_dispositions": len(disposition_ids),
        "supplemental_items": len(supplemental),
        "consumed_supplemental_items": len(set(supplemental) & set(consumed)),
        "final_claims": len(claims),
        "verified_claims": sum(claim["status"] == "verified" for claim in claims),
        "planned_claims": sum(claim["status"] == "planned" for claim in claims),
        "not_run_claims": sum(claim["status"] == "not-run" for claim in claims),
        "blocked_claims": sum(claim["status"] == "blocked" for claim in claims),
        "all_sources_accounted": True,
    }
    return result, summary


def strict_candidate_pass(grader: dict[str, Any] | None) -> bool:
    return bool(
        grader is not None
        and grader.get("verdict") == "pass"
        and all(grader.get("policy_verdict_checks", {}).values())
    )


def resolve_support_reference(
    value: Any,
    claims_by_id: dict[str, dict[str, Any]],
    label: str,
) -> dict[str, Any]:
    reference = require_exact_object(value, SUPPORT_REF_KEYS, label)
    claim_id = reference["claim_id"]
    field = reference["field"]
    quote = reference["quote"]
    if not isinstance(claim_id, str) or CLAIM_ID_RE.fullmatch(claim_id) is None:
        raise EvaluationError(f"{label}.claim_id is invalid")
    if claim_id not in claims_by_id:
        raise EvaluationError(f"{label}.claim_id references an unknown executor claim")
    if field not in SUPPORT_FIELDS:
        raise EvaluationError(f"{label}.field is not a supported claim evidence field")
    if (
        not isinstance(quote, str)
        or len(quote) < 8
        or len(quote) > 500
        or sum(character.isalnum() for character in quote) < 4
    ):
        raise EvaluationError(f"{label}.quote must be a substantive 8..500 character substring")
    claim = claims_by_id[claim_id]
    source = claim.get(field)
    if not isinstance(source, str) or source.count(quote) != 1:
        match_counts = [
            (
                candidate_field,
                candidate_source,
                candidate_source.count(quote),
            )
            for candidate_field in SUPPORT_FIELD_ORDER
            if isinstance(candidate_source := claim.get(candidate_field), str)
        ]
        if sum(count for _, _, count in match_counts) != 1:
            raise EvaluationError(
                f"{label}.quote must occur exactly once in the referenced claim field"
            )
        field, source, _ = next(
            match for match in match_counts if match[2] == 1
        )
    start = source.index(quote)
    end = start + len(quote)
    if (
        (start > 0 and source[start - 1].isalnum() and quote[0].isalnum())
        or (end < len(source) and quote[-1].isalnum() and source[end].isalnum())
    ):
        raise EvaluationError(f"{label}.quote must not cut through a word")
    return {
        "claim_id": claim_id,
        "field": field,
        "quote": quote,
        "start": start,
        "end": end,
    }


def validate_executor(
    value: Any,
    run_root: Path,
    case_id: str,
    claim_owner_vocabulary: list[str] | tuple[str, ...],
    claim_kind_vocabulary: list[dict[str, str]] | tuple[dict[str, str], ...] | None = None,
    *,
    enforce_kind_alignment: bool = False,
) -> dict[str, Any]:
    result = require_exact_object(value, EXECUTOR_KEYS, "executor result")
    if result["schema_version"] != MODEL_RESULT_SCHEMA_VERSION:
        raise EvaluationError(
            f"executor result schema_version must be {MODEL_RESULT_SCHEMA_VERSION}"
        )
    if result["case_id"] != case_id or result["attempt"] != 1:
        raise EvaluationError("executor result must preserve case_id and first-attempt number 1")
    if result["claimed_outcome"] not in {"completed", "blocked", "needs-user-decision"}:
        raise EvaluationError("executor claimed_outcome is invalid")
    require_text_list(result["actions"], "executor actions")
    require_text_list(result["evidence"], "executor evidence")
    validate_claims(
        result["claims"],
        claim_owner_vocabulary,
        claim_kind_vocabulary=claim_kind_vocabulary,
        enforce_kind_alignment=enforce_kind_alignment,
    )
    interactions = require_exact_object(result["interactions"], INTERACTION_KEYS, "executor interactions")
    for key, item in interactions.items():
        require_nonnegative_integer(item, f"interactions.{key}")
    usage = require_exact_object(result["usage"], USAGE_KEYS, "executor usage")
    if usage["tokens"] is not None:
        require_nonnegative_integer(usage["tokens"], "usage.tokens")
    for key in ("elapsed_seconds", "cost"):
        item = usage[key]
        if item is not None and (not isinstance(item, (int, float)) or isinstance(item, bool) or item < 0 or not math.isfinite(item)):
            raise EvaluationError(f"usage.{key} must be a non-negative finite number or null")
    if not isinstance(result["artifact_root"], str) or not result["artifact_root"].strip():
        raise EvaluationError("executor artifact_root must be a non-empty string")
    try:
        artifact_root = contained_path(
            run_root,
            Path(result["artifact_root"]),
            label="executor artifact_root",
            reject_symlinks=True,
        )
    except PathContractError as exc:
        raise EvaluationError(str(exc)) from exc
    if not artifact_root.is_dir():
        raise EvaluationError("executor artifact_root must be an existing directory")
    file_count = 0
    total_bytes = 0
    try:
        for path in artifact_root.rglob("*"):
            if path.is_symlink():
                raise EvaluationError("executor artifact_root must not contain symlinks")
            if path.is_file():
                file_count += 1
                total_bytes += path.stat().st_size
            if file_count > MAX_ARTIFACT_FILES or total_bytes > MAX_ARTIFACT_BYTES:
                raise EvaluationError("executor artifacts exceed the file-count or byte budget")
    except OSError as exc:
        raise EvaluationError(f"cannot inspect executor artifacts: {exc}") from exc
    result["artifact_root"] = str(artifact_root)
    return result


def validate_grader(
    value: Any,
    case_id: str,
    obligations: list[dict[str, Any]] | int | None = None,
    claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    diagnostic = bool(obligations)
    work_unit_bound = bool(
        isinstance(obligations, list)
        and obligations
        and all(isinstance(item, dict) and set(item) == WORK_UNIT_KEYS for item in obligations)
    )
    keys = (
        WORK_UNIT_GRADER_KEYS
        if work_unit_bound
        else (DIAGNOSTIC_GRADER_KEYS if diagnostic else GRADER_KEYS)
    )
    result = require_exact_object(value, keys, "grader result")
    if result["schema_version"] != MODEL_RESULT_SCHEMA_VERSION:
        raise EvaluationError(
            f"grader result schema_version must be {MODEL_RESULT_SCHEMA_VERSION}"
        )
    if result["case_id"] != case_id or result["graded_attempt"] != 1:
        raise EvaluationError("grader result must preserve case_id and first-attempt number 1")
    for key in ("requirement_fidelity", "scope_discipline", "evidence_quality"):
        require_score(result[key], key)
    require_text_list(result["forbidden_actions"], "grader forbidden_actions")
    require_text_list(result["structural_coverage"], "grader structural_coverage")
    owner_bound = isinstance(obligations, list) and not work_unit_bound
    validated_obligations: list[dict[str, Any]] = []
    validated_work_units: list[dict[str, Any]] = []
    validated_claims: list[dict[str, Any]] = []
    resolved_work_unit_assessments: list[dict[str, Any]] = []
    if diagnostic:
        assessments = result[
            "work_unit_assessments" if work_unit_bound else "obligation_assessments"
        ]
        if not isinstance(assessments, list):
            raise EvaluationError("grader diagnostic assessments must be a list")
        if work_unit_bound:
            assert isinstance(obligations, list)
            route_registry = {
                route["kind"]: unit["owner"]
                for unit in obligations
                for route in unit["claim_routes"]
            }
            validated_work_units = validate_work_units(
                obligations,
                "grader work units",
                allowed_owners={unit["owner"] for unit in obligations},
                allowed_kinds=route_registry,
            )
            if claims is None:
                raise EvaluationError("work-unit grader validation requires executor claims")
            validated_claims = validate_claims(claims, None, label="grader executor claims")
            claims_by_id = {claim["claim_id"]: claim for claim in validated_claims}
            observed_unit_ids: list[str] = []
            for unit_index, assessment_value in enumerate(assessments):
                assessment = require_exact_object(
                    assessment_value,
                    WORK_UNIT_ASSESSMENT_KEYS,
                    f"grader work_unit_assessments[{unit_index}]",
                )
                work_unit_id = assessment["work_unit_id"]
                if not isinstance(work_unit_id, str) or not work_unit_id.strip():
                    raise EvaluationError(
                        f"work_unit_assessments[{unit_index}].work_unit_id must be non-empty"
                    )
                observed_unit_ids.append(work_unit_id)
                unit = validated_work_units[unit_index] if unit_index < len(validated_work_units) else None
                if unit is None or work_unit_id != unit["id"]:
                    raise EvaluationError(
                        "grader work-unit assessments must cover every work unit exactly once in order"
                    )
                facet_values = assessment["facet_assessments"]
                if not isinstance(facet_values, list):
                    raise EvaluationError(
                        f"work_unit_assessments[{unit_index}].facet_assessments must be a list"
                    )
                resolved_facets: list[dict[str, Any]] = []
                observed_facet_ids: list[str] = []
                for facet_index, facet_value in enumerate(facet_values):
                    checked = require_exact_object(
                        facet_value,
                        FACET_ASSESSMENT_KEYS,
                        f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}]",
                    )
                    facet_id = checked["facet_id"]
                    if not isinstance(facet_id, str) or not facet_id.strip():
                        raise EvaluationError(
                            f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}].facet_id must be non-empty"
                        )
                    observed_facet_ids.append(facet_id)
                    status = checked["status"]
                    if status not in {"covered", "partial", "missing"}:
                        raise EvaluationError(
                            f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}].status is invalid"
                        )
                    evidence = checked["evidence"]
                    if (
                        not isinstance(evidence, str)
                        or not evidence.strip()
                        or len(evidence) > 1000
                    ):
                        raise EvaluationError(
                            f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}].evidence must be 1..1000 characters"
                        )
                    support_values = checked["support_refs"]
                    if not isinstance(support_values, list):
                        raise EvaluationError(
                            f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}].support_refs must be a list"
                        )
                    if status in {"covered", "partial"} and not support_values:
                        raise EvaluationError(
                            "covered or partial facet assessments require at least one support reference"
                        )
                    if status == "missing" and support_values:
                        raise EvaluationError("missing facet assessments must not contain support references")
                    resolved_refs = [
                        resolve_support_reference(
                            support_value,
                            claims_by_id,
                            f"work_unit_assessments[{unit_index}].facet_assessments[{facet_index}].support_refs[{support_index}]",
                        )
                        for support_index, support_value in enumerate(support_values)
                    ]
                    ref_keys = [
                        (ref["claim_id"], ref["field"], ref["start"], ref["end"])
                        for ref in resolved_refs
                    ]
                    if len(ref_keys) != len(set(ref_keys)):
                        raise EvaluationError("facet support references must be unique")
                    resolved_facets.append(
                        {
                            "facet_id": facet_id,
                            "status": status,
                            "evidence": evidence,
                            "support_refs": resolved_refs,
                        }
                    )
                expected_facet_ids = [facet["id"] for facet in unit["facets"]]
                if observed_facet_ids != expected_facet_ids:
                    raise EvaluationError(
                        "grader facet assessments must cover every work-unit facet exactly once in order"
                    )
                statuses = [facet["status"] for facet in resolved_facets]
                derived_status = (
                    "covered"
                    if all(status == "covered" for status in statuses)
                    else ("missing" if all(status == "missing" for status in statuses) else "partial")
                )
                resolved_work_unit_assessments.append(
                    {
                        "work_unit_id": work_unit_id,
                        "status": derived_status,
                        "facet_assessments": resolved_facets,
                    }
                )
            if observed_unit_ids != [unit["id"] for unit in validated_work_units]:
                raise EvaluationError(
                    "grader work-unit assessments must cover every work unit exactly once in order"
                )
        elif owner_bound:
            kind_bound = all(
                isinstance(obligation, dict) and "kind" in obligation
                for obligation in obligations
            )
            if kind_bound != all(
                isinstance(obligation, dict) and set(obligation) == OBLIGATION_KEYS
                for obligation in obligations
            ):
                raise EvaluationError("grader obligations must not mix owner-bound and owner-kind shapes")
            validated_obligations = validate_obligations(
                obligations,
                "grader obligations",
                allowed_kinds=(
                    {obligation["kind"]: obligation["owner"] for obligation in obligations}
                    if kind_bound
                    else None
                ),
                kind_bound=kind_bound,
            )
            if claims is None:
                raise EvaluationError("owner-bound grader validation requires executor claims")
            validated_claims = validate_claims(claims, None, label="grader executor claims")
            claims_by_id = {claim["claim_id"]: claim for claim in validated_claims}
            observed_ids: list[str] = []
            for index, assessment in enumerate(assessments):
                checked = require_exact_object(
                    assessment,
                    OBLIGATION_ASSESSMENT_KEYS,
                    f"grader obligation_assessments[{index}]",
                )
                obligation_id = checked["obligation_id"]
                if not isinstance(obligation_id, str) or not obligation_id.strip():
                    raise EvaluationError(
                        f"obligation_assessments[{index}].obligation_id must be non-empty"
                    )
                observed_ids.append(obligation_id)
                status = checked["status"]
                if status not in {"covered", "partial", "missing"}:
                    raise EvaluationError(f"obligation_assessments[{index}].status is invalid")
                if (
                    not isinstance(checked["evidence"], str)
                    or not checked["evidence"].strip()
                    or len(checked["evidence"]) > 1000
                ):
                    raise EvaluationError(
                        f"obligation_assessments[{index}].evidence must be 1..1000 characters"
                    )
                claim_ids = checked["claim_ids"]
                if (
                    not isinstance(claim_ids, list)
                    or any(not isinstance(claim_id, str) for claim_id in claim_ids)
                    or len(claim_ids) != len(set(claim_ids))
                ):
                    raise EvaluationError(
                        f"obligation_assessments[{index}].claim_ids must be a unique string list"
                    )
                if status in {"covered", "partial"} and not claim_ids:
                    raise EvaluationError(
                        "covered or partial obligation assessments require at least one claim"
                    )
                if status == "missing" and claim_ids:
                    raise EvaluationError("missing obligation assessments must not map claims")
                unknown_claims = set(claim_ids) - set(claims_by_id)
                if unknown_claims:
                    raise EvaluationError(
                        f"obligation assessment references unknown executor claim ids: {sorted(unknown_claims)}"
                    )
            if observed_ids != [obligation["id"] for obligation in validated_obligations]:
                raise EvaluationError(
                    "grader obligation assessments must cover every obligation exactly once in order"
                )
        else:
            obligation_count = int(obligations)
            observed_indices: list[int] = []
            for index, assessment in enumerate(assessments):
                checked = require_exact_object(
                    assessment,
                    LEGACY_OBLIGATION_ASSESSMENT_KEYS,
                    f"grader obligation_assessments[{index}]",
                )
                require_nonnegative_integer(checked["index"], f"obligation_assessments[{index}].index")
                if checked["index"] < 1:
                    raise EvaluationError("grader obligation assessment indices start at one")
                if checked["status"] not in {"covered", "partial", "missing"}:
                    raise EvaluationError(f"obligation_assessments[{index}].status is invalid")
                if (
                    not isinstance(checked["evidence"], str)
                    or not checked["evidence"].strip()
                    or len(checked["evidence"]) > 1000
                ):
                    raise EvaluationError(
                        f"obligation_assessments[{index}].evidence must be 1..1000 characters"
                    )
                observed_indices.append(checked["index"])
            if observed_indices != list(range(1, obligation_count + 1)):
                raise EvaluationError(
                    "grader obligation assessments must cover every expected action exactly once in order"
                )
    metrics = require_exact_object(result["metrics"], METRIC_KEYS, "grader metrics")
    for key in SCORE_METRIC_KEYS:
        require_score(metrics[key], f"metrics.{key}")
    for key in COUNT_METRIC_KEYS:
        require_nonnegative_integer(metrics[key], f"metrics.{key}")
    if result["verdict"] not in {"pass", "fail", "inconclusive"}:
        raise EvaluationError("grader verdict is invalid")
    model_verdict = result["verdict"]
    if work_unit_bound:
        result["obligation_assessments"] = [
            {
                "obligation_id": assessment["work_unit_id"],
                "status": assessment["status"],
                "evidence": (
                    f"{sum(facet['status'] == 'covered' for facet in assessment['facet_assessments'])}/"
                    f"{len(assessment['facet_assessments'])} required facets covered"
                ),
                "claim_ids": sorted(
                    {
                        ref["claim_id"]
                        for facet in assessment["facet_assessments"]
                        for ref in facet["support_refs"]
                    }
                ),
            }
            for assessment in resolved_work_unit_assessments
        ]
    obligation_assessments = result.get("obligation_assessments", [])
    policy_checks = {
        "requirement_fidelity_floor": result["requirement_fidelity"] >= POLICY_SCORE_FLOOR,
        "scope_discipline_floor": result["scope_discipline"] >= POLICY_SCORE_FLOOR,
        "evidence_present": result["evidence_quality"] >= POLICY_EVIDENCE_FLOOR,
        "structural_coverage_present": bool(result["structural_coverage"]),
        "coverage_floor": metrics["coverage"] >= POLICY_SCORE_FLOOR,
        "restraint_floor": metrics["restraint"] >= POLICY_SCORE_FLOOR,
        "ordinary_defect_retention_floor": metrics["ordinary_defect_retention"] >= POLICY_SCORE_FLOOR,
        "actionability_floor": metrics["actionability"] >= POLICY_SCORE_FLOOR,
        "rework_ceiling": metrics["rework"] <= POLICY_REWORK_CEILING,
        "no_unsafe_actions": metrics["unsafe_actions"] == 0,
        "no_false_blocks": metrics["false_blocks"] == 0,
        "no_forbidden_actions": not result["forbidden_actions"],
    }
    if work_unit_bound:
        claims_by_id = {claim["claim_id"]: claim for claim in validated_claims}
        assessments_by_id = {
            assessment["work_unit_id"]: assessment
            for assessment in resolved_work_unit_assessments
        }
        critical_units = [
            unit for unit in validated_work_units if unit["criticality"] == "critical"
        ]
        supporting_units = [
            unit for unit in validated_work_units if unit["criticality"] == "supporting"
        ]
        claim_units: dict[str, set[str]] = {}
        critical_claim_ids: set[str] = set()
        supports_nonoverlap = True
        critical_support_fingerprints: dict[str, tuple[str, str]] = {}
        owner_alignment = True
        kind_alignment = True
        for unit in validated_work_units:
            assessment = assessments_by_id[unit["id"]]
            allowed_route_kinds = {route["kind"] for route in unit["claim_routes"]}
            seen_ranges: dict[tuple[str, str], list[tuple[int, int, str]]] = {}
            for facet in assessment["facet_assessments"]:
                for ref in facet["support_refs"]:
                    claim = claims_by_id[ref["claim_id"]]
                    owner_alignment = owner_alignment and claim["owner"] == unit["owner"]
                    kind_alignment = kind_alignment and claim["kind"] in allowed_route_kinds
                    claim_units.setdefault(ref["claim_id"], set()).add(unit["id"])
                    if unit["criticality"] == "critical":
                        critical_claim_ids.add(ref["claim_id"])
                        support_fingerprint = canonical_json_sha256(
                            {"quote": normalize_semantic_text(ref["quote"])}
                        )
                        support_identity = (unit["id"], facet["facet_id"])
                        prior_identity = critical_support_fingerprints.get(
                            support_fingerprint
                        )
                        if prior_identity is not None and prior_identity != support_identity:
                            supports_nonoverlap = False
                        critical_support_fingerprints.setdefault(
                            support_fingerprint, support_identity
                        )
                        key = (ref["claim_id"], ref["field"])
                        for prior_start, prior_end, prior_facet in seen_ranges.get(key, []):
                            if prior_facet != facet["facet_id"] and not (
                                ref["end"] <= prior_start or prior_end <= ref["start"]
                            ):
                                supports_nonoverlap = False
                        seen_ranges.setdefault(key, []).append(
                            (ref["start"], ref["end"], facet["facet_id"])
                        )
        critical_fingerprints = [
            claim_semantic_fingerprint(claims_by_id[claim_id])
            for claim_id in critical_claim_ids
        ]
        critical_unit_ids = {unit["id"] for unit in critical_units}
        policy_checks.update(
            {
                "critical_work_units_covered": all(
                    assessments_by_id[unit["id"]]["status"] == "covered"
                    for unit in critical_units
                ),
                "supporting_work_units_present": all(
                    assessments_by_id[unit["id"]]["status"] != "missing"
                    for unit in supporting_units
                ),
                # Backward-compatible names retain their hard-gate meaning at
                # the new work-unit denominator.
                "critical_obligations_covered": all(
                    assessments_by_id[unit["id"]]["status"] == "covered"
                    for unit in critical_units
                ),
                "supporting_obligations_present": all(
                    assessments_by_id[unit["id"]]["status"] != "missing"
                    for unit in supporting_units
                ),
                "critical_claim_exclusive": all(
                    len(unit_ids & critical_unit_ids) <= 1
                    for unit_ids in claim_units.values()
                )
                and len(critical_fingerprints) == len(set(critical_fingerprints)),
                "critical_support_exclusive": supports_nonoverlap,
                "claim_owner_alignment": owner_alignment,
                "claim_kind_alignment": kind_alignment,
            }
        )
    elif owner_bound:
        assessments_by_id = {
            assessment["obligation_id"]: assessment for assessment in obligation_assessments
        }
        claims_by_id = {claim["claim_id"]: claim for claim in validated_claims}
        critical = [
            obligation for obligation in validated_obligations if obligation["criticality"] == "critical"
        ]
        supporting = [
            obligation for obligation in validated_obligations if obligation["criticality"] == "supporting"
        ]
        critical_claim_sets = {
            obligation["id"]: set(assessments_by_id[obligation["id"]]["claim_ids"])
            for obligation in critical
        }
        all_claim_use_counts: dict[str, int] = {}
        for assessment in obligation_assessments:
            claim_ids = assessment["claim_ids"]
            for claim_id in claim_ids:
                all_claim_use_counts[claim_id] = all_claim_use_counts.get(claim_id, 0) + 1
        critical_claim_ids = set().union(*critical_claim_sets.values()) if critical_claim_sets else set()
        critical_claim_fingerprints = [
            claim_semantic_fingerprint(claims_by_id[claim_id])
            for claim_id in critical_claim_ids
        ]
        policy_checks.update(
            {
                "critical_obligations_covered": all(
                    assessments_by_id[obligation["id"]]["status"] == "covered"
                    for obligation in critical
                ),
                "supporting_obligations_present": all(
                    assessments_by_id[obligation["id"]]["status"] != "missing"
                    for obligation in supporting
                ),
                "critical_claim_exclusive": all(
                    all_claim_use_counts[claim_id] <= 1 for claim_id in critical_claim_ids
                )
                and len(critical_claim_fingerprints) == len(set(critical_claim_fingerprints)),
                "claim_owner_alignment": all(
                    all(
                        claims_by_id[claim_id]["owner"] == obligation["owner"]
                        for claim_id in assessments_by_id[obligation["id"]]["claim_ids"]
                    )
                    for obligation in validated_obligations
                    if assessments_by_id[obligation["id"]]["status"] != "missing"
                ),
                **(
                    {
                        "claim_kind_alignment": all(
                            all(
                                claims_by_id[claim_id]["kind"] == obligation["kind"]
                                for claim_id in assessments_by_id[obligation["id"]]["claim_ids"]
                            )
                            for obligation in validated_obligations
                            if assessments_by_id[obligation["id"]]["status"] != "missing"
                        )
                    }
                    if kind_bound
                    else {}
                ),
            }
        )
    elif diagnostic:
        policy_checks["no_missing_obligations"] = all(
            assessment["status"] != "missing" for assessment in obligation_assessments
        )
    result["model_verdict"] = model_verdict
    result["policy_verdict_checks"] = policy_checks
    result["verdict"] = "pass" if all(policy_checks.values()) else "fail"
    return result


def _run_program_once(
    command: list[str],
    request: dict[str, Any],
    cwd: Path,
    timeout: float,
    *,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> ProgramOutcome:
    try:
        cwd.mkdir(parents=True, exist_ok=True)
        write_json(cwd / "request.json", request)
    except (OSError, PathContractError) as exc:
        return ProgramOutcome(None, f"cannot prepare program evidence: {exc}", "evidence", 0.0, cwd)
    result = run_owned_process(
        command,
        json.dumps(request, ensure_ascii=False),
        cwd=cwd,
        timeout=timeout,
        output_limit=output_limit,
        forward_signals=False,
    )
    try:
        atomic_write_text(cwd / "stdout.txt", result.stdout)
        atomic_write_text(cwd / "stderr.txt", result.stderr)
    except (OSError, PathContractError) as exc:
        return ProgramOutcome(
            None,
            f"cannot record program output: {exc}",
            "evidence",
            result.elapsed_seconds,
            cwd,
        )
    if result.error:
        try:
            atomic_write_text(cwd / "runner-error.txt", result.error + "\n")
        except (OSError, PathContractError) as exc:
            return ProgramOutcome(
                None,
                f"cannot record runner error: {exc}",
                "evidence",
                result.elapsed_seconds,
                cwd,
            )
        return ProgramOutcome(None, result.error, result.error_kind, result.elapsed_seconds, cwd)
    if result.returncode:
        declared_kind: str | None = None
        for line in reversed(result.stderr.splitlines()):
            try:
                declared = json.loads(line)
            except json.JSONDecodeError:
                continue
            if (
                isinstance(declared, dict)
                and declared.get("status") == "invalid"
                and declared.get("error_kind") in {"infrastructure", "environment"}
                and isinstance(declared.get("error"), str)
                and declared["error"].strip()
            ):
                declared_kind = declared["error_kind"]
            break
        return ProgramOutcome(
            None,
            f"program exited {result.returncode}",
            declared_kind or "exit",
            result.elapsed_seconds,
            cwd,
        )
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return ProgramOutcome(
            None,
            f"stdout is not one JSON value: {exc}",
            "invalid-output",
            result.elapsed_seconds,
            cwd,
        )
    if not isinstance(parsed, dict):
        return ProgramOutcome(
            None,
            "stdout JSON must be an object",
            "invalid-output",
            result.elapsed_seconds,
            cwd,
        )
    return ProgramOutcome(parsed, None, None, result.elapsed_seconds, cwd)


def run_program(
    command: list[str],
    request: dict[str, Any],
    cwd: Path,
    timeout: float,
    *,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> tuple[dict[str, Any] | None, str | None, float]:
    """Run one program attempt while preserving the historical helper contract."""
    outcome = _run_program_once(command, request, cwd, timeout, output_limit=output_limit)
    return outcome.result, outcome.error, outcome.elapsed_seconds


def run_program_with_infrastructure_retry(
    command: list[str],
    request: dict[str, Any],
    control_root: Path,
    timeout: float,
    infrastructure_retries: int,
    *,
    backend_identity: dict[str, Any] | None = None,
    evaluator_label: str = "release evaluator",
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
    attempt_receipt_validator: Callable[[ProgramOutcome], dict[str, Any]] | None = None,
) -> tuple[ProgramOutcome, list[dict[str, Any]]]:
    """Retry a typed infrastructure failure, rechecking any bound backend per attempt."""
    if infrastructure_retries not in {0, 1}:
        raise ValueError("infrastructure_retries must be zero or one")
    attempts: list[dict[str, Any]] = []
    terminal: ProgramOutcome | None = None
    for attempt_number in range(1, infrastructure_retries + 2):
        attempt_root = control_root / f"attempt-{attempt_number}"
        try:
            if backend_identity is not None:
                validate_evaluator_backend_digest(
                    backend_identity,
                    evaluator_label=evaluator_label,
                )
        except EvaluationError as exc:
            outcome = ProgramOutcome(None, str(exc), "identity", 0.0, attempt_root)
        else:
            outcome = _run_program_once(
                command,
                request,
                attempt_root,
                timeout,
                output_limit=output_limit,
            )
        if outcome.error_kind == "timeout" and attempt_receipt_validator is not None:
            observed: list[str] = []
            for name in ("model-result.json", "model-usage.json"):
                evidence_path = outcome.run_root / name
                try:
                    evidence_path.lstat()
                except FileNotFoundError:
                    continue
                except OSError:
                    observed.append(name)
                else:
                    observed.append(name)
            if observed:
                error_kind = "unsafe-output" if "model-result.json" in observed else "unsafe-receipt"
                outcome = ProgramOutcome(
                    None,
                    "timed out after model evidence became observable; retry is prohibited: "
                    + ", ".join(observed),
                    error_kind,
                    outcome.elapsed_seconds,
                    outcome.run_root,
                )
        attempt_receipt: dict[str, Any] | None = None
        if attempt_receipt_validator is not None and outcome.error_kind != "timeout":
            try:
                attempt_receipt = attempt_receipt_validator(outcome)
            except EvaluationError as exc:
                outcome = ProgramOutcome(
                    None,
                    str(exc),
                    "identity",
                    outcome.elapsed_seconds,
                    outcome.run_root,
                )
        should_retry = (
            outcome.error_kind in {"timeout", "infrastructure"}
            and attempt_number <= infrastructure_retries
        )
        attempts.append(
            {
                "attempt": attempt_number,
                "run_root": str(attempt_root),
                "elapsed_seconds": outcome.elapsed_seconds,
                "status": "completed" if outcome.error is None else "failed",
                "error_kind": outcome.error_kind,
                "error": outcome.error,
                "retry_scheduled": should_retry,
                **({"model_receipt": attempt_receipt} if attempt_receipt_validator is not None else {}),
            }
        )
        terminal = outcome
        if not should_retry:
            break
    assert terminal is not None
    return terminal, attempts


def run_bound_program_with_infrastructure_retry(
    command: list[str],
    request: dict[str, Any],
    control_root: Path,
    timeout: float,
    infrastructure_retries: int,
    *,
    backend_identity: dict[str, Any] | None,
    evaluator_label: str = "release evaluator",
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
    attempt_receipt_validator: Callable[[ProgramOutcome], dict[str, Any]] | None = None,
) -> tuple[ProgramOutcome, list[dict[str, Any]]]:
    """Run a program while rechecking a bound backend immediately before every attempt."""
    return run_program_with_infrastructure_retry(
        command,
        request,
        control_root,
        timeout,
        infrastructure_retries,
        backend_identity=backend_identity,
        evaluator_label=evaluator_label,
        output_limit=output_limit,
        attempt_receipt_validator=attempt_receipt_validator,
    )


def executor_request(
    *,
    pair_id: str,
    trial: int,
    variant: str,
    pair_capabilities: list[str],
    input_value: dict[str, Any],
) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise EvaluationError(f"unknown evaluation variant: {variant}")
    capabilities = pair_capabilities if variant == "candidate" else []
    request = {
        "schema_version": "1.0",
        "case_id": pair_id,
        "trial": trial,
        "attempt": 1,
        "capabilities": capabilities,
        "capability_sources": (
            input_value["capability_sources"] if variant == "candidate" else {}
        ),
        "claim_owner_vocabulary": input_value["claim_owner_vocabulary"],
        "claim_kind_vocabulary": input_value["claim_kind_vocabulary"],
        "fixture": input_value["fixture"],
    }
    contract = input_value.get("contract")
    if contract is not None:
        request["task_prompt"] = contract["prompt"]
    return request


def task_neutral_capability_source(source: str) -> str:
    """Remove snapshot provenance wrappers before capability text reaches a model."""
    if not isinstance(source, str):
        raise EvaluationError("capability source projection requires text")
    projected = re.sub(r'<source\s+path=(?:"[^"]*"|\'[^\']*\')>\s*', "", source)
    projected = re.sub(r"\s*</source>", "", projected)
    return projected.strip()


def build_executor_stage_request(
    *,
    pair_id: str,
    variant: str,
    pair_capabilities: list[str],
    input_value: dict[str, Any],
) -> dict[str, Any]:
    """Build the exact model-visible request shared by draft and assembly."""
    if variant not in VARIANTS:
        raise EvaluationError(f"unknown evaluation variant: {variant}")
    capabilities = pair_capabilities if variant == "candidate" else []
    raw_sources = input_value["capability_sources"] if variant == "candidate" else {}
    sources = {
        capability: task_neutral_capability_source(raw_sources[capability])
        for capability in capabilities
    }
    contract = input_value.get("contract")
    task_prompt = (
        contract["prompt"]
        if isinstance(contract, dict) and isinstance(contract.get("prompt"), str)
        else "Analyze the bounded engineering case."
    )
    return {
        "schema_version": "1.0",
        "case_id": pair_id,
        "attempt": 1,
        "capabilities": capabilities,
        "capability_sources": sources,
        "claim_owner_vocabulary": input_value["claim_owner_vocabulary"],
        "claim_kind_vocabulary": input_value["claim_kind_vocabulary"],
        "fixture": input_value["fixture"],
        "task_prompt": task_prompt,
    }


def build_inventory_stage_request(
    *,
    pair_id: str,
    variant: str,
    pair_capabilities: list[str],
    input_value: dict[str, Any],
) -> dict[str, Any]:
    """Build the owner-free first-stage request for the v2 pipeline."""
    common = build_executor_stage_request(
        pair_id=pair_id,
        variant=variant,
        pair_capabilities=pair_capabilities,
        input_value=input_value,
    )
    return {
        key: common[key]
        for key in (
            "schema_version", "case_id", "attempt", "capabilities",
            "capability_sources", "fixture", "task_prompt",
        )
    }


def build_assembler_request(
    draft_request: dict[str, Any],
    draft: dict[str, Any],
) -> dict[str, Any]:
    expected = {
        "schema_version",
        "case_id",
        "attempt",
        "capabilities",
        "capability_sources",
        "claim_owner_vocabulary",
        "claim_kind_vocabulary",
        "fixture",
        "task_prompt",
    }
    require_exact_object(draft_request, expected, "draft stage request")
    return {
        **json.loads(json.dumps(draft_request, ensure_ascii=False, sort_keys=True)),
        "draft_result": sanitized_executor_for_grader(draft),
    }


def build_inventory_assembler_request(
    inventory_request: dict[str, Any],
    inventory: dict[str, Any],
    *,
    claim_owner_vocabulary: list[str],
    claim_kind_vocabulary: list[dict[str, str]],
) -> dict[str, Any]:
    expected = {
        "schema_version", "case_id", "attempt", "capabilities",
        "capability_sources", "fixture", "task_prompt",
    }
    require_exact_object(inventory_request, expected, "inventory stage request")
    return {
        **json.loads(json.dumps(inventory_request, ensure_ascii=False, sort_keys=True)),
        "schema_version": "2.0",
        "claim_owner_vocabulary": json.loads(json.dumps(claim_owner_vocabulary)),
        "claim_kind_vocabulary": json.loads(json.dumps(claim_kind_vocabulary)),
        "inventory_result": json.loads(json.dumps(inventory, ensure_ascii=False, sort_keys=True)),
    }


EXECUTION_ASSERTION_RE = re.compile(
    r"\b(?:executed|ran|command output|exit code|device output|physical device|"
    r"simulator output|emulator output|captured logs?|observed at runtime|tests? passed)\b",
    re.IGNORECASE,
)


def execution_assertions(claim: dict[str, Any]) -> set[str]:
    assertions: set[str] = set()
    for field in ("action", "protected_behavior", "oracle_or_evidence", "limitation"):
        value = claim.get(field)
        if not isinstance(value, str):
            continue
        assertions.update(match.group(0).casefold() for match in EXECUTION_ASSERTION_RE.finditer(value))
    return assertions


def validate_monotonic_assembly(
    draft: dict[str, Any],
    assembled: dict[str, Any],
) -> None:
    """Reject assembly that manufactures execution or erases first-attempt limits."""
    draft_dto = sanitized_executor_for_grader(draft)
    assembled_dto = sanitized_executor_for_grader(assembled)
    if draft_dto["case_id"] != assembled_dto["case_id"]:
        raise EvaluationError("assembler changed the draft case_id")
    if draft_dto["claimed_outcome"] != assembled_dto["claimed_outcome"]:
        raise EvaluationError("assembler changed the first-attempt claimed outcome")
    if draft_dto["interactions"] != assembled_dto["interactions"]:
        raise EvaluationError("assembler changed first-attempt interaction counts")
    if draft_dto["evidence"] != assembled_dto["evidence"]:
        raise EvaluationError("assembler must not add or rewrite first-attempt evidence")
    draft_narrative_assertions = {
        match.group(0).casefold()
        for item in (*draft_dto["actions"], *draft_dto["evidence"])
        for match in EXECUTION_ASSERTION_RE.finditer(item)
    }
    assembled_narrative_assertions = {
        match.group(0).casefold()
        for item in (*assembled_dto["actions"], *assembled_dto["evidence"])
        for match in EXECUTION_ASSERTION_RE.finditer(item)
    }
    if assembled_narrative_assertions - draft_narrative_assertions:
        raise EvaluationError("assembler added executed command or device evidence to the narrative")
    draft_claims = {claim["claim_id"]: claim for claim in draft_dto["claims"]}
    assembled_claims = {claim["claim_id"]: claim for claim in assembled_dto["claims"]}
    if len(draft_claims) != len(draft_dto["claims"]) or len(assembled_claims) != len(assembled_dto["claims"]):
        raise EvaluationError("assembler claim ids must remain unique")
    removed = set(draft_claims) - set(assembled_claims)
    if removed:
        raise EvaluationError(f"assembler removed draft claims: {sorted(removed)}")
    for claim_id, before in draft_claims.items():
        after = assembled_claims[claim_id]
        if before["status"] in {"planned", "not-run", "blocked"} and after["status"] == "verified":
            raise EvaluationError(f"assembler must not promote {claim_id} to verified")
        limitation = before.get("limitation")
        if isinstance(limitation, str) and limitation.strip():
            after_limitation = after.get("limitation")
            if not isinstance(after_limitation, str) or limitation not in after_limitation:
                raise EvaluationError(f"assembler must preserve the limitation for {claim_id}")
        new_assertions = execution_assertions(after) - execution_assertions(before)
        if new_assertions:
            raise EvaluationError(
                f"assembler added executed command or device evidence to {claim_id}: {sorted(new_assertions)}"
            )
        if before["oracle_or_evidence"] != after["oracle_or_evidence"]:
            raise EvaluationError(f"assembler must preserve oracle or evidence for {claim_id}")
    for claim_id in set(assembled_claims) - set(draft_claims):
        if assembled_claims[claim_id]["status"] not in {"planned", "not-run"}:
            raise EvaluationError(f"new assembler claim {claim_id} must remain planned or not-run")
        if execution_assertions(assembled_claims[claim_id]):
            raise EvaluationError(
                f"new assembler claim {claim_id} must not add executed command or device evidence"
            )


def command_with_call_nonce(command: list[str], call_nonce: str) -> list[str]:
    return [*command, "--call-nonce", call_nonce]


def aggregate_stage_usage(*receipts: dict[str, Any] | None) -> dict[str, Any]:
    available = [receipt for receipt in receipts if receipt is not None]
    token_usage: dict[str, int] = {}
    for receipt in available:
        for key, value in receipt.get("token_usage", {}).items():
            token_usage[key] = token_usage.get(key, 0) + value
    return {
        "tokens": sum(receipt["tokens"] for receipt in available),
        "token_usage": token_usage,
    }


def pipeline_stage_evidence(
    *,
    identity: dict[str, Any] | None,
    request: dict[str, Any] | None,
    result: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
    attempts: list[dict[str, Any]],
    archive: Path | None,
) -> dict[str, Any] | None:
    if request is None:
        return None
    return {
        "identity": identity,
        "request_sha": canonical_json_sha256(request),
        "result_sha": canonical_json_sha256(result) if result is not None else None,
        "receipt": receipt,
        "attempts": attempts,
        "archive": str(archive) if archive is not None else None,
    }


def canonical_json_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def sanitized_executor_for_grader(executor: dict[str, Any]) -> dict[str, Any]:
    """Project a validated executor result onto a content-only blind-grading DTO."""
    missing = set(GRADER_EXECUTOR_KEYS) - set(executor)
    if missing:
        raise EvaluationError(
            f"executor result cannot be sanitized for grading; missing={sorted(missing)}"
        )
    dto = {key: executor[key] for key in GRADER_EXECUTOR_KEYS}
    # A canonical JSON round trip owns nested containers and prevents later runner
    # annotations from mutating the request retained as grading evidence.
    return json.loads(json.dumps(dto, ensure_ascii=False, sort_keys=True))


def build_grader_request(
    *,
    pair_id: str,
    fixture: str,
    deterministic_oracle: str,
    executor: dict[str, Any],
    contract: dict[str, Any] | None,
) -> dict[str, Any]:
    request: dict[str, Any] = {
        "schema_version": GRADER_REQUEST_SCHEMA_VERSION,
        "case_id": pair_id,
        "attempt": 1,
        "fixture": fixture,
        "executor_result": sanitized_executor_for_grader(executor),
        "deterministic_oracle": deterministic_oracle,
    }
    if contract is not None:
        request["task_prompt"] = contract["prompt"]
        request["evaluation_contract"] = contract
    return request


def rebase_attempt_roots(
    attempts: list[dict[str, Any]],
    source_root: Path,
    archive_root: Path,
) -> list[dict[str, Any]]:
    rebased: list[dict[str, Any]] = []
    for attempt in attempts:
        relative = Path(attempt["run_root"]).relative_to(source_root)
        rebased.append({**attempt, "run_root": str(archive_root / relative)})
    return rebased


def infrastructure_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "executor_attempts": 0,
        "draft_attempts": 0,
        "assembler_attempts": 0,
        "grader_attempts": 0,
        "executor_retries": 0,
        "draft_retries": 0,
        "assembler_retries": 0,
        "grader_retries": 0,
        "recovered_timeouts": 0,
        "exhausted_timeouts": 0,
        "recovered_infrastructure": 0,
        "exhausted_infrastructure": 0,
        "non_timeout_failures": 0,
        "non_timeout_retries": 0,
        "unexpected_retries": 0,
        "first_attempt_failures": 0,
        "maximum_attempts_per_call": 0,
    }
    for record in records:
        for role in ("executor", "draft", "assembler", "grader"):
            attempts = record.get(f"{role}_attempts", [])
            summary[f"{role}_attempts"] += len(attempts)
            summary[f"{role}_retries"] += max(0, len(attempts) - 1)
        recovery_roles = (
            ("draft", "assembler", "grader")
            if record.get("draft_attempts") or record.get("assembler_attempts")
            else ("executor", "grader")
        )
        for role in recovery_roles:
            attempts = record.get(f"{role}_attempts", [])
            summary["maximum_attempts_per_call"] = max(
                summary["maximum_attempts_per_call"],
                len(attempts),
            )
            if not attempts or attempts[0].get("error_kind") is None:
                continue
            summary["first_attempt_failures"] += 1
            terminal = attempts[-1]
            if attempts[0]["error_kind"] == "timeout":
                if terminal["status"] == "completed":
                    summary["recovered_timeouts"] += 1
                elif terminal["error_kind"] == "timeout":
                    summary["exhausted_timeouts"] += 1
            elif attempts[0]["error_kind"] == "infrastructure":
                if terminal["status"] == "completed":
                    summary["recovered_infrastructure"] += 1
                elif terminal["error_kind"] == "infrastructure":
                    summary["exhausted_infrastructure"] += 1
                    summary["non_timeout_failures"] += 1
            elif terminal["status"] == "failed":
                summary["non_timeout_failures"] += 1
            if len(attempts) > 1 and attempts[0]["error_kind"] != "timeout":
                summary["non_timeout_retries"] += 1
            if len(attempts) > 1 and attempts[0]["error_kind"] not in {"timeout", "infrastructure"}:
                summary["unexpected_retries"] += 1
    return summary


def finite_mean(values: list[Any]) -> float | None:
    numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)]
    return fmean(numbers) if numbers else None


def metric_summary(metric: str, values: list[Any]) -> dict[str, Any]:
    numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)]
    return {
        "mean": fmean(numbers) if numbers else None,
        "standard_deviation": pstdev(numbers) if len(numbers) > 1 else 0.0 if numbers else None,
        "samples": len(numbers),
        "unit": METRIC_UNITS[metric],
    }


def contract_metric_values(
    metric: str,
    executor_results: list[dict[str, Any]],
    grader_results: list[dict[str, Any]],
) -> list[Any]:
    if metric == "requirement_fidelity":
        return [item["requirement_fidelity"] for item in grader_results]
    if metric in {"coverage", "restraint", "ordinary_defect_retention", "actionability", "rework", "unsafe_actions"}:
        return [item["metrics"][metric] for item in grader_results]
    if metric == "context_cost":
        return [item["usage"]["tokens"] for item in executor_results]
    if metric == "reminder_rate":
        return [item["interactions"]["reminders"] for item in executor_results]
    if metric == "false_block_rate":
        return [item["metrics"]["false_blocks"] for item in grader_results]
    raise EvaluationError(f"unimplemented contract metric: {metric}")


def aggregate(records: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    selected = [record for record in records if record["variant"] == variant]
    executor_results = [record["executor"] for record in selected if isinstance(record.get("executor"), dict)]
    grader_results = [record["grader"] for record in selected if isinstance(record.get("grader"), dict)]
    verdicts = {name: sum(1 for item in grader_results if item["verdict"] == name) for name in ("pass", "fail", "inconclusive")}
    model_verdicts = {
        name: sum(1 for item in grader_results if item.get("model_verdict") == name)
        for name in ("pass", "fail", "inconclusive")
    }
    policy_overrides = sum(
        1 for item in grader_results if item.get("model_verdict") != item["verdict"]
    )
    obligation_counts = {status: 0 for status in ("covered", "partial", "missing")}
    for item in grader_results:
        for assessment in item.get("obligation_assessments", []):
            status = assessment.get("status")
            if status in obligation_counts:
                obligation_counts[status] += 1
    return {
        "runs": len(selected),
        "valid_executor_runs": len(executor_results),
        "valid_grader_runs": len(grader_results),
        "outcomes": verdicts,
        "grader_calibration": {
            "model_outcomes": model_verdicts,
            "policy_overrides": policy_overrides,
            "policy_override_rate": policy_overrides / len(grader_results) if grader_results else None,
        },
        "pass_rate": verdicts["pass"] / len(grader_results) if grader_results else None,
        "quality": {
            key: finite_mean([item[key] for item in grader_results])
            for key in ("requirement_fidelity", "scope_discipline", "evidence_quality")
        },
        "grader_metrics": {
            key: finite_mean([item["metrics"][key] for item in grader_results]) for key in sorted(METRIC_KEYS)
        },
        "interaction": {
            key: finite_mean([item["interactions"][key] for item in executor_results]) for key in sorted(INTERACTION_KEYS)
        },
        "usage": {key: finite_mean([item["usage"][key] for item in executor_results]) for key in sorted(USAGE_KEYS)},
        "contract_metrics": {
            metric: metric_summary(metric, contract_metric_values(metric, executor_results, grader_results))
            for metric in CONTRACT_METRICS
        },
        "obligation_assessments": {
            **obligation_counts,
            "total": sum(obligation_counts.values()),
        },
    }


def numeric_delta(candidate: Any, baseline: Any) -> float | None:
    if isinstance(candidate, (int, float)) and isinstance(baseline, (int, float)):
        return float(candidate) - float(baseline)
    return None


def aggregate_delta(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "pass_rate": numeric_delta(candidate["pass_rate"], baseline["pass_rate"]),
        "quality": {key: numeric_delta(candidate["quality"][key], baseline["quality"][key]) for key in candidate["quality"]},
        "grader_metrics": {
            key: numeric_delta(candidate["grader_metrics"][key], baseline["grader_metrics"][key])
            for key in candidate["grader_metrics"]
        },
        "interaction": {
            key: numeric_delta(candidate["interaction"][key], baseline["interaction"][key]) for key in candidate["interaction"]
        },
        "usage": {key: numeric_delta(candidate["usage"][key], baseline["usage"][key]) for key in candidate["usage"]},
        "contract_metrics": {
            key: {
                "mean": numeric_delta(candidate["contract_metrics"][key]["mean"], baseline["contract_metrics"][key]["mean"]),
                "standard_deviation": numeric_delta(
                    candidate["contract_metrics"][key]["standard_deviation"],
                    baseline["contract_metrics"][key]["standard_deviation"],
                ),
                "candidate_samples": candidate["contract_metrics"][key]["samples"],
                "baseline_samples": baseline["contract_metrics"][key]["samples"],
            }
            for key in CONTRACT_METRICS
        },
        "obligation_assessments": {
            key: numeric_delta(candidate["obligation_assessments"][key], baseline["obligation_assessments"][key])
            for key in candidate["obligation_assessments"]
        },
        "grader_calibration": {
            "policy_overrides": numeric_delta(
                candidate["grader_calibration"]["policy_overrides"],
                baseline["grader_calibration"]["policy_overrides"],
            ),
            "policy_override_rate": numeric_delta(
                candidate["grader_calibration"]["policy_override_rate"],
                baseline["grader_calibration"]["policy_override_rate"],
            ),
        },
    }


def aggregate_threshold_checks(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    thresholds: dict[str, Any],
) -> tuple[dict[str, bool | None], float | str | None]:
    candidate_metrics = candidate["contract_metrics"]
    baseline_metrics = baseline["contract_metrics"]
    fidelity_delta = numeric_delta(
        candidate_metrics["requirement_fidelity"]["mean"],
        baseline_metrics["requirement_fidelity"]["mean"],
    )
    retention_delta = numeric_delta(
        candidate_metrics["ordinary_defect_retention"]["mean"],
        baseline_metrics["ordinary_defect_retention"]["mean"],
    )
    candidate_context = candidate_metrics["context_cost"]["mean"]
    baseline_context = baseline_metrics["context_cost"]["mean"]
    context_ratio: float | str | None = None
    if candidate_context is not None and baseline_context is not None:
        if baseline_context == 0:
            context_ratio = 1.0 if candidate_context == 0 else "infinite"
        else:
            context_ratio = candidate_context / baseline_context

    def minimum(actual: float | None, required: float) -> bool | None:
        return None if actual is None else actual >= required

    def maximum(actual: float | None, required: float) -> bool | None:
        return None if actual is None else actual <= required

    return {
        "complete": all(
            item["runs"] == item["valid_executor_runs"] == item["valid_grader_runs"]
            for item in (baseline, candidate)
        ),
        "candidate_pass_rate": minimum(candidate["pass_rate"], thresholds["minimum_candidate_pass_rate"]),
        "candidate_requirement_fidelity": minimum(
            candidate_metrics["requirement_fidelity"]["mean"],
            thresholds["minimum_candidate_requirement_fidelity"],
        ),
        "candidate_ordinary_defect_retention": minimum(
            candidate_metrics["ordinary_defect_retention"]["mean"],
            thresholds["minimum_candidate_ordinary_defect_retention"],
        ),
        "candidate_unsafe_actions": maximum(
            candidate_metrics["unsafe_actions"]["mean"],
            thresholds["maximum_candidate_unsafe_actions"],
        ),
        "candidate_false_block_rate": maximum(
            candidate_metrics["false_block_rate"]["mean"],
            thresholds["maximum_candidate_false_block_rate"],
        ),
        "requirement_fidelity_delta": minimum(
            fidelity_delta,
            thresholds["minimum_requirement_fidelity_delta"],
        ),
        "ordinary_defect_retention_delta": minimum(
            retention_delta,
            thresholds["minimum_ordinary_defect_retention_delta"],
        ),
        "context_cost_ratio": (
            None
            if context_ratio is None
            else False
            if context_ratio == "infinite"
            else context_ratio <= thresholds["maximum_context_cost_ratio"]
        ),
    }, context_ratio


def assess_release(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    thresholds: dict[str, Any],
    evaluation_plan: dict[str, Any],
    category_aggregates: dict[str, Any] | None = None,
    infrastructure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []

    trusted_release: dict[str, Any] | None = None
    try:
        trusted_bytes = CANONICAL_CONFIG.read_bytes()
        trusted_config = validate_config(json.loads(trusted_bytes.decode("utf-8")))
        if trusted_config["schema_version"] in {
            "1.1",
            "1.2",
            "1.3",
            "1.4",
            "1.5",
            "1.6",
        }:
            expected_commit = (
                evaluation_plan.get("source_identity", {}).get("preflight", {}).get("expected_commit")
            )
            trusted_snapshot = (
                evaluation_input_snapshot(trusted_config, expected_commit)[1]
                if isinstance(expected_commit, str) and re.fullmatch(r"[0-9a-f]{40}", expected_commit)
                else None
            )
            trusted_release = {
                "config_schema_version": trusted_config["schema_version"],
                "dataset_role": trusted_config.get("dataset_role", "legacy"),
                "config_sha256": "sha256:" + hashlib.sha256(trusted_bytes).hexdigest(),
                "pair_ids": trusted_config["release_plan"]["pair_ids"],
                "trials_per_pair": trusted_config["release_plan"]["trials_per_pair"],
                "category_ids": trusted_config["release_plan"].get("category_ids", []),
                "minimum_cases_per_category": trusted_config["release_plan"].get(
                    "minimum_cases_per_category"
                ),
                "thresholds": trusted_config["release_thresholds"],
                "input_snapshot": trusted_snapshot,
            }
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, EvaluationError):
        trusted_release = None
    expected_runs = (
        len(trusted_release["pair_ids"]) * trusted_release["trials_per_pair"]
        if trusted_release is not None
        else None
    )
    release_plan_complete = (
        trusted_release is not None
        and evaluation_plan.get("mode") == "release"
        and trusted_release["dataset_role"] == "acceptance"
        and evaluation_plan.get("dataset_role") == trusted_release["dataset_role"]
        and evaluation_plan.get("config_schema_version") == trusted_release["config_schema_version"]
        and evaluation_plan.get("config_sha256") == trusted_release["config_sha256"]
        and evaluation_plan.get("required_pair_ids") == trusted_release["pair_ids"]
        and evaluation_plan.get("evaluated_pair_ids") == trusted_release["pair_ids"]
        and evaluation_plan.get("required_trials_per_pair") == trusted_release["trials_per_pair"]
        and evaluation_plan.get("actual_trials_per_pair") == trusted_release["trials_per_pair"]
        and evaluation_plan.get("required_category_ids") == trusted_release["category_ids"]
        and evaluation_plan.get("evaluated_category_ids") == trusted_release["category_ids"]
        and evaluation_plan.get("minimum_cases_per_category")
        == trusted_release["minimum_cases_per_category"]
        and thresholds == trusted_release["thresholds"]
        and evaluation_plan.get("input_snapshot") == trusted_release["input_snapshot"]
        and baseline.get("runs") == candidate.get("runs") == expected_runs
        and evaluation_plan.get("source_identity", {}).get("status") == "matched-clean-commit"
        and evaluation_plan.get("config_identity", {}).get("status") == "matched-canonical-commit"
    )
    gates.append(
        {
            "gate": "release-plan-completeness",
            "actual": evaluation_plan,
            "required": {
                "mode": "release",
                "dataset_role": "acceptance",
                "all_configured_pairs": True,
                "canonical_config_sha256": trusted_release["config_sha256"] if trusted_release else None,
                "exact_pair_ids": trusted_release["pair_ids"] if trusted_release else None,
                "exact_trials_per_pair": trusted_release["trials_per_pair"] if trusted_release else None,
                "exact_category_ids": trusted_release["category_ids"] if trusted_release else None,
                "minimum_cases_per_category": trusted_release["minimum_cases_per_category"] if trusted_release else None,
                "expected_runs_per_variant": expected_runs,
                "immutable_input_snapshot": trusted_release["input_snapshot"] if trusted_release else None,
                "matched_clean_commit": True,
                "matched_canonical_config": True,
            },
            "status": "passed" if release_plan_complete else "not-evaluable",
        }
    )

    if infrastructure is not None:
        policy = evaluation_plan.get("infrastructure_policy", {})
        maximum_retries = policy.get("maximum_timeout_retries")
        retry_integrity = (
            isinstance(maximum_retries, int)
            and not isinstance(maximum_retries, bool)
            and maximum_retries in {0, 1}
            and infrastructure.get("maximum_attempts_per_call", 0) <= maximum_retries + 1
            and infrastructure.get("unexpected_retries") == 0
            and infrastructure.get("exhausted_timeouts") == 0
            and infrastructure.get("exhausted_infrastructure") == 0
        )
        gates.append(
            {
                "gate": "infrastructure-retry-integrity",
                "actual": infrastructure,
                "required": {
                    "maximum_attempts_per_call": maximum_retries + 1
                    if isinstance(maximum_retries, int) and not isinstance(maximum_retries, bool)
                    else None,
                    "unexpected_retries": 0,
                    "exhausted_timeouts": 0,
                    "exhausted_infrastructure": 0,
                    "first_failures_retained": True,
                },
                "status": "passed" if retry_integrity else "failed",
            }
        )

    complete = all(
        aggregate["runs"] == aggregate["valid_executor_runs"] == aggregate["valid_grader_runs"]
        for aggregate in (baseline, candidate)
    )
    gates.append(
        {
            "gate": "evaluation-completeness",
            "actual": {
                "baseline": {
                    "runs": baseline["runs"],
                    "valid_executor_runs": baseline["valid_executor_runs"],
                    "valid_grader_runs": baseline["valid_grader_runs"],
                },
                "candidate": {
                    "runs": candidate["runs"],
                    "valid_executor_runs": candidate["valid_executor_runs"],
                    "valid_grader_runs": candidate["valid_grader_runs"],
                },
            },
            "required": {"all_planned_runs_valid": True},
            "status": "passed" if complete else "failed",
        }
    )

    def minimum(name: str, actual: float | None, required: float) -> None:
        gates.append(
            {
                "gate": name,
                "actual": actual,
                "required": {"minimum": required},
                "status": "not-evaluable" if actual is None else "passed" if actual >= required else "failed",
            }
        )

    def maximum(name: str, actual: float | None, required: float) -> None:
        gates.append(
            {
                "gate": name,
                "actual": actual,
                "required": {"maximum": required},
                "status": "not-evaluable" if actual is None else "passed" if actual <= required else "failed",
            }
        )

    candidate_metrics = candidate["contract_metrics"]
    baseline_metrics = baseline["contract_metrics"]
    minimum("candidate-pass-rate", candidate["pass_rate"], thresholds["minimum_candidate_pass_rate"])
    minimum(
        "candidate-requirement-fidelity",
        candidate_metrics["requirement_fidelity"]["mean"],
        thresholds["minimum_candidate_requirement_fidelity"],
    )
    minimum(
        "candidate-ordinary-defect-retention",
        candidate_metrics["ordinary_defect_retention"]["mean"],
        thresholds["minimum_candidate_ordinary_defect_retention"],
    )
    maximum(
        "candidate-unsafe-actions",
        candidate_metrics["unsafe_actions"]["mean"],
        thresholds["maximum_candidate_unsafe_actions"],
    )
    maximum(
        "candidate-false-block-rate",
        candidate_metrics["false_block_rate"]["mean"],
        thresholds["maximum_candidate_false_block_rate"],
    )
    minimum(
        "requirement-fidelity-delta",
        numeric_delta(
            candidate_metrics["requirement_fidelity"]["mean"],
            baseline_metrics["requirement_fidelity"]["mean"],
        ),
        thresholds["minimum_requirement_fidelity_delta"],
    )
    minimum(
        "ordinary-defect-retention-delta",
        numeric_delta(
            candidate_metrics["ordinary_defect_retention"]["mean"],
            baseline_metrics["ordinary_defect_retention"]["mean"],
        ),
        thresholds["minimum_ordinary_defect_retention_delta"],
    )
    candidate_context = candidate_metrics["context_cost"]["mean"]
    baseline_context = baseline_metrics["context_cost"]["mean"]
    if candidate_context is not None and baseline_context is not None and baseline_context == 0 < candidate_context:
        gates.append(
            {
                "gate": "context-cost-ratio",
                "actual": {"candidate": candidate_context, "baseline": baseline_context},
                "required": {"maximum": thresholds["maximum_context_cost_ratio"]},
                "status": "failed",
            }
        )
    else:
        ratio = None
        if candidate_context is not None and baseline_context is not None:
            ratio = 1.0 if baseline_context == candidate_context == 0 else candidate_context / baseline_context
        maximum("context-cost-ratio", ratio, thresholds["maximum_context_cost_ratio"])

    if category_aggregates is not None:
        expected_categories = evaluation_plan.get("evaluated_category_ids", [])
        category_set_matches = (
            isinstance(expected_categories, list)
            and list(category_aggregates) == expected_categories
        )
        gates.append(
            {
                "gate": "category-set-completeness",
                "actual": list(category_aggregates),
                "required": expected_categories,
                "status": "passed" if category_set_matches else "failed",
            }
        )
        for category in expected_categories if isinstance(expected_categories, list) else []:
            aggregate_pair = category_aggregates.get(category)
            if not isinstance(aggregate_pair, dict):
                gates.append(
                    {
                        "gate": f"category-quality:{category}",
                        "actual": None,
                        "required": thresholds,
                        "status": "failed",
                    }
                )
                continue
            category_baseline = aggregate_pair["baseline"]
            category_candidate = aggregate_pair["candidate"]
            checks, context_ratio = aggregate_threshold_checks(
                category_candidate,
                category_baseline,
                thresholds,
            )
            gate_status = "not-evaluable" if any(value is None for value in checks.values()) else (
                "passed" if all(checks.values()) else "failed"
            )
            gates.append(
                {
                    "gate": f"category-quality:{category}",
                    "actual": {
                        "checks": checks,
                        "candidate": category_candidate,
                        "baseline": category_baseline,
                        "context_cost_ratio": context_ratio,
                    },
                    "required": thresholds,
                    "status": gate_status,
                }
            )
    threshold_gates = [item for item in gates if item["gate"] != "release-plan-completeness"]
    model_gate_ready = bool(gates) and all(item["status"] == "passed" for item in gates)
    return {
        "model_gate_ready": model_gate_ready,
        "release_ready": False,
        "release_ready_reason": (
            "This runner measures bounded first-attempt engineering-plan quality only; "
            "repository verification, independent review, and release lifecycle evidence remain external gates."
        ),
        "pilot_thresholds_passed": bool(threshold_gates)
        and all(item["status"] == "passed" for item in threshold_gates),
        "mode": evaluation_plan.get("mode"),
        "gates": gates,
        "policy": "quality and safety floors are mandatory; context cost is a secondary bounded constraint",
        "scope": "paired-model-plan-gate-only",
    }


def source_identity(expected_commit: str | None) -> dict[str, Any]:
    observed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    status = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=normal"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    observed_commit = observed.stdout.strip() if observed.returncode == 0 else None
    clean = status.returncode == 0 and not status.stdout.strip()
    matched = bool(expected_commit) and observed_commit == expected_commit and clean
    return {
        "expected_commit": expected_commit,
        "observed_commit": observed_commit,
        "clean_worktree": clean,
        "status": "matched-clean-commit" if matched else "not-release-bound",
    }


def config_identity(config_path: Path, expected_digest: str, expected_commit: str | None) -> dict[str, Any]:
    observed_digest: str | None = None
    try:
        current_bytes = config_path.read_bytes()
        observed_digest = "sha256:" + hashlib.sha256(current_bytes).hexdigest()
    except OSError:
        current_bytes = None
    canonical = not config_path.is_symlink() and config_path.resolve() == CANONICAL_CONFIG.resolve()
    canonical_relative = CANONICAL_CONFIG.relative_to(ROOT).as_posix()
    committed = subprocess.run(
        ["git", "show", f"{expected_commit}:{canonical_relative}"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    ) if expected_commit else None
    matched = (
        canonical
        and current_bytes is not None
        and observed_digest == expected_digest
        and committed is not None
        and committed.returncode == 0
        and committed.stdout == current_bytes
    )
    return {
        "expected_commit": expected_commit,
        "expected_sha256": expected_digest,
        "observed_sha256": observed_digest,
        "canonical_path": str(CANONICAL_CONFIG),
        "observed_path": str(config_path.resolve()),
        "status": "matched-canonical-commit" if matched else "not-release-bound",
    }


def finalize_release_identity(
    evaluation_plan: dict[str, Any],
    *,
    config_path: Path,
    config_digest: str,
    expected_commit: str,
) -> list[str]:
    postflight_source = source_identity(expected_commit)
    postflight_config = config_identity(config_path, config_digest, expected_commit)
    source = evaluation_plan["source_identity"]
    config = evaluation_plan["config_identity"]
    source["postflight"] = postflight_source
    config["postflight"] = postflight_config
    source_matched = all(
        snapshot["status"] == "matched-clean-commit"
        for snapshot in (source["preflight"], postflight_source)
    )
    config_matched = all(
        snapshot["status"] == "matched-canonical-commit"
        for snapshot in (config["preflight"], postflight_config)
    )
    source["status"] = "matched-clean-commit" if source_matched else "source-drift-detected"
    config["status"] = "matched-canonical-commit" if config_matched else "config-drift-detected"
    errors: list[str] = []
    if not source_matched:
        errors.append("release source identity changed during evaluation")
    if not config_matched:
        errors.append("release config identity changed during evaluation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    executor_modes = parser.add_mutually_exclusive_group()
    executor_modes.add_argument("--executor", help="Quoted legacy single-pass executor command")
    executor_modes.add_argument("--executor-draft", help="Quoted blind first-stage draft command")
    parser.add_argument("--executor-assembler", help="Quoted blind second-stage assembler command")
    parser.add_argument("--grader", required=True, help="Quoted independent grader command; receives one blind JSON request on stdin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--config",
        type=Path,
        help="Evaluation config; defaults to the development set, or the frozen acceptance set with --release",
    )
    parser.add_argument("--pair", action="append", default=[])
    parser.add_argument("--category", action="append", default=[])
    parser.add_argument("--trials", type=int)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument(
        "--infrastructure-retries",
        type=int,
        default=0,
        help="Retry a typed timeout or adapter-declared transport/service failure at most once; content and quality failures are never retried",
    )
    parser.add_argument(
        "--stop-on-first-candidate-fail",
        action="store_true",
        help="Diagnostic-only: stop before the next model call after a complete candidate strict failure",
    )
    parser.add_argument("--seed", type=int, default=0)
    identity_mode = parser.add_mutually_exclusive_group()
    identity_mode.add_argument(
        "--release",
        action="store_true",
        help="Enable the frozen full-release plan; never use for a pilot",
    )
    identity_mode.add_argument(
        "--attested-pilot",
        action="store_true",
        help="Bind approved evaluator identity for a filtered development pilot; never claims release",
    )
    parser.add_argument("--expected-commit", help="Full lowercase commit SHA required with --release")
    args = parser.parse_args()
    config_path = args.config or (CANONICAL_CONFIG if args.release else DEVELOPMENT_CONFIG)

    if args.timeout < 1:
        parser.error("--timeout must be positive")
    if args.infrastructure_retries not in {0, 1}:
        parser.error("--infrastructure-retries must be zero or one")
    try:
        config_bytes = config_path.read_bytes()
        config = validate_config(json.loads(config_bytes.decode("utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.error(f"cannot load paired evaluation config: {exc}")
    except EvaluationError as exc:
        parser.error(str(exc))
    trials = args.trials if args.trials is not None else config.get("default_trials", 3)
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 3:
        parser.error("paired evaluations require at least three independent trials")
    try:
        executor_command = bind_bundled_adapter_command(split_program_command(args.executor or args.executor_draft or ""))
        assembler_command = bind_bundled_adapter_command(
            split_program_command(args.executor_assembler or "")
        )
        grader_command = bind_bundled_adapter_command(split_program_command(args.grader))
    except EvaluationError as exc:
        parser.error(str(exc))
    two_stage = config["schema_version"] in {"1.7", "1.8"}
    inventory_stage = config["schema_version"] == "1.8"
    if two_stage:
        if args.executor is not None or not executor_command or not assembler_command:
            parser.error(
                f"schema {config['schema_version']} requires --executor-draft and --executor-assembler; legacy --executor is invalid"
            )
    elif args.executor is None or args.executor_assembler is not None:
        parser.error("schema 1.0 through 1.6 require legacy --executor only")
    if not executor_command or not grader_command:
        parser.error("executor and grader commands must not be empty")
    if args.stop_on_first_candidate_fail and (
        not args.attested_pilot or not inventory_stage
    ):
        parser.error(
            "--stop-on-first-candidate-fail requires a filtered schema 1.8 attested development pilot"
        )
    evaluator_identities: dict[str, dict[str, Any]] = {}
    backend_identity: dict[str, Any] | None = None
    evaluator_label = "release evaluator" if args.release else "attested pilot evaluator"
    identity_bound = args.release or args.attested_pilot
    selected_ids = set(args.pair)
    selected_categories = set(args.category)
    pairs = [
        item
        for item in config.get("pairs", [])
        if (not selected_ids or item.get("id") in selected_ids)
        and (not selected_categories or pair_category(item) in selected_categories)
    ]
    missing = selected_ids - {item.get("id") for item in pairs}
    if missing:
        parser.error(f"unknown pair ids: {sorted(missing)}")
    configured_categories = {pair_category(item) for item in config.get("pairs", [])}
    missing_categories = selected_categories - configured_categories
    if missing_categories:
        parser.error(f"unknown category ids: {sorted(missing_categories)}")
    if not pairs:
        parser.error("no paired evaluation cases were selected")
    release_plan = config.get("release_plan") or {
        "pair_ids": [item["id"] for item in config["pairs"]],
        "trials_per_pair": config["default_trials"],
        "category_ids": list(dict.fromkeys(pair_category(item) for item in config["pairs"])),
        "minimum_cases_per_category": None,
    }
    if args.release:
        if args.infrastructure_retries:
            parser.error("--release requires zero infrastructure retries")
        if config_path.is_symlink() or config_path.resolve() != CANONICAL_CONFIG.resolve():
            parser.error(f"--release requires the canonical config at {CANONICAL_CONFIG}")
        if args.pair or args.category:
            parser.error("--release requires the complete configured pair/category set; filters are not allowed")
        if config["schema_version"] != "1.6" or config.get("dataset_role") != "acceptance":
            parser.error("--release requires canonical paired evaluation config schema 1.6 with dataset_role acceptance")
        if trials != release_plan["trials_per_pair"]:
            parser.error(f"--release requires exactly {release_plan['trials_per_pair']} trials per pair")
        if not isinstance(args.expected_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", args.expected_commit):
            parser.error("--release requires --expected-commit as a full lowercase 40-character SHA")
        try:
            evaluator_identities = {
                "executor": validate_release_evaluator_command(
                    executor_command,
                    "executor",
                    config["release_evaluators"],
                ),
                "grader": validate_release_evaluator_command(
                    grader_command,
                    "grader",
                    config["release_evaluators"],
                ),
            }
            backend_identity = resolve_release_backend_identity(
                config["release_evaluators"],
                evaluator_label=evaluator_label,
            )
            for identity in evaluator_identities.values():
                identity["backend"] = backend_identity
            executor_command = bind_release_backend(executor_command, backend_identity)
            grader_command = bind_release_backend(grader_command, backend_identity)
        except EvaluationError as exc:
            parser.error(str(exc))
    elif args.attested_pilot:
        if (
            config["schema_version"] not in {"1.6", "1.7", "1.8"}
            or config.get("dataset_role") != "development"
        ):
            parser.error("--attested-pilot requires schema 1.6, 1.7, or 1.8 development config")
        if not (args.pair or args.category) or len(pairs) >= len(config["pairs"]):
            parser.error("--attested-pilot is only valid for a filtered development pilot")
        if "evaluator_identity" not in config:
            parser.error("--attested-pilot requires evaluator_identity in the development config")
        try:
            if two_stage:
                evaluator_identities = {
                    ("inventory" if inventory_stage else "draft"): validate_release_evaluator_command(
                        executor_command,
                        "inventory" if inventory_stage else "draft",
                        config["evaluator_identity"],
                        evaluator_label=evaluator_label,
                    ),
                    "assembler": validate_release_evaluator_command(
                        assembler_command, "assembler", config["evaluator_identity"], evaluator_label=evaluator_label
                    ),
                    "grader": validate_release_evaluator_command(
                        grader_command, "grader", config["evaluator_identity"], evaluator_label=evaluator_label
                    ),
                }
            else:
                evaluator_identities = {
                    "executor": validate_release_evaluator_command(
                        executor_command,
                        "executor",
                        config["evaluator_identity"],
                        evaluator_label=evaluator_label,
                    ),
                    "grader": validate_release_evaluator_command(
                        grader_command,
                        "grader",
                        config["evaluator_identity"],
                        evaluator_label=evaluator_label,
                    ),
                }
            backend_identity = resolve_release_backend_identity(
                config["evaluator_identity"],
                evaluator_label=evaluator_label,
            )
            for identity in evaluator_identities.values():
                identity["backend"] = backend_identity
            executor_command = bind_release_backend(executor_command, backend_identity)
            if two_stage:
                assembler_command = bind_release_backend(assembler_command, backend_identity)
            grader_command = bind_release_backend(grader_command, backend_identity)
            if inventory_stage:
                grader_command = [*grader_command, "--receipt-schema-version", "1.2"]
        except EvaluationError as exc:
            parser.error(str(exc))
    if not args.release and args.expected_commit is not None:
        parser.error("--expected-commit is only valid with --release")
    if two_stage and not args.attested_pilot:
        parser.error(f"schema {config['schema_version']} blind pipeline requires --attested-pilot")
    evaluated_pair_ids = [item["id"] for item in pairs]
    evaluated_category_ids = list(dict.fromkeys(pair_category(item) for item in pairs))
    config_digest = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
    preflight_source = source_identity(args.expected_commit)
    preflight_config = config_identity(config_path, config_digest, args.expected_commit)
    evaluation_plan = {
        "mode": (
            "release"
            if args.release
            else ("attested-pilot" if args.attested_pilot else "pilot")
        ),
        "config_schema_version": config["schema_version"],
        "dataset_role": config.get("dataset_role", "legacy"),
        "required_pair_ids": release_plan["pair_ids"],
        "evaluated_pair_ids": evaluated_pair_ids,
        "required_category_ids": release_plan.get("category_ids", []),
        "evaluated_category_ids": evaluated_category_ids,
        "minimum_cases_per_category": release_plan.get("minimum_cases_per_category"),
        "required_trials_per_pair": release_plan["trials_per_pair"],
        "actual_trials_per_pair": trials,
        "config_sha256": config_digest,
        "evaluator_identity": (
            {
                "status": (
                    "matched-approved-first-party"
                    if args.release
                    else "matched-attested-development"
                ),
                **evaluator_identities,
            }
            if identity_bound
            else {"status": "pilot-unbound"}
        ),
        "infrastructure_policy": {
            "timeout_seconds": args.timeout,
            "maximum_timeout_retries": args.infrastructure_retries,
            "maximum_infrastructure_retries": args.infrastructure_retries,
            "retryable_error_kinds": ["timeout", "infrastructure"],
            "content_or_quality_retries": 0,
        },
        "early_stop_policy": {
            "enabled": args.stop_on_first_candidate_fail,
            "trigger": "complete-candidate-strict-fail",
            "release_eligible": False if args.stop_on_first_candidate_fail else True,
        },
        "source_identity": {
            "status": "pending-postflight" if args.release else "not-release-bound",
            "preflight": preflight_source,
        },
        "config_identity": {
            "status": "pending-postflight" if args.release else "not-release-bound",
            "preflight": preflight_config,
        },
    }
    if args.release and preflight_source["status"] != "matched-clean-commit":
        parser.error("--release requires --expected-commit to match HEAD and a clean worktree")
    if args.release and preflight_config["status"] != "matched-canonical-commit":
        parser.error("--release requires the canonical config bytes from --expected-commit")
    try:
        input_values, input_snapshot = evaluation_input_snapshot(
            config,
            args.expected_commit if args.release else None,
        )
    except EvaluationError as exc:
        parser.error(str(exc))
    evaluation_plan["input_snapshot"] = input_snapshot
    semantic_protocol = {
        "model_result_schema_version": MODEL_RESULT_SCHEMA_VERSION,
        "grader_request_schema_version": GRADER_REQUEST_SCHEMA_VERSION,
        "grader_executor_dto": "content-only-v1",
        "grader_executor_fields": list(GRADER_EXECUTOR_KEYS),
        "claim_kind_alignment": (
            "registry-owner-kind-v2"
            if input_snapshot["kind_alignment_enforced"]
            else "legacy-vocabulary-no-alignment"
        ),
        "support_protocol": (
            "work-unit-facet-exact-span-v3"
            if config["schema_version"] in {"1.6", "1.7", "1.8"}
            else "legacy-whole-claim"
        ),
        "claim_owner_vocabulary_sha256": input_snapshot["claim_owner_vocabulary_sha256"],
        "claim_kind_vocabulary_sha256": input_snapshot["claim_kind_vocabulary_sha256"],
        "executor_pipeline": (
            config["executor_pipeline"] if two_stage else {"protocol": "single-pass-v1"}
        ),
    }
    semantic_protocol_sha256 = canonical_json_sha256(semantic_protocol)
    evaluation_plan["semantic_protocol"] = semantic_protocol
    evaluation_plan["semantic_protocol_sha256"] = semantic_protocol_sha256
    output = args.output.resolve()
    if args.output.is_symlink():
        parser.error(f"--output must not be a symlink: {args.output}")
    if output.exists():
        if not output.is_dir():
            parser.error(f"--output must be a directory: {output}")
        if any(output.iterdir()):
            parser.error(f"--output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    random.Random(args.seed).shuffle(pairs)

    records: list[dict[str, Any]] = []
    errors: list[str] = []
    infrastructure_circuit_open = False
    semantic_early_stop = False
    expected_records = len(pairs) * trials * len(VARIANTS)
    last_progress_record: dict[str, Any] | None = None
    active_stage: str | None = None

    def write_progress(status: str, last_record: dict[str, Any] | None = None) -> None:
        write_json(
            output / "progress.json",
            {
                "schema_version": PROGRESS_SCHEMA_VERSION,
                "status": status,
                "mode": evaluation_plan["mode"],
                "seed": args.seed,
                "trials_per_pair": trials,
                "dataset_role": config.get("dataset_role", "legacy"),
                "config_sha256": config_digest,
                "input_snapshot_sha256": input_snapshot["sha256"],
                "semantic_protocol_sha256": semantic_protocol_sha256,
                "completed_records": len(records),
                "expected_records": expected_records,
                "failed_records": sum(
                    1 for record in records if record["executor_error"] or record["grader_error"]
                ),
                "active_stage": active_stage,
                "last_record": last_record if last_record is not None else last_progress_record,
            },
        )

    write_progress("running")
    for pair in pairs:
        if infrastructure_circuit_open:
            break
        pair_id = pair["id"]
        fixture = input_values[pair_id]["fixture"]
        for trial in range(1, trials + 1):
            if infrastructure_circuit_open:
                break
            order = VARIANTS if trial % 2 else tuple(reversed(VARIANTS))
            for variant in order:
                if infrastructure_circuit_open:
                    break
                pipeline_state = (
                    "InventoryPending"
                    if inventory_stage
                    else "DraftPending"
                    if two_stage
                    else "AssemblyPending"
                )
                pipeline_transitions = [pipeline_state]
                draft_request: dict[str, Any] | None = None
                assembly_request: dict[str, Any] | None = None
                draft: dict[str, Any] | None = None
                draft_receipt: dict[str, Any] | None = None
                draft_attempts: list[dict[str, Any]] = []
                draft_root: Path | None = None
                assembly_root: Path | None = None
                assembler_receipt: dict[str, Any] | None = None
                assembler_attempts: list[dict[str, Any]] = []
                assembly_manifest: dict[str, Any] | None = None
                lineage_summary: dict[str, Any] | None = None
                executor: dict[str, Any] | None = None
                executor_receipt: dict[str, Any] | None = None
                executor_attempts: list[dict[str, Any]] = []
                executor_error: str | None = None
                runner_elapsed = 0.0
                if two_stage:
                    draft_root = contained_path(
                        output,
                        Path("model-runs") / uuid.uuid4().hex,
                        label="opaque draft run root",
                        require_relative=True,
                        reject_symlinks=True,
                    )
                    draft_request = (
                        build_inventory_stage_request(
                            pair_id=pair_id,
                            variant=variant,
                            pair_capabilities=pair["capabilities"],
                            input_value=input_values[pair_id],
                        )
                        if inventory_stage
                        else build_executor_stage_request(
                            pair_id=pair_id,
                            variant=variant,
                            pair_capabilities=pair["capabilities"],
                            input_value=input_values[pair_id],
                        )
                    )
                    draft_nonce = uuid.uuid4().hex
                    active_stage = "inventory" if inventory_stage else "draft"
                    write_progress("running")
                    draft_outcome, draft_attempts = run_bound_program_with_infrastructure_retry(
                        command_with_call_nonce(executor_command, draft_nonce),
                        draft_request,
                        draft_root,
                        args.timeout,
                        args.infrastructure_retries,
                        backend_identity=backend_identity,
                        evaluator_label=evaluator_label,
                        attempt_receipt_validator=lambda outcome: validate_bound_attempt_receipt(
                            outcome,
                            evaluator_identities["inventory" if inventory_stage else "draft"],
                            request=draft_request,
                            call_nonce=draft_nonce,
                            draft=None,
                            evaluator_label=evaluator_label,
                        ),
                    )
                    runner_elapsed += sum(item["elapsed_seconds"] for item in draft_attempts)
                    executor_error = draft_outcome.error
                    if executor_error is None:
                        try:
                            draft_receipt = validate_release_model_receipt(
                                draft_outcome.run_root,
                                evaluator_identities["inventory" if inventory_stage else "draft"],
                                evaluator_label=evaluator_label,
                                request=draft_request,
                                call_nonce=draft_nonce,
                            )
                            if inventory_stage:
                                draft = validate_inventory_result(draft_outcome.result, pair_id)
                                validate_inventory_evidence_refs(
                                    draft,
                                    fixture=input_values[pair_id]["fixture"],
                                    task_prompt=draft_request["task_prompt"],
                                )
                            else:
                                draft = validate_executor(
                                    draft_outcome.result,
                                    draft_outcome.run_root,
                                    pair_id,
                                    input_values[pair_id]["claim_owner_vocabulary"],
                                    input_values[pair_id]["claim_kind_vocabulary"],
                                    enforce_kind_alignment=input_values[pair_id]["kind_alignment_enforced"],
                                )
                            write_json(draft_outcome.run_root / "result.json", draft)
                            pipeline_state = "InventoryValidated" if inventory_stage else "DraftValidated"
                            pipeline_transitions.append(pipeline_state)
                        except (EvaluationError, OSError, PathContractError) as exc:
                            executor_error = str(exc)
                    if draft is not None:
                        pipeline_state = "AssemblyPending"
                        pipeline_transitions.append(pipeline_state)
                        assembly_root = contained_path(
                            output,
                            Path("model-runs") / uuid.uuid4().hex,
                            label="opaque assembly run root",
                            require_relative=True,
                            reject_symlinks=True,
                        )
                        assembly_request = (
                            build_inventory_assembler_request(
                                draft_request,
                                draft,
                                claim_owner_vocabulary=input_values[pair_id]["claim_owner_vocabulary"],
                                claim_kind_vocabulary=input_values[pair_id]["claim_kind_vocabulary"],
                            )
                            if inventory_stage
                            else build_assembler_request(draft_request, draft)
                        )
                        assembly_nonce = uuid.uuid4().hex
                        active_stage = "assembler"
                        write_progress("running")
                        assembly_outcome, assembler_attempts = run_bound_program_with_infrastructure_retry(
                            command_with_call_nonce(assembler_command, assembly_nonce),
                            assembly_request,
                            assembly_root,
                            args.timeout,
                            args.infrastructure_retries,
                            backend_identity=backend_identity,
                            evaluator_label=evaluator_label,
                            attempt_receipt_validator=lambda outcome: validate_bound_attempt_receipt(
                                outcome,
                                evaluator_identities["assembler"],
                                request=assembly_request,
                                call_nonce=assembly_nonce,
                                draft=(draft if inventory_stage else sanitized_executor_for_grader(draft)),
                                evaluator_label=evaluator_label,
                            ),
                        )
                        runner_elapsed += sum(item["elapsed_seconds"] for item in assembler_attempts)
                        executor_error = assembly_outcome.error
                        if executor_error is None:
                            try:
                                assembler_receipt = validate_release_model_receipt(
                                    assembly_outcome.run_root,
                                    evaluator_identities["assembler"],
                                    evaluator_label=evaluator_label,
                                    request=assembly_request,
                                    call_nonce=assembly_nonce,
                                    draft=(draft if inventory_stage else sanitized_executor_for_grader(draft)),
                                )
                                if inventory_stage:
                                    assembly_manifest = validate_assembly_manifest(
                                        assembly_outcome.result,
                                        pair_id,
                                    )
                                    materialized, lineage_summary = materialize_inventory_claims(
                                        draft,
                                        assembly_manifest,
                                        claim_owner_vocabulary=input_values[pair_id]["claim_owner_vocabulary"],
                                        claim_kind_vocabulary=input_values[pair_id]["claim_kind_vocabulary"],
                                    )
                                    executor = validate_executor(
                                        materialized,
                                        assembly_outcome.run_root,
                                        pair_id,
                                        input_values[pair_id]["claim_owner_vocabulary"],
                                        input_values[pair_id]["claim_kind_vocabulary"],
                                        enforce_kind_alignment=input_values[pair_id]["kind_alignment_enforced"],
                                    )
                                else:
                                    executor = validate_executor(
                                        assembly_outcome.result,
                                        assembly_outcome.run_root,
                                        pair_id,
                                        input_values[pair_id]["claim_owner_vocabulary"],
                                        input_values[pair_id]["claim_kind_vocabulary"],
                                        enforce_kind_alignment=input_values[pair_id]["kind_alignment_enforced"],
                                    )
                                    validate_monotonic_assembly(draft, executor)
                                combined_usage = aggregate_stage_usage(draft_receipt, assembler_receipt)
                                executor["usage"]["tokens"] = combined_usage["tokens"]
                                executor["usage"]["elapsed_seconds"] = runner_elapsed
                                write_json(assembly_outcome.run_root / "result.json", executor)
                                pipeline_state = "FinalValidated"
                                pipeline_transitions.append(pipeline_state)
                            except (EvaluationError, OSError, PathContractError) as exc:
                                executor_error = str(exc)
                                executor = None
                        executor_attempts = assembler_attempts
                        executor_receipt = assembler_receipt
                        executor_outcome = assembly_outcome
                    else:
                        executor_outcome = draft_outcome
                else:
                    run_root = contained_path(
                        output,
                        Path(pair_id) / f"trial-{trial}" / variant / "executor",
                        label="executor run root",
                        require_relative=True,
                        reject_symlinks=True,
                    )
                    request = executor_request(
                        pair_id=pair_id,
                        trial=trial,
                        variant=variant,
                        pair_capabilities=pair["capabilities"],
                        input_value=input_values[pair_id],
                    )
                    executor_outcome, executor_attempts = run_bound_program_with_infrastructure_retry(
                        executor_command,
                        request,
                        run_root,
                        args.timeout,
                        args.infrastructure_retries,
                        backend_identity=backend_identity,
                        evaluator_label=evaluator_label,
                    )
                    executor_error = executor_outcome.error
                    runner_elapsed = sum(item["elapsed_seconds"] for item in executor_attempts)
                    if executor_error is None:
                        try:
                            if identity_bound:
                                executor_receipt = validate_release_model_receipt(
                                    executor_outcome.run_root,
                                    evaluator_identities["executor"],
                                    evaluator_label=evaluator_label,
                                )
                            executor = validate_executor(
                                executor_outcome.result,
                                executor_outcome.run_root,
                                pair_id,
                                input_values[pair_id]["claim_owner_vocabulary"],
                                input_values[pair_id]["claim_kind_vocabulary"],
                                enforce_kind_alignment=input_values[pair_id]["kind_alignment_enforced"],
                            )
                            write_json(executor_outcome.run_root / "result.json", executor)
                            pipeline_state = "FinalValidated"
                            pipeline_transitions.append(pipeline_state)
                        except (EvaluationError, OSError, PathContractError) as exc:
                            executor_error = str(exc)
                grader: dict[str, Any] | None = None
                grader_error: str | None = None
                grader_elapsed: float | None = None
                grader_archive: Path | None = None
                grader_terminal_run_root: Path | None = None
                grader_attempts: list[dict[str, Any]] = []
                grader_receipt: dict[str, Any] | None = None
                grader_input_sha256: str | None = None
                grader_request: dict[str, Any] | None = None
                if executor is not None:
                    grader_id = uuid.uuid4().hex
                    grader_archive = contained_path(
                        output,
                        Path("grader-runs") / grader_id,
                        label="grader archive root",
                        require_relative=True,
                        reject_symlinks=True,
                    )
                    with tempfile.TemporaryDirectory(prefix="dev-flow-blind-grader-") as grader_temp:
                        grader_root = Path(grader_temp) / grader_id
                        try:
                            grader_request = build_grader_request(
                                pair_id=pair_id,
                                fixture=fixture,
                                deterministic_oracle=pair["deterministic_oracle"],
                                executor=executor,
                                contract=input_values[pair_id]["contract"],
                            )
                            grader_input_sha256 = canonical_json_sha256(grader_request)
                        except (EvaluationError, TypeError, ValueError) as exc:
                            grader_error = f"cannot construct sanitized grader request: {exc}"
                        else:
                            grader_nonce = uuid.uuid4().hex if two_stage else None
                            active_stage = "grader"
                            write_progress("running")
                            grader_outcome, grader_attempts = run_bound_program_with_infrastructure_retry(
                                (
                                    command_with_call_nonce(grader_command, grader_nonce)
                                    if grader_nonce is not None
                                    else grader_command
                                ),
                                grader_request,
                                grader_root,
                                args.timeout,
                                args.infrastructure_retries,
                                backend_identity=backend_identity,
                                evaluator_label=evaluator_label,
                                attempt_receipt_validator=(
                                    lambda outcome: validate_bound_attempt_receipt(
                                        outcome,
                                        evaluator_identities["grader"],
                                        request=grader_request,
                                        call_nonce=grader_nonce,
                                        draft=None,
                                        evaluator_label=evaluator_label,
                                    )
                                    if two_stage and grader_nonce is not None
                                    else None
                                ),
                            )
                            raw_grader = grader_outcome.result
                            grader_error = grader_outcome.error
                            grader_elapsed = sum(attempt["elapsed_seconds"] for attempt in grader_attempts)
                            if grader_error is None:
                                try:
                                    if identity_bound:
                                        grader_receipt = validate_release_model_receipt(
                                            grader_outcome.run_root,
                                            evaluator_identities["grader"],
                                            evaluator_label=evaluator_label,
                                            request=grader_request if two_stage else None,
                                            call_nonce=grader_nonce,
                                        )
                                    contract = input_values[pair_id]["contract"]
                                    grader_obligations: list[dict[str, Any]] | int | None = None
                                    if contract is not None:
                                        grader_obligations = (
                                            contract["work_units"]
                                            if "work_units" in contract
                                            else (
                                                contract["obligations"]
                                                if "obligations" in contract
                                                else len(contract["expected_actions"])
                                            )
                                        )
                                    grader = validate_grader(
                                        raw_grader,
                                        pair_id,
                                        grader_obligations,
                                        executor["claims"],
                                    )
                                    write_json(grader_outcome.run_root / "result.json", grader)
                                    pipeline_state = "Graded"
                                    pipeline_transitions.append(pipeline_state)
                                except (EvaluationError, OSError, PathContractError) as exc:
                                    grader_error = str(exc)
                                    try:
                                        atomic_write_text(
                                            grader_outcome.run_root / "runner-error.txt",
                                            grader_error + "\n",
                                        )
                                    except (OSError, PathContractError):
                                        pass
                        try:
                            grader_archive.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copytree(grader_root, grader_archive)
                            if grader_attempts:
                                grader_terminal_run_root = grader_archive / grader_outcome.run_root.relative_to(
                                    grader_root
                                )
                                grader_attempts = rebase_attempt_roots(
                                    grader_attempts,
                                    grader_root,
                                    grader_archive,
                                )
                        except OSError as exc:
                            grader_error = grader_error or f"cannot archive grader evidence: {exc}"
                aggregate_usage = (
                    aggregate_stage_usage(draft_receipt, assembler_receipt)
                    if two_stage
                    else {
                        "tokens": (
                            executor["usage"]["tokens"]
                            if executor is not None and isinstance(executor["usage"]["tokens"], int)
                            else 0
                        ),
                        "token_usage": (
                            executor_receipt["token_usage"] if executor_receipt is not None else {}
                        ),
                    }
                )
                draft_content = (
                    draft
                    if inventory_stage and draft is not None
                    else sanitized_executor_for_grader(draft)
                    if draft is not None
                    else None
                )
                final_content = sanitized_executor_for_grader(executor) if executor is not None else None
                hash_chain = {
                    "draft_request_sha": (
                        canonical_json_sha256(draft_request) if draft_request is not None else None
                    ),
                    "draft_content_sha": (
                        canonical_json_sha256(draft_content) if draft_content is not None else None
                    ),
                    "assembler_request_sha": (
                        canonical_json_sha256(assembly_request) if assembly_request is not None else None
                    ),
                    "assembler_result_sha": (
                        canonical_json_sha256(assembly_manifest)
                        if inventory_stage and assembly_manifest is not None
                        else canonical_json_sha256(final_content)
                        if two_stage and final_content is not None
                        else None
                    ),
                    "materialized_final_sha": (
                        canonical_json_sha256(final_content)
                        if inventory_stage and final_content is not None
                        else None
                    ),
                    "grader_request_sha": (
                        canonical_json_sha256(grader_request) if grader_request is not None else None
                    ),
                }
                hash_chain["pipeline_sha"] = canonical_json_sha256(hash_chain)
                pipeline_stages = {
                    "protocol": (
                        INVENTORY_PIPELINE_PROTOCOL
                        if inventory_stage
                        else BLIND_PIPELINE_PROTOCOL
                        if two_stage
                        else "single-pass-v1"
                    ),
                    "state": pipeline_state,
                    "state_transitions": pipeline_transitions,
                    "draft": pipeline_stage_evidence(
                        identity=evaluator_identities.get("inventory" if inventory_stage else "draft"),
                        request=draft_request,
                        result=draft_content,
                        receipt=draft_receipt,
                        attempts=draft_attempts,
                        archive=draft_root,
                    ),
                    "assembly": pipeline_stage_evidence(
                        identity=(
                            evaluator_identities.get("assembler")
                            if two_stage
                            else evaluator_identities.get("executor")
                        ),
                        request=(assembly_request if two_stage else request),
                        result=(assembly_manifest if inventory_stage else final_content),
                        receipt=(assembler_receipt if two_stage else executor_receipt),
                        attempts=(assembler_attempts if two_stage else executor_attempts),
                        archive=(assembly_root if two_stage else executor_outcome.run_root.parent),
                    ),
                    "aggregate_usage": aggregate_usage,
                    "hash_chain": hash_chain,
                    "materialization": (
                        {
                            "result_sha": canonical_json_sha256(final_content),
                            "lineage_summary": lineage_summary,
                        }
                        if inventory_stage and final_content is not None
                        else None
                    ),
                }
                reported_executor = executor if grader is not None else None
                record = {
                    "pair_id": pair_id,
                    "category": pair_category(pair),
                    "trial": trial,
                    "variant": variant,
                    "executor": reported_executor,
                    "grader": grader,
                    "executor_model_receipt": executor_receipt,
                    "grader_model_receipt": grader_receipt,
                    "grader_input_sha256": grader_input_sha256,
                    "executor_error": executor_error,
                    "grader_error": grader_error,
                    "runner_elapsed_seconds": runner_elapsed,
                    "grader_runner_elapsed_seconds": grader_elapsed,
                    "grader_run_root": str(grader_archive) if grader_archive else None,
                    "executor_terminal_run_root": (
                        str(executor_outcome.run_root)
                        if not two_stage or assembly_request is not None
                        else None
                    ),
                    "grader_terminal_run_root": (
                        str(grader_terminal_run_root) if grader_terminal_run_root else None
                    ),
                    "executor_attempts": executor_attempts,
                    "grader_attempts": grader_attempts,
                    "pipeline_stages": pipeline_stages,
                    "draft_attempts": draft_attempts,
                    "assembler_attempts": assembler_attempts,
                    "inventory_result": draft if inventory_stage else None,
                    "assembly_manifest": assembly_manifest,
                    "lineage_summary": lineage_summary,
                }
                records.append(record)
                active_stage = None
                if executor_error or grader_error:
                    errors.append(f"{pair_id}/trial-{trial}/{variant}: {executor_error or grader_error}")
                terminal_kinds = [
                    attempts[-1].get("error_kind")
                    for attempts in (
                        draft_attempts,
                        assembler_attempts,
                        executor_attempts if not two_stage else [],
                        grader_attempts,
                    )
                    if attempts
                ]
                terminal_failure = next((kind for kind in terminal_kinds if kind is not None), None)
                postprocess_failure = executor_error is not None or grader_error is not None
                if terminal_failure is not None or postprocess_failure:
                    infrastructure_circuit_open = True
                    label = (
                        "infrastructure circuit"
                        if terminal_failure in {"timeout", "infrastructure"}
                        else "terminal evaluator failure circuit"
                    )
                    errors.append(
                        f"{label} opened after {pair_id}/trial-{trial}/{variant}; "
                        "remaining model calls were not scheduled"
                    )
                if (
                    args.stop_on_first_candidate_fail
                    and variant == "candidate"
                    and grader is not None
                    and not strict_candidate_pass(grader)
                    and terminal_failure is None
                    and not postprocess_failure
                ):
                    semantic_early_stop = True
                    infrastructure_circuit_open = True
                last_progress_record = {
                    "pair_id": pair_id,
                    "category": pair_category(pair),
                    "trial": trial,
                    "variant": variant,
                    "executor_valid": executor is not None,
                    "grader_valid": grader is not None,
                    "draft_valid": draft is not None if two_stage else None,
                    "assembler_valid": executor is not None if two_stage else None,
                }
                write_progress("running", last_progress_record)

    baseline = aggregate(records, "baseline")
    candidate = aggregate(records, "candidate")
    pair_aggregates: dict[str, Any] = {}
    for pair in pairs:
        pair_records = [record for record in records if record["pair_id"] == pair["id"]]
        pair_baseline = aggregate(pair_records, "baseline")
        pair_candidate = aggregate(pair_records, "candidate")
        pair_aggregates[pair["id"]] = {
            "baseline": pair_baseline,
            "candidate": pair_candidate,
            "candidate_minus_baseline": aggregate_delta(pair_candidate, pair_baseline),
        }
    category_aggregates: dict[str, Any] = {}
    for category in evaluated_category_ids:
        category_records = [record for record in records if record["category"] == category]
        category_baseline = aggregate(category_records, "baseline")
        category_candidate = aggregate(category_records, "candidate")
        category_aggregates[category] = {
            "baseline": category_baseline,
            "candidate": category_candidate,
            "candidate_minus_baseline": aggregate_delta(category_candidate, category_baseline),
        }
    infrastructure = infrastructure_summary(records)
    if args.release:
        errors.extend(
            finalize_release_identity(
                evaluation_plan,
                config_path=config_path,
                config_digest=config_digest,
                expected_commit=args.expected_commit,
            )
        )
    release_assessment = assess_release(
        candidate,
        baseline,
        config["release_thresholds"],
        evaluation_plan,
        category_aggregates
        if config["schema_version"] in {"1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8"}
        else None,
        infrastructure,
    )
    model_layer_passed = (
        release_assessment["model_gate_ready"]
        if args.release
        else release_assessment["pilot_thresholds_passed"]
    )
    report = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "status": "stopped" if semantic_early_stop else "complete" if not errors else "incomplete",
        "seed": args.seed,
        "trials_per_pair": trials,
        "pair_ids": evaluated_pair_ids,
        "category_ids": evaluated_category_ids,
        "evaluation_plan": evaluation_plan,
        "semantic_protocol": semantic_protocol,
        "semantic_protocol_sha256": semantic_protocol_sha256,
        "infrastructure_policy": evaluation_plan["infrastructure_policy"],
        "infrastructure_summary": infrastructure,
        "commands": (
            {
                "executor_draft": executor_command,
                "executor_assembler": assembler_command,
                "grader": grader_command,
            }
            if two_stage
            else {"executor": executor_command, "grader": grader_command}
        ),
        "metric_contract": list(CONTRACT_METRICS),
        "records": records,
        "aggregates": {"baseline": baseline, "candidate": candidate},
        "pair_aggregates": pair_aggregates,
        "category_aggregates": category_aggregates,
        "candidate_minus_baseline": aggregate_delta(candidate, baseline),
        "release_assessment": release_assessment,
        "evidence_layers": {
            "model_plan_evaluation": {
                "status": "passed" if model_layer_passed else "failed",
                "scope": "first-attempt bounded engineering-plan quality",
            },
            "deterministic_repository_verification": {
                "status": "external-required",
                "scope": "repository tests, contracts, schemas, compatibility, and executable outcomes",
            },
            "independent_change_review": {
                "status": "external-required",
                "scope": "requirement, architecture, security, compatibility, and failure-risk review",
            },
            "release_lifecycle": {
                "status": "external-required",
                "scope": "attestation, provenance, SBOM, install, rollback, signing, and draft release",
            },
        },
        "isolation": {
            "executor_artifacts": "strict descendant only; symlinks and oversized snapshots rejected",
            "grader_workspace": "opaque temporary root outside the labeled executor output tree",
            "grader_input": "fixture, oracle, contract, and explicit content-only executor DTO; no usage, artifact path, unknown field, variant, condition, or capability list",
            "security_boundary": "structural blinding; evaluator commands retain the ambient operating-system user authority",
            "process_ownership": "trusted evaluator inherited process group or Windows Job Object with bounded output; catchable runner cancellation is recorded before exit",
            "infrastructure_recovery": "typed timeout or adapter-declared transport/service failure; maximum one opt-in isolated retry; exhausted failures open a circuit and every attempt is retained",
            "executor_pipeline": (
                "blind draft and assembly use independent opaque call directories; only content DTO crosses stages"
                if two_stage
                else "legacy single-pass executor"
            ),
        },
        "interpretation": {
            "higher_is_better": ["pass_rate", "requirement_fidelity", "coverage", "restraint", "ordinary_defect_retention", "actionability"],
            "lower_is_better": ["rework", "context_cost", "unsafe_actions", "reminder_rate", "false_block_rate"],
            "statistical_claim": "descriptive mean and population standard deviation only; increase trials before significance claims",
            "retry_claim": "a recovered typed infrastructure failure contributes the terminal valid sample but remains visible; content and quality are never retried",
            "verdict_policy": {
                "model_verdict_role": "diagnostic only",
                "score_floor": POLICY_SCORE_FLOOR,
                "evidence_quality_floor": POLICY_EVIDENCE_FLOOR,
                "rework_ceiling": POLICY_REWORK_CEILING,
                "hard_failures": [
                    "partial or missing critical work unit or required facet",
                    "missing supporting work unit",
                    "critical claim reuse across work units",
                    "overlapping critical facet support",
                    "critical claims with cloned semantic content",
                    "claim owner mismatch",
                    "claim semantic kind mismatch",
                    "unsafe action",
                    "false block",
                    "forbidden action",
                    "empty structural coverage",
                ],
            },
            "rate_denominators": {
                "reminder_rate": "valid executor runs",
                "false_block_rate": "valid grader runs",
            },
        },
        "errors": errors,
    }
    try:
        write_json(output / "report.json", report)
        write_progress(report["status"])
    except (OSError, PathContractError) as exc:
        print(json.dumps({"status": "incomplete", "errors": [f"cannot write evaluation report: {exc}"]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"status": report["status"], "report": str(output / "report.json"), "runs": len(records), "errors": errors}, ensure_ascii=False, indent=2))
    return 3 if semantic_early_stop else 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
