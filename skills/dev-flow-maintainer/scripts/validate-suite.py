#!/usr/bin/env python3
"""Validate the Dev Flow 12-Skill inventory and cutover invariants."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
EXPECTED = {
    "architecture-decisions",
    "change-review",
    "delivery-readiness",
    "dependency-decisions",
    "dev-flow",
    "dev-flow-maintainer",
    "manage-engineering-profiles",
    "product-ux-discovery",
    "repo-context",
    "requirements-design",
    "systematic-debugging",
    "verification",
}
HISTORICAL_FILES = {"CHANGELOG.md", "content-migration-v1.json"}
DESCRIPTION_BUDGET = 2500
ORDINARY_STATIC_BUDGET = 15000
ORDINARY_STATIC_FILES = (
    "skills/dev-flow/SKILL.md",
    "skills/dev-flow/references/artifact-schemas.md",
    "skills/repo-context/SKILL.md",
    "skills/verification/SKILL.md",
)


def main() -> int:
    errors: list[str] = []
    skills = {path.name for path in (ROOT / "skills").iterdir() if path.is_dir()}
    if skills != EXPECTED:
        errors.append(f"expected 12 Skills {sorted(EXPECTED)}, observed {sorted(skills)}")
    names: set[str] = set()
    description_total = 0
    for directory in sorted((ROOT / "skills").iterdir()):
        if not directory.is_dir():
            continue
        skill = directory / "SKILL.md"
        text = skill.read_text(encoding="utf-8") if skill.is_file() else ""
        match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text)
        if not match or match.group(1) != directory.name:
            errors.append(f"{directory.name}: invalid or mismatched Skill name")
        if match and match.group(1) in names:
            errors.append(f"duplicate Skill name: {match.group(1)}")
        if match:
            names.add(match.group(1))
        description = re.search(r"(?m)^description:\s*(.+)\s*$", text)
        if not description:
            errors.append(f"{directory.name}: missing one-line Skill description")
        else:
            description_total += len(description.group(1).strip())
        if text.count("\n") + 1 > 500:
            errors.append(f"{directory.name}: SKILL.md exceeds 500 lines")
        if "TODO" in text or "[TODO" in text:
            errors.append(f"{directory.name}: unresolved scaffold placeholder")
        metadata = directory / "agents" / "openai.yaml"
        if not metadata.is_file() or f"${directory.name}" not in metadata.read_text(encoding="utf-8"):
            errors.append(f"{directory.name}: stale agents/openai.yaml")
    if description_total > DESCRIPTION_BUDGET:
        errors.append(f"Skill descriptions exceed {DESCRIPTION_BUDGET} characters: {description_total}")
    ordinary_static_total = sum(
        len((ROOT / path).read_text(encoding="utf-8").encode("utf-8"))
        for path in ORDINARY_STATIC_FILES
    )
    if ordinary_static_total > ORDINARY_STATIC_BUDGET:
        errors.append(f"ordinary static path exceeds {ORDINARY_STATIC_BUDGET} bytes: {ordinary_static_total}")
    maintainer_metadata = (ROOT / "skills" / "dev-flow-maintainer" / "agents" / "openai.yaml").read_text(encoding="utf-8")
    if "allow_implicit_invocation: false" not in maintainer_metadata:
        errors.append("dev-flow-maintainer must remain explicit-only")
    legacy = "engineering-" + "preferences"
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in {".git", ".codex", "__pycache__"} for part in path.parts):
            continue
        if path.name in HISTORICAL_FILES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if legacy in text:
            errors.append(f"live legacy Skill reference remains: {path.relative_to(ROOT)}")
    print(
        json.dumps(
            {
                "status": "valid" if not errors else "invalid",
                "skills": len(skills),
                "description_characters": description_total,
                "ordinary_static_bytes": ordinary_static_total,
                "errors": errors,
            },
            indent=2,
        )
    )
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
