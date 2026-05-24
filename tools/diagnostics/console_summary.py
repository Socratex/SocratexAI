#!/usr/bin/env python3
"""Summarize the project CONSOLE-LOG into a compact text report."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--console-log-path", "-ConsoleLogPath", default="")
    parser.add_argument("--output-path", "-OutputPath", default="")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    console_log_path = Path(args.console_log_path).resolve() if args.console_log_path else repo_root / "CONSOLE-LOG"
    output_path = Path(args.output_path).resolve() if args.output_path else repo_root / "CONSOLE-LOG-SUMMARY"

    lines = [
        "# Console Log Summary",
        f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}",
        f"Source: {console_log_path}",
    ]
    if not console_log_path.exists():
        lines.extend(["", "CONSOLE-LOG is missing."])
        write_lines(output_path, lines)
        print(f"Console summary written to: {output_path}")
        return 0

    content = read_lines(console_log_path)
    problem_re = re.compile(r"ERROR|SCRIPT ERROR|WARNING", re.IGNORECASE)
    error_re = re.compile(r"ERROR|SCRIPT ERROR", re.IGNORECASE)
    warning_re = re.compile(r"WARNING", re.IGNORECASE)
    startup_re = re.compile(r"engine startup|graphics backend ", re.IGNORECASE)
    backtrace_re = re.compile(r"GDScript backtrace", re.IGNORECASE)

    error_matches = [line for line in content if error_re.search(line)]
    warning_matches = [line for line in content if warning_re.search(line)]
    lines.extend(["", f"Errors: {len(error_matches)}", f"Warnings: {len(warning_matches)}"])

    startup_lines = [line for line in content if startup_re.search(line)][-6:]
    lines.extend(["", "## Latest Startup Lines"])
    lines.extend(startup_lines or ["(none)"])

    unique_problem_lines = sorted({line for line in content if problem_re.search(line)})[:40]
    lines.extend(["", "## Unique Error/Warning Lines"])
    lines.extend(unique_problem_lines or ["(none)"])

    last_backtrace_index = -1
    for index in range(len(content) - 1, -1, -1):
        if backtrace_re.search(content[index]):
            last_backtrace_index = index
            break

    lines.extend(["", "## Latest GDScript Backtrace"])
    if last_backtrace_index < 0:
        lines.append("(none)")
    else:
        lines.extend(content[last_backtrace_index : min(len(content), last_backtrace_index + 25)])

    write_lines(output_path, lines)
    print(f"Console summary written to: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
