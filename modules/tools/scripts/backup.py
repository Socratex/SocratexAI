#!/usr/bin/env python3
"""Zip the global Claude Code and Codex configuration (never credentials) before any config change.

Usage:
    backup.py                    # writes ~/claude-backup/ai-config-<timestamp>.zip
    backup.py --list             # list existing backups
    backup.py --restore <zip>    # put the files from a backup back in place (backs up the current state first)
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
import zipfile
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[3]   # the SocratexAI checkout
BACKUP_DIR = HOME / "claude-backup"
FILES = [
    ".claude/CLAUDE.md",
    ".claude/INDEX.json",
    ".claude/settings.json",
    ".claude/settings.local.json",
    ".codex/AGENTS.md",
    ".codex/config.toml",
]
DIRS = [".claude/agents", ".claude/skills", ".claude/hooks", ".claude/scheduled-tasks", ".codex/rules", ".codex/agents"]
# Knowledge that lives only in local/ (outside git); after the WORK migration this is the one copy. local/cache is not saved.
KNOWLEDGE_DIRS = ["local/projects", "local/groups", "local/tickets", "local/handovers", "local/notes", "local/archive"]
EXTERNAL_PREFIX = "SocratexAI/"   # archive name prefix for a checkout that is not under HOME
NEVER = {".credentials.json", "auth.json", "auth.json.lock"}


def collect() -> list[Path]:
    paths = [HOME / name for name in FILES if (HOME / name).is_file()]
    for folder in DIRS:
        root = HOME / folder
        if root.is_dir():
            paths += [path for path in root.rglob("*") if path.is_file() and "__pycache__" not in path.parts]
    for folder in KNOWLEDGE_DIRS:
        root = ROOT / folder
        if root.is_dir():
            paths += [path for path in root.rglob("*") if path.is_file() and not {"__pycache__", ".git"} & set(path.parts)]
    return [path for path in paths if path.name not in NEVER]


def archive_name(path: Path) -> str:
    """Name inside the zip: relative to HOME; a file of a checkout outside HOME is stored as SocratexAI/<path in the checkout>."""
    try:
        return path.relative_to(HOME).as_posix()
    except ValueError:
        return EXTERNAL_PREFIX + path.relative_to(ROOT).as_posix()


def restore_target(name: str) -> Path:
    inside_home = (ROOT / "x").is_relative_to(HOME)
    return ROOT / name[len(EXTERNAL_PREFIX):] if name.startswith(EXTERNAL_PREFIX) and not inside_home else HOME / name


def backup(label: str = "ai-config") -> Path:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    out = BACKUP_DIR / f"{label}-{dt.datetime.now():%Y%m%d-%H%M%S}.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in collect():
            archive.write(path, archive_name(path))
    return out


def restore(zip_path: Path) -> int:
    safety = backup("before-restore")
    with zipfile.ZipFile(zip_path) as archive:
        for name in archive.namelist():
            if Path(name).name in NEVER or ".." in Path(name).parts:
                continue
            target = restore_target(name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(name))
    print(f"Restored {zip_path.name}; previous state saved in {safety}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Back up or restore the global AI agent configuration.")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--restore", type=Path)
    args = parser.parse_args(argv)
    if args.list:
        for path in sorted(BACKUP_DIR.glob("*.zip")):
            print(path)
        return 0
    if args.restore:
        return restore(args.restore)
    print(backup())
    return 0


if __name__ == "__main__":
    sys.exit(main())
