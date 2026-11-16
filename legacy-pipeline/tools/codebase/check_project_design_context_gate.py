#!/usr/bin/env python3
"""Validate that changed code work has loaded project-specific design context."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from context_gate_helpers import (  # noqa: E402
    changed_code_paths,
    configure_stdio,
    declared_design_reads,
    gate_age_minutes,
    git_head,
    load_json,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", "-ProjectRoot", default=".")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--max-age-minutes", "-MaxAgeMinutes", type=int, default=0)
    return parser.parse_args()


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def main() -> int:
    configure_stdio()
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    gate_path = project_root / "ignored/project_design_context_gate.json"
    declared_reads = declared_design_reads(project_root)

    if declared_reads is None:
        print("OK: no PIPELINE-CONFIG.json at project root; skipping per-project design gate.")
        return 0
    if not declared_reads:
        print("OK: project declares no code_design_required_reads; per-project design gate is a no-op.")
        return 0

    code_paths = changed_code_paths(project_root, args.paths)
    if not code_paths:
        print("OK: no changed code paths require per-project design context.")
        return 0

    run_hint = f"tools/knowledge/project_design_context.py --project-root {project_root}"
    if not gate_path.is_file():
        return fail(f"Changed code paths require a fresh per-project design context load. Run {run_hint} before code work.")

    gate = load_json(gate_path)
    if not gate.get("full_set_loaded"):
        return fail(f"Project design context gate marker reports incomplete load (missing files in declared_reads). Re-run {run_hint} after fixing missing files.")

    if args.max_age_minutes > 0:
        age_minutes = gate_age_minutes(str(gate.get("loaded_at", "")))
        if age_minutes > args.max_age_minutes:
            return fail(f"Project design context gate marker is stale ({age_minutes:.1f} minutes old). Run {run_hint} again.")

    current_head = git_head(project_root)
    gate_head = gate.get("repo_head")
    if current_head and gate_head and str(gate_head) != current_head:
        return fail(f"Project design context gate marker was loaded for a different HEAD. Run {run_hint} again.")

    gate_declared = {str(item) for item in gate.get("declared_reads", [])}
    missing_from_gate = [item for item in declared_reads if item not in gate_declared]
    if missing_from_gate:
        return fail("Project design context gate marker is missing declared reads from current config: " + ", ".join(missing_from_gate) + f". Run {run_hint} again.")

    print(f"OK: per-project design context loaded for changed code paths ({len(declared_reads)} file(s) from PIPELINE-CONFIG.code_design_required_reads).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
