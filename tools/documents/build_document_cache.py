#!/usr/bin/env python3
"""Build the structured document read cache with a Python entrypoint."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import repo_root as shared_repo_root  # noqa: E402


def repo_root(start: Path) -> Path:
    return shared_repo_root(start, marker_files=("SCRIPTS.json",), marker_dirs=("tools",), use_git=False)


def engine_path(root: Path) -> Path:
    colocated = Path(__file__).resolve().with_name("document_read_cache_engine.py")
    if colocated.is_file():
        return colocated
    return root / "tools" / "documents" / "document_read_cache_engine.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the SocratexPipeline document read cache.")
    parser.add_argument("positional_paths", nargs="*", help="JSON document paths or glob patterns.")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[], help="JSON document paths or glob patterns.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to nearest SocratexPipeline root.")
    parser.add_argument("--output-dir", "-OutputDir", default="docs-tech/cache", help="Output directory for doc_index.json.")
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
        *(args.paths + args.positional_paths or ["__ALL_JSON__"]),
        "--output-dir",
        str(output_dir),
        "--repo-root",
        str(root),
    ]
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
