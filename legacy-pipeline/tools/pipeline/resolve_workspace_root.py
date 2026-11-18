#!/usr/bin/env python3
"""Resolve the Socratex workspace root with Python-only tooling."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from pipeline_script_helpers import configure_stdio, read_json


def existing_path(value: str) -> Path | None:
    if not value or not value.strip():
        return None
    path = Path(value).expanduser()
    try:
        return path.resolve(strict=True)
    except FileNotFoundError:
        return None


def read_workspace_config(path: Path) -> dict[str, Any]:
    try:
        document = read_json(path)
    except Exception as exc:
        raise ValueError(f"workspace.json is not valid JSON: {path}") from exc
    content = document.get("content") if isinstance(document, dict) else None
    return content if isinstance(content, dict) else document


def workspace_relative(root: Path, config: dict[str, Any], key: str, default: str) -> Path:
    value = str(config.get(key) or default)
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def is_workspace_candidate(root: Path) -> bool:
    config_path = root / "workspace.json"
    if not config_path.is_file():
        return False
    config = read_workspace_config(config_path)
    return workspace_relative(root, config, "socratex_ai_dir", "SocratexAI").is_dir()


def find_workspace_root(start: str) -> Path | None:
    resolved = existing_path(start) or existing_path(".")
    if resolved is None:
        raise ValueError(f"Cannot resolve workspace search start path: {start}")
    current = resolved.parent if resolved.is_file() else resolved
    for candidate in [current, *current.parents]:
        if is_workspace_candidate(candidate):
            return candidate
    return None


def script_fallback_root() -> Path | None:
    for candidate in [Path(__file__).resolve(), *Path(__file__).resolve().parents]:
        if candidate.name == "SocratexAI":
            parent = candidate.parent
            if (parent / "SocratexAI").is_dir():
                return parent
    return None


def resolve_workspace_root(start_path: str, workspace_root: str) -> Path:
    explicit = existing_path(workspace_root)
    if explicit is not None:
        if not is_workspace_candidate(explicit):
            raise ValueError(f"Explicit workspace root must contain workspace.json and a SocratexAI directory: {explicit}")
        return explicit
    found = find_workspace_root(start_path)
    if found is not None:
        return found
    env_root = existing_path(os.environ.get("SOCRATEX_WORKSPACE_ROOT", ""))
    if env_root is not None and is_workspace_candidate(env_root):
        return env_root
    fallback = script_fallback_root()
    if fallback is not None:
        return fallback
    raise ValueError("Could not resolve Socratex workspace root. Put workspace.json next to SocratexAI/ or set SOCRATEX_WORKSPACE_ROOT.")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-path", "-StartPath", default=".")
    parser.add_argument("--workspace-root", "-WorkspaceRoot", default="")
    parser.add_argument("--json", "-Json", action="store_true")
    args = parser.parse_args()

    root = resolve_workspace_root(args.start_path, args.workspace_root)
    config_path = root / "workspace.json"
    config = read_workspace_config(config_path) if config_path.is_file() else {
        "schema": "socratex-workspace/v1",
        "workspace_name": "inferred",
        "socratex_ai_dir": "SocratexAI",
        "projects_dir": ".",
    }
    result = {
        "workspace_root": str(root),
        "workspace_config": str(config_path),
        "projects_dir": str(workspace_relative(root, config, "projects_dir", ".")),
        "socratex_ai_dir": str(workspace_relative(root, config, "socratex_ai_dir", "SocratexAI")),
        "tools_dir": str(workspace_relative(root, config, "tools_dir", "tools")),
        "archive_dir": str(workspace_relative(root, config, "archive_dir", "_archive")),
        "drive_exports_dir": str(workspace_relative(root, config, "drive_exports_dir", "drive-exports")),
        "google_drive_projects_uri": str(config.get("google_drive_projects_uri", "")),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=4))
    else:
        print(result["workspace_root"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
