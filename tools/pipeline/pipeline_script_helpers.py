#!/usr/bin/env python3
"""Small shared helpers for Python-first SocratexPipeline entrypoints."""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import python_runtime

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio, split_values  # noqa: E402


UTF8_NEWLINE = "\n"


def package_root() -> Path:
    return python_runtime.repo_root(Path(__file__))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: Any, *, dry_run: bool = False) -> None:
    if dry_run:
        print(f"Would write JSON: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=4) + UTF8_NEWLINE, encoding="utf-8", newline=UTF8_NEWLINE)


def write_text(path: Path, value: str, *, dry_run: bool = False) -> None:
    if dry_run:
        print(f"Would write text: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline=UTF8_NEWLINE)


def content_of(document: Any) -> Any:
    if isinstance(document, dict) and isinstance(document.get("content"), dict):
        return document["content"]
    return document


def slug(value: str, default: str = "item") -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return normalized or default


def unique_key(document: dict[str, Any], requested: str, title: str, default: str = "item") -> str:
    base = slug(requested or title, default)
    content = document.get("content")
    existing = set(content.keys()) if isinstance(content, dict) else set()
    key = base
    suffix = 1
    while key in existing:
        key = f"{base}_{suffix}"
        suffix += 1
    return key


def append_indexed_content_entry(document: dict[str, Any], key: str, entry: Any) -> dict[str, Any]:
    content = document.setdefault("content", {})
    if not isinstance(content, dict):
        raise ValueError("Document content must be an object.")
    content[key] = entry
    index = document.setdefault("index", [])
    if not isinstance(index, list):
        index = list(content.keys())
    if key not in index:
        index.append(key)
    document["index"] = index
    return document


def now_local_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
