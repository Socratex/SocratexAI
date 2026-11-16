"""Active grant amendments preserve progress and reject unsafe lifecycle changes."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from automation.auto import main
from automation.controller import Registry

class AmendTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.repo = self.root / "project"
        self.repo.mkdir()
        (self.repo / "PLAN.json").write_text('{"tasks": ["A", "B", "C"]}', encoding="utf-8")
        self.registry = Registry(self.root / "state")
        self.entry = self.registry.start("thread-A", str(self.repo), "migration", ["PLAN.json"], 3)
        self.run = self.entry["run_id"]

    def finalize(self, **changes):
        report = {"receipt_id": "receipt-1", "checkpoint": "checked code", "decision": "continue", "needs": []}
        report.update(changes)
        return self.registry.finalize("thread-A", self.run, report, str(self.repo))

    def test_amend_preserves_completed_receipts_needs_and_recovery_without_dispatch(self):
        with self.registry.transaction() as data:
            entry = data["threads"]["thread-A"]
            entry["batch_size"] = 9
        for index in range(4):
            self.finalize(receipt_id=f"receipt-{index}", wake_id=f"wake-{index}")
        with self.registry.transaction() as data:
            entry = data["threads"]["thread-A"]
            entry["pending_needs"] = [{"id": "map", "needed": "test", "how": "manual", "blocks": "none"}]
            entry["task_projection"] = [{"id": "stale"}]
        before = self.registry.get("thread-A")
        result = self.registry.amend("thread-A", self.run, "approved expanded queue", 13, "Owner approved four stages", "exact queue")
        self.assertFalse(result["dispatch"])
        after = Registry(self.registry.home).get("thread-A")
        for key in ("run_id", "completed", "completed_steps", "receipts", "processed_wakes", "pending_needs",
                    "checkpoint", "state", "enabled", "repo", "sources", "mode", "wake_transport", "scheduler_id", "recovery"):
            self.assertEqual(before[key], after[key], key)
        self.assertEqual(4, after["completed"])
        self.assertEqual(13, after["batch_size"])
        self.assertNotIn("task_projection", after)
        self.assertEqual(1, len(after["grant_amendments"]))
        self.assertEqual("grant_unchanged", self.registry.amend("thread-A", self.run, "approved expanded queue", 13,
                                                              "Owner approved four stages", "exact queue")["action"])
        self.assertEqual(1, len(self.registry.get("thread-A")["grant_amendments"]))
        from automation.files import paths
        files = paths(self.registry.home, "thread-A", self.run)
        for key in ("thread", "progress"):
            self.assertEqual(after["grant_amendments"], json.loads(Path(files[key]).read_text(encoding="utf-8"))["grant_amendments"])

    def test_amend_rejects_stale_terminal_reserved_or_unapproved_changes_atomically(self):
        for overrides, run_id, limit, note in (
            ({}, "wrong-run", 13, "approved"),
            ({"enabled": False}, self.run, 13, "approved"),
            ({"state": "needs_input"}, self.run, 13, "approved"),
            ({"state": "batch_complete"}, self.run, 13, "approved"),
            ({"inflight": {"task_id": "A", "wake_id": "active"}}, self.run, 13, "approved"),
            ({}, self.run, 2, "approved"),
            ({}, self.run, 13, "  "),
            ({}, self.run, True, "approved"),
            ({}, self.run, 101, "approved"),
        ):
            with self.subTest(overrides=overrides, run_id=run_id, limit=limit, note=note):
                with self.registry.transaction() as data:
                    entry = data["threads"]["thread-A"]
                    entry.update(enabled=True, state="registered", inflight=None)
                    entry.update(overrides)
                original = self.registry.path.read_bytes()
                with self.assertRaises(ValueError):
                    self.registry.amend("thread-A", run_id, "expanded", limit, note)
                self.assertEqual(original, self.registry.path.read_bytes())

    def test_amend_cli_requires_exact_run_and_approval(self):
        self.assertEqual(0, main(["--state-dir", str(self.registry.home), "amend", "--thread-id", "thread-A",
                                 "--run-id", self.run, "--scope", "expanded", "--batch-size", "13",
                                 "--approval-note", "Owner approved extension"]))
        self.assertEqual(self.run, self.registry.get("thread-A")["run_id"])
