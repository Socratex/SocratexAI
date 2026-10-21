"""Own AUTO grants, lifecycle and project reservations independently of agent UI."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

_TEXT_TOOLS = Path(__file__).resolve().parents[1] / "text"
if str(_TEXT_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TEXT_TOOLS))
from utf8_file_helpers import write_utf8_file


SCHEMA_VERSION = 1
TERMINAL_STATES = {"stopped", "needs_input", "batch_complete", "pilot_complete", "queue_complete"}


def nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    return value.strip()


def number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} must be finite numeric data")
    return float(value)


def project_path(value: str | Path) -> str:
    text = str(value)
    if os.name == "nt" and text.startswith("\\\\?\\"):
        text = "\\\\" + text[8:] if text.startswith("\\\\?\\UNC\\") else text[4:]
    return os.path.normcase(str(Path(text).resolve()))


def default_home() -> Path:
    configured = os.environ.get("SOCRATEX_AUTO_HOME")
    if configured:
        return Path(configured).expanduser().resolve()
    base = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local" / "state")))
    return base / "SocratexPipeline" / "auto"


class Registry:
    def __init__(self, home: Path | None = None):
        self.home = home or default_home()
        self.path = self.home / "registry.json"

    @contextmanager
    def transaction(self):
        self.home.mkdir(parents=True, exist_ok=True)
        # OS locks are released on process death; stale files never require deletion.
        with (self.home / "registry.lock").open("a+b") as lock:
            lock.seek(0, os.SEEK_END)
            if lock.tell() == 0:
                lock.write(b"\0")
                lock.flush()
            lock.seek(0)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as exc:
                raise RuntimeError("AUTO registry is busy; retry on the next tick") from exc
            try:
                data = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {
                    "schema_version": SCHEMA_VERSION, "threads": {},
                }
                if data.get("schema_version") != SCHEMA_VERSION or not isinstance(data.get("threads"), dict):
                    raise ValueError("Unsupported or malformed AUTO registry; original preserved")
                yield data
                from .files import progress_record, synchronize
                from .recovery import cancel_terminal_delivery, recovery_record
                runs = data.setdefault("runs", {})
                for entry in data["threads"].values():
                    cancel_terminal_delivery(entry)
                    entry["recovery"] = recovery_record(entry)
                    runs.setdefault(entry["thread_id"], {})[entry["run_id"]] = progress_record(entry)
                temporary = self.home / f"registry.{uuid.uuid4().hex}.tmp"
                try:
                    write_utf8_file(temporary, json.dumps(data, ensure_ascii=False, indent=4))
                    os.replace(temporary, self.path)
                finally:
                    temporary.unlink(missing_ok=True)
                synchronize(self.home, data)
            finally:
                lock.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

    def start(self, thread_id: str, repo: str, scope: str, sources: list[str], batch_size: int = 3,
              mode: str = "pilot", prompt_context: str = "", wake_transport: str = "manual") -> dict:
        thread_id = nonempty(thread_id, "thread_id")
        scope = nonempty(scope, "scope")
        if not isinstance(prompt_context, str):
            raise ValueError("prompt_context must be text")
        prompt_context = prompt_context.strip()
        if mode not in {"pilot", "native"}:
            raise ValueError("AUTO mode must be pilot or native")
        if wake_transport not in {"heartbeat", "manual"}:
            raise ValueError("AUTO wake transport must be heartbeat or manual")
        if isinstance(batch_size, bool) or not isinstance(batch_size, int) or not 1 <= batch_size <= 100:
            raise ValueError("batch_size must be an integer between 1 and 100")
        root = Path(repo).resolve(strict=True)
        if not root.is_dir() or not sources:
            raise ValueError("An existing project directory and approved source list are required")
        normalized_sources = sorted({source_path(root, source)[0] for source in sources})
        with self.transaction() as data:
            previous = data["threads"].get(thread_id)
            if previous and previous["enabled"]:
                if (previous["repo"], previous["scope"], previous["sources"], previous["batch_size"], previous["mode"]) != (
                    project_path(root), scope, normalized_sources, batch_size, mode,
                ):
                    raise ValueError("STOP AUTO before changing an active grant")
                if previous.get("prompt_context", "") != prompt_context:
                    raise ValueError("STOP AUTO before changing the stored prompt context")
                if previous.get("wake_transport", "heartbeat") != wake_transport:
                    raise ValueError("STOP AUTO before changing the wake transport")
                return dict(previous)
            if previous and previous.get("inflight"):
                raise ValueError("Previous work still owns this project; finish or reconcile it before START AUTO")
            if previous:
                from .files import progress_record
                data.setdefault("runs", {}).setdefault(thread_id, {})[previous["run_id"]] = progress_record(previous)
            entry = {
                "thread_id": thread_id, "repo": project_path(root), "scope": scope,
                "sources": normalized_sources, "batch_size": batch_size, "completed": 0,
                "run_id": str(uuid.uuid4()), "enabled": True, "mode": mode,
                "state": "registered", "checkpoint": None, "next_check_at": 0,
                "resume_pending": False, "scheduler_id": None, "notices": [],
                "needs": [], "last_decision": None, "receipts": [],
                "inflight": None, "processed_wakes": [], "pending_needs": [],
                "completed_steps": [],
                "task_policy_version": 2, "prompt_context": prompt_context,
                "wake_transport": wake_transport,
            }
            data["threads"][thread_id] = entry
            return dict(entry)

    def get(self, thread_id: str) -> dict:
        with self.transaction() as data:
            return dict(data["threads"][thread_id])

    def use_manual_transport(self, thread_id: str, run_id: str) -> dict:
        with self.transaction() as data:
            entry = current_run(data, thread_id, run_id)
            previous = entry.get("scheduler_id")
            if previous:
                entry["retired_scheduler_id"] = previous
            entry.update(wake_transport="manual", scheduler_id=None)
            return {"action": "manual_transport", "thread_id": thread_id, "run_id": run_id,
                    "scheduler_id_to_pause": previous, "dispatch": False}

    def context(self, thread_id: str | None = None, scheduler_id: str | None = None) -> dict:
        with self.transaction() as data:
            if scheduler_id:
                matches = [entry for entry in data["threads"].values() if entry.get("scheduler_id") == scheduler_id]
                if len(matches) != 1:
                    raise ValueError("Scheduler does not identify exactly one current AUTO thread")
                matched = matches[0]["thread_id"]
                if thread_id and thread_id != matched:
                    raise ValueError("Current thread and scheduler identity disagree")
                thread_id = matched
            if not thread_id:
                raise ValueError("Use CODEX_THREAD_ID, trusted heartbeat scheduler ID, or an explicit known current thread ID")
            entry = data["threads"][thread_id]
            from .files import paths
            return {"thread_id": thread_id, "run_id": entry["run_id"], "mode": entry["mode"],
                    "state": entry["state"], "enabled": entry["enabled"], "completed": entry["completed"],
                    "batch_size": entry["batch_size"], "files": paths(self.home, thread_id, entry["run_id"])}

    def import_progress(self, thread_id: str, run_id: str, reports: list[tuple[str, dict]]) -> dict:
        with self.transaction() as data:
            entry = current_run(data, thread_id, run_id)
            steps = entry.setdefault("completed_steps", [])
            indexed = {step["receipt_id"] for step in steps}
            added = 0
            for source, report in reports:
                receipt = nonempty(report.get("receipt_id"), "receipt_id")
                if receipt not in entry["receipts"] or report.get("decision") != "continue":
                    raise ValueError("Only already accepted completed receipts may be imported")
                if report.get("wake_id") not in entry.get("processed_wakes", []):
                    raise ValueError("Imported receipt wake does not belong to this run")
                if receipt in indexed:
                    continue
                checkpoint = nonempty(report.get("checkpoint"), "checkpoint")
                task_id = checkpoint.split(":", 1)[0] if ":" in checkpoint else receipt
                progress = validate_progress(report)
                steps.append({"receipt_id": receipt, "wake_id": report["wake_id"], "task_id": task_id,
                              **progress, "conclusions": checkpoint, "commit": report.get("commit"),
                              "finished_at": None, "imported": True, "source_receipt": source})
                indexed.add(receipt)
                added += 1
            if len(steps) > entry["completed"]:
                raise ValueError("Imported steps exceed the accepted completed count")
            steps.sort(key=lambda step: entry["receipts"].index(step["receipt_id"]))
            return {"action": "progress_imported", "added": added, "completed": entry["completed"], "state": entry["state"]}

    def stop(self, thread_id: str) -> dict:
        with self.transaction() as data:
            entry = data["threads"][thread_id]
            entry.update(enabled=False, state="stopped", next_check_at=0)
            return dict(entry)

    def attach_scheduler(self, thread_id: str, run_id: str, scheduler_id: str) -> None:
        with self.transaction() as data:
            entry = current_run(data, thread_id, run_id)
            if not entry["enabled"]:
                raise ValueError("Cannot attach a scheduler to a stopped AUTO run")
            entry["scheduler_id"] = nonempty(scheduler_id, "scheduler_id")
            entry["wake_transport"] = "heartbeat"

    def confirm_wake(self, thread_id: str, run_id: str, scheduler_id: str) -> dict:
        with self.transaction() as data:
            entry = current_run(data, thread_id, run_id)
            if entry["mode"] != "pilot":
                raise ValueError("confirm-wake is only for the report-only pilot")
            if entry["scheduler_id"] != scheduler_id:
                raise ValueError("Wake is not from the registered scheduler")
            if not entry["enabled"]:
                return {"action": "ignored", "reason": entry["state"]}
            entry.update(enabled=False, state="pilot_complete", wake_confirmed_at=time.time())
            return {"action": "pilot_wake_confirmed", "thread_id": thread_id, "dispatch": False,
                    "scheduler_id_to_pause": scheduler_id}

    def finalize(self, thread_id: str, run_id: str, report: dict, repo: str) -> dict:
        if report.get("decision") not in {"continue", "needs_input"}:
            raise ValueError("Finalizer report decision must be continue or needs_input")
        checkpoint = nonempty(report.get("checkpoint"), "checkpoint")
        needs = validate_needs(report.get("needs", []))
        pending_needs = validate_needs(report.get("pending_needs", []))
        progress = validate_progress(report)
        if report["decision"] == "needs_input" and not needs:
            raise ValueError("needs_input requires an actionable operator table")
        if report["decision"] == "continue" and needs:
            raise ValueError("continue cannot discard pending operator needs")
        receipt = nonempty(report.get("receipt_id"), "receipt_id")
        with self.transaction() as data:
            entry = current_run(data, thread_id, run_id)
            if entry["repo"] != project_path(repo):
                raise ValueError("Finalizer project does not match registered project")
            validate_native_receipt(entry, report)
            if report.get("reconciles_commit"):
                return reconcile_receipt(entry, report, progress, checkpoint, receipt)
            if not entry["enabled"] or entry["state"] in TERMINAL_STATES:
                if entry.get("inflight") and receipt not in entry["receipts"]:
                    work = entry["inflight"]
                    entry.update(checkpoint=checkpoint, pending_needs=pending_needs or entry.get("pending_needs", []))
                    if needs:
                        entry["needs"] = needs
                    entry["receipts"].append(receipt)
                    if report["decision"] == "continue":
                        record_step(entry, report, progress, work, checkpoint, receipt)
                entry["inflight"] = None
                return {"action": "ignored", "reason": entry["state"]}
            if receipt in entry["receipts"]:
                return {"action": "ignored", "reason": "duplicate_receipt"}
            work = entry.get("inflight")
            entry.update(checkpoint=checkpoint, last_receipt=receipt, needs=needs)
            if "pending_needs" in report:
                entry["pending_needs"] = pending_needs
            entry["receipts"].append(receipt)
            unit_completed = (entry["mode"] == "pilot" or bool(work)) and report["decision"] == "continue"
            if unit_completed:
                record_step(entry, report, progress, work, checkpoint, receipt)
            entry.update(inflight=None, resume_pending=False)
            if needs:
                entry.update(enabled=False, state="needs_input")
                return notice(entry, needs)
            if entry["completed"] >= entry["batch_size"]:
                entry.update(enabled=False, state="batch_complete")
            else:
                entry["state"] = "waiting_turn_end"
            result = {"action": "checkpoint_saved", "state": entry["state"], "mode": entry["mode"],
                      "scheduler_id": entry["scheduler_id"], "completed": entry["completed"]}
            if entry["state"] == "batch_complete" and entry.get("pending_needs"):
                result.update(notice(entry, entry["pending_needs"]))
            return result

    def tick(self, thread_id: str, snapshot: dict, tasks: list[dict], now: float | None = None) -> dict:
        now = time.time() if now is None else number(now, "now")
        with self.transaction() as data:
            entry = data["threads"][thread_id]
            if not entry["enabled"]:
                return {"action": "wait", "reason": entry["state"], "mode": "pilot"}
            if entry["next_check_at"] > now:
                return {"action": "wait", "reason": "scheduled_wait", "next_check_at": entry["next_check_at"]}
            validate_snapshot(entry, snapshot, now)
            if snapshot["status"] == "active" or snapshot["active_project_threads"]:
                return {"action": "wait", "reason": "project_busy" if snapshot["active_project_threads"] else snapshot["status"]}
            if not snapshot["authoritative"]:
                return {"action": "inspect_only", "reason": "desktop_activity_not_verified"}
            interrupted = snapshot.get("interrupted_by_limit", False)
            if not isinstance(interrupted, bool):
                raise ValueError("interrupted_by_limit must be boolean")
            if interrupted:
                entry["resume_pending"] = True
            available, retry_at = limit_availability(snapshot.get("limits"), now)
            if not available:
                entry.update(state="waiting_limit", next_check_at=retry_at)
                return {"action": "wait", "reason": "account_limit", "next_check_at": retry_at}
            if snapshot["status"] != "idle":
                return {"action": "wait", "reason": snapshot["status"]}
            if entry["resume_pending"]:
                result = {"action": "would_resume", "command": "LIMIT", "checkpoint": entry["checkpoint"]}
            elif entry["checkpoint"] is None:
                result = {"action": "inspect_only", "reason": "no_finalized_checkpoint"}
            else:
                result = choose_task(entry, tasks)
            result.update(mode="pilot", thread_id=thread_id, dispatch=False)
            entry["last_decision"] = result
            return result


def current_run(data: dict, thread_id: str, run_id: str) -> dict:
    entry = data["threads"][thread_id]
    if entry["run_id"] != run_id:
        raise ValueError("Stale AUTO run; finalizer cannot affect a newer START AUTO")
    return entry


def validate_native_receipt(entry: dict, report: dict) -> None:
    if entry["mode"] != "native":
        return
    if report.get("receipt_id") in entry["receipts"]:
        return
    work = entry.get("inflight")
    if work and report.get("wake_id") != work["wake_id"]:
        raise ValueError("Native finalizer must match the reserved wake_id")
    if not work and report.get("decision") == "continue":
        raise ValueError("Native continue receipt requires an active work reservation")


def validate_progress(report: dict) -> dict:
    value = report.get("progress")
    if value is None:
        return {"summary": nonempty(report.get("checkpoint"), "checkpoint"), "verification": [], "evidence": []}
    if not isinstance(value, dict):
        raise ValueError("progress must be an object")
    result = {"summary": nonempty(value.get("summary"), "progress.summary")}
    for key in ("verification", "evidence"):
        entries = value.get(key, [])
        if not isinstance(entries, list):
            raise ValueError(f"progress.{key} must be an array")
        result[key] = [nonempty(item, f"progress.{key}") for item in entries]
    return result


def reconcile_receipt(entry: dict, report: dict, progress: dict, checkpoint: str, receipt: str) -> dict:
    matches = [step for step in entry.get("completed_steps", []) if step["receipt_id"] == receipt]
    if receipt not in entry["receipts"] or len(matches) != 1 or entry.get("inflight"):
        raise ValueError("Commit reconciliation requires one completed receipt and no active reservation")
    step = matches[0]
    if step.get("wake_id") != report.get("wake_id"):
        raise ValueError("Commit reconciliation must preserve the original wake identity")
    commit = nonempty(report.get("commit"), "commit")
    previous = nonempty(report.get("reconciles_commit"), "reconciles_commit")
    if step.get("commit") == commit:
        return {"action": "ignored", "reason": "duplicate_reconciliation"}
    if step.get("commit") != previous:
        raise ValueError("Commit reconciliation target does not match the recorded commit")
    step.setdefault("previous_commits", []).append(previous)
    step.update(progress, commit=commit, conclusions=checkpoint, reconciled_at=time.time())
    entry["checkpoint"] = checkpoint
    return {"action": "receipt_reconciled", "completed": entry["completed"], "state": entry["state"]}


def record_step(entry: dict, report: dict, progress: dict, work: dict | None, checkpoint: str, receipt: str) -> None:
    entry["completed"] += 1
    entry.setdefault("completed_steps", []).append({"receipt_id": receipt, "wake_id": report.get("wake_id"),
        "task_id": work["task_id"] if work else report.get("task_id", "pilot"), **progress,
        "conclusions": checkpoint, "commit": report.get("commit"), "finished_at": time.time(), "imported": False})


def source_path(root: Path, value: str) -> tuple[str, Path]:
    relative = Path(nonempty(value, "source"))
    if relative.is_absolute():
        raise ValueError("Approved source must be project-relative")
    resolved = (root / relative).resolve(strict=True)
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError("Approved source must be a file inside the project")
    return resolved.relative_to(root).as_posix(), resolved


def validate_snapshot(entry: dict, snapshot: dict, now: float) -> None:
    if snapshot.get("thread_id") != entry["thread_id"] or project_path(snapshot.get("repo", "")) != entry["repo"]:
        raise ValueError("Observation is for a different thread or project")
    age = now - number(snapshot.get("observed_at"), "observed_at")
    if not 0 <= age <= 90:
        raise ValueError("Observation must be fresh (at most 90 seconds) and not from the future")
    if snapshot.get("status") not in {"idle", "active", "notLoaded", "systemError"}:
        raise ValueError("Unknown thread state; no idle assumption")
    if type(snapshot.get("authoritative")) is not bool or not isinstance(snapshot.get("active_project_threads"), list):
        raise ValueError("Explicit authority and project activity observations are required")
    if snapshot["authoritative"] and snapshot.get("project_activity_complete") is not True:
        raise ValueError("Authoritative observation must cover all project threads")


def limit_availability(limits: dict | None, now: float) -> tuple[bool, float]:
    if not isinstance(limits, dict):
        raise ValueError("Missing limit information; availability is unknown")
    if limits.get("ordinaryUsageAllowed") is False:
        return False, now + 300
    buckets = limits.get("rateLimitsByLimitId")
    if buckets is None:
        legacy = limits.get("rateLimits")
        buckets = {"legacy": legacy} if legacy is not None else {}
    if not isinstance(buckets, dict) or not buckets:
        raise ValueError("No observed rate-limit buckets")
    resets = []
    exhausted = False
    unknown_reset = False
    for bucket in buckets.values():
        if not isinstance(bucket, dict):
            raise ValueError("Malformed rate-limit bucket")
        if bucket.get("spendControlReached") is True:
            return False, now + 300
        if bucket.get("individualLimit") is not None:
            raise ValueError("Unrecognized individual account limit; availability is unknown")
        windows = [bucket[key] for key in ("primary", "secondary") if bucket.get(key) is not None]
        if not windows:
            raise ValueError("Missing rate-limit windows")
        bucket_exhausted = False
        for window in windows:
            if not isinstance(window, dict):
                raise ValueError("Malformed rate-limit window")
            used = number(window.get("usedPercent"), "usedPercent")
            if not 0 <= used <= 100:
                raise ValueError("usedPercent is outside 0..100")
            if used >= 100:
                exhausted = bucket_exhausted = True
                reset = window.get("resetsAt")
                if reset is None:
                    unknown_reset = True
                else:
                    resets.append(number(reset, "resetsAt") + 60)
        # A server-reported limit is authoritative even when percentages lag.
        if bucket.get("rateLimitReachedType") and not bucket_exhausted:
            exhausted = unknown_reset = True
    if not exhausted:
        return True, 0
    return False, max([now + (300 if unknown_reset else 60), *resets])


def validate_needs(needs: object) -> list[dict]:
    if not isinstance(needs, list):
        raise ValueError("needs must be an array")
    return [{key: nonempty(row.get(key), key) for key in ("id", "needed", "how", "blocks")} for row in needs]


def notice(entry: dict, needs: list[dict]) -> dict:
    identifier = hashlib.sha256(json.dumps(needs, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
    duplicate = identifier in entry["notices"]
    if not duplicate:
        entry["notices"].append(identifier)
    return {"action": "needs_input", "notice_id": identifier, "notify": not duplicate, "needs": needs}


def choose_task(entry: dict, projection: list[dict] | dict) -> dict:
    from .selection import EXECUTABLE, matches_context, status, unpack_projection
    tasks, context = unpack_projection(entry, projection)
    known = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("Each task must be an object")
        identifier = nonempty(task.get("id"), "task id")
        if identifier in known:
            raise ValueError("Duplicate task IDs in projection")
        current_status = status(task.get("status"), legacy=entry.get("task_policy_version", 1) < 2)
        if "approved" in task and type(task["approved"]) is not bool:
            raise ValueError("Optional task approval veto must be boolean")
        for field in ("depends_on", "independent_of"):
            if not isinstance(task.get(field, []), list) or any(not isinstance(item, str) for item in task.get(field, [])):
                raise ValueError(f"{field} must be a list of task IDs")
        source, path = source_path(Path(entry["repo"]), task.get("source"))
        if source not in entry["sources"]:
            raise ValueError("Task source is outside the approved grant")
        if hashlib.sha256(path.read_bytes()).hexdigest() != task.get("source_sha256"):
            raise ValueError("Stale task projection; regenerate from canonical sources")
        known[identifier] = {**task, "status": current_status}
    for task in tasks:
        references = task.get("depends_on", []) + task.get("independent_of", [])
        if any(dep not in known for dep in references):
            raise ValueError("Unknown dependency or independence reference")
        if task["id"] in references:
            raise ValueError("Task cannot depend on or skip itself")
    blocked = []
    for task in tasks:
        candidate = known[task["id"]]
        if candidate["status"] not in EXECUTABLE or task.get("scope", entry["scope"]) != entry["scope"]:
            continue
        if not matches_context(task, context):
            continue
        dependencies_done = all(known[dep]["status"] == "done" for dep in task.get("depends_on", []))
        if task.get("approved", True) and not task.get("selection_blocked") and dependencies_done:
            return {"action": "would_continue", "command": "CONTINUE-AUTO", "task_id": task["id"]}
        blocked.append(task["id"])
    return {"action": "would_need_input", "blocked_task_ids": blocked, "reason": "no_executable_context_task"}


def render_needs(needs: list[dict]) -> str:
    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    lines = ["| Zadanie | Czego potrzebuję | Jak sprawdzić | Co blokuje |", "|---|---|---|---|"]
    lines.extend("| " + " | ".join(cell(row[key]) for key in ("id", "needed", "how", "blocks")) + " |" for row in validate_needs(needs))
    return "\n".join(lines)
