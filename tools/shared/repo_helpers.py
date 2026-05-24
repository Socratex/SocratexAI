#!/usr/bin/env python3
"""Shared repository and subprocess helpers for SocratexPipeline tools."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shared.cli_helpers import split_values


GIT_WARNING_FRAGMENT = "will be replaced by"


def normalize_repo_path(value: str) -> str:
    return value.replace("\\", "/").removeprefix("./").strip()


def repo_root(
    start: Path,
    *,
    marker_files: tuple[str, ...] = ("SCRIPTS.json",),
    marker_dirs: tuple[str, ...] = (),
    use_git: bool = True,
) -> Path:
    resolved = start.resolve()
    git_start = resolved if resolved.is_dir() else resolved.parent
    if use_git:
        completed = subprocess.run(
            ["git", "-C", str(git_start), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
        )
        if completed.returncode == 0 and completed.stdout.strip():
            return Path(completed.stdout.strip()).resolve()
    for candidate in [resolved, *resolved.parents]:
        if all((candidate / path).is_file() for path in marker_files) and all(
            (candidate / path).is_dir() for path in marker_dirs
        ):
            return candidate
    return resolved


def run_step(label: str, command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> int:
    print()
    print(f"==> {label}")
    completed = subprocess.run(command, cwd=cwd, env=env, check=False)
    if completed.returncode != 0:
        print(f"ERROR: {label} failed with exit code {completed.returncode}", file=sys.stderr)
    return completed.returncode


def git_lines(root: Path, args: list[str], *, allow_failure: bool = False) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        if allow_failure:
            return []
        raise RuntimeError(f"git {' '.join(args)} failed: {output.strip()}")
    return [
        normalize_repo_path(line.strip())
        for line in output.splitlines()
        if line.strip()
        and GIT_WARNING_FRAGMENT not in line
        and not line.lstrip().startswith("warning:")
    ]


def split_paths(values: list[str]) -> list[str]:
    return split_values(values, separators=(",", ";"), transform=normalize_repo_path, sort=True)


def changed_paths(
    root: Path,
    explicit: list[str] | None = None,
    *,
    diff_filter: str = "ACMRD",
    include_untracked: bool = True,
) -> list[str]:
    explicit_paths = split_paths(explicit or [])
    if explicit_paths:
        return explicit_paths
    if not (root / ".git").exists():
        return []
    paths: set[str] = set()
    for args in (
        ["diff", "--name-only", f"--diff-filter={diff_filter}"],
        ["diff", "--cached", "--name-only", f"--diff-filter={diff_filter}"],
    ):
        paths.update(git_lines(root, args))
    if include_untracked:
        paths.update(git_lines(root, ["ls-files", "--others", "--exclude-standard"]))
    return sorted(path for path in paths if path)
