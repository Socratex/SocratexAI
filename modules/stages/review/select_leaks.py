"""Tier-script checker for leaks: applies the modules/tools/scripts/check_leaks.py patterns to changed lines, no model involved."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "modules" / "tools" / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "engine"))

import check_leaks  # noqa: E402
import selectlib  # noqa: E402


def main() -> None:
    request = selectlib.load_request()
    rules = check_leaks.patterns()
    rows: list[dict] = []
    for rel in selectlib.files_of(request):
        lines = selectlib.read_lines(request, rel)
        for chunk in (c for c in request["chunks"] if c["file"] == rel):
            for number in range(chunk["line_start"], min(chunk["line_end"], len(lines)) + 1):
                if any(rule.search(lines[number - 1]) for rule in rules):
                    rows.append(selectlib.candidate(
                        rel, number, number, "leak", "Line matches a private-reference pattern (value not shown).",
                        severity="blocker", kind="judgment", confidence="high"))
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
