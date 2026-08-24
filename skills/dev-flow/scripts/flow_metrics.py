#!/usr/bin/env python3
"""Compatibility-named Flow Activation Coverage runner with no effect score."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any


class ActivationContractError(ValueError):
    """Raised when a Flow Activation Coverage fixture is invalid."""


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
R4_CATEGORY_IDS = {
    "implicit-entry",
    "material-transition",
    "failure-isolation",
    "method-disposition-realization",
    "evidence-freshness",
    "scope-convergence",
    "constraint-preservation",
    "context-synthesis-adaptation",
    "negative-control-quietness",
}
TRANSITION_FIXTURE_MAX_FILES = 8
TRANSITION_FIXTURE_MAX_FILE_BYTES = 64 * 1024
TRANSITION_FIXTURE_MAX_TOTAL_BYTES = 256 * 1024
TRANSITION_REPOSITORY_MAX_FILES = 256
TRANSITION_REPOSITORY_MAX_FILE_BYTES = 64 * 1024
TRANSITION_REPOSITORY_MAX_TOTAL_BYTES = 1024 * 1024
TRANSITION_FIXTURE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
TRANSITION_UNMET_LABELS = {"blocked-claim", "no-invariant-retry"}


def transition_fixture_path_is_safe(path: Any) -> bool:
    """Return whether a fixture path is a canonical safe Python file operand."""
    if (
        not isinstance(path, str)
        or not path
        or path == "."
        or path.startswith("-")
        or TRANSITION_FIXTURE_PATH_RE.fullmatch(path) is None
    ):
        return False
    normalized = PurePosixPath(path)
    return (
        not normalized.is_absolute()
        and normalized.as_posix() == path
        and ".." not in normalized.parts
        and not any(part.rstrip(".").casefold() == ".git" for part in normalized.parts)
    )


def transition_fixture_evidence_bytes(fixture: dict[str, str]) -> int:
    """Return a worst-case encoded fixture delta size for assessment preflight."""
    digest = "sha256:" + "0" * 64
    delta = [
        {
            "path": path,
            "before_sha256": digest,
            "after_sha256": digest,
            "after_text": content,
        }
        for path, content in sorted(fixture.items())
    ]
    return len(json.dumps(delta, ensure_ascii=False).encode("utf-8"))


def validate_transition_repository_fixture(repository: Any) -> dict[str, str]:
    """Validate the complete initial fixture before any filesystem write."""
    if (
        not isinstance(repository, dict)
        or not repository
        or len(repository) > TRANSITION_REPOSITORY_MAX_FILES
    ):
        raise ActivationContractError(
            "initial repository fixture must be a bounded non-empty object"
        )
    identities: set[tuple[str, ...]] = set()
    total_bytes = 0
    for path, content in repository.items():
        if not transition_fixture_path_is_safe(path) or not isinstance(content, str):
            raise ActivationContractError(
                "initial repository fixture contains an unsafe path or non-string content"
            )
        identity = tuple(
            part.rstrip(".").casefold() for part in PurePosixPath(path).parts
        )
        if identity in identities:
            raise ActivationContractError(
                "initial repository fixture contains a host-ambiguous path alias"
            )
        identities.add(identity)
        encoded_bytes = len(content.encode("utf-8"))
        if encoded_bytes > TRANSITION_REPOSITORY_MAX_FILE_BYTES:
            raise ActivationContractError(
                "initial repository fixture exceeds its per-file byte bound"
            )
        total_bytes += encoded_bytes
        if total_bytes > TRANSITION_REPOSITORY_MAX_TOTAL_BYTES:
            raise ActivationContractError(
                "initial repository fixture exceeds its total byte bound"
            )
    if any(
        identity[:depth] in identities
        for identity in identities
        for depth in range(1, len(identity))
    ):
        raise ActivationContractError(
            "initial repository fixture contains a file/directory path collision"
        )
    return repository


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


def validate_transition_catalog(catalog: Any) -> dict[str, Any]:
    """Validate multi-turn activation fixtures without invoking a model."""
    if not isinstance(catalog, dict) or set(catalog) != {
        "schema_version",
        "purpose",
        "qualification",
        "cases",
    }:
        raise ActivationContractError(
            "transition catalog must contain schema_version, purpose, qualification, and cases"
        )
    if catalog["schema_version"] != "flow.transition.catalog.v1" or not isinstance(
        catalog["purpose"], str
    ):
        raise ActivationContractError(
            "transition catalog requires schema_version flow.transition.catalog.v1 and a purpose"
        )
    qualification = catalog["qualification"]
    if not isinstance(qualification, dict) or set(qualification) != {
        "release_tier",
        "minimum_cases_per_category",
        "minimum_first_attempts_per_case",
        "categories",
    }:
        raise ActivationContractError("transition qualification has invalid fields")
    if qualification["release_tier"] != "R4":
        raise ActivationContractError("transition qualification release_tier must be R4")
    for field in ("minimum_cases_per_category", "minimum_first_attempts_per_case"):
        value = qualification[field]
        if not isinstance(value, int) or isinstance(value, bool) or value < 3:
            raise ActivationContractError(f"transition qualification {field} must be at least 3")
    categories = qualification["categories"]
    if (
        not isinstance(categories, list)
        or set(categories) != R4_CATEGORY_IDS
        or len(categories) != len(R4_CATEGORY_IDS)
    ):
        raise ActivationContractError(
            "transition qualification categories must contain the nine canonical R4 categories exactly once"
        )
    cases = catalog["cases"]
    if not isinstance(cases, list) or not cases:
        raise ActivationContractError("transition catalog cases must be a non-empty list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "categories",
            "lineage",
            "repository",
            "turns",
        }:
            raise ActivationContractError("each transition case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise ActivationContractError("transition case ids must be unique non-empty strings")
        seen.add(case_id)
        case_categories = case.get("categories")
        if (
            not isinstance(case_categories, list)
            or not case_categories
            or any(category not in R4_CATEGORY_IDS for category in case_categories)
            or len(case_categories) != len(set(case_categories))
        ):
            raise ActivationContractError(
                f"{case_id}: categories must be a unique non-empty subset of the R4 categories"
            )
        if case.get("lineage") not in {"resume", "fork"}:
            raise ActivationContractError(f"{case_id}: lineage must be resume or fork")
        try:
            repository = validate_transition_repository_fixture(case.get("repository"))
        except ActivationContractError as exc:
            raise ActivationContractError(f"{case_id}: {exc}") from exc
        turns = case.get("turns")
        if not isinstance(turns, list) or len(turns) < 2:
            raise ActivationContractError(f"{case_id}: turns must contain at least two turns")
        for turn_number, turn in enumerate(turns, 1):
            required_turn_fields = {
                "prompt",
                "expected",
                "forbidden",
                "mutation",
            }
            optional_turn_fields = {
                "expected_unmet",
                "pre_turn_fixture",
                "mutation_paths",
            }
            if (
                not isinstance(turn, dict)
                or not required_turn_fields <= set(turn)
                or not set(turn) <= required_turn_fields | optional_turn_fields
            ):
                raise ActivationContractError(f"{case_id} turn {turn_number}: invalid fields")
            if not isinstance(turn.get("prompt"), str) or not turn["prompt"]:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: prompt must be non-empty"
                )
            if turn.get("mutation") not in {"none", "repository"}:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: mutation must be none or repository"
                )
            mutation_paths = turn.get("mutation_paths")
            if turn["mutation"] == "repository":
                if (
                    not isinstance(mutation_paths, list)
                    or not mutation_paths
                    or any(
                        not transition_fixture_path_is_safe(path)
                        for path in mutation_paths
                    )
                    or len(mutation_paths) != len(set(mutation_paths))
                    or not set(mutation_paths) <= set(repository)
                ):
                    raise ActivationContractError(
                        f"{case_id} turn {turn_number}: repository mutation requires unique existing mutation_paths"
                    )
            elif mutation_paths is not None:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: mutation=none forbids mutation_paths"
                )
            if not isinstance(turn.get("expected_unmet", False), bool):
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: expected_unmet must be boolean"
                )
            fixture = turn.get("pre_turn_fixture", {})
            if (
                not isinstance(fixture, dict)
                or len(fixture) > TRANSITION_FIXTURE_MAX_FILES
                or any(
                    not transition_fixture_path_is_safe(path)
                    or not isinstance(content, str)
                    or len(content.encode("utf-8"))
                    > TRANSITION_FIXTURE_MAX_FILE_BYTES
                    for path, content in fixture.items()
                )
            ):
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: pre_turn_fixture is invalid"
                )
            if (
                transition_fixture_evidence_bytes(fixture)
                > TRANSITION_FIXTURE_MAX_TOTAL_BYTES
            ):
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: pre_turn_fixture exceeds its assessment evidence byte bound"
                )
            for field in ("expected", "forbidden"):
                values = turn.get(field)
                if (
                    not isinstance(values, list)
                    or not values
                    or any(not isinstance(value, str) or not value for value in values)
                    or len(values) != len(set(values))
                ):
                    raise ActivationContractError(
                        f"{case_id} turn {turn_number}: {field} must be a unique non-empty string list"
                    )
            overlap = sorted(set(turn["expected"]) & set(turn["forbidden"]))
            if overlap:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: expected/forbidden overlap: {overlap}"
                )
            expected_implies_unmet = bool(
                set(turn["expected"]) & TRANSITION_UNMET_LABELS
            )
            if turn.get("expected_unmet", False) and not expected_implies_unmet:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: expected_unmet requires a semantically entailing expected label"
                )
            if not turn.get("expected_unmet", False) and expected_implies_unmet:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: unmet-implying expected label requires expected_unmet"
                )
            if "readiness-fact-changed" in turn["expected"] and not fixture:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: readiness-fact-changed requires a runner-owned pre_turn_fixture"
                )
            if "one-justified-retry" in turn["expected"] and not fixture:
                raise ActivationContractError(
                    f"{case_id} turn {turn_number}: one-justified-retry requires a runner-owned pre_turn_fixture"
                )
    minimum_cases = qualification["minimum_cases_per_category"]
    coverage = {
        category: [case["id"] for case in cases if category in case["categories"]]
        for category in categories
    }
    underfilled = {
        category: case_ids
        for category, case_ids in coverage.items()
        if len(case_ids) < minimum_cases
    }
    if underfilled:
        raise ActivationContractError(
            f"transition qualification categories require at least {minimum_cases} cases: {underfilled}"
        )
    return catalog


def validate_transition_observations(
    observations: Any,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate sanitized turn-bound observations produced by an external runner."""
    if not isinstance(observations, dict) or set(observations) != {"schema_version", "cases"}:
        raise ActivationContractError(
            "transition observations must contain schema_version and cases"
        )
    if observations["schema_version"] != "flow.transition.observations.v1":
        raise ActivationContractError(
            "transition observations require schema_version flow.transition.observations.v1"
        )
    catalog_by_id = {case["id"]: case for case in catalog["cases"]}
    cases = observations["cases"]
    if not isinstance(cases, list):
        raise ActivationContractError("transition observation cases must be a list")
    seen_cases: set[str] = set()
    seen_evidence: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {
            "id",
            "lineage_id",
            "initial_git_head_sha256",
            "initial_repository_sha256",
            "turns",
        }:
            raise ActivationContractError("each transition observation case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen_cases:
            raise ActivationContractError(
                "transition observation case ids must be unique non-empty strings"
            )
        if case_id not in catalog_by_id:
            raise ActivationContractError(f"unknown transition observation case {case_id!r}")
        seen_cases.add(case_id)
        if not isinstance(case.get("lineage_id"), str) or not case["lineage_id"]:
            raise ActivationContractError(f"{case_id}: lineage_id must be non-empty")
        initial_repository_sha = case.get("initial_repository_sha256")
        if not isinstance(initial_repository_sha, str) or SHA256_RE.fullmatch(
            initial_repository_sha
        ) is None:
            raise ActivationContractError(
                f"{case_id}: initial_repository_sha256 must be a sha256 digest"
            )
        initial_git_head_sha = case.get("initial_git_head_sha256")
        if not isinstance(initial_git_head_sha, str) or SHA256_RE.fullmatch(
            initial_git_head_sha
        ) is None:
            raise ActivationContractError(
                f"{case_id}: initial_git_head_sha256 must be a sha256 digest"
            )
        turns = case.get("turns")
        if not isinstance(turns, list):
            raise ActivationContractError(f"{case_id}: turns must be a list")
        seen_turns: set[int] = set()
        last_turn = 0
        previous_repository_sha = initial_repository_sha
        for item in turns:
            allowed = {
                "turn",
                "observed",
                "evidence",
                "evidence_sha256",
                "repository_sha256",
                "unmet_prerequisites",
                "authority_violations",
            }
            if not isinstance(item, dict) or set(item) != allowed:
                raise ActivationContractError(
                    f"{case_id}: each transition turn observation has invalid fields"
                )
            turn = item.get("turn")
            if (
                not isinstance(turn, int)
                or isinstance(turn, bool)
                or turn < 1
                or turn > len(catalog_by_id[case_id]["turns"])
                or turn in seen_turns
            ):
                raise ActivationContractError(f"{case_id}: invalid or duplicate turn {turn!r}")
            if turn <= last_turn:
                raise ActivationContractError(
                    f"{case_id}: turn observations must be ordered by turn number"
                )
            seen_turns.add(turn)
            last_turn = turn
            for field in (
                "observed",
                "evidence",
                "unmet_prerequisites",
                "authority_violations",
            ):
                values = item.get(field)
                if (
                    not isinstance(values, list)
                    or any(not isinstance(value, str) or not value for value in values)
                    or len(values) != len(set(values))
                ):
                    raise ActivationContractError(
                        f"{case_id} turn {turn}: {field} must be a unique string list"
                    )
            if not item["evidence"]:
                raise ActivationContractError(f"{case_id} turn {turn}: evidence is required")
            for field in ("evidence_sha256", "repository_sha256"):
                value = item.get(field)
                if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
                    raise ActivationContractError(
                        f"{case_id} turn {turn}: {field} must be a sha256 digest"
                    )
            if item["evidence_sha256"] in seen_evidence:
                raise ActivationContractError(
                    f"{case_id} turn {turn}: evidence digest was reused across turns"
                )
            seen_evidence.add(item["evidence_sha256"])
            expected_mutation = catalog_by_id[case_id]["turns"][turn - 1]["mutation"]
            repository_changed = item["repository_sha256"] != previous_repository_sha
            if expected_mutation == "repository" and not repository_changed:
                raise ActivationContractError(
                    f"{case_id} turn {turn}: repository mutation is not bound to changed bytes"
                )
            fixture_changed = bool(
                catalog_by_id[case_id]["turns"][turn - 1].get("pre_turn_fixture")
            )
            if fixture_changed and not repository_changed:
                raise ActivationContractError(
                    f"{case_id} turn {turn}: pre_turn_fixture is not bound to changed bytes"
                )
            if expected_mutation == "none" and repository_changed and not fixture_changed:
                raise ActivationContractError(
                    f"{case_id} turn {turn}: mutation=none changed repository bytes"
                )
            previous_repository_sha = item["repository_sha256"]
    return observations


def run_transition_catalog(
    catalog_path: Path,
    observations_path: Path,
    case_ids: set[str] | None = None,
) -> dict[str, Any]:
    catalog = validate_transition_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    observations = validate_transition_observations(
        json.loads(observations_path.read_text(encoding="utf-8")),
        catalog,
    )
    observed_by_id = {case["id"]: case for case in observations["cases"]}
    results: list[dict[str, Any]] = []
    for case in catalog["cases"]:
        if case_ids is not None and case["id"] not in case_ids:
            continue
        observed_case = observed_by_id.get(case["id"])
        observed_turns = {
            item["turn"]: item for item in observed_case["turns"]
        } if observed_case is not None else {}
        turn_results: list[dict[str, Any]] = []
        for turn_number, expected_turn in enumerate(case["turns"], 1):
            observation = observed_turns.get(turn_number)
            details: list[str] = []
            observed: list[str] = []
            if observation is None:
                details.append("turn observation is missing")
            else:
                observed = observation["observed"]
                missing = sorted(set(expected_turn["expected"]) - set(observed))
                forbidden = sorted(set(expected_turn["forbidden"]) & set(observed))
                if missing:
                    details.append(f"missing expected activation: {missing}")
                if forbidden:
                    details.append(f"forbidden activation observed: {forbidden}")
                expected_unmet = expected_turn.get("expected_unmet", False)
                observed_unmet = bool(observation["unmet_prerequisites"]) or bool(
                    set(observed) & TRANSITION_UNMET_LABELS
                )
                if expected_unmet and not observed_unmet:
                    details.append("expected unmet prerequisite was not observed")
                if not expected_unmet and observed_unmet:
                    details.append(
                        f"unmet prerequisites: {observation['unmet_prerequisites']}"
                    )
                if observation["authority_violations"]:
                    details.append(
                        f"authority violations: {observation['authority_violations']}"
                    )
            turn_results.append(
                {
                    "turn": turn_number,
                    "status": "matched" if not details else "mismatched",
                    "observed": observed,
                    "observations": details,
                }
            )
        results.append(
            {
                "id": case["id"],
                "categories": case["categories"],
                "lineage": case["lineage"],
                "status": (
                    "matched"
                    if all(item["status"] == "matched" for item in turn_results)
                    else "mismatched"
                ),
                "turns": turn_results,
            }
        )
    mismatched = [result["id"] for result in results if result["status"] == "mismatched"]
    category_results = []
    for category in catalog["qualification"]["categories"]:
        category_cases = [result for result in results if category in result["categories"]]
        category_mismatches = [
            result["id"] for result in category_cases if result["status"] != "matched"
        ]
        category_results.append(
            {
                "id": category,
                "cases": len(category_cases),
                "matched": len(category_cases) - len(category_mismatches),
                "mismatched": category_mismatches,
                "status": "matched" if not category_mismatches else "mismatched",
            }
        )
    return {
        "status": "matched" if not mismatched else "mismatched",
        "schema_version": "flow.transition.coverage.v1",
        "lane": "transition-observation",
        "purpose": "multi-turn branch recalibration and negative-trigger coverage only",
        "effect_measurement": False,
        "aggregate_score": None,
        "cases": len(results),
        "matched": len(results) - len(mismatched),
        "mismatched": mismatched,
        "qualification": {
            **catalog["qualification"],
            "category_results": category_results,
        },
        "results": results,
    }


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
    parser.add_argument(
        "--lane", choices=("deterministic", "semantic", "transition"), default="deterministic"
    )
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--observations", type=Path)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.catalog and args.legacy_catalog:
        parser.error("use either positional catalog compatibility or --catalog, not both")
    default_name = {
        "deterministic": "flow-activation-cases.json",
        "semantic": "flow-activation-semantic-cases.json",
        "transition": "flow-transition-semantic-cases.json",
    }[args.lane]
    catalog = (args.catalog or args.legacy_catalog or repository / "evals" / default_name).resolve()
    try:
        if args.lane == "semantic":
            if args.observations is None:
                raise ActivationContractError("semantic lane requires --observations from actual first attempts")
            result = run_semantic_catalog(catalog, args.observations.resolve())
        elif args.lane == "transition":
            if args.observations is None:
                raise ActivationContractError(
                    "transition lane requires --observations from actual multi-turn attempts"
                )
            result = run_transition_catalog(catalog, args.observations.resolve())
        else:
            if args.observations is not None:
                raise ActivationContractError(
                    "--observations is only valid for the semantic or transition lane"
                )
            result = run_catalog(catalog, script.with_name("dev-flow.py"))
    except (OSError, json.JSONDecodeError, ActivationContractError) as exc:
        print(json.dumps({"status": "invalid", "errors": [str(exc)]}, indent=2))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "matched" else 1


if __name__ == "__main__":
    raise SystemExit(main())
