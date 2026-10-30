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
    def test_verification_selects_views_by_failure_sensitivity(self) -> None:
        skill = read("skills/verification/SKILL.md")
        strategy = read("skills/verification/references/test-strategy.md")
        self.assertRegex(
            strategy,
            r"(?i)focused regression[^.\n]*no further classification",
        )
        self.assertRegex(
            strategy,
            r"(?i)views when they resolve a concrete uncertainty",
        )
        self.assertRegex(
            skill,
            r"(?i)When evidence is suspicious[^.\n]*credible high-consequence failure",
        )
        self.assertRegex(
            skill,
            r"(?i)Confirm failure at the protected assertion[^.\n]*restore[^.\n]*rerun",
        )

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

    def test_multi_agent_brief_is_minimal_and_reconciled_by_root(self) -> None:
        orchestration = read(
            "skills/dev-flow/references/multi-agent-v2-orchestration.md"
        )
        brief = read("skills/dev-flow/templates/task-brief.md")
        execution = read("skills/dev-flow/templates/execution.md")
        report = read("skills/dev-flow/templates/agent-report.md")

        for contract in (
            r"(?i)short brief[^.\n]*sufficient[^.\n]*small task",
            r"(?i)child boundary[^.\n]*subset[^.\n]*parent envelope",
            r"(?i)Before integrating child changes[^.\n]*actual diff[^.\n]*delegated scope[^.\n]*recheck only affected evidence",
            r"(?i)child (?:report|final)[^.\n]*\b(?:never|cannot|does not)\b[^.\n]*proves? integration",
        ):
            self.assertRegex(orchestration, contract)
        self.assertIn("Shared writers need disjoint paths", orchestration)

        # Legacy templates remain readable, but they are not the 2.0 orchestration contract.
        self.assertTrue(brief)
        self.assertTrue(execution)
        self.assertTrue(report)


if __name__ == "__main__":
    unittest.main()
