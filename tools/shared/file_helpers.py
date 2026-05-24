#!/usr/bin/env python3
"""Shared file and content hashing helpers for SocratexPipeline tools."""

from __future__ import annotations

import hashlib
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def write_text_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and read_text(path) == content:
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def normalized_hash_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    normalized = "\n".join(lines).rstrip("\n")
    return normalized + "\n" if normalized else ""


def sha256_text(text: str) -> str:
    return hashlib.sha256(normalized_hash_text(text).encode("utf-8")).hexdigest()


def sha256_text_file(path: Path) -> str:
    return sha256_text(read_text(path))


def sha256_optional_text_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return sha256_text_file(path)


def sha256_binary_file(path: Path) -> str:
    if not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
