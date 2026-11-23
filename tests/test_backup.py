"""sox backup also saves the knowledge kept only in local/ (spec decision 12), and restores it."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "modules" / "tools" / "scripts"))

import backup  # noqa: E402

KNOWLEDGE = ["projects/P/PROJECT.md", "groups/g/GROUP.md", "tickets/AB/AB-1/STATE.md", "handovers/h.md", "notes/n.md", "archive/a.md"]


def fake(tmp_path, monkeypatch, inside_home=True):
    home = tmp_path / "home"
    root = (home / "SocratexAI") if inside_home else (tmp_path / "elsewhere" / "SocratexAI")
    for rel in KNOWLEDGE + ["cache/graph.json", "projects/P/__pycache__/x.pyc", "profile.md"]:
        path = root / "local" / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(rel, encoding="utf-8")
    (home / ".claude").mkdir(parents=True)
    (home / ".claude" / "CLAUDE.md").write_text("c", encoding="utf-8")
    monkeypatch.setattr(backup, "HOME", home)
    monkeypatch.setattr(backup, "ROOT", root)
    monkeypatch.setattr(backup, "BACKUP_DIR", tmp_path / "bk")
    return home, root


def names(zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        return set(archive.namelist())


def test_backup_includes_knowledge_but_not_cache_or_pycache(tmp_path, monkeypatch):
    fake(tmp_path, monkeypatch)
    got = names(backup.backup())
    for rel in KNOWLEDGE:
        assert f"SocratexAI/local/{rel}" in got
    assert ".claude/CLAUDE.md" in got
    assert not any("cache" in n or "profile.md" in n for n in got)


def test_backup_of_checkout_outside_home_uses_prefix_and_restores_into_root(tmp_path, monkeypatch):
    home, root = fake(tmp_path, monkeypatch, inside_home=False)
    out = backup.backup()
    assert "SocratexAI/local/groups/g/GROUP.md" in names(out)
    (root / "local" / "groups" / "g" / "GROUP.md").unlink()
    assert backup.restore(out) == 0
    assert (root / "local" / "groups" / "g" / "GROUP.md").read_text(encoding="utf-8") == "groups/g/GROUP.md"


def test_restore_inside_home_puts_knowledge_back(tmp_path, monkeypatch):
    home, root = fake(tmp_path, monkeypatch)
    out = backup.backup()
    (root / "local" / "tickets" / "AB" / "AB-1" / "STATE.md").unlink()
    backup.restore(out)
    assert (root / "local" / "tickets" / "AB" / "AB-1" / "STATE.md").is_file()
