"""Guards the always-loaded context: the files every session pays for must stay small."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[4]
sys.path.insert(0, str(ROOT / "modules" / "tools" / "scripts"))

import install  # noqa: E402  (single source of truth for what the Claude entry file imports)

# Everything the Claude entry file imports, plus DIRECTIVES (read at every session start).
# local/profile.md is outside git: counted when present, so a fresh clone is not penalised.
ALWAYS_LOADED = [*install.CLAUDE_IMPORTS, "defaults/DIRECTIVES.json"]
# Measured 2026-11-26: 22.3 KB in git plus 1.5 KB profile = 23.8 KB (about 6K tokens). The limit is a ratchet
# just above that, not a target: lower it when text is moved out, raise it only with a written reason.
BUDGET_BYTES = 24_500


class StartupBudget(unittest.TestCase):
    def test_always_loaded_files_fit_budget(self) -> None:
        sizes = {name: (ROOT / name).stat().st_size for name in ALWAYS_LOADED if (ROOT / name).exists()}
        total = sum(sizes.values())
        detail = ", ".join(f"{name}={size}" for name, size in sizes.items())
        self.assertLessEqual(total, BUDGET_BYTES, f"always-loaded context is {total} bytes ({detail}); move text to defaults/rules/")


if __name__ == "__main__":
    unittest.main()
