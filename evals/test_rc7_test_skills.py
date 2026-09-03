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

    def test_verification_derives_and_challenges_material_coverage(self) -> None:
        guidance = "\n".join(
            (
                read("skills/verification/SKILL.md"),
                read("skills/verification/references/test-strategy.md"),
                read("skills/verification/references/coverage-techniques.md"),
            )
        )
        assert_concepts(
            self,
            guidance,
            {
                "independent black and white derivation": (
                    "Black-box",
                    "user outcomes",
                    "White-box",
                    "final implementation",
                    "changed branches",
                ),
                "promise-selected native layers": (
                    "Unit",
                    "Component",
                    "Integration",
                    "Contract/consumer",
                    "End-to-end",
                    "Platform/device",
                ),
                "problem-driven expansion": (
                    "coverage-diff",
                    "pairwise",
                    "property",
                    "model-based",
                    "Fuzzing",
                    "Differential",
                    "Metamorphic",
                    "fault injection",
                    "replay",
                    "changed-code mutation",
                    "seeded fault",
                ),
                "value stop and consequence override": (
                    "Core",
                    "Extended",
                    "Fringe",
                    "low-probability, low-consequence, high-cost",
                    "Probability alone cannot demote",
                ),
                "real environment attribution": (
                    "simulator or emulator",
                    "physical-device",
                    "BLOCKED",
                    "NOT RUN",
                ),
            },
        )

    def test_test_system_covers_false_green_and_native_growth_modes(self) -> None:
        skill = read("skills/test-system-engineering/SKILL.md")
        integrity = read("skills/test-system-engineering/references/test-system-integrity.md")
        design = read("skills/test-system-engineering/references/system-design.md")
        for obligation in (
            "Discovery",
            "Selection",
            "Sensitivity",
            "Isolation",
            "Interpretation",
            "Representativeness",
        ):
            self.assertIn(f"## {obligation}", integrity)
        assert_concepts(
            self,
            skill + integrity + design,
            {
                "runner false-green audit": (
                    "zero discovery",
                    "filters",
                    "fixtures",
                    "cached results",
                    "retries",
                    "skips",
                    "negative control",
                ),
                "AI self-confirmation challenge": (
                    "AI self-confirmation audit",
                    "independent source",
                    "seeded fault",
                    "public promise",
                ),
                "new project minimum": (
                    "New project: minimum sustainable skeleton",
                    "project-native command",
                    "fast failing test",
                    "black-box slice",
                    "smallest CI feedback path",
                ),
                "mature project restraint": (
                    "Mature project: strengthen what exists",
                    "existing runner",
                    "parallel harness",
                    "universal runner",
                ),
                "lane roles not a matrix": (
                    "Feedback roles, not prescribed lane names",
                    "Focused, PR, Nightly, or Release",
                    "not required names or a fixed matrix",
                ),
            },
        )

    def test_review_reports_only_verified_consequence_and_stops_at_saturation(self) -> None:
        guidance = read("skills/change-review/SKILL.md") + read(
            "skills/change-review/references/review-protocol.md"
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
                "simplification with behavior guard": (
                    "unsupported abstractions",
                    "preserves the required behavior",
                    "Line count",
                    "not proof",
                ),
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


if __name__ == "__main__":
    unittest.main()
