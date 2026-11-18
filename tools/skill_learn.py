#!/usr/bin/env python3
"""Learnings log for skills: the capture half of the self-improving skill loop.

Each skill keeps its own LEARNINGS.jsonl next to SKILL.md. Agents never load it while using the skill,
so capture costs nothing per session. The skill-reflect skill reads only the skills this tool marks READY
and turns their open entries into small, owner-approved edits of SKILL.md (delta updates, never rewrites).

Repeated notes are merged deterministically (similarity check) and counted, so the log does not grow
with duplicates and the count shows how often a problem really happens.

Usage:
    skill_learn.py add --skill spec --kind correction --note "Owner wants the form before reading code"
    skill_learn.py status                 # one line per skill with open entries
    skill_learn.py show --skill spec      # open entries of one skill, compact
    skill_learn.py close --skill spec --ids a1b2c3 d4e5f6 --as applied
"""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import re
import sys
from pathlib import Path

SOCRATEX = Path(__file__).resolve().parents[1]
LOG_NAME = "LEARNINGS.jsonl"
KINDS = ("correction", "failure", "workaround", "misfire", "win")
CLOSED_STATES = ("applied", "rejected")
SIMILARITY = 0.85
READY_OPEN = 3  # open entries (counting repeats) that make a skill worth a reflect pass
MAX_NOTE = 240


def skill_roots(project: Path | None = None) -> list[Path]:
    """Folders that hold skills we own. Plugin skills are not ours and are never edited."""
    roots = [SOCRATEX / "skills", SOCRATEX / "claude" / "skills"]
    start = (project or Path.cwd()).resolve()
    for folder in (start, *start.parents):
        candidate = folder / ".claude" / "skills"
        if candidate.is_dir():
            roots.append(candidate)
            break
    return [root for root in roots if root.is_dir()]


def find_skill(name: str, roots: list[Path]) -> Path | None:
    for root in roots:
        folder = root / name
        if (folder / "SKILL.md").is_file():
            return folder
    return None


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


def entry_id(skill: str, note: str) -> str:
    return hashlib.sha1(f"{skill}:{normalize(note)}".encode()).hexdigest()[:6]


def load(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save(path: Path, entries: list[dict]) -> None:
    text = "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in entries)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def similar(left: str, right: str) -> bool:
    return difflib.SequenceMatcher(None, normalize(left), normalize(right)).ratio() >= SIMILARITY


def add(entries: list[dict], skill: str, kind: str, note: str, today: str) -> tuple[dict, bool]:
    """Merge into a similar open entry of the same kind, or append a new one. Returns (entry, merged)."""
    note = " ".join(note.split())[:MAX_NOTE]
    for entry in entries:
        # A rejected idea is counted on its old entry instead of coming back as new work.
        if entry["status"] in ("open", "rejected") and entry["kind"] == kind and similar(entry["note"], note):
            entry["count"] += 1
            entry["last"] = today
            return entry, True
    entry = {"id": entry_id(skill, note), "kind": kind, "note": note, "count": 1,
             "first": today, "last": today, "status": "open"}
    entries.append(entry)
    return entry, False


def open_weight(entries: list[dict]) -> int:
    return sum(entry["count"] for entry in entries if entry["status"] == "open" and entry["kind"] != "win")


def is_ready(entries: list[dict]) -> bool:
    """A repeated correction is enough; otherwise wait for several open problems to batch the pass."""
    if any(e["status"] == "open" and e["kind"] == "correction" and e["count"] >= 2 for e in entries):
        return True
    return open_weight(entries) >= READY_OPEN


def close(entries: list[dict], ids: list[str], state: str, today: str) -> list[str]:
    done = []
    for entry in entries:
        if entry["id"] in ids and entry["status"] == "open":
            entry["status"] = state
            entry["closed"] = today
            done.append(entry["id"])
    return done


def all_logs(roots: list[Path]) -> list[tuple[str, Path]]:
    found = []
    for root in roots:
        for log in sorted(root.glob(f"*/{LOG_NAME}")):
            found.append((log.parent.name, log))
    return found


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture and manage skill learnings.")
    parser.add_argument("--project", type=Path, help="Project folder for project skills; default is the cwd.")
    sub = parser.add_subparsers(dest="command", required=True)
    p_add = sub.add_parser("add", help="Record one learning.")
    p_add.add_argument("--skill", required=True)
    p_add.add_argument("--kind", choices=KINDS, required=True)
    p_add.add_argument("--note", required=True, help="One sentence: what went wrong and what works instead.")
    sub.add_parser("status", help="Skills with open learnings.")
    p_show = sub.add_parser("show", help="Open learnings of one skill.")
    p_show.add_argument("--skill", required=True)
    p_close = sub.add_parser("close", help="Mark learnings applied or rejected.")
    p_close.add_argument("--skill", required=True)
    p_close.add_argument("--ids", nargs="+", required=True)
    p_close.add_argument("--as", dest="state", choices=CLOSED_STATES, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    roots = skill_roots(args.project)
    today = dt.date.today().isoformat()

    if args.command == "status":
        lines = []
        for name, log in all_logs(roots):
            entries = load(log)
            weight = open_weight(entries)
            if weight:
                lines.append(f"{'READY' if is_ready(entries) else 'wait '} {name}: {weight} open")
        print("\n".join(lines) if lines else "no open skill learnings")
        return 0

    folder = find_skill(args.skill, roots)
    if folder is None:
        print(f"unknown skill '{args.skill}' (only own skills in: {', '.join(str(r) for r in roots)})", file=sys.stderr)
        return 2
    log = folder / LOG_NAME
    entries = load(log)

    if args.command == "add":
        entry, merged = add(entries, args.skill, args.kind, args.note, today)
        save(log, entries)
        state = "merged into rejected" if entry["status"] == "rejected" else "merged" if merged else "added"
        print(f"{state} {entry['id']} x{entry['count']}" + (" READY" if is_ready(entries) else ""))
    elif args.command == "show":
        for entry in entries:
            recurring_rejected = entry["status"] == "rejected" and entry["count"] >= READY_OPEN
            if entry["status"] == "open" or recurring_rejected:
                mark = " (rejected before)" if recurring_rejected else ""
                print(f"{entry['id']} {entry['kind']} x{entry['count']} {entry['last']}{mark}: {entry['note']}")
    elif args.command == "close":
        done = close(entries, args.ids, args.state, today)
        save(log, entries)
        missing = sorted(set(args.ids) - set(done))
        print(f"{args.state}: {' '.join(done) or '-'}" + (f"; not open: {' '.join(missing)}" if missing else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
