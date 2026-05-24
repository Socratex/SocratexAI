#!/usr/bin/env python3
"""Commit and push git-derived task changes after Python final checks."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from repo_tool_helpers import changed_paths, git_lines, normalize_path, package_root, repo_root, run


LOCAL_ARTIFACT_PREFIXES = (
    "logs/",
    "logs-diagnostics/",
    "logs-performance/",
    "temp/",
    "tmp/",
    "prompt-export/",
)
LOCAL_ARTIFACT_PATHS = {
    "OUTPUT",
    "CONSOLE-LOG",
    "CONSOLE-LOG-SUMMARY",
    "PROMPT-SNAPSHOT",
}


def run_git(root: Path, args: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=False,
        capture_output=capture,
        text=True,
    )


def artifact_path(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized in LOCAL_ARTIFACT_PATHS or normalized.startswith(LOCAL_ARTIFACT_PREFIXES)


def commit_candidate_paths(root: Path, raw_paths: list[str]) -> list[str]:
    candidates = changed_paths(root, raw_paths or None)
    return [path for path in candidates if not artifact_path(path)]


def final_checks_command(root: Path, args: argparse.Namespace) -> list[str]:
    script = package_root() / "tools" / "repo" / "run_final_task_checks.py"
    command = [sys.executable, "-B", str(script), "--repo-root", str(root)]
    if not args.no_quality:
        command.append("--quality")
    if args.quality_command:
        command.append("--quality-command")
        command.extend(args.quality_command)
    if args.quality_command_names:
        command.append("--quality-command-names")
        command.extend(args.quality_command_names)
    if args.strict_audit:
        command.append("--strict-audit")
    if args.no_audit:
        command.append("--no-audit")
    if args.require_task_flow_evidence:
        command.append("--require-task-flow-evidence")
        if args.task_flow_evidence_path:
            command.extend(["--task-flow-evidence-path", args.task_flow_evidence_path])
    return command


def stage_paths(root: Path, paths: list[str]) -> int:
    print("\n==> staging git-derived paths")
    completed = run_git(root, ["add", "--", *paths], capture=True)
    if completed.returncode != 0:
        print((completed.stderr or completed.stdout).strip(), file=sys.stderr)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Python final checks, commit changed paths, and push.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to the current git worktree.")
    parser.add_argument("--message", "-m", required=True, help="Commit message.")
    parser.add_argument("--paths", nargs="*", default=[], help="Explicit changed paths, comma-separated or repeated.")
    parser.add_argument("--no-push", action="store_true", help="Commit without pushing.")
    parser.add_argument("--no-quality", action="store_true", help="Skip quality gate inside final checks.")
    parser.add_argument("--quality-command", nargs="*", default=[], help="Explicit quality command for run_quality_gate.py.")
    parser.add_argument("--quality-command-names", nargs="*", default=[], help="QUALITY-GATE command names for run_quality_gate.py.")
    parser.add_argument("--strict-audit", action="store_true", help="Pass strict audit mode to final checks.")
    parser.add_argument("--no-audit", action="store_true", help="Skip document audit inside final checks.")
    parser.add_argument("--require-task-flow-evidence", action="store_true", help="Validate closure evidence JSON inside final checks.")
    parser.add_argument("--task-flow-evidence-path", default="", help="Closure evidence JSON path.")
    parser.add_argument("--allow-pre-staged", action="store_true", help="Allow already staged changes.")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path.cwd())
    if not args.message.strip():
        print("ERROR: commit message must not be empty.", file=sys.stderr)
        return 2
    if not (root / ".git").exists():
        print(f"ERROR: not a git repository: {root}", file=sys.stderr)
        return 2

    staged = git_lines(root, ["diff", "--cached", "--name-only"])
    if staged and not args.allow_pre_staged:
        print("ERROR: refusing to continue because staged changes already exist.", file=sys.stderr)
        print("Use --allow-pre-staged if this is intentional.", file=sys.stderr)
        return 2

    initial_candidates = commit_candidate_paths(root, args.paths)
    if not initial_candidates:
        print("ERROR: no changed non-local-artifact paths to close.", file=sys.stderr)
        return 2

    if run("final task checks", final_checks_command(root, args), root) != 0:
        return 1

    paths = commit_candidate_paths(root, args.paths)
    if not paths:
        print("ERROR: no changed non-local-artifact paths after final checks.", file=sys.stderr)
        return 2

    if stage_paths(root, paths) != 0:
        return 1

    staged = git_lines(root, ["diff", "--cached", "--name-only"])
    if not staged:
        print("ERROR: no staged changes after git add.", file=sys.stderr)
        return 2

    print("\n==> staged files")
    for path in staged:
        print(path)

    if run("git diff --cached --check", ["git", "diff", "--cached", "--check"], root) != 0:
        return 1
    if run("git commit", ["git", "commit", "-m", args.message], root) != 0:
        return 1
    if not args.no_push and run("git push", ["git", "push", "origin", "HEAD"], root) != 0:
        return 1

    print("\n==> final repository state")
    remaining = git_lines(root, ["status", "--short"])
    if not remaining:
        print("OK: working tree clean; subtask closed.")
    else:
        print("WARN: working tree still has changes; subtask not fully closed.")
        for line in remaining:
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
