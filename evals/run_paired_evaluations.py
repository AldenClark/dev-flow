#!/usr/bin/env python3
"""Run isolated, counterbalanced Dev Flow capability evaluations."""

from __future__ import annotations

import argparse
import json
import math
import random
import shlex
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from statistics import fmean
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ("baseline", "candidate")
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
METRIC_KEYS = {"coverage", "restraint", "actionability", "rework", "unsafe_actions", "false_blocks"}


class EvaluationError(ValueError):
    pass


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
    artifact_root = Path(result["artifact_root"])
    if not artifact_root.is_absolute():
        artifact_root = (run_root / artifact_root).resolve()
    else:
        artifact_root = artifact_root.resolve()
    if artifact_root != run_root and not artifact_root.is_relative_to(run_root):
        raise EvaluationError("executor artifact_root escapes its isolated run directory")
    if not artifact_root.is_dir():
        raise EvaluationError("executor artifact_root must be an existing directory")
    if any(path.is_symlink() for path in artifact_root.rglob("*")):
        raise EvaluationError("executor artifact_root must not contain symlinks")
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
    for key in ("coverage", "restraint", "actionability", "rework"):
        require_score(metrics[key], f"metrics.{key}")
    for key in ("unsafe_actions", "false_blocks"):
        require_nonnegative_integer(metrics[key], f"metrics.{key}")
    if result["verdict"] not in {"pass", "fail", "inconclusive"}:
        raise EvaluationError("grader verdict is invalid")
    return result


def run_program(command: list[str], request: dict[str, Any], cwd: Path, timeout: int) -> tuple[dict[str, Any] | None, str | None, float]:
    cwd.mkdir(parents=True, exist_ok=True)
    write_json(cwd / "request.json", request)
    started = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        elapsed = time.monotonic() - started
        (cwd / "runner-error.txt").write_text(str(exc) + "\n", encoding="utf-8")
        return None, str(exc), elapsed
    elapsed = time.monotonic() - started
    (cwd / "stdout.txt").write_text(result.stdout, encoding="utf-8")
    (cwd / "stderr.txt").write_text(result.stderr, encoding="utf-8")
    if result.returncode:
        return None, f"program exited {result.returncode}", elapsed
    try:
        parsed = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, f"stdout is not one JSON value: {exc}", elapsed
    if not isinstance(parsed, dict):
        return None, "stdout JSON must be an object", elapsed
    return parsed, None, elapsed


def finite_mean(values: list[Any]) -> float | None:
    numbers = [float(value) for value in values if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)]
    return fmean(numbers) if numbers else None


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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--executor", required=True, help="Quoted executor command; receives one JSON request on stdin")
    parser.add_argument("--grader", required=True, help="Quoted independent grader command; receives one blind JSON request on stdin")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "evals" / "paired-evaluations.json")
    parser.add_argument("--pair", action="append", default=[])
    parser.add_argument("--trials", type=int)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.timeout < 1:
        parser.error("--timeout must be positive")
    output = args.output.resolve()
    if output.exists():
        if not output.is_dir():
            parser.error(f"--output must be a directory: {output}")
        if any(output.iterdir()):
            parser.error(f"--output must be absent or empty: {output}")
    output.mkdir(parents=True, exist_ok=True)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"cannot load paired evaluation config: {exc}")
    if not isinstance(config, dict) or not isinstance(config.get("pairs"), list):
        parser.error("paired evaluation config must be an object with a pairs list")
    pair_keys = {"id", "fixture", "capabilities", "deterministic_oracle"}
    seen_pair_ids: set[str] = set()
    for index, pair in enumerate(config["pairs"]):
        try:
            checked = require_exact_object(pair, pair_keys, f"pairs[{index}]")
            if not isinstance(checked["id"], str) or not checked["id"].strip() or checked["id"] in seen_pair_ids:
                raise EvaluationError(f"pairs[{index}].id must be a unique non-empty string")
            seen_pair_ids.add(checked["id"])
            if not isinstance(checked["fixture"], str) or not checked["fixture"].strip():
                raise EvaluationError(f"pairs[{index}].fixture must be a non-empty string")
            require_text_list(checked["capabilities"], f"pairs[{index}].capabilities")
            if not checked["capabilities"]:
                raise EvaluationError(f"pairs[{index}].capabilities must not be empty")
            if not isinstance(checked["deterministic_oracle"], str) or not checked["deterministic_oracle"].strip():
                raise EvaluationError(f"pairs[{index}].deterministic_oracle must be a non-empty string")
            fixture = (ROOT / "evals" / checked["fixture"]).resolve()
            eval_root = (ROOT / "evals").resolve()
            if not fixture.is_relative_to(eval_root) or not fixture.is_file():
                raise EvaluationError(f"pairs[{index}].fixture must resolve to an eval fixture")
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
    random.Random(args.seed).shuffle(pairs)

    records: list[dict[str, Any]] = []
    errors: list[str] = []
    for pair in pairs:
        pair_id = pair["id"]
        fixture_path = (ROOT / "evals" / pair["fixture"]).resolve()
        fixture = fixture_path.read_text(encoding="utf-8")
        for trial in range(1, trials + 1):
            order = VARIANTS if trial % 2 else tuple(reversed(VARIANTS))
            for variant in order:
                run_root = output / pair_id / f"trial-{trial}" / variant / "executor"
                request = {
                    "schema_version": "1.0",
                    "case_id": pair_id,
                    "trial": trial,
                    "attempt": 1,
                    "condition": "with-capabilities" if variant == "candidate" else "without-capabilities",
                    "capabilities": pair["capabilities"] if variant == "candidate" else [],
                    "fixture_path": str(fixture_path),
                    "fixture": fixture,
                }
                raw_executor, executor_error, runner_elapsed = run_program(executor_command, request, run_root, args.timeout)
                executor: dict[str, Any] | None = None
                if executor_error is None:
                    try:
                        executor = validate_executor(raw_executor, run_root, pair_id)
                        write_json(run_root / "result.json", executor)
                    except EvaluationError as exc:
                        executor_error = str(exc)
                grader: dict[str, Any] | None = None
                grader_error: str | None = None
                grader_elapsed: float | None = None
                grader_root: Path | None = None
                if executor is not None:
                    grader_root = output / "grader-runs" / uuid.uuid4().hex
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
                        raw_grader, grader_error, grader_elapsed = run_program(grader_command, grader_request, grader_root, args.timeout)
                        if grader_error is None:
                            try:
                                grader = validate_grader(raw_grader, pair_id)
                                write_json(grader_root / "result.json", grader)
                            except EvaluationError as exc:
                                grader_error = str(exc)
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
                    "grader_run_root": str(grader_root) if grader_root else None,
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
    report = {
        "schema_version": "1.0",
        "status": "complete" if not errors else "incomplete",
        "seed": args.seed,
        "trials_per_pair": trials,
        "pair_ids": [item["id"] for item in pairs],
        "commands": {"executor": executor_command, "grader": grader_command},
        "records": records,
        "aggregates": {"baseline": baseline, "candidate": candidate},
        "pair_aggregates": pair_aggregates,
        "candidate_minus_baseline": aggregate_delta(candidate, baseline),
        "interpretation": {
            "higher_is_better": ["pass_rate", "quality.*", "coverage", "restraint", "actionability"],
            "lower_is_better": ["rework", "unsafe_actions", "false_blocks", "interaction.*", "usage.*"],
            "statistical_claim": "descriptive only; increase trials and analyze variance before significance claims",
        },
        "errors": errors,
    }
    write_json(output / "report.json", report)
    print(json.dumps({"status": report["status"], "report": str(output / "report.json"), "runs": len(records), "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
