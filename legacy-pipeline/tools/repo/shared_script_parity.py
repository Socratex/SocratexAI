#!/usr/bin/env python3
"""Audit script parity between a project tool root and an embedded pipeline tool root."""

from __future__ import annotations

import argparse
import hashlib
import fnmatch
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_SKIP_PARTS = {
    ".git",
    "__pycache__",
    "Python312",
    "python-installer",
    "tmp",
}
DEFAULT_SUFFIXES = {".py"}
THIN_ADAPTER_MARKERS = (
    "SocratexAI",
    "subprocess.run",
    "runpy.run_path",
    "execv",
    "execve",
)
MANAGED_TOOL_ADAPTER_MARKERS = (
    "project_runtime",
    "run_managed_tool",
)


def normalize(value: str) -> str:
    return value.replace("\\", "/").strip("/")


def split_values(values: list[str]) -> set[str]:
    result: set[str] = set()
    for value in values:
        for part in value.replace(";", ",").split(","):
            stripped = part.strip()
            if stripped:
                result.add(stripped)
    return result


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_skipped(path: Path, root: Path, skip_parts: set[str], suffixes: set[str]) -> bool:
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    if path.suffix.lower() not in suffixes:
        return True
    return bool(set(relative.parts) & skip_parts)


def script_files(root: Path, skip_parts: set[str], suffixes: set[str]) -> dict[str, Path]:
    files: dict[str, Path] = {}
    if not root.is_dir():
        return files
    for path in sorted(root.rglob("*")):
        if path.is_file() and not is_skipped(path, root, skip_parts, suffixes):
            files[path.relative_to(root).as_posix()] = path
    return files


def basename_index(files: dict[str, Path]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for relative in files:
        index[Path(relative).name].append(relative)
    return {name: sorted(paths) for name, paths in index.items()}


def is_thin_adapter(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if THIN_ADAPTER_MARKERS[0] in text and any(marker in text for marker in THIN_ADAPTER_MARKERS[1:]):
        return True
    return all(marker in text for marker in MANAGED_TOOL_ADAPTER_MARKERS)


def read_classifications(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    content = data.get("content", data) if isinstance(data, dict) else {}
    if not isinstance(content, dict):
        return {}
    entries: dict[str, dict[str, str]] = {}
    direct = content.get("drift_classifications", {})
    if isinstance(direct, dict):
        for key, value in direct.items():
            if isinstance(value, dict):
                entries[normalize(str(key))] = {
                    "classification": str(value.get("classification", "")).strip(),
                    "reason": str(value.get("reason", "")).strip(),
                }
    groups = content.get("classification_groups", [])
    if isinstance(groups, list):
        for group in groups:
            if not isinstance(group, dict):
                continue
            classification = str(group.get("classification", "")).strip()
            reason = str(group.get("reason", "")).strip()
            for key in group.get("left", []):
                entries[normalize(str(key))] = {"classification": classification, "reason": reason}
    return entries


def classification_for(
    left_relative: str,
    right_relative: str,
    classifications: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    keys = [
        left_relative,
        f"{left_relative} -> {right_relative}",
        Path(left_relative).name,
    ]
    for key in keys:
        if key in classifications:
            return classifications[key]
    for pattern, value in classifications.items():
        if fnmatch.fnmatch(left_relative, pattern) or fnmatch.fnmatch(f"{left_relative} -> {right_relative}", pattern):
            return value
    return None


def classify_pair(
    left_relative: str,
    left_path: Path,
    right_relative: str,
    right_path: Path,
    classifications: dict[str, dict[str, str]],
) -> dict[str, Any]:
    left_hash = sha256_file(left_path)
    right_hash = sha256_file(right_path)
    classification = classification_for(left_relative, right_relative, classifications)
    if left_hash == right_hash:
        status = "exact_copy"
    elif is_thin_adapter(left_path):
        status = "thin_adapter"
    elif classification:
        status = "classified_" + (classification.get("classification") or "drift")
    else:
        status = "drift"
    return {
        "left": left_relative,
        "right": right_relative,
        "left_hash": left_hash,
        "right_hash": right_hash,
        "status": status,
        "classification": classification.get("classification", "") if classification else "",
        "reason": classification.get("reason", "") if classification else "",
        "same_relative_path": left_relative == right_relative,
    }


def build_report(
    left_root: Path,
    right_root: Path,
    skip_parts: set[str],
    suffixes: set[str],
    classifications: dict[str, dict[str, str]],
) -> dict[str, Any]:
    left_files = script_files(left_root, skip_parts, suffixes)
    right_files = script_files(right_root, skip_parts, suffixes)
    right_by_name = basename_index(right_files)
    paired_right: set[str] = set()
    pairs: list[dict[str, Any]] = []
    root_only: list[str] = []

    for left_relative, left_path in left_files.items():
        if left_relative in right_files:
            pairs.append(classify_pair(left_relative, left_path, left_relative, right_files[left_relative], classifications))
            paired_right.add(left_relative)
            continue
        candidates = right_by_name.get(Path(left_relative).name, [])
        if candidates:
            right_relative = candidates[0]
            pairs.append(classify_pair(left_relative, left_path, right_relative, right_files[right_relative], classifications))
            paired_right.add(right_relative)
        else:
            root_only.append(left_relative)

    right_only = sorted(relative for relative in right_files if relative not in paired_right)
    failures = [pair for pair in pairs if pair["status"] == "drift"]
    counts: dict[str, int] = defaultdict(int)
    for pair in pairs:
        counts[pair["status"]] += 1
    return {
        "schema": "socratex-shared-script-parity/v1",
        "status": "fail" if failures else "pass",
        "left_root": str(left_root),
        "right_root": str(right_root),
        "summary": {
            "pairs": len(pairs),
            "exact_copy": counts["exact_copy"],
            "thin_adapter": counts["thin_adapter"],
            "classified": sum(count for status, count in counts.items() if status.startswith("classified_")),
            "drift": counts["drift"],
            "left_only": len(root_only),
            "right_only": len(right_only),
        },
        "pairs": pairs,
        "left_only": sorted(root_only),
        "right_only": right_only,
        "failures": failures,
    }


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def print_report(report: dict[str, Any], max_examples: int) -> None:
    summary = report["summary"]
    print(f"status: {report['status']}")
    print(f"pairs: {summary['pairs']}")
    print(f"exact copies: {summary['exact_copy']}")
    print(f"thin adapters: {summary['thin_adapter']}")
    print(f"classified drift: {summary['classified']}")
    print(f"drift: {summary['drift']}")
    print(f"left-only: {summary['left_only']}")
    print(f"right-only: {summary['right_only']}")
    if report["failures"]:
        print("drift examples:")
        for pair in report["failures"][:max_examples]:
            print(f" - {pair['left']} != {pair['right']}")
    if report["left_only"]:
        print("left-only examples:")
        for relative in report["left_only"][:max_examples]:
            print(f" - {relative}")
    if report["right_only"]:
        print("right-only examples:")
        for relative in report["right_only"][:max_examples]:
            print(f" - {relative}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit root/project script parity against an embedded pipeline package.")
    parser.add_argument("--project-root", default=".", help="Project root used for default left/right roots.")
    parser.add_argument("--left-root", default="", help="Project tool root. Defaults to PROJECT/Tools.")
    parser.add_argument("--right-root", default="", help="Embedded pipeline tool root. Defaults to PROJECT/SocratexAI/tools.")
    parser.add_argument(
        "--classification-file",
        default="",
        help="Optional JSON file that classifies allowed project-specific drifts. Defaults to PROJECT/Tools/SHARED-SCRIPT-PARITY.json when present.",
    )
    parser.add_argument("--skip-part", action="append", default=[], help="Path segment to skip; comma-separated values are accepted.")
    parser.add_argument("--suffix", action="append", default=[], help="File suffix to include; defaults to .py.")
    parser.add_argument("--json", action="store_true", help="Print full JSON report.")
    parser.add_argument("--write-report", default="", help="Optional JSON report output path.")
    parser.add_argument("--max-examples", type=int, default=25, help="Maximum text examples per section.")
    args = parser.parse_args()

    project_root = Path(args.project_root).expanduser().resolve()
    left_root = Path(args.left_root).expanduser().resolve() if args.left_root else project_root / "Tools"
    right_root = Path(args.right_root).expanduser().resolve() if args.right_root else project_root / "SocratexAI" / "tools"
    classification_file = (
        Path(args.classification_file).expanduser().resolve()
        if args.classification_file
        else project_root / "Tools" / "SHARED-SCRIPT-PARITY.json"
    )
    skip_parts = DEFAULT_SKIP_PARTS | split_values(args.skip_part)
    suffixes = split_values(args.suffix) if args.suffix else set(DEFAULT_SUFFIXES)
    report = build_report(left_root, right_root, skip_parts, suffixes, read_classifications(classification_file))
    report["classification_file"] = str(classification_file) if classification_file.is_file() else ""
    if args.write_report:
        write_report(Path(args.write_report).expanduser().resolve(), report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=4))
    else:
        print_report(report, args.max_examples)
    return 0 if report["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
