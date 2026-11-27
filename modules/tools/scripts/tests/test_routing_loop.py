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
RULES_FILE = risk.DEFAULT_RULES
RULES = risk.load_rules(RULES_FILE)
GAME_RULES = risk.build_rules(Path("."), ["gamedev"], [])


def change(path: str, lines: int = 10):
    return risk.FileChange(path, lines)


def entry(**overrides) -> dict:
    base = {"date": "2026-11-16", "task": None, "type": "implementation", "tier": "standard", "agent": "implementer",
            "effort": "medium", "risk": 2, "level": "LIGHT", "first_pass": True, "fixes": 0, "escalated": False,
            "regression_of": None, "areas": ["src/app/core"]}
    base.update(overrides)
    return base


class RiskScoreTests(unittest.TestCase):
    def test_docs_only_change_is_light(self):
        result = risk.score_changes([change("docs/README.md")], RULES)
        self.assertEqual((result["score"], result["level"]), (0, "LIGHT"))

    def test_migration_code_without_tests_is_full(self):
        result = risk.score_changes([change("src/app/db/Migration.py"), change("src/app/db/auth/login.py")], RULES)
        self.assertEqual(result["level"], "FULL")
        self.assertEqual(result["score"], 10)

    def test_game_save_code_is_neutral_by_default_and_full_with_gamedev_profile(self):
        path = change("Unity/Assets/Game/Runtime/Save/SaveStore.cs")
        self.assertEqual(risk.score_changes([path], RULES)["score"], 2)
        result = risk.score_changes([path], GAME_RULES)
        self.assertEqual((result["score"], result["level"]), (6, "FULL"))

    def test_gamedev_profile_scores_project_files_and_ignores_meta(self):
        self.assertEqual(risk.score_changes([change("Unity/ProjectSettings/a.asset")], GAME_RULES)["score"], 4)
        self.assertEqual(risk.score_changes([change("Unity/Assets/a.cs.meta")], GAME_RULES)["files"], 0)
        self.assertEqual(risk.score_changes([change("Unity/Assets/a.cs.meta")], RULES)["files"], 1)

    def test_matching_test_change_removes_missing_tests_points(self):
        result = risk.score_changes([change("src/app/world/map.py"),
                                     change("tests/test_map.py")], RULES)
        self.assertEqual((result["score"], result["level"]), (0, "LIGHT"))
        self.assertEqual(risk.score_changes([change("src/app/world/map.py")], RULES)["score"], 2)

    def test_cheap_tier_retry_and_size_raise_score(self):
        changes = [change(f"tools/x/f{i}.py", 40) for i in range(6)] + [change("tools/x/tests/test_f.py")]
        result = risk.score_changes(changes, RULES, tier="cheap", attempt=2)
        self.assertEqual((result["score"], result["level"]), (4, "STANDARD"))

    def test_score_is_capped(self):
        changes = [change("Dockerfile", 400), change("db/schema.sql"), change(".claude/settings.json"), change("src/app/a.py")]
        self.assertEqual(risk.score_changes(changes, RULES, tier="cheap", attempt=3)["score"], RULES["levels"]["score_cap"])

    def test_generated_files_are_ignored(self):
        result = risk.score_changes([change("tools/cache/doc_index.json", 30000), change("x/Repo/Core.dll")], RULES)
        self.assertEqual((result["files"], result["level"]), (0, "LIGHT"))

    def test_numstat_keeps_new_name_and_skips_binary_counts(self):
        parsed = risk.parse_numstat("3\t1\tsrc/{Old.cs => New.cs}\n-\t-\timg.png\n")
        self.assertEqual(parsed[1], risk.FileChange("img.png", 0))
        self.assertEqual(parsed[0], risk.FileChange("src/New.cs", 4))
        self.assertEqual(risk.renamed_target("a/{b => c/d}/e.cs"), "a/c/d/e.cs")


class LayeredRulesTests(unittest.TestCase):
    def write(self, folder: str, name: str, data: dict) -> Path:
        path = Path(folder) / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_lists_append_without_duplicates_and_scalars_are_replaced(self):
        base = {"levels": {"light_max": 2}, "ignore_globs": ["a", "b"], "size": {"lines": 150, "points": 2},
                "missing_tests": {"points": 2, "code_suffixes": [".py"]}, "path_rules": []}
        over = {"levels": {"light_max": 3}, "ignore_globs": ["b", "c"], "size": {"points": 5},
                "missing_tests": {"code_suffixes": [".py", ".cs"]}}
        merged = risk.merge_rules(base, over)
        self.assertEqual(merged["ignore_globs"], ["a", "b", "c"])
        self.assertEqual((merged["levels"]["light_max"], merged["size"]), (3, {"lines": 150, "points": 5}))
        self.assertEqual(merged["missing_tests"], {"points": 2, "code_suffixes": [".py", ".cs"]})
        self.assertEqual(base["ignore_globs"], ["a", "b"])

    def test_same_name_path_rules_join_globs_and_new_names_append(self):
        base = {"path_rules": [{"name": "x", "points": 2, "globs": ["a"]}]}
        over = {"path_rules": [{"name": "x", "points": 4, "globs": ["a", "b"]}, {"name": "y", "points": 1, "globs": ["c"]}]}
        self.assertEqual(risk.merge_rules(base, over)["path_rules"],
                         [{"name": "x", "points": 4, "globs": ["a", "b"]}, {"name": "y", "points": 1, "globs": ["c"]}])

    def test_order_is_defaults_then_profiles_then_files_with_later_winning(self):
        with tempfile.TemporaryDirectory() as folder:
            default = self.write(folder, "d.json", {"levels": {"light_max": 1}, "ignore_globs": ["d"], "path_rules": []})
            self.write(folder, "profiles/p/RISK-RULES.json", {"levels": {"light_max": 2}, "ignore_globs": ["p"]})
            extra = self.write(folder, "extra.json", {"levels": {"light_max": 3}, "ignore_globs": ["e", "d"]})
            rules = risk.build_rules(Path(folder), ["p"], ["extra.json"], default, Path(folder) / "profiles")
            self.assertEqual((rules["levels"]["light_max"], rules["ignore_globs"]), (3, ["d", "p", "e"]))
            absolute = risk.build_rules(Path("elsewhere"), [], [str(extra)], default)
            self.assertEqual(absolute["levels"]["light_max"], 3)

    def test_missing_profile_or_file_is_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(FileNotFoundError):
                risk.build_rules(Path(folder), ["nope"], [])
            with self.assertRaises(FileNotFoundError):
                risk.build_rules(Path(folder), [], ["missing.json"])

    def test_legacy_ai_file_replaces_everything_only_without_layered_keys(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            legacy = dict(RULES, ignore_globs=["only-legacy"])
            self.write(folder, ".ai/RISK-RULES.json", legacy)
            original = risk.layered_config
            try:
                risk.layered_config = lambda root, home=None: ([], [])
                self.assertEqual(risk.load_rules(root=root)["ignore_globs"], ["only-legacy"])
                risk.layered_config = lambda root, home=None: (["gamedev"], [])
                layered = risk.load_rules(root=root)
                self.assertIn("*.meta", layered["ignore_globs"])
                self.assertIn("*.dll", layered["ignore_globs"])
                self.assertNotIn("only-legacy", layered["ignore_globs"])
            finally:
                risk.layered_config = original

    def test_project_config_keys_are_read_through_the_config_resolver(self):
        with tempfile.TemporaryDirectory() as folder:
            self.write(folder, ".socratex/config.json", {"schema_version": 1, "profiles": ["gamedev"], "risk_rules": ["x.json"]})
            self.assertEqual(risk.layered_config(Path(folder)), (["gamedev"], ["x.json"]))


class RoutingLogTests(unittest.TestCase):
    def test_areas_are_short_unique_prefixes(self):
        paths = ["src/app/core/a.py", "src/app/core/tests/b.py", "README.md", "tools/build/x.py"]
        self.assertEqual(log.areas(paths), ["src/app/core", "README.md", "tools/build"])

    def test_append_writes_one_json_line(self):
        args = log.parse_args(["--type", "docs", "--tier", "cheap", "--first-pass", "yes"])
        built = log.build_entry(args, [change("a/b.md")], {"score": 0, "level": "LIGHT"})
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "logs" / "routing_log.jsonl"
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
        entries = [entry(task="aaa111", level="LIGHT", areas=["src/app/core"]),
                   entry(task="bbb222", type="debug", regression_of="aaa111")]
        self.assertIn("add learned rule 'src/app/core/*'", " ".join(stats.risk_proposals(entries)))

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
