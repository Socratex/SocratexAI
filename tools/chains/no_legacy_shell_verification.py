#!/usr/bin/env python3
"""Run the no-legacy-shell verification chain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, add_chain_arguments, git_root_for, report_path_from, run_chain


def chain_steps(root: Path) -> list[ChainStep]:
    runtime_root = git_root_for(root)
    return [
        ChainStep(
            step_id="runtime_gate",
            label="no legacy shell runtime gate",
            command=[sys.executable, "-B", str(root / "tools" / "quality" / "script_runtime_gate.py"), "--repo-root", str(runtime_root), "--max-examples", "10"],
            cwd=runtime_root,
            recovery_hint="Remove tracked legacy shell files/references or move historical-only mentions outside executable pipeline surfaces.",
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the no-legacy-shell verification chain.")
    add_chain_arguments(parser)
    args = parser.parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    return run_chain(
        "no_legacy_shell_verification",
        chain_steps(root),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
