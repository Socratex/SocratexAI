#!/usr/bin/env python3
"""Check the compiled JSON knowledge file fallback."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", "-RepoRoot", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
    command = [sys.executable, "-B", str(tool), "file-check", "--repo-root", str(repo_root)]
    return subprocess.run(command, cwd=repo_root, text=True, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
