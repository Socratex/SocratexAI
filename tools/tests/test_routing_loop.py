"""Checks for the router feedback loop: risk scoring, outcome log and routing proposals."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_TOOLS = Path(__file__).parents[1]


def load_module(name: str):
    spec = importlib.util.spec_from_file_location(name, REPO_TOOLS / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses look the module up while the class is built
    spec.loader.exec_module(module)
    return module


risk = load_module("risk_score")
log = load_module("routing_log")
stats = load_module("routing_stats")
RULES = risk.load_rules()


def change(path: str, lines: int = 10):
    return risk.FileChange(path, lines)


def entry(**overrides) -> dict:
    base = {"date": "2026-11-16", "task": None, "type": "implementation", "tier": "standard", "agent": "implementer",
            "effort": "medium", "risk": 2, "level": "LIGHT", "first_pass": True, "fixes": 0, "escalated": False,
            "regression_of": None, "areas": ["Unity/Assets/Game"]}
    base.update(overrides)
    return base


class RiskScoreTests(unittest.TestCase):
    def test_docs_only_change_is_light(self):
        result = risk.score_changes([change("docs-tech/README.md")], RULES)
        self.assertEqual((result["score"], result["level"]), (0, "LIGHT"))

    def test_save_code_without_tests_is_full(self):
        result = risk.score_changes([change("Unity/Assets/Game/Runtime/Runtime/Save/SaveStore.cs")], RULES)
        self.assertEqual(result["level"], "FULL")
        self.assertEqual(result["score"], 6)

    def test_matching_test_change_removes_missing_tests_points(self):
        result = risk.score_changes([change("src/Game.Core/World/Map.cs"),
                                     change("tests/Game.Core.Tests/MapTests.cs")], RULES)
        self.assertEqual((result["score"], result["level"]), (2, "LIGHT"))

    def test_cheap_tier_retry_and_size_raise_score(self):
        changes = [change(f"Tools/x/f{i}.py", 40) for i in range(6)] + [change("Tools/x/tests/test_f.py")]
        result = risk.score_changes(changes, RULES, tier="cheap", attempt=2)
        self.assertEqual((result["score"], result["level"]), (4, "STANDARD"))

    def test_score_is_capped(self):
        changes = [change("Unity/ProjectSettings/ProjectSettings.asset", 400), change("x/Save/a.cs"),
                   change(".claude/settings.json"), change("src/Game.Core/a.cs")]
        self.assertEqual(risk.score_changes(changes, RULES, tier="cheap", attempt=3)["score"], RULES["levels"]["score_cap"])

    def test_generated_files_are_ignored(self):
        result = risk.score_changes([change("docs-tech/cache/doc_index.json", 30000), change("x/Repo/Core.dll")], RULES)
        self.assertEqual((result["files"], result["level"]), (0, "LIGHT"))

    def test_numstat_keeps_new_name_and_skips_binary_counts(self):
        parsed = risk.parse_numstat("3\t1\tsrc/{Old.cs => New.cs}\n-\t-\timg.png\n")
        self.assertEqual(parsed[1], risk.FileChange("img.png", 0))
        self.assertEqual(parsed[0], risk.FileChange("src/New.cs", 4))
        self.assertEqual(risk.renamed_target("a/{b => c/d}/e.cs"), "a/c/d/e.cs")


class RoutingLogTests(unittest.TestCase):
    def test_areas_are_short_unique_prefixes(self):
        paths = ["Unity/Assets/Game/Runtime/A.cs", "Unity/Assets/Game/Tests/B.cs", "TASKS.json", "Tools/build/x.py"]
        self.assertEqual(log.areas(paths), ["Unity/Assets/Game", "TASKS.json", "Tools/build"])

    def test_append_writes_one_json_line(self):
        args = log.parse_args(["--type", "docs", "--tier", "cheap", "--first-pass", "yes"])
        built = log.build_entry(args, [change("a/b.md")], {"score": 0, "level": "LIGHT"})
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "audits" / "routing_log.jsonl"
            log.append(built, target)
            log.append(built, target)
            lines = target.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["level"], "LIGHT")
        self.assertTrue(json.loads(lines[0])["first_pass"])


class RoutingStatsTests(unittest.TestCase):
    def test_small_samples_give_no_proposals(self):
        self.assertEqual(stats.summarize([entry() for _ in range(5)])["proposals"], [])

    def test_failing_cheap_tier_is_moved_up(self):
        entries = [entry(tier="cheap", first_pass=i < 5) for i in range(10)]
        self.assertIn("move default from cheap to standard", " ".join(stats.tier_proposals(entries)))

    def test_high_tier_is_never_proposed_to_go_top(self):
        entries = [entry(tier="high", first_pass=False) for _ in range(10)]
        self.assertFalse(any("to top" in proposal for proposal in stats.tier_proposals(entries)))

    def test_reliable_standard_tier_is_offered_cheaper(self):
        entries = [entry() for _ in range(10)]
        self.assertIn("try cheap instead of standard", " ".join(stats.tier_proposals(entries)))

    def test_high_tier_share_warning(self):
        entries = [entry(tier="high")] * 3 + [entry()] * 7
        self.assertTrue(stats.high_tier_proposal(entries))

    def test_regression_after_light_proposes_learned_rule(self):
        entries = [entry(task="aaa111", level="LIGHT", areas=["Unity/Assets/Game"]),
                   entry(task="bbb222", type="debug", regression_of="aaa111")]
        self.assertIn("add learned rule 'Unity/Assets/Game/*'", " ".join(stats.risk_proposals(entries)))

    def test_lower_effort_with_same_result_is_proposed(self):
        entries = [entry(effort="medium")] * 10 + [entry(effort="high")] * 10
        self.assertIn("effort medium does as well as high", " ".join(stats.effort_proposals(entries)))

    def test_broken_log_line_is_skipped(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "log.jsonl"
            target.write_text(json.dumps(entry()) + "\n{broken\n", encoding="utf-8")
            self.assertEqual(len(stats.load(target)), 1)

    def test_markdown_report_without_data(self):
        self.assertIn("None yet", stats.to_markdown(stats.summarize([])))


if __name__ == "__main__":
    unittest.main()
