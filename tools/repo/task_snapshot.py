#!/usr/bin/env python3
"""Print a compact task snapshot for repository finalization workflows."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from repo_tool_helpers import repo_root


LINE_WARNING = "will be replaced by"
SNAPSHOT_FILES = (
    "DOCS.json",
    "STATE.json",
    "_PLAN.json",
    "TODO.json",
    "BUGS.json",
    "STATE.md",
    "_PLAN.md",
    "TODO.md",
    "ISSUES.md",
)


def command_lines(command: list[str], cwd: Path, max_lines: int) -> list[str]:
    completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    lines = [line for line in (completed.stdout + completed.stderr).splitlines() if LINE_WARNING not in line]
    if completed.returncode != 0:
        lines = [f"command failed: {' '.join(command)}", f"exit code: {completed.returncode}", *lines]
    if not lines:
        return ["(no output)"]
    if len(lines) > max_lines:
        return [*lines[:max_lines], f"... truncated {len(lines) - max_lines} lines"]
    return lines


def print_section(title: str, lines: list[str]) -> None:
    print()
    print(f"## {title}")
    for line in lines:
        print(line)


def count_lines(path: Path) -> int:
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        return sum(1 for _ in handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a compact task snapshot.")
    parser.add_argument("--root", default="", help="Repository root. Defaults to the current git worktree.")
    parser.add_argument("--max-lines", type=int, default=120, help="Maximum lines per command section.")
    parser.add_argument("--no-git", action="store_true", help="Skip git state sections.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root(Path.cwd())
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    print("# Task Snapshot")
    print(f"Generated: {now}")
    print(f"Repository: {root}")

    if not args.no_git and (root / ".git").exists():
        print_section("Git Branch", command_lines(["git", "branch", "--show-current"], root, 10))
        print_section("Last Commit", command_lines(["git", "log", "-1", "--oneline", "--decorate"], root, 10))
        print_section("Git Status Short", command_lines(["git", "status", "--short"], root, args.max_lines))
        print_section("Staged Diff Summary", command_lines(["git", "diff", "--cached", "--stat"], root, args.max_lines))
        print_section("Unstaged Diff Summary", command_lines(["git", "diff", "--stat"], root, args.max_lines))
        print_section("Untracked Files", command_lines(["git", "ls-files", "--others", "--exclude-standard"], root, args.max_lines))

    for relative in SNAPSHOT_FILES:
        path = root / relative
        if path.is_file():
            print(f"{relative}: {count_lines(path)} line(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
