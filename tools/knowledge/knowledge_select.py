#!/usr/bin/env python3
"""Select compiled knowledge entries from SQLite or the file fallback."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def split_tags(values: list[str]) -> list[str]:
    tags: list[str] = []
    for value in values:
        for tag in value.split(","):
            cleaned = tag.strip()
            if cleaned:
                tags.append(cleaned)
    return tags


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--match", choices=["all", "any"], default="all")
    parser.add_argument("--type", default="")
    parser.add_argument("--view", default="")
    parser.add_argument("--load-at-start", action="store_true")
    parser.add_argument("--context-tier", action="append", default=[])
    parser.add_argument("--max-context-tier", type=int, default=0)
    parser.add_argument("--source-path", default="")
    parser.add_argument("--document-path", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--file-fallback", action="store_true")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
    mode = "file-select" if args.file_fallback else "select"
    command = [
        sys.executable,
        "-B",
        str(tool),
        mode,
        "--repo-root",
        str(repo_root),
        "--match",
        args.match,
        "--format",
        args.format,
    ]
    if args.type:
        command.extend(["--type", args.type])
    if args.view:
        command.extend(["--view", args.view])
    if args.load_at_start:
        command.append("--load-at-start")
    for tier in args.context_tier:
        command.extend(["--context-tier", str(tier)])
    if args.max_context_tier:
        command.extend(["--max-context-tier", str(args.max_context_tier)])
    if args.source_path:
        command.extend(["--source-path", args.source_path])
    if args.document_path:
        command.extend(["--document-path", args.document_path])
    if args.name:
        command.extend(["--name", args.name])
    tags = split_tags(args.tags)
    if tags:
        command.append("--tags")
        command.extend(tags)

    result = subprocess.run(command, cwd=repo_root, text=True, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
