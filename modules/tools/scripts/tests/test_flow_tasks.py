"""Tests of the flow-panel background-task parsing (runs the real <tasks> block with Node 22+)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402


def run(expr: str) -> object:
    return run_blocks(expr, "tasks")


def verdict(expr: str) -> object:
    return run(f"(v => ({{close: v.close, misses: [...v.misses]}}))({expr})")


class FlowTasks(unittest.TestCase):
    def test_background_bash_task_id_comes_from_the_result(self) -> None:
        self.assertEqual(run("taskIdOf('Bash', {result: {stdout: '', backgroundTaskId: 'bx1'}})"), "bx1")
        self.assertEqual(run("taskIdOf('Bash', {backgroundTaskId: 'bx2'})"), "bx2")  # a bare record works too

    def test_foreground_bash_has_no_task(self) -> None:
        self.assertIsNone(run("taskIdOf('Bash', {result: {stdout: 'ok', interrupted: false}})"))
        self.assertIsNone(run("taskIdOf('Bash', {result: {backgroundTaskId: ''}})"))
        self.assertIsNone(run("taskIdOf('Bash', undefined)"))

    def test_monitor_task_id_and_other_tools(self) -> None:
        self.assertEqual(run("taskIdOf('Monitor', {result: {taskId: 'm7', timeoutMs: 300000}})"), "m7")
        self.assertIsNone(run("taskIdOf('Read', {result: {taskId: 'x'}})"))  # only Bash and Monitor start tasks

    def test_monitor_timeout(self) -> None:
        self.assertEqual(run("monitorTimeoutMs({result: {taskId: 'm', timeoutMs: 300000}})"), 300000)
        self.assertEqual(run("monitorTimeoutMs({result: {taskId: 'm', timeoutMs: 0, persistent: true}})"), 0)
        self.assertEqual(run("monitorTimeoutMs({result: {taskId: 'm', timeoutMs: 5, persistent: true}})"), 0)

    def test_task_name_is_description_else_command(self) -> None:
        self.assertEqual(run("taskNameOf('Bash', {description: 'Run the server', command: 'npm start'})"), "Run the server")
        self.assertEqual(run("taskNameOf('Bash', {command: 'npm   start\\n--port 1'})"), "npm start --port 1")
        self.assertEqual(run("taskNameOf('Monitor', {description: 'Watch the log', command: 'tail -f x'})"), "Watch the log")
        self.assertEqual(run("taskNameOf('Bash', {})"), "Bash")
        self.assertEqual(len(run("taskNameOf('Bash', {command: 'x'.repeat(5000)})")), 200)

    def test_stopped_task(self) -> None:
        self.assertEqual(run("stoppedTaskOf({task_id: 'a'}, {result: {task_id: 'b', message: 'ok'}})"), "b")
        self.assertEqual(run("stoppedTaskOf({task_id: 'a'}, undefined)"), "a")
        self.assertEqual(run("stoppedTaskOf({shell_id: 's'}, {})"), "s")
        self.assertIsNone(run("stoppedTaskOf({}, {})"))

    def test_task_end_notification(self) -> None:
        text = (
            "<task-notification>\n<task-id>bx1</task-id>\n<tool-use-id>toolu_1</tool-use-id>\n"
            "<output-file>/tmp/bx1.output</output-file>\n<status>completed</status>\n"
            '<summary>Background command "npm start" completed (exit code 0)</summary>\n</task-notification>'
        )
        got = run(f"parseTaskEnd({text!r})")
        self.assertEqual(got["id"], "bx1")
        self.assertEqual(got["status"], "completed")
        self.assertTrue(got["isEnded"])
        self.assertIn("npm start", got["summary"])

    def test_failed_and_killed_are_ends_too(self) -> None:
        for status in ("failed", "killed", "Completed"):
            got = run(f"parseTaskEnd('<task-notification><task-id>t</task-id><status>{status}</status></task-notification>')")
            self.assertTrue(got["isEnded"], status)
            self.assertEqual(got["status"], status.lower())

    def test_notification_without_a_status_is_not_an_end(self) -> None:
        got = run("parseTaskEnd('<task-notification><task-id>m7</task-id><summary>Monitor event</summary></task-notification>')")
        self.assertEqual(got["id"], "m7")
        self.assertFalse(got["isEnded"])
        self.assertFalse(run("parseTaskEnd('<task-notification><task-id>m7</task-id><status>running</status></task-notification>')")["isEnded"])

    def test_text_without_an_id_is_ignored(self) -> None:
        self.assertIsNone(run("parseTaskEnd('hello there')"))
        self.assertIsNone(run("parseTaskEnd('')"))

    def test_loose_id_formats(self) -> None:
        self.assertEqual(run("parseTaskEnd('task id: ab-12 status')")["id"], "ab-12")

    def test_task_not_seen_starting_in_this_process_is_closed(self) -> None:
        # regression: the stored view survives a reload, the set of live tasks does not
        got = run(
            "closeStaleTasks([{taskId: 'old', running: 1, startSum: 5, isBackground: true}, "
            "{taskId: 'live', running: 1, startSum: 7, isBackground: true}, "
            "{taskId: 'done', running: 0, isBackground: false}, {running: 1, isBackground: false}], id => id === 'live')"
        )
        self.assertEqual(got[0], {"taskId": "old", "running": 0, "startSum": 0, "isBackground": False})
        self.assertEqual(got[1]["running"], 1)  # seen live: no time limit
        self.assertEqual(got[2]["running"], 0)
        self.assertEqual(got[3]["running"], 1)  # not a task node
        self.assertTrue(run("isStaleTask({taskId: 'x', running: 1, isBackground: true}, () => false)"))
        self.assertFalse(run("isStaleTask({taskId: 'x', running: 1, isBackground: true}, () => true)"))

    def test_agent_closes_after_two_missed_reconciles_not_before(self) -> None:
        agents = "new Set(['a'])"
        live = "new Map([['a', 0]])"
        first = verdict(f"reconcileTasks({live}, new Map(), {agents}, {{agents: []}}, 100000)")
        self.assertEqual(first["close"], [])
        self.assertEqual(first["misses"], [["a", 1]])
        second = verdict(f"reconcileTasks({live}, new Map([['a', 1]]), {agents}, {{agents: []}}, 130000)")
        self.assertEqual(second["close"], ["a"])

    def test_running_row_resets_the_misses(self) -> None:
        got = verdict("reconcileTasks(new Map([['a', 0]]), new Map([['a', 1]]), new Set(['a']), {agents: [{id: 'a', status: 'running'}]}, 100000)")
        self.assertEqual(got["close"], [])
        self.assertEqual(got["misses"], [["a", 0]])

    def test_ended_status_closes_at_once_even_inside_the_grace(self) -> None:
        for status in ("completed", "Failed", "killed"):
            got = verdict(f"reconcileTasks(new Map([['a', 99000]]), new Map(), new Set(['a']), {{agents: [{{id: 'a', status: '{status}'}}]}}, 100000)")
            self.assertEqual(got["close"], ["a"], status)

    def test_fresh_work_is_not_judged_inside_the_grace(self) -> None:
        got = verdict("reconcileTasks(new Map([['a', 90000]]), new Map(), new Set(['a']), {agents: []}, 100000)")  # 10 s old
        self.assertEqual(got["close"], [])
        self.assertEqual(got["misses"], [["a", 0]])

    def test_shell_truth_is_the_stop_list_and_only_when_newer_than_the_start(self) -> None:
        live = "new Map([['b', 50000]])"
        stale = verdict(f"reconcileTasks({live}, new Map([['b', 1]]), new Set(), {{stop: {{at: 40000, rows: []}}}}, 100000)")
        self.assertEqual(stale["close"], [])  # the Stop was before the task started: it says nothing
        self.assertEqual(stale["misses"], [["b", 1]])  # neither a miss nor a reset
        none = verdict(f"reconcileTasks({live}, new Map([['b', 1]]), new Set(), {{}}, 100000)")
        self.assertEqual(none["close"], [])  # no Stop yet
        fresh = verdict(f"reconcileTasks({live}, new Map([['b', 1]]), new Set(), {{stop: {{at: 70000, rows: []}}}}, 100000)")
        self.assertEqual(fresh["close"], ["b"])  # second miss
        listed = verdict(f"reconcileTasks({live}, new Map([['b', 1]]), new Set(), {{stop: {{at: 70000, rows: [{{id: 'b'}}]}}}}, 100000)")
        self.assertEqual(listed["close"], [])  # listed without a status: still in flight

    def test_unreadable_agent_list_closes_nothing(self) -> None:
        got = verdict("reconcileTasks(new Map([['a', 0]]), new Map([['a', 5]]), new Set(['a']), {}, 100000)")
        self.assertEqual(got["close"], [])

    def test_notification_row_ends_the_task_it_names(self) -> None:
        row = "{origin: {kind: 'task-notification'}, task: {id: 'bu0y', status: 'failed'}}"
        self.assertEqual(run(f"endedTaskOfRow({row})"), {"id": "bu0y", "status": "failed"})
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'user'}, task: {id: 'b', status: 'failed'}})"))
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'task-notification'}, task: {id: 'b'}})"))
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'task-notification'}, task: {id: 'b', status: 'running'}})"))
        self.assertIsNone(run("endedTaskOfRow(undefined)"))


if __name__ == "__main__":
    unittest.main()
