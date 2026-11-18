"""Checks for the skill learnings log: dedupe, readiness, closing and skill lookup."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

SPEC = importlib.util.spec_from_file_location("skill_learn", Path(__file__).parents[1] / "skill_learn.py")
assert SPEC is not None and SPEC.loader is not None
learn = importlib.util.module_from_spec(SPEC)
sys.modules["skill_learn"] = learn
SPEC.loader.exec_module(learn)

DAY = "2026-11-16"


class SkillLearnTest(unittest.TestCase):
    def test_similar_note_merges_and_counts(self):
        entries: list[dict] = []
        learn.add(entries, "spec", "failure", "Form asked before reading the repo", DAY)
        entry, merged = learn.add(entries, "spec", "failure", "Form asked before reading the repo!", DAY)
        self.assertTrue(merged)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entry["count"], 2)

    def test_different_kind_or_note_is_new_entry(self):
        entries: list[dict] = []
        learn.add(entries, "spec", "failure", "Form asked before reading the repo", DAY)
        learn.add(entries, "spec", "workaround", "Form asked before reading the repo", DAY)
        learn.add(entries, "spec", "failure", "SPEC.md written to the wrong folder", DAY)
        self.assertEqual(len(entries), 3)

    def test_ready_after_batch_or_repeated_correction(self):
        entries: list[dict] = []
        learn.add(entries, "spec", "failure", "first problem with steps", DAY)
        learn.add(entries, "spec", "win", "worked fine", DAY)
        self.assertFalse(learn.is_ready(entries))
        learn.add(entries, "spec", "correction", "owner wants the form first", DAY)
        self.assertFalse(learn.is_ready(entries))
        learn.add(entries, "spec", "correction", "owner wants the form first", DAY)
        self.assertTrue(learn.is_ready(entries))

    def test_wins_never_count_as_open_work(self):
        entries: list[dict] = []
        for note in ("a worked", "b worked well today", "c was great"):
            learn.add(entries, "spec", "win", note, DAY)
        self.assertEqual(learn.open_weight(entries), 0)

    def test_rejected_idea_absorbs_repeats(self):
        entries: list[dict] = []
        entry, _ = learn.add(entries, "spec", "failure", "skip the form for tiny tasks", DAY)
        learn.close(entries, [entry["id"]], "rejected", DAY)
        again, merged = learn.add(entries, "spec", "failure", "skip the form for tiny tasks", DAY)
        self.assertTrue(merged)
        self.assertEqual(again["status"], "rejected")
        self.assertEqual(learn.open_weight(entries), 0)

    def test_close_reports_only_open_ids(self):
        entries: list[dict] = []
        entry, _ = learn.add(entries, "spec", "failure", "x", DAY)
        self.assertEqual(learn.close(entries, [entry["id"], "zzzzzz"], "applied", DAY), [entry["id"]])
        self.assertEqual(learn.close(entries, [entry["id"]], "applied", DAY), [])

    def test_cli_roundtrip_in_project_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / ".claude" / "skills" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\n---\n", encoding="utf-8")
            base = ["--project", tmp]
            self.assertEqual(learn.main([*base, "add", "--skill", "demo", "--kind", "failure", "--note", "n1"]), 0)
            self.assertEqual(len(learn.load(skill / learn.LOG_NAME)), 1)
            self.assertEqual(learn.main([*base, "add", "--skill", "nope", "--kind", "failure", "--note", "n"]), 2)


if __name__ == "__main__":
    unittest.main()
