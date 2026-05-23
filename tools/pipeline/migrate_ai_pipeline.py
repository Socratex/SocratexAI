#!/usr/bin/env python3
"""Migrate legacy AI directives to SocratexPipeline with Python-only tooling."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from pipeline_script_helpers import configure_stdio, split_values


def run_python(script: Path, args: list[str]) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{script.name} failed with exit code {completed.returncode}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", "-TargetPath", default=".")
    parser.add_argument("--legacy-directive-files", "-LegacyDirectiveFiles", nargs="*", default=["AGENTS.md", "CLAUDE.md", ".cursor/rules", ".github/copilot-instructions.md"])
    parser.add_argument("--packs", "-Packs", nargs="*", default=["code"])
    parser.add_argument("--directive-mode", "-DirectiveMode", choices=("snapshot", "merge", "replace"), default="merge")
    parser.add_argument("--create-project-files", "-CreateProjectFiles", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    pipeline_root = Path(__file__).resolve().parents[2]
    target_root = Path(args.target_path).resolve()
    packs = split_values(args.packs)
    existing = [item for item in args.legacy_directive_files if (target_root / item).exists()]
    if not existing:
        existing = ["AGENTS.md"]

    print("==> migrating existing AI pipeline")
    print(f"Target: {target_root}")
    print(f"Mode: {args.directive_mode}")

    if args.dry_run:
        print(f"Would install packs: {', '.join(packs)}")
        print(f"Would update directives: {', '.join(existing)}")
        return 0

    import_args = ["--target-path", str(target_root), "--packs", *packs]
    if args.create_project_files:
        import_args.append("--create-project-files")
    run_python(pipeline_root / "tools" / "pipeline" / "import_existing_project.py", import_args)
    run_python(
        target_root / "SocratexAI" / "tools" / "pipeline" / "set_directives.py",
        ["--target-path", str(target_root), "--mode", args.directive_mode, "--directive-files", *existing],
    )
    print("Migration complete. SocratexAI is now active for this project; future sessions should start from SOCRATEX.md.")
    print("Review SOCRATEX.md, any *.old directive files, and run SocratexAI/tools/documents/audit_docs.py.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
