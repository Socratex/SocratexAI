"""Fix script for the comments checker: delete commented-out code and comments that repeat the code (idempotent)."""

from __future__ import annotations

import sys
from pathlib import Path

import comment_rules


def parse_ranges(spec: str) -> list[tuple[int, int]]:
    return [(int(a), int(b)) for a, b in (part.split("-") for part in spec.split(",") if part)]


def fixed_text(suffix: str, text: str, ranges: list[tuple[int, int]] | None = None) -> str:
    """Remove flagged comment lines until none are left, so a second run never finds more.

    With `ranges` (1-based, in the numbering of the original text) only flagged lines inside them are removed;
    all other lines, flagged or not, stay byte-identical.
    """
    kept = list(enumerate(text.splitlines(keepends=True), 1))
    while True:
        issues = comment_rules.find_issues(suffix, [line.rstrip("\r\n") for _, line in kept])
        dropped = {kept[issue.line - 1][0] for issue in issues}
        if ranges is not None:
            dropped = {n for n in dropped if any(a <= n <= b for a, b in ranges)}
        if not dropped:
            return "".join(line for _, line in kept)
        kept = [(n, line) for n, line in kept if n not in dropped]


def main(argv: list[str]) -> int:
    ranges = None
    if len(argv) == 3 and argv[0] == "--lines":
        ranges, argv = parse_ranges(argv[1]), argv[2:]
    if len(argv) != 1:
        print("usage: fix_comments.py [--lines S-E,S-E] FILE", file=sys.stderr)
        return 2
    path = Path(argv[0])
    original = path.read_bytes().decode("utf-8")
    updated = fixed_text(path.suffix.lower(), original, ranges)
    if updated != original:
        path.write_bytes(updated.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
