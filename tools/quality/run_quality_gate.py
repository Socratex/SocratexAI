#!/usr/bin/env python3
"""Run the repository quality gate with Python-only tooling."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import repo_root as shared_repo_root  # noqa: E402


FALLBACK_COMMANDS = [
    ("package.json", "npm test"),
    ("pyproject.toml", "python -m pytest"),
    ("Cargo.toml", "cargo test"),
    ("go.mod", "go test ./..."),
    ("pom.xml", "mvn test"),
    ("build.gradle", "gradle test"),
    ("build.gradle.kts", "gradle test"),
]


def repo_root(start: Path) -> Path:
    return shared_repo_root(start, marker_files=("SCRIPTS.json",), marker_dirs=("tools",), use_git=False)


def run_shell(command: str, cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd, shell=True, check=False)
    return completed.returncode


def run_contract(root: Path, names: list[str]) -> int:
    runner = root / "tools" / "quality" / "run_quality_gate_contract.py"
    contract = root / "QUALITY-GATE.json"
    if not contract.is_file() or not runner.is_file():
        return -1
    command = [sys.executable, "-B", str(runner), "--path", str(contract), "--repo-root", str(root)]
    if names:
        command.append("--command-names")
        command.extend(names)
    completed = subprocess.run(command, cwd=root, check=False)
    return completed.returncode


def split_names(values: list[str]) -> list[str]:
    names: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item and item not in names:
                names.append(item)
    return names


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the repository quality gate.")
    parser.add_argument("--repo-root", "--root", default="", help="Repository root. Defaults to the script package root.")
    parser.add_argument("--command", nargs="*", default=[], help="Explicit command to run instead of QUALITY-GATE.json.")
    parser.add_argument("--command-names", nargs="*", default=[], help="QUALITY-GATE.json command keys, comma-separated or repeated.")
    parser.add_argument("--skip", action="store_true", help="Skip quality gate and exit 0.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve() if args.repo_root else repo_root(Path(__file__).resolve())
    if args.skip:
        print("SKIP: quality gate skipped by request.")
        return 0

    print("==> quality gate")
    if args.command:
        command_line = " ".join(args.command)
        print(f"Running configured command: {command_line}")
        return run_shell(command_line, root)

    contract_exit = run_contract(root, split_names(args.command_names))
    if contract_exit >= 0:
        return contract_exit

    for marker, command in FALLBACK_COMMANDS:
        if (root / marker).is_file():
            print(f"Detected {marker}; running {command}")
            return run_shell(command, root)

    print("WARNING: no quality gate detected. Pass --command '<command>' to run one explicitly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
