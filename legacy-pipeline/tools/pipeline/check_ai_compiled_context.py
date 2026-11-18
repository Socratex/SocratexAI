#!/usr/bin/env python3
"""Cheap Python check for generated SocratexAI compiled-context freshness anchors."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


TOOLS_ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Python-verifiable compiled-context anchors.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--output-dir", default="AI-compiled", help="Compiled context directory.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    output = root / args.output_dir
    root_rebuild = root / "tools" / "pipeline" / "rebuild_ai_compiled_context.py"
    package_rebuild = TOOLS_ROOT / "pipeline" / "rebuild_ai_compiled_context.py"
    rebuild = root_rebuild if root_rebuild.is_file() else package_rebuild
    if rebuild.is_file():
        completed = subprocess.run(
            [sys.executable, "-B", str(rebuild), "--repo-root", str(root), "--output-dir", args.output_dir, "--check"],
            cwd=root,
            check=False,
        )
        return completed.returncode

    required = [
        output / "codex" / "ENTRYPOINT.md",
        output / "codex" / "RULES.compiled.md",
        output / "codex" / "WORKFLOW.compiled.md",
        output / "INDEX.json",
        output / "checksum.json",
        output / "project" / "knowledge-manifest.json",
        output / "project" / "knowledge-files" / "manifest.json",
    ]
    missing = [path for path in required if not path.is_file()]
    if missing:
        for path in missing:
            print(f"ERROR: missing compiled context artifact: {path.relative_to(root)}")
        return 1

    root_bootstrap = root / "tools" / "pipeline" / "pipeline_bootstrap_index.py"
    package_bootstrap = TOOLS_ROOT / "pipeline" / "pipeline_bootstrap_index.py"
    bootstrap = root_bootstrap if root_bootstrap.is_file() else package_bootstrap
    if bootstrap.is_file():
        completed = subprocess.run(
            [sys.executable, "-B", str(bootstrap), "--repo-root", str(root), "--check"],
            cwd=root,
            check=False,
        )
        if completed.returncode != 0:
            return completed.returncode
    print("OK: Python compiled-context anchor check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
