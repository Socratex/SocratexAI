#!/usr/bin/env python3
"""Require pipeline_featurelist.json updates for pipeline-owned changes."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_tool_helpers import changed_paths, featurelist_path, pipeline_owned_path, repo_root, run


def main() -> int:
    parser = argparse.ArgumentParser(description="Check that pipeline-owned changes update pipeline_featurelist.json.")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[], help="Changed paths, comma-separated or repeated.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to nearest git root.")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    paths = changed_paths(root, args.paths)
    pipeline_paths = [path for path in paths if pipeline_owned_path(path)]
    if not pipeline_paths:
        print("OK: no pipeline-owned changes; feature list guard skipped.")
        return 0

    if any(featurelist_path(path) for path in paths):
        print("OK: pipeline feature list changed with pipeline-owned changes.")
        checker = root / "tools" / "repo" / "check_pipeline_feature_contracts.py"
        if checker.is_file():
            return run(
                "pipeline feature contract check",
                [sys.executable, "-B", str(checker), "--repo-root", str(root), "--paths", ",".join(paths)],
                root,
            )
        return 0

    print("ERROR: pipeline-owned changes require a pipeline_featurelist.json update.")
    print("Changed pipeline-owned paths:")
    for path in pipeline_paths:
        print(f" - {path}")
    print()
    print("If this change adds or improves reusable pipeline behavior, add a feature ID to pipeline_featurelist.json.")
    print("If it is intentionally not a pipeline capability change, split it from pipeline improvement work.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
