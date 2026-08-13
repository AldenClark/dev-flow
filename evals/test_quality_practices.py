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
    def test_verification_requires_two_independent_derivation_views(self) -> None:
        skill = read("skills/verification/SKILL.md")
        strategy = read("skills/verification/references/test-strategy.md")
        required = (
            "For every non-trivial behavior change",
            "Black-box",
            "White-box",
            "cannot substitute for black-box or white-box",
            "Use `N/A` only with a concrete reason tied to the actual change",
            "Black-box and white-box describe how obligations are derived, not where tests run",
        )
        self.assertEqual(missing_contract_terms(strategy, required), [])
        self.assertIn("run each applicable view", skill)
        self.assertIn("third view, never a substitute", skill)

        # Negative control: losing either independent derivation view must fail the contract.
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
            "Freeze the approved requirement/design baseline",
            "same coherent slice",
            "narrow oracle early",
            "representative smoke path",
            "Before calling a slice commit-ready",
            "never authorizes staging, committing, pushing",
            "why, invariants, safety/privacy, compatibility/protocol",
            "concurrency/lifecycle/resource ownership",
            "workaround/removal conditions",
            "public API contracts, limits, and errors",
            "narrate obvious code",
            "commented-out code",
            "`TODO` without an owner",
        ):
            self.assertIn(term, policy)

        numeric_target = re.compile(
            r"(?:coverage|comments?|tests?)[^\n]{0,40}"
            r"(?:minimum|at least|target(?: of)?)\s+\d+(?:\.\d+)?%?",
            re.IGNORECASE,
        )
        self.assertIsNone(numeric_target.search(policy))

    def test_multi_agent_brief_binds_every_drift_sensitive_input(self) -> None:
        orchestration = read(
            "skills/dev-flow/references/multi-agent-v2-orchestration.md"
        )
        brief = read("skills/dev-flow/templates/task-brief.md")
        report = read("skills/dev-flow/templates/agent-report.md")

        for term in (
            "base commit and worktree",
            "requirement and design revisions/digests",
            "effective instruction/profile/capability fingerprint",
            "`AC/SC/VO` IDs",
            "exclusive paths/symbols/environments",
            "separately derived black-box and white-box obligations",
            "must stop and return drift",
            "root independently rechecks",
            "Terminal child status is coordination evidence only",
        ):
            self.assertIn(term, orchestration)

        for term in (
            "Base commit and worktree binding",
            "Effective engineering context",
            "Requirement and design baseline",
            "Acceptance, scope, and verification IDs",
            "Black-box obligations",
            "White-box obligations",
            "Resource lease and teardown",
            "no delivery authority",
            "engineering-context fingerprint",
        ):
            self.assertIn(term, brief)

        for term in (
            "Bound baseline recheck",
            "Effective engineering context recheck",
            "Black-box and white-box accountability",
            "Test-oracle validity",
            "Resource lease and teardown",
            "root must independently recheck",
        ):
            self.assertIn(term, report)

        without_base = brief.replace("Base commit and worktree binding", "Initial state", 1)
        self.assertEqual(
            missing_contract_terms(without_base, ("Base commit and worktree binding",)),
            ["Base commit and worktree binding"],
        )


if __name__ == "__main__":
    unittest.main()
