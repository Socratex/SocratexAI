#!/usr/bin/env python3
"""Compatibility wrapper for legacy explicit-path commit calls."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from repo_tool_helpers import repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Delegate legacy commit calls to finalize_changed_files_commit_push.py.")
    parser.add_argument("--message", "-m", "-Message", required=True)
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--quality", "-Quality", action="store_true")
    parser.add_argument("--quality-command", "-QualityCommand", nargs="*", default=[])
    parser.add_argument("--strict-audit", "-StrictAudit", action="store_true")
    parser.add_argument("--no-audit", "-NoAudit", action="store_true")
    parser.add_argument("--no-verify", "-NoVerify", action="store_true")
    parser.add_argument("--no-push", "-NoPush", action="store_true")
    parser.add_argument("--allow-pre-staged", "-AllowPreStaged", action="store_true")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    if args.paths:
        print("legacy_commit_task_compatibility_wrapper.py delegates to finalize_changed_files_commit_push.py; explicit --paths are accepted for compatibility.")
    else:
        print("legacy_commit_task_compatibility_wrapper.py delegates to finalize_changed_files_commit_push.py; prefer finalize_changed_files_commit_push.py for new automation.")

    command = [
        sys.executable,
        "-B",
        str(root / "tools" / "repo" / "finalize_changed_files_commit_push.py"),
        "--repo-root",
        str(root),
        "--message",
        args.message,
    ]
    if args.paths:
        command.append("--paths")
        command.extend(args.paths)
    if not args.quality:
        command.append("--no-quality")
    if args.quality_command:
        command.append("--quality-command")
        command.extend(args.quality_command)
    if args.strict_audit:
        command.append("--strict-audit")
    if args.no_audit or args.no_verify:
        command.append("--no-audit")
    if args.no_push:
        command.append("--no-push")
    if args.allow_pre_staged:
        command.append("--allow-pre-staged")
    return subprocess.run(command, cwd=root, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
