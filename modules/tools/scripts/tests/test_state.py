"""Tests for modules/tools/scripts/state.py: state dir creation and rotation by age and count."""

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


# ---------- daily rotation trigger and adopting legacy logs ----------

def make_root(tmp_path: Path, old: int = 3, new: int = 2) -> Path:
    logs = tmp_path / "state" / "flow-debug"
    logs.mkdir(parents=True)
    for i in range(old):
        make(logs, f"old{i}.log", 30)
    for i in range(new):
        make(logs, f"new{i}.log", 1)
    return tmp_path


def test_rotate_dry_run_deletes_nothing(tmp_path):
    root = make_root(tmp_path)
    removed = state.rotate_known(root, dry_run=True)
    assert len(removed["flow-debug"]) == 3
    assert len(list((root / "state" / "flow-debug").iterdir())) == 5


def test_rotate_known_skips_missing_subdirs(tmp_path):
    assert state.rotate_known(tmp_path) == {}


def test_rotate_daily_runs_once_per_day_and_writes_marker(tmp_path):
    root = make_root(tmp_path)
    assert state.rotate_daily(root) is True
    assert sorted(p.name for p in (root / "state" / "flow-debug").iterdir()) == ["new0.log", "new1.log"]
    make(root / "state" / "flow-debug", "stale.log", 40)
    assert state.rotate_daily(root) is False  # marker is fresh, so the stale file stays
    assert (root / "state" / "flow-debug" / "stale.log").exists()
    assert state.rotate_daily(root, now=time.time() + 2 * DAY) is True
    assert not (root / "state" / "flow-debug" / "stale.log").exists()


def test_rotate_daily_never_raises(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise OSError("disk on fire")

    monkeypatch.setattr(state, "rotate_known", boom)
    assert state.rotate_daily(tmp_path) is False


def test_adopt_logs_lists_then_moves_never_overwrites(tmp_path):
    (tmp_path / "local").mkdir()
    for name in ("flow-debug-aaaa.log", "flow-debug-bbbb.log"):
        (tmp_path / "local" / name).write_text("12345", encoding="utf-8")
    (tmp_path / "local" / "profile.md").write_text("keep", encoding="utf-8")
    found = state.adopt_logs(tmp_path)
    assert [size for _, _, size in found] == [5, 5]
    assert (tmp_path / "local" / "flow-debug-aaaa.log").exists()  # dry run moves nothing
    (tmp_path / "state" / "flow-debug").mkdir(parents=True)
    (tmp_path / "state" / "flow-debug" / "flow-debug-bbbb.log").write_text("existing", encoding="utf-8")
    moved = state.adopt_logs(tmp_path, move=True)
    assert [s.name for s, _, _ in moved] == ["flow-debug-aaaa.log"]
    assert (tmp_path / "state" / "flow-debug" / "flow-debug-aaaa.log").read_text(encoding="utf-8") == "12345"
    assert (tmp_path / "local" / "flow-debug-bbbb.log").exists()  # collision: left in place
    assert (tmp_path / "state" / "flow-debug" / "flow-debug-bbbb.log").read_text(encoding="utf-8") == "existing"
    assert (tmp_path / "local" / "profile.md").exists()
