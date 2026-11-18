#!/usr/bin/env python3
"""Static contract tests for development-practice and collaboration guidance."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class QualityPracticesContractTests(unittest.TestCase):
    def test_test_matrix_is_optional_coordination(self) -> None:
        matrix = read("skills/dev-flow/templates/test-matrix.md")
        self.assertRegex(
            matrix,
            r"(?i)ordinary work[^\n]*native test results[^\n]*no matrix",
        )
        self.assertRegex(
            matrix,
            r"(?i)table only when[^.\n]*required environments or owners[^.\n]*coordination",
        )
        table = [line for line in matrix.splitlines() if line.startswith("|")]
        self.assertTrue(table)
        self.assertTrue(all(len(line.strip("|").split("|")) == 3 for line in table))

    def test_slice_and_comment_policy_is_quality_first_without_count_targets(self) -> None:
        policy = read(
            "skills/architecture-decisions/references/neutral-engineering-policy.md"
        )
        for term in (
            "smallest coherent change",
            "never authorizes stage, commit, push, PR, release, or deployment",
            "ownership/lifecycle",
            "narrate obvious code",
            "distinct failure sensitivity",
        ):
            self.assertIn(term, policy)

        numeric_target = re.compile(
            r"(?:coverage|comments?|tests?)[^\n]{0,40}"
            r"(?:minimum|at least|target(?: of)?)\s+\d+(?:\.\d+)?%?",
            re.IGNORECASE,
        )
        self.assertIsNone(numeric_target.search(policy))

if __name__ == "__main__":
    unittest.main()
