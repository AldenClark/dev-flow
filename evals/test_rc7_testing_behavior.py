#!/usr/bin/env python3
"""Executable RC.7 testing-method sensitivity fixtures.

These fixtures exercise project-native ``unittest`` commands against real
temporary files and seeded faults.  They qualify deterministic guidance and
harness sensitivity only; they do not claim that a live model selected or
applied the guidance.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass, replace
from pathlib import Path


@dataclass(frozen=True)
class NativeResult:
    returncode: int
    tests_run: int
    skipped: int
    test_ids: frozenset[str]
    skipped_test_ids: frozenset[str]
    source_fingerprint: str
    run_identity: str
    output: str


def _source_fingerprint(project: Path) -> str:
    sources = sorted(
        path
        for path in project.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and path.suffix not in {".pyc", ".pyo"}
    )
    entries = [
        (
            source.relative_to(project).as_posix(),
            hashlib.sha256(source.read_bytes()).hexdigest(),
        )
        for source in sources
    ]
    return hashlib.sha256(
        json.dumps(entries, separators=(",", ":"), ensure_ascii=True).encode()
    ).hexdigest()


def _run_native(project: Path, *, extra_env: dict[str, str] | None = None) -> NativeResult:
    environment_overrides = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(project),
    }
    if extra_env:
        environment_overrides.update(extra_env)
    environment = os.environ.copy()
    environment.update(environment_overrides)
    source_fingerprint = _source_fingerprint(project)
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
    test_ids = frozenset(
        re.findall(r"(?m)^\S+ \(([^)]+)\) \.\.\.", output)
    )
    skipped_test_ids = frozenset(
        re.findall(
            r"(?m)^\S+ \(([^)]+)\) \.\.\. skipped", output
        )
    )
    identity_payload = {
        "command": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        "environment": environment_overrides,
        "source_and_config": source_fingerprint,
        "version": sys.version,
    }
    identity = hashlib.sha256(
        json.dumps(
            identity_payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
        ).encode()
    )
    return NativeResult(
        returncode=completed.returncode,
        tests_run=int(count.group(1)) if count else 0,
        skipped=int(skipped.group(1)) if skipped else 0,
        test_ids=test_ids,
        skipped_test_ids=skipped_test_ids,
        source_fingerprint=source_fingerprint,
        run_identity=identity.hexdigest(),
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
    if not attempts or len({result.run_identity for result in attempts}) != 1:
        return "NOT COMPARABLE"
    selections = {
        (result.test_ids, result.skipped_test_ids) for result in attempts
    }
    if len(selections) != 1:
        return "FLAKY"
    outcomes = {result.returncode == 0 for result in attempts}
    if len(outcomes) > 1:
        return "FLAKY"
    return "PASSED" if outcomes == {True} else "FAILED"


def _discovery_disposition(
    result: NativeResult, *, expected_tests: frozenset[str]
) -> str:
    if not expected_tests.issubset(result.test_ids):
        return "FAILED"
    if expected_tests.intersection(result.skipped_test_ids):
        return "FAILED"
    return "PASSED" if result.returncode == 0 else "FAILED"


def _write_isolation_project(project: Path, *, isolated: bool) -> None:
    tests = project / "tests"
    tests.mkdir(parents=True)
    (tests / "__init__.py").write_text("", encoding="utf-8")
    setup = "    def setUp(self):\n        shared.clear()\n\n" if isolated else ""
    (tests / "test_isolation.py").write_text(
        """import unittest

shared = []

class IsolationTests(unittest.TestCase):
"""
        + setup
        + """    def test_a_mutates_fixture(self):
        shared.append("leak")
        self.assertEqual(shared, ["leak"])

    def test_b_requires_clean_fixture(self):
        self.assertEqual(shared, [])
""",
        encoding="utf-8",
    )


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
            self.assertEqual(
                _discovery_disposition(
                    result,
                    expected_tests=frozenset(
                        {
                            "test_quote.QuoteTests.test_vip_threshold",
                            "test_quote.QuoteTests.test_negative_total_is_rejected",
                            "test_receipt.ReceiptBoundaryTests.test_real_filesystem_boundary",
                        }
                    ),
                ),
                "FAILED",
            )

    def test_expected_test_identity_and_skip_state_prevent_count_only_false_green(self) -> None:
        expected = frozenset(
            {
                "test_quote.QuoteTests.test_vip_threshold",
                "test_quote.QuoteTests.test_negative_total_is_rejected",
                "test_receipt.ReceiptBoundaryTests.test_real_filesystem_boundary",
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project)
            result = _run_native(project)
            self.assertEqual(_discovery_disposition(result, expected_tests=expected), "PASSED")

            (project / "tests" / "test_quote.py").rename(
                project / "tests" / "disabled_test_quote.py"
            )
            (project / "tests" / "test_dummy.py").write_text(
                """import unittest

class DummyTests(unittest.TestCase):
    def test_vip_threshold(self): pass
    def test_unrelated_two(self): pass
""",
                encoding="utf-8",
            )
            count_preserved = _run_native(project)
            self.assertEqual(count_preserved.tests_run, 3, count_preserved.output)
            self.assertEqual(
                _discovery_disposition(count_preserved, expected_tests=expected), "FAILED"
            )

            _write_project(project, skip_product=True)
            skipped = _run_native(project)
            self.assertEqual(skipped.returncode, 0, skipped.output)
            self.assertIn(
                "test_quote.QuoteTests.test_vip_threshold", skipped.skipped_test_ids
            )
            self.assertEqual(_discovery_disposition(skipped, expected_tests=expected), "FAILED")

    def test_retry_identity_binds_non_python_config_and_canonical_effective_environment(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_project(project)
            config = project / "settings.json"
            config.write_text('{"mode":"a"}\n', encoding="utf-8")
            first = _run_native(project, extra_env={"A": "BC"})

            config.write_text('{"mode":"b"}\n', encoding="utf-8")
            changed_config = _run_native(project, extra_env={"A": "BC"})
            self.assertNotEqual(first.source_fingerprint, changed_config.source_fingerprint)
            self.assertEqual(
                _retry_disposition([first, changed_config]), "NOT COMPARABLE"
            )

            config.write_text('{"mode":"a"}\n', encoding="utf-8")
            ambiguous_without_canonical_encoding = _run_native(
                project, extra_env={"AB": "C"}
            )
            self.assertEqual(first.source_fingerprint, ambiguous_without_canonical_encoding.source_fingerprint)
            self.assertNotEqual(first.run_identity, ambiguous_without_canonical_encoding.run_identity)

            config.unlink()
            (project / "a").write_text("bc\n", encoding="utf-8")
            first_tree = _run_native(project)
            (project / "a").unlink()
            (project / "ab").write_text("c\n", encoding="utf-8")
            distinct_tree = _run_native(project)
            self.assertNotEqual(first_tree.source_fingerprint, distinct_tree.source_fingerprint)
            self.assertEqual(
                _retry_disposition([first_tree, distinct_tree]), "NOT COMPARABLE"
            )

    def test_native_ids_without_underscore_preserve_skip_and_selection_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            project = base / "project"
            marker = base / "external-marker"
            _write_project(project)
            (project / "tests" / "test_dynamic.py").write_text(
                f'''import unittest
from pathlib import Path

MARKER = Path({str(marker)!r})

class DynamicTests(unittest.TestCase):
    @unittest.skipIf(MARKER.exists(), "external selection state")
    def testAlpha(self):
        self.assertTrue(True)
''',
                encoding="utf-8",
            )
            selected = _run_native(project)
            self.assertIn(
                "test_dynamic.DynamicTests.testAlpha", selected.test_ids
            )

            marker.write_text("skip\n", encoding="utf-8")
            skipped = _run_native(project)
            self.assertEqual(selected.run_identity, skipped.run_identity)
            self.assertIn(
                "test_dynamic.DynamicTests.testAlpha", skipped.skipped_test_ids
            )
            self.assertEqual(_retry_disposition([selected, skipped]), "FLAKY")

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

    def test_native_runner_preserves_required_host_environment(self) -> None:
        key = "DEV_FLOW_TEST_HOST_SENTINEL"
        previous = os.environ.get(key)
        try:
            os.environ[key] = "present"
            with tempfile.TemporaryDirectory() as directory:
                project = Path(directory)
                _write_project(project)
                (project / "tests" / "test_host_environment.py").write_text(
                    f'''import os
import unittest

class HostEnvironmentTests(unittest.TestCase):
    def test_required_host_value_is_available(self):
        self.assertEqual(os.environ.get({key!r}), "present")
''',
                    encoding="utf-8",
                )

                result = _run_native(project)

                self.assertEqual(result.returncode, 0, result.output)
        finally:
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous

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
            self.assertNotEqual(first.run_identity, second.run_identity)
            self.assertEqual(_retry_disposition([first, second]), "NOT COMPARABLE")

            stable = _run_native(project)
            same_identity_failure = replace(stable, returncode=1)
            self.assertEqual(
                _retry_disposition([same_identity_failure, stable]), "FLAKY"
            )
            self.assertEqual(
                _retry_disposition([stable, same_identity_failure]), "FLAKY"
            )
            changed_selection = replace(
                stable,
                test_ids=frozenset(
                    {"test_dummy.ImpostorTests.test_vip_threshold"}
                ),
            )
            self.assertEqual(
                _retry_disposition([stable, changed_selection]), "FLAKY"
            )

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

    def test_fixture_pollution_is_detected_and_isolated_control_passes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_isolation_project(project, isolated=False)
            leaky = _run_native(project)
            self.assertNotEqual(leaky.returncode, 0, leaky.output)
            self.assertIn("test_b_requires_clean_fixture", leaky.output)

        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            _write_isolation_project(project, isolated=True)
            isolated = _run_native(project)
            self.assertEqual((isolated.returncode, isolated.tests_run), (0, 2), isolated.output)

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
