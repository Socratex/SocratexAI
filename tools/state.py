#!/usr/bin/env python3
"""Shared helper for machine output that lives in `state/` (outside git), so `local/` holds only owner settings.

Usage:
    state.py dir                      print the state directory (created on demand)
    state.py rotate <subdir> [--max-files N] [--max-age-days D]
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_FILES = 20
DEFAULT_MAX_AGE_DAYS = 14


def state_dir(root: Path | None = None) -> Path:
    """Return <root>/state, creating it when missing."""
    path = (root or ROOT) / "state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def rotate(
    directory: Path,
    max_files: int = DEFAULT_MAX_FILES,
    max_age_days: float = DEFAULT_MAX_AGE_DAYS,
    now: float | None = None,
) -> list[Path]:
    """Delete files older than max_age_days, then keep at most max_files newest. Returns the removed paths."""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    now = time.time() if now is None else now
    cutoff = now - max_age_days * 86400
    files = sorted((p for p in directory.iterdir() if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)
    removed: list[Path] = []
    kept: list[Path] = []
    for path in files:
        if path.stat().st_mtime < cutoff:
            removed.append(path)
        else:
            kept.append(path)
    removed.extend(kept[max_files:])
    for path in removed:
        path.unlink(missing_ok=True)
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("dir")
    rot = sub.add_parser("rotate")
    rot.add_argument("subdir")
    rot.add_argument("--max-files", type=int, default=DEFAULT_MAX_FILES)
    rot.add_argument("--max-age-days", type=float, default=DEFAULT_MAX_AGE_DAYS)
    args = parser.parse_args()
    if args.cmd == "dir":
        print(state_dir())
        return 0
    removed = rotate(state_dir() / args.subdir, args.max_files, args.max_age_days)
    print(f"removed {len(removed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
