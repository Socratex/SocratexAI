#!/usr/bin/env python3
"""Derive compact knowledge tags from user text."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


DEFAULT_TAGS = ["engineering", "workflow", "docs-workflow"]

RULES = {
    "architecture": [
        "architecture",
        "architect",
        "architekt",
        "boundary",
        "boundaries",
        "ownership",
        "contract",
        "ddd",
        "adiv",
        "design",
        "runtime",
        "source of truth",
    ],
    "coding": ["code", "coding", "program", "script", "implement", "implementation", "refactor", "review", "bugfix", "function", "class"],
    "compiled-context": ["compiled", "skompil", "ai-compiled", "context layer", "compiled context", "dyrektyw", "directive", "instruction"],
    "knowledge": ["knowledge", "sqlite", "tag", "tags", "notat", "note", "notes", "selector", "context", "kontekst"],
    "debugging": ["bug", "error", "crash", "console", "log", "trace", "diagnostic", "diagnost"],
    "performance": ["performance", "fps", "memory", "profiler", "budget", "hot path"],
    "domain_modeling": ["domain_modeling", "world", "chunk", "biome", "terrain", "route"],
    "persistence": ["save", "load", "persistence", "persistent", "reconstruction", "stable id"],
    "verification": ["test", "check", "verify", "verification", "audit", "quality gate", "gate"],
    "gamedev": ["game", "gameplay", "combat", "movement", "camera", "collision", "traversal"],
    "documentation": ["doc", "docs", "document", "markdown", "json", "changelog", "featurelist"],
    "planning": ["plan", "roadmap", "priority", "todo", "pass", "continue"],
}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def normalize_tag(tag: str) -> str:
    return tag.strip().lower()


def append_tag(tags: list[str], tag: str) -> None:
    value = normalize_tag(tag)
    if value and value not in tags:
        tags.append(value)


def known_tags(repo_root: Path) -> set[str]:
    manifest_path = repo_root / "AI-compiled/project/knowledge-manifest.json"
    if not manifest_path.is_file():
        return set()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    return {
        normalize_tag(str(row.get("tag", "")))
        for row in manifest.get("tags", [])
        if isinstance(row, dict) and str(row.get("tag", "")).strip()
    }


def derive_tags(text: str, include_defaults: bool, allowed_tags: Iterable[str]) -> list[str]:
    normalized = text.lower()
    tags: list[str] = []
    if include_defaults:
        for tag in DEFAULT_TAGS:
            append_tag(tags, tag)
    for tag, patterns in RULES.items():
        if any(pattern in normalized for pattern in patterns):
            append_tag(tags, tag)
    allowed = set(allowed_tags)
    if allowed:
        tags = [tag for tag in tags if tag in allowed]
    return tags


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="*", help="Text to classify. Remaining arguments are joined with spaces.")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--no-defaults", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--as-knowledge-select-args", action="store_true")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    text = " ".join(args.text).strip()
    tags = derive_tags(text, not args.no_defaults, known_tags(repo_root))

    if args.as_knowledge_select_args:
        if not tags:
            print("--match any")
            return 0
        print("--tags " + " ".join(tags) + " --match any")
        return 0

    if args.json:
        print(json.dumps({"text": text, "tags": tags}, ensure_ascii=False, indent=4))
        return 0

    for tag in tags:
        print(tag)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
