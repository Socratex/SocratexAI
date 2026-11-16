"""Read local chat identities, then require native runtime status for every identity."""

import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path

from .controller import project_path


def read_roster(repo: str, database: Path | None = None) -> dict:
    if database is None:
        home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        candidates = [path for path in home.glob("state_*.sqlite") if path.stem.removeprefix("state_").isdigit()]
        if not candidates:
            raise ValueError("Local Codex thread index was not found")
        database = max(candidates, key=lambda path: int(path.stem.removeprefix("state_")))
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")}
        if not {"id", "cwd", "archived"}.issubset(columns):
            raise ValueError("Unsupported local Codex thread-index schema")
        rows = connection.execute("SELECT id, cwd FROM threads WHERE archived = 0").fetchall()
    root = project_path(repo)
    return {"repo": root, "observed_at": time.time(), "source": "local_identity_index_only",
            "threads": [{"id": identifier, "cwd": root} for identifier, cwd in rows if project_path(cwd) == root]}


def complete_inventory(entry: dict, roster: dict, observations: list[dict], recent: dict, now: float) -> dict:
    from .native import payload
    if project_path(roster.get("repo", "")) != entry["repo"] or not 0 <= now - roster.get("observed_at", 0) <= 90:
        raise ValueError("Project identity roster is stale or foreign")
    identities = {item["id"] for item in roster["threads"]}
    if entry["thread_id"] not in identities:
        raise ValueError("Registered thread is missing from the local identity roster")
    recent = payload(recent)
    if recent.get("unavailableHosts") or recent.get("unavailableSources"):
        raise ValueError("Recent native inventory has unavailable sources")
    states = {item["id"]: item["status"] for item in recent.get("pinnedThreads", []) + recent.get("threads", [])
              if item.get("kind") == "codex" and project_path(item.get("cwd", "")) == entry["repo"]}
    for raw in observations:
        block = payload(raw)
        if not 0 <= now - block.get("observed_at", 0) <= 90:
            raise ValueError("Native runtime statuses are stale")
        if block.get("errors"):
            raise ValueError("Some native thread status reads failed")
        for poll in block.get("polls", []):
            thread = poll["thread"]
            status = thread["status"]["type"]
            if status not in {"active", "idle", "notLoaded", "systemError"}:
                raise ValueError("Unknown native runtime status")
            if states.get(thread["id"]) != "active":
                states[thread["id"]] = status
    if not identities.issubset(states):
        raise ValueError("Native runtime status is missing for project roster identities")
    threads = {identifier: {"id": identifier, "cwd": entry["repo"], "kind": "codex", "status": states[identifier]}
               for identifier in identities}
    for item in recent.get("pinnedThreads", []) + recent.get("threads", []):
        if item.get("kind") == "codex" and project_path(item.get("cwd", "")) == entry["repo"]:
            previous = threads.get(item["id"])
            if previous and previous["status"] == "active":
                continue
            threads[item["id"]] = item
    return {"threads": list(threads.values()), "pinnedThreads": [], "unavailableHosts": [], "unavailableSources": [],
            "complete_project_roster": True}
