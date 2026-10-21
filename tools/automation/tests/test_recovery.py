"""Recovery safety: lifecycle, crash window, native authority and exact delivery."""

import json
import struct
import tempfile
import unittest
from pathlib import Path

from tools.automation.controller import Registry, limit_availability
from tools.automation.desktop_bridge import DesktopBridge
from tools.automation.native import authorize, scheduler_request
from tools.automation.recovery import record_delivery, recovery_record, reserve_wake
from tools.automation.resume_auto import sweep
from tools.text.utf8_file_helpers import write_utf8_file


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        write_utf8_file(self.root / "PLAN.json", "{}")
        self.registry = Registry(self.root / "state")
        self.entry = self.registry.start("A", str(self.root), "test", ["PLAN.json"], 3, "native")
        self.registry.attach_scheduler("A", self.entry["run_id"], "heartbeat-A")

    def observe(self, **changes):
        result = {"thread_id": "A", "repo": str(self.root), "observed_at": 1000, "status": "idle",
                  "authoritative": True, "project_activity_complete": True, "source": "native_desktop_tools",
                  "active_project_threads": [], "limits": {"rateLimits": {"primary": {"usedPercent": 10}}}}
        result.update(changes)
        return result

    def reserve(self, **changes):
        return reserve_wake(self.registry, "A", self.entry["run_id"], self.observe(**changes), now=1000)

    def change(self, **changes):
        with self.registry.transaction() as data:
            data["threads"]["A"].update(changes)

    def test_terminal_states_are_never_woken_even_if_enabled_is_stale(self):
        for state in ("stopped", "needs_input", "batch_complete", "queue_complete", "pilot_complete", "unknown"):
            with self.subTest(state=state):
                self.change(state=state, enabled=True)
                self.assertEqual("skip", self.reserve()["action"])

    def test_batch_limit_and_blocking_needs_win(self):
        self.change(completed=3)
        self.assertEqual("batch_finished_or_invalid", self.reserve()["reason"])
        self.change(completed=0, needs=[{"id": "operator", "needed": "decision", "how": "reply", "blocks": "work"}])
        self.assertEqual("terminal_or_needs_input", self.reserve()["reason"])

    def test_active_target_or_any_other_project_thread_blocks(self):
        self.assertEqual("thread_not_idle", self.reserve(status="active")["reason"])
        self.assertEqual("project_busy", self.reserve(active_project_threads=["B"])["reason"])
        self.assertEqual("thread_not_idle", self.reserve(status="systemError")["reason"])

    def test_native_unloaded_thread_is_eligible_but_private_server_is_not(self):
        self.assertEqual("prepared", self.reserve(status="notLoaded")["action"])
        self.change(wake_dispatch=None)
        with self.assertRaises(ValueError):
            self.reserve(status="notLoaded", source="private_app_server_read_only", authoritative=False)

    def test_stale_partial_foreign_observations_fail_closed(self):
        for changes in ({"observed_at": 800}, {"project_activity_complete": False}, {"thread_id": "B"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                self.reserve(**changes)

    def test_limits_and_future_reset_are_respected(self):
        result = self.reserve(limits={"rateLimits": {"primary": {"usedPercent": 100, "resetsAt": 2000}}})
        self.assertEqual("account_limit", result["reason"])
        self.assertEqual(2060, result["next_check_at"])
        self.assertEqual("backoff", self.reserve()["reason"])

    def test_missing_limits_are_not_treated_as_available(self):
        with self.assertRaises(ValueError):
            self.reserve(limits={})

    def test_spend_control_and_account_denial_are_not_ignored(self):
        for limits in ({"ordinaryUsageAllowed": False},
                       {"rateLimits": {"spendControlReached": True, "primary": {"usedPercent": 0}}}):
            self.assertFalse(limit_availability(limits, 1000)[0])

    def test_duplicate_survives_process_recreation_and_delivery_timeout(self):
        reservation = self.reserve()
        record_delivery(self.registry, reservation, "unknown", "timeout after write")
        fresh = Registry(self.registry.home)
        result = reserve_wake(fresh, "A", self.entry["run_id"], self.observe(), now=1000)
        self.assertEqual("delivery_pending", result["reason"])
        self.assertEqual("unknown", fresh.get("A")["recovery"]["dispatch"]["status"])

    def test_prepared_send_blocks_other_chat_and_never_expires_by_timeout(self):
        self.reserve()
        second = self.registry.start("B", str(self.root), "test", ["PLAN.json"], 3, "native")
        observation = self.observe(thread_id="B", observed_at=999999)
        result = reserve_wake(self.registry, "B", second["run_id"], observation, now=999999)
        self.assertEqual("project_reserved", result["reason"])
        self.assertEqual("delivery_pending", self.reserve()["reason"])

    def test_another_project_reservation_does_not_block(self):
        folder = self.root / "other"
        write_utf8_file(folder / "PLAN.json", "{}")
        self.registry.start("B", str(folder), "test", ["PLAN.json"], 3, "native")
        with self.registry.transaction() as data:
            data["threads"]["B"]["inflight"] = {"task_id": "other", "wake_id": "x"}
        self.assertEqual("prepared", self.reserve()["action"])

    def test_stop_cancels_pending_delivery_without_leaking_project_lock(self):
        reservation = self.reserve()
        self.registry.stop("A")
        record_delivery(self.registry, reservation, "sent")
        self.assertEqual("cancelled", self.registry.get("A")["wake_dispatch"]["status"])
        second = self.registry.start("B", str(self.root), "test", ["PLAN.json"], 3, "native")
        result = reserve_wake(self.registry, "B", second["run_id"], self.observe(thread_id="B"), now=1000)
        self.assertEqual("prepared", result["action"])

    def test_native_begin_acknowledges_without_erasing_reserved_work(self):
        reservation = self.reserve()
        work = {"wake_id": "old", "task_id": "unfinished", "started_at": 900}
        self.change(inflight=work, state="executing")
        result = authorize(self.registry, "A", self.entry["run_id"], "heartbeat-A", "new",
                           self.observe(status="active", active_project_threads=["A"]), [], now=1000)
        self.assertEqual("reconcile", result["action"])
        self.assertEqual(work, self.registry.get("A")["inflight"])
        record_delivery(self.registry, reservation, "sent")
        self.assertEqual("acknowledged", self.registry.get("A")["wake_dispatch"]["status"])

    def test_heartbeat_cannot_reserve_different_chat_while_send_is_pending(self):
        self.reserve()
        second = self.registry.start("B", str(self.root), "test", ["PLAN.json"], 3, "native")
        self.registry.attach_scheduler("B", second["run_id"], "heartbeat-B")
        result = authorize(self.registry, "B", second["run_id"], "heartbeat-B", "wake-B",
                           self.observe(thread_id="B", status="active", active_project_threads=["B"]), [], now=1000)
        self.assertEqual("project_wake_pending", result["reason"])

    def test_own_interrupted_reservation_can_receive_recovery_without_being_released(self):
        work = {"wake_id": "old", "task_id": "unfinished", "started_at": 900}
        self.change(state="executing", inflight=work)
        self.assertEqual("prepared", self.reserve()["action"])
        self.assertEqual(work, self.registry.get("A")["inflight"])

    def test_stale_run_cannot_send_or_update_new_start(self):
        self.registry.stop("A")
        self.registry.start("A", str(self.root), "test", ["PLAN.json"], 3, "native")
        with self.assertRaises(ValueError):
            self.reserve()

    def test_dry_run_neither_reserves_nor_sends(self):
        result = reserve_wake(self.registry, "A", self.entry["run_id"], self.observe(), now=1000, dry_run=True)
        self.assertEqual("would_send", result["action"])
        self.assertIsNone(self.registry.get("A").get("wake_dispatch"))

    def test_registry_lock_rejects_second_process_owner(self):
        with self.registry.transaction():
            with self.assertRaises((RuntimeError, OSError)):
                with Registry(self.registry.home).transaction():
                    self.fail("Concurrent owner acquired the same registry")

    def test_progress_distinguishes_batch_from_queue_completion(self):
        self.change(state="batch_complete", enabled=False, completed=3)
        entry = self.registry.get("A")
        record = recovery_record(entry)
        self.assertTrue(record["run_finished"])
        self.assertTrue(record["batch_finished"])
        self.assertFalse(record["queue_finished"])
        progress = json.loads(Path(self.registry.context("A")["files"]["progress"]).read_text(encoding="utf-8"))
        self.assertEqual(record, progress["recovery"])

    def test_manual_transport_does_not_create_heartbeat(self):
        self.registry.stop("A")
        entry = self.registry.start("A", str(self.root), "test", ["PLAN.json"], 3, "native", wake_transport="manual")
        self.assertEqual("manual_wake_only", scheduler_request(entry)["action"])
        result = authorize(self.registry, "A", entry["run_id"], None, "manual-turn",
                           self.observe(status="active", active_project_threads=["A"]), [], now=1000)
        self.assertEqual("queue_complete", result["reason"])

    def test_stop_between_observation_and_claim_prevents_send(self):
        registry = self.registry
        observation = self.observe(observed_at=__import__("time").time())

        class Bridge:
            def observation(self, entry):
                registry.stop("A")
                return observation

            def send(self, thread):
                raise AssertionError("STOP was ignored")

        self.assertEqual("inactive", sweep(self.registry, Bridge())[0]["reason"])

    def test_sweep_sends_only_exact_prompt_and_id_once(self):
        observation = self.observe(observed_at=__import__("time").time())
        sent = []

        class Bridge:
            def observation(self, entry):
                return observation

            def send(self, thread):
                sent.append(thread)
                return {"threadId": thread}

        self.assertEqual("sent", sweep(self.registry, Bridge())[0]["action"])
        self.assertEqual(["A"], sent)
        self.assertEqual("delivery_pending", sweep(self.registry, Bridge())[0]["reason"])

    def test_wrong_destination_acknowledgement_is_not_success(self):
        observation = self.observe(observed_at=__import__("time").time())

        class Bridge:
            def observation(self, entry):
                return observation

            def send(self, thread):
                return {"threadId": "different"}

        self.assertEqual("delivery_unknown", sweep(self.registry, Bridge())[0]["action"])


class DesktopProtocolTests(unittest.TestCase):
    def bridge(self, response):
        encoded = json.dumps(response).encode("utf-8")

        class Channel:
            def __init__(self):
                self.buffer = struct.pack("<I", len(encoded)) + encoded
                self.written = b""

            def write(self, data):
                self.written += data

            def read(self, count):
                result, self.buffer = self.buffer[:count], self.buffer[count:]
                return result

        bridge = DesktopBridge("unused", "controller")
        bridge.channel = Channel()
        return bridge

    def test_frame_checks_identity_and_rejects_errors(self):
        for response in ({"id": 2, "jsonrpc": "2.0", "result": {}},
                         {"id": 1, "jsonrpc": "2.0", "error": {"message": "rejected"}}):
            with self.subTest(response=response), self.assertRaises((ValueError, RuntimeError)):
                self.bridge(response).request("tools/list", {})

    def test_send_has_exact_id_and_prompt_without_model_override(self):
        bridge = DesktopBridge("unused", "controller")
        bridge.tools = {"send_message_to_thread": {"inputSchema": {
            "properties": {"threadId": {}, "hostId": {}, "prompt": {}}, "required": ["threadId", "prompt"]}}}
        captured = []

        def request(method, params):
            captured.append(params)
            return {"success": True, "contentItems": [{"type": "inputText", "text": '{"threadId":"A"}'}]}

        bridge.request = request
        bridge.send("A")
        self.assertEqual({"threadId": "A", "hostId": "local", "prompt": "CONTINUE-AUTO"}, captured[0]["arguments"])


if __name__ == "__main__":
    unittest.main()
