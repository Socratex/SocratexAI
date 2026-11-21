"""Tests of the flow-panel background-task re-check logic (runs the real <tasks> and <recheck> blocks with Node 22+)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402


def run(expr: str) -> object:
    return run_blocks(expr, "tasks", "recheck")


STATE = "{isEnabled: true, failures: 0, mainRunning: false, liveAgents: 0, nodes: [{taskId: 'a', running: 1}]}"


def state(**over: str) -> str:
    base = {"isEnabled": "true", "failures": "0", "mainRunning": "false", "liveAgents": "0", "nodes": "[{taskId: 'a', running: 1}]"}
    base.update(over)
    return "{" + ", ".join(f"{k}: {v}" for k, v in base.items()) + "}"


class FlowRecheck(unittest.TestCase):
    def test_checks_when_only_background_tasks_run(self) -> None:
        self.assertTrue(run(f"shouldRecheck({STATE})"))
        self.assertTrue(run(f"shouldRecheck({state(nodes="[{taskId: 'a', running: 1}, {key: 'x', running: 0}]")})"))

    def test_no_check_while_other_work_runs(self) -> None:
        self.assertFalse(run(f"shouldRecheck({state(mainRunning='true')})"))
        self.assertFalse(run(f"shouldRecheck({state(liveAgents='1')})"))
        nodes = "[{taskId: 'a', running: 1}, {running: 1}]"  # a tool or side fork is running too
        self.assertFalse(run(f"shouldRecheck({state(nodes=nodes)})"))

    def test_no_check_without_tasks_or_when_switched_off_or_given_up(self) -> None:
        self.assertFalse(run(f"shouldRecheck({state(nodes='[]')})"))
        self.assertFalse(run(f"shouldRecheck({state(nodes="[{taskId: 'a', running: 0}]")})"))
        self.assertFalse(run(f"shouldRecheck({state(isEnabled='false')})"))
        self.assertFalse(run(f"shouldRecheck({state(failures='3')})"))
        self.assertTrue(run(f"shouldRecheck({state(failures='2')})"))

    def test_probe_of_a_status(self) -> None:
        self.assertEqual(run("probeOfResult({result: {taskId: 'a', status: 'working'}})"), {"kind": "running"})
        self.assertEqual(run("probeOfResult({taskId: 'a', status: 'Working'})"), {"kind": "running"})  # bare record
        self.assertEqual(run("probeOfResult({result: {status: 'completed'}})"), {"kind": "ended", "status": "completed"})
        self.assertEqual(run("probeOfResult({result: {status: 'failed'}})"), {"kind": "ended", "status": "failed"})
        for word in ("killed", "stopped", "cancelled"):
            self.assertEqual(run(f"probeOfResult({{result: {{status: '{word}'}}}})"), {"kind": "ended", "status": "killed"}, word)

    def test_unknown_shapes_and_statuses_close_nothing(self) -> None:
        for expr in ("undefined", "{}", "{result: 'text'}", "{result: {status: 3}}", "{result: {status: 'weird'}}", "'oops'"):
            self.assertEqual(run(f"probeOfResult({expr})"), {"kind": "unknown"}, expr)
            self.assertNotIn("close", run(f"decideProbe(probeOfResult({expr}), {{failures: 0}})"))

    def test_deny_and_errors_are_failures(self) -> None:
        self.assertEqual(run("probeOfResult({deny: 'no'})"), {"kind": "error"})
        self.assertEqual(run("probeOfResult({isError: true, text: 'boom'})"), {"kind": "error"})
        self.assertEqual(run("probeOfError(new Error('network down'))"), {"kind": "error"})
        self.assertEqual(run("probeOfError('x')"), {"kind": "error"})

    def test_not_found_is_only_a_failure(self) -> None:
        for text in ("Task not found: abc", "No such task", "unknown task abc", "Tool not found: GetTask", "timeout"):
            self.assertEqual(run(f"probeOfError(new Error({text!r}))"), {"kind": "error"}, text)
        self.assertEqual(run("probeOfResult({isError: true, text: 'Task not found'})"), {"kind": "error"})

    def test_decide_close_and_book(self) -> None:
        fresh = "{failures: 0}"
        self.assertEqual(run(f"decideProbe({{kind: 'running'}}, {{failures: 2}})"), {"book": {"failures": 0}})
        self.assertEqual(
            run(f"decideProbe({{kind: 'ended', status: 'failed'}}, {fresh})"),
            {"close": "failed", "book": {"failures": 0}},
        )

    def test_not_found_keeps_the_task_running(self) -> None:
        for expr in ("probeOfResult({isError: true, text: 'Task not found'})", "probeOfError(new Error('No such task'))"):
            decided = run(f"decideProbe({expr}, {{failures: 1}})")
            self.assertNotIn("close", decided)
            self.assertEqual(decided["book"], {"failures": 2})

    def test_failure_backoff(self) -> None:
        book = run("[1, 2, 3].reduce((b) => decideProbe({kind: 'error'}, b).book, {failures: 0})")
        self.assertEqual(book["failures"], 3)
        self.assertTrue(run("isRecheckOff(3)"))
        self.assertFalse(run("isRecheckOff(2)"))
        # a good answer resets the run of failures
        self.assertEqual(run("decideProbe({kind: 'running'}, {failures: 2})")["book"]["failures"], 0)

    def test_tasks_to_probe_respects_the_start_grace_and_dedupes(self) -> None:
        nodes = "[{taskId: 'old', running: 1}, {taskId: 'new', running: 1}, {taskId: 'done', running: 0}, {taskId: 'unseen', running: 1}, {running: 1}]"
        live = "new Map([['old', 0], ['new', 95000], ['done', 0]])"
        self.assertEqual(run(f"tasksToProbe({nodes}, {live}, 100000)"), ["old"])
        self.assertEqual(run("tasksToProbe([{taskId: 'a', running: 1}, {taskId: 'a', running: 1}], new Map([['a', 0]]), 100000)"), ["a"])


if __name__ == "__main__":
    unittest.main()
