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


GIT_WARNING_FRAGMENT = "will be replaced by"
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


def repo_root(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()
    for candidate in [start.resolve(), *start.resolve().parents]:
        if (candidate / "SCRIPTS.json").is_file() and (candidate / "tools").is_dir():
            return candidate
    return start.resolve()


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def normalize_path(value: str) -> str:
    return value.replace("\\", "/").removeprefix("./").strip()


def split_values(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in str(value).replace(";", ",").split(","):
            item = normalize_path(part)
            if item and item not in result:
                result.append(item)
    return result


def run(label: str, command: list[str], cwd: Path) -> int:
    print()
    print(f"==> {label}")
    completed = subprocess.run(command, cwd=cwd, check=False)
    if completed.returncode != 0:
        print(f"ERROR: {label} failed with exit code {completed.returncode}", file=sys.stderr)
    return completed.returncode


def git_lines(root: Path, args: list[str]) -> list[str]:
    completed = subprocess.run(["git", *args], cwd=root, check=False, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    if completed.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {output.strip()}")
    return [
        line.strip()
        for line in output.splitlines()
        if line.strip()
        and GIT_WARNING_FRAGMENT not in line
        and not line.lstrip().startswith("warning:")
    ]


def changed_paths(root: Path, explicit: list[str] | None = None, *, diff_filter: str = "ACMRD") -> list[str]:
    explicit_paths = split_values(explicit or [])
    if explicit_paths:
        return sorted(set(explicit_paths))
    if not (root / ".git").exists():
        return []
    paths: set[str] = set()
    for args in (
        ["diff", "--name-only", f"--diff-filter={diff_filter}"],
        ["diff", "--cached", "--name-only", f"--diff-filter={diff_filter}"],
        ["ls-files", "--others", "--exclude-standard"],
    ):
        paths.update(normalize_path(path) for path in git_lines(root, args))
    return sorted(path for path in paths if path)


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
