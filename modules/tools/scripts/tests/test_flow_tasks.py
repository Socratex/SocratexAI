"""Tests of the flow-panel background-task parsing (runs the real <tasks> block with Node 22+)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from flow_js import run_blocks  # noqa: E402


def run(expr: str) -> object:
    return run_blocks(expr, "tasks")


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

    def test_agent_done_by_list_status_or_when_dropped(self) -> None:
        for status in ("completed", "failed", "killed"):
            self.assertTrue(run(f"isAgentDone('{status}', 0)"), status)
        for status in ("pending", "running", "waiting", "idle"):
            self.assertFalse(run(f"isAgentDone('{status}', 999999)"), status)
        self.assertFalse(run("isAgentDone(undefined, 5000)"))  # not listed yet: grace
        self.assertTrue(run("isAgentDone(undefined, 20000)"))  # dropped by the engine

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

    def test_task_gone_by_stop_list(self) -> None:
        self.assertTrue(run("isTaskGone({id: 'a', status: 'completed'}, 0)"))
        self.assertTrue(run("isTaskGone({id: 'a', status: 'Killed'}, 0)"))
        self.assertFalse(run("isTaskGone({id: 'a', status: 'running'}, 999999)"))
        self.assertFalse(run("isTaskGone({id: 'a'}, 999999)"))  # listed without a status: still in flight
        self.assertFalse(run("isTaskGone(undefined, 5000)"))  # not listed yet: grace
        self.assertTrue(run("isTaskGone(undefined, 20000)"))  # dropped from the list

    def test_gone_tasks_from_a_list(self) -> None:
        live = "new Map([['a', 0], ['b', 0], ['c', 95000], ['d', 0]])"
        rows = "[{id: 'a', status: 'running'}, {id: 'd', status: 'failed'}]"
        self.assertEqual(run(f"goneTasks({live}, {rows}, 100000)"), ["b", "d"])  # c is inside its grace
        self.assertEqual(run(f"goneTasks({live}, [], 100000)"), ["a", "b", "d"])  # nothing in flight
        self.assertEqual(run(f"goneTasks({live}, undefined, 100000)"), [])  # no list: close nothing


    def test_notification_row_ends_the_task_it_names(self) -> None:
        row = "{origin: {kind: 'task-notification'}, task: {id: 'bu0y', status: 'failed'}}"
        self.assertEqual(run(f"endedTaskOfRow({row})"), {"id": "bu0y", "status": "failed"})
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'user'}, task: {id: 'b', status: 'failed'}})"))
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'task-notification'}, task: {id: 'b'}})"))
        self.assertIsNone(run("endedTaskOfRow({origin: {kind: 'task-notification'}, task: {id: 'b', status: 'running'}})"))
        self.assertIsNone(run("endedTaskOfRow(undefined)"))


if __name__ == "__main__":
    unittest.main()
