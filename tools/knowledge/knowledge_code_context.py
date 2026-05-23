#!/usr/bin/env python3
"""Load full compiled code-guidance context and write the code-context gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


BASE_CODE_GUIDANCE_TAGS = [
    "engineering",
    "coding",
    "architecture",
    "best-practices",
    "borrowed-before-invented",
    "production-grade",
    "ddd-adiv",
    "future-first",
    "data-first",
    "ownership",
    "runtime",
    "diagnostics",
    "performance",
    "verification",
    "domain_modeling",
    "readability",
]


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def normalize_values(values: list[str]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item and item not in normalized:
                normalized.append(item)
    return sorted(normalized)


def run_tool(repo_root: Path, args: list[str], fallback_args: list[str] | None = None) -> None:
    tool = repo_root / "tools/knowledge/knowledge_index.py"
    result = subprocess.run(
        [sys.executable, "-B", str(tool), *args],
        cwd=repo_root,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return
    if fallback_args is None:
        raise SystemExit(result.returncode)
    print(
        f"WARNING: SQLite knowledge select failed with exit code {result.returncode}. "
        "Falling back to compiled JSON table knowledge.",
        file=sys.stderr,
    )
    fallback = subprocess.run(
        [sys.executable, "-B", str(tool), *fallback_args],
        cwd=repo_root,
        text=True,
        check=False,
    )
    if fallback.returncode != 0:
        raise SystemExit(result.returncode)


def git_head(repo_root: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git rev-parse HEAD failed: {message}")
    return result.stdout.strip()


def write_gate(repo_root: Path, selected_tags: list[str], views: list[str], additional_tags: list[str], output_format: str) -> None:
    gate_path = repo_root / "ignored/code_context_gate.json"
    gate = {
        "schema": 1,
        "tool": "knowledge_code_context",
        "loaded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_head": git_head(repo_root),
        "base_tags": BASE_CODE_GUIDANCE_TAGS,
        "additional_tags": additional_tags,
        "selected_tags": selected_tags,
        "views": views,
        "format": output_format,
        "full_base_loaded": True,
    }
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--views", "-Views", nargs="*", default=[])
    parser.add_argument("--additional-tags", "-AdditionalTags", nargs="*", default=[])
    parser.add_argument("--format", "-Format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--skip-check", "-SkipCheck", action="store_true")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    views = normalize_values(args.views)
    additional_tags = normalize_values(args.additional_tags)
    selected_tags = normalize_values([*BASE_CODE_GUIDANCE_TAGS, *additional_tags])

    if not args.skip_check:
        run_tool(repo_root, ["check", "--repo-root", str(repo_root)])

    select_args = [
        "select",
        "--repo-root",
        str(repo_root),
        "--tags",
        *selected_tags,
        "--match",
        "any",
        "--type",
        "rule",
        "--format",
        args.format,
    ]
    fallback_args = [
        "file-select",
        "--repo-root",
        str(repo_root),
        "--tags",
        *selected_tags,
        "--match",
        "any",
        "--type",
        "rule",
        "--format",
        args.format,
    ]
    run_tool(repo_root, select_args, fallback_args=fallback_args)

    for view in views:
        run_tool(
            repo_root,
            ["select", "--repo-root", str(repo_root), "--view", view, "--format", args.format],
        )

    write_gate(repo_root, selected_tags, views, additional_tags, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
