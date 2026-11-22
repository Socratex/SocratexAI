#!/usr/bin/env python3
"""Shared helper for machine output that lives in `state/` (outside git), so `local/` holds only owner settings.

Usage:
    state.py dir                      print the state directory (created on demand)
    state.py rotate <subdir> [--max-files N] [--max-age-days D]

Log rotation trigger (no agent config is touched, no hook is needed):
    `sox config resolve` (core.write_effective), `sox install` and `sox index` call `rotate_daily()`. It rotates
    every directory named in ROTATED_SUBDIRS that exists, at most once per day (marker file state/.rotated), silently,
    and never raises, so a rotation problem cannot fail the command that triggered it.
    `sox state rotate [--dry-run]` rotates on demand (ignores the daily marker); add a subdir to ROTATED_SUBDIRS
    when a new kind of machine output starts to accumulate in state/.
    `sox state adopt-logs --yes` moves (never deletes) legacy local/flow-debug-*.log into state/flow-debug/.
"""

from __future__ import annotations

import argparse
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MAX_FILES = 20
DEFAULT_MAX_AGE_DAYS = 14
ROTATED_SUBDIRS = ("flow-debug",)   # state/ subdirectories that hold only disposable logs
MARKER_NAME = ".rotated"
ROTATE_INTERVAL_SECONDS = 86400
LEGACY_LOG_GLOB = "flow-debug-*.log"


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
    dry_run: bool = False,
) -> list[Path]:
    """Delete files older than max_age_days, then keep at most max_files newest. Returns the removed paths.

    With dry_run nothing is deleted; the result lists what would be."""
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
    if not dry_run:
        for path in removed:
            path.unlink(missing_ok=True)
    return removed


def rotate_known(root: Path | None = None, dry_run: bool = False, now: float | None = None) -> dict[str, list[Path]]:
    """Rotate every existing directory of ROTATED_SUBDIRS under <root>/state. Returns {subdir: removed paths}."""
    base = (root or ROOT) / "state"
    return {name: rotate(base / name, dry_run=dry_run, now=now) for name in ROTATED_SUBDIRS if (base / name).is_dir()}


def rotate_daily(root: Path | None = None, now: float | None = None) -> bool:
    """Run rotate_known at most once per day (marker state/.rotated). Silent; never raises. Returns True when it ran."""
    try:
        now = time.time() if now is None else now
        marker = (root or ROOT) / "state" / MARKER_NAME
        if marker.is_file() and now - marker.stat().st_mtime < ROTATE_INTERVAL_SECONDS:
            return False
        rotate_known(root, now=now)
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(now)) + "\n", encoding="utf-8")
        return True
    except Exception:  # noqa: BLE001 - a rotation problem must never fail the calling command
        return False


def adopt_logs(root: Path | None = None, move: bool = False) -> list[tuple[Path, Path, int]]:
    """List (source, target, bytes) for legacy <root>/local/flow-debug-*.log; with move=True move them (never delete).

    A file whose target already exists is skipped and stays where it is."""
    base = root or ROOT
    target_dir = base / "state" / "flow-debug"
    found = []
    for source in sorted((base / "local").glob(LEGACY_LOG_GLOB)):
        target = target_dir / source.name
        if source.is_file() and not target.exists():
            found.append((source, target, source.stat().st_size))
    if move and found:
        target_dir.mkdir(parents=True, exist_ok=True)
        for source, target, _ in found:
            shutil.move(str(source), str(target))
    return found


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
