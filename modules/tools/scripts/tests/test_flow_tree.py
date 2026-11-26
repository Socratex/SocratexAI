"""Tests of the flow-panel session tree derived from the desktop app's session store (runs the real <tree> block with Node 22+)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402


def run(expr: str) -> object:
    return run_blocks(expr, "tree")


def entry(local: str, **over: object) -> str:
    base = {"local": local, "cli": f"cli-{local}", "prior": [], "lastCli": "", "from": "", "isFork": False, "isArchived": False, "title": local, "created": 0, "mtime": 0}
    base.update(over)
    return json.dumps(base)


def entries(*items: str) -> str:
    return "[" + ", ".join(items) + "]"


def locals_of(nodes: list[dict]) -> list[object]:
    return [[n["entry"]["local"], locals_of(n["kids"])] for n in nodes]


class FlowTree(unittest.TestCase):
    def test_child_without_engine_id_and_a_grandchild_are_in_the_tree(self) -> None:
        store = entries(
            entry("root", cli="me"),
            entry("kid", **{"from": "root", "cli": "", "created": 1}),  # just started: no engine id yet
            entry("grandkid", **{"from": "kid", "created": 2}),
            entry("other", **{"from": "elsewhere"}),
        )
        got = run(f"treeBelow({store}, 'root')")
        self.assertEqual(locals_of(got), [["kid", [["grandkid", []]]]])
        self.assertEqual(got[0]["entry"]["cli"], "")

    def test_archived_and_forks_are_hidden_with_their_subtrees(self) -> None:
        store = entries(
            entry("root"),
            entry("old", **{"from": "root", "isArchived": True}),
            entry("underOld", **{"from": "old"}),
            entry("fork", **{"from": "root", "isFork": True}),
            entry("ok", **{"from": "root", "created": 5}),
            entry("first", **{"from": "root", "created": 1}),
        )
        self.assertEqual(locals_of(run(f"treeBelow({store}, 'root')")), [["first", []], ["ok", []]])

    def test_no_age_cutoff_and_cycles_do_not_loop(self) -> None:
        store = entries(entry("root", **{"from": "b"}), entry("a", **{"from": "root", "mtime": 1}), entry("b", **{"from": "a"}))
        self.assertEqual(locals_of(run(f"treeBelow({store}, 'root')")), [["a", [["b", []]]]])

    def test_own_local_id_by_current_last_or_earlier_engine_id(self) -> None:
        store = entries(entry("x", cli="c1"), entry("y", cli="c2", prior=["me"]), entry("z", cli="c3", lastCli="me2"))
        self.assertEqual(run(f"localIdOf({store}, 'c1', '')"), "x")
        self.assertEqual(run(f"localIdOf({store}, 'me', '')"), "y")  # the engine id changed since
        self.assertEqual(run(f"localIdOf({store}, 'me2', '')"), "z")
        self.assertEqual(run(f"localIdOf({store}, 'nobody', '')"), "")
        self.assertEqual(run(f"localIdOf({store}, 'nobody', 'x')"), "x")  # a learned id is kept


if __name__ == "__main__":
    unittest.main()
