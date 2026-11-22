"""Tests for the reference-pack tool: location, search ranking, pins and failure reporting."""

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


def ref_manifest(name: str, cat: str, **source: str) -> dict:
    return {"schema": "socratex-extension/v1", "name": name, "kind": "ref", "category": cat,
            "source": {"url": "https://example.com/x", "branch": "main", "commit": "unknown", **source},
            "when_to_use": "w", "status": "adopted", "default_enabled": False,
            "context_cost": {"level": "none", "note": "n"}, "risks": "r"}


def fake_packs(tmp_path, monkeypatch) -> Path:
    folder = tmp_path / "modules" / "extensions"
    folder.mkdir(parents=True)
    for name, cat in (("a", "workflow"), ("b", "frontend")):
        (folder / f"{name}.json").write_text(json.dumps(ref_manifest(name, cat)), encoding="utf-8")
    monkeypatch.setattr(subrepos, "ROOT", tmp_path)
    monkeypatch.setenv("SOCRATEX_REFS", str(tmp_path / "packs"))
    return tmp_path / "packs"


def test_real_manifest_is_github_https_pinned_and_categorised():
    repos = subrepos.load_manifest()
    assert len(repos) >= 15
    for repo in repos:
        assert repo["url"].startswith("https://github.com/") and repo["branch"] and repo["cat"]
        assert len(repo.get("commit", "x" * 40)) == 40


def test_packs_come_from_ref_manifests_only(tmp_path, monkeypatch):
    fake_packs(tmp_path, monkeypatch)
    note = ref_manifest("c", "list")
    note.update(kind="note")
    (tmp_path / "modules" / "extensions" / "c.json").write_text(json.dumps(note), encoding="utf-8")
    assert [repo["name"] for repo in subrepos.load_manifest()] == ["a", "b"]


def test_unknown_pin_counts_as_unpinned_and_local_manifest_is_a_pack(tmp_path, monkeypatch):
    fake_packs(tmp_path, monkeypatch)
    local = tmp_path / "local" / "extensions"
    local.mkdir(parents=True)
    (local / "z.json").write_text(json.dumps(ref_manifest("z", "list", commit="1" * 40)), encoding="utf-8")
    repos = {repo["name"]: repo for repo in subrepos.load_manifest()}
    assert "commit" not in repos["a"] and repos["z"]["commit"] == "1" * 40


def test_bump_writes_the_new_pin_into_the_manifest_file(tmp_path, monkeypatch):
    fake_packs(tmp_path, monkeypatch)
    repos = subrepos.load_manifest()
    repos[0]["commit"] = "2" * 40
    subrepos.save_manifest(repos)
    saved = json.loads((tmp_path / "modules" / "extensions" / "a.json").read_text(encoding="utf-8"))
    assert saved["source"]["commit"] == "2" * 40 and saved["name"] == "a"
    assert json.loads((tmp_path / "modules" / "extensions" / "b.json").read_text(encoding="utf-8"))["source"]["commit"] == "unknown"


def test_packs_live_outside_the_repo(monkeypatch):
    monkeypatch.delenv("SOCRATEX_REFS", raising=False)
    assert subrepos.ROOT not in subrepos.refs_dir().parents and subrepos.refs_dir() != subrepos.ROOT
    monkeypatch.setenv("SOCRATEX_REFS", "/somewhere/else")
    assert subrepos.refs_dir() == Path("/somewhere/else")


def test_search_matches_all_words_and_treats_hyphens_as_spaces(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/test-driven-development/SKILL.md", "test-driven-development", "Write the test first")
    skill(packs / "a", "skills/cooking/SKILL.md", "cooking", "Make soup")
    assert [hit[2] for hit in subrepos.search(["test", "driven", "development"])] == ["test-driven-development"]
    assert subrepos.search(["test", "soup"]) == []


def test_filler_words_are_ignored_and_alone_they_are_rejected(tmp_path, monkeypatch, capsys):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/review/SKILL.md", "review", "Review code", "it works for it")
    assert subrepos.meaningful(["it", "works", "Review"]) == ["review"]
    assert subrepos.cmd_search(["it", "works"], None) == 1
    assert "filler" in capsys.readouterr().out


def test_name_and_description_outweigh_body_mentions(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/x/SKILL.md", "x", "unrelated", "deploy " * 40)
    skill(packs / "a", "skills/deploy/SKILL.md", "deploy", "Deploy the app", "deploy once")
    assert subrepos.search(["deploy"])[0][2] == "deploy"


def test_each_pack_contributes_at_most_per_pack_hits(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    for number in range(6):
        skill(packs / "a", f"skills/s{number}/SKILL.md", f"s{number}", "review code carefully")
    skill(packs / "b", "skills/r/SKILL.md", "r", "review code once")
    hits = subrepos.search(["review"], per_pack=3)
    assert sum(hit[1].startswith("a/") for hit in hits) == 3 and any(hit[1].startswith("b/") for hit in hits)


def test_category_filter(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/r/SKILL.md", "r", "review code")
    skill(packs / "b", "skills/q/SKILL.md", "q", "review design")
    assert [hit[1][0] for hit in subrepos.search(["review"], cat="frontend")] == ["b"]


def test_search_output_is_marked_as_third_party_data(tmp_path, monkeypatch, capsys):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "skills/r/SKILL.md", "r", "review code")
    assert subrepos.cmd_search(["review"], None) == 0
    assert capsys.readouterr().out.startswith("THIRD-PARTY CONTENT")


def test_non_skill_folders_and_tests_are_ignored(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    skill(packs / "a", "docs/guide.md", "guide", "review code")
    skill(packs / "a", "tests/skills/x/SKILL.md", "x", "review code")
    assert subrepos.search(["review"]) == []


def test_failures_are_reported_not_hidden(tmp_path, monkeypatch, capsys):
    fake_packs(tmp_path, monkeypatch)
    monkeypatch.setattr(subrepos, "git", lambda *a, **k: subprocess.CompletedProcess([], 1, "", "offline"))
    assert subrepos.cmd_update([]) == 1
    out = capsys.readouterr().out
    assert "[error  ] a" in out and "[error  ] b" in out and "2 error" in out


def test_one_failing_pack_does_not_stop_the_others(tmp_path, monkeypatch):
    fake_packs(tmp_path, monkeypatch)
    calls = []

    def fake_update(repo, dest):
        calls.append(repo["name"])
        return ("error", "boom") if repo["name"] == "a" else ("ok", "fine")

    monkeypatch.setattr(subrepos, "update_one", fake_update)
    assert subrepos.cmd_update([]) == 1 and calls == ["a", "b"]


def test_disabled_pack_is_skipped(tmp_path):
    status, _ = subrepos.update_one({"name": "z", "url": "x", "branch": "m", "disabled": True}, tmp_path)
    assert status == "skipped"


def test_bump_needs_a_terminal_or_yes_and_keeps_the_pin(tmp_path, monkeypatch):
    packs = fake_packs(tmp_path, monkeypatch)
    repo = {"name": "a", "url": "x", "branch": "main", "commit": "1" * 40}
    outputs = {"rev-parse": "2" * 40, "log": "subject"}

    def fake_git(args, cwd=None):
        return subprocess.CompletedProcess([], 0, outputs.get(args[0], ""), "")

    monkeypatch.setattr(subrepos, "git", fake_git)
    monkeypatch.setattr(subrepos, "prepare", lambda *a: None)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    status, _ = subrepos.bump_one(repo, packs, yes=False)
    assert status == "skipped" and repo["commit"] == "1" * 40
    status, _ = subrepos.bump_one(repo, packs, yes=True)
    assert status == "ok" and repo["commit"] == "2" * 40


def make_origin(tmp_path: Path) -> tuple[Path, str, str]:
    """A local git repo with two commits; returns (path, first_commit, second_commit)."""
    origin = tmp_path / "origin"
    origin.mkdir()
    run = lambda *args: subprocess.run(["git", *args], cwd=origin, capture_output=True, text=True, check=True).stdout.strip()  # noqa: E731
    run("init", "-q", "-b", "main")
    run("config", "user.email", "t@example.com")
    run("config", "user.name", "t")
    (origin / "a.txt").write_text("one", encoding="utf-8")
    run("add", "a.txt")
    run("commit", "-q", "-m", "one")
    first = run("rev-parse", "HEAD")
    (origin / "a.txt").write_text("two", encoding="utf-8")
    run("commit", "-q", "-am", "two")
    return origin, first, run("rev-parse", "HEAD")


def test_update_one_moves_a_pack_to_its_pin_not_the_branch_tip(tmp_path):
    origin, first, second = make_origin(tmp_path)
    repo = {"name": "p", "url": origin.as_posix(), "branch": "main", "commit": first}
    dest = tmp_path / "packs"
    dest.mkdir()
    status, message = subrepos.update_one(repo, dest)
    assert status == "ok" and "pinned" in message
    assert (dest / "p" / "a.txt").read_text(encoding="utf-8") == "one"
    repo["commit"] = second  # a bump moves the pin forward
    assert subrepos.update_one(repo, dest)[0] == "ok"
    assert (dest / "p" / "a.txt").read_text(encoding="utf-8") == "two"


def test_update_one_reports_an_unreachable_source_as_an_error(tmp_path):
    dest = tmp_path / "packs"
    dest.mkdir()
    repo = {"name": "p", "url": (tmp_path / "missing").as_posix(), "branch": "main", "commit": "0" * 40}
    assert subrepos.update_one(repo, dest)[0] == "error"


def test_refs_dir_is_read_from_local_install_json(tmp_path, monkeypatch):
    prefs = tmp_path / "install.json"
    prefs.write_text(json.dumps({"refs_dir": str(tmp_path / "chosen")}), encoding="utf-8")
    monkeypatch.setattr(subrepos, "PREFS_FILE", prefs)
    monkeypatch.delenv("SOCRATEX_REFS", raising=False)
    assert subrepos.refs_dir() == tmp_path / "chosen"
    monkeypatch.setenv("SOCRATEX_REFS", str(tmp_path / "env"))  # the environment wins over the saved choice
    assert subrepos.refs_dir() == tmp_path / "env"


def test_update_script_exit_code_follows_the_pack_result(monkeypatch):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import update  # noqa: E402

    monkeypatch.setattr(update.subrepos, "cmd_update", lambda names: 1)
    assert update.main(["refs"]) == 1
    monkeypatch.setattr(update.subrepos, "cmd_update", lambda names: 0)
    assert update.main(["refs"]) == 0
    monkeypatch.setattr(update, "update_self", lambda: 1)  # a failed pull never hides behind good packs
    assert update.main(["all"]) == 1
