"""No test may execute an OS power command or arm the real registry."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import importlib

from tools.automation.controller import Registry
from tools.automation import shutdown
from tools.automation.files import paths
from tools.automation.native import render_instructions
from tools.automation.recovery import eligibility


class ShutdownTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="auto-power-żółć ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "PLAN.json").write_text("{}")
        self.registry = Registry(self.root / "registry")
        self.entry = self.registry.start("A", str(self.root), "approved", ["PLAN.json"], 2, "native")
        self.run = self.entry["run_id"]
        self.executor = Mock()
        self.original_system_shutdown = shutdown.system_shutdown
        boot = patch.object(shutdown, "boot_marker", return_value=500)
        boot.start(); self.addCleanup(boot.stop)
        forbidden = patch.object(shutdown, "system_shutdown", side_effect=AssertionError("Real power command forbidden in tests"))
        forbidden.start(); self.addCleanup(forbidden.stop)

    def arm(self):
        return shutdown.configure(self.registry, "A", self.run, enabled=True, approval_note="continue auto + limit shut down", now=1000, boot=500)

    def change(self, **values):
        with self.registry.transaction() as data:
            data["threads"]["A"].update(values)

    def observe(self, now=1000, limited=False, **values):
        result = {"thread_id": "A", "repo": str(self.root), "observed_at": now, "status": "idle",
            "authoritative": True, "project_activity_complete": True, "active_project_threads": [],
            "active_host_threads": [], "source": "native_desktop_tools",
            "limits": {"rateLimits": {"primary": {"usedPercent": 100 if limited else 10, "resetsAt": 5000}}}}
        result.update(values)
        return result

    def advance(self, now=1000, **values):
        return shutdown.advance(self.registry, "A", self.run, self.observe(now, **values), executor=self.executor, now=now, boot=500)

    def test_default_status_and_unarmed_completed_run_never_dispatch(self):
        self.assertEqual("continue", self.advance()["action"])
        self.change(state="batch_complete", enabled=False)
        self.assertEqual("continue", self.advance()["action"])
        self.executor.assert_not_called()

    def test_explicit_native_grant_and_exact_run_are_required(self):
        with self.assertRaises(ValueError):
            shutdown.configure(self.registry, "A", self.run, enabled=True)
        with self.assertRaises(ValueError):
            shutdown.configure(self.registry, "A", "foreign", enabled=True, approval_note="yes")
        self.change(mode="pilot")
        with self.assertRaises(ValueError):
            self.arm()

    def test_arming_does_not_modify_the_grant_or_start_work(self):
        before = self.registry.get("A")
        result = self.arm()
        after = self.registry.get("A")
        self.assertFalse(result["dispatch"])
        for key in ("scope", "sources", "run_id", "completed", "batch_size", "state", "inflight"):
            self.assertEqual(before[key], after[key])
        self.assertIn("Nie zadawaj pytań", render_instructions(after))
        self.assertFalse(after["shutdown_policy"]["wait_for_build"])

    def test_fresh_limit_counts_down_then_saves_before_one_os_dispatch(self):
        self.arm()
        self.change(inflight={"task_id": "unfinished"}, checkpoint="last verified")
        self.assertEqual("shutdown_pending", self.advance(limited=True)["action"])
        self.assertEqual("shutdown_pending", eligibility(self.registry.get("A"), 1001))
        self.assertEqual("shutdown_pending", self.advance(now=1029, limited=True)["action"])
        self.executor.assert_not_called()

        def verify_saved():
            entry = json.loads(self.registry.path.read_text(encoding="utf-8"))["threads"]["A"]
            self.assertFalse(entry["shutdown_policy"]["armed"])
            self.assertEqual("dispatch_reserved", entry["shutdown_policy"]["phase"])
            self.assertEqual("unfinished", entry["shutdown_policy"]["checkpoint"]["inflight"]["task_id"])
            record = json.loads(Path(paths(self.registry.home, "A", self.run)["progress"]).read_text(encoding="utf-8"))
            self.assertEqual("last verified", record["shutdown_policy"]["checkpoint"]["last_verified"])
        self.executor.side_effect = verify_saved
        self.assertEqual("shutdown_requested", self.advance(now=1031, limited=True)["action"])
        self.advance(now=1032, limited=True)
        self.executor.assert_called_once()
        self.assertEqual(0, self.registry.get("A")["completed"])
        self.assertEqual("shutdown_finished", eligibility(self.registry.get("A"), 1032))

    def test_batch_queue_and_operator_block_are_shutdown_conditions(self):
        for state in ("batch_complete", "queue_complete", "needs_input"):
            self.change(enabled=True, state="registered")
            self.arm()
            self.change(state=state, enabled=False)
            result = self.advance()
            self.assertEqual("shutdown_pending", result["action"])
            self.assertEqual("work_blocked" if state == "needs_input" else "work_complete", result["trigger"])
        self.executor.assert_not_called()

    def test_failed_quality_check_can_record_a_block_without_fake_finalization(self):
        self.arm()
        self.change(inflight={"task_id": "broken"}, checkpoint="verified before failure")
        shutdown.block(self.registry, "A", self.run, "Required check failed")
        result = self.advance()
        self.assertEqual("work_blocked", result["trigger"])
        entry = self.registry.get("A")
        self.assertEqual(0, entry["completed"])
        self.assertEqual([], entry["receipts"])
        self.assertEqual("broken", entry["inflight"]["task_id"])

    def test_stop_and_explicit_cancel_remove_pending_power_action(self):
        self.arm(); self.advance(limited=True)
        shutdown.configure(self.registry, "A", self.run, enabled=False)
        self.advance(now=1100, limited=True)
        self.executor.assert_not_called()
        self.arm(); self.advance(limited=True)
        self.registry.stop("A")
        self.advance(now=1100, limited=True)
        self.executor.assert_not_called()

    def test_new_grant_and_new_boot_do_not_inherit_authorization(self):
        self.arm()
        result = shutdown.advance(self.registry, "A", self.run, self.observe(), executor=self.executor, now=1000, boot=800)
        self.assertEqual("shutdown_cancelled", result["action"])
        self.registry.stop("A")
        fresh = self.registry.start("A", str(self.root), "approved", ["PLAN.json"], 2, "native")
        self.assertNotIn("shutdown_policy", fresh)
        self.assertNotEqual(self.run, fresh["run_id"])

    def test_stale_foreign_and_private_observations_cannot_turn_off_a_computer(self):
        self.arm()
        for values in ({"observed_at": 0}, {"source": "private_app_server"}, {"thread_id": "foreign"}):
            with self.subTest(values=values), self.assertRaises(ValueError):
                shutdown.advance(self.registry, "A", self.run, self.observe(limited=True, **values), executor=self.executor, now=1000, boot=500)
        self.executor.assert_not_called()

    def test_active_current_project_and_other_visible_chat_defer_shutdown(self):
        self.arm()
        for values in ({"status": "active"}, {"active_project_threads": ["B"]}, {"active_host_threads": ["X"]}):
            self.assertEqual("shutdown_deferred", self.advance(limited=True, **values)["action"])
        self.executor.assert_not_called()

    def test_dry_run_never_arms_a_countdown_or_invokes_power(self):
        self.arm()
        result = shutdown.advance(self.registry, "A", self.run, self.observe(limited=True), executor=self.executor, now=1000, boot=500, dry_run=True)
        self.assertEqual("would_shutdown", result["action"])
        self.assertEqual("armed", self.registry.get("A")["shutdown_policy"]["phase"])
        self.executor.assert_not_called()

    def test_native_system_error_is_a_saved_block_without_questions(self):
        self.arm()
        result = self.advance(status="systemError")
        self.assertEqual("work_blocked", result["trigger"])

    def test_execution_failure_is_recorded_and_never_automatically_retried(self):
        self.arm(); self.advance(limited=True)
        self.executor.side_effect = OSError("permission denied")
        self.assertEqual("shutdown_failed", self.advance(now=1031, limited=True)["action"])
        self.advance(now=1032, limited=True)
        self.executor.assert_called_once()
        self.assertEqual("failed", self.registry.get("A")["shutdown_policy"]["phase"])

    def test_watchdog_handles_terminal_and_limited_runs_before_recovery_dispatch(self):
        from tools.automation import resume_auto
        power = importlib.import_module("automation.shutdown")
        fixture = self
        class Bridge:
            def __init__(self, *args): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def observation(self, entry): return fixture.observe(limited=True)
            def send(self, *args): raise AssertionError("Must not send a prompt while powering down")
        self.arm()
        with patch.object(resume_auto, "DesktopBridge", Bridge), patch.object(resume_auto, "find_endpoint", return_value="test"), \
                patch.object(power, "boot_marker", return_value=500), patch.object(power, "system_shutdown", self.executor), \
                patch.object(power.time, "time", return_value=1000):
            result = resume_auto.check_registered(self.registry, caller=None, endpoint=None, timeout=1,
                                                  dry_run=False, repo=None, thread_id="A")
        self.assertEqual("shutdown_pending", result[0]["action"])
        with patch.object(resume_auto, "DesktopBridge", Bridge), patch.object(resume_auto, "find_endpoint", return_value="test"), \
                patch.object(power, "boot_marker", return_value=500), patch.object(power, "system_shutdown", self.executor), \
                patch.object(power.time, "time", return_value=1031):
            result = resume_auto.check_registered(self.registry, caller=None, endpoint=None, timeout=1,
                                                  dry_run=False, repo=None, thread_id="A")
        self.assertEqual("shutdown_requested", result[0]["action"])
        self.executor.assert_called_once()

    def test_cli_arm_ensures_a_monitor_and_failed_monitor_start_disarms(self):
        from tools.automation.auto import main
        arguments = ["--state-dir", str(self.registry.home), "shutdown-policy", "--thread-id", "A",
                     "--run-id", self.run, "--enable", "--approval-note", "explicit night mode"]
        with patch("automation.console_scheduler.ensure_scheduler", return_value={"action": "started"}) as start:
            self.assertEqual(0, main(arguments))
        start.assert_called_once()
        with patch("automation.console_scheduler.ensure_scheduler", side_effect=OSError("cannot start monitor")):
            self.assertEqual(2, main(arguments))
        self.assertFalse(self.registry.get("A")["shutdown_policy"]["armed"])

    @unittest.skipUnless(os.name == "nt", "Windows command boundary")
    def test_windows_command_uses_own_countdown_and_never_forces_applications(self):
        with patch.object(shutdown.subprocess, "run") as run:
            self.original_system_shutdown()
        command = run.call_args.args[0]
        self.assertEqual(["/s", "/t", "0"], command[1:4])
        self.assertNotIn("/f", command)
        self.executor.assert_not_called()


if __name__ == "__main__":
    unittest.main()
