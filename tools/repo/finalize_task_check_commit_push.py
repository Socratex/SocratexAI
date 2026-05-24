#!/usr/bin/env python3
"""Top-level task finalizer wrapper for Python-first repository closure."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from repo_tool_helpers import repo_root


def main() -> int:
    parser = argparse.ArgumentParser(description="Run full checks, commit, and push.")
    parser.add_argument("--message", "-m", "-Message", required=True, help="Commit message.")
    parser.add_argument("--quality-command", "-QualityCommand", nargs="*", default=[], help="Explicit quality command.")
    parser.add_argument("--strict-audit", "-StrictAudit", action="store_true")
    parser.add_argument("--no-push", "-NoPush", action="store_true")
    parser.add_argument("--no-audit", "-NoAudit", action="store_true")
    parser.add_argument("--allow-pre-staged", "-AllowPreStaged", action="store_true")
    parser.add_argument("--require-task-flow-evidence", "-RequireTaskFlowEvidence", action="store_true")
    parser.add_argument("--task-flow-evidence-path", "-TaskFlowEvidencePath", default="")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    if not args.message.strip():
        print("ERROR: commit message must not be empty.", file=sys.stderr)
        return 2

    command = [
        sys.executable,
        "-B",
        str(root / "tools" / "repo" / "finalize_changed_files_commit_push.py"),
        "--repo-root",
        str(root),
        "--message",
        args.message,
    ]
    if args.quality_command:
        command.append("--quality-command")
        command.extend(args.quality_command)
    if args.strict_audit:
        command.append("--strict-audit")
    if args.no_push:
        command.append("--no-push")
    if args.no_audit:
        command.append("--no-audit")
    if args.allow_pre_staged:
        command.append("--allow-pre-staged")
    if args.require_task_flow_evidence:
        command.append("--require-task-flow-evidence")
        if args.task_flow_evidence_path:
            command.extend(["--task-flow-evidence-path", args.task_flow_evidence_path])

    print("==> finalize task: check, commit, and push")
    print(f"message: {args.message}")
    print("quality: full")
    print(f"push: {not args.no_push}")
    completed = subprocess.run(command, cwd=root, check=False)
    if completed.returncode != 0:
        print()
        print("FAILED: task finalizer did not commit or push a completed task.")
        print("Next step: fix the reported failure. If it is mechanical and reusable, improve the owning script.")
        return completed.returncode

    print()
    print("OK: task finalized; checks passed before commit/push.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
