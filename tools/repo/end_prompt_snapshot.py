#!/usr/bin/env python3
"""Write an end-of-task OUTPUT snapshot without PowerShell."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


LINE_WARNING = "will be replaced by"


def repo_root(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()
    return start.resolve()


def run_lines(command: list[str], cwd: Path) -> list[str]:
    try:
        completed = subprocess.run(command, cwd=cwd, check=False, capture_output=True, text=True)
    except OSError as exc:
        return [f"command failed: {' '.join(command)}", str(exc)]
    lines = [
        line
        for line in (completed.stdout + completed.stderr).splitlines()
        if LINE_WARNING not in line and not line.lstrip().startswith("warning:")
    ]
    if completed.returncode != 0:
        return [f"command failed: {' '.join(command)}", f"exit code: {completed.returncode}", *lines]
    return lines


def add_section(lines: list[str], title: str) -> None:
    lines.append("")
    lines.append(f"## {title}")


def add_command(lines: list[str], title: str, command: list[str], cwd: Path, max_lines: int) -> None:
    add_section(lines, title)
    output = run_lines(command, cwd)
    if not output:
        lines.append("(no output)")
        return
    lines.extend(output[:max_lines])
    if len(output) > max_lines:
        lines.append(f"... truncated {len(output) - max_lines} lines")


def recent_changed_files(root: Path, limit: int) -> list[str]:
    changed = run_lines(["git", "diff", "--name-only", "HEAD"], root)
    untracked = run_lines(["git", "ls-files", "--others", "--exclude-standard"], root)
    return sorted({line.strip() for line in changed + untracked if line.strip() and not line.startswith("command failed:")})[:limit]


def read_tail(path: Path, limit: int) -> list[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    except OSError as exc:
        return [str(exc)]


def add_quality_log(lines: list[str], root: Path) -> None:
    add_section(lines, "Last Quality Gate Log")
    candidates: list[Path] = []
    for search_root in (root / "Tools" / "tmp", root / "logs", root):
        if not search_root.exists():
            continue
        for path in search_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".log", ".txt", ".out"}:
                continue
            lower_name = path.name.lower()
            if any(token in lower_name for token in ("quality", "gate", "gdlint", "gdformat", "headless")):
                candidates.append(path)
    if not candidates:
        lines.append("No quality gate log file found.")
        return
    latest = max(candidates, key=lambda path: path.stat().st_mtime)
    modified = datetime.fromtimestamp(latest.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"File: {latest}")
    lines.append(f"Modified: {modified}")
    tail = read_tail(latest, 80)
    lines.extend(tail if tail else ["(empty)"])


def add_console_log(lines: list[str], root: Path) -> None:
    add_section(lines, "CONSOLE-LOG Errors And Warnings")
    path = root / "CONSOLE-LOG"
    if not path.is_file():
        lines.append("CONSOLE-LOG is missing.")
        return
    modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    lines.append("Present: yes")
    lines.append(f"Modified: {modified}")
    matches = [
        f"{index}: {line}"
        for index, line in enumerate(read_tail(path, 5000), start=1)
        if any(token in line.upper() for token in ("ERROR", "WARNING", "SCRIPT ERROR", "GDSCRIPT BACKTRACE"))
    ][-80:]
    lines.extend(matches if matches else ["No ERROR/WARNING lines found."])


def add_debug_log_pairs(lines: list[str], root: Path, max_items: int) -> None:
    add_section(lines, "Debug Log Pairs")
    logs_root = root / "logs"
    if not logs_root.exists():
        lines.append("logs/ is missing.")
        return
    json_logs = sorted(logs_root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)[:max_items]
    if not json_logs:
        lines.append("No root logs/*.json debug dumps found.")
    for log in json_logs:
        modified = datetime.fromtimestamp(log.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        png_status = "png=yes" if log.with_suffix(".png").is_file() else "png=no"
        lines.append(f"{modified} {log.name} {png_status}")
    diagnostics_root = root / "logs-diagnostics"
    if diagnostics_root.exists():
        diagnostics = sorted(
            [path for path in diagnostics_root.iterdir() if path.is_file()],
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )[:max_items]
        if diagnostics:
            lines.append("")
            lines.append("Diagnostics:")
            for path in diagnostics:
                modified = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                lines.append(f"{modified} {path.name}")


def item_text(item: Any) -> list[str]:
    if isinstance(item, dict):
        if isinstance(item.get("content"), str):
            return item["content"].splitlines()
        if isinstance(item.get("value"), list):
            return [str(value) for value in item["value"]]
        if "value" in item:
            return str(item["value"]).splitlines()
    if isinstance(item, str):
        return item.splitlines()
    return [json.dumps(item, ensure_ascii=False)]


def add_state_summary(lines: list[str], root: Path, tail_lines: int) -> None:
    add_section(lines, "docs-tech/STATE.json Summary")
    state_path = root / "docs-tech" / "STATE.json"
    if not state_path.is_file():
        lines.append("docs-tech/STATE.json is missing.")
        return
    try:
        document = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        lines.append("JSON reader unavailable; using raw tail fallback.")
        lines.extend(read_tail(state_path, tail_lines))
        return
    content = document.get("content") if isinstance(document, dict) else {}
    if not isinstance(content, dict):
        lines.extend(read_tail(state_path, tail_lines))
        return
    for selector in ("current", "immediate_focus", "risks"):
        lines.append("")
        lines.append(f"### {selector}")
        section_lines = item_text(content.get(selector, "(missing)"))
        lines.extend(section_lines[:tail_lines])


def main() -> int:
    parser = argparse.ArgumentParser(description="Write an end-of-task OUTPUT snapshot.")
    parser.add_argument("--root", default="", help="Repository root. Defaults to the current git worktree.")
    parser.add_argument("--output-path", default="", help="Output path. Defaults to OUTPUT in the root.")
    parser.add_argument("--state-tail-lines", type=int, default=80)
    parser.add_argument("--max-list-items", type=int, default=40)
    parser.add_argument("--no-sound", action="store_true", help="Accepted for CLI parity; Python path does not play a sound.")
    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else repo_root(Path.cwd())
    output_path = Path(args.output_path).resolve() if args.output_path else root / "OUTPUT"
    now = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    lines = ["# Prompt Snapshot", f"Generated: {now}", f"Repository: {root}"]
    add_command(lines, "Git Branch", ["git", "branch", "--show-current"], root, 10)
    add_command(lines, "Last Commit", ["git", "log", "-1", "--oneline", "--decorate"], root, 10)
    add_command(lines, "Git Status Short", ["git", "status", "--short"], root, 120)
    add_command(lines, "Staged Diff Summary", ["git", "diff", "--cached", "--stat"], root, 80)
    add_command(lines, "Unstaged Diff Summary", ["git", "diff", "--stat"], root, 80)

    add_section(lines, "Recently Changed Files")
    recent_files = recent_changed_files(root, args.max_list_items)
    lines.extend(recent_files if recent_files else ["(none)"])
    add_command(lines, "Untracked Files", ["git", "ls-files", "--others", "--exclude-standard"], root, 120)
    add_quality_log(lines, root)
    add_console_log(lines, root)
    add_debug_log_pairs(lines, root, args.max_list_items)
    add_state_summary(lines, root, args.state_tail_lines)

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"Prompt snapshot written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
