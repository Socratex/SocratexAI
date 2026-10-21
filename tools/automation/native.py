"""Authorize one scoped unit of real work inside an already scheduled native turn."""

from __future__ import annotations

import json
import math
import time

from .controller import Registry, TERMINAL_STATES, choose_task, current_run, limit_availability, nonempty, number, project_path, validate_snapshot
from .selection import EXECUTABLE, projection_context, status, unpack_projection


def payload(value: dict) -> dict:
    if "content" in value:
        parts = [item["text"] for item in value["content"] if item.get("type") == "text"]
        if len(parts) != 1:
            raise ValueError("Expected one JSON observation payload")
        value = json.loads(parts[0])
    if not isinstance(value, dict):
        raise ValueError("Native observation must be an object")
    return value


def snapshot(entry: dict, threads: dict, limits: dict, observed_at: float, list_limit: int = 1000,
             interrupted_by_limit: bool = False) -> dict:
    threads = payload(threads)
    if threads.get("unavailableHosts") or threads.get("unavailableSources"):
        raise ValueError("Native project activity is incomplete")
    if len(threads.get("threads", [])) >= list_limit and not threads.get("complete_project_roster"):
        raise ValueError("Thread inventory is truncated; request a larger list")
    observed = threads.get("pinnedThreads", []) + threads.get("threads", [])
    matching = [item for item in observed if item.get("id") == entry["thread_id"]]
    if len(matching) != 1:
        raise ValueError("Exact registered native thread was not observed once")
    target = matching[0]
    if target.get("kind") != "codex" or project_path(target.get("cwd", "")) != entry["repo"]:
        raise ValueError("Native target is not the registered Codex project")
    active = [item["id"] for item in observed if item.get("kind") == "codex"
              and item.get("status") == "active" and project_path(item.get("cwd", "")) == entry["repo"]]
    return {"thread_id": entry["thread_id"], "repo": entry["repo"], "observed_at": number(observed_at, "observed_at"),
            "status": target["status"], "authoritative": True, "project_activity_complete": True,
            "active_project_threads": active, "source": "native_desktop_tools", "limits": payload(limits),
            "interrupted_by_limit": interrupted_by_limit}


def control_handoff(registry: Registry, thread_id: str, run_id: str, control_thread_id: str, now: float | None = None) -> dict:
    now = time.time() if now is None else number(now, "now")
    if control_thread_id == thread_id:
        raise ValueError("Control chat and worker chat must differ")
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        if entry["mode"] != "native" or not entry["enabled"]:
            raise ValueError("Handoff requires an active native grant")
        entry["control_handoff"] = {"thread_id": nonempty(control_thread_id, "control_thread_id"), "read_only_until": now + 180}
        return {"action": "control_read_only", "until": now + 180}


def authorize(registry: Registry, thread_id: str, run_id: str, scheduler_id: str, wake_id: str,
              observation: dict, tasks: list[dict] | dict, now: float | None = None, prompt_context: str | None = None) -> dict:
    now = time.time() if now is None else number(now, "now")
    wake_id = nonempty(wake_id, "wake_id")
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        if entry["mode"] != "native":
            raise ValueError("Native execution requires explicit START AUTO --mode native")
        if not entry["enabled"] or entry["state"] in TERMINAL_STATES:
            return {"action": "stop", "reason": entry["state"], "scheduler_id": entry["scheduler_id"]}
        if entry["scheduler_id"] != scheduler_id or (not scheduler_id and entry.get("wake_transport", "heartbeat") != "manual"):
            raise ValueError("Native event scheduler does not match the registered scheduler")
        if wake_id in entry.get("processed_wakes", []):
            return {"action": "wait", "reason": "duplicate_wake"}
        if entry["next_check_at"] > now:
            return {"action": "wait", "reason": "account_limit", "next_check_at": entry["next_check_at"]}
        validate_snapshot(entry, observation, now)
        if not observation["authoritative"] or observation.get("source") != "native_desktop_tools":
            raise ValueError("Private App Server cannot authorize desktop execution")
        if observation["status"] != "active":
            raise ValueError("Only the current active native wake can authorize its own work")
        from .recovery import PENDING_DELIVERY, acknowledge
        acknowledge(entry, now)
        busy = set(observation["active_project_threads"]) - {thread_id}
        handoff = entry.get("control_handoff", {})
        if handoff.get("read_only_until", 0) >= now:
            busy.discard(handoff["thread_id"])
        if busy:
            return {"action": "wait", "reason": "project_busy", "threads": sorted(busy)}
        for other in data["threads"].values():
            if other["thread_id"] != thread_id and other["repo"] == entry["repo"] and other.get("inflight"):
                return {"action": "wait", "reason": "project_reserved", "thread_id": other["thread_id"]}
            if (other["thread_id"] != thread_id and other["repo"] == entry["repo"]
                    and (other.get("wake_dispatch") or {}).get("status") in PENDING_DELIVERY):
                return {"action": "wait", "reason": "project_wake_pending", "thread_id": other["thread_id"]}
        interrupted = observation.get("interrupted_by_limit", False)
        if type(interrupted) is not bool:
            raise ValueError("interrupted_by_limit must be boolean")
        if interrupted:
            entry["resume_pending"] = True
        available, retry_at = limit_availability(observation.get("limits"), now)
        if not available:
            entry.update(state="waiting_limit", next_check_at=retry_at)
            return {"action": "wait", "reason": "account_limit", "next_check_at": retry_at}
        if entry.get("inflight") and not entry["resume_pending"]:
            return {"action": "reconcile", "reason": "unfinished_reserved_work", "work": entry["inflight"]}
        if entry["resume_pending"]:
            task_id = (entry.get("inflight") or {}).get("task_id", "interrupted_task")
            command = "LIMIT"
        else:
            if prompt_context is not None and not isinstance(prompt_context, str):
                raise ValueError("prompt_context must be text")
            selection_entry = entry if prompt_context is None else {**entry, "prompt_context": prompt_context.strip()}
            selected = choose_task(selection_entry, tasks)
            entry["task_projection"] = tasks
            entry["last_prompt_context"] = (projection_context(selection_entry) if isinstance(tasks, dict)
                                            else selection_entry.get("prompt_context", ""))
            if selected["action"] != "would_continue":
                if not selected["blocked_task_ids"]:
                    candidates, context = unpack_projection(selection_entry, tasks)
                    unassessed = [task["id"] for task in candidates
                                  if status(task.get("status"), legacy=entry.get("task_policy_version", 1) < 2) in EXECUTABLE
                                  and task.get("scope", entry["scope"]) == entry["scope"]
                                  and task.get("context_assessment") is None]
                    if context and unassessed:
                        return {"action": "assess_context", "reason": "unassessed_prompt_mismatch",
                                "task_ids": unassessed}
                    entry.update(enabled=False, state="queue_complete", next_check_at=0)
                    return {"action": "stop", "reason": "queue_complete", "scheduler_id": entry["scheduler_id"]}
                return {"action": "select_or_block", "reason": selected["reason"], "blocked_task_ids": selected["blocked_task_ids"]}
            task_id, command = selected["task_id"], "CONTINUE-AUTO"
        entry["inflight"] = {"wake_id": wake_id, "task_id": task_id, "started_at": now}
        entry["processed_wakes"].append(wake_id)
        entry.update(state="executing", next_check_at=0)
        return {"action": "execute", "command": command, "task_id": task_id, "wake_id": wake_id,
                "thread_id": thread_id, "run_id": run_id, "mode": "native", "authorization": "current_native_turn",
                "scope": entry["scope"], "completed": entry["completed"], "batch_size": entry["batch_size"]}


def render_instructions(entry: dict) -> str:
    try:
        from .instructions import render_instructions as render
    except ModuleNotFoundError as exc:
        if exc.name != __package__ + ".instructions":
            raise
        from .generic_instructions import render_instructions as render
    return render(entry)


def scheduler_request(entry: dict, retry_at: float | None = None, now: float | None = None, pause: bool = False) -> dict:
    if entry["mode"] != "native":
        raise ValueError("Scheduling real work requires native mode")
    if entry.get("wake_transport") == "manual":
        return {"action": "manual_wake_only", "dispatch": False, "thread_id": entry["thread_id"]}
    now = time.time() if now is None else number(now, "now")
    interval = 1 if retry_at is None else max(1, math.ceil((number(retry_at, "retry_at") - now) / 60))
    thread_id = entry["thread_id"]
    result = {"mode": "update" if entry.get("scheduler_id") else "create", "kind": "heartbeat", "destination": "thread",
              "targetThreadId": thread_id, "name": f"AUTO: {thread_id[:8]}", "prompt": "CONTINUE-AUTO",
              "rrule": f"RRULE:FREQ=MINUTELY;INTERVAL={interval}", "status": "ACTIVE" if entry["enabled"] and not pause else "PAUSED"}
    if entry.get("scheduler_id"):
        result["id"] = entry["scheduler_id"]
    return result
