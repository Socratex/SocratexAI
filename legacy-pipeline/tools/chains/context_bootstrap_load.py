#!/usr/bin/env python3
"""Run the standard compiled-context bootstrap read chain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, add_chain_arguments, report_path_from, run_chain


def chain_steps(root: Path) -> list[ChainStep]:
    reader = root / "tools" / "pipeline" / "read_compiled_context.py"
    return [
        ChainStep(
            step_id="bootstrap_context",
            label="read bootstrap compiled context",
            command=[sys.executable, "-B", str(reader), "bootstrap"],
            cwd=root,
            recovery_hint="Rebuild compiled context or run the project-specific bootstrap/context loader.",
        ),
        ChainStep(
            step_id="state_context",
            label="read STATE compiled context",
            command=[sys.executable, "-B", str(reader), "STATE"],
            cwd=root,
            recovery_hint="Rebuild compiled context or inspect the project state document directly.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the compiled-context bootstrap read chain.")
    add_chain_arguments(parser)
    args = parser.parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    return run_chain(
        "context_bootstrap_load",
        chain_steps(root),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
