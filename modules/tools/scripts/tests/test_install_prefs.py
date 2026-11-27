"""Tests for the install questions: nothing optional is forced, answers are honoured."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

import install  # noqa: E402


@pytest.fixture(autouse=True)
def restore_prefs():
    saved = dict(install.PREFS), install.CLAUDE, install.CODEX
    yield
    install.PREFS.clear()
    install.PREFS.update(saved[0])
    install.CLAUDE, install.CODEX = saved[1], saved[2]


def test_default_settings_fragment_has_guard_hook_and_optional_parts():
    install.apply_prefs({})
    fragment = install.settings_fragment("python")
    assert "PreToolUse" in fragment["hooks"]
    assert "enabledPlugins" in fragment and "CLAUDE_CODE_PLUGIN_DIRS" in fragment["env"]


def test_codex_plugin_and_flow_panel_are_optional():
    install.apply_prefs({"codex_plugin": False, "flow_panel": False})
    fragment = install.settings_fragment("python")
    assert "enabledPlugins" not in fragment and "extraKnownMarketplaces" not in fragment
    assert "CLAUDE_CODE_PLUGIN_DIRS" not in fragment["env"]
    assert "PreToolUse" in fragment["hooks"] and fragment["permissions"]["deny"]


def test_plain_style_drops_the_reply_style_document_everywhere():
    install.apply_prefs({"style": "plain"})
    assert "defaults/STYLE.md" not in install.claude_block()
    assert "Reply profile UCE" not in install.codex_agents_md()
    install.apply_prefs({"style": "uce"})
    assert "defaults/STYLE.md" in install.claude_block()
    assert "Reply profile UCE" in install.codex_agents_md()


def test_config_folders_come_from_saved_choice_or_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "c"))
    monkeypatch.setenv("CODEX_HOME", str(tmp_path / "x"))
    install.apply_prefs({})
    assert install.CLAUDE == tmp_path / "c" and install.CODEX == tmp_path / "x"
    install.apply_prefs({"claude_dir": str(tmp_path / "mine")})
    assert install.CLAUDE == tmp_path / "mine" and install.CODEX == tmp_path / "x"


def test_unattended_wizard_gives_the_recommended_answers():
    prefs = install.collect_prefs(auto=True)
    assert prefs["merge_settings"] and prefs["style"] == "uce" and prefs["git_hooks"] and prefs["set_env"]
    assert prefs["flow_panel"] is False


def test_interactive_wizard_respects_no_answers(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda _prompt="": "n")
    monkeypatch.setattr(install, "detect_dirs", lambda: (Path("c"), Path("x")))
    prefs = install.collect_prefs(auto=False)
    assert not prefs["merge_settings"] and not prefs["codex_plugin"] and not prefs["flow_panel"]
    assert prefs["style"] == "plain" and not prefs["git_hooks"] and not prefs["set_env"]


def test_full_install_without_terminal_or_yes_refuses_to_guess(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(install, "PREFS_FILE", tmp_path / "install.json")
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    assert install.resolve_prefs("full", auto=False, reconfigure=False) is False
    assert "--yes" in capsys.readouterr().out


def test_panel_stack_is_off_by_default_and_needs_flow_panel():
    install.apply_prefs({})
    assert install.PREFS["panel_stack"] is False
    install.apply_prefs({"panel_stack": True})
    assert install.PREFS["panel_stack"] is True


def test_panel_stack_adds_the_quiet_option_for_lot_map():
    install.apply_prefs({"panel_stack": True})
    options = install.settings_fragment("python")["pluginConfigs"]["lot-map@sox-local"]["options"]
    assert options == {"guardedHooks": False}
    install.apply_prefs({})
    assert "pluginConfigs" not in install.settings_fragment("python")


def test_legacy_generated_block_is_stripped():
    text = "A\n" + install.LEGACY_BEGIN + "\n@x\n" + install.END + "\n\nmine\n"
    out = install.strip_legacy_block(text)
    assert install.LEGACY_BEGIN not in out and "@x" not in out and "mine" in out and out.startswith("A")
