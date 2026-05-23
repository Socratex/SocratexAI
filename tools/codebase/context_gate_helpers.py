#!/usr/bin/env python3
"""Shared helpers for source-code context gate tools."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CODE_PATH_SUFFIXES = {
    ".gd",
    ".cs",
    ".csproj",
    ".props",
    ".targets",
    ".sln",
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".sh",
    ".bash",
    ".zsh",
    ".lua",
    ".rs",
    ".go",
    ".java",
    ".kt",
    ".kts",
    ".c",
    ".cc",
    ".cpp",
    ".h",
    ".hpp",
    ".php",
    ".rb",
    ".swift",
}

SKIP_CODE_PREFIXES = (
    "ignored/",
    "logs/",
    "logs-diagnostics/",
    "logs-performance/",
    "tools/tmp/",
    "AI-compiled/",
    "SocratexAI/AI-compiled/",
    "docs-tech/cache/",
)


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def split_path_values(values: list[str]) -> list[str]:
    paths: set[str] = set()
    for value in values:
        for candidate in value.split(","):
            cleaned = normalize_path(candidate)
            if cleaned:
                paths.add(cleaned)
    return sorted(paths)


def git_lines(root: Path, args: list[str], *, allow_failure: bool = False) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        if allow_failure:
            return []
        output = "\n".join(part for part in (completed.stdout.strip(), completed.stderr.strip()) if part)
        raise RuntimeError(f"git {' '.join(args)} failed in {root}: {output}")
    return [
        normalize_path(line)
        for line in completed.stdout.splitlines()
        if line.strip() and not line.startswith("warning: ")
    ]


def changed_paths(root: Path, explicit_paths: list[str]) -> list[str]:
    if explicit_paths:
        return split_path_values(explicit_paths)
    paths = [
        *git_lines(root, ["diff", "--name-only", "--diff-filter=ACMR"]),
        *git_lines(root, ["diff", "--cached", "--name-only", "--diff-filter=ACMR"]),
        *git_lines(root, ["ls-files", "--others", "--exclude-standard"]),
    ]
    return sorted(set(paths))


def is_code_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "OUTPUT":
        return False
    if normalized.startswith(SKIP_CODE_PREFIXES):
        return False
    return Path(normalized).suffix.lower() in CODE_PATH_SUFFIXES


def changed_code_paths(root: Path, explicit_paths: list[str]) -> list[str]:
    return [path for path in changed_paths(root, explicit_paths) if is_code_path(path)]


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def config_content(config: Any) -> Any:
    if isinstance(config, dict) and config.get("content") is not None:
        return config["content"]
    return config


def declared_design_reads(project_root: Path) -> list[str] | None:
    config_path = project_root / ".aiassistant/socratex/PIPELINE-CONFIG.json"
    if not config_path.is_file():
        return None
    content = config_content(load_json(config_path))
    if isinstance(content, dict):
        reads = content.get("code_design_required_reads", [])
        if isinstance(reads, list):
            return [str(item) for item in reads]
    return []


def git_head(root: Path) -> str | None:
    lines = git_lines(root, ["rev-parse", "HEAD"], allow_failure=True)
    return lines[0] if lines else None


def parse_utc_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def gate_age_minutes(loaded_at: str) -> float:
    return (datetime.now(timezone.utc) - parse_utc_datetime(loaded_at)).total_seconds() / 60.0
