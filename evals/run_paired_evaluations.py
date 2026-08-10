#!/usr/bin/env python3
"""Run isolated, counterbalanced Dev Flow capability evaluations."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_CONFIG = ROOT / "evals" / "paired-evaluations.json"
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
EXECUTOR_KEYS = {
    "case_id",
    "attempt",
    "artifact_root",
    "claimed_outcome",
    "actions",
    "evidence",
    "interactions",
    "usage",
}
GRADER_KEYS = {
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


def validate_config(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise EvaluationError("paired evaluation config must be an object")
    required_keys = {"schema_version", "evaluation_contract", "default_trials", "metrics", "pairs"}
    allowed_keys = required_keys | {"release_thresholds", "release_plan"}
    missing = required_keys - set(value)
    extra = set(value) - allowed_keys
    if missing or extra:
        raise EvaluationError(f"paired evaluation config key mismatch: missing={sorted(missing)}, extra={sorted(extra)}")
    config = dict(value)
    if config["schema_version"] not in {"1.0", "1.1"}:
        raise EvaluationError("paired evaluation config schema_version must be 1.0 or 1.1")
    if config["schema_version"] == "1.1" and "release_plan" not in config:
        raise EvaluationError("paired evaluation config schema 1.1 requires release_plan")
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
    pair_keys = {"id", "fixture", "capabilities", "deterministic_oracle"}
    seen_pair_ids: set[str] = set()
    eval_root = ROOT / "evals"
    for index, pair in enumerate(config["pairs"]):
        checked = require_exact_object(pair, pair_keys, f"pairs[{index}]")
        try:
            pair_id = safe_path_component(checked["id"], label=f"pairs[{index}].id")
        except PathContractError as exc:
            raise EvaluationError(str(exc)) from exc
        if pair_id in seen_pair_ids:
            raise EvaluationError(f"pairs[{index}].id must be unique")
        seen_pair_ids.add(pair_id)
        if not isinstance(checked["fixture"], str) or not checked["fixture"].strip():
            raise EvaluationError(f"pairs[{index}].fixture must be a non-empty string")
        require_text_list(checked["capabilities"], f"pairs[{index}].capabilities")
        if not checked["capabilities"]:
            raise EvaluationError(f"pairs[{index}].capabilities must not be empty")
        if not isinstance(checked["deterministic_oracle"], str) or not checked["deterministic_oracle"].strip():
            raise EvaluationError(f"pairs[{index}].deterministic_oracle must be a non-empty string")
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
    if "release_plan" in config:
        release_plan = require_exact_object(
            config["release_plan"],
            {"pair_ids", "trials_per_pair"},
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

    inputs: dict[str, dict[str, Any]] = {}
    for pair in config["pairs"]:
        fixture_relative = f"evals/{pair['fixture']}"
        fixture = read_text(fixture_relative)
        if len(fixture.encode("utf-8")) > MAX_FIXTURE_BYTES:
            raise EvaluationError(f"{pair['id']} fixture exceeds {MAX_FIXTURE_BYTES} bytes")
        capability_sources: dict[str, str] = {}
        for capability in pair["capabilities"]:
            try:
                safe_capability = safe_path_component(capability, label="evaluation capability")
            except PathContractError as exc:
                raise EvaluationError(str(exc)) from exc
            capability_sources[safe_capability] = read_text(f"skills/{safe_capability}/SKILL.md")
        inputs[pair["id"]] = {"fixture": fixture, "capability_sources": capability_sources}
    entries.sort(key=lambda item: item["path"])
    canonical_entries = json.dumps(entries, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return inputs, {
        "source": "git-commit" if expected_commit else "worktree-snapshot",
        "commit": expected_commit,
        "entries": entries,
        "sha256": "sha256:" + hashlib.sha256(canonical_entries).hexdigest(),
    }


def validate_executor(value: Any, run_root: Path, case_id: str) -> dict[str, Any]:
    result = require_exact_object(value, EXECUTOR_KEYS, "executor result")
    if result["case_id"] != case_id or result["attempt"] != 1:
        raise EvaluationError("executor result must preserve case_id and first-attempt number 1")
    if result["claimed_outcome"] not in {"completed", "blocked", "needs-user-decision"}:
        raise EvaluationError("executor claimed_outcome is invalid")
    require_text_list(result["actions"], "executor actions")
    require_text_list(result["evidence"], "executor evidence")
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


def validate_grader(value: Any, case_id: str) -> dict[str, Any]:
    result = require_exact_object(value, GRADER_KEYS, "grader result")
    if result["case_id"] != case_id or result["graded_attempt"] != 1:
        raise EvaluationError("grader result must preserve case_id and first-attempt number 1")
    for key in ("requirement_fidelity", "scope_discipline", "evidence_quality"):
        require_score(result[key], key)
    require_text_list(result["forbidden_actions"], "grader forbidden_actions")
    require_text_list(result["structural_coverage"], "grader structural_coverage")
    metrics = require_exact_object(result["metrics"], METRIC_KEYS, "grader metrics")
    for key in SCORE_METRIC_KEYS:
        require_score(metrics[key], f"metrics.{key}")
    for key in COUNT_METRIC_KEYS:
        require_nonnegative_integer(metrics[key], f"metrics.{key}")
    if result["verdict"] not in {"pass", "fail", "inconclusive"}:
        raise EvaluationError("grader verdict is invalid")
    return result


def run_program(
    command: list[str],
    request: dict[str, Any],
    cwd: Path,
    timeout: int,
    *,
    output_limit: int = DEFAULT_OUTPUT_LIMIT,
) -> tuple[dict[str, Any] | None, str | None, float]:
    try:
        cwd.mkdir(parents=True, exist_ok=True)
        write_json(cwd / "request.json", request)
    except (OSError, PathContractError) as exc:
        return None, f"cannot prepare program evidence: {exc}", 0.0
    result = run_owned_process(
        command,
        json.dumps(request, ensure_ascii=False),
        cwd=cwd,
        timeout=timeout,
        output_limit=output_limit,
    )
    try:
        atomic_write_text(cwd / "stdout.txt", result.stdout)
        atomic_write_text(cwd / "stderr.txt", result.stderr)
    except (OSError, PathContractError) as exc:
        return None, f"cannot record program output: {exc}", result.elapsed_seconds
    if result.error:
        try:
            atomic_write_text(cwd / "runner-error.txt", result.error + "\n")
        except (OSError, PathContractError) as exc:
            return None, f"cannot record runner error: {exc}", result.elapsed_seconds
        return None, result.error, result.elapsed_seconds
    if result.returncode:
        return None, f"program exited {result.returncode}", result.elapsed_seconds
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, f"stdout is not one JSON value: {exc}", result.elapsed_seconds
    if not isinstance(parsed, dict):
        return None, "stdout JSON must be an object", result.elapsed_seconds
    return parsed, None, result.elapsed_seconds


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
    return {
        "runs": len(selected),
        "valid_executor_runs": len(executor_results),
        "valid_grader_runs": len(grader_results),
        "outcomes": verdicts,
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
    }


def assess_release(
    candidate: dict[str, Any],
    baseline: dict[str, Any],
    thresholds: dict[str, Any],
    evaluation_plan: dict[str, Any],
) -> dict[str, Any]:
    gates: list[dict[str, Any]] = []

    trusted_release: dict[str, Any] | None = None
    try:
        trusted_bytes = CANONICAL_CONFIG.read_bytes()
        trusted_config = validate_config(json.loads(trusted_bytes.decode("utf-8")))
        if trusted_config["schema_version"] == "1.1":
            expected_commit = (
                evaluation_plan.get("source_identity", {}).get("preflight", {}).get("expected_commit")
            )
            trusted_snapshot = (
                evaluation_input_snapshot(trusted_config, expected_commit)[1]
                if isinstance(expected_commit, str) and re.fullmatch(r"[0-9a-f]{40}", expected_commit)
                else None
            )
            trusted_release = {
                "config_sha256": "sha256:" + hashlib.sha256(trusted_bytes).hexdigest(),
                "pair_ids": trusted_config["release_plan"]["pair_ids"],
                "trials_per_pair": trusted_config["release_plan"]["trials_per_pair"],
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
        and evaluation_plan.get("config_schema_version") == "1.1"
        and evaluation_plan.get("config_sha256") == trusted_release["config_sha256"]
        and evaluation_plan.get("required_pair_ids") == trusted_release["pair_ids"]
        and evaluation_plan.get("evaluated_pair_ids") == trusted_release["pair_ids"]
        and evaluation_plan.get("required_trials_per_pair") == trusted_release["trials_per_pair"]
        and evaluation_plan.get("actual_trials_per_pair") == trusted_release["trials_per_pair"]
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
                "all_configured_pairs": True,
                "canonical_config_sha256": trusted_release["config_sha256"] if trusted_release else None,
                "exact_pair_ids": trusted_release["pair_ids"] if trusted_release else None,
                "exact_trials_per_pair": trusted_release["trials_per_pair"] if trusted_release else None,
                "expected_runs_per_variant": expected_runs,
                "immutable_input_snapshot": trusted_release["input_snapshot"] if trusted_release else None,
                "matched_clean_commit": True,
                "matched_canonical_config": True,
            },
            "status": "passed" if release_plan_complete else "not-evaluable",
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
    threshold_gates = [item for item in gates if item["gate"] != "release-plan-completeness"]
    return {
        "release_ready": bool(gates) and all(item["status"] == "passed" for item in gates),
        "pilot_thresholds_passed": bool(threshold_gates)
        and all(item["status"] == "passed" for item in threshold_gates),
        "mode": evaluation_plan.get("mode"),
        "gates": gates,
        "policy": "quality and safety floors are mandatory; context cost is a secondary bounded constraint",
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
    committed = subprocess.run(
        ["git", "show", f"{expected_commit}:evals/paired-evaluations.json"],
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
    parser.add_argument("--executor", required=True, help="Quoted executor command; receives one JSON request on stdin")
    parser.add_argument("--grader", required=True, help="Quoted independent grader command; receives one blind JSON request on stdin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=CANONICAL_CONFIG)
    parser.add_argument("--pair", action="append", default=[])
    parser.add_argument("--trials", type=int)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--release", action="store_true", help="Enable the frozen full-release plan; never use for a pilot")
    parser.add_argument("--expected-commit", help="Full lowercase commit SHA required with --release")
    args = parser.parse_args()

    if args.timeout < 1:
        parser.error("--timeout must be positive")
    try:
        config_bytes = args.config.read_bytes()
        config = validate_config(json.loads(config_bytes.decode("utf-8")))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        parser.error(f"cannot load paired evaluation config: {exc}")
    except EvaluationError as exc:
        parser.error(str(exc))
    trials = args.trials if args.trials is not None else config.get("default_trials", 3)
    if not isinstance(trials, int) or isinstance(trials, bool) or trials < 3:
        parser.error("paired evaluations require at least three independent trials")
    executor_command = shlex.split(args.executor)
    grader_command = shlex.split(args.grader)
    if not executor_command or not grader_command:
        parser.error("executor and grader commands must not be empty")
    selected_ids = set(args.pair)
    pairs = [item for item in config.get("pairs", []) if not selected_ids or item.get("id") in selected_ids]
    missing = selected_ids - {item.get("id") for item in pairs}
    if missing:
        parser.error(f"unknown pair ids: {sorted(missing)}")
    if not pairs:
        parser.error("no paired evaluation cases were selected")
    release_plan = config.get("release_plan") or {
        "pair_ids": [item["id"] for item in config["pairs"]],
        "trials_per_pair": config["default_trials"],
    }
    if args.release:
        if config["schema_version"] != "1.1":
            parser.error("--release requires canonical paired evaluation config schema 1.1")
        if args.config.is_symlink() or args.config.resolve() != CANONICAL_CONFIG.resolve():
            parser.error(f"--release requires the canonical config at {CANONICAL_CONFIG}")
        if args.pair:
            parser.error("--release requires the complete configured pair set; --pair is not allowed")
        if trials != release_plan["trials_per_pair"]:
            parser.error(f"--release requires exactly {release_plan['trials_per_pair']} trials per pair")
        if not isinstance(args.expected_commit, str) or not re.fullmatch(r"[0-9a-f]{40}", args.expected_commit):
            parser.error("--release requires --expected-commit as a full lowercase 40-character SHA")
    elif args.expected_commit is not None:
        parser.error("--expected-commit is only valid with --release")
    evaluated_pair_ids = [item["id"] for item in pairs]
    config_digest = "sha256:" + hashlib.sha256(config_bytes).hexdigest()
    preflight_source = source_identity(args.expected_commit)
    preflight_config = config_identity(args.config, config_digest, args.expected_commit)
    evaluation_plan = {
        "mode": "release" if args.release else "pilot",
        "config_schema_version": config["schema_version"],
        "required_pair_ids": release_plan["pair_ids"],
        "evaluated_pair_ids": evaluated_pair_ids,
        "required_trials_per_pair": release_plan["trials_per_pair"],
        "actual_trials_per_pair": trials,
        "config_sha256": config_digest,
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
    for pair in pairs:
        pair_id = pair["id"]
        fixture_path = contained_path(
            ROOT / "evals",
            pair["fixture"],
            label=f"{pair_id} fixture",
            require_relative=True,
            reject_symlinks=True,
        )
        fixture = input_values[pair_id]["fixture"]
        for trial in range(1, trials + 1):
            order = VARIANTS if trial % 2 else tuple(reversed(VARIANTS))
            for variant in order:
                run_root = contained_path(
                    output,
                    Path(pair_id) / f"trial-{trial}" / variant / "executor",
                    label="executor run root",
                    require_relative=True,
                    reject_symlinks=True,
                )
                request = {
                    "schema_version": "1.0",
                    "case_id": pair_id,
                    "trial": trial,
                    "attempt": 1,
                    "condition": "with-capabilities" if variant == "candidate" else "without-capabilities",
                    "capabilities": pair["capabilities"] if variant == "candidate" else [],
                    "capability_sources": (
                        input_values[pair_id]["capability_sources"] if variant == "candidate" else {}
                    ),
                    "fixture_path": str(fixture_path),
                    "fixture": fixture,
                }
                raw_executor, executor_error, runner_elapsed = run_program(executor_command, request, run_root, args.timeout)
                executor: dict[str, Any] | None = None
                if executor_error is None:
                    try:
                        executor = validate_executor(raw_executor, run_root, pair_id)
                        write_json(run_root / "result.json", executor)
                    except (EvaluationError, OSError, PathContractError) as exc:
                        executor_error = str(exc)
                grader: dict[str, Any] | None = None
                grader_error: str | None = None
                grader_elapsed: float | None = None
                grader_archive: Path | None = None
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
                        artifact_snapshot = grader_root / "executor-artifacts"
                        try:
                            shutil.copytree(Path(executor["artifact_root"]), artifact_snapshot)
                        except OSError as exc:
                            grader_error = f"cannot snapshot executor artifacts: {exc}"
                        else:
                            blinded_executor = {**executor, "artifact_root": str(artifact_snapshot)}
                            grader_request = {
                                "schema_version": "1.0",
                                "case_id": pair_id,
                                "attempt": 1,
                                "fixture_path": str(fixture_path),
                                "fixture": fixture,
                                "executor_result": blinded_executor,
                                "deterministic_oracle": pair["deterministic_oracle"],
                            }
                            raw_grader, grader_error, grader_elapsed = run_program(
                                grader_command,
                                grader_request,
                                grader_root,
                                args.timeout,
                            )
                            if grader_error is None:
                                try:
                                    grader = validate_grader(raw_grader, pair_id)
                                    write_json(grader_root / "result.json", grader)
                                except (EvaluationError, OSError, PathContractError) as exc:
                                    grader_error = str(exc)
                                    try:
                                        atomic_write_text(grader_root / "runner-error.txt", grader_error + "\n")
                                    except (OSError, PathContractError):
                                        pass
                        try:
                            grader_archive.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copytree(grader_root, grader_archive)
                        except OSError as exc:
                            grader_error = grader_error or f"cannot archive grader evidence: {exc}"
                record = {
                    "pair_id": pair_id,
                    "trial": trial,
                    "variant": variant,
                    "executor": executor,
                    "grader": grader,
                    "executor_error": executor_error,
                    "grader_error": grader_error,
                    "runner_elapsed_seconds": runner_elapsed,
                    "grader_runner_elapsed_seconds": grader_elapsed,
                    "grader_run_root": str(grader_archive) if grader_archive else None,
                }
                records.append(record)
                if executor_error or grader_error:
                    errors.append(f"{pair_id}/trial-{trial}/{variant}: {executor_error or grader_error}")

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
    if args.release:
        errors.extend(
            finalize_release_identity(
                evaluation_plan,
                config_path=args.config,
                config_digest=config_digest,
                expected_commit=args.expected_commit,
            )
        )
    report = {
        "schema_version": "1.0",
        "status": "complete" if not errors else "incomplete",
        "seed": args.seed,
        "trials_per_pair": trials,
        "pair_ids": evaluated_pair_ids,
        "evaluation_plan": evaluation_plan,
        "commands": {"executor": executor_command, "grader": grader_command},
        "metric_contract": list(CONTRACT_METRICS),
        "records": records,
        "aggregates": {"baseline": baseline, "candidate": candidate},
        "pair_aggregates": pair_aggregates,
        "candidate_minus_baseline": aggregate_delta(candidate, baseline),
        "release_assessment": assess_release(candidate, baseline, config["release_thresholds"], evaluation_plan),
        "isolation": {
            "executor_artifacts": "strict descendant only; symlinks and oversized snapshots rejected",
            "grader_workspace": "opaque temporary root outside the labeled executor output tree",
            "grader_input": "fixture, oracle, and sanitized executor result only; no variant, condition, or capability list",
            "security_boundary": "structural blinding; evaluator commands retain the ambient operating-system user authority",
            "process_ownership": "owned process group or Windows Job Object with bounded output and descendant teardown",
        },
        "interpretation": {
            "higher_is_better": ["pass_rate", "requirement_fidelity", "coverage", "restraint", "ordinary_defect_retention", "actionability"],
            "lower_is_better": ["rework", "context_cost", "unsafe_actions", "reminder_rate", "false_block_rate"],
            "statistical_claim": "descriptive mean and population standard deviation only; increase trials before significance claims",
            "rate_denominators": {
                "reminder_rate": "valid executor runs",
                "false_block_rate": "valid grader runs",
            },
        },
        "errors": errors,
    }
    try:
        write_json(output / "report.json", report)
    except (OSError, PathContractError) as exc:
        print(json.dumps({"status": "incomplete", "errors": [f"cannot write evaluation report: {exc}"]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps({"status": report["status"], "report": str(output / "report.json"), "runs": len(records), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
