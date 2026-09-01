#!/usr/bin/env python3
"""Bench-owned case, fixture, observation, and assessment contracts."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import re
from typing import Any


class BenchContractError(ValueError):
    """Raised when a Dev Flow Bench contract is invalid."""


SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
BENCHMARK_FIXTURE_MAX_FILES = 8
BENCHMARK_FIXTURE_MAX_FILE_BYTES = 64 * 1024
BENCHMARK_FIXTURE_MAX_TOTAL_BYTES = 256 * 1024
BENCHMARK_REPOSITORY_MAX_FILES = 256
BENCHMARK_REPOSITORY_MAX_FILE_BYTES = 64 * 1024
BENCHMARK_REPOSITORY_MAX_TOTAL_BYTES = 1024 * 1024
BENCHMARK_FIXTURE_PATH_RE = re.compile(r"^[A-Za-z0-9._/-]+$")
BENCHMARK_MCP_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
BENCHMARK_UNMET_LABELS = {"blocked-claim", "no-invariant-retry"}


def benchmark_fixture_path_is_safe(path: Any) -> bool:
    """Return whether a fixture path is a canonical safe Python file operand."""
    if (
        not isinstance(path, str)
        or not path
        or path == "."
        or path.startswith("-")
        or BENCHMARK_FIXTURE_PATH_RE.fullmatch(path) is None
    ):
        return False
    normalized = PurePosixPath(path)
    return (
        not normalized.is_absolute()
        and normalized.as_posix() == path
        and ".." not in normalized.parts
        and not any(part.rstrip(".").casefold() == ".git" for part in normalized.parts)
    )


def benchmark_fixture_evidence_bytes(fixture: dict[str, str]) -> int:
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


def validate_benchmark_repository_fixture(repository: Any) -> dict[str, str]:
    """Validate the complete initial fixture before any filesystem write."""
    if (
        not isinstance(repository, dict)
        or not repository
        or len(repository) > BENCHMARK_REPOSITORY_MAX_FILES
    ):
        raise BenchContractError(
            "initial repository fixture must be a bounded non-empty object"
        )
    identities: set[tuple[str, ...]] = set()
    total_bytes = 0
    for path, content in repository.items():
        if not benchmark_fixture_path_is_safe(path) or not isinstance(content, str):
            raise BenchContractError(
                "initial repository fixture contains an unsafe path or non-string content"
            )
        identity = tuple(
            part.rstrip(".").casefold() for part in PurePosixPath(path).parts
        )
        if identity in identities:
            raise BenchContractError(
                "initial repository fixture contains a host-ambiguous path alias"
            )
        identities.add(identity)
        encoded_bytes = len(content.encode("utf-8"))
        if encoded_bytes > BENCHMARK_REPOSITORY_MAX_FILE_BYTES:
            raise BenchContractError(
                "initial repository fixture exceeds its per-file byte bound"
            )
        total_bytes += encoded_bytes
        if total_bytes > BENCHMARK_REPOSITORY_MAX_TOTAL_BYTES:
            raise BenchContractError(
                "initial repository fixture exceeds its total byte bound"
            )
    if any(
        identity[:depth] in identities
        for identity in identities
        for depth in range(1, len(identity))
    ):
        raise BenchContractError(
            "initial repository fixture contains a file/directory path collision"
        )
    return repository


def validate_benchmark_catalog(catalog: Any) -> dict[str, Any]:
    """Validate Bench-owned multi-turn research fixtures without invoking a model."""
    if not isinstance(catalog, dict) or set(catalog) != {
        "schema_version",
        "purpose",
        "cases",
    }:
        raise BenchContractError(
            "benchmark catalog must contain schema_version, purpose, and cases"
        )
    if catalog["schema_version"] != "dev-flow.benchmark.catalog.v1" or not isinstance(
        catalog["purpose"], str
    ) or not catalog["purpose"].strip():
        raise BenchContractError(
            "benchmark catalog requires schema_version dev-flow.benchmark.catalog.v1 and a purpose"
        )
    cases = catalog["cases"]
    if not isinstance(cases, list) or not cases:
        raise BenchContractError("benchmark catalog cases must be a non-empty list")
    seen: set[str] = set()
    for case in cases:
        if not isinstance(case, dict) or not {
            "id",
            "categories",
            "lineage",
            "repository",
            "turns",
        } <= set(case) or not set(case) <= {
            "id",
            "categories",
            "lineage",
            "repository",
            "turns",
            "mcp_fixture",
        }:
            raise BenchContractError("each benchmark case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            raise BenchContractError("benchmark case ids must be unique non-empty strings")
        seen.add(case_id)
        case_categories = case.get("categories")
        if (
            not isinstance(case_categories, list)
            or not case_categories
            or any(
                not isinstance(category, str)
                or BENCHMARK_MCP_ID_RE.fullmatch(category) is None
                for category in case_categories
            )
            or len(case_categories) != len(set(case_categories))
        ):
            raise BenchContractError(
                f"{case_id}: categories must be unique non-empty bounded identifiers"
            )
        if case.get("lineage") not in {"resume", "fork"}:
            raise BenchContractError(f"{case_id}: lineage must be resume or fork")
        try:
            repository = validate_benchmark_repository_fixture(case.get("repository"))
        except BenchContractError as exc:
            raise BenchContractError(f"{case_id}: {exc}") from exc
        mcp_fixture = case.get("mcp_fixture")
        if mcp_fixture is not None:
            if (
                not isinstance(mcp_fixture, dict)
                or set(mcp_fixture) != {"server", "tool"}
                or any(
                    not isinstance(mcp_fixture.get(field), str)
                    or BENCHMARK_MCP_ID_RE.fullmatch(mcp_fixture[field]) is None
                    for field in ("server", "tool")
                )
            ):
                raise BenchContractError(
                    f"{case_id}: mcp_fixture must name one bounded runner-owned tool"
                )
        turns = case.get("turns")
        if not isinstance(turns, list) or len(turns) < 2:
            raise BenchContractError(f"{case_id}: turns must contain at least two turns")
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
                "allowed_mcp_tools",
            }
            if (
                not isinstance(turn, dict)
                or not required_turn_fields <= set(turn)
                or not set(turn) <= required_turn_fields | optional_turn_fields
            ):
                raise BenchContractError(f"{case_id} turn {turn_number}: invalid fields")
            if not isinstance(turn.get("prompt"), str) or not turn["prompt"]:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: prompt must be non-empty"
                )
            if turn.get("mutation") not in {"none", "repository"}:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: mutation must be none or repository"
                )
            mutation_paths = turn.get("mutation_paths")
            if turn["mutation"] == "repository":
                if (
                    not isinstance(mutation_paths, list)
                    or not mutation_paths
                    or any(
                        not benchmark_fixture_path_is_safe(path)
                        for path in mutation_paths
                    )
                    or len(mutation_paths) != len(set(mutation_paths))
                    or not set(mutation_paths) <= set(repository)
                ):
                    raise BenchContractError(
                        f"{case_id} turn {turn_number}: repository mutation requires unique existing mutation_paths"
                    )
            elif mutation_paths is not None:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: mutation=none forbids mutation_paths"
                )
            if not isinstance(turn.get("expected_unmet", False), bool):
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: expected_unmet must be boolean"
                )
            allowed_mcp_tools = turn.get("allowed_mcp_tools", [])
            expected_mcp_tool = (
                f"{mcp_fixture['server']}/{mcp_fixture['tool']}"
                if mcp_fixture is not None
                else None
            )
            if (
                not isinstance(allowed_mcp_tools, list)
                or len(allowed_mcp_tools) != len(set(allowed_mcp_tools))
                or any(
                    not isinstance(value, str) or value != expected_mcp_tool
                    for value in allowed_mcp_tools
                )
                or (allowed_mcp_tools and mcp_fixture is None)
            ):
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: allowed_mcp_tools must reference the exact runner-owned fixture tool"
                )
            fixture = turn.get("pre_turn_fixture", {})
            if (
                not isinstance(fixture, dict)
                or len(fixture) > BENCHMARK_FIXTURE_MAX_FILES
                or any(
                    not benchmark_fixture_path_is_safe(path)
                    or not isinstance(content, str)
                    or len(content.encode("utf-8"))
                    > BENCHMARK_FIXTURE_MAX_FILE_BYTES
                    for path, content in fixture.items()
                )
            ):
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: pre_turn_fixture is invalid"
                )
            if (
                benchmark_fixture_evidence_bytes(fixture)
                > BENCHMARK_FIXTURE_MAX_TOTAL_BYTES
            ):
                raise BenchContractError(
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
                    raise BenchContractError(
                        f"{case_id} turn {turn_number}: {field} must be a unique non-empty string list"
                    )
            overlap = sorted(set(turn["expected"]) & set(turn["forbidden"]))
            if overlap:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: expected/forbidden overlap: {overlap}"
                )
            if "exact-mcp-tool-once" in turn["expected"] and len(allowed_mcp_tools) != 1:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: exact-mcp-tool-once requires one allowed_mcp_tools entry"
                )
            if allowed_mcp_tools and "exact-mcp-tool-once" not in turn["expected"]:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: allowed_mcp_tools requires exact-mcp-tool-once"
                )
            expected_implies_unmet = bool(
                set(turn["expected"]) & BENCHMARK_UNMET_LABELS
            )
            if turn.get("expected_unmet", False) and not expected_implies_unmet:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: expected_unmet requires a semantically entailing expected label"
                )
            if not turn.get("expected_unmet", False) and expected_implies_unmet:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: unmet-implying expected label requires expected_unmet"
                )
            if "readiness-fact-changed" in turn["expected"] and not fixture:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: readiness-fact-changed requires a runner-owned pre_turn_fixture"
                )
            if "one-justified-retry" in turn["expected"] and not fixture:
                raise BenchContractError(
                    f"{case_id} turn {turn_number}: one-justified-retry requires a runner-owned pre_turn_fixture"
                )
    return catalog


def validate_benchmark_observations(
    observations: Any,
    catalog: dict[str, Any],
) -> dict[str, Any]:
    """Validate sanitized turn-bound observations produced by an external runner."""
    if not isinstance(observations, dict) or set(observations) != {"schema_version", "cases"}:
        raise BenchContractError(
            "benchmark observations must contain schema_version and cases"
        )
    if observations["schema_version"] != "dev-flow.benchmark.observations.v1":
        raise BenchContractError(
            "benchmark observations require schema_version dev-flow.benchmark.observations.v1"
        )
    catalog_by_id = {case["id"]: case for case in catalog["cases"]}
    cases = observations["cases"]
    if not isinstance(cases, list):
        raise BenchContractError("benchmark observation cases must be a list")
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
            raise BenchContractError("each benchmark observation case has invalid fields")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen_cases:
            raise BenchContractError(
                "benchmark observation case ids must be unique non-empty strings"
            )
        if case_id not in catalog_by_id:
            raise BenchContractError(f"unknown benchmark observation case {case_id!r}")
        seen_cases.add(case_id)
        if not isinstance(case.get("lineage_id"), str) or not case["lineage_id"]:
            raise BenchContractError(f"{case_id}: lineage_id must be non-empty")
        initial_repository_sha = case.get("initial_repository_sha256")
        if not isinstance(initial_repository_sha, str) or SHA256_RE.fullmatch(
            initial_repository_sha
        ) is None:
            raise BenchContractError(
                f"{case_id}: initial_repository_sha256 must be a sha256 digest"
            )
        initial_git_head_sha = case.get("initial_git_head_sha256")
        if not isinstance(initial_git_head_sha, str) or SHA256_RE.fullmatch(
            initial_git_head_sha
        ) is None:
            raise BenchContractError(
                f"{case_id}: initial_git_head_sha256 must be a sha256 digest"
            )
        turns = case.get("turns")
        if not isinstance(turns, list):
            raise BenchContractError(f"{case_id}: turns must be a list")
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
                raise BenchContractError(
                    f"{case_id}: each benchmark turn observation has invalid fields"
                )
            turn = item.get("turn")
            if (
                not isinstance(turn, int)
                or isinstance(turn, bool)
                or turn < 1
                or turn > len(catalog_by_id[case_id]["turns"])
                or turn in seen_turns
            ):
                raise BenchContractError(f"{case_id}: invalid or duplicate turn {turn!r}")
            if turn <= last_turn:
                raise BenchContractError(
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
                    raise BenchContractError(
                        f"{case_id} turn {turn}: {field} must be a unique string list"
                    )
            if not item["evidence"]:
                raise BenchContractError(f"{case_id} turn {turn}: evidence is required")
            for field in ("evidence_sha256", "repository_sha256"):
                value = item.get(field)
                if not isinstance(value, str) or SHA256_RE.fullmatch(value) is None:
                    raise BenchContractError(
                        f"{case_id} turn {turn}: {field} must be a sha256 digest"
                    )
            if item["evidence_sha256"] in seen_evidence:
                raise BenchContractError(
                    f"{case_id} turn {turn}: evidence digest was reused across turns"
                )
            seen_evidence.add(item["evidence_sha256"])
            expected_mutation = catalog_by_id[case_id]["turns"][turn - 1]["mutation"]
            repository_changed = item["repository_sha256"] != previous_repository_sha
            if expected_mutation == "repository" and not repository_changed:
                raise BenchContractError(
                    f"{case_id} turn {turn}: repository mutation is not bound to changed bytes"
                )
            fixture_changed = bool(
                catalog_by_id[case_id]["turns"][turn - 1].get("pre_turn_fixture")
            )
            if fixture_changed and not repository_changed:
                raise BenchContractError(
                    f"{case_id} turn {turn}: pre_turn_fixture is not bound to changed bytes"
                )
            if expected_mutation == "none" and repository_changed and not fixture_changed:
                raise BenchContractError(
                    f"{case_id} turn {turn}: mutation=none changed repository bytes"
                )
            previous_repository_sha = item["repository_sha256"]
    return observations


def run_benchmark_catalog(
    catalog_path: Path,
    observations_path: Path,
    case_ids: set[str] | None = None,
) -> dict[str, Any]:
    catalog = validate_benchmark_catalog(json.loads(catalog_path.read_text(encoding="utf-8")))
    observations = validate_benchmark_observations(
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
                    set(observed) & BENCHMARK_UNMET_LABELS
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
    categories = sorted(
        {category for result in results for category in result["categories"]}
    )
    for category in categories:
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
        "schema_version": "dev-flow.benchmark.assessment.v1",
        "lane": "benchmark-observation",
        "purpose": "per-case multi-turn research observations only",
        "effect_measurement": False,
        "aggregate_score": None,
        "cases": len(results),
        "matched": len(results) - len(mismatched),
        "mismatched": mismatched,
        "category_results": category_results,
        "results": results,
    }
