"""Tiny helpers shared by the select scripts: read the request from stdin, emit candidates as JSON."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def load_request() -> dict:
    return json.load(sys.stdin)


def emit(rows: list[dict]) -> None:
    json.dump(rows, sys.stdout)


def files_of(request: dict) -> list[str]:
    seen: list[str] = []
    for chunk in request["chunks"]:
        if chunk["file"] not in seen:
            seen.append(chunk["file"])
    return seen


def read_lines(request: dict, rel: str) -> list[str]:
    return (Path(request["project_dir"]) / rel).read_bytes().decode("utf-8", errors="replace").splitlines()


def candidate(rel: str, start: int, end: int, category: str, message: str, **extra) -> dict:
    return {"file": rel, "line_start": start, "line_end": end, "category": category, "message": message, **extra}


def is_changed(chunks: list[dict], rel: str, line: int) -> bool:
    """True when `line` is a changed line (not only context) of some chunk; chunks without `changed` accept all."""
    for chunk in chunks:
        if chunk["file"] != rel or not chunk["line_start"] <= line <= chunk["line_end"]:
            continue
        if "changed" not in chunk or any(s <= line <= e for s, e in chunk["changed"]):
            return True
    return False


def overlaps(chunks: list[dict], rel: str, start: int, end: int) -> bool:
    return any(c["file"] == rel and c["line_start"] <= end and start <= c["line_end"] for c in chunks)
