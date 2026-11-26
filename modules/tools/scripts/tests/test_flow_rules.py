"""Tests of the flow-panel rules: `nextState` (events) and `reconcile` (real sources), one test per closing reason (real rules.ts, Node 22+)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402

START = "nextState(INITIAL_STATE, {type: 'task-start', now: 1000, startedAt: 900, id: 'b1', tool: 'Bash', args: {command: 'npm start'}})"
# a summary of a state that a test can compare: the work entries and the task node
SUMMARY = (
    "(s => ({work: [...s.work.values()].map(w => [w.id, w.kind, w.phase, w.reason ?? null, w.misses]),"
    " nodes: s.view.nodes.map(n => [n.key, n.running, n.errorAt, n.ms ?? 0])}))"
)


def run(expr: str) -> object:
    return run_blocks(expr)


def summary(expr: str) -> dict:
    return run(f"{SUMMARY}({expr})")


def ended(reason: str, status: str = "completed", now: int = 2000, with_agent: str = "false") -> str:
    return f"nextState({START}, {{type: 'task-ended', now: {now}, id: 'b1', reason: '{reason}', status: '{status}', withAgent: {with_agent}}})"


class FlowLifeCycle(unittest.TestCase):
    def test_a_task_starts_running_with_a_block(self) -> None:
        got = summary(START)
        self.assertEqual(got["work"], [["b1", "task", "running", None, 0]])
        self.assertEqual(got["nodes"], [["task:b1", 1, 0, 0]])

    def test_every_close_reason_has_a_one_line_rule(self) -> None:
        reasons = run("Object.keys(CLOSE_RULES)")
        self.assertEqual(len(reasons), 7)
        self.assertTrue(all(isinstance(run(f"CLOSE_RULES['{r}']"), str) for r in reasons))


class FlowClosingReasons(unittest.TestCase):
    def test_task_stop_closes_at_once_and_books_the_time(self) -> None:
        got = summary(ended("task-stop", "killed"))
        self.assertEqual(got["work"], [["b1", "task", "closed", "task-stop", 0]])
        self.assertEqual(got["nodes"], [["task:b1", 0, 0, 1100]])  # 2000 - the start 900

    def test_monitor_deadline_closes(self) -> None:
        self.assertEqual(summary(ended("monitor-deadline", "timeout"))["work"][0][2:4], ["closed", "monitor-deadline"])

    def test_notification_closes_and_a_failed_one_gets_the_red_ring(self) -> None:
        self.assertEqual(summary(ended("notification"))["nodes"][0][2], 0)
        got = summary(ended("notification", "failed"))
        self.assertEqual(got["work"][0][2:4], ["closed", "notification"])
        self.assertEqual(got["nodes"][0][2], 2000)  # errorAt

    def test_transcript_row_closes_only_what_is_followed(self) -> None:
        row = f"nextState({START}, {{type: 'row-ended', now: 2000, id: 'b1', status: 'completed'}})"
        self.assertEqual(summary(row)["work"][0][2:4], ["closed", "transcript-row"])
        other = f"nextState({START}, {{type: 'row-ended', now: 2000, id: 'zz', status: 'completed'}})"
        self.assertEqual(summary(other)["work"][0][2], "running")

    def test_an_ended_status_in_the_stop_list_closes_at_once(self) -> None:
        stopped = f"({{...{START}, lastStop: {{at: 1500, rows: [{{id: 'b1', status: 'Completed'}}]}}}})"
        got = summary(f"reconcile({stopped}, {{agents: undefined}}, 1600)")  # inside the grace: still closed
        self.assertEqual(got["work"][0][2:4], ["closed", "ended-status"])
        self.assertEqual(got["nodes"][0][1], 0)

    def test_two_missed_reconciles_close_it_not_one(self) -> None:
        stop = f"({{...{START}, lastStop: {{at: 1500, rows: []}}}})"
        first = f"reconcile({stop}, {{agents: undefined}}, 40000)"
        self.assertEqual(summary(first)["work"], [["b1", "task", "running", None, 1]])
        self.assertEqual(summary(f"reconcile({first}, {{agents: undefined}}, 70000)")["work"][0][2:4], ["closed", "missed-reconciles"])

    def test_a_running_task_in_the_saved_view_that_was_never_seen_is_closed(self) -> None:
        old = "({...INITIAL_STATE, view: {...INITIAL, nodes: [{key: 'task:old', taskId: 'old', running: 1, isBackground: true, startSum: 5, at: 0, errorAt: 0, w: 0, label: 'x', kind: 'tool'}]}})"
        self.assertEqual(summary(f"reconcile({old}, {{agents: undefined}}, 1000)")["nodes"], [["task:old", 0, 0, 0]])

    def test_a_closed_entry_stays_closed(self) -> None:
        closed = ended("task-stop", "killed")
        again = f"nextState({closed}, {{type: 'task-ended', now: 3000, id: 'b1', reason: 'notification', status: 'completed', withAgent: false}})"
        self.assertEqual(summary(again)["work"], [["b1", "task", "closed", "task-stop", 0]])


class FlowAgentsAndPrompts(unittest.TestCase):
    SPAWN = "nextState(INITIAL_STATE, {type: 'agent-spawn', now: 1000, agentId: 'a1', subagentType: 'Explore', background: true})"

    def test_a_background_agent_runs_until_the_list_says_it_is_over(self) -> None:
        self.assertEqual(summary(self.SPAWN)["work"], [["a1", "agent", "running", None, 0]])
        over = f"reconcile({self.SPAWN}, {{agents: [{{id: 'a1', status: 'completed'}}]}}, 2000)"
        got = summary(over)
        self.assertEqual(got["work"][0][2:4], ["closed", "ended-status"])
        self.assertEqual(got["nodes"][0][1], 0)

    def test_a_foreground_agent_is_not_followed(self) -> None:
        self.assertEqual(summary("nextState(INITIAL_STATE, {type: 'agent-spawn', now: 1, agentId: 'a2', subagentType: 'Explore'})")["work"], [])

    def test_a_new_prompt_keeps_only_work_that_still_runs(self) -> None:
        busy = f"nextState({START}, {{type: 'tool-start', now: 1100, tool: 'Read', args: {{}}}})"
        got = summary(f"nextState({busy}, {{type: 'prompt', usd: 1}})")
        self.assertEqual([n[0] for n in got["nodes"]], ["task:b1"])


class FlowSessionVisibility(unittest.TestCase):
    @staticmethod
    def entry(local: str, **over: object) -> str:
        base = {"local": local, "cli": f"cli-{local}", "prior": [], "lastCli": "", "from": "", "isFork": False, "isArchived": False, "title": local, "created": 0, "mtime": 0}
        base.update(over)
        return json.dumps(base)

    def tiles(self, *entries: str, shared: str = "new Map()") -> list[list[str]]:
        state = "({...INITIAL_STATE, selfId: 'cli-root'})"
        got = run(
            f"(s => s.view.subs.map(t => [t.id, t.title]))(reconcile({state}, {{agents: undefined, entries: [{', '.join(entries)}], shared: {shared}}}, 1))"
        )
        return got

    def test_archived_and_forks_are_hidden_a_starting_child_is_shown(self) -> None:
        got = self.tiles(
            self.entry("root"),
            self.entry("ok", **{"from": "root", "created": 1}),
            self.entry("old", **{"from": "root", "isArchived": True}),
            self.entry("fork", **{"from": "root", "isFork": True}),
            self.entry("new", **{"from": "root", "cli": "", "created": 2}),
        )
        self.assertEqual(got, [["cli-ok", "ok"], ["new", "new (starting)"]])

    def test_the_tree_is_recursive(self) -> None:
        got = run(
            "(s => s.view.subs.map(t => [t.id, t.subs.map(u => u.id)]))(reconcile({...INITIAL_STATE, selfId: 'cli-root'},"
            f" {{agents: undefined, entries: [{self.entry('root')}, {self.entry('a', **{'from': 'root'})}, {self.entry('b', **{'from': 'a'})}]}}, 1))"
        )
        self.assertEqual(got, [["cli-a", ["cli-b"]]])


if __name__ == "__main__":
    unittest.main()
