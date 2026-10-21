"""Explicit finalizer adapter; an inactive pilot never affects ordinary task closure."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .controller import Registry, validate_native_receipt, validate_progress


def validate_handoff(thread_id: str | None, run_id: str | None, report_path: str | None, repo: Path) -> None:
    values = (thread_id, run_id, report_path)
    if not any(values):
        return
    if not all(values):
        raise ValueError("AUTO handoff requires thread ID, run ID and report file together")
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    from .controller import nonempty, project_path, validate_needs
    entry = Registry().get(thread_id)
    if entry["run_id"] != run_id or entry["repo"] != project_path(repo):
        raise ValueError("AUTO finalizer identity does not match the registered run/project")
    if report.get("decision") not in {"continue", "needs_input"}:
        raise ValueError("Invalid AUTO finalizer decision")
    nonempty(report.get("checkpoint"), "checkpoint")
    nonempty(report.get("receipt_id"), "receipt_id")
    needs = validate_needs(report.get("needs", []))
    validate_needs(report.get("pending_needs", []))
    validate_progress(report)
    validate_native_receipt(entry, report)
    if (report["decision"] == "needs_input") != bool(needs):
        raise ValueError("AUTO finalizer decision and operator needs disagree")


def complete_handoff(thread_id: str | None, run_id: str | None, report_path: str | None, repo: Path) -> dict | None:
    if not thread_id:
        return None
    report = json.loads(Path(report_path).read_text(encoding="utf-8"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=False)
    if commit.returncode == 0:
        report["commit"] = commit.stdout.strip()
    registry = Registry()
    result = registry.finalize(thread_id, run_id, report, str(repo))
    return handoff_result(registry, thread_id, run_id, result)


def handoff_result(registry: Registry, thread_id: str, run_id: str, result: dict) -> dict:
    from .controller import current_run
    from .files import paths, progress_record, summary
    from .native import scheduler_request

    with registry.transaction() as data:
        entry = current_run(data, thread_id, run_id)
        located = paths(registry.home, thread_id, run_id)
        result.update(files=located, state=entry["state"], completed=entry["completed"],
                      summary_markdown=summary(progress_record(entry)))
        if (entry["mode"] == "native" and entry.get("wake_transport") == "manual"
                and entry["enabled"] and entry["state"] == "waiting_turn_end"
                and result["action"] == "checkpoint_saved"):
            result["continuation"] = {"action": "continue_current_turn", "thread_id": thread_id,
                                      "run_id": run_id, "wake_id_suffix": f":auto:{entry['completed']}",
                                      "requires": "fresh native snapshot, task projection and native-begin"}
        # Desktop tool calls belong to the agent; Python returns the concrete next action.
        if entry["mode"] == "native" and entry.get("scheduler_id") and entry.get("wake_transport") != "manual":
            if not entry["enabled"] or entry["state"] == "waiting_turn_end":
                result["scheduler_request"] = scheduler_request(entry)
    return result
