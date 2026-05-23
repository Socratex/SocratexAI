#!/usr/bin/env python3
"""Delete documents or entries from the JSON knowledge file fallback."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from knowledge_cli import add_repo_root, collect_paths, configure_stdio, resolved_repo_root, run_index  # noqa: E402


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    add_repo_root(parser)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--name", default="")
    parser.add_argument("paths", nargs="*")
    args = parser.parse_args()

    paths = collect_paths(args)
    if not paths:
        parser.error("knowledge_file_delete.py requires at least one --path or positional path")
    command_args = [item for path in paths for item in ("--path", path)]
    if args.name:
        command_args.extend(["--name", args.name])
    return run_index(resolved_repo_root(args.repo_root), "file-delete", command_args)


if __name__ == "__main__":
    raise SystemExit(main())
