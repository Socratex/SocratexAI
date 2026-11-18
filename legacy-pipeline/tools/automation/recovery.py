"""Durable recovery decisions and outbox shared by manual and scheduled wake-ups.

The registry remains the grant owner. A prepared send is committed before I/O;
an ambiguous delivery never expires into permission to send another prompt.
"""

from __future__ import annotations

import time
import uuid

from .controller import TERMINAL_STATES, current_run, limit_availability, project_path, remember_limit

RECOVERABLE_STATES = {"registered", "waiting_turn_end", "waiting_limit", "executing"}
PENDING_DELIVERY = {"prepared", "sent", "unknown"}


def cancel_terminal_delivery(entry: dict) -> None:
    delivery = entry.get("wake_dispatch") or {}
    if (entry.get("enabled") is not True or entry.get("state") in TERMINAL_STATES) and delivery.get("status") in PENDING_DELIVERY:
        delivery.update(status="cancelled", cancelled_at=time.time())


def recovery_record(entry: dict) -> dict:
    state = entry["state"]
    finished = state in {"batch_complete", "queue_complete", "pilot_complete"}
    return {"schema_version": 1, "run_finished": finished,
            "queue_finished": state == "queue_complete", "batch_finished": state == "batch_complete",
            "stopped": state == "stopped", "needs_input": state == "needs_input" or bool(entry.get("needs")),
            "active": entry.get("enabled") is True and state not in TERMINAL_STATES,
            "limit_wait": entry.get("limit_wait"),
            "work_reserved": bool(entry.get("inflight")), "next_check_at": entry.get("next_check_at", 0),
            "dispatch": entry.get("wake_dispatch")}


def eligibility(entry: dict, now: float) -> str | None:
    from .shutdown import pending
    if pending(entry):
        return "shutdown_pending" if (entry.get("shutdown_policy") or {}).get("armed") else "shutdown_finished"
    if entry.get("mode") != "native" or entry.get("enabled") is not True:
        return "inactive"
    if entry.get("state") not in RECOVERABLE_STATES or entry.get("needs"):
        return "terminal_or_needs_input"
    completed, batch = entry.get("completed"), entry.get("batch_size")
    if type(completed) is not int or type(batch) is not int or not 0 <= completed < batch:
        return "batch_finished_or_invalid"
    if entry.get("next_check_at", 0) > now:
        return "backoff"
    if (entry.get("wake_dispatch") or {}).get("status") in PENDING_DELIVERY:
        return "delivery_pending"
    return None


def acknowledge(entry: dict, now: float) -> None:
    delivery = entry.get("wake_dispatch")
    if delivery and delivery.get("status") in PENDING_DELIVERY:
        delivery.update(status="acknowledged", acknowledged_at=now)
        if entry.get("limit_wait"):
            entry["limit_wait"]["active"] = False


def reserve_wake(registry, thread_id: str, run_id: str, observation: dict,
                 *, dry_run: bool = False, now: float | None = None) -> dict:
    from .controller import validate_snapshot

    now = time.time() if now is None else now
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        reason = eligibility(entry, now)
        if reason:
            return {"action": "skip", "reason": reason, "thread_id": thread_id}
        validate_snapshot(entry, observation, now)
        if observation.get("source") != "native_desktop_tools" or not observation["authoritative"]:
            raise ValueError("Recovery requires a fresh complete desktop observation")
        # Native desktop notLoaded is a known unloaded chat. A private server's
        # identically named status cannot reach this authority boundary.
        if observation["status"] not in {"idle", "notLoaded"}:
            return {"action": "skip", "reason": "thread_not_idle", "thread_id": thread_id}
        if observation["active_project_threads"]:
            return {"action": "skip", "reason": "project_busy", "thread_id": thread_id}
        for other in data["threads"].values():
            if other["thread_id"] == thread_id or project_path(other["repo"]) != entry["repo"]:
                continue
            if other.get("inflight") or (other.get("wake_dispatch") or {}).get("status") in PENDING_DELIVERY:
                return {"action": "skip", "reason": "project_reserved", "thread_id": thread_id}
        available, retry_at = limit_availability(observation.get("limits"), now)
        if not available:
            if not dry_run:
                remember_limit(entry, observation["limits"], now, retry_at)
            from .controller import limit_reset_at
            return {"action": "skip", "reason": "account_limit", "next_check_at": retry_at,
                    "limit_reset_at": limit_reset_at(observation["limits"]), "thread_id": thread_id}
        after_limit = (entry.get("limit_wait") or {}).get("active") or entry["state"] == "waiting_limit"
        result = {"action": "would_send" if dry_run else "prepared", "thread_id": thread_id,
                  "run_id": run_id, "prompt": "CONTINUE-AUTO (limit reached previously, continue)" if after_limit else "CONTINUE-AUTO"}
        if not dry_run:
            result["delivery_id"] = str(uuid.uuid4())
            entry["wake_dispatch"] = {"id": result["delivery_id"], "run_id": run_id,
                                      "status": "prepared", "prepared_at": now, "prompt": result["prompt"]}
        return result


def record_delivery(registry, reservation: dict, status: str, detail: str = "") -> None:
    if status not in {"sent", "unknown"}:
        raise ValueError("Delivery outcome must be sent or unknown")
    with registry.transaction() as data:
        entry = current_run(data, reservation["thread_id"], reservation["run_id"])
        delivery = entry.get("wake_dispatch") or {}
        if delivery.get("id") != reservation["delivery_id"]:
            raise ValueError("Delivery no longer belongs to this run")
        # The target can acknowledge before the sender receives the IPC response.
        if delivery.get("status") == "prepared":
            delivery.update(status=status, finished_at=time.time(), detail=detail)


def resolve_delivery(registry, thread_id: str, delivery_id: str) -> dict:
    """Explicit operator reconciliation, never a timeout-based automatic retry."""
    with registry.transaction() as data:
        entry = data["threads"][thread_id]
        delivery = entry.get("wake_dispatch") or {}
        if delivery.get("id") != delivery_id or delivery.get("run_id") != entry["run_id"]:
            raise ValueError("Delivery ID does not belong to the exact current AUTO run")
        if delivery.get("status") not in PENDING_DELIVERY:
            raise ValueError("Delivery is already resolved")
        delivery.update(status="acknowledged", acknowledged_at=time.time(), resolution="explicit_operator_reconciliation")
        return {"action": "delivery_resolved", "thread_id": thread_id, "delivery_id": delivery_id, "dispatch": False}
