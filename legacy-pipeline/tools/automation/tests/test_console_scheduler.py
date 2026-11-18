"""Console lifetime, duplicate protection and START AUTO orchestration."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.automation.auto import execute, parser
from tools.automation.console_scheduler import ensure_scheduler, scheduler_lock, serve, start_for_grant
from tools.automation.controller import Registry
from tools.text.utf8_file_helpers import write_utf8_file


class ConsoleStartupTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="auto żółć ")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.home = self.root / "state"
        self.launcher = self.root / "AUTO scheduler.bat"
        write_utf8_file(self.launcher, "@exit /b 37\n")

    def test_process_lock_rejects_duplicate_and_recovers_after_owner_death(self):
        code = ('import sys,time; from pathlib import Path; '
                'from tools.automation.console_scheduler import scheduler_lock; '
                'ctx=scheduler_lock(Path(sys.argv[1])); print(ctx.__enter__(),flush=True); time.sleep(30)')
        path = self.home / "console-scheduler.lock"
        child = subprocess.Popen([sys.executable, "-B", "-c", code, str(path)], stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual("True", child.stdout.readline().strip())
            with scheduler_lock(path) as available:
                self.assertFalse(available)
        finally:
            child.kill()
            child.wait(timeout=5)
            child.stdout.close()
        # Windows may finish releasing file locks shortly after process exit is signalled.
        deadline = time.monotonic() + 2
        while True:
            with scheduler_lock(path) as available:
                if available:
                    break
            self.assertLess(time.monotonic(), deadline, "Lock survived owner process death")
            time.sleep(0.01)

    @unittest.skipUnless(os.name == "nt", "Windows CMD")
    def test_serve_preserves_spaces_unicode_exit_code_and_releases_lock(self):
        self.assertEqual(37, serve(self.home, self.launcher, "test"))
        ready = json.loads((self.home / "scheduler-ready.json").read_text(encoding="utf-8"))
        self.assertEqual({"request": "test", "action": "started"}, ready)
        with scheduler_lock(self.home / "console-scheduler.lock") as available:
            self.assertTrue(available)

    @unittest.skipUnless(os.name == "nt", "Windows CMD")
    def test_duplicate_does_not_open_console(self):
        with scheduler_lock(self.home / "console-scheduler.lock"):
            with patch("tools.automation.console_scheduler.subprocess.Popen") as launch:
                self.assertEqual({"action": "already_running"}, ensure_scheduler(self.home, self.launcher))
                self.assertEqual(0, serve(self.home, self.launcher))
                launch.assert_not_called()

    def test_non_native_and_heartbeat_grants_never_open_console(self):
        with patch("tools.automation.console_scheduler.ensure_scheduler") as launch:
            for mode, transport in (("pilot", "manual"), ("native", "heartbeat")):
                self.assertEqual("not_applicable", start_for_grant(
                    {"mode": mode, "wake_transport": transport}, self.home, self.launcher)["action"])
            launch.assert_not_called()

    def test_start_registers_before_launch_and_retry_keeps_run(self):
        write_utf8_file(self.root / "PLAN.json", "{}\n")
        args = parser().parse_args(["--state-dir", str(self.home), "start", "--thread-id", "A", "--repo", str(self.root),
                                   "--scope", "approved", "--sources", "PLAN.json", "--mode", "native"])
        runs = []

        def launch(entry, home, launcher):
            registered = Registry(home).get("A")
            self.assertEqual(entry["run_id"], registered["run_id"])
            self.assertEqual(0, registered["completed"])
            runs.append(entry["run_id"])
            if len(runs) == 1:
                raise OSError("cannot open console")
            return {"action": "started"}

        with patch("automation.console_scheduler.start_for_grant", side_effect=launch):
            with self.assertRaises(OSError):
                execute(args)
            self.assertEqual("started", execute(args)["console_scheduler"]["action"])
        self.assertEqual(runs[0], runs[1])

    @unittest.skipUnless(os.name == "nt", "Windows console creation")
    def test_start_passes_exact_registry_and_waits_for_matching_ack(self):
        def spawn(command, **kwargs):
            self.assertEqual(str(self.home.resolve()), command[command.index("--state-dir") + 1])
            self.assertEqual(subprocess.CREATE_NEW_CONSOLE, kwargs["creationflags"])
            self.assertEqual(str(self.home.resolve()), kwargs["env"]["SOCRATEX_AUTO_HOME"])
            request = command[command.index("--request") + 1]
            write_utf8_file(self.home / "scheduler-ready.json", json.dumps({"request": request, "action": "started"}))

        with patch("tools.automation.console_scheduler.subprocess.Popen", side_effect=spawn):
            self.assertEqual({"action": "started"}, ensure_scheduler(self.home, self.launcher))


if __name__ == "__main__":
    unittest.main()
