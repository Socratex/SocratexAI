#!/usr/bin/env python3
"""Load full compiled code-guidance context and write the code-context gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio, split_values as split_cli_values  # noqa: E402
from shared.repo_helpers import git_lines  # noqa: E402


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


def normalize_values(values: list[str]) -> list[str]:
    return split_cli_values(values, sort=True)


def run_tool(repo_root: Path, args: list[str], fallback_args: list[str] | None = None) -> None:
    tool = Path(__file__).resolve().with_name("knowledge_index.py")
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
    lines = git_lines(repo_root, ["rev-parse", "HEAD"])
    return lines[0] if lines else ""


def write_gate(
    repo_root: Path,
    base_tags: list[str],
    selected_tags: list[str],
    views: list[str],
    additional_tags: list[str],
    output_format: str,
) -> None:
    gate_path = repo_root / "ignored/code_context_gate.json"
    gate = {
        "schema": 1,
        "tool": "knowledge_code_context",
        "loaded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_head": git_head(repo_root),
        "base_tags": base_tags,
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
    parser.add_argument("--repo-root", "-RepoRoot", default="")
    parser.add_argument("--db", default="")
    parser.add_argument("--manifest", default="")
    parser.add_argument("--file-dir", default="")
    parser.add_argument("--base-tags", "-BaseTags", nargs="*", default=[])
    parser.add_argument("--views", "-Views", nargs="*", default=[])
    parser.add_argument("--additional-tags", "-AdditionalTags", nargs="*", default=[])
    parser.add_argument("--format", "-Format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--skip-check", "-SkipCheck", action="store_true")
    return parser.parse_args()


def index_artifact_args(args: argparse.Namespace) -> list[str]:
    forwarded: list[str] = []
    if args.db:
        forwarded.extend(["--db", args.db])
    if args.manifest:
        forwarded.extend(["--manifest", args.manifest])
    if args.file_dir:
        forwarded.extend(["--file-dir", args.file_dir])
    return forwarded


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    base_tags = normalize_values(args.base_tags) if args.base_tags else BASE_CODE_GUIDANCE_TAGS
    views = normalize_values(args.views)
    additional_tags = normalize_values(args.additional_tags)
    selected_tags = normalize_values([*base_tags, *additional_tags])
    artifact_args = index_artifact_args(args)

    if not args.skip_check:
        run_tool(repo_root, ["check", "--repo-root", str(repo_root), *artifact_args])

    select_args = [
        "select",
        "--repo-root",
        str(repo_root),
        *artifact_args,
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
        *artifact_args,
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
            ["select", "--repo-root", str(repo_root), *artifact_args, "--view", view, "--format", args.format],
        )

    write_gate(repo_root, base_tags, selected_tags, views, additional_tags, args.format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
