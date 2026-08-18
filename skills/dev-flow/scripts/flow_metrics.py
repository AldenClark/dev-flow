#!/usr/bin/env python3
"""Compatibility-named Flow Activation Coverage runner with no effect score."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


class ActivationContractError(ValueError):
    """Raised when a Flow Activation Coverage fixture is invalid."""


def value_at(payload: Any, dotted_path: str) -> Any:
    value = payload
    for segment in dotted_path.split("."):
        if not isinstance(value, dict) or segment not in value:
            raise ActivationContractError(f"missing result path {dotted_path!r}")
        value = value[segment]
    return value


def flattened_values(value: Any) -> list[Any]:
    if isinstance(value, dict):
        result: list[Any] = []
        for key, child in value.items():
            result.append(key)
            result.extend(flattened_values(child))
        return result
    if isinstance(value, list):
        result = []
        for child in value:
            result.extend(flattened_values(child))
        return result
    return [value]


def validate_catalog(catalog: Any) -> dict[str, Any]:
    """Validate the deterministic public-command catalog."""
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "purpose", "cases"}:
        raise ActivationContractError("catalog must contain schema_version, purpose, and cases")
    if catalog["schema_version"] != "1.0" or not isinstance(catalog["purpose"], str):
        raise ActivationContractError("catalog requires schema_version 1.0 and a purpose")
    cases = catalog["cases"]
    if not isinstance(cases, list) or not cases:
        raise ActivationContractError("catalog cases must be a non-empty list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not set(case).issubset({"id", "command", "expect", "contains", "excludes"}):
            raise ActivationContractError("each case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ActivationContractError("case ids must be unique non-empty strings")
        seen.add(case_id)
        command = case.get("command")
        if not isinstance(command, list) or not command or any(not isinstance(item, str) or not item for item in command):
            raise ActivationContractError(f"{case_id}: command must be a non-empty string list")
        for field in ("expect", "contains", "excludes"):
            checks = case.get(field, {})
            if not isinstance(checks, dict) or any(not isinstance(path, str) or not path for path in checks):
                raise ActivationContractError(f"{case_id}: {field} must be an object keyed by result path")
    return catalog


def validate_semantic_catalog(catalog: Any) -> dict[str, Any]:
    """Validate bounded natural-language activation fixtures without executing a model."""
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "purpose", "cases"}:
        raise ActivationContractError("semantic catalog must contain schema_version, purpose, and cases")
    if catalog["schema_version"] != "1.0" or not isinstance(catalog["purpose"], str):
        raise ActivationContractError("semantic catalog requires schema_version 1.0 and a purpose")
    cases = catalog["cases"]
    if not isinstance(cases, list) or not cases:
        raise ActivationContractError("semantic catalog cases must be a non-empty list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id", "repository", "prompt", "expected", "forbidden"
        }:
            raise ActivationContractError("each semantic case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ActivationContractError("semantic case ids must be unique non-empty strings")
        seen.add(case_id)
        repository = case.get("repository")
        if (
            not isinstance(repository, dict)
            or not repository
            or any(not isinstance(path, str) or not path or not isinstance(text, str) for path, text in repository.items())
        ):
            raise ActivationContractError(f"{case_id}: repository must map non-empty paths to strings")
        if not isinstance(case.get("prompt"), str) or not case["prompt"]:
            raise ActivationContractError(f"{case_id}: prompt must be a non-empty string")
        for field in ("expected", "forbidden"):
            values = case.get(field)
            if (
                not isinstance(values, list)
                or not values
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ActivationContractError(f"{case_id}: {field} must be a unique non-empty string list")
        overlap = sorted(set(case["expected"]) & set(case["forbidden"]))
        if overlap:
            raise ActivationContractError(f"{case_id}: activation cannot be expected and forbidden: {overlap}")
    return catalog


def validate_semantic_observations(observations: Any, case_ids: set[str]) -> dict[str, Any]:
    """Validate first-attempt observations produced outside this cost-free evaluator."""
    if not isinstance(observations, dict) or set(observations) != {"schema_version", "cases"}:
        raise ActivationContractError("observations must contain schema_version and cases")
    if observations["schema_version"] != "flow.activation.observations.v1":
        raise ActivationContractError("observations require schema_version flow.activation.observations.v1")
    cases = observations["cases"]
    if not isinstance(cases, list):
        raise ActivationContractError("observation cases must be a list")
    seen: set[str] = set()
    allowed = {"id", "observed", "evidence", "unmet_prerequisites", "authority_violations"}
    for case in cases:
        if not isinstance(case, dict) or set(case) != allowed:
            raise ActivationContractError("each observation case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ActivationContractError("observation case ids must be unique non-empty strings")
        if case_id not in case_ids:
            raise ActivationContractError(f"unknown observation case {case_id!r}")
        seen.add(case_id)
        for field in ("observed", "evidence", "unmet_prerequisites", "authority_violations"):
            values = case.get(field)
            if (
                not isinstance(values, list)
                or any(not isinstance(value, str) or not value for value in values)
                or len(values) != len(set(values))
            ):
                raise ActivationContractError(f"{case_id}: {field} must be a unique string list")
        if not case["evidence"]:
            raise ActivationContractError(f"{case_id}: evidence must identify the observed first attempt")
    return observations


def run_catalog(catalog_path: Path, flow_path: Path) -> dict[str, Any]:
    catalog = validate_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    results: list[dict[str, Any]] = []
    for case in catalog["cases"]:
        completed = subprocess.run(
            [sys.executable, str(flow_path), *case["command"]],
            check=False,
            capture_output=True,
            text=True,
            cwd=flow_path.parents[3],
        )
        observations: list[str] = []
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = {}
            observations.append("command did not return JSON")
        if completed.returncode != 0:
            observations.append(f"command exited {completed.returncode}")
        for path, expected in case.get("expect", {}).items():
            try:
                observed = value_at(payload, path)
                if observed != expected:
                    observations.append(f"{path}: expected {expected!r}, observed {observed!r}")
            except ActivationContractError as exc:
                observations.append(str(exc))
        for field, should_exist in (("contains", True), ("excludes", False)):
            for path, expected in case.get(field, {}).items():
                try:
                    observed_values = flattened_values(value_at(payload, path))
                    expected_values = expected if isinstance(expected, list) else [expected]
                    for expected_value in expected_values:
                        observed = expected_value in observed_values
                        if observed != should_exist:
                            observations.append(
                                f"{path}: expected {expected_value!r} to be "
                                f"{'present' if should_exist else 'absent'}"
                            )
                except ActivationContractError as exc:
                    observations.append(str(exc))
        results.append(
            {
                "id": case["id"],
                "status": "matched" if not observations else "mismatched",
                "observations": observations,
            }
        )
    mismatched = [result["id"] for result in results if result["status"] == "mismatched"]
    return {
        "status": "matched" if not mismatched else "mismatched",
        "schema_version": "flow.activation.coverage.v1",
        "purpose": "branch activation and negative-trigger coverage only",
        "effect_measurement": False,
        "aggregate_score": None,
        "cases": len(results),
        "matched": len(results) - len(mismatched),
        "mismatched": mismatched,
        "results": results,
    }


def run_semantic_catalog(catalog_path: Path, observations_path: Path) -> dict[str, Any]:
    """Compare pre-recorded first-attempt activation with semantic fixture boundaries."""
    catalog = validate_semantic_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    case_ids = {case["id"] for case in catalog["cases"]}
    observations = validate_semantic_observations(
        json.loads(observations_path.read_text(encoding="utf-8")),
        case_ids,
    )
    by_id = {case["id"]: case for case in observations["cases"]}
    results: list[dict[str, Any]] = []
    for case in catalog["cases"]:
        case_id = case["id"]
        observation = by_id.get(case_id)
        if observation is None:
            details = ["first-attempt observation is missing"]
            observed: list[str] = []
            evidence: list[str] = []
            unmet: list[str] = []
            violations: list[str] = []
        else:
            observed = observation["observed"]
            evidence = observation["evidence"]
            unmet = observation["unmet_prerequisites"]
            violations = observation["authority_violations"]
            missing = sorted(set(case["expected"]) - set(observed))
            forbidden = sorted(set(case["forbidden"]) & set(observed))
            details = []
            if missing:
                details.append(f"missing expected activation: {missing}")
            if forbidden:
                details.append(f"forbidden activation observed: {forbidden}")
            if unmet:
                details.append(f"unmet prerequisites: {unmet}")
            if violations:
                details.append(f"authority violations: {violations}")
        results.append(
            {
                "id": case_id,
                "status": "matched" if not details else "mismatched",
                "observed": observed,
                "evidence": evidence,
                "observations": details,
            }
        )
    mismatched = [result["id"] for result in results if result["status"] == "mismatched"]
    return {
        "status": "matched" if not mismatched else "mismatched",
        "schema_version": "flow.activation.coverage.v1",
        "lane": "semantic-observation",
        "purpose": "first-attempt branch activation and negative-trigger coverage only",
        "effect_measurement": False,
        "aggregate_score": None,
        "cases": len(results),
        "matched": len(results) - len(mismatched),
        "mismatched": mismatched,
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    script = Path(__file__).resolve()
    repository = script.parents[3]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy_catalog", nargs="?", type=Path)
    parser.add_argument("--lane", choices=("deterministic", "semantic"), default="deterministic")
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.catalog and args.legacy_catalog:
        parser.error("use either positional catalog compatibility or --catalog, not both")
    default_name = "flow-activation-semantic-cases.json" if args.lane == "semantic" else "flow-activation-cases.json"
    catalog = (args.catalog or args.legacy_catalog or repository / "evals" / default_name).resolve()
    try:
        if args.lane == "semantic":
            if args.observations is None:
                raise ActivationContractError("semantic lane requires --observations from actual first attempts")
            result = run_semantic_catalog(catalog, args.observations.resolve())
        else:
            if args.observations is not None:
                raise ActivationContractError("--observations is only valid for the semantic lane")
            result = run_catalog(catalog, script.with_name("dev-flow.py"))
    except (OSError, json.JSONDecodeError, ActivationContractError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "matched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
