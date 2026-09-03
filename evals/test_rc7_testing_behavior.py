#!/usr/bin/env python3
"""Executable RC.7 testing-method sensitivity fixtures.

These fixtures exercise project-native ``unittest`` commands against real
temporary files and seeded faults.  They qualify deterministic guidance and
harness sensitivity only; they do not claim that a live model selected or
applied the guidance.
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class NativeResult:
    returncode: int
    tests_run: int
    skipped: int
    output: str


def _source_fingerprint(project: Path) -> str:
    digest = hashlib.sha256()
    for source in sorted(project.rglob("*.py")):
        digest.update(source.relative_to(project).as_posix().encode())
        digest.update(source.read_bytes())
    return digest.hexdigest()


def _run_native(project: Path, *, extra_env: dict[str, str] | None = None) -> NativeResult:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(project)
    if extra_env:
        environment.update(extra_env)
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        cwd=project,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout + completed.stderr
    count = re.search(r"Ran (\d+) tests?", output)
    skipped = re.search(r"skipped=(\d+)", output)
    return NativeResult(
        returncode=completed.returncode,
        tests_run=int(count.group(1)) if count else 0,
        skipped=int(skipped.group(1)) if skipped else 0,
        output=output,
    )


def _write_project(
    project: Path,
    *,
    mature: bool = False,
    product_fault: bool = False,
    boundary_fault: bool = False,
    weak_product_oracle: bool = False,
    mock_boundary: bool = False,
    skip_product: bool = False,
) -> None:
    unit_dir = project / "tests" / ("unit" if mature else "")
    boundary_dir = project / "tests" / ("integration" if mature else "")
    unit_dir.mkdir(parents=True, exist_ok=True)
    boundary_dir.mkdir(parents=True, exist_ok=True)
    (project / "tests" / "__init__.py").write_text("", encoding="utf-8")
    if mature:
        (unit_dir / "__init__.py").write_text("", encoding="utf-8")
        (boundary_dir / "__init__.py").write_text("", encoding="utf-8")

    threshold = 1000 if product_fault else 100
    target = 'path.with_suffix(".tmp")' if boundary_fault else "path"
    (project / "checkout.py").write_text(
        f"""from pathlib import Path

def quote(total: int, vip: bool) -> float:
    if total < 0:
        raise ValueError("total must be non-negative")
    return round(total * 0.9, 2) if vip and total >= {threshold} else float(total)

def persist_receipt(path: Path, payload: str) -> str:
    target = {target}
    target.write_text(payload, encoding="utf-8")
    return payload
""",
        encoding="utf-8",
    )

    skip = "@unittest.skip('seeded masking fault')\n    " if skip_product else ""
    assertion = (
        "self.assertGreaterEqual(quote(100, True), 0)"
        if weak_product_oracle
        else "self.assertEqual(quote(100, True), 90.0)"
    )
    (unit_dir / "test_quote.py").write_text(
        f"""import unittest
from checkout import quote

class QuoteTests(unittest.TestCase):
    {skip}def test_vip_threshold(self):
        {assertion}

    def test_negative_total_is_rejected(self):
        with self.assertRaises(ValueError):
            quote(-1, False)
""",
        encoding="utf-8",
    )

    if mock_boundary:
        boundary_body = """from unittest.mock import patch
        with patch("pathlib.Path.write_text") as write:
            persist_receipt(Path("receipt.txt"), "paid")
            write.assert_called_once()
"""
    else:
        boundary_body = """with tempfile.TemporaryDirectory() as directory:
            receipt = Path(directory) / "receipt.txt"
            persist_receipt(receipt, "paid")
            self.assertEqual(receipt.read_text(encoding="utf-8"), "paid")
"""
    (boundary_dir / "test_receipt.py").write_text(
        f"""import tempfile
import unittest
from pathlib import Path
from checkout import persist_receipt

class ReceiptBoundaryTests(unittest.TestCase):
    def test_real_filesystem_boundary(self):
        {boundary_body}
""",
        encoding="utf-8",
    )


def _retry_disposition(attempts: list[NativeResult]) -> str:
    if any(result.returncode != 0 for result in attempts):
        return "FLAKY" if attempts[-1].returncode == 0 else "FAILED"
    return "PASSED"


def _discovery_disposition(result: NativeResult, *, expected_tests: int) -> str:
    if result.tests_run != expected_tests:
        return "FAILED"
    return "PASSED" if result.returncode == 0 else "FAILED"


def _environment_disposition(*, observed: str, promised: str, passed: bool) -> str:
    if observed != promised:
        return "NOT RUN"
    return "PASSED" if passed else "FAILED"


def _select_coverage_cases(
    cases: list[dict[str, str]], *, user_requested_fringe: bool = False
) -> list[str]:
    selected: list[str] = []
    for case in cases:
        low_value_fringe = (
            case["probability"] == "low"
            and case["consequence"] == "low"
            and case["cost"] == "high"
        )
        if not low_value_fringe or user_requested_fringe:
            selected.append(case["id"])
    return selected


class Rc7ExecutableTestingBehaviorTests(unittest.TestCase):
    def test_new_project_native_skeleton_catches_logic_and_real_boundary_faults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project)
            healthy = _run_native(project)
            self.assertEqual((healthy.returncode, healthy.tests_run), (0, 3), healthy.output)

            _write_project(project, product_fault=True)
            product_fault = _run_native(project)
            self.assertNotEqual(product_fault.returncode, 0, product_fault.output)
            self.assertIn("test_vip_threshold", product_fault.output)

            _write_project(project, boundary_fault=True)
            boundary_fault = _run_native(project)
            self.assertNotEqual(boundary_fault.returncode, 0, boundary_fault.output)
            self.assertIn("test_real_filesystem_boundary", boundary_fault.output)

    def test_mature_project_extends_its_native_layout_without_parallel_runner(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project, mature=True)
            result = _run_native(project)
            self.assertEqual((result.returncode, result.tests_run), (0, 3), result.output)
            self.assertTrue((project / "tests/unit/test_quote.py").is_file())
            self.assertTrue((project / "tests/integration/test_receipt.py").is_file())
            self.assertFalse((project / "universal_test_runner.py").exists())

    def test_discovery_fault_is_not_misreported_as_a_pass(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project)
            for test_file in project.glob("tests/test_*.py"):
                test_file.rename(test_file.with_name(f"disabled_{test_file.name}"))
            result = _run_native(project)
            self.assertEqual(result.tests_run, 0, result.output)
            self.assertEqual(_discovery_disposition(result, expected_tests=3), "FAILED")

    def test_inert_assertion_and_mock_substitution_are_exposed_by_independent_oracles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project, product_fault=True, weak_product_oracle=True)
            weak = _run_native(project)
            self.assertEqual(weak.returncode, 0, weak.output)
            _write_project(project, product_fault=True)
            strong = _run_native(project)
            self.assertNotEqual(strong.returncode, 0, strong.output)

            _write_project(project, boundary_fault=True, mock_boundary=True)
            mocked = _run_native(project)
            self.assertEqual(mocked.returncode, 0, mocked.output)
            _write_project(project, boundary_fault=True)
            real_boundary = _run_native(project)
            self.assertNotEqual(real_boundary.returncode, 0, real_boundary.output)

    def test_stale_cache_is_detected_against_current_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project)
            cached_result = _run_native(project)
            cached_fingerprint = _source_fingerprint(project)
            self.assertEqual(cached_result.returncode, 0, cached_result.output)

            _write_project(project, product_fault=True)
            self.assertNotEqual(cached_fingerprint, _source_fingerprint(project))
            direct_result = _run_native(project)
            self.assertNotEqual(direct_result.returncode, 0, direct_result.output)
            self.assertEqual(cached_result.returncode, 0, "the stale result demonstrates false green")

    def test_retry_skip_and_environment_faults_keep_their_exact_dispositions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project, product_fault=True)
            first = _run_native(project)
            _write_project(project)
            second = _run_native(project)
            self.assertEqual(_retry_disposition([first, second]), "FLAKY")

            _write_project(project, product_fault=True, skip_product=True)
            skipped = _run_native(project)
            self.assertEqual(skipped.returncode, 0, skipped.output)
            self.assertEqual(skipped.skipped, 1, skipped.output)
            self.assertEqual(
                _environment_disposition(
                    observed="host", promised="physical-device", passed=True
                ),
                "NOT RUN",
            )

    def test_coverage_expands_for_material_faults_and_stops_low_value_fringe(self) -> None:
        cases = [
            {"id": "principal-outcome", "probability": "high", "consequence": "high", "cost": "low"},
            {"id": "rare-corruption", "probability": "low", "consequence": "high", "cost": "high"},
            {"id": "ordinary-combination", "probability": "medium", "consequence": "medium", "cost": "medium"},
            {"id": "cosmetic-fringe", "probability": "low", "consequence": "low", "cost": "high"},
        ]
        selected = _select_coverage_cases(cases)
        self.assertIn("principal-outcome", selected)
        self.assertIn("rare-corruption", selected)
        self.assertIn("ordinary-combination", selected)
        self.assertNotIn("cosmetic-fringe", selected)
        self.assertIn(
            "cosmetic-fringe", _select_coverage_cases(cases, user_requested_fringe=True)
        )


if __name__ == "__main__":
    unittest.main()
