#!/usr/bin/env python3
"""Fail when tracked automation still uses the retired command runtime."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import git_lines as shared_git_lines  # noqa: E402


BLOCKED_EXTENSION = "." + "ps1"
BLOCKED_TERMS = ("pw" + "sh", "power" + "shell")
BLOCKED_PATTERN = re.compile(
    r"(?i)(?<![a-z0-9_])("
    + re.escape(BLOCKED_TERMS[0])
    + r"|"
    + re.escape(BLOCKED_TERMS[1])
    + r"(?:\.exe)?|"
    + re.escape(BLOCKED_EXTENSION)
    + r")(?![a-z0-9_])"
)
DEFAULT_SKIP_PARTS = {
    ".git",
    "_PROMPTS",
    "AI-compiled",
    "audits",
    "cache",
    "CHANGELOG.md",
    "docs-tech",
    "Python312",
    "python-installer",
    "tmp",
    "_PLAN.json",
}
TEXT_SUFFIX_ALLOWLIST = {
    ".bat",
    ".cfg",
    ".gd",
    ".gitignore",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sh",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}


def git_lines(root: Path, args: list[str]) -> list[str]:
    return shared_git_lines(root, args)


def tracked_files(root: Path) -> list[str]:
    return git_lines(root, ["ls-files"])


def is_skipped(path: str, extra_skip: set[str]) -> bool:
    parts = set(Path(path).parts)
    return bool(parts & (DEFAULT_SKIP_PARTS | extra_skip))


def is_probably_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIX_ALLOWLIST:
        return True
    try:
        sample = path.read_bytes()[:4096]
    except OSError:
        return False
    return b"\x00" not in sample


def read_lines(path: Path) -> list[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return []
    except OSError:
        return []


def compact_line(line: str, limit: int) -> str:
    stripped = line.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."


def find_reference_hits(root: Path, paths: list[str], max_line_length: int, extra_skip: set[str]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for rel in paths:
        if is_skipped(rel, extra_skip):
            continue
        path = root / rel
        if not path.is_file() or not is_probably_text(path):
            continue
        for line_number, line in enumerate(read_lines(path), start=1):
            match = BLOCKED_PATTERN.search(line)
            if not match:
                continue
            hits.append(
                {
                    "path": rel,
                    "line": line_number,
                    "token": match.group(1),
                    "text": compact_line(line, max_line_length),
                }
            )
    return hits


def summarize_by_top_path(paths: list[str]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for rel in paths:
        parts = Path(rel).parts
        counts[parts[0] if parts else rel] += 1
    return dict(sorted(counts.items()))


def build_report(root: Path, max_line_length: int, extra_skip: set[str]) -> dict[str, Any]:
    paths = tracked_files(root)
    blocked_files = [
        path
        for path in paths
        if path.lower().endswith(BLOCKED_EXTENSION) and not is_skipped(path, extra_skip)
    ]
    reference_hits = find_reference_hits(root, paths, max_line_length, extra_skip)
    return {
        "schema": "socratex-script-runtime-gate/v1",
        "root": str(root),
        "status": "fail" if blocked_files or reference_hits else "pass",
        "summary": {
            "tracked_files": len(paths),
            "blocked_script_files": len(blocked_files),
            "blocked_reference_hits": len(reference_hits),
            "blocked_script_files_by_top_path": summarize_by_top_path(blocked_files),
            "blocked_reference_hits_by_top_path": summarize_by_top_path([hit["path"] for hit in reference_hits]),
        },
        "blocked_script_files": blocked_files,
        "blocked_reference_hits": reference_hits,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def print_text_report(report: dict[str, Any], max_examples: int) -> None:
    summary = report["summary"]
    print(f"status: {report['status']}")
    print(f"tracked files: {summary['tracked_files']}")
    print(f"blocked script files: {summary['blocked_script_files']}")
    print(f"blocked reference hits: {summary['blocked_reference_hits']}")
    if summary["blocked_script_files_by_top_path"]:
        print("blocked script files by top path:")
        for key, value in summary["blocked_script_files_by_top_path"].items():
            print(f" - {key}: {value}")
    if summary["blocked_reference_hits_by_top_path"]:
        print("blocked reference hits by top path:")
        for key, value in summary["blocked_reference_hits_by_top_path"].items():
            print(f" - {key}: {value}")
    if report["blocked_script_files"]:
        print("blocked script file examples:")
        for path in report["blocked_script_files"][:max_examples]:
            print(f" - {path}")
    if report["blocked_reference_hits"]:
        print("blocked reference examples:")
        for hit in report["blocked_reference_hits"][:max_examples]:
            print(f" - {hit['path']}:{hit['line']} [{hit['token']}] {hit['text']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check tracked files for retired automation runtime debt.")
    parser.add_argument("--repo-root", default=".", help="Repository root to inspect.")
    parser.add_argument("--json", action="store_true", help="Print the full report as JSON.")
    parser.add_argument("--write-report", default="", help="Optional JSON report output path.")
    parser.add_argument("--max-examples", type=int, default=25, help="Maximum text examples to print.")
    parser.add_argument("--max-line-length", type=int, default=180, help="Maximum captured line length.")
    parser.add_argument(
        "--skip-part",
        action="append",
        default=[],
        help="Additional path segment to skip, for local exploratory runs only.",
    )
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    if not (root / ".git").exists():
        raise SystemExit(f"Repository root is not a git checkout: {root}")
    report = build_report(root, args.max_line_length, set(args.skip_part))
    if args.write_report:
        write_report(Path(args.write_report), report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=4))
    else:
        print_text_report(report, args.max_examples)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
