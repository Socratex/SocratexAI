#!/usr/bin/env python3
"""Refresh or check SocratexAI compiled context using Python entrypoints."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def run_step(label: str, command: list[str], cwd: Path) -> int:
    print(f"==> {label}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        print(f"ERROR: {label} failed with exit code {completed.returncode}", file=sys.stderr)
    return completed.returncode


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh or check SocratexAI compiled context.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to this script's package root.")
    parser.add_argument("--output-dir", default="AI-compiled", help="Compiled context output directory.")
    parser.add_argument("--check", action="store_true", help="Check without writing generated compiled context files.")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    tools = repo_root / "tools" / "pipeline"
    bootstrap = tools / "pipeline_bootstrap_index.py"
    rebuild = tools / "rebuild_ai_compiled_context.py"
    check = tools / "check_ai_compiled_context.py"

    bootstrap_command = [sys.executable, "-B", str(bootstrap), "--repo-root", str(repo_root)]
    if args.check:
        bootstrap_command.append("--check")
    code = run_step("pipeline bootstrap index check" if args.check else "pipeline bootstrap index refresh", bootstrap_command, repo_root)
    if code != 0:
        return code

    if args.check:
        return run_step(
            "compiled context check",
            [sys.executable, "-B", str(check), "--repo-root", str(repo_root), "--output-dir", args.output_dir],
            repo_root,
        )
    code = run_step(
        "compiled context refresh",
        [sys.executable, "-B", str(rebuild), "--repo-root", str(repo_root), "--output-dir", args.output_dir],
        repo_root,
    )
    if code != 0:
        return code
    return run_step(
        "compiled context check",
        [sys.executable, "-B", str(check), "--repo-root", str(repo_root), "--output-dir", args.output_dir],
        repo_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
