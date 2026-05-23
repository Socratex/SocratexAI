#!/usr/bin/env python3
"""Compile Python source text in memory without writing bytecode caches."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Python source syntax without writing .pyc files.")
    parser.add_argument("paths", nargs="+", help="Python source files to compile.")
    parser.add_argument("--repo-root", default=".", help="Repository root for relative paths.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    errors: list[str] = []
    for raw_path in args.paths:
        path = Path(raw_path)
        if not path.is_absolute():
            path = root / path
        if not path.is_file():
            errors.append(f"missing Python source: {raw_path}")
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            errors.append(f"{raw_path}: {exc}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: Python syntax check passed for {len(args.paths)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
