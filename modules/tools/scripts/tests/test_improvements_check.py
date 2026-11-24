"""Checks for the improvements checker: missing programs, failing and passing commands, scope filter."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("improvements_check", Path(__file__).parents[1] / "improvements_check.py")
assert SPEC is not None and SPEC.loader is not None
tool = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(tool)

OK = [sys.executable, "-c", "pass"]
FAIL = [sys.executable, "-c", "raise SystemExit(1)"]


class ImprovementsCheckTest(unittest.TestCase):
    def test_missing_program_is_not_installed(self) -> None:
        self.assertFalse(tool.passes(["no-such-program-xyz"]))

    def test_exit_code_decides(self) -> None:
        self.assertTrue(tool.passes(OK))
        self.assertFalse(tool.passes(FAIL))

    def test_scope_filter_and_items_without_check(self) -> None:
        items = [
            {"id": 1, "title": "a", "verify": FAIL, "scope": "business"},
            {"id": 2, "title": "b", "verify": FAIL, "scope": "game"},
            {"id": 3, "title": "c", "verify": OK},
            {"id": 4, "title": "d"},
        ]
        self.assertEqual([i["id"] for i in tool.missing(items, "business")], [1])
        self.assertEqual([i["id"] for i in tool.missing(items, None)], [1, 2])

    def test_keywords_must_be_a_list_of_lowercase_strings(self) -> None:
        self.assertEqual(tool.keyword_errors([{"id": 1, "keywords": ["desktop", "gui app"]}, {"id": 2}]), [])
        self.assertEqual(len(tool.keyword_errors([{"id": 1, "keywords": "desktop"}])), 1)
        self.assertEqual(len(tool.keyword_errors([{"id": 1, "keywords": ["Desktop", "", 3]}])), 3)


if __name__ == "__main__":
    unittest.main()
