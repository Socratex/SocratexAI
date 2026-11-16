#!/usr/bin/env python3
"""Compile the SQLite knowledge index and JSON file fallback."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402


def run_index(repo_root: Path, mode: str) -> int:
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
    command = [sys.executable, "-B", str(tool), mode, "--repo-root", str(repo_root)]
    return subprocess.run(command, cwd=repo_root, text=True, check=False).returncode


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", "-RepoRoot", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    db_exit_code = run_index(repo_root, "compile")
    if db_exit_code != 0:
        print(
            f"WARNING: SQLite knowledge compile failed with exit code {db_exit_code}. "
            "Falling back to compiled JSON table files.",
            file=sys.stderr,
        )
        return run_index(repo_root, "file-compile")

    return run_index(repo_root, "file-compile")


if __name__ == "__main__":
    raise SystemExit(main())
