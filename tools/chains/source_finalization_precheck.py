#!/usr/bin/env python3
"""Run the source finalization precheck chain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, add_chain_arguments, report_path_from, run_chain


def chain_steps(root: Path, quality: bool) -> list[ChainStep]:
    final_checks = [
        sys.executable,
        "-B",
        str(root / "tools" / "repo" / "run_final_task_checks.py"),
        "--repo-root",
        str(root),
        "--no-output",
        "--no-sound",
    ]
    if quality:
        final_checks.append("--quality")
    return [
        ChainStep(
            step_id="final_task_checks",
            label="source final task checks without output snapshot",
            command=final_checks,
            cwd=root,
            recovery_hint="Fix the first failing final-check step; do not commit until generated artifacts and checks are current.",
        ),
        ChainStep(
            step_id="runtime_gate",
            label="no legacy shell runtime gate",
            command=[sys.executable, "-B", str(root / "tools" / "quality" / "script_runtime_gate.py"), "--repo-root", str(root), "--max-examples", "5"],
            cwd=root,
            recovery_hint="Remove tracked legacy shell files/references before finalizing.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the source finalization precheck chain.")
    add_chain_arguments(parser)
    parser.add_argument("--quality", action="store_true", help="Include the configured quality gate.")
    args = parser.parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    return run_chain(
        "source_finalization_precheck",
        chain_steps(root, args.quality),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
