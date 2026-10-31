"""Opt-in, one-run unattended shutdown; never execute from status or a dry run."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import time

from .controller import current_run, limit_availability, nonempty, validate_snapshot

COUNTDOWN_SECONDS = 30


def boot_marker() -> float:
    if os.name != "nt":
        return 0
    import ctypes
    kernel = ctypes.WinDLL("kernel32")
    kernel.GetTickCount64.restype = ctypes.c_ulonglong
    return time.time() - kernel.GetTickCount64() / 1000


def cancel(entry: dict, reason: str) -> None:
    policy = entry.get("shutdown_policy")
    if policy:
        policy.update(armed=False, phase="cancelled", cancel_reason=reason)


def configure(registry, thread_id: str, run_id: str, *, enabled: bool,
              approval_note: str = "", now: float | None = None, boot: float | None = None) -> dict:
    now = time.time() if now is None else now
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        if enabled:
            if entry["mode"] != "native" or not entry["enabled"]:
                raise ValueError("Shutdown requires an active native AUTO grant")
            entry["shutdown_policy"] = {"armed": True, "phase": "armed", "run_id": run_id,
                "approval_note": nonempty(approval_note, "explicit shutdown request"), "armed_at": now,
                "boot": boot_marker() if boot is None else boot, "wait_for_build": False}
        else:
            cancel(entry, "explicit_cancel")
        return {"action": "shutdown_armed" if enabled else "shutdown_cancelled", "run_id": run_id,
                "dispatch": False, "policy": dict(entry.get("shutdown_policy") or {})}


def block(registry, thread_id: str, run_id: str, reason: str) -> dict:
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        policy = entry.get("shutdown_policy") or {}
        if not policy.get("armed"):
            raise ValueError("No unattended shutdown policy is armed for this run")
        policy["blocked_reason"] = nonempty(reason, "blocked reason")
        return {"action": "shutdown_block_recorded", "reason": reason, "completed": entry["completed"],
                "checkpoint": entry.get("checkpoint"), "inflight": entry.get("inflight")}


def pending(entry: dict) -> bool:
    policy = entry.get("shutdown_policy") or {}
    if not policy:
        return False
    if abs(boot_marker() - policy["boot"]) > 5:
        return False
    return bool(policy.get("phase") in {"pending", "dispatch_reserved", "requested", "failed"}
                or policy.get("armed") and policy.get("blocked_reason"))


def reason(entry: dict, observation: dict, now: float) -> str | None:
    if entry["state"] == "stopped":
        return None
    if entry["state"] in {"batch_complete", "queue_complete"}:
        return "work_complete"
    if entry["state"] == "needs_input" or (entry.get("shutdown_policy") or {}).get("blocked_reason"):
        return "work_blocked"
    if not limit_availability(observation.get("limits"), now)[0]:
        return "account_limit"
    if observation["status"] == "systemError":
        return "work_blocked"
    return None


def advance(registry, thread_id: str, run_id: str, observation: dict, *, executor,
            dry_run: bool = False, now: float | None = None, boot: float | None = None) -> dict:
    now = time.time() if now is None else now
    boot = boot_marker() if boot is None else boot
    base = {"thread_id": thread_id, "run_id": run_id}
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        policy = entry.get("shutdown_policy") or {}
        if not policy.get("armed") or entry["mode"] != "native":
            return {**base, "action": "continue"}
        if policy.get("run_id") != run_id or not isinstance(policy.get("approval_note"), str) or not policy["approval_note"].strip():
            raise ValueError("Shutdown authorization does not match this run")
        if entry["state"] == "stopped" or abs(boot - policy["boot"]) > 5:
            if not dry_run:
                cancel(entry, "stop_or_new_boot")
            return {**base, "action": "shutdown_cancelled"}
        validate_snapshot(entry, observation, now)
        if observation.get("source") != "native_desktop_tools" or not observation.get("authoritative"):
            raise ValueError("Shutdown requires a fresh native desktop observation")
        trigger = policy.get("trigger") if policy.get("phase") == "pending" else reason(entry, observation, now)
        if trigger is None:
            return {**base, "action": "continue"}
        if (observation["status"] not in {"idle", "notLoaded", "systemError"} or observation["active_project_threads"]
                or observation.get("active_host_threads")):
            if not dry_run:
                policy.update(phase="armed")
                policy.pop("trigger", None)
            return {**base, "action": "shutdown_deferred", "reason": "thread_not_idle"}
        if dry_run:
            return {**base, "action": "would_shutdown", "trigger": trigger, "dispatch": False}
        if policy.get("phase") != "pending":
            policy.update(phase="pending", trigger=trigger, shutdown_at=now + COUNTDOWN_SECONDS)
        if now < policy["shutdown_at"]:
            return {**base, "action": "shutdown_pending", "reason": "shutdown_pending", "trigger": trigger,
                    "shutdown_at": policy["shutdown_at"]}
        # Persist a one-shot dispatch claim and the unfinished-work checkpoint before OS I/O.
        policy.update(armed=False, phase="dispatch_reserved", dispatch_at=now,
            checkpoint={"last_verified": entry.get("checkpoint"), "inflight": entry.get("inflight"),
                        "completed": entry["completed"], "reason": trigger,
                        "blocked_reason": policy.get("blocked_reason")})
    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        policy = entry.get("shutdown_policy") or {}
        if entry["state"] == "stopped" or policy.get("phase") != "dispatch_reserved":
            return {**base, "action": "shutdown_cancelled"}
        try:
            executor()
        except (OSError, RuntimeError, subprocess.SubprocessError) as error:
            policy.update(phase="failed", error=str(error))
            return {**base, "action": "shutdown_failed", "error": str(error)}
        policy["phase"] = "requested"
        return {**base, "action": "shutdown_requested", "trigger": policy["trigger"]}


def system_shutdown() -> None:
    if os.name != "nt":
        raise OSError("Automatic computer shutdown is available only on Windows")
    executable = Path(os.environ["SystemRoot"]) / "System32/shutdown.exe"
    # A positive Windows /t implicitly forces applications closed. Our countdown is above.
    subprocess.run([str(executable), "/s", "/t", "0", "/d", "p:0:0", "/c", "Socratex AUTO: progress saved"],
                   check=True, timeout=15, creationflags=subprocess.CREATE_NO_WINDOW)


def instructions(entry: dict) -> str:
    policy = entry.get("shutdown_policy") or {}
    if not policy.get("armed") or abs(boot_marker() - policy["boot"]) > 5:
        return ""
    return """
## 🌙 Tryb nocny

🌙 Jawnie włączone wyłączenie komputera dla tego runa po limicie konta, końcu partii/kolejki albo blokadzie. Nie czekaj na build. Nie zadawaj pytań i nie rozszerzaj zgody: wykonuj wyłącznie zatwierdzone zadania. Gdy brakuje koniecznej decyzji, zapisz potrzebę i checkpoint zamiast zgadywać lub otwierać pytanie.
🧾 Użyj needs_input w prawdziwym finalizerze. Jeśli błąd kontroli uniemożliwia finalizację, użyj auto.py shutdown-blocked --thread-id ID --run-id RUN --reason OPIS: zachowuje rezerwację i ostatni zweryfikowany checkpoint, bez fikcyjnego commitu/ukończenia. Zakończ turę; CMD wykryje bezczynność i wykona własne30s odliczania.
🛑 STOP AUTO albo shutdown-policy --disable anuluje tę opcję przed wysłaniem komendy systemowej. Nowy run i nowy start Windows nie dziedziczą zgody. Status/dry-run nie wyłączają komputera. Nie uruchamiaj shutdown samodzielnie ani podczas testowania tej funkcji.
"""
