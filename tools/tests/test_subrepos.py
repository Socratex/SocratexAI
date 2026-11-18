"""Tests for the reference-pack tool: search ranking, caps and the manifest."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import subrepos  # noqa: E402


def skill(pack: Path, rel: str, name: str, description: str, body: str = "") -> None:
    path = pack / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nname: {name}\ndescription: {description}\n---\n{body}\n", encoding="utf-8")


def fake_packs(tmp_path, monkeypatch):
    manifest = tmp_path / "subrepos.json"
    manifest.write_text(json.dumps({"repos": [{"name": "a", "url": "x", "branch": "main", "what": ""},
                                              {"name": "b", "url": "x", "branch": "main", "what": ""}]}),
                        encoding="utf-8")
    monkeypatch.setattr(subrepos, "MANIFEST", manifest)
    monkeypatch.setattr(subrepos, "DEST", tmp_path / "packs")
    return tmp_path / "packs"


def test_manifest_lists_only_github_https_urls():
    for repo in subrepos.load_manifest():
        assert repo["url"].startswith("https://github.com/") and repo["branch"]


def test_search_matches_all_words_and_treats_hyphens_as_spaces(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/test-driven-development/SKILL.md", "test-driven-development", "Write the test first")
    skill(packs / "a", "skills/cooking/SKILL.md", "cooking", "Make soup")
    hits = subrepos.search(["test", "driven", "development"])
    assert [hit[2] for hit in hits] == ["test-driven-development"]
    assert subrepos.search(["test", "soup"]) == []


def test_each_pack_contributes_at_most_per_pack_hits(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    for number in range(6):
        skill(packs / "a", f"skills/s{number}/SKILL.md", f"s{number}", "review code carefully")
    skill(packs / "b", "skills/r/SKILL.md", "r", "review code once")
    hits = subrepos.search(["review"], per_pack=3)
    assert sum(hit[1].startswith("a/") for hit in hits) == 3
    assert any(hit[1].startswith("b/") for hit in hits)


def test_non_skill_folders_and_tests_are_ignored(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "docs/guide.md", "guide", "review code")
    skill(packs / "a", "tests/skills/x/SKILL.md", "x", "review code")
    assert subrepos.search(["review"]) == []


def test_update_reports_clone_failure_without_raising(tmp_path, monkeypatch):
    fake_packs(tmp_path, monkeypatch)
    monkeypatch.setattr(subrepos, "git", lambda *a, **k: subprocess.CompletedProcess([], 1, "", "offline"))
    line = subrepos.update_one({"name": "a", "url": "https://github.com/none/none", "branch": "main"})
    assert "clone failed" in line
