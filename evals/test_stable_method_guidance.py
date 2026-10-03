#!/usr/bin/env python3
"""Focused task-facing guidance contracts for stable methodology maintenance."""

from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAINTAINER = ROOT / "skills" / "dev-flow-maintainer"


class StableMethodGuidanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        payload = json.loads((ROOT / "governance" / "industry-practices.json").read_text())
        cls.practices = {item["id"]: item for item in payload["practices"]}

    def test_maintainer_defers_release_gates_to_the_release_contract(self) -> None:
        skill = (MAINTAINER / "SKILL.md").read_text()
        contract = (MAINTAINER / "references" / "maintenance-contract.md").read_text()
        self.assertNotIn("three distinct cases per category", skill)
        self.assertNotIn("at least three independent first attempts", skill)
        self.assertIn("docs/releasing.md", skill)
        for text in (skill, contract):
            self.assertIn("first attempt", text)
            self.assertIn("five bounded real functional journeys", text)
            self.assertIn("Dev Flow Bench", text)

    def test_correctness_repairs_trials_and_promotion_have_distinct_evidence(self) -> None:
        for relative in (
            "SKILL.md", "references/maintenance-contract.md", "references/behavior-evaluation.md",
        ):
            with self.subTest(surface=relative):
                text = (MAINTAINER / relative).read_text().lower()
                self.assertIn("correctness", text)
                self.assertIn("compatibility", text)
                self.assertIn("conflict", text)
                self.assertIn("source counterexample", text)
                self.assertIn("deterministic", text)
                self.assertIn("trial", text)
                self.assertIn("marginal value", text)

    def test_delegation_projection_allows_bounded_nesting_and_keeps_authority(self) -> None:
        practice = self.practices["IND-OPENAI-V2"]
        text = " ".join(str(practice[field]) for field in (
            "decision", "adaptation", "complexity_limit", "evaluation",
        )).lower()
        self.assertNotIn("zero to three children", text)
        self.assertNotIn("one child level", text)
        self.assertNotIn("no automatic delegation", text)
        self.assertNotIn("forbids reviewer writes, worker dependency edits, and child-to-child delegation", text)
        for boundary in ("nested", "ancestor", "host", "budget", "integration"):
            self.assertIn(boundary, text)

    def test_active_requirement_and_continuity_projections_use_existing_owners(self) -> None:
        for practice_id in (
            "IND-SPEC-KIT", "IND-ANTHROPIC-LONG-RUNNING", "IND-NASA-REQ-BASELINE",
        ):
            with self.subTest(practice=practice_id):
                practice = self.practices[practice_id]
                text = " ".join(str(practice[field]) for field in (
                    "decision", "adaptation", "complexity_limit", "evaluation",
                )).lower()
                self.assertIn("existing owner", text)
                self.assertNotRegex(text, r"digest-bound|stable ac/sc/vo|sha-256 binding|sealed boundaries")

    def test_eval_projection_separates_release_journeys_from_bench_repetition(self) -> None:
        practice = self.practices["IND-ANTHROPIC-AGENT-EVALS"]
        text = " ".join(str(practice[field]) for field in (
            "decision", "adaptation", "complexity_limit", "evaluation",
        )).lower()
        self.assertIn("first attempt", text)
        self.assertIn("five", text)
        self.assertIn("bench", text)
        self.assertIn("separately authorized", text)
        self.assertNotIn("pilots with three independent first attempts", text)

    def test_method_budget_is_presentation_guidance_with_a_residual_risk_exception(self) -> None:
        text = (ROOT / "skills" / "dev-flow" / "references" / "methodology-system.md").read_text()
        self.assertIn("three ready methods and two relevant blocked methods", text)
        self.assertIn("presentation budget", text)
        self.assertIn("named residual failure mechanism", text)
        self.assertIn("execution limit", text)
        calibration = (ROOT / "skills" / "dev-flow" / "references" / "quality-calibration.md").read_text()
        self.assertIn("Normally apply at most three", calibration)
        self.assertIn("named residual failure mechanism", calibration)
        self.assertIn("current authority and resource budget", calibration)

    def test_semantic_topology_stops_only_dependent_work(self) -> None:
        payload = json.loads((ROOT / "governance" / "capability-contracts.json").read_text())
        records = payload["capabilities"] if "capabilities" in payload else payload["contracts"]
        contract = next(item for item in records if item["skill"] == "requirements-design")
        text = " ".join(contract["stops"])
        self.assertIn("surviving material user-owned choice", text)
        self.assertIn("explicit review-first", text)
        self.assertIn("independent authorized learning", text)
        self.assertNotIn("unconfirmed semantic creation or change", text)


if __name__ == "__main__":
    unittest.main()
