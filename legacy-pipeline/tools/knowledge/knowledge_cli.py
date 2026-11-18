#!/usr/bin/env python3
"""Shared CLI helpers for knowledge wrapper entrypoints."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
_EMBEDDED_TOOLS_ROOT = Path(__file__).resolve().parents[2] / "SocratexAI" / "tools"
for tools_root in (_TOOLS_ROOT, _EMBEDDED_TOOLS_ROOT):
    if tools_root.is_dir() and str(tools_root) not in sys.path:
        sys.path.insert(0, str(tools_root))

from shared.cli_helpers import configure_stdio  # noqa: E402


def default_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def resolved_repo_root(value: str) -> Path:
    return Path(value).resolve() if value else default_repo_root()


def add_repo_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", "-RepoRoot", default="")


def collect_paths(args: argparse.Namespace) -> list[str]:
    values: list[str] = []
    for value in getattr(args, "path", []) or []:
        if value:
            values.append(value)
    for value in getattr(args, "paths", []) or []:
        if value:
            values.append(value)
    return values


def run_index(repo_root: Path, mode: str, arguments: list[str]) -> int:
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
    command = [sys.executable, "-B", str(tool), mode, "--repo-root", str(repo_root), *arguments]
    return subprocess.run(command, cwd=repo_root, text=True, check=False).returncode
