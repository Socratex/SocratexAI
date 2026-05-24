#!/usr/bin/env python3
"""Run available source quality fixes, then the Python quality gate."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import repo_root as shared_repo_root  # noqa: E402


def repo_root(start: Path) -> Path:
    return shared_repo_root(start, marker_files=("QUALITY-GATE.json",), marker_dirs=("tools",), use_git=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run safe auto-fixes where available, then the quality gate.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--skip-formatters", action="store_true", help="Skip best-effort formatters.")
    parser.add_argument("--quality-command", nargs="*", default=[], help="Explicit quality command passed to run_quality_gate.py.")
    parser.add_argument("--quality-command-names", nargs="*", default=[], help="QUALITY-GATE command names.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root(Path(__file__).resolve())
    if not args.skip_formatters and shutil.which("ruff"):
        print("==> ruff format")
        completed = subprocess.run(["ruff", "format", "."], cwd=root, check=False)
        if completed.returncode != 0:
            return completed.returncode

    command = [sys.executable, "-B", str(root / "tools" / "quality" / "run_quality_gate.py"), "--repo-root", str(root)]
    if args.quality_command:
        command.append("--command")
        command.extend(args.quality_command)
    if args.quality_command_names:
        command.append("--command-names")
        command.extend(args.quality_command_names)
    print("==> quality gate")
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
