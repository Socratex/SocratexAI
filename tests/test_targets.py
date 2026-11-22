"""Tests for generated targets (markers, hand-edit detection), `sox install --plan/--check/--yes` and startup.load_rules."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "tools"))

import core  # noqa: E402
import generated  # noqa: E402
import install  # noqa: E402
import targets  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli", str(REPO / "core" / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)

RULES_TITLE = "SocratexAI core rules"
INIT_TITLE = "# SocratexAI init"


@pytest.fixture(autouse=True)
def isolated_install(tmp_path, monkeypatch):
    """Point every install path at temp folders: nothing here may touch the real home or the real targets/."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "home" / ".claude"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "home" / ".codex"))
    monkeypatch.setattr(install, "PREFS_FILE", tmp_path / "install.json")
    monkeypatch.setattr(install, "TARGETS", tmp_path / "targets")
    saved = dict(install.PREFS), install.CLAUDE, install.CODEX
    install.apply_prefs({})
    yield
    install.PREFS.clear()
    install.PREFS.update(saved[0])
    install.CLAUDE, install.CODEX = saved[1], saved[2]


def tree(folder: Path) -> dict[str, str]:
    return {p.relative_to(folder).as_posix(): p.read_text(encoding="utf-8") for p in sorted(folder.rglob("*")) if p.is_file()} \
        if folder.is_dir() else {}


# ---------- marker ----------

def test_marker_roundtrip_and_hand_edit_detection():
    stamped = generated.stamp("line one\nline two\n", ["a.md", "b.md"])
    assert generated.verify(stamped) == "ok"
    assert generated.unstamp(stamped)[0] == "line one\nline two\n"
    assert generated.verify(stamped.replace("line two", "line 2")) == "hand-edited"
    assert generated.verify("no marker\n") == "unmarked"
    assert "from a.md, b.md; hash=" in stamped


def test_frontmatter_marker_keeps_the_frontmatter_first():
    text = generated.stamp_frontmatter("---\nname: x\n---\nbody\n", ["x.md"])
    assert text.startswith("---\nname: x\ngenerated: ") and generated.verify(text) == "ok"


def test_json_marker_lives_under_generated_key():
    data = generated.stamp_json({"b": 1, "a": {"c": 2}}, ["s.json"])
    assert list(data)[0] == "_generated" and generated.verify_json(data) == "ok"
    data["b"] = 2
    assert generated.verify_json(data) == "hand-edited"


# ---------- generated targets ----------

def test_generate_writes_marked_files_for_both_agents(tmp_path):
    written = targets.generate()
    assert {"claude/CLAUDE.md", "claude/settings.fragment.json", "codex/AGENTS.md", "claude/agents/scout.md"} <= set(written)
    files = tree(tmp_path / "targets")
    for rel, text in files.items():
        marker = generated.MARKER.search(text)
        assert marker, rel
        assert rel.endswith(".json") or generated.verify(text) == "ok"
    assert generated.verify_json(json.loads(files["claude/settings.fragment.json"])) == "ok"
    assert targets.check() == []


def test_check_detects_hand_edits_stale_and_stray_files(tmp_path):
    targets.generate()
    out = tmp_path / "targets"
    (out / "claude" / "CLAUDE.md").write_text((out / "claude" / "CLAUDE.md").read_text(encoding="utf-8") + "extra\n", encoding="utf-8")
    agent = out / "claude" / "agents" / "scout.md"
    agent.write_text(agent.read_text(encoding="utf-8").replace("name: scout", "name: scoot"), encoding="utf-8")
    fragment = json.loads((out / "claude" / "settings.fragment.json").read_text(encoding="utf-8"))
    fragment["autoCompactWindow"] = 1
    (out / "claude" / "settings.fragment.json").write_text(json.dumps(fragment), encoding="utf-8")
    (out / "codex" / "stray.md").write_text("x", encoding="utf-8")
    problems = targets.check()
    assert sum("hand-edited" in line for line in problems) == 3
    assert any("stray.md" in line and "not produced" in line for line in problems)
    targets.generate()
    assert targets.check() == []  # regenerating removes the stray file and the edits


def test_check_detects_missing_and_stale_files(tmp_path):
    assert any("missing" in line for line in targets.check())
    targets.generate()
    stale = generated.stamp("old text\n", ["x"])
    (tmp_path / "targets" / "codex" / "AGENTS.md").write_text(stale, encoding="utf-8")
    assert any("AGENTS.md: stale" in line for line in targets.check())


def test_sox_install_check_exit_codes(tmp_path):
    assert sox.main(["install", "--check"]) == 1
    targets.generate()
    assert sox.main(["install", "--check"]) == 0
    (tmp_path / "targets" / "codex" / "AGENTS.md").write_text("hand\n", encoding="utf-8")
    assert sox.main(["install", "--check", "--target", "claude"]) == 0
    assert sox.main(["install", "--check", "--target", "codex"]) == 1


def test_targets_directory_is_gitignored():
    assert "/targets/" in (REPO / ".gitignore").read_text(encoding="utf-8").splitlines()


# ---------- plan, apply ----------

def test_plan_writes_nothing_to_home(tmp_path, capsys):
    claude, codex = tmp_path / "home" / ".claude", tmp_path / "home" / ".codex"
    claude.mkdir(parents=True)
    codex.mkdir(parents=True)
    (claude / "CLAUDE.md").write_text("my own notes\n", encoding="utf-8")
    (claude / "settings.json").write_text(json.dumps({"theme": "dark"}), encoding="utf-8")
    (codex / "config.toml").write_text("[x]\ny = 1\n", encoding="utf-8")
    before = tree(tmp_path / "home")
    assert sox.main(["install", "--plan"]) == 0
    out = capsys.readouterr().out
    assert tree(tmp_path / "home") == before
    assert "create:" in out and "change:" in out and "remove: none" in out
    assert f"--- {claude / 'CLAUDE.md'} (installed)" in out and "+++ " in out and "GENERATED by sox install" in out
    assert (tmp_path / "targets" / "claude" / "CLAUDE.md").is_file()


def test_plan_can_be_limited_to_one_agent(tmp_path, capsys):
    assert sox.main(["install", "--plan", "--target", "codex"]) == 0
    out = capsys.readouterr().out
    summary = " ".join(line for line in out.splitlines() if line.startswith(("  create:", "  change:")))
    assert "AGENTS.md" in summary and "CLAUDE.md" not in summary
    assert not (tmp_path / "home" / ".claude").exists() and not (tmp_path / "targets" / "claude").exists()


def test_apply_refuses_without_yes(monkeypatch, capsys):
    monkeypatch.setattr(install, "run", lambda *a, **k: pytest.fail("must not install without --yes"))
    assert sox.main(["install"]) == 2
    assert "--yes" in capsys.readouterr().err


def test_apply_backs_up_before_changing_anything(monkeypatch):
    import backup

    order = []
    monkeypatch.setattr(backup, "backup", lambda label="ai-config": order.append("backup") or Path("backup.zip"))
    monkeypatch.setattr(targets, "generate", lambda *a, **k: order.append("targets") or [])
    monkeypatch.setattr(install, "install_steps", lambda *a, **k: order.append("steps"))
    monkeypatch.setattr(install, "save_prefs", lambda: None)
    assert sox.main(["install", "--yes"]) == 0
    assert order == ["backup", "targets", "steps"]


def test_sync_waits_for_the_first_approved_apply(monkeypatch, capsys):
    monkeypatch.setattr(install, "install_steps", lambda *a, **k: pytest.fail("sync must not apply before the owner did"))
    assert install.run("sync") == 0
    assert "sox install --plan" in capsys.readouterr().out


# ---------- startup entry ----------

@pytest.mark.parametrize("load", [True, False])
def test_load_rules_toggles_the_rules_document(monkeypatch, load):
    monkeypatch.setattr(install, "load_rules", lambda: load)
    block = install.claude_block()
    assert ("core/RULES.md" in block) is load
    assert "core/INIT.md" in block and "core/STYLE.md" in block and "claude/CLAUDE.md" in block and "local/profile.md" in block
    agents = install.codex_agents_md()
    assert (RULES_TITLE in agents) is load
    assert INIT_TITLE in agents and "Reply profile UCE" in agents
    assert generated.verify(agents) == "ok"


def test_startup_size_shrinks_without_the_rules_document(monkeypatch):
    monkeypatch.setattr(install, "load_rules", lambda: True)
    full = {name: targets.startup_bytes(name) for name in ("claude", "codex")}
    monkeypatch.setattr(install, "load_rules", lambda: False)
    lean = {name: targets.startup_bytes(name) for name in ("claude", "codex")}
    rules = (REPO / "core" / "RULES.md").stat().st_size
    assert all(lean[name] < full[name] for name in full) and full["claude"] - lean["claude"] >= rules


def test_load_rules_reads_the_config_key(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    shutil.copytree(REPO / "defaults", root / "defaults")
    monkeypatch.setattr(install, "SOCRATEX", root)
    assert core.resolve(None, root)["values"]["startup"]["load_rules"] is True
    assert install.load_rules() is True
    override = root / "local" / "overrides" / "config.json"
    override.parent.mkdir(parents=True)
    override.write_text(json.dumps({"schema_version": 1, "startup": {"load_rules": False}}), encoding="utf-8")
    assert install.load_rules() is False
    assert core.resolve(None, root)["provenance"]["startup.load_rules"]["layer"] == "local"
