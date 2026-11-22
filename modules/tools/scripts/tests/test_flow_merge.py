"""Tests of the flow-panel merge of cheap leaf blocks (runs the real <merge> block with Node 22+)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402

# A row as `rowsOf` builds it, with only the fields the merge reads.
ROW = (
    "const row = (label, kind, usd, o = {}) => ({label, kind, usd, tok: 1000, ms: 2000, liveN: 0, liveSum: 0, text: 'x', "
    "isActive: false, kids: [], ...o});"
)


def run(expr: str) -> object:
    return run_blocks(f"(() => {{ {ROW} return {expr} }})()", "tiers", "merge")


class FlowMerge(unittest.TestCase):
    def test_two_cheap_blocks_of_a_category_become_one(self) -> None:
        rows = run("mergeCheap([row('Grep','tool',0.002), row('Read','tool',0.004)], 'cost', 0).map(r => [r.label, r.text])")
        self.assertEqual(rows, [["Tools", "0.6¢"]])

    def test_a_single_cheap_block_stays_as_is(self) -> None:
        rows = run("mergeCheap([row('Grep','tool',0.002), row('Bash','mcp',0.5)], 'cost', 0).map(r => r.label)")
        self.assertEqual(rows, ["Grep", "Bash"])

    def test_threshold_is_one_cent_and_exact_cent_is_not_cheap(self) -> None:
        rows = run("mergeCheap([row('A','tool',0.0099), row('B','tool',0.01), row('C','tool',0.0001)], 'cost', 0).map(r => r.label)")
        self.assertEqual(rows, ["Tools", "B"])

    def test_categories_are_merged_apart_with_their_labels(self) -> None:
        rows = run(
            "mergeCheap([row('a','tool',0.001), row('s1','skill',0.001), row('m1','mcp',0.001), row('p1','app',0.001), "
            "row('b','tool',0.001), row('s2','skill',0.001), row('m2','mcp',0.001), row('p2','app',0.001)], 'cost', 0).map(r => r.label)"
        )
        self.assertEqual(rows, ["Tools", "Skills", "MCP", "Apps"])

    def test_blocks_with_unknown_cost_children_agents_and_tasks_are_not_merged(self) -> None:
        rows = run(
            "mergeCheap([row('u1','tool',undefined), row('u2','tool',undefined), row('k','tool',0.001,{kids:[1]}), row('k2','tool',0.001,{kids:[1]}), "
            "row('ag','agent',0.001), row('ag2','agent',0.001), row('t1','tool',0.001,{noUsage:true}), row('t2','tool',0.001,{noUsage:true}), "
            "row('ok','tool',0.001)], 'cost', 0).map(r => r.label)"
        )
        self.assertEqual(rows, ["u1", "u2", "k", "k2", "ag", "ag2", "t1", "t2", "ok"])

    def test_merged_block_takes_the_place_of_the_first_member(self) -> None:
        rows = run("mergeCheap([row('big','tool',0.5), row('a','tool',0.001), row('mid','mcp',0.2), row('b','tool',0.001)], 'cost', 0).map(r => r.label)")
        self.assertEqual(rows, ["big", "Tools", "mid"])

    def test_same_blocks_under_every_unit(self) -> None:
        rows = [
            "row('Grep','tool',0.002)",
            "row('Read','tool',0.004,{calls:2})",
            "row('Edit','tool',0.3)",
            "row('a','skill',0.001)",
            "row('b','skill',0.001)",
            "row('c','mcp',0.001)",
        ]
        labels = {
            unit: run(f"mergeCheap([{', '.join(rows)}], '{unit}', 0).map(r => r.label)") for unit in ("cost", "time", "tokens")
        }
        self.assertEqual(labels["cost"], ["Tools", "Edit", "Skills", "c"])
        self.assertEqual(labels["time"], labels["cost"])
        self.assertEqual(labels["tokens"], labels["cost"])

    def test_merged_block_shows_the_sum_in_the_current_unit(self) -> None:
        rows = "[row('a','tool',0.002,{tok:1000,ms:2000}), row('b','tool',0.004,{tok:2500,ms:3000})]"
        self.assertEqual(run(f"mergeCheap({rows}, 'cost', 0)[0].text"), "0.6¢")
        self.assertEqual(run(f"mergeCheap({rows}, 'time', 0)[0].text"), "5s")
        self.assertEqual(run(f"mergeCheap({rows}, 'tokens', 0)[0].text"), "3.5K")

    def test_tooltip_lists_members_one_per_line_in_the_current_unit(self) -> None:
        rows = "[row('Grep','tool',0.002,{tok:1000,ms:2000}), row('Read','tool',0.004,{calls:2,tok:500,ms:3000})]"
        self.assertEqual(run(f"mergeCheap({rows}, 'cost', 0)[0].full"), "Grep 0.2¢\nRead (x2) 0.4¢")
        self.assertEqual(run(f"mergeCheap({rows}, 'time', 0)[0].full"), "Grep 2s\nRead (x2) 3s")
        self.assertEqual(run(f"mergeCheap({rows}, 'tokens', 0)[0].full"), "Grep 1.0K\nRead (x2) 0.5K")

    def test_duplicate_names_are_merged_with_a_call_counter(self) -> None:
        rows = "[row('Read','tool',0.002), row('Read','tool',0.002,{calls:3}), row('Grep','tool',0.001)]"
        self.assertEqual(run(f"mergeCheap({rows}, 'cost', 0)[0].full"), "Read (x4) 0.4¢\nGrep 0.1¢")

    def test_active_if_any_member_is_active_and_led_if_any_has_one(self) -> None:
        rows = "[row('a','tool',0.001), row('b','tool',0.001,{isActive:true, led:true})]"
        self.assertTrue(run(f"mergeCheap({rows}, 'cost', 0)[0].isActive"))
        self.assertTrue(run(f"mergeCheap({rows}, 'cost', 0)[0].led"))
        quiet = "[row('a','tool',0.001), row('b','tool',0.001)]"
        self.assertFalse(run(f"mergeCheap({quiet}, 'cost', 0)[0].isActive"))
        self.assertFalse(run(f"!!mergeCheap({quiet}, 'cost', 0)[0].led"))

    def test_error_ring_beats_background_ring_beats_none(self) -> None:
        both = "[row('a','tool',0.001,{ring:'background'}), row('b','tool',0.001,{ring:'error'}), row('c','tool',0.001)]"
        self.assertEqual(run(f"mergeCheap({both}, 'cost', 0)[0].ring"), "error")
        green = "[row('a','tool',0.001,{ring:'background'}), row('c','tool',0.001)]"
        self.assertEqual(run(f"mergeCheap({green}, 'cost', 0)[0].ring"), "background")
        self.assertIsNone(run("mergeCheap([row('a','tool',0.001), row('c','tool',0.001)], 'cost', 0)[0].ring"))

    def test_live_time_of_members_ticks_in_the_merged_figure(self) -> None:
        # one member runs since t=1000, now t=4000: 3 s live on top of its 2 s booked, plus the other's 2 s
        rows = "[row('a','tool',0.001,{liveN:1, liveSum:1000}), row('b','tool',0.001)]"
        self.assertEqual(run(f"mergeCheap({rows}, 'time', 4000)[0].text"), "7s")

    def test_tooltip_text_is_stripped_of_markup(self) -> None:
        rows = "[row('a<b>','tool',0.001), row('c&d','tool',0.001)]"
        self.assertEqual(run(f"mergeCheap({rows}, 'cost', 0)[0].full"), "ab 0.1¢\ncd 0.1¢")

    def test_names_sharing_a_cut_prefix_stay_apart_and_show_whole(self) -> None:
        # regression: labels are cut to 8 characters; the whole name is `full`
        rows = (
            "[row('skill-a\u2026','skill',0.001,{full:'skill-alpha'}), row('skill-a\u2026','skill',0.001,{full:'skill-akira'}), "
            "row('skill-a\u2026','skill',0.001,{full:'skill-akira'})]"
        )
        self.assertEqual(run(f"mergeCheap({rows}, 'cost', 0)[0].full"), "skill-alpha 0.1¢\nskill-akira (x2) 0.2¢")


if __name__ == "__main__":
    unittest.main()
