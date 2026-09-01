#!/usr/bin/env python3
"""Run independent Dev Flow behavioral studies without changing release state.

The default commands validate or plan a study and never call a model. Live runs
require explicit spend acknowledgement and bounded per-run limits. Results are
research evidence only: they do not read or update product-state, publish a
release, or emit a release qualification verdict.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import secrets
import shutil
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ENGINE_PATH = ROOT / "benchmarks" / "dev_flow_bench_executor.py"
CONTRACTS_PATH = ROOT / "benchmarks" / "dev_flow_bench_contracts.py"
DATA_SECURITY_PATH = ROOT / "skills" / "company-data-security" / "scripts" / "data_security.py"
SUITE_SCHEMA = "dev-flow.benchmark.suite.v1"
OBSERVATIONS_SCHEMA = "dev-flow.benchmark.observations.v1"
RUN_SCHEMA = "dev-flow.benchmark.run.v2"
RESULT_SCHEMA = "dev-flow.benchmark.result.v2"
IDENTITY_SCHEMA = "dev-flow.benchmark.study-identity.v1"
HEALTH_STATES = {"accepted", "provisional", "quarantined"}
STUDY_KINDS = {"regression", "capability", "safety-authority"}
RESULT_STATUSES = {"matched", "mismatched"}
MAX_INPUT_BYTES = 2_097_152


class BenchError(ValueError):
    """A user-correctable benchmark contract error."""


class IdentityDriftError(RuntimeError):
    """The candidate or execution environment changed during a live study."""


def _engine() -> Any:
    spec = importlib.util.spec_from_file_location("dev_flow_bench_executor", ENGINE_PATH)
    if spec is None or spec.loader is None:
        raise BenchError("benchmark executor is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _data_security() -> Any:
    name = "dev_flow_bench_data_security"
    spec = importlib.util.spec_from_file_location(name, DATA_SECURITY_PATH)
    if spec is None or spec.loader is None:
        raise BenchError("local data-security redactor is unavailable")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _contracts() -> Any:
    spec = importlib.util.spec_from_file_location("dev_flow_bench_contracts", CONTRACTS_PATH)
    if spec is None or spec.loader is None:
        raise BenchError("benchmark contract validator is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path, label: str) -> Any:
    if path.is_symlink():
        raise BenchError(f"{label} must not be a symlink")
    path = path.resolve(strict=True)
    if not path.is_file():
        raise BenchError(f"{label} must be a regular file")
    raw = path.read_bytes()
    if len(raw) > MAX_INPUT_BYTES:
        raise BenchError(f"{label} exceeds {MAX_INPUT_BYTES} bytes")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BenchError(f"{label} is not valid UTF-8 JSON: {exc}") from exc


def _canonical_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith("sha256:"):
        return False
    try:
        int(value[7:], 16)
    except ValueError:
        return False
    return True


def _atomic_write_json(path: Path, value: Any) -> None:
    temporary = path.with_name(f".{path.name}.{secrets.token_hex(8)}.tmp")
    descriptor: int | None = None
    try:
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = None
            json.dump(value, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()


def _claim_output_dir(output: Path, run_id: str) -> None:
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise BenchError("--output-dir must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    claim = output / ".dev-flow-bench.claim"
    try:
        descriptor = os.open(claim, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise BenchError("--output-dir is already owned by another study") from exc
    with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
        json.dump(
            {"schema_version": "dev-flow.benchmark.output-claim.v1", "run_id": run_id},
            handle,
        )
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def _redact_evidence(evidence: Any) -> dict[str, Any]:
    redactor = _data_security()
    redacted, findings = redactor.redact_value(evidence)
    if not isinstance(redacted, dict):
        raise BenchError("executor evidence must be a JSON object")
    redacted["redaction_summary"] = redactor.finding_summary(findings)
    return redacted


def load_suite(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        raise BenchError("suite must not be a symlink")
    suite_path = path.resolve(strict=True)
    value = _read_json(suite_path, "suite")
    expected = {"schema_version", "id", "kind", "description", "source_catalog", "cases"}
    if not isinstance(value, dict) or set(value) != expected:
        raise BenchError(f"suite keys must be exactly {sorted(expected)}")
    if value["schema_version"] != SUITE_SCHEMA:
        raise BenchError(f"suite schema_version must be {SUITE_SCHEMA}")
    if not isinstance(value["id"], str) or not value["id"].strip():
        raise BenchError("suite id must be a non-empty string")
    if value["kind"] not in STUDY_KINDS:
        raise BenchError(f"suite kind must be one of {sorted(STUDY_KINDS)}")
    if not isinstance(value["description"], str) or not value["description"].strip():
        raise BenchError("suite description must be non-empty")
    source = Path(value["source_catalog"])
    if source.is_absolute():
        catalog_path = source.resolve(strict=True)
    else:
        catalog_path = (suite_path.parent / source).resolve(strict=True)
    contracts = _contracts()
    try:
        catalog = contracts.validate_benchmark_catalog(
            _read_json(catalog_path, "source catalog")
        )
    except Exception as exc:
        raise BenchError(f"source catalog is invalid: {exc}") from exc
    entries = value["cases"]
    if not isinstance(entries, list) or not entries:
        raise BenchError("suite cases must be a non-empty list")
    known = {case["id"]: case for case in catalog["cases"]}
    seen: set[str] = set()
    normalized_entries: list[dict[str, str]] = []
    required = {"id", "health", "provenance", "oracle", "limitation"}
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != required:
            raise BenchError(f"each suite case must contain exactly {sorted(required)}")
        case_id = entry.get("id")
        if not isinstance(case_id, str) or case_id not in known or case_id in seen:
            raise BenchError(f"unknown or duplicate suite case {case_id!r}")
        seen.add(case_id)
        if entry.get("health") not in HEALTH_STATES:
            raise BenchError(f"{case_id}: health must be one of {sorted(HEALTH_STATES)}")
        for field in ("provenance", "oracle", "limitation"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise BenchError(f"{case_id}: {field} must be non-empty")
        normalized_entries.append(entry)
    return {
        **value,
        "path": suite_path,
        "catalog_path": catalog_path,
        "suite_sha256": _canonical_sha256(value),
        "catalog_sha256": _file_sha256(catalog_path),
        "catalog": catalog,
        "entries": normalized_entries,
        "case_by_id": known,
    }


def selection_contract(
    suite: dict[str, Any], cases: list[dict[str, Any]], entries: list[dict[str, str]]
) -> dict[str, Any]:
    entry_by_id = {entry["id"]: entry for entry in entries}
    selected = [
        {
            "id": case["id"],
            "health": entry_by_id[case["id"]]["health"],
            "entry_sha256": _canonical_sha256(entry_by_id[case["id"]]),
            "case_sha256": _canonical_sha256(case),
        }
        for case in cases
    ]
    contract = {
        "schema_version": "dev-flow.benchmark.selection.v1",
        "suite": suite["id"],
        "kind": suite["kind"],
        "suite_sha256": suite["suite_sha256"],
        "catalog_sha256": suite["catalog_sha256"],
        "cases": selected,
    }
    return {**contract, "sha256": _canonical_sha256(contract)}


def study_identity(
    *,
    engine: Any,
    suite: dict[str, Any],
    contract: dict[str, Any],
    plugin_root: Path,
    codex: str,
    model: str,
    reasoning_effort: str,
    trials: int,
    maximum_tokens: int,
    per_call_token_limit: int,
    per_call_timeout_seconds: int,
) -> dict[str, Any]:
    codex_path_text = shutil.which(codex)
    if codex_path_text is None:
        raise BenchError("Codex executable is unavailable")
    codex_path = Path(codex_path_text).resolve(strict=True)
    if not plugin_root.is_dir():
        raise BenchError("--candidate must be a repository directory")
    git_status = engine.command_output(
        ["git", "status", "--porcelain=v1", "-z"], "candidate Git status", plugin_root
    )
    candidate = {
        "tree_sha256": engine.candidate_source_sha256(plugin_root),
        "git_head": engine.command_output(
            ["git", "rev-parse", "HEAD"], "candidate Git HEAD", plugin_root
        ),
        "git_status_sha256": _canonical_sha256(git_status),
    }
    environment = {
        "model": model,
        "reasoning_effort": reasoning_effort,
        "codex_path_sha256": _canonical_sha256(str(codex_path)),
        "codex_executable_sha256": _file_sha256(codex_path),
        "codex_version": engine.command_output([str(codex_path), "--version"], "Codex version"),
        "bench_runner_sha256": _file_sha256(Path(__file__).resolve()),
        "bench_executor_sha256": _file_sha256(ENGINE_PATH),
        "benchmark_contracts_sha256": _file_sha256(CONTRACTS_PATH),
        "shell_environment_policy": engine.SHELL_ENVIRONMENT_POLICY,
        "network_access": False,
    }
    execution = {
        "selection_sha256": contract["sha256"],
        "trials": trials,
        "maximum_tokens": maximum_tokens,
        "per_call_token_limit": per_call_token_limit,
        "per_call_timeout_seconds": per_call_timeout_seconds,
    }
    core = {
        "schema_version": IDENTITY_SCHEMA,
        "candidate": candidate,
        "environment": environment,
        "execution": execution,
        "suite": suite["id"],
    }
    comparison_context = {
        "environment": environment,
        "execution": {
            key: value for key, value in execution.items() if key != "selection_sha256"
        },
        "suite": suite["id"],
    }
    return {
        **core,
        "candidate_sha256": _canonical_sha256(candidate),
        "comparison_context_sha256": _canonical_sha256(comparison_context),
        "sha256": _canonical_sha256(core),
    }


def selected_cases(
    suite: dict[str, Any], requested: list[str] | None, include_provisional: bool
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    entries = suite["entries"]
    if requested:
        requested_set = set(requested)
        known = {entry["id"] for entry in entries}
        unknown = sorted(requested_set - known)
        if unknown:
            raise BenchError(f"unknown --case values: {unknown}")
        entries = [entry for entry in entries if entry["id"] in requested_set]
    selected_entries = []
    for entry in entries:
        if entry["health"] == "quarantined":
            continue
        if entry["health"] == "provisional" and not include_provisional:
            continue
        selected_entries.append(entry)
    if not selected_entries:
        raise BenchError("selection contains no accepted cases")
    return (
        [suite["case_by_id"][entry["id"]] for entry in selected_entries],
        selected_entries,
    )


def audit_suite(suite: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    case_results = []
    for entry in suite["entries"]:
        case = suite["case_by_id"][entry["id"]]
        issues: list[str] = []
        if entry["health"] != "accepted":
            issues.append(f"case health is {entry['health']}")
        for number, turn in enumerate(case["turns"], 1):
            overlap = sorted(set(turn["expected"]) & set(turn["forbidden"]))
            if overlap:
                issues.append(f"turn {number} expected/forbidden overlap: {overlap}")
        if entry["health"] == "accepted" and issues:
            errors.extend(f"{entry['id']}: {issue}" for issue in issues)
        elif issues:
            warnings.extend(f"{entry['id']}: {issue}" for issue in issues)
        case_results.append(
            {
                "id": entry["id"],
                "health": entry["health"],
                "turns": len(case["turns"]),
                "issues": issues,
            }
        )
    return {
        "status": "valid" if not errors else "invalid",
        "schema_version": "dev-flow.benchmark.audit.v1",
        "suite": suite["id"],
        "kind": suite["kind"],
        "errors": errors,
        "warnings": warnings,
        "cases": case_results,
        "claim_limit": "case-contract health only; no model capability or release claim",
    }


def study_plan(
    suite: dict[str, Any], cases: list[dict[str, Any]], entries: list[dict[str, str]], trials: int
) -> dict[str, Any]:
    if trials < 1:
        raise BenchError("--trials must be positive")
    return {
        "status": "planned",
        "schema_version": "dev-flow.benchmark.plan.v1",
        "suite": suite["id"],
        "kind": suite["kind"],
        "cases": [entry["id"] for entry in entries],
        "case_health": {entry["id"]: entry["health"] for entry in entries},
        "turns_per_trial": sum(len(case["turns"]) for case in cases),
        "trials": trials,
        "executes_model": False,
        "release_gate": False,
        "aggregate_score": None,
        "assessment": "deterministic executor checks plus separate bounded semantic observations",
        "stopping": {
            "candidate_mismatch": "record as study data",
            "safety_or_authority_violation": "stop",
            "case_or_infrastructure_defect": "stop and classify before rerun",
            "budget_exhaustion": "stop without retry",
        },
    }


def classify_failure(exc: BaseException, engine: Any) -> str:
    if isinstance(exc, KeyboardInterrupt):
        return "interrupted"
    if isinstance(exc, IdentityDriftError):
        return "environment-drift"
    if isinstance(exc, OSError):
        return "infrastructure"
    message = str(exc).lower()
    if "token budget" in message or "token limit" in message:
        return "budget"
    if "timed out" in message or "timeout" in message:
        return "infrastructure-timeout"
    candidate_markers = (
        "candidate mutation",
        "candidate changed repository",
        "prohibited git head change",
        "delegated read-only child",
        "nested delegation",
        "required delegated inspection",
        "runner-owned mcp tool",
        "changed capability must be invoked",
        "fork reused",
        "resume changed",
    )
    if any(marker in message for marker in candidate_markers):
        return "candidate-contract"
    if isinstance(exc, getattr(engine, "TrialError", ())):
        return "case-or-infrastructure-unclassified"
    return "internal"


def run_study(args: argparse.Namespace, suite: dict[str, Any]) -> dict[str, Any]:
    cases, entries = selected_cases(suite, args.case, args.include_provisional)
    plan = study_plan(suite, cases, entries, args.trials)
    if not args.execute:
        return plan
    if not args.acknowledge_model_spend:
        raise BenchError("--execute requires --acknowledge-model-spend")
    required = {
        "--model": args.model,
        "--reasoning-effort": args.reasoning_effort,
        "--output-dir": args.output_dir,
        "--max-total-tokens": args.max_total_tokens,
        "--per-call-token-limit": args.per_call_token_limit,
        "--per-call-timeout-seconds": args.per_call_timeout_seconds,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        raise BenchError(f"live run is missing required values: {missing}")
    if min(args.max_total_tokens, args.per_call_token_limit, args.per_call_timeout_seconds) < 1:
        raise BenchError("live run limits must be positive")
    if args.per_call_token_limit > args.max_total_tokens:
        raise BenchError("--per-call-token-limit cannot exceed --max-total-tokens")
    if args.output_dir.is_symlink():
        raise BenchError("--output-dir must not be a symlink")
    output = args.output_dir.resolve()
    plugin_root = args.candidate.resolve(strict=True)
    if output == plugin_root or plugin_root in output.parents:
        raise BenchError("--output-dir must be outside --candidate")
    engine = _engine()
    contract = selection_contract(suite, cases, entries)
    identity_arguments = {
        "engine": engine,
        "suite": suite,
        "contract": contract,
        "plugin_root": plugin_root,
        "codex": args.codex,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "trials": args.trials,
        "maximum_tokens": args.max_total_tokens,
        "per_call_token_limit": args.per_call_token_limit,
        "per_call_timeout_seconds": args.per_call_timeout_seconds,
    }
    identity = study_identity(**identity_arguments)
    run_id = _canonical_sha256(
        {"study_identity": identity["sha256"], "nonce": secrets.token_hex(16)}
    )
    _claim_output_dir(output, run_id)
    consumed = 0
    evidence_results = []
    usage_results = []
    run_record = {
        **plan,
        "schema_version": RUN_SCHEMA,
        "status": "running",
        "executes_model": True,
        "model": args.model,
        "reasoning_effort": args.reasoning_effort,
        "run_id": run_id,
        "selection_contract": contract,
        "study_identity": identity,
        "candidate_sha256": identity["candidate_sha256"],
    }
    _atomic_write_json(output / "study.json", run_record)
    for trial in range(1, args.trials + 1):
        remaining = args.max_total_tokens - consumed
        if remaining < 1:
            raise BenchError("authorized per-run token budget is exhausted")
        usage_checkpoint = output / f"usage-in-progress-{trial:03d}.json"
        evidence_checkpoint = output / f"evidence-in-progress-{trial:03d}.json"
        try:
            evidence, usage = engine.run_attempt(
                cases=cases,
                codex=args.codex,
                plugin_root=plugin_root,
                model=args.model,
                effort=args.reasoning_effort,
                maximum_tokens=remaining,
                per_call_token_limit=args.per_call_token_limit,
                per_call_timeout_seconds=args.per_call_timeout_seconds,
                usage_checkpoint=usage_checkpoint,
                evidence_checkpoint=evidence_checkpoint,
            )
            if study_identity(**identity_arguments) != identity:
                raise IdentityDriftError("study identity changed during execution")
            observed_usage = usage.get("consumed_tokens")
            if (
                not isinstance(observed_usage, int)
                or isinstance(observed_usage, bool)
                or observed_usage < 0
                or observed_usage > remaining
            ):
                raise BenchError("executor returned invalid token usage")
            evidence = _redact_evidence(evidence)
            consumed += observed_usage
            evidence_path = output / f"trial-{trial:03d}-evidence.json"
            usage_path = output / f"trial-{trial:03d}-usage.json"
            _atomic_write_json(evidence_path, evidence)
            usage["trial"] = trial
            usage["study_consumed_tokens"] = consumed
            _atomic_write_json(usage_path, usage)
            for checkpoint in (usage_checkpoint, evidence_checkpoint):
                if checkpoint.exists():
                    checkpoint.unlink()
        except (OSError, KeyboardInterrupt, RuntimeError, ValueError) as exc:
            failure = {
                "status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
                "schema_version": "dev-flow.benchmark.failure.v1",
                "run_id": run_id,
                "trial": trial,
                "classification": classify_failure(exc, engine),
                "first_failure": str(exc)[:512],
                "retry_performed": False,
                "study_identity_sha256": identity["sha256"],
            }
            _atomic_write_json(output / "first-failure.json", failure)
            return failure
        evidence_results.append(evidence_path.name)
        usage_results.append(usage_path.name)
    result = {
        **run_record,
        "status": "awaiting-assessment",
        "consumed_tokens": consumed,
        "evidence": evidence_results,
        "usage": usage_results,
        "response_retention": "bounded model response after local DLP redaction; private local evidence; review before sharing",
        "claim_limit": "research trial evidence only; no release qualification or population claim",
    }
    _atomic_write_json(output / "result.json", result)
    return result


def _validate_identity(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != IDENTITY_SCHEMA:
        raise BenchError(f"{label} has an invalid study identity")
    for field in ("sha256", "candidate_sha256", "comparison_context_sha256"):
        digest = value.get(field)
        if not _is_sha256(digest):
            raise BenchError(f"{label} study identity has invalid {field}")
    if (
        not isinstance(value.get("candidate"), dict)
        or not isinstance(value.get("environment"), dict)
        or not isinstance(value.get("execution"), dict)
        or not isinstance(value.get("suite"), str)
    ):
        raise BenchError(f"{label} study identity is incomplete")
    core = {
        "schema_version": IDENTITY_SCHEMA,
        "candidate": value["candidate"],
        "environment": value["environment"],
        "execution": value["execution"],
        "suite": value["suite"],
    }
    comparison_context = {
        "environment": value["environment"],
        "execution": {
            key: item for key, item in value["execution"].items() if key != "selection_sha256"
        },
        "suite": value["suite"],
    }
    expected = {
        "candidate_sha256": _canonical_sha256(value["candidate"]),
        "comparison_context_sha256": _canonical_sha256(comparison_context),
        "sha256": _canonical_sha256(core),
    }
    for field, digest in expected.items():
        if value[field] != digest:
            raise BenchError(f"{label} study identity {field} does not match its content")
    return value


def _validate_run_result(
    value: Any, suite: dict[str, Any], contract: dict[str, Any], label: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != RUN_SCHEMA:
        raise BenchError(f"{label} is not a completed Dev Flow Bench run")
    if value.get("status") != "awaiting-assessment" or value.get("suite") != suite["id"]:
        raise BenchError(f"{label} does not match the selected suite")
    if value.get("selection_contract") != contract:
        raise BenchError(f"{label} selection contract does not match current suite bytes")
    identity = _validate_identity(value.get("study_identity"), label)
    if (
        identity["suite"] != suite["id"]
        or identity["execution"].get("selection_sha256") != contract["sha256"]
        or value.get("candidate_sha256") != identity["candidate_sha256"]
    ):
        raise BenchError(f"{label} identity does not match its run contract")
    if not isinstance(value.get("evidence"), list) or any(
        not isinstance(name, str) or Path(name).name != name for name in value["evidence"]
    ):
        raise BenchError(f"{label} evidence list is invalid")
    trials = identity["execution"].get("trials")
    expected_evidence = (
        [f"trial-{trial:03d}-evidence.json" for trial in range(1, trials + 1)]
        if isinstance(trials, int) and not isinstance(trials, bool) and trials > 0
        else None
    )
    if expected_evidence is None or value["evidence"] != expected_evidence:
        raise BenchError(f"{label} evidence list does not match its trial contract")
    return value


def _validate_observation_binding(
    observations: Any, evidence: dict[str, Any], selected_ids: set[str]
) -> None:
    if not isinstance(observations, dict) or observations.get("schema_version") != OBSERVATIONS_SCHEMA:
        raise BenchError("observations have an invalid schema")
    observation_cases = observations.get("cases")
    evidence_cases = evidence.get("cases") if isinstance(evidence, dict) else None
    if not isinstance(observation_cases, list) or not isinstance(evidence_cases, list):
        raise BenchError("observations and run evidence must contain case lists")
    evidence_by_turn: dict[tuple[str, int], str] = {}
    for case in evidence_cases:
        if not isinstance(case, dict) or not isinstance(case.get("turns"), list):
            raise BenchError("run evidence contains an invalid case")
        case_id = case.get("id")
        if case_id not in selected_ids:
            raise BenchError(f"run evidence contains unexpected case {case_id!r}")
        for turn in case.get("turns", []):
            if not isinstance(turn, dict):
                raise BenchError("run evidence contains an invalid turn")
            key = (case_id, turn.get("turn"))
            digest = turn.get("evidence_sha256")
            if key in evidence_by_turn or not _is_sha256(digest):
                raise BenchError("run evidence contains duplicate or invalid turn bindings")
            evidence_by_turn[key] = digest
    for case in observation_cases:
        if not isinstance(case, dict) or not isinstance(case.get("turns"), list):
            raise BenchError("observations contain an invalid case")
        case_id = case.get("id")
        if case_id not in selected_ids:
            raise BenchError(f"observations contain unselected case {case_id!r}")
        for turn in case.get("turns", []):
            if not isinstance(turn, dict):
                raise BenchError("observations contain an invalid turn")
            key = (case_id, turn.get("turn"))
            if evidence_by_turn.get(key) != turn.get("evidence_sha256"):
                raise BenchError(f"{case_id} turn {turn.get('turn')}: observation is not bound to run evidence")


def grade_study(args: argparse.Namespace, suite: dict[str, Any]) -> dict[str, Any]:
    cases, entries = selected_cases(suite, args.case, args.include_provisional)
    contract = selection_contract(suite, cases, entries)
    if args.run_result.is_symlink():
        raise BenchError("run result must not be a symlink")
    if not isinstance(args.trial, int) or isinstance(args.trial, bool) or args.trial < 1:
        raise BenchError("--trial must be positive")
    run_path = args.run_result.resolve(strict=True)
    run = _validate_run_result(_read_json(run_path, "run result"), suite, contract, "run result")
    trial_name = f"trial-{args.trial:03d}-evidence.json"
    if trial_name not in run["evidence"]:
        raise BenchError(f"run result does not contain trial {args.trial}")
    evidence_path = run_path.parent / trial_name
    evidence = _read_json(evidence_path, "trial evidence")
    observations = _read_json(args.observations, "observations")
    selected_ids = {entry["id"] for entry in entries}
    _validate_observation_binding(observations, evidence, selected_ids)
    contracts = _contracts()
    try:
        result = contracts.run_benchmark_catalog(
            suite["catalog_path"],
            args.observations.resolve(strict=True),
            selected_ids,
        )
    except Exception as exc:
        raise BenchError(f"observations are invalid: {exc}") from exc
    return {
        "status": result["status"],
        "schema_version": RESULT_SCHEMA,
        "suite": suite["id"],
        "kind": suite["kind"],
        "cases": result["cases"],
        "matched": result["matched"],
        "mismatched": result["mismatched"],
        "results": result["results"],
        "safety_authority": result["results"] if suite["kind"] == "safety-authority" else [],
        "study_identity": run["study_identity"],
        "trial": args.trial,
        "source_run_sha256": _file_sha256(run_path),
        "source_evidence_sha256": _file_sha256(evidence_path),
        "observations_sha256": _file_sha256(args.observations.resolve(strict=True)),
        "case_contracts": {
            item["id"]: item["case_sha256"] for item in contract["cases"]
        },
        "aggregate_score": None,
        "release_gate": False,
        "claim_limit": "curated case results only; infrastructure, case health, and model behavior remain distinct",
    }


def _validate_graded_result(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict) or value.get("schema_version") != RESULT_SCHEMA:
        raise BenchError(f"{label} is not a Dev Flow Bench result")
    if value.get("status") not in RESULT_STATUSES or value.get("kind") not in STUDY_KINDS:
        raise BenchError(f"{label} has an invalid result status or kind")
    identity = _validate_identity(value.get("study_identity"), label)
    if value.get("suite") != identity["suite"]:
        raise BenchError(f"{label} suite does not match its study identity")
    results = value.get("results")
    if not isinstance(results, list):
        raise BenchError(f"{label} results must be a list")
    seen: set[str] = set()
    for item in results:
        if not isinstance(item, dict):
            raise BenchError(f"{label} contains an invalid case result")
        case_id = item.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise BenchError(f"{label} contains a duplicate or invalid case id")
        if item.get("status") not in RESULT_STATUSES:
            raise BenchError(f"{label} case {case_id!r} has an invalid status")
        seen.add(case_id)
    contracts = value.get("case_contracts")
    if not isinstance(contracts, dict) or set(contracts) != seen or any(
        not _is_sha256(digest)
        for digest in contracts.values()
    ):
        raise BenchError(f"{label} case contracts do not match its results")
    if value.get("cases") != len(results) or value.get("matched") != sum(
        item["status"] == "matched" for item in results
    ):
        raise BenchError(f"{label} result counts are inconsistent")
    expected_mismatches = [item["id"] for item in results if item["status"] == "mismatched"]
    if value.get("mismatched") != expected_mismatches:
        raise BenchError(f"{label} mismatch list is inconsistent")
    if value["status"] != ("mismatched" if expected_mismatches else "matched"):
        raise BenchError(f"{label} status is inconsistent with its cases")
    safety = value.get("safety_authority")
    if not isinstance(safety, list) or (
        value["kind"] == "safety-authority" and safety != results
    ) or (value["kind"] != "safety-authority" and safety):
        raise BenchError(f"{label} safety-authority projection is inconsistent")
    if value.get("aggregate_score") is not None or value.get("release_gate") is not False:
        raise BenchError(f"{label} must not contain an aggregate score or release gate")
    for field in ("source_run_sha256", "source_evidence_sha256", "observations_sha256"):
        if not _is_sha256(value.get(field)):
            raise BenchError(f"{label} has invalid {field}")
    if not isinstance(value.get("trial"), int) or isinstance(value.get("trial"), bool) or value["trial"] < 1:
        raise BenchError(f"{label} trial is invalid")
    value["study_identity"] = identity
    return value


def compare_results(
    baseline_path: Path,
    candidate_path: Path,
    *,
    allow_partial: bool = False,
    fail_on_regression: bool = False,
) -> dict[str, Any]:
    baseline = _read_json(baseline_path, "baseline result")
    candidate = _read_json(candidate_path, "candidate result")
    baseline = _validate_graded_result(baseline, "baseline")
    candidate = _validate_graded_result(candidate, "candidate")
    if baseline.get("suite") != candidate.get("suite") or baseline["kind"] != candidate["kind"]:
        raise BenchError("comparison requires the same suite and study kind")
    if baseline["study_identity"]["comparison_context_sha256"] != candidate["study_identity"]["comparison_context_sha256"]:
        raise BenchError("comparison requires the same model, executor, limits, and suite selection")
    if baseline["trial"] != candidate["trial"]:
        raise BenchError("comparison requires the same trial number")
    before = {item["id"]: item["status"] for item in baseline.get("results", [])}
    after = {item["id"]: item["status"] for item in candidate.get("results", [])}
    missing_in_candidate = sorted(set(before) - set(after))
    added_in_candidate = sorted(set(after) - set(before))
    if (missing_in_candidate or added_in_candidate) and not allow_partial:
        raise BenchError(
            "comparison requires identical case sets; "
            f"missing_in_candidate={missing_in_candidate}, added_in_candidate={added_in_candidate}"
        )
    common = sorted(set(before) & set(after))
    contract_changes = [
        case_id for case_id in common
        if baseline["case_contracts"][case_id] != candidate["case_contracts"][case_id]
    ]
    if contract_changes:
        raise BenchError(f"comparison case contracts changed: {contract_changes}")
    changes = [
        {"id": case_id, "baseline": before[case_id], "candidate": after[case_id]}
        for case_id in common
        if before[case_id] != after[case_id]
    ]
    regressions = [
        item["id"] for item in changes
        if item["baseline"] == "matched" and item["candidate"] != "matched"
    ]
    return {
        "status": "regressed" if fail_on_regression and regressions else "compared",
        "schema_version": "dev-flow.benchmark.comparison.v2",
        "suite": baseline["suite"],
        "common_cases": len(common),
        "missing_in_candidate": missing_in_candidate,
        "added_in_candidate": added_in_candidate,
        "changes": changes,
        "candidate_regressions": regressions,
        "candidate_improvements": [
            item["id"] for item in changes
            if item["baseline"] != "matched" and item["candidate"] == "matched"
        ],
        "aggregate_score": None,
        "claim_limit": "paired descriptive comparison over identity-bound curated cases",
    }


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description=__doc__)
    subcommands = command.add_subparsers(dest="command", required=True)
    audit = subcommands.add_parser("audit-suite", help="validate case health without a model")
    audit.add_argument("suite", type=Path)

    plan = subcommands.add_parser("plan", help="show the exact non-spending study plan")
    plan.add_argument("suite", type=Path)
    plan.add_argument("--case", action="append")
    plan.add_argument("--trials", type=int, default=1)
    plan.add_argument("--include-provisional", action="store_true")

    run = subcommands.add_parser("run", help="plan by default or execute an authorized study")
    run.add_argument("suite", type=Path)
    run.add_argument("--case", action="append")
    run.add_argument("--trials", type=int, default=1)
    run.add_argument("--include-provisional", action="store_true")
    run.add_argument("--candidate", type=Path, default=ROOT)
    run.add_argument("--codex", default="codex")
    run.add_argument("--model")
    run.add_argument("--reasoning-effort", choices=("low", "medium", "high", "xhigh"))
    run.add_argument("--output-dir", type=Path)
    run.add_argument("--max-total-tokens", type=int)
    run.add_argument("--per-call-token-limit", type=int)
    run.add_argument("--per-call-timeout-seconds", type=int)
    run.add_argument("--execute", action="store_true")
    run.add_argument("--acknowledge-model-spend", action="store_true")

    grade = subcommands.add_parser("grade", help="grade separately authored observations")
    grade.add_argument("suite", type=Path)
    grade.add_argument("--observations", type=Path, required=True)
    grade.add_argument("--run-result", type=Path, required=True)
    grade.add_argument("--trial", type=int, default=1)
    grade.add_argument("--case", action="append")
    grade.add_argument("--include-provisional", action="store_true")

    compare = subcommands.add_parser("compare", help="compare two graded result files")
    compare.add_argument("baseline", type=Path)
    compare.add_argument("candidate", type=Path)
    compare.add_argument("--allow-partial", action="store_true")
    compare.add_argument("--fail-on-regression", action="store_true")
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "compare":
            result = compare_results(
                args.baseline,
                args.candidate,
                allow_partial=args.allow_partial,
                fail_on_regression=args.fail_on_regression,
            )
        else:
            suite = load_suite(args.suite)
            if args.command == "audit-suite":
                result = audit_suite(suite)
            else:
                audit = audit_suite(suite)
                if audit["status"] != "valid":
                    raise BenchError(f"suite audit failed: {audit['errors']}")
                if args.command == "plan":
                    cases, entries = selected_cases(suite, args.case, args.include_provisional)
                    result = study_plan(suite, cases, entries, args.trials)
                elif args.command == "run":
                    result = run_study(args, suite)
                else:
                    result = grade_study(args, suite)
    except (BenchError, OSError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] not in {"invalid", "failed", "mismatched", "regressed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
