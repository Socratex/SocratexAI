#!/usr/bin/env python3
"""Compact changed-path task check with Python-only tooling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_tool_helpers import changed_text_paths, repo_root, run, split_values


def text_normalization(root: Path, paths: list[str], *, check: bool) -> int:
    if not paths:
        print()
        print(f"==> text normalization {'check' if check else 'refresh'}")
        print("skipped; no changed text paths and no --paths were provided")
        return 0
    command = [sys.executable, "-B", str(root / "tools" / "text" / "normalize_text_files.py"), "--repo-root", str(root)]
    if check:
        command.append("--check")
    command.extend(paths)
    return run(f"text normalization {'check' if check else 'refresh'}", command, root)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run compact changed-path task checks.")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--project-root", "-ProjectRoot", default="")
    parser.add_argument("--audit", "-Audit", action="store_true")
    parser.add_argument("--markdown-emoji", "-MarkdownEmoji", action="store_true")
    parser.add_argument("--no-line-index", "-NoLineIndex", action="store_true")
    parser.add_argument("--no-normalize", "-NoNormalize", action="store_true")
    parser.add_argument("--no-stat", "-NoStat", action="store_true")
    parser.add_argument("--no-status", "-NoStatus", action="store_true")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    check_paths = split_values(args.paths) if args.paths else changed_text_paths(root)

    steps: list[tuple[str, list[str]]] = []
    code_gate = root / "tools" / "codebase" / "check_code_context_gate.py"
    if code_gate.is_file():
        if run("compiled code-guidance context gate", [sys.executable, "-B", str(code_gate), "--paths", ",".join(check_paths)], root) != 0:
            return 1
    else:
        print("ERROR: missing Python code context gate: tools/codebase/check_code_context_gate.py", file=sys.stderr)
        return 1
    if args.project_root:
        design_gate = root / "tools" / "codebase" / "check_project_design_context_gate.py"
        if not design_gate.is_file():
            print("ERROR: missing Python project design context gate: tools/codebase/check_project_design_context_gate.py", file=sys.stderr)
            return 1
        if run(
            "per-project design context gate",
            [sys.executable, "-B", str(design_gate), "--project-root", str(Path(args.project_root).resolve()), "--paths", ",".join(check_paths)],
            root,
        ) != 0:
            return 1
    if args.markdown_emoji:
        print("ERROR: --markdown-emoji has no Python implementation in this write-set yet.", file=sys.stderr)
        return 2
    if not args.no_normalize:
        if text_normalization(root, check_paths, check=False) != 0:
            return 1
        json_normalizer = root / "tools" / "text" / "normalize_json_files.py"
        if json_normalizer.is_file():
            steps.append(("JSON normalization refresh", [sys.executable, "-B", str(json_normalizer), "--repo-root", str(root)]))
    steps.append(("pipeline bootstrap index refresh", [sys.executable, "-B", str(root / "tools" / "pipeline" / "pipeline_bootstrap_index.py"), "--repo-root", str(root)]))
    if not args.no_normalize:
        if text_normalization(root, check_paths, check=True) != 0:
            return 1
        json_normalizer = root / "tools" / "text" / "normalize_json_files.py"
        if json_normalizer.is_file():
            steps.append(("JSON normalization check", [sys.executable, "-B", str(json_normalizer), "--repo-root", str(root), "--check"]))
    steps.append(("pipeline bootstrap index check", [sys.executable, "-B", str(root / "tools" / "pipeline" / "pipeline_bootstrap_index.py"), "--repo-root", str(root), "--check"]))
    diff_command = ["git", "-c", "core.safecrlf=false", "diff", "--check"]
    if check_paths:
        diff_command.extend(["--", *check_paths])
    steps.append(("git diff --check", diff_command))
    if check_paths:
        steps.append(("UTF-8 write check", [sys.executable, "-B", str(root / "tools" / "text" / "check_utf8_writes.py"), "--repo-root", str(root), "--paths", ",".join(check_paths)]))
        steps.append(("pipeline feature list guard", [sys.executable, "-B", str(root / "tools" / "repo" / "check_pipeline_featurelist_update.py"), "--repo-root", str(root), "--paths", ",".join(check_paths)]))
    if not args.no_line_index:
        steps.append(("code line index refresh", [sys.executable, "-B", str(root / "tools" / "codebase" / "update_code_line_index.py"), "--root", str(root), "--changed-only"]))
        if not args.no_normalize:
            if text_normalization(root, check_paths, check=False) != 0:
                return 1
        steps.append(("code line index check", [sys.executable, "-B", str(root / "tools" / "codebase" / "update_code_line_index.py"), "--root", str(root), "--changed-only", "--check"]))
    if args.audit:
        steps.append(("compiled AI instructions refresh", [sys.executable, "-B", str(root / "tools" / "pipeline" / "rebuild_ai_compiled_context.py"), "--repo-root", str(root)]))
        steps.append(("audit docs", [sys.executable, "-B", str(root / "tools" / "documents" / "audit_docs.py"), "--repo-root", str(root)]))
    if not args.no_stat:
        steps.append(("git diff --stat", ["git", "diff", "--stat"]))
    if not args.no_status:
        steps.append(("git status --short", ["git", "status", "--short"]))

    for label, command in steps:
        if run(label, command, root) != 0:
            return 1
    print()
    print("OK: task check completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
