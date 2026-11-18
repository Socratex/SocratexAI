#!/usr/bin/env python3
"""Execute the SocratexPipeline QUALITY-GATE.json command contract."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def content_of(document: dict[str, Any]) -> dict[str, Any]:
    content = document.get("content")
    return content if isinstance(content, dict) else document


def split_names(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for part in value.split(","):
            name = part.strip()
            if name and name not in names:
                names.append(name)
    return names


def selected_commands(commands: dict[str, Any], names: list[str]) -> list[tuple[str, dict[str, Any]]]:
    if not names:
        return [(name, command) for name, command in commands.items() if isinstance(command, dict)]

    lower_lookup = {name.lower(): name for name in commands}
    missing = [name for name in names if name.lower() not in lower_lookup]
    if missing:
        raise ValueError(f"Quality gate command(s) not found: {', '.join(missing)}")
    return [
        (lower_lookup[name.lower()], commands[lower_lookup[name.lower()]])
        for name in names
        if isinstance(commands[lower_lookup[name.lower()]], dict)
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run QUALITY-GATE.json commands in order.")
    parser.add_argument("--path", default="QUALITY-GATE.json", help="Quality gate JSON path.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--command-names", nargs="*", default=[], help="Optional command keys, comma-separated or repeated.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    gate_path = Path(args.path)
    if not gate_path.is_absolute():
        gate_path = root / gate_path
    if not gate_path.is_file():
        print(f"ERROR: Quality gate contract not found: {gate_path}", file=sys.stderr)
        return 1

    try:
        document = read_json(gate_path)
        commands = content_of(document).get("commands")
        if not isinstance(commands, dict):
            raise ValueError(f"Quality gate contract has no content.commands object: {gate_path}")
        selected = selected_commands(commands, split_names(args.command_names))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("==> quality gate contract")
    for name, entry in selected:
        command = str(entry.get("command", "")).strip()
        if not command:
            print(f"ERROR: Quality gate command has empty command text: {name}", file=sys.stderr)
            return 1

        print(f"\n==> {name}")
        description = str(entry.get("description", "")).strip()
        if description:
            print(description)
        completed = subprocess.run(command, cwd=root, shell=True, check=False)
        if completed.returncode != 0:
            print(f"ERROR: Quality gate command failed with exit code {completed.returncode}: {name}", file=sys.stderr)
            return completed.returncode

    print("\nOK: quality gate contract passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
