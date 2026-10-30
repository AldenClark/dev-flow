#!/usr/bin/env python3
"""Static RC.7 integrity checks for the testing and review Skill group.

These checks protect discoverability and decision boundaries in the shipped Skill
bytes. They do not claim that a model followed the guidance; representative
application-effect observations remain behavior-evaluation work.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def assert_concepts(test: unittest.TestCase, text: str, groups: dict[str, tuple[str, ...]]) -> None:
    missing = [name for name, terms in groups.items() if not all(term in text for term in terms)]
    test.assertEqual(missing, [])


class Rc7TestSkillIntegrityTests(unittest.TestCase):
    def test_entrypoint_references_resolve(self) -> None:
        for skill_name in ("verification", "test-system-engineering", "change-review"):
            skill_dir = ROOT / "skills" / skill_name
            skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
            references = set(re.findall(r"`(references/[^`]+\.md)`", skill))
            self.assertTrue(references, skill_name)
            for reference in references:
                self.assertTrue((skill_dir / reference).is_file(), f"{skill_name}: {reference}")

    def test_descriptions_are_compact_and_ui_prompts_match(self) -> None:
        limits = {
            "verification": 100,
            "test-system-engineering": 125,
            "change-review": 100,
        }
        for skill_name, limit in limits.items():
            skill = read(f"skills/{skill_name}/SKILL.md")
            match = re.search(r"(?m)^description:\s*(.+)$", skill)
            self.assertIsNotNone(match, skill_name)
            assert match is not None
            self.assertLessEqual(len(match.group(1).strip()), limit, skill_name)

            metadata = read(f"skills/{skill_name}/agents/openai.yaml")
            self.assertIn(f"${skill_name}", metadata)
            short = re.search(r'(?m)^\s*short_description:\s*"([^"]+)"$', metadata)
            self.assertIsNotNone(short, skill_name)
            assert short is not None
            self.assertGreaterEqual(len(short.group(1)), 25)
            self.assertLessEqual(len(short.group(1)), 64)

    def test_verification_selects_checks_for_concrete_gaps(self) -> None:
        guidance = "\n".join(
            (
                read("skills/verification/SKILL.md"),
                read("skills/verification/references/test-strategy.md"),
                read("skills/verification/references/coverage-techniques.md"),
            )
        )
        self.assertRegex(guidance, r"(?i)cheapest (?:native check|layer)")
        self.assertRegex(guidance, r"(?i)credible mechanism connected to this change")
        self.assertRegex(
            guidance,
            r"(?i)simulator or emulator[^.\n]*cannot prove[^.\n]*physical-device",
        )
        self.assertRegex(
            guidance,
            r"(?i)required unobserved path[^.\n]*BLOCKED[^.\n]*NOT RUN",
        )

    def test_test_system_covers_false_green_and_native_growth_modes(self) -> None:
        skill = read("skills/test-system-engineering/SKILL.md")
        integrity = read("skills/test-system-engineering/references/test-system-integrity.md")
        design = read("skills/test-system-engineering/references/system-design.md")
        self.assertRegex(skill, r"(?i)investigate the suspect boundary")
        self.assertRegex(
            integrity,
            r"(?i)When discovery is unclear or suspect[^.\n]*native collection or execution output",
        )
        self.assertRegex(
            integrity,
            r"(?i)AI authorship[^.\n]*does not[^.\n]*require[^.\n]*seeded fault",
        )
        self.assertRegex(
            design,
            r"(?i)smallest check[^.\n]*first meaningful rule or outcome",
        )
        self.assertIn(
            "Do not replace repository-native runners with a universal runner",
            skill,
        )

    def test_review_reports_only_verified_consequence_and_stops_at_saturation(self) -> None:
        guidance = read("skills/change-review/SKILL.md") + read(
            "skills/change-review/references/review-protocol.md"
        )
        behavior_guard = (
            "unsupported abstractions",
            "preserves the requirement",
            "preserves untrusted-input validation, contractual failures and resource safety",
            "returning business guarantee changes for confirmation",
            "Line count",
            "not proof",
        )
        assert_concepts(
            self,
            guidance,
            {
                "finding proof": (
                    "verified causal path",
                    "concrete consequence",
                    "current source location",
                    "bounded correction",
                ),
                "simplification with behavior guard": behavior_guard,
                "test self-proof challenge": (
                    "AI self-confirmation",
                    "product contracts",
                    "discovered/selected",
                    "host/mock/emulator evidence",
                ),
                "saturation": (
                    "Stop when",
                    "no new consequential evidence",
                    "Reopen only",
                    "Do not target a finding count",
                    "fixed number of rounds",
                ),
            },
        )

        for term in behavior_guard[1:4]:
            with self.subTest(missing_behavior_guard=term):
                with self.assertRaises(AssertionError):
                    assert_concepts(
                        self,
                        guidance.replace(term, "", 1),
                        {"simplification with behavior guard": behavior_guard},
                    )


if __name__ == "__main__":
    unittest.main()
