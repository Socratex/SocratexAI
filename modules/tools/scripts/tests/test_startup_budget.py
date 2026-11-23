"""Guards the always-loaded context: the files every session pays for must stay small."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).parents[4]
ALWAYS_LOADED = ["defaults/RULES.md", "defaults/STYLE.md", "claude/CLAUDE.md", "defaults/DIRECTIVES.json"]
BUDGET_BYTES = 20_000  # about 5K tokens; today about 19K with DIRECTIVES. Raise only with a written reason.


class StartupBudget(unittest.TestCase):
    def test_always_loaded_files_fit_budget(self) -> None:
        total = sum((ROOT / name).stat().st_size for name in ALWAYS_LOADED)
        self.assertLessEqual(total, BUDGET_BYTES, f"always-loaded context is {total} bytes; move text to defaults/rules/")


if __name__ == "__main__":
    unittest.main()
