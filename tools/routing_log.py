#!/usr/bin/env python3
"""Append one task outcome to audits/routing_log.jsonl (the router feedback loop).

The router calls this once per finished task. Risk comes from risk_score.py (deterministic);
the outcome fields come from the router's own record of the task. routing_stats.py reads the log.

Usage:
    routing_log.py --type implementation --tier standard --agent implementer --effort medium \
        --first-pass yes --fixes 0 --escalated no --commit HEAD [--task qv6lrl] [--regression-of abc123]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import risk_score  # noqa: E402

LOG_PATH = risk_score.ROOT / "audits" / "routing_log.jsonl"
TASK_TYPES = ("search", "implementation", "refactor", "docs", "debug", "review", "plan", "ops")
TIERS = ("cheap", "standard", "high", "top")
EFFORTS = ("low", "medium", "high", "xhigh", "max", "default")
AREA_DEPTH = 3
MAX_AREAS = 8


def areas(paths: list[str]) -> list[str]:
    """Folder prefixes of changed paths, so the stats can find risky areas without storing every file."""
    seen: list[str] = []
    for path in paths:
        parts = path.split("/")
        area = "/".join(parts[:AREA_DEPTH]) if len(parts) > AREA_DEPTH else "/".join(parts[:-1]) or path
        if area not in seen:
            seen.append(area)
    return seen[:MAX_AREAS]


def build_entry(args: argparse.Namespace, changes: list[risk_score.FileChange], risk: dict) -> dict:
    return {
        "date": dt.date.today().isoformat(),
        "task": args.task,
        "type": args.type,
        "tier": args.tier,
        "agent": args.agent,
        "effort": args.effort,
        "risk": risk["score"],
        "level": risk["level"],
        "first_pass": args.first_pass == "yes",
        "fixes": args.fixes,
        "escalated": args.escalated == "yes",
        "regression_of": args.regression_of,
        "areas": areas([change.path for change in changes]),
    }


def append(entry: dict, path: Path = LOG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Record one task outcome for the router feedback loop.")
    parser.add_argument("--type", choices=TASK_TYPES, required=True)
    parser.add_argument("--tier", choices=TIERS, required=True, help="Tier that did the main work.")
    parser.add_argument("--agent", default="router", help="Agent name (scout, implementer, planner, reviewer, router, codex).")
    parser.add_argument("--effort", choices=EFFORTS, default="default")
    parser.add_argument("--first-pass", choices=("yes", "no"), required=True, help="Passed its verification on the first try.")
    parser.add_argument("--fixes", type=int, default=0, help="Fix rounds after the first verification.")
    parser.add_argument("--escalated", choices=("yes", "no"), default="no")
    parser.add_argument("--task", help="Task short code, if any.")
    parser.add_argument("--regression-of", help="Task code or commit whose change this task repairs.")
    parser.add_argument("--commit", help="Commit to score; default is the working tree.")
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--attempt", type=int, default=1)
    parser.add_argument("--dry-run", action="store_true", help="Print the entry without writing it.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    rules = risk_score.load_rules()
    changes = risk_score.relevant(risk_score.collect_changes(args.commit, args.paths), rules)
    risk = risk_score.score_changes(changes, rules, tier=args.tier, attempt=args.attempt)
    entry = build_entry(args, changes, risk)
    if not args.dry_run:
        append(entry)
    print(json.dumps(entry, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
