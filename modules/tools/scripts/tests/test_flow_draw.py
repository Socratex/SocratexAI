"""Tests of the flow-panel drawing of task blocks and merged blocks (real register.tsx, fixed data, Node 22+)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_module  # noqa: E402

NOW = 1_000_000
LED = '<circle cx="'  # the LED and the plain activity dot are both circles; the LED has the background-grey fill
GREEN = "#9e9e9e"

SETUP = f"""
const NOW = {NOW}
const mk = (key: string, kind: string, o: Record<string, unknown> = {{}}): FlowNode =>
  ({{ key, label: key, kind, at: NOW, running: 0, isBackground: false, errorAt: 0, w: 0, ms: 2000, tok: 1000, ...o }}) as FlowNode
const task = mk('task:b1', 'tool', {{
  label: 'Run the dev server', taskId: 'b1', taskName: 'Run the dev server', hasUsage: false,
  running: 1, isBackground: true, startSum: NOW - 5000, calls: 1, ms: 0,
}})
const grep = mk('tool:Grep', 'tool', {{ label: 'Grep', usd: 0.002, ms: 2000, tok: 1000 }})
const read = mk('tool:Read', 'tool', {{ label: 'Read', usd: 0.004, ms: 3000, tok: 500, calls: 2 }})
const agent = mk('agent:Explore', 'agent', {{ label: 'Explore', usd: 0.5, running: 1, isBackground: true, startSum: NOW - 9000, tps: 3000 }})
const view = (nodes: FlowNode[], extra: Partial<FlowView> = {{}}): FlowView => ({{ ...INITIAL, nodes, ...extra }})
const count = (s: string, part: string): number => s.split(part).length - 1
"""


def run(tail: str) -> object:
    return run_module("{" + SETUP + tail + "}")  # a block, so the names below may shadow the module's


class FlowDraw(unittest.TestCase):
    def test_task_block_has_a_led_and_a_pulsing_line_but_no_dots(self) -> None:
        got = run(
            "const s = fitted(view([task]), NOW, 'cost');"
            f"console.log(JSON.stringify({{leds: count(s, 'fill=\"{GREEN}\" stroke=\"#000\"'), ellipses: count(s, '<ellipse'), motion: count(s, 'animateMotion'),"
            " pulse: count(s, 'values=\"0.7;0.15;0.7\"'), glow: count(s, 'values=\"0.25;0.7;0.25\"'), ring: count(s, 'stroke=\"#9e9e9e\"'),"
            " title: s.includes('<title>Run the dev server</title>'), label: s.includes('>Run the…<') || s.includes('>Run the…</text>')}))"
        )
        self.assertEqual(got["leds"], 1)
        self.assertEqual(got["ellipses"], 0)
        self.assertEqual(got["motion"], 0)
        self.assertGreaterEqual(got["pulse"], 1)  # the line pulses
        self.assertGreaterEqual(got["glow"], 1)  # the block glows
        self.assertGreaterEqual(got["ring"], 1)  # grey ring
        self.assertTrue(got["title"])  # tooltip: the full task name

    def test_task_figure_is_time_only(self) -> None:
        got = run(
            "console.log(JSON.stringify(['cost','tokens','time'].map(f => { const s = fitted(view([task]), NOW, f as Figure);"
            " return [s.includes('>-<'), /<text class=\"t\"[^>]*>5s</.test(s)] })))"
        )
        self.assertEqual(got[0], [True, False])
        self.assertEqual(got[1], [True, False])
        self.assertEqual(got[2][0], False)  # no placeholder dash in time view
        self.assertTrue(got[2][1])  # ticking time, 5 s after the start

    def test_background_agent_keeps_its_dots_and_gets_no_led(self) -> None:
        got = run(
            "const s = fitted(view([agent]), NOW, 'cost');"
            f"console.log(JSON.stringify({{leds: count(s, 'fill=\"{GREEN}\" stroke=\"#000\"'), ellipses: count(s, '<ellipse')}}))"
        )
        self.assertEqual(got["leds"], 0)
        self.assertGreater(got["ellipses"], 0)

    def test_merged_block_has_a_tooltip_with_its_members(self) -> None:
        got = run(
            "console.log(JSON.stringify(['cost','time','tokens'].map(f => { const s = fitted(view([grep, read]), NOW, f as Figure);"
            " return [s.match(/<title>([^<]*)<\\/title>/)?.[1], s.includes('>Tools<'), s.includes('>Grep<')] })))"
        )
        self.assertEqual(got[0], ["Grep 0.2¢\nRead (x2) 0.4¢", True, False])
        self.assertEqual(got[1][0], "Grep 2s\nRead (x2) 3s")
        self.assertEqual(got[2][0], "Grep 1.0K\nRead (x2) 0.5K")
        self.assertTrue(got[1][1] and got[2][1])  # the same single block under every unit

    def test_a_task_and_cheap_blocks_are_drawn_together_without_merging_the_task(self) -> None:
        got = run(
            "const s = fitted(view([task, grep, read, agent]), NOW, 'cost');"
            "console.log(JSON.stringify({tools: s.includes('>Tools<'), task: s.includes('>Run the…<'), agent: s.includes('>Explore<')}))"
        )
        self.assertEqual(got, {"tools": True, "task": True, "agent": True})

    def test_drawing_stays_under_the_size_limit_with_the_most_blocks(self) -> None:
        got = run(
            "const kinds = ['tool','mcp','skill','app'];"
            "const many = (n: number): FlowNode[] => Array.from({length: n}, (_, i) => mk(`${kinds[i % 4]}:n${i}`, kinds[i % 4]!,"
            " { label: `item${i}`, usd: 0.05 + i, running: 1, tps: 1500 + i * 400, tpsIn: 900 + i * 300, isBackground: i % 3 === 0 }));"
            "const sub = (id: string): SubTree => ({ id, nodes: many(12), subs: [], mainRunning: true, isWaiting: false, wTotal: 0, k: 0, usd: 1, perW: 1 });"
            "const big = view(many(12), { mainRunning: true, subs: [sub('a'), sub('b'), sub('c'), sub('d')] });"
            "const s = fitted(big, NOW, 'cost');"
            "console.log(JSON.stringify({len: s.length, closed: s.endsWith('</svg>'), limit: SVG_LIMIT, max: MAX_NODES}))"
        )
        self.assertEqual(got["max"], 12)
        self.assertLessEqual(got["len"], got["limit"])
        self.assertTrue(got["closed"])

    def test_twelve_blocks_fit_without_folding(self) -> None:
        got = run(
            "const kinds = ['tool','mcp','skill','app'];"
            "const many = Array.from({length: 12}, (_, i) => mk(`${kinds[i % 4]}:n${i}`, kinds[i % 4]!, { label: `item${i}`, usd: 0.05 + i, running: 1, tps: 6000, tpsIn: 6000 }));"
            "const s = fitted(view(many, { mainRunning: true }), NOW, 'cost');"
            "console.log(JSON.stringify({len: s.length, items: count(s, '>item') }))"
        )
        self.assertLessEqual(got["len"], 126000)
        self.assertEqual(got["items"], 12)

    def test_background_task_time_stays_out_of_the_sums(self) -> None:
        # regression: a task running for a long time must not inflate the total (trunk) time
        got = run(
            "const long = { ...task, startSum: NOW - 1800000 };"
            "const sub: SubTree = { id: 's', nodes: [grep], subs: [], mainRunning: false, isWaiting: false, wTotal: 0, k: 0, usd: 0, perW: 1 };"
            "const s = fitted(view([long, grep], { subs: [sub] }), NOW, 'time');"
            "const labels = [...s.matchAll(/<text class=\"t\"[^>]*>([^<]*)</g)].map(m => m[1]);"
            "console.log(JSON.stringify({labels, has30: s.includes('>30m00s<')}))"
        )
        self.assertTrue(got["has30"])  # the task's own line still shows its 30 minutes
        self.assertEqual(sum(1 for t in got["labels"] if t == "30m00s"), 1)  # and nothing else does (trunk, session)


if __name__ == "__main__":
    unittest.main()
