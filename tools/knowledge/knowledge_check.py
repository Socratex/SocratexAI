#!/usr/bin/env python3
"""Check the compiled SQLite knowledge index, with file fallback validation."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def run_index(repo_root: Path, mode: str) -> int:
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
    command = [sys.executable, "-B", str(tool), mode, "--repo-root", str(repo_root)]
    return subprocess.run(command, cwd=repo_root, text=True, check=False).returncode


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    db_exit_code = run_index(repo_root, "check")
    if db_exit_code == 0:
        return 0

    print(
        f"WARNING: SQLite knowledge check failed with exit code {db_exit_code}. "
        "Checking compiled JSON table fallback.",
        file=sys.stderr,
    )
    fallback_exit_code = run_index(repo_root, "file-check")
    if fallback_exit_code == 0:
        return 0
    return db_exit_code


if __name__ == "__main__":
    raise SystemExit(main())
