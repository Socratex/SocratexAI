from __future__ import annotations

import argparse
import sys
from pathlib import Path

from document_wrapper_helpers import repo_root, split_values
from shared.repo_helpers import run_step


def relative_path(root: Path, value: str) -> str:
    path = Path(value)
    resolved = path.resolve() if path.is_absolute() else (root / path).resolve()
    try:
        return resolved.relative_to(root.resolve()).as_posix()
    except ValueError:
        return resolved.as_posix()


def run(label: str, command: list[str], cwd: Path) -> int:
    return run_step(label, command, cwd)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Python document post-edit checks.")
    parser.add_argument("positional_paths", nargs="*")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--no-cache", "-NoCache", action="store_true")
    parser.add_argument("--audit", "-Audit", action="store_true")
    parser.add_argument("--no-audit", "-NoAudit", action="store_true")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root()
    paths = [relative_path(root, value) for value in split_values(args.paths + args.positional_paths)]
    if not paths:
        raise SystemExit("--paths is required.")

    normalize = root / "tools" / "text" / "normalize_text_files.py"
    if run("text normalization refresh", [sys.executable, "-B", str(normalize), "--repo-root", str(root), *paths], root) != 0:
        return 1

    check_paths = list(paths)
    has_yaml = any(path.endswith((".yaml", ".yml")) for path in paths)
    if has_yaml and not args.no_cache:
        build_cache = root / "tools" / "documents" / "build_document_cache.py"
        if run("document cache rebuild", [sys.executable, "-B", str(build_cache), "--repo-root", str(root)], root) != 0:
            return 1
        cache_path = root / "docs-tech" / "cache" / "doc_index.json"
        if cache_path.is_file():
            check_paths.append("docs-tech/cache/doc_index.json")

    check_task = root / "tools" / "repo" / "check_task.py"
    command = [
        sys.executable,
        "-B",
        str(check_task),
        "--paths",
        *check_paths,
        "--no-normalize",
        "--no-line-index",
        "--no-stat",
        "--no-status",
    ]
    if args.audit and not args.no_audit:
        command.append("--audit")
    if run("document task check", command, root) != 0:
        return 1

    print(f"OK: document edit pipeline completed for {len(paths)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
