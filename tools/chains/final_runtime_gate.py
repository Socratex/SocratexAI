#!/usr/bin/env python3
"""Run the final runtime-gate chain for a pipeline package or repo."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, add_chain_arguments, git_root_for, report_path_from, run_chain


def chain_steps(root: Path) -> list[ChainStep]:
    runtime_root = git_root_for(root)
    return [
        ChainStep(
            step_id="feature_contracts",
            label="pipeline feature contracts",
            command=[sys.executable, "-B", str(root / "tools" / "repo" / "check_pipeline_feature_contracts.py"), "--repo-root", str(root)],
            cwd=root,
            recovery_hint="Restore missing contracted pipeline artifacts or update the feature contract with the new ownership.",
        ),
        ChainStep(
            step_id="runtime_gate",
            label="no legacy shell runtime gate",
            command=[sys.executable, "-B", str(root / "tools" / "quality" / "script_runtime_gate.py"), "--repo-root", str(runtime_root), "--max-examples", "5"],
            cwd=runtime_root,
            recovery_hint="Remove tracked legacy shell files/references before declaring the pipeline Python-only.",
        ),
        ChainStep(
            step_id="git_clean",
            label="git diff is clean",
            command=["git", "diff", "--quiet"],
            cwd=runtime_root,
            recovery_hint="Review and commit intended changes, or discard only changes you created and no longer need.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the final runtime-gate chain.")
    add_chain_arguments(parser)
    args = parser.parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    return run_chain(
        "final_runtime_gate",
        chain_steps(root),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
