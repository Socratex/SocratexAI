#!/usr/bin/env python3
"""Rename a source document path in the JSON knowledge file fallback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from knowledge_cli import add_repo_root, configure_stdio, resolved_repo_root, run_index  # noqa: E402


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    add_repo_root(parser)
    parser.add_argument("--old-path", "-OldPath", default="")
    parser.add_argument("--new-path", "-NewPath", default="")
    parser.add_argument("path_args", nargs="*")
    args = parser.parse_args()

    old_path = args.old_path or (args.path_args[0] if len(args.path_args) >= 1 else "")
    new_path = args.new_path or (args.path_args[1] if len(args.path_args) >= 2 else "")
    if not old_path or not new_path:
        parser.error("knowledge_file_rename.py requires --old-path and --new-path")
    return run_index(resolved_repo_root(args.repo_root), "file-rename", ["--old-path", old_path, "--new-path", new_path])


if __name__ == "__main__":
    raise SystemExit(main())
