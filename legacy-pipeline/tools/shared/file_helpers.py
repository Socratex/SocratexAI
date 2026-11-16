#!/usr/bin/env python3
"""Shared file and content hashing helpers for SocratexPipeline tools."""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(path, content)


def write_text_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and read_text(path) == content:
        return False
    write_text_atomic(path, content)
    return True


def write_text_atomic(path: Path, content: str) -> None:
    temp_path = path.with_name(f".{path.name}.tmp")
    last_error: OSError | None = None
    for attempt in range(3):
        try:
            temp_path.write_text(content, encoding="utf-8", newline="\n")
            os.replace(temp_path, path)
            return
        except OSError as exc:
            last_error = exc
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            time.sleep(0.2 * (attempt + 1))
    if last_error is not None:
        raise last_error


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
