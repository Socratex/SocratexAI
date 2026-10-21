"""Watchdog signal-only reporting and limit recovery, without live prompt delivery."""

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.automation.controller import Registry, limit_availability
from tools.automation.resume_auto import main, sweep
from tools.automation.watchdog_status import changes, print_changes
from tools.text.utf8_file_helpers import write_utf8_file


class WatchdogTests(unittest.TestCase):
    def test_repeated_limit_countdown_is_quiet_but_new_reset_and_resume_are_logged(self):
        row = {"thread_id": "A", "action": "skip", "reason": "account_limit", "limit_reset_at": 5000}
        report = {"observed_at": 1000, "results": [row]}
        lines, state = changes(report, {})
        self.assertIn("pozostalo 67 min", lines[0])
        self.assertIn("odnowienie", lines[0])
        self.assertEqual([], changes({**report, "observed_at": 1600}, state)[0])
        self.assertTrue(changes({**report, "results": [{**row, "limit_reset_at": 6000}]}, state)[0])
        sent = {"thread_id": "A", "action": "sent", "delivery_id": "one",
                "prompt": "CONTINUE-AUTO (limit reached previously, continue)"}
        self.assertIn("wyslano CONTINUE-AUTO (limit reached previously, continue)",
                      changes({**report, "results": [sent]}, state)[0][0])

    def test_terminal_noise_and_repeated_errors_are_suppressed_and_recovery_is_visible(self):
        report = {"observed_at": 1000, "results": [{"thread_id": "old", "action": "skip", "reason": "inactive"}]}
        self.assertEqual([], changes(report, {})[0])
        error = {**report, "results": [{"thread_id": "scheduler", "action": "blocked", "error": "app closed"}]}
        lines, state = changes(error, {})
        self.assertIn("BLAD: app closed", lines[0])
        self.assertEqual([], changes(error, state)[0])
        self.assertIn("ponownie dziala", changes(report, state)[0][0])
        with tempfile.TemporaryDirectory() as folder, redirect_stdout(StringIO()) as output:
            print_changes(Path(folder), error)
            first = output.getvalue()
            print_changes(Path(folder), error)
            self.assertEqual(first, output.getvalue())

    def test_account_denial_retains_known_reset_time(self):
        limits = {"ordinaryUsageAllowed": False, "rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 5000}}}
        self.assertEqual((False, 5060), limit_availability(limits, 1000))

    def test_after_clock_reset_fresh_denial_still_blocks_then_available_sends_annotation_once(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_utf8_file(root / "PLAN.json", "{}")
            registry = Registry(root / "state")
            registry.start("A", str(root), "test", ["PLAN.json"], 3, "native")
            sent = []
            limits = {"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 2000}}}

            class Bridge:
                def observation(self, entry):
                    return {"thread_id": "A", "repo": str(root), "observed_at": 4000, "status": "idle",
                            "authoritative": True, "project_activity_complete": True, "source": "native_desktop_tools",
                            "active_project_threads": [], "limits": limits}

                def send(self, thread, prompt):
                    sent.append((thread, prompt))
                    return {"threadId": thread}

            with patch("tools.automation.resume_auto.time.time", return_value=1000):
                self.assertEqual("account_limit", sweep(registry, Bridge(), account_limits=limits)[0]["reason"])
            self.assertEqual(1600, registry.get("A")["next_check_at"])
            self.assertEqual(2000, registry.get("A")["recovery"]["limit_wait"]["reset_at"])
            with patch("tools.automation.resume_auto.time.time", return_value=3000):
                self.assertEqual("account_limit", sweep(registry, Bridge(), account_limits=limits)[0]["reason"])
            self.assertEqual([], sent)
            limits["rateLimits"]["primary"]["usedPercent"] = 10
            with patch("tools.automation.resume_auto.time.time", return_value=4000):
                self.assertEqual("sent", sweep(registry, Bridge(), account_limits=limits)[0]["action"])
                self.assertEqual("delivery_pending", sweep(registry, Bridge(), account_limits=limits)[0]["reason"])
            self.assertEqual([("A", "CONTINUE-AUTO (limit reached previously, continue)")], sent)

    def test_watchdog_exit10_selects_limit_cadence_and_persists_quiet_state(self):
        import tools.automation.resume_auto as runner
        with tempfile.TemporaryDirectory() as folder:
            results = [{"thread_id": "A", "action": "skip", "reason": "account_limit", "limit_reset_at": 5000}]
            with patch.object(runner, "check_registered", return_value=results), redirect_stdout(StringIO()) as output:
                self.assertEqual(10, main(["--state-dir", folder, "--watchdog"]))
                first = output.getvalue()
                self.assertEqual(10, main(["--state-dir", folder, "--watchdog"]))
                self.assertEqual(first, output.getvalue())
            self.assertTrue(json.loads((Path(folder) / "watchdog-status.json").read_text())["A"])


if __name__ == "__main__":
    unittest.main()
