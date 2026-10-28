"""Materialize per-chat AUTO instructions, progress and summaries from durable state."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import uuid
from pathlib import Path

_TEXT_TOOLS = Path(__file__).resolve().parents[1] / "text"
if str(_TEXT_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TEXT_TOOLS))
from utf8_file_helpers import write_utf8_file


def directory_name(identifier: str) -> str:
    if re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", identifier):
        return identifier
    return "id-" + hashlib.sha256(identifier.encode("utf-8")).hexdigest()


def paths(home: Path, thread_id: str, run_id: str) -> dict:
    folder = home / "threads" / directory_name(thread_id)
    run = folder / "runs" / directory_name(run_id)
    return {"folder": str(folder), "instructions": str(folder / "instructions.md"),
            "thread": str(folder / "thread.json"), "tasks": str(folder / "tasks.json"), "progress": str(run / "progress.json"),
            "summary": str(run / "SUMMARY.md")}


def progress_record(entry: dict) -> dict:
    steps = entry.get("completed_steps", [])
    needs = {row["id"]: row for row in entry.get("pending_needs", [])}
    needs.update({row["id"]: row for row in entry.get("needs", [])})
    return {"thread_id": entry["thread_id"], "run_id": entry["run_id"], "repo": entry["repo"],
            "scope": entry["scope"], "sources": entry["sources"], "state": entry["state"],
            "prompt_context": entry.get("prompt_context", ""),
            "grant_amendments": entry.get("grant_amendments", []),
            "completed": entry["completed"], "batch_size": entry["batch_size"],
            "steps": steps, "inflight": entry.get("inflight"), "checkpoint": entry.get("checkpoint"),
            "task_projection": entry.get("task_projection", []),
            "needs": list(needs.values()),
            "recovery": entry.get("recovery"),
            "unrecorded_completed": max(0, entry["completed"] - len(steps))}


def summary(record: dict) -> str:
    def cell(value: object) -> str:
        return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
    states = {"registered": "gotowe", "executing": "w toku", "waiting_turn_end": "oczekuje na kontynuację",
              "waiting_limit": "oczekuje na limit", "needs_input": "potrzebny operator", "stopped": "zatrzymane",
              "batch_complete": "batch zakończony", "pilot_complete": "pilot zakończony", "queue_complete": "kolejka zakończona"}
    lines = ["# 📊 Postęp AUTO", "", f"📌 Stan: **{states.get(record['state'], record['state'])}**; wykonano **{record['completed']}/{record['batch_size']}**.",
             f"🎯 Zakres: {record['scope']}", f"🧵 Czat: `{record['thread_id']}`; uruchomienie: `{record['run_id']}`.",
             "", "## ✅ Wykonano", "", "| Zadanie | Wynik | Weryfikacja | Commit |", "|---|---|---|---|"]
    for step in record["steps"]:
        values = [step["task_id"], step["summary"], "; ".join(step.get("verification", [])) or "Wnioski i wskazane dowody",
                  step.get("commit") or "—"]
        lines.append("| " + " | ".join(cell(value) for value in values) + " |")
    if not record["steps"]:
        lines.append("| — | Brak zapisanych ukończonych kroków | — | — |")
    if record["unrecorded_completed"]:
        lines += ["", f"🗃️ Starszy zapis potwierdza jeszcze {record['unrecorded_completed']} ukończone kroki bez szczegółowych raportów. Nie odtworzono ich przez zgadywanie."]
    if record.get("inflight"):
        lines += ["", f"🔧 Bieżące zadanie: **{record['inflight']['task_id']}**; nie jest jeszcze ukończone."]
    lines += ["", "## 🧾 Wnioski", "", "📝 " + (record.get("checkpoint") or "Brak zakończonej finalizacji.")]
    lines += ["", "## 👤 Potrzebne", ""]
    if record["needs"]:
        lines += ["| Zadanie | Czego potrzebuję | Jak sprawdzić | Co blokuje |", "|---|---|---|---|"]
        for row in record["needs"]:
            lines.append("| " + " | ".join(cell(row[key]) for key in ("id", "needed", "how", "blocks")) + " |")
    else:
        lines.append("📌 Nie zapisano aktualnych próśb do operatora.")
    return "\n".join(lines) + "\n"


def write_projection(path: Path, text: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        write_utf8_file(temporary, text)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def synchronize(home: Path, data: dict) -> None:
    from .native import render_instructions
    for thread_id, runs in data.get("runs", {}).items():
        for run_id, record in runs.items():
            located = paths(home, thread_id, run_id)
            write_projection(Path(located["progress"]), json.dumps(record, ensure_ascii=False, indent=4) + "\n")
            write_projection(Path(located["summary"]), summary(record))
    for entry in data["threads"].values():
        located = paths(home, entry["thread_id"], entry["run_id"])
        configuration = {key: entry.get(key) for key in ("thread_id", "run_id", "repo", "scope", "sources", "mode",
                         "enabled", "state", "batch_size", "completed", "scheduler_id", "prompt_context", "task_policy_version", "last_prompt_context", "wake_transport", "grant_amendments")}
        configuration.update(files=located, source_registry=str(home / "registry.json"))
        configuration["recovery"] = entry.get("recovery")
        write_projection(Path(located["thread"]), json.dumps(configuration, ensure_ascii=False, indent=4) + "\n")
        projection = entry.get("task_projection", [])
        queue = {"thread_id": entry["thread_id"], "run_id": entry["run_id"],
                 **(projection if isinstance(projection, dict) else {"tasks": projection})}
        write_projection(Path(located["tasks"]), json.dumps(queue, ensure_ascii=False, indent=4) + "\n")
        write_projection(Path(located["instructions"]), render_instructions(entry))
