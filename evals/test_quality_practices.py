#!/usr/bin/env python3
"""Static contract tests for development-practice and collaboration guidance."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def missing_contract_terms(text: str, terms: tuple[str, ...]) -> list[str]:
    """Return exact terms lost from a policy/template projection."""
    return [term for term in terms if term not in text]


class QualityPracticesContractTests(unittest.TestCase):
    def test_verification_selects_views_by_failure_sensitivity(self) -> None:
        skill = read("skills/verification/SKILL.md")
        strategy = read("skills/verification/references/test-strategy.md")
        required = (
            "Start from the changed behavior",
            "Black-box",
            "White-box",
            "distinct failure sensitivity",
            "do not require every view or a prose `N/A`",
            "high-risk or easy-to-fake oracle",
        )
        self.assertEqual(missing_contract_terms(strategy, required), [])
        self.assertIn("where they add distinct failure sensitivity", skill)
        self.assertIn("Do not require each view or a prose `N/A`", skill)
        self.assertIn("practical negative control", skill)

        # Negative control: losing an available derivation view weakens the strategy contract.
        without_white_box = strategy.replace("**White-box:**", "**Structure checks:**", 1)
        self.assertIn("**White-box:**", missing_contract_terms(without_white_box, ("**White-box:**",)))

    def test_test_matrix_accounts_for_techniques_and_oracle_validity(self) -> None:
        matrix = read("skills/dev-flow/templates/test-matrix.md")
        for term in (
            "## Technique accountability",
            "| Black-box |",
            "| White-box |",
            "| Experience-based / exploratory / adversarial |",
            "concrete change-specific reason",
            "cannot substitute",
            "## Oracle validity review",
            "Failure-sensitivity challenge",
            "pre-fix failure",
            "OPEN evidence gap",
        ):
            self.assertIn(term, matrix)

        without_oracle_review = matrix.replace("## Oracle validity review", "## Notes", 1)
        self.assertEqual(
            missing_contract_terms(without_oracle_review, ("## Oracle validity review",)),
            ["## Oracle validity review"],
        )

    def test_slice_and_comment_policy_is_quality_first_without_count_targets(self) -> None:
        policy = read(
            "skills/architecture-decisions/references/neutral-engineering-policy.md"
        )
        for term in (
            "Re-read current product intent",
            "smallest coherent change",
            "Run the narrow oracle early",
            "representative integration path when relevant",
            "Before calling a slice complete",
            "never authorizes stage, commit, push, PR, release, or deployment",
            "why, invariants, safety/privacy, compatibility",
            "ownership/lifecycle",
            "workaround removal",
            "public limits",
            "narrate obvious code",
            "preserve dead code",
            "unowned `TODO`",
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

        for term in (
            "objective and expected outcome",
            "relevant business/repository context",
            "owned paths or an explicit read-only boundary",
            "allowed verification and resource limits",
            "stop conditions",
            "expected return",
            "Shared writers need disjoint paths",
            "root reconciles returned work against the current Git state",
            "reruns affected checks",
            "A child final is a report",
        ):
            self.assertIn(term, orchestration)
        self.assertIn("Do not require packet IDs", orchestration)
        self.assertIn("context fingerprints", orchestration)
        self.assertIn("unless a repository-native system genuinely consumes them", orchestration)

        # Legacy templates remain readable, but they are not the 2.0 orchestration contract.
        self.assertTrue(brief)
        self.assertTrue(execution)
        self.assertTrue(report)

        without_objective = orchestration.replace("objective and expected outcome", "goal", 1)
        self.assertEqual(
            missing_contract_terms(without_objective, ("objective and expected outcome",)),
            ["objective and expected outcome"],
        )


if __name__ == "__main__":
    unittest.main()
