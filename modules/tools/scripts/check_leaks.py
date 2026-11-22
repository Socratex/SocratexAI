#!/usr/bin/env python3
"""Fail when tracked files contain private references: user paths or patterns from local/sensitive-patterns.txt.

The pattern file is gitignored (one regex per line, `#` = comment), so the public repo never names what it hides.
Runs as the pre-push hook installed by modules/tools/scripts/install.py.

Usage:
    python modules/tools/scripts/check_leaks.py            # scan all tracked files
    python modules/tools/scripts/check_leaks.py FILE...    # scan given files
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PATTERN_FILE = ROOT / "local" / "sensitive-patterns.txt"
BUILTIN = [
    r"[A-Za-z]:[\\/]+Users[\\/]+(?!<|\{|USER|you|name)[A-Za-z0-9._-]+",  # Windows user profile paths
    r"/home/(?!<|\{|user\b|you\b)[a-z0-9._-]+/",                          # Linux home paths
    r"/Users/(?!<|\{|you\b|name\b)[A-Za-z0-9._-]+/",                       # macOS home paths
    r"\b(?:sk-ant-|sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{16,}",          # API tokens
]
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".ico", ".zip", ".pdf", ".woff", ".woff2", ".ttf"}


def patterns() -> list[re.Pattern[str]]:
    rows = list(BUILTIN)
    if PATTERN_FILE.exists():
        rows += [line.strip() for line in PATTERN_FILE.read_text(encoding="utf-8").splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
    return [re.compile(row, re.IGNORECASE) for row in rows]


def tracked_files() -> list[Path]:
    out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=ROOT, capture_output=True, check=True).stdout
    return [ROOT / name for name in out.decode("utf-8").split("\0") if name]


def display(path: Path) -> str:
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix()


def scan(files: list[Path], rules: list[re.Pattern[str]]) -> list[str]:
    hits = []
    for path in files:
        if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for number, line in enumerate(text.splitlines(), 1):
            for rule in rules:
                if rule.search(line):
                    hits.append(f"{display(path)}:{number}: matches /{rule.pattern}/")
                    break
    return hits


def main(argv: list[str]) -> int:
    files = [Path(arg).resolve() for arg in argv] if argv else tracked_files()
    hits = scan(files, patterns())
    if not PATTERN_FILE.exists():
        print("note: local/sensitive-patterns.txt missing; only built-in patterns checked.")
    if hits:
        print("Private references found (fix or move to local/):")
        print("\n".join("  " + hit for hit in hits[:200]))
        return 1
    print(f"Leak check clean ({len(files)} files).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
