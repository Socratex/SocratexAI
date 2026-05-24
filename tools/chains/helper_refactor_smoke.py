#!/usr/bin/env python3
"""Run the standard helper-refactor smoke chain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, add_chain_arguments, git_root_for, report_path_from, run_chain


def chain_steps(root: Path) -> list[ChainStep]:
    runtime_root = git_root_for(root)
    python_files = [
        "tools/shared/repo_helpers.py",
        "tools/pipeline/pipeline_sweep.py",
        "tools/chains/chain_runner.py",
        "tools/chains/helper_refactor_smoke.py",
        "tools/quality/script_runtime_gate.py",
        "tools/repo/check_pipeline_feature_contracts.py",
    ]
    return [
        ChainStep(
            step_id="python_syntax",
            label="compile key helper and pipeline scripts",
            command=[sys.executable, "-B", str(root / "tools" / "quality" / "check_python_syntax.py"), "--repo-root", str(root), *python_files],
            cwd=root,
            recovery_hint="Fix the syntax error before running broader generated checks.",
        ),
        ChainStep(
            step_id="feature_contracts",
            label="pipeline feature contracts",
            command=[sys.executable, "-B", str(root / "tools" / "repo" / "check_pipeline_feature_contracts.py"), "--repo-root", str(root)],
            cwd=root,
            recovery_hint="Update pipeline_featurelist.json or restore the missing contracted artifact.",
        ),
        ChainStep(
            step_id="runtime_gate",
            label="no legacy shell runtime gate",
            command=[sys.executable, "-B", str(root / "tools" / "quality" / "script_runtime_gate.py"), "--repo-root", str(runtime_root), "--max-examples", "5"],
            cwd=runtime_root,
            recovery_hint="Remove tracked legacy shell files/references or mark historical text outside executable surfaces.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the helper-refactor smoke chain.")
    add_chain_arguments(parser)
    args = parser.parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    return run_chain(
        "helper_refactor_smoke",
        chain_steps(root),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
