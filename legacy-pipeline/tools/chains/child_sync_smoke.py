#!/usr/bin/env python3
"""Run the child package sync smoke chain."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from chain_runner import ChainStep, report_path_from, run_chain


def chain_steps(source_root: Path, project_root: Path, install_root: Path, profile: str, apply_sync: bool) -> list[ChainStep]:
    sync_command = [
        sys.executable,
        "-B",
        str(source_root / "tools" / "pipeline" / "sync_managed_pipeline_package.py"),
        "--source-root",
        str(source_root),
        "--install-root",
        str(install_root),
        "--project-root",
        str(project_root),
    ]
    if profile:
        sync_command.extend(["--profile", profile, "--apply-project-profile"])
    if not apply_sync:
        sync_command.append("--dry-run")
    return [
        ChainStep(
            step_id="managed_package_sync",
            label="managed pipeline package sync",
            command=sync_command,
            cwd=source_root,
            recovery_hint="Fix source package drift or rerun with --apply-sync only after the dry-run plan is understood.",
        ),
        ChainStep(
            step_id="child_runtime_gate",
            label="child no legacy shell runtime gate",
            command=[sys.executable, "-B", str(install_root / "tools" / "quality" / "script_runtime_gate.py"), "--repo-root", str(project_root), "--max-examples", "5"],
            cwd=project_root,
            recovery_hint="Remove managed or project-local legacy shell files/references before finalizing the child.",
        ),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the child package sync smoke chain.")
    parser.add_argument("--source-root", required=True, help="SocratexAI source root.")
    parser.add_argument("--project-root", required=True, help="Child project root.")
    parser.add_argument("--install-root", default="", help="Installed SocratexAI package root; defaults to PROJECT/SocratexAI.")
    parser.add_argument("--profile", default="", help="Optional project profile to apply during sync.")
    parser.add_argument("--apply-sync", action="store_true", help="Apply sync instead of dry-running it.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after failing required steps.")
    parser.add_argument("--report-path", default="", help="Optional JSON report path.")
    args = parser.parse_args()
    source_root = Path(args.source_root).expanduser().resolve()
    project_root = Path(args.project_root).expanduser().resolve()
    install_root = Path(args.install_root).expanduser().resolve() if args.install_root else project_root / "SocratexAI"
    return run_chain(
        "child_sync_smoke",
        chain_steps(source_root, project_root, install_root, args.profile, args.apply_sync),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )


if __name__ == "__main__":
    raise SystemExit(main())
