#!/usr/bin/env python3
"""Review pipeline CLI: runs the shared engine (modules/engine) with modules/stages/review/checkers.json and prints the UCE report.

Usage:
    python modules/stages/review/run.py --files app.py lib/util.py [--project-dir DIR] [--dry-run] [--no-fix] [--keep]
        [--run-id ID] [--registry PATH] [--min-changed-lines N] [--report-file PATH]

Only the files given in --files are read or changed. Run files live outside the repo in the temp folder
(<temp>/socratex-pipeline/review/<run id>/, base overridable with SOCRATEX_PIPELINE_DIR) and are removed after the
run; --keep leaves findings.json, per-checker files and log.jsonl for a separate aggregator session.
Spec: docs/specs/review-pipeline/SPEC.md
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "engine"))
sys.path.insert(0, str(HERE))

import common  # noqa: E402
import engine  # noqa: E402
import merge  # noqa: E402
import report  # noqa: E402

DEFAULT_REGISTRY = HERE / "checkers.json"
default_model = engine.default_model
default_implementer = engine.default_implementer


def run_review(project_dir, files, *, registry_path=None, **options) -> dict:
    """Run the review pipeline; `options` are the keyword arguments of engine.run_pipeline."""
    return engine.run_pipeline(registry_path or DEFAULT_REGISTRY, project_dir, files, **options)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the review pipeline over a list of changed files.")
    parser.add_argument("--files", nargs="+", required=True, help="Changed files to review (only these are touched).")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--run-id")
    parser.add_argument("--registry", help="Registry path (default: modules/stages/review/checkers.json).")
    parser.add_argument("--min-changed-lines", type=int, help="Override the registry threshold for trivial changes.")
    parser.add_argument("--dry-run", action="store_true", help="Show checkers, chunks and predicted model calls only.")
    parser.add_argument("--no-fix", action="store_true", help="Check and merge, do not apply fixes.")
    parser.add_argument("--keep", action="store_true", help="Keep the run folder (findings.json, log) after the run.")
    parser.add_argument("--report-file", help="Also write the UCE report to this file.")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = run_review(args.project_dir, args.files, registry_path=args.registry, run_id=args.run_id,
                            dry_run=args.dry_run, min_changed_lines=args.min_changed_lines, fix=not args.no_fix,
                            keep=args.keep)
    except (common.RegistryError, merge.SchemaError) as err:
        print(f"review: {err}", file=sys.stderr)
        return 2
    if result.get("doc"):
        text = report.render(result["doc"])
        print(text)
        if args.report_file:
            Path(args.report_file).write_text(text + "\n", encoding="utf-8", newline="\n")
        if result.get("run_dir"):
            print(f"Run files kept in: {result['run_dir']}", file=sys.stderr)
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
