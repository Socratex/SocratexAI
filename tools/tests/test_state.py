"""Tests for tools/state.py: state dir creation and rotation by age and count."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import state  # noqa: E402

DAY = 86400


def make(directory: Path, name: str, age_days: float) -> Path:
    path = directory / name
    path.write_text("x", encoding="utf-8")
    stamp = time.time() - age_days * DAY
    os.utime(path, (stamp, stamp))
    return path


def test_state_dir_created_on_demand(tmp_path):
    assert not (tmp_path / "state").exists()
    assert state.state_dir(tmp_path) == tmp_path / "state"
    assert (tmp_path / "state").is_dir()


def test_rotate_missing_dir_is_noop(tmp_path):
    assert state.rotate(tmp_path / "nope") == []


def test_rotate_removes_old_files(tmp_path):
    old = make(tmp_path, "old.log", 30)
    new = make(tmp_path, "new.log", 1)
    removed = state.rotate(tmp_path, max_files=20, max_age_days=14)
    assert removed == [old]
    assert new.exists() and not old.exists()


def test_rotate_keeps_newest_n(tmp_path):
    files = [make(tmp_path, f"f{i}.log", i * 0.1) for i in range(5)]
    state.rotate(tmp_path, max_files=2, max_age_days=14)
    assert [p.exists() for p in files] == [True, True, False, False, False]


def test_rotate_leaves_subdirs(tmp_path):
    (tmp_path / "sub").mkdir()
    make(tmp_path, "a.log", 100)
    state.rotate(tmp_path, max_files=1, max_age_days=1)
    assert (tmp_path / "sub").is_dir()
