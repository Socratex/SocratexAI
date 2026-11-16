"""Native wake execution, project reservations and recovery invariants."""

import hashlib
import json
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path

from tools.automation.controller import Registry
from tools.automation.native import authorize, control_handoff, render_instructions, scheduler_request, snapshot
from tools.automation.auto import main
from tools.automation.roster import complete_inventory, read_roster
from tools.automation.finalizer import handoff_result
from tools.text.utf8_file_helpers import write_utf8_file


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_utf8_file(self.root / "PLAN.json", "{}")
        self.registry = Registry(self.root / "state")
        self.entry = self.registry.start("A", str(self.root), "migration", ["PLAN.json"], 3, "native")
        self.run = self.entry["run_id"]
        self.registry.attach_scheduler("A", self.run, "schedule-A")

    def observe(self, others=(), **changes):
        value = {"thread_id": "A", "repo": str(self.root), "observed_at": 1000, "status": "active",
                 "authoritative": True, "project_activity_complete": True, "source": "native_desktop_tools",
                 "active_project_threads": ["A", *others], "limits": {"rateLimits": {"primary": {"usedPercent": 10}}}}
        value.update(changes)
        return value

    def tasks(self):
        return [{"id": "issue-1", "source": "PLAN.json", "source_sha256": hashlib.sha256((self.root / "PLAN.json").read_bytes()).hexdigest(),
                 "scope": "migration", "approved": True, "status": "todo", "depends_on": [], "independent_of": []}]

    def claim(self, wake="wake-1", **changes):
        return authorize(self.registry, "A", self.run, "schedule-A", wake, self.observe(**changes), self.tasks(), 1000)

    def report(self, **changes):
        value = {"receipt_id": "r1", "wake_id": "wake-1", "decision": "continue", "checkpoint": "verified"}
        value.update(changes)
        return self.registry.finalize("A", self.run, value, str(self.root))

    def test_claim_authorizes_real_work_and_reserves_project(self):
        result = self.claim()
        self.assertEqual("execute", result["action"])
        self.assertEqual("issue-1", result["task_id"])
        self.assertEqual("CONTINUE-AUTO", result["command"])
        self.assertEqual("executing", self.registry.get("A")["state"])

    def test_validated_task_list_is_saved_in_the_thread_folder(self):
        self.claim()
        context = self.registry.context("A")
        queue = json.loads(Path(context["files"]["tasks"]).read_text(encoding="utf-8"))
        self.assertEqual(self.run, queue["run_id"])
        self.assertEqual(self.tasks(), queue["tasks"])

    def test_blocked_projection_is_saved_without_authorizing_work(self):
        tasks = self.tasks()
        tasks[0]["status"] = "test"
        result = authorize(self.registry, "A", self.run, "schedule-A", "wake", self.observe(), tasks, 1000)
        self.assertEqual("stop", result["action"])
        self.assertEqual("queue_complete", result["reason"])
        self.assertEqual(tasks, self.registry.get("A")["task_projection"])

    def test_consuming_wake_pauses_scheduler_without_stopping_grant(self):
        result = scheduler_request(self.registry.get("A"), pause=True)
        self.assertEqual("PAUSED", result["status"])
        self.assertTrue(self.registry.get("A")["enabled"])

    def test_each_completed_step_returns_progress_and_next_wake(self):
        self.claim()
        result = handoff_result(self.registry, "A", self.run, self.report())
        self.assertIn("1/3", result["summary_markdown"])
        self.assertEqual("ACTIVE", result["scheduler_request"]["status"])
        self.assertEqual("CONTINUE-AUTO", result["scheduler_request"]["prompt"])
        self.assertEqual("A", result["scheduler_request"]["targetThreadId"])

    def test_terminal_handoff_pauses_instead_of_chaining(self):
        needs = [{"id": "F3", "needed": "test", "how": "walk", "blocks": "camera"}]
        result = handoff_result(self.registry, "A", self.run, self.report(decision="needs_input", needs=needs))
        self.assertEqual("PAUSED", result["scheduler_request"]["status"])
        self.assertIn("F3", result["summary_markdown"])

    def test_manual_auto_chains_in_current_turn_until_batch_limit_without_external_wake(self):
        self.registry.use_manual_transport("A", self.run)
        for index in range(3):
            wake = f"turn:auto:{index}"
            result = authorize(self.registry, "A", self.run, None, wake, self.observe(), self.tasks(), 1000)
            self.assertEqual("execute", result["action"])
            self.assertEqual("duplicate_wake", authorize(self.registry, "A", self.run, None, wake,
                                                        self.observe(), self.tasks(), 1000)["reason"])
            result = handoff_result(self.registry, "A", self.run, self.report(receipt_id=f"receipt-{index}", wake_id=wake))
            self.assertNotIn("scheduler_request", result)
            if index < 2:
                self.assertEqual("continue_current_turn", result["continuation"]["action"])
                self.assertEqual(f":auto:{index + 1}", result["continuation"]["wake_id_suffix"])
            else:
                self.assertNotIn("continuation", result)
                self.assertEqual("batch_complete", result["state"])

    def test_manual_continuation_still_requires_fresh_project_and_limit_gates(self):
        self.registry.use_manual_transport("A", self.run)
        authorize(self.registry, "A", self.run, None, "turn:auto:0", self.observe(), self.tasks(), 1000)
        self.report(wake_id="turn:auto:0")
        result = authorize(self.registry, "A", self.run, None, "turn:auto:1", self.observe(others=["B"]), self.tasks(), 1000)
        self.assertEqual("project_busy", result["reason"])
        limits = {"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 2000}}}
        result = authorize(self.registry, "A", self.run, None, "turn:auto:1", self.observe(limits=limits), self.tasks(), 1000)
        self.assertEqual("account_limit", result["reason"])
        self.registry.stop("A")
        self.assertEqual("stop", authorize(self.registry, "A", self.run, None, "turn:auto:1",
                                           self.observe(), self.tasks(), 3000)["action"])

    def test_completed_batch_handoff_does_not_schedule_fourth_unit(self):
        result = None
        for index in range(3):
            self.claim(f"wake-{index}")
            result = self.report(receipt_id=f"r{index}", wake_id=f"wake-{index}")
        result = handoff_result(self.registry, "A", self.run, result)
        self.assertEqual("PAUSED", result["scheduler_request"]["status"])
        self.assertIn("3/3", result["summary_markdown"])

    def test_old_finalizer_cannot_rearm_a_newer_start(self):
        self.registry.stop("A")
        self.registry.start("A", str(self.root), "migration", ["PLAN.json"], 3, "native")
        with self.assertRaises(ValueError):
            handoff_result(self.registry, "A", self.run, {})

    def test_duplicate_finalizer_never_rearms_while_next_unit_executes(self):
        self.claim()
        self.report()
        self.claim("wake-2")
        result = handoff_result(self.registry, "A", self.run, self.report())
        self.assertNotIn("scheduler_request", result)

    def test_duplicate_wake_and_unfinished_work_cannot_start_second_task(self):
        self.claim()
        self.assertEqual("duplicate_wake", self.claim()["reason"])
        self.assertEqual("reconcile", self.claim("wake-2")["action"])

    def test_other_active_thread_blocks_native_work(self):
        self.assertEqual("project_busy", self.claim(active_project_threads=["A", "B"])["reason"])

    def test_read_only_controller_handoff_is_bounded_and_specific(self):
        control_handoff(self.registry, "A", self.run, "control", 900)
        self.assertEqual("execute", self.claim(active_project_threads=["A", "control"])["action"])

    def test_expired_control_handoff_never_ignores_active_writer(self):
        control_handoff(self.registry, "A", self.run, "control", 800)
        self.assertEqual("project_busy", self.claim(active_project_threads=["A", "control"])["reason"])

    def test_self_handoff_cannot_bypass_worker_activity(self):
        with self.assertRaises(ValueError):
            control_handoff(self.registry, "A", self.run, "A", 1000)

    def test_sibling_reservation_blocks_even_if_native_inventory_says_idle(self):
        other = self.registry.start("B", str(self.root), "other", ["PLAN.json"], 3, "native")
        with self.registry.transaction() as data:
            data["threads"]["B"]["inflight"] = {"wake_id": "other", "task_id": "other", "started_at": 1}
        self.assertEqual("project_reserved", self.claim()["reason"])

    def test_stop_during_work_prevents_restart_until_matching_finalization(self):
        self.claim()
        self.registry.stop("A")
        with self.assertRaises(ValueError):
            self.registry.start("A", str(self.root), "migration", ["PLAN.json"], 3, "native")
        self.assertEqual("ignored", self.report()["action"])
        entry = self.registry.start("A", str(self.root), "migration", ["PLAN.json"], 3, "native")
        self.assertNotEqual(self.run, entry["run_id"])

    def test_foreign_scheduler_cannot_execute(self):
        with self.assertRaises(ValueError):
            authorize(self.registry, "A", self.run, "other", "w", self.observe(), self.tasks(), 1000)

    def test_pilot_or_private_observer_cannot_execute(self):
        for changes in ({"source": "private_app_server_read_only"}, {"authoritative": False}, {"status": "idle"}):
            with self.assertRaises(ValueError):
                self.claim(**changes)
        entry = self.registry.start("pilot", str(self.root), "scope", ["PLAN.json"])
        with self.assertRaises(ValueError):
            authorize(self.registry, "pilot", entry["run_id"], "s", "w", {}, [], 1000)

    def test_without_selected_approved_task_there_is_no_work_reservation(self):
        result = authorize(self.registry, "A", self.run, "schedule-A", "w", self.observe(), [], 1000)
        self.assertEqual("stop", result["action"])
        self.assertEqual("queue_complete", result["reason"])
        self.assertIsNone(self.registry.get("A")["inflight"])

    def test_unassessed_prompt_mismatch_cannot_terminate_an_executable_queue(self):
        with self.registry.transaction() as data:
            data["threads"]["A"]["prompt_context"] = "approved movement A2 through A13"
        result = self.claim()
        self.assertEqual("assess_context", result["action"])
        entry = self.registry.get("A")
        self.assertTrue(entry["enabled"])
        self.assertEqual(0, entry["completed"])
        self.assertIsNone(entry["inflight"])
        self.assertNotIn("wake-1", entry["processed_wakes"])
        tasks = self.tasks()
        tasks[0]["context_assessment"] = {"context": entry["prompt_context"], "matches": True,
                                          "reason": "Approved movement unit."}
        result = authorize(self.registry, "A", self.run, "schedule-A", "wake-1", self.observe(), tasks, 1000)
        self.assertEqual("execute", result["action"])

    def test_explicit_nonmatching_assessment_can_complete_the_context_queue(self):
        context = "approved movement A2 through A13"
        with self.registry.transaction() as data:
            data["threads"]["A"]["prompt_context"] = context
        tasks = self.tasks()
        tasks[0]["context_assessment"] = {"context": context, "matches": False, "reason": "Different approved topic."}
        result = authorize(self.registry, "A", self.run, "schedule-A", "wake-1", self.observe(), tasks, 1000)
        self.assertEqual("queue_complete", result["reason"])

    def test_finalization_releases_reservation_and_pending_retests_do_not_block_independent_work(self):
        self.claim()
        needs = [{"id": "F3", "needed": "test", "how": "walk", "blocks": "camera"}]
        self.report(pending_needs=needs)
        entry = self.registry.get("A")
        self.assertIsNone(entry["inflight"])
        self.assertTrue(entry["enabled"])
        self.assertEqual(needs, entry["pending_needs"])
        self.assertEqual("execute", self.claim("wake-2")["action"])

    def test_native_receipt_without_reservation_or_with_wrong_wake_rejected(self):
        with self.assertRaises(ValueError):
            self.report()
        self.claim()
        with self.assertRaises(ValueError):
            self.report(wake_id="wrong")
        self.assertIsNotNone(self.registry.get("A")["inflight"])

    def test_same_receipt_is_idempotent_after_native_lease_released(self):
        self.claim()
        self.report()
        self.assertEqual("duplicate_receipt", self.report()["reason"])
        self.assertEqual(1, self.registry.get("A")["completed"])

    def test_limit_recovery_preserves_task_and_invalidates_old_wake_receipt(self):
        self.claim()
        limits = {"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 1200}}}
        result = self.claim("recovery", interrupted_by_limit=True, limits=limits)
        self.assertEqual(1260, result["next_check_at"])
        observation = self.observe(observed_at=1260)
        result = authorize(self.registry, "A", self.run, "schedule-A", "recovery", observation, [], 1260)
        self.assertEqual("LIMIT", result["command"])
        self.assertEqual("issue-1", result["task_id"])
        with self.assertRaises(ValueError):
            self.report()
        self.report(wake_id="recovery")
        self.assertFalse(self.registry.get("A")["resume_pending"])

    def test_terminal_operator_block_does_not_count_an_unstarted_task(self):
        needs = [{"id": "F3", "needed": "test", "how": "walk", "blocks": "camera"}]
        result = self.report(decision="needs_input", needs=needs)
        self.assertEqual("needs_input", result["action"])
        self.assertEqual(0, self.registry.get("A")["completed"])
        self.assertEqual("stop", self.claim()["action"])

    def test_native_snapshot_rejects_incomplete_inventory(self):
        threads = {"threads": [{"id": "A", "kind": "codex", "cwd": str(self.root), "status": "active"}],
                   "pinnedThreads": [], "unavailableHosts": [], "unavailableSources": []}
        result = snapshot(self.entry, threads, self.observe()["limits"], 1000)
        self.assertEqual(["A"], result["active_project_threads"])
        with self.assertRaises(ValueError):
            snapshot(self.entry, threads, {}, 1000, list_limit=1)
        threads["unavailableHosts"] = ["local"]
        with self.assertRaises(ValueError):
            snapshot(self.entry, threads, {}, 1000)

    def test_scheduler_request_targets_exact_thread_and_defers_until_after_reset(self):
        entry = self.registry.get("A")
        request = scheduler_request(entry)
        self.assertEqual("A", request["targetThreadId"])
        self.assertEqual("update", request["mode"])
        self.assertEqual("schedule-A", request["id"])
        self.assertEqual("CONTINUE-AUTO", request["prompt"])
        self.assertIn(self.run, render_instructions(entry))
        self.assertIn("native-begin", render_instructions(entry))
        self.assertIn("INTERVAL=5", scheduler_request(entry, 1260, 1000)["rrule"])

    def test_actual_native_snapshot_cli_writes_observation(self):
        threads = {"threads": [{"id": "A", "kind": "codex", "cwd": str(self.root), "status": "active"}]}
        for name, value in (("threads", threads), ("limits", self.observe()["limits"])):
            write_utf8_file(self.root / f"{name}.json", json.dumps(value))
        output = self.root / "observed.json"
        code = main(["--state-dir", str(self.registry.home), "native-snapshot", "--thread-id", "A",
                     "--threads-file", str(self.root / "threads.json"), "--limits-file", str(self.root / "limits.json"),
                     "--observed-at", "1000", "--output", str(output)])
        self.assertEqual(0, code)
        self.assertEqual("active", json.loads(output.read_text(encoding="utf-8"))["status"])

    def test_complete_roster_requires_native_status_for_every_identity(self):
        roster = {"repo": self.entry["repo"], "observed_at": 1000, "threads": [{"id": "A"}, {"id": "old-active"}]}
        results = [{"observed_at": 1000, "polls": [{"thread": {"id": "A", "status": {"type": "active"}}}]}]
        recent = {"threads": [{"id": "A", "kind": "codex", "cwd": str(self.root), "status": "active"}]}
        with self.assertRaises(ValueError):
            complete_inventory(self.entry, roster, results, recent, 1000)
        results[0]["polls"].append({"thread": {"id": "old-active", "status": {"type": "active"}}})
        full = complete_inventory(self.entry, roster, results, recent, 1000)
        observed = snapshot(self.entry, full, self.observe()["limits"], 1000, list_limit=1)
        self.assertIn("old-active", observed["active_project_threads"])

    def test_local_index_supplies_identities_only_and_excludes_other_projects_and_archives(self):
        database = self.root / "state.sqlite"
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE threads (id TEXT, cwd TEXT, archived INTEGER)")
            connection.executemany("INSERT INTO threads VALUES (?,?,?)", [("A", str(self.root), 0),
                                    ("archived", str(self.root), 1), ("foreign", str(self.root.parent), 0)])
        connection.close()
        result = read_roster(str(self.root), database)
        self.assertEqual(["A"], [item["id"] for item in result["threads"]])
        self.assertNotIn("status", result["threads"][0])

    @unittest.skipUnless(os.name == "nt", "Windows extended path syntax")
    def test_windows_extended_paths_match_normal_project_identity(self):
        from tools.automation.controller import project_path
        self.assertEqual(project_path(str(self.root)), project_path("\\\\?\\" + str(self.root)))


if __name__ == "__main__":
    unittest.main()
