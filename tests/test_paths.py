"""No living file may point to a path the restructure removed or moved (history in docs/specs and the shims excepted)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core"))

import shims  # noqa: E402

REMOVED = re.compile(r"(?<![A-Za-z0-9_./-])tools/(review|planning|pipeline)/")
MOVED = re.compile(r"(?<![A-Za-z0-9_./-])tools/((?:" + "|".join(shims.SHIM_NAMES + ("generated",)) + r")\.py|tests\b|gpt/)")
HISTORY = ("docs/specs/",)
SHIM_FILES = {f"tools/{name}.py" for name in shims.SHIM_NAMES} | {"core/shims.py", "tests/test_shims.py", "tests/test_paths.py"}
MOVED_ALLOWED = {"docs/IMPROVEMENTS.json"}   # ledger results are history: they name the path that was used then


def living_files() -> list[tuple[str, str]]:
    """(relative path, text) of every tracked text file that is not history."""
    out = subprocess.run(["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True).stdout.split("\n")
    rows = []
    for name in out:
        path = REPO / name
        if not name or name.startswith(HISTORY) or not path.is_file():
            continue
        try:
            rows.append((name, path.read_text(encoding="utf-8")))
        except UnicodeDecodeError:
            continue
    return rows


def test_removed_directories_are_not_referenced():
    hits = [f"{rel}: {m.group(0)}" for rel, text in living_files() if rel not in SHIM_FILES for m in REMOVED.finditer(text)]
    assert hits == []


def test_moved_scripts_are_referenced_only_through_the_new_path():
    hits = []
    for rel, text in living_files():
        if rel not in SHIM_FILES and rel not in MOVED_ALLOWED:
            hits += [f"{rel}: {m.group(0)}" for m in MOVED.finditer(text)]
    assert hits == []


def test_removed_redirect_directories_are_gone():
    assert not (REPO / "tools" / "review").exists() and not (REPO / "tools" / "planning").exists()
    names = sorted(p.name for p in (REPO / "tools").iterdir() if p.is_file())
    assert names == sorted(f"{n}.py" for n in shims.SHIM_NAMES)
