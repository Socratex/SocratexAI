#!/usr/bin/env python3
"""Validate that changed code work has loaded the compiled code-guidance context."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from context_gate_helpers import changed_code_paths, configure_stdio, gate_age_minutes, git_head, load_json  # noqa: E402


REQUIRED_TAGS = {
    "engineering",
    "coding",
    "architecture",
    "best-practices",
    "borrowed-before-invented",
    "production-grade",
    "ddd-adiv",
    "future-first",
    "data-first",
    "runtime",
    "diagnostics",
    "performance",
    "verification",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--max-age-minutes", "-MaxAgeMinutes", type=int, default=0)
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    code_paths = changed_code_paths(repo_root, args.paths)
    if not code_paths:
        print("OK: no changed code paths require compiled code-guidance context.")
        return 0

    gate_path = repo_root / "ignored/code_context_gate.json"
    if not gate_path.is_file():
        return fail("Changed code paths require a fresh full compiled code-guidance load. Run tools/knowledge/knowledge_code_context.py before code work.")

    gate = load_json(gate_path)
    if not gate.get("full_base_loaded"):
        return fail("Code context gate marker does not confirm a full base code-guidance load. Run tools/knowledge/knowledge_code_context.py.")

    if args.max_age_minutes > 0:
        age_minutes = gate_age_minutes(str(gate.get("loaded_at", "")))
        if age_minutes > args.max_age_minutes:
            return fail(f"Code context gate marker is stale ({age_minutes:.1f} minutes old). Run tools/knowledge/knowledge_code_context.py again.")

    current_head = git_head(repo_root)
    if current_head and str(gate.get("repo_head", "")) != current_head:
        return fail("Code context gate marker was loaded for a different HEAD. Run tools/knowledge/knowledge_code_context.py again.")

    selected_tags = {str(tag) for tag in gate.get("selected_tags", [])}
    missing_tags = sorted(REQUIRED_TAGS - selected_tags)
    if missing_tags:
        return fail("Code context gate marker is missing required tags: " + ", ".join(missing_tags) + ". Run tools/knowledge/knowledge_code_context.py.")

    print("OK: full compiled code-guidance context loaded for changed code paths.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

