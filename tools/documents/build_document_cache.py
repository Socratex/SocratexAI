#!/usr/bin/env python3
"""Build the structured document read cache without a PowerShell wrapper."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def repo_root(start: Path) -> Path:
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / "SCRIPTS.json").is_file() and (candidate / "tools").is_dir():
            return candidate
    return start.resolve()


def engine_path(root: Path) -> Path:
    colocated = Path(__file__).resolve().with_name("document_read_cache_engine.py")
    if colocated.is_file():
        return colocated
    return root / "tools" / "documents" / "document_read_cache_engine.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the SocratexPipeline document read cache.")
    parser.add_argument("paths", nargs="*", default=["__ALL_JSON__"], help="JSON document paths or glob patterns.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to nearest SocratexPipeline root.")
    parser.add_argument("--output-dir", default="docs-tech/cache", help="Output directory for doc_index.json.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root(Path(__file__).resolve())
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    engine = engine_path(root)
    command = [
        sys.executable,
        "-B",
        str(engine),
        "build-cache",
        *args.paths,
        "--output-dir",
        str(output_dir),
        "--repo-root",
        str(root),
    ]
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
