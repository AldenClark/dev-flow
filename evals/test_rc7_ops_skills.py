#!/usr/bin/env python3
"""Focused RC.7 checks for profile, data-boundary, and delivery-skill ownership."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def skill_text(name: str) -> str:
    return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")


class RC7OperationsSkillTests(unittest.TestCase):
    def test_profiles_consume_confirmed_values_without_frequency_policy(self) -> None:
        text = skill_text("manage-engineering-profiles")
        for phrase in (
            "confirmed personal, team, project, component, or task preference",
            "validated, unexpired entries",
            "Never turn code frequency",
            "explicit owner confirmation",
            "ordinary implementation consumes an already supplied effective snapshot",
        ):
            self.assertIn(phrase, text)
        self.assertNotIn("frequency alone", text.split("## Resolve a confirmed value", 1)[1].split("## Maintain", 1)[0])

    def test_data_security_is_a_cross_cutting_owner_with_short_routes(self) -> None:
        text = skill_text("company-data-security")
        self.assertIn("cross-cutting owner for the data boundary, not a second repository lifecycle", text)
        for route in (
            "**Requirements and design:**",
            "**Fixtures and tests:**",
            "**Logs and failures:**",
            "**Connectors and external tools:**",
            "**Release and operational evidence:**",
        ):
            self.assertIn(route, text)
        self.assertIn("Do not load it for ordinary public-only code", text)
        self.assertIn("does not authorize disclosure", text)

    def test_delivery_keeps_git_units_and_actions_separate(self) -> None:
        text = skill_text("delivery-readiness")
        for phrase in (
            "one understandable, reviewable, and reversible behavior change",
            "exact source commit/tree and version",
            "observation signal and owner, stop trigger, restore/rollback trigger",
            "each need their own authorization and post-action result",
            "`NOT RUN`",
        ):
            self.assertIn(phrase, text)
        for owner in (
            "`requirements-design`",
            "`product-ux-discovery`",
            "`verification` or `test-system-engineering`",
            "`repository-knowledge`",
        ):
            self.assertIn(owner, text)

    def test_openai_metadata_is_discriminating_and_invocable(self) -> None:
        for name in (
            "manage-engineering-profiles",
            "company-data-security",
            "delivery-readiness",
        ):
            text = (ROOT / "skills" / name / "agents" / "openai.yaml").read_text(encoding="utf-8")
            match = re.search(r'^  short_description: "([^"]+)"$', text, re.MULTILINE)
            self.assertIsNotNone(match, name)
            assert match is not None
            self.assertGreaterEqual(len(match.group(1)), 25, name)
            self.assertLessEqual(len(match.group(1)), 64, name)
            self.assertIn(f"${name}", text, name)


if __name__ == "__main__":
    unittest.main()
