#!/usr/bin/env python3
"""Shared helpers for Python repository tooling entrypoints."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import split_values as split_cli_values  # noqa: E402
from shared.repo_helpers import (  # noqa: E402
    changed_paths,
    git_lines,
    normalize_repo_path,
    repo_root,
    run_step as run,
)


PIPELINE_ROOT_FILES = {
    "AGENTS.md",
    "PUBLIC-BOOTSTRAP.md",
    "QUALITY-GATE.json",
    "CHANGELOG.json",
    "COMMANDS.json",
    "DOCS.json",
    "FLOWS.json",
    "JSON-FORMAT-CONTRACT.json",
    "SCRIPTS.json",
    "WORKFLOW.json",
    "pipeline_featurelist.json",
}
PIPELINE_ROOT_DIRS = ("tools/", "core/", "project/", "profiles/", "templates/", "adapters/", "evals/")
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".gd", ".tscn", ".tres", ".py"}
CODE_EXTENSIONS = {
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
IGNORED_CODE_PREFIXES = (
    "ignored/",
    "logs/",
    "logs-diagnostics/",
    "logs-performance/",
    "tools/tmp/",
    "AI-compiled/",
    "SocratexAI/AI-compiled/",
    "docs-tech/cache/",
)


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_path(value: str) -> str:
    return normalize_repo_path(value)


def split_values(values: list[str]) -> list[str]:
    return split_cli_values(values, separators=(",", ";"), transform=normalize_path)


def changed_text_paths(root: Path, explicit: list[str] | None = None) -> list[str]:
    return [path for path in changed_paths(root, explicit, diff_filter="ACMR") if Path(path).suffix.lower() in TEXT_EXTENSIONS]


def is_code_path(path: str) -> bool:
    normalized = normalize_path(path)
    if normalized == "OUTPUT" or normalized.startswith(IGNORED_CODE_PREFIXES):
        return False
    return Path(normalized).suffix.lower() in CODE_EXTENSIONS


def changed_code_paths(root: Path, explicit: list[str] | None = None) -> list[str]:
    return [path for path in changed_paths(root, explicit, diff_filter="ACMR") if is_code_path(path)]


def pipeline_owned_path(path: str) -> bool:
    normalized = normalize_path(path).lstrip("/")
    if normalized.startswith("SocratexAI/"):
        normalized = normalized.removeprefix("SocratexAI/")
    if normalized.startswith("AI-compiled/"):
        return False
    return normalized in PIPELINE_ROOT_FILES or normalized.startswith(PIPELINE_ROOT_DIRS)


def featurelist_path(path: str) -> bool:
    normalized = normalize_path(path).lstrip("/")
    if normalized.startswith("SocratexAI/"):
        normalized = normalized.removeprefix("SocratexAI/")
    return normalized == "pipeline_featurelist.json"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def content_of(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        return {}
    content = document.get("content")
    return content if isinstance(content, dict) else document


def as_list(value: Any) -> list[str]:
    if value is None:
        raw: list[Any] = []
    elif isinstance(value, list):
        raw = value
    else:
        raw = [value]
    result: list[str] = []
    for item in raw:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
