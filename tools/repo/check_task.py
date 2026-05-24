#!/usr/bin/env python3
"""Compact changed-path task check with Python-only tooling."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from repo_tool_helpers import changed_text_paths, repo_root, run, split_values


def text_normalization(root: Path, tools_dir: str, paths: list[str], *, check: bool) -> int:
    if not paths:
        print()
        print(f"==> text normalization {'check' if check else 'refresh'}")
        print("skipped; no changed text paths and no --paths were provided")
        return 0
    command = [sys.executable, "-B", str(tool_path(root, tools_dir, "text/normalize_text_files.py")), "--repo-root", str(root)]
    if check:
        command.append("--check")
    command.extend(paths)
    return run(f"text normalization {'check' if check else 'refresh'}", command, root)


def tool_path(root: Path, tools_dir: str, relative: str) -> Path:
    return root / tools_dir / relative


def add_optional_root(command: list[str], root: Path, option: str) -> None:
    if option.strip():
        command.extend([option, str(root)])


def main() -> int:
    parser = argparse.ArgumentParser(description="Run compact changed-path task checks.")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--project-root", "-ProjectRoot", default="")
    parser.add_argument("--tools-dir", default="tools", help="Tool directory relative to the repository root.")
    parser.add_argument("--line-index-root-option", default="--root", help="Root option supported by update_code_line_index.py; pass an empty value when unsupported.")
    parser.add_argument("--utf8-root-option", default="--repo-root", help="Root option supported by check_utf8_writes.py; pass an empty value when unsupported.")
    parser.add_argument("--no-featurelist-check", action="store_true")
    parser.add_argument("--no-utf8-check", action="store_true")
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
    tools_dir = args.tools_dir.strip().strip("/\\") or "tools"

    steps: list[tuple[str, list[str]]] = []
    code_gate = tool_path(root, tools_dir, "codebase/check_code_context_gate.py")
    if code_gate.is_file():
        if run("compiled code-guidance context gate", [sys.executable, "-B", str(code_gate), "--paths", ",".join(check_paths)], root) != 0:
            return 1
    else:
        print("ERROR: missing Python code context gate: tools/codebase/check_code_context_gate.py", file=sys.stderr)
        return 1
    if args.project_root:
        design_gate = tool_path(root, tools_dir, "codebase/check_project_design_context_gate.py")
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
        if text_normalization(root, tools_dir, check_paths, check=False) != 0:
            return 1
        json_normalizer = tool_path(root, tools_dir, "text/normalize_json_files.py")
        if json_normalizer.is_file():
            steps.append(("JSON normalization refresh", [sys.executable, "-B", str(json_normalizer), "--repo-root", str(root)]))
    steps.append(("pipeline bootstrap index refresh", [sys.executable, "-B", str(tool_path(root, tools_dir, "pipeline/pipeline_bootstrap_index.py")), "--repo-root", str(root)]))
    if not args.no_normalize:
        if text_normalization(root, tools_dir, check_paths, check=True) != 0:
            return 1
        json_normalizer = tool_path(root, tools_dir, "text/normalize_json_files.py")
        if json_normalizer.is_file():
            steps.append(("JSON normalization check", [sys.executable, "-B", str(json_normalizer), "--repo-root", str(root), "--check"]))
    steps.append(("pipeline bootstrap index check", [sys.executable, "-B", str(tool_path(root, tools_dir, "pipeline/pipeline_bootstrap_index.py")), "--repo-root", str(root), "--check"]))
    diff_command = ["git", "-c", "core.safecrlf=false", "diff", "--check"]
    if check_paths:
        diff_command.extend(["--", *check_paths])
    steps.append(("git diff --check", diff_command))
    if check_paths:
        if not args.no_utf8_check:
            utf8_command = [sys.executable, "-B", str(tool_path(root, tools_dir, "text/check_utf8_writes.py")), "--paths", ",".join(check_paths)]
            add_optional_root(utf8_command, root, args.utf8_root_option)
            steps.append(("UTF-8 write check", utf8_command))
        featurelist_check = tool_path(root, tools_dir, "repo/check_pipeline_featurelist_update.py")
        if not args.no_featurelist_check and featurelist_check.is_file():
            steps.append(("pipeline feature list guard", [sys.executable, "-B", str(featurelist_check), "--repo-root", str(root), "--paths", ",".join(check_paths)]))
        elif not args.no_featurelist_check:
            print(f"WARN: featurelist check unavailable: {featurelist_check}", file=sys.stderr)
    if not args.no_line_index:
        line_index = tool_path(root, tools_dir, "codebase/update_code_line_index.py")
        line_index_refresh = [sys.executable, "-B", str(line_index)]
        add_optional_root(line_index_refresh, root, args.line_index_root_option)
        line_index_refresh.append("--changed-only")
        steps.append(("code line index refresh", line_index_refresh))
        if not args.no_normalize:
            if text_normalization(root, tools_dir, check_paths, check=False) != 0:
                return 1
        line_index_check = [sys.executable, "-B", str(line_index)]
        add_optional_root(line_index_check, root, args.line_index_root_option)
        line_index_check.extend(["--changed-only", "--check"])
        steps.append(("code line index check", line_index_check))
    if args.audit:
        steps.append(("compiled AI instructions refresh", [sys.executable, "-B", str(tool_path(root, tools_dir, "pipeline/rebuild_ai_compiled_context.py")), "--repo-root", str(root)]))
        steps.append(("audit docs", [sys.executable, "-B", str(tool_path(root, tools_dir, "documents/audit_docs.py")), "--repo-root", str(root)]))
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
