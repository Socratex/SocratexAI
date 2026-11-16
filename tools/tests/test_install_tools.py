"""Tests for the installer merge logic, frontmatter stripping and the leak scanner."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_leaks  # noqa: E402
import install  # noqa: E402


def test_deep_merge_keeps_user_keys_and_skips_notes():
    current = {"permissions": {"defaultMode": "auto", "deny": ["Read(.env)"]}, "theme": "dark"}
    fragment = {"_note": "skip me", "permissions": {"deny": ["Read(.env)", "Read(*.pem)"]}, "env": {"A": "1"}}
    merged = install.deep_merge(current, fragment)
    assert merged["permissions"]["defaultMode"] == "auto"
    assert merged["permissions"]["deny"] == ["Read(.env)", "Read(*.pem)"]
    assert merged["theme"] == "dark" and merged["env"] == {"A": "1"}
    assert "_note" not in merged


def test_merge_list_replaces_old_guard_hook_instead_of_duplicating():
    old = [{"hooks": [{"command": "py old/claude/hooks/guard.py"}]}, {"hooks": [{"command": "other.py"}]}]
    new = [{"hooks": [{"command": "py new/claude/hooks/guard.py"}]}]
    merged = install.merge_list(old, new)
    assert len(merged) == 2
    assert merged[-1] == new[0]


def test_strip_frontmatter():
    assert install.strip_frontmatter("---\ntype: rules\n---\n\n# Title\n") == "# Title\n"
    assert install.strip_frontmatter("# No meta\n") == "# No meta\n"


def test_claude_block_imports_core_and_local_profile():
    block = install.claude_block()
    assert block.startswith(install.BEGIN) and block.endswith(install.END)
    for item in install.CLAUDE_IMPORTS:
        assert item in block


def test_leak_scanner_flags_user_paths_and_tokens(tmp_path):
    sample = tmp_path / "sample.md"
    sample.write_text("ok line\npath " + "C:/" + "Users/alice/project\nkey " + "ghp" + "_abcdefghijklmnopqrstuv\nC:/Users/<you>/x\n",
                      encoding="utf-8")
    hits = check_leaks.scan([sample], [__import__("re").compile(p, 2) for p in check_leaks.BUILTIN])
    assert len(hits) == 2
