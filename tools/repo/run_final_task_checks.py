#!/usr/bin/env python3
"""Run Python-first final task checks for SocratexPipeline repositories."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Any

from repo_tool_helpers import changed_text_paths, package_root
from shared.repo_helpers import changed_paths as git_changed_paths
from shared.repo_helpers import git_lines, repo_root, run_step as run


def normalize_changed_text(root: Path, tools: Path, label: str, skip: bool) -> int:
    if skip:
        return 0
    paths = changed_text_paths(root)
    if not paths:
        return 0
    return run(
        label,
        [
            sys.executable,
            "-B",
            str(tools / "text" / "normalize_text_files.py"),
            "--repo-root",
            str(root),
            *paths,
        ],
        root,
    )


def print_task_snapshot(root: Path) -> int:
    print("# Task Snapshot")
    print(f"Repository: {root}")
    branch = git_lines(root, ["branch", "--show-current"], allow_failure=True)
    print(f"Branch: {branch[0] if branch else '(unknown)'}")
    status = git_lines(root, ["status", "--short"], allow_failure=True)
    print("\n## Git Status Short")
    print("\n".join(status) if status else "(clean)")
    return 0


def ensure_no_python_cache(root: Path) -> int:
    caches = sorted(path.relative_to(root).as_posix() for path in root.rglob("__pycache__") if path.is_dir())
    if caches:
        print("ERROR: Python bytecode cache directories found:")
        for path in caches[:50]:
            print(f" - {path}")
        if len(caches) > 50:
            print(f" - ... {len(caches) - 50} more")
        return 1
    print("OK: no __pycache__ directories found.")
    return 0


def clean_python_cache(root: Path) -> int:
    caches = sorted(path for path in root.rglob("__pycache__") if path.is_dir())
    for path in caches:
        def retry_after_chmod(function: Any, retry_path: str, exc_info: Any) -> None:
            del exc_info
            target = Path(retry_path)
            target.chmod(0o700)
            function(retry_path)

        shutil.rmtree(path, onexc=retry_after_chmod)
    print(f"OK: removed {len(caches)} Python bytecode cache directorie(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Python-first final task checks.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to nearest SocratexPipeline root.")
    parser.add_argument("--quality", action="store_true", help="Run the Python quality gate.")
    parser.add_argument("--quality-command", nargs="*", default=[], help="Explicit quality command passed to run_quality_gate.py.")
    parser.add_argument("--quality-command-names", nargs="*", default=[], help="QUALITY-GATE.json command names passed to run_quality_gate.py.")
    parser.add_argument("--strict-audit", action="store_true", help="Passed through to Python audit docs for parity.")
    parser.add_argument("--no-audit", action="store_true", help="Skip document audit.")
    parser.add_argument("--no-line-index", action="store_true", help="Skip code line index refresh/check.")
    parser.add_argument("--no-normalize", action="store_true", help="Skip changed text normalization.")
    parser.add_argument("--no-doc-cache", action="store_true", help="Skip document cache refresh.")
    parser.add_argument("--no-output", action="store_true", help="Skip OUTPUT snapshot.")
    parser.add_argument("--no-sound", action="store_true", help="Accepted for CLI parity; Python output snapshot is silent.")
    parser.add_argument("--require-task-flow-evidence", action="store_true", help="Validate closure evidence JSON.")
    parser.add_argument("--task-flow-evidence-path", default="", help="Closure evidence JSON path.")
    parser.add_argument("--no-compiled-context-check", action="store_true", help="Skip compiled-context anchor check.")
    parser.add_argument("--no-cache-check", action="store_true", help="Skip __pycache__ check.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root(Path(__file__).resolve())
    tools = package_root() / "tools"
    python = sys.executable

    print("==> Python final task checks")
    if normalize_changed_text(root, tools, "text normalization refresh", args.no_normalize) != 0:
        return 1

    steps: list[tuple[str, list[str]]] = [
        ("document cache refresh", [python, "-B", str(tools / "documents" / "build_document_cache.py"), "--repo-root", str(root)]),
        ("code line index refresh", [python, "-B", str(tools / "codebase" / "update_code_line_index.py"), "--root", str(root), "--changed-only"]),
        ("pipeline bootstrap index refresh", [python, "-B", str(tools / "pipeline" / "pipeline_bootstrap_index.py"), "--repo-root", str(root)]),
        ("compiled AI instructions refresh", [python, "-B", str(tools / "pipeline" / "rebuild_ai_compiled_context.py"), "--repo-root", str(root)]),
        ("task snapshot", [python, "-B", str(tools / "repo" / "task_snapshot.py"), "--root", str(root)]),
        ("git diff --check", ["git", "diff", "--check"]),
        ("task flow audit", [python, "-B", str(tools / "repo" / "task_flow_audit.py"), "--project-root", str(root)]),
        ("pipeline feature list guard", [python, "-B", str(tools / "repo" / "check_pipeline_featurelist_update.py"), "--repo-root", str(root)]),
    ]
    if args.no_doc_cache:
        steps = [(label, command) for label, command in steps if label != "document cache refresh"]
    if args.no_line_index:
        steps = [(label, command) for label, command in steps if label != "code line index refresh"]
    if args.require_task_flow_evidence:
        for index, (label, command) in enumerate(steps):
            if label == "task flow audit":
                command = [*command, "--require-closure-evidence"]
                if args.task_flow_evidence_path:
                    command.extend(["--closure-evidence-path", args.task_flow_evidence_path])
                steps[index] = (label, command)
                break
    if not args.no_compiled_context_check:
        steps.append(("compiled context check", [python, "-B", str(tools / "pipeline" / "check_ai_compiled_context.py"), "--repo-root", str(root)]))
    if not args.no_line_index:
        steps.append(("code line index check", [python, "-B", str(tools / "codebase" / "update_code_line_index.py"), "--root", str(root), "--changed-only", "--check"]))
    if not args.no_audit:
        audit_command = [python, "-B", str(tools / "documents" / "audit_docs.py"), "--repo-root", str(root)]
        if args.strict_audit:
            audit_command.append("--strict")
        steps.append(("audit docs", audit_command))
    if args.quality:
        quality_command = [python, "-B", str(tools / "quality" / "run_quality_gate.py"), "--repo-root", str(root)]
        if args.quality_command:
            quality_command.append("--command")
            quality_command.extend(args.quality_command)
        if args.quality_command_names:
            quality_command.append("--command-names")
            quality_command.extend(args.quality_command_names)
        steps.append(("quality gate", quality_command))
    if not args.no_cache_check:
        steps.append(("Python cache cleanup", []))
        steps.append(("Python cache check", []))
    if not args.no_output:
        output_command = [python, "-B", str(tools / "repo" / "end_prompt_snapshot.py"), "--root", str(root)]
        if args.no_sound:
            output_command.append("--no-sound")
        steps.append(("OUTPUT snapshot", output_command))

    for label, command in steps:
        if label == "code line index check" and normalize_changed_text(root, tools, "post-generator text normalization refresh", args.no_normalize) != 0:
            return 1
        if label == "Python cache check":
            code = ensure_no_python_cache(root)
        elif label == "Python cache cleanup":
            code = clean_python_cache(root)
        else:
            code = run(label, command, root)
        if code != 0:
            return code

    changed = git_changed_paths(root)
    if changed:
        print("\nChanged path count:", len(changed))
        for path in changed[:80]:
            print(f"- {path}")
        if len(changed) > 80:
            print(f"- ... {len(changed) - 80} more")
    print("\nOK: Python final task checks completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
