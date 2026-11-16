#!/usr/bin/env python3
"""Read audits/routing_log.jsonl and propose routing changes (the LEARNED half of the loop).

Proposals only: nothing here edits MODEL-ROUTING.json or RISK-RULES.json. The router shows the
proposals to the owner in one form; approved ones are applied after a backup.

Usage:
    routing_stats.py                 # Markdown report to stdout
    routing_stats.py --json
    routing_stats.py --out audits/routing_stats_20261123.md
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import risk_score  # noqa: E402

ROOT = risk_score.ROOT
LOG_PATH = ROOT / "audits" / "routing_log.jsonl"

MIN_SAMPLE = 10
GOOD_RATE = 0.90
BAD_RATE = 0.70
BAD_ESCALATION_RATE = 0.30
HIGH_TIER_SHARE = 0.15
EFFORT_TOLERANCE = 0.05
TIER_ORDER = ("cheap", "standard", "high", "top")
EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")


def load(path: Path = LOG_PATH) -> list[dict]:
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except ValueError:
                continue  # one broken line must not hide the rest
    return entries


def rate(entries: list[dict]) -> float:
    return sum(1 for entry in entries if entry["first_pass"]) / len(entries)


def tier_proposals(entries: list[dict]) -> list[str]:
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for entry in entries:
        groups[(entry["type"], entry["tier"])].append(entry)
    proposals = []
    for (task_type, tier), group in sorted(groups.items()):
        if len(group) < MIN_SAMPLE:
            continue
        first_pass = rate(group)
        escalations = sum(1 for entry in group if entry["escalated"]) / len(group)
        index = TIER_ORDER.index(tier)
        if (first_pass < BAD_RATE or escalations > BAD_ESCALATION_RATE) and index + 1 < len(TIER_ORDER) - 1:
            proposals.append(f"{task_type}: move default from {tier} to {TIER_ORDER[index + 1]} "
                             f"(first pass {first_pass:.0%}, escalated {escalations:.0%}, n={len(group)})")
        elif first_pass >= GOOD_RATE and index > 0 and tier != "top":
            proposals.append(f"{task_type}: try {TIER_ORDER[index - 1]} instead of {tier} on the next tasks "
                             f"(first pass {first_pass:.0%}, n={len(group)})")
    return proposals


def high_tier_proposal(entries: list[dict]) -> list[str]:
    if len(entries) < MIN_SAMPLE:
        return []
    share = sum(1 for entry in entries if entry["tier"] in ("high", "top")) / len(entries)
    if share > HIGH_TIER_SHARE:
        return [f"high/top tier does {share:.0%} of tasks (limit {HIGH_TIER_SHARE:.0%}): routing is too conservative, review task types"]
    return []


def effort_proposals(entries: list[dict]) -> list[str]:
    groups: dict[tuple[str, str], dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for entry in entries:
        if entry.get("effort") in EFFORT_ORDER:
            groups[(entry["type"], entry["tier"])][entry["effort"]].append(entry)
    proposals = []
    for (task_type, tier), by_effort in sorted(groups.items()):
        ranked = [(effort, by_effort[effort]) for effort in EFFORT_ORDER if len(by_effort.get(effort, [])) >= MIN_SAMPLE]
        for (low, low_group), (high, high_group) in zip(ranked, ranked[1:]):
            if rate(low_group) >= rate(high_group) - EFFORT_TOLERANCE:
                proposals.append(f"{task_type}/{tier}: effort {low} does as well as {high} "
                                 f"({rate(low_group):.0%} vs {rate(high_group):.0%}); default to {low}")
    return proposals


def risk_proposals(entries: list[dict]) -> list[str]:
    by_task = {entry["task"]: entry for entry in entries if entry.get("task")}
    proposals = []
    missed: dict[str, int] = defaultdict(int)
    for entry in entries:
        source = by_task.get(entry.get("regression_of") or "")
        if source and source["level"] in ("LIGHT", "STANDARD"):
            for area in source.get("areas", []):
                missed[area] += 1
    for area, count in sorted(missed.items()):
        proposals.append(f"add learned rule '{area}/*' +1 risk point ({count} regression(s) slipped past LIGHT/STANDARD)")

    regressed = {entry.get("regression_of") for entry in entries if entry.get("regression_of")}
    full_by_area: dict[str, list[dict]] = defaultdict(list)
    for entry in entries:
        if entry["level"] == "FULL":
            for area in entry.get("areas", []):
                full_by_area[area].append(entry)
    for area, group in sorted(full_by_area.items()):
        clean = all(entry["first_pass"] and entry["fixes"] == 0 and entry.get("task") not in regressed for entry in group)
        if len(group) >= MIN_SAMPLE and clean:
            proposals.append(f"area '{area}': {len(group)} FULL reviews found nothing; consider -1 risk point")
    return proposals


def summarize(entries: list[dict]) -> dict:
    levels = defaultdict(int)
    for entry in entries:
        levels[entry["level"]] += 1
    proposals = tier_proposals(entries) + high_tier_proposal(entries) + effort_proposals(entries) + risk_proposals(entries)
    return {
        "tasks": len(entries),
        "first_pass_rate": round(rate(entries), 3) if entries else None,
        "levels": dict(levels),
        "regressions": sum(1 for entry in entries if entry.get("regression_of")),
        "min_sample": MIN_SAMPLE,
        "proposals": proposals,
    }


def to_markdown(summary: dict) -> str:
    lines = [
        "# Routing stats",
        "",
        f"- Tasks logged: {summary['tasks']}",
        f"- First pass rate: {summary['first_pass_rate']:.0%}" if summary["first_pass_rate"] is not None else "- First pass rate: no data",
        f"- Verification levels: {summary['levels'] or 'none'}",
        f"- Regressions recorded: {summary['regressions']}",
        "",
        "## Proposals (owner approval required)",
        "",
    ]
    lines += [f"- {proposal}" for proposal in summary["proposals"]] or [f"- None yet (groups need at least {summary['min_sample']} tasks)."]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Propose routing changes from logged task outcomes.")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", help="Also write the Markdown report to this path.")
    args = parser.parse_args()
    summary = summarize(load())
    report = to_markdown(summary)
    if args.out:
        out = Path(args.out)
        (out if out.is_absolute() else ROOT / out).write_text(report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False) if args.json else report, end="" if not args.json else "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
