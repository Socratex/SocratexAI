#!/usr/bin/env python3
"""Shared CLI helpers for SocratexPipeline tool entrypoints."""

from __future__ import annotations

import sys
from collections.abc import Callable, Iterable


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def split_values(
    values: Iterable[str],
    *,
    separators: tuple[str, ...] = (",",),
    transform: Callable[[str], str] | None = None,
    unique: bool = True,
    sort: bool = False,
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        parts = [str(value)]
        for separator in separators:
            parts = [item for part in parts for item in part.split(separator)]
        for part in parts:
            item = part.strip()
            if transform is not None:
                item = transform(item)
            if not item:
                continue
            if unique:
                if item in seen:
                    continue
                seen.add(item)
            result.append(item)
    return sorted(result) if sort else result
