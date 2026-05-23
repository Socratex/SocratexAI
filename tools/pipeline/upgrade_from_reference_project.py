#!/usr/bin/env python3
"""Refresh the maintainer reference-project tool tree with Python-only tooling."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from pipeline_script_helpers import configure_stdio


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-project-path", "-ReferenceProjectPath", required=True)
    parser.add_argument("--target-path", "-TargetPath", default="")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_path).resolve() if args.target_path else Path(__file__).resolve().parents[2]
    source_root = Path(args.reference_project_path).resolve()
    source_tools = source_root / "Tools"
    target_tools = target_root / "tools"
    reference_tools = target_tools / "upstream-reference-project"
    print("==> maintainer upgrade from reference project")
    print(f"Source: {source_root}")
    print(f"Target: {target_root}")
    if not source_tools.exists():
        raise SystemExit(f"Missing source Tools folder: {source_tools}")
    if args.dry_run:
        print(f"Would refresh upstream reference tools: {reference_tools}")
    else:
        if reference_tools.exists():
            shutil.rmtree(reference_tools)
        reference_tools.mkdir(parents=True, exist_ok=True)
        for child in source_tools.iterdir():
            destination = reference_tools / child.name
            if child.is_dir():
                shutil.copytree(child, destination)
            else:
                shutil.copy2(child, destination)
    print("Reference project tools were refreshed as a recursive reference tree.")
    print("Reusable source changes must be ported into categorized source tools explicitly, then cataloged in SCRIPTS.json and pipeline_featurelist.json.")
    if not args.dry_run:
        audit_py = target_tools / "documents" / "audit_docs.py"
        if audit_py.is_file():
            completed = subprocess.run([sys.executable, str(audit_py)], check=False)
            if completed.returncode != 0:
                raise SystemExit(f"audit_docs.py failed with exit code {completed.returncode}")
        else:
            print("No Python audit_docs.py entrypoint is available; skipped instead of invoking legacy shell tooling.")
    print("Maintainer upgrade complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
