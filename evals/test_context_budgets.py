#!/usr/bin/env python3
"""Context-budget headroom tests for ordinary Dev Flow activation."""

from __future__ import annotations

import importlib.util
import io
import re
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "skills" / "dev-flow-maintainer" / "scripts" / "validate-suite.py"
SPEC = importlib.util.spec_from_file_location("validate_suite", VALIDATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class ContextBudgetTests(unittest.TestCase):
    def test_current_descriptions_and_ordinary_static_path_meet_targets(self) -> None:
        descriptions = 0
        for skill in (ROOT / "skills").glob("*/SKILL.md"):
            match = re.search(r"(?m)^description:\s*(.+)\s*$", skill.read_text(encoding="utf-8"))
            self.assertIsNotNone(match, skill)
            assert match is not None
            descriptions += len(match.group(1).strip())
        ordinary = sum(len((ROOT / path).read_bytes()) for path in VALIDATOR.ORDINARY_STATIC_FILES)
        self.assertLessEqual(descriptions, VALIDATOR.DESCRIPTION_TARGET)
        self.assertLessEqual(ordinary, VALIDATOR.ORDINARY_STATIC_TARGET)
        self.assertLess(VALIDATOR.DESCRIPTION_WARNING, VALIDATOR.DESCRIPTION_TARGET)
        self.assertLess(
            VALIDATOR.ORDINARY_STATIC_STRETCH_TARGET,
            VALIDATOR.ORDINARY_STATIC_TARGET,
        )

    def test_rc7_static_limit_is_an_error_not_a_warning(self) -> None:
        ordinary = sum(len((ROOT / path).read_bytes()) for path in VALIDATOR.ORDINARY_STATIC_FILES)
        output = io.StringIO()
        with patch.object(VALIDATOR, "ORDINARY_STATIC_BUDGET", ordinary - 1):
            with redirect_stdout(output):
                code = VALIDATOR.main()
        self.assertEqual(code, 2)
        self.assertIn("ordinary static path exceeds", output.getvalue())


if __name__ == "__main__":
    unittest.main()
