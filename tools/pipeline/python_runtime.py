#!/usr/bin/env python3
"""Shared Python runtime resolution for SocratexPipeline tools."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


MIN_PYTHON = (3, 10)
RECOMMENDED_PYTHON = (3, 12)


@dataclass(frozen=True)
class PythonRuntime:
    executable: str
    version: str
    source: str
    ok: bool
    message: str


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "SCRIPTS.json").is_file() and (candidate / "tools").is_dir():
            return candidate
    return Path.cwd().resolve()


def _candidate_paths(search_root: Path) -> Iterable[tuple[str, str]]:
    env_python = os.environ.get("SOCRATEX_PYTHON", "").strip()
    if env_python:
        yield env_python, "SOCRATEX_PYTHON"

    yield sys.executable, "current_process"

    child_python = search_root / "Tools" / "Python312" / "python.exe"
    if child_python.is_file():
        yield str(child_python), "bundled_child_python"

    for name in ("python3", "python"):
        found = shutil.which(name)
        if found:
            yield found, f"PATH:{name}"

    py_launcher = shutil.which("py")
    if py_launcher:
        yield py_launcher, "PATH:py"


def _probe(command: str, source: str) -> PythonRuntime | None:
    args = [command, "-c", "import platform,sys; print(platform.python_version()); sys.exit(0 if sys.version_info >= (3, 10) else 1)"]
    if source == "PATH:py":
        args = [command, "-3", "-c", "import platform,sys; print(platform.python_version()); sys.exit(0 if sys.version_info >= (3, 10) else 1)"]
    try:
        completed = subprocess.run(args, check=False, capture_output=True, text=True, timeout=5)
    except Exception:
        return None
    version = (completed.stdout or completed.stderr).strip().splitlines()
    version_text = version[0] if version else "unknown"
    if completed.returncode != 0:
        return PythonRuntime(command, version_text, source, False, f"Python >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} is required.")
    return PythonRuntime(command, version_text, source, True, "OK")


def resolve_python(search_root: Path | None = None) -> PythonRuntime:
    root = (search_root or repo_root()).resolve()
    seen: set[str] = set()
    best_failure: PythonRuntime | None = None
    for command, source in _candidate_paths(root):
        key = f"{source}:{command}"
        if key in seen:
            continue
        seen.add(key)
        runtime = _probe(command, source)
        if runtime is None:
            continue
        if runtime.ok:
            return runtime
        best_failure = runtime
    return best_failure or PythonRuntime("", "", "unresolved", False, python_install_hint())


def python_install_hint() -> str:
    system = platform.system().lower()
    if system == "linux":
        return "Install Python 3.10+ with your distro package manager, pyenv, or the project-approved toolchain."
    if system == "darwin":
        return "Install Python 3.10+ with python.org, Homebrew, or pyenv."
    if system == "windows":
        return "Install Python 3.10+ with winget, python.org, or the Windows Store, then set SOCRATEX_PYTHON if needed."
    return "Install Python 3.10+ and set SOCRATEX_PYTHON to the executable path if automatic discovery fails."


def runtime_report(search_root: Path | None = None) -> dict[str, object]:
    runtime = resolve_python(search_root)
    return {
        "python3": {
            "ok": runtime.ok,
            "version": runtime.version,
            "executable": runtime.executable,
            "source": runtime.source,
            "minimum_version": f"{MIN_PYTHON[0]}.{MIN_PYTHON[1]}",
            "recommended_version": f"{RECOMMENDED_PYTHON[0]}.{RECOMMENDED_PYTHON[1]}",
            "install_hint": None if runtime.ok else python_install_hint(),
            "message": runtime.message,
        }
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve the SocratexPipeline Python runtime.")
    parser.add_argument("--root-key", default="runtime", help="JSON root key to emit.")
    parser.add_argument("--search-root", default=".", help="Root used for bundled child Python discovery.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when Python is missing or too old.")
    args = parser.parse_args()

    report = runtime_report(Path(args.search_root))
    print(json.dumps({args.root_key: report}, ensure_ascii=False, indent=4))
    return 1 if args.strict and not report["python3"]["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
