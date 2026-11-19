"""Tests of the flow-panel tps -> tier mapping (runs the real code with Node 22+)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "claude/mods/flow-panel/hooks/register.tsx"
NODES = [str(Path.home() / ".local/opt/node22/bin/node"), "node"]


def _node() -> str | None:
    for candidate in NODES:
        path = candidate if Path(candidate).is_absolute() else shutil.which(candidate)
        if not path or not Path(path).exists():
            continue
        out = subprocess.run([path, "--version"], capture_output=True, text=True).stdout.strip()
        major = int(re.match(r"v(\d+)", out).group(1)) if re.match(r"v(\d+)", out) else 0
        if major >= 22:
            return path
    return None


def _run(expr: str) -> object:
    """Evaluate a JS expression inside the <tiers> block of register.tsx."""
    node = _node()
    if node is None:
        raise unittest.SkipTest("Node 22+ not available")
    block = re.search(r"// <tiers>\n(.*?)// </tiers>", SOURCE.read_text(), re.S)
    assert block, "tiers block markers missing in register.tsx"
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "t.ts"
        script.write_text(block.group(1) + f"\nconsole.log(JSON.stringify(({expr}) ?? null))\n")
        res = subprocess.run(
            [node, "--experimental-strip-types", "--no-warnings", str(script)], capture_output=True, text=True
        )
    assert res.returncode == 0, res.stderr
    return json.loads(res.stdout)


class FlowTiers(unittest.TestCase):
    def test_eight_tiers_one_to_eight_dots(self) -> None:
        self.assertEqual(_run("TIERS.map(t => t.dots)"), [1, 2, 3, 4, 5, 6, 7, 8])

    def test_thresholds_start_at_zero_and_strictly_increase(self) -> None:
        mins = _run("TIERS.map(t => t.minTps)")
        self.assertEqual(mins[0], 0)
        self.assertTrue(all(a < b for a, b in zip(mins, mins[1:])))

    def test_every_boundary_belongs_to_the_higher_tier(self) -> None:
        mins = _run("TIERS.map(t => t.minTps)")
        for i, m in enumerate(mins):
            self.assertEqual(_run(f"tierOf({m})"), i)
            if i:
                self.assertEqual(_run(f"tierOf({m} - 0.001)"), i - 1)

    def test_zero_negative_and_unknown_are_the_lowest_tier(self) -> None:
        for value in ["0", "-5", "undefined", "NaN"]:
            self.assertEqual(_run(f"tierOf({value})"), 0)

    def test_huge_values_cap_at_the_top_tier(self) -> None:
        for value in ["1e6", "1e12", "Infinity"]:
            self.assertEqual(_run(f"tierOf({value})"), 7)

    def test_monotonic(self) -> None:
        tiers = _run("Array.from({length: 20000}, (_, i) => tierOf(i * 0.5))")
        self.assertTrue(all(a <= b for a, b in zip(tiers, tiers[1:])))

    def test_pace_of_a_turn(self) -> None:
        self.assertEqual(_run("paceOf(1000, 2000)"), 500)
        self.assertIsNone(_run("paceOf(1000, 100)"))  # too short to mean anything
        self.assertEqual(_run("paceOf(0, 5000)"), 0)

    def test_busiest_line_is_painted_last_and_ties_keep_order(self) -> None:
        order = _run(
            "byIntensity([{rank: 3, n: 'a'}, {rank: -1, n: 'b'}, {rank: 7, n: 'c'}, "
            "{rank: 3, n: 'd'}, {rank: 0, n: 'e'}]).map(x => x.n)"
        )
        self.assertEqual(order, ["b", "e", "a", "d", "c"])

    def test_side_fork_is_a_fork_without_a_tool_call(self) -> None:
        # /btw, /subtask and /fork start a fork with an empty tool_use_id
        self.assertTrue(_run("isSideFork({fork: true, tool_use_id: ''})"))
        self.assertTrue(_run("isSideFork({fork: true})"))

    def test_agent_tool_fork_and_plain_agents_are_not_side(self) -> None:
        self.assertFalse(_run("isSideFork({fork: true, tool_use_id: 'toolu_1'})"))
        self.assertFalse(_run("isSideFork({fork: false, tool_use_id: ''})"))
        self.assertFalse(_run("isSideFork({tool_use_id: ''})"))

    def test_figure_toggle_cycles_through_three_states(self) -> None:
        self.assertEqual(_run("FIGURES"), ["cost", "tokens", "time"])
        self.assertEqual(_run("nextFigure('cost')"), "tokens")
        self.assertEqual(_run("nextFigure('tokens')"), "time")
        self.assertEqual(_run("nextFigure('time')"), "cost")
        self.assertEqual(_run("nextFigure(undefined)"), "tokens")  # unknown counts as the first state

    def test_token_format(self) -> None:
        cases = {"0": "0", "950": "950", "1000": "1k", "1234": "1.2k", "34500": "35k", "1500000": "1.5M", "-5": "0"}
        for value, text in cases.items():
            self.assertEqual(_run(f"fmtTokens({value})"), text, value)
        self.assertEqual(_run("fmtTokens(NaN)"), "0")

    def test_time_format(self) -> None:
        cases = {"0": "0s", "400": "0.4s", "12000": "12s", "185000": "3m05s", "3720000": "1h02m"}
        for value, text in cases.items():
            self.assertEqual(_run(f"fmtTime({value})"), text, value)
        self.assertEqual(_run("fmtTime(undefined)"), "0s")


if __name__ == "__main__":
    unittest.main()
