"""Tests for the PreToolUse guard: the deterministic safety net, so it is run exactly as Claude Code runs it."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

GUARD = Path(__file__).resolve().parents[2] / "claude" / "hooks" / "guard.py"


def run_guard(payload, tmp_path: Path, project_config: dict | None = None, env: dict | None = None):
    """Run guard.py with the payload on stdin (a str is sent raw). Returns (exit code, stderr)."""
    if project_config is not None:
        (tmp_path / ".ai").mkdir(exist_ok=True)
        (tmp_path / ".ai" / "guard.json").write_text(json.dumps(project_config), encoding="utf-8")
    environment = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path), **(env or {})}
    if not env or "SOCRATEX_GUARD" not in env:
        environment.pop("SOCRATEX_GUARD", None)
    stdin = payload if isinstance(payload, str) else json.dumps(payload)
    result = subprocess.run([sys.executable, "-I", "-B", str(GUARD)], input=stdin, capture_output=True, text=True,
                            env=environment, cwd=tmp_path)
    return result.returncode, result.stderr


def bash(command: str) -> dict:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def tool(name: str, path: str, **extra) -> dict:
    return {"tool_name": name, "tool_input": {"file_path": path, **extra}}


@pytest.mark.parametrize("command", [
    "git reset --hard",
    "git reset --hard HEAD~1",
    "git -C some/dir reset --hard",
    "git clean -fd",
    "git checkout .",
    "git restore .",
    "git checkout -- .",
    "git stash drop",
    "git stash clear",
    "git push --force origin main",
    "git push origin main -f",
    "git branch -D feature",
    "git add -A",
    "git add .",
    "git add --all",
    "cat .env",
    "type .env.local",
    "Get-Content .env",
    "echo hi && git reset --hard",
])
def test_blocks_dangerous_bash(command, tmp_path):
    code, stderr = run_guard(bash(command), tmp_path)
    assert code == 2, command
    assert "Blocked by guard" in stderr


@pytest.mark.parametrize("command", [
    "git status",
    "git add src/app.py",
    "git add docs/README.md tools/install.py",
    "git commit -m 'simple message'",
    "git push origin main",
    "git push origin feature",
    "git reset --soft HEAD~1",
    "git branch -d merged-branch",
    "git checkout feature",
    "cat README.md",
    "cat .env.example",
    "ls -la",
])
def test_allows_normal_bash(command, tmp_path):
    code, stderr = run_guard(bash(command), tmp_path)
    assert code == 0, (command, stderr)


@pytest.mark.parametrize("name", [".env", ".env.production", "server.pem", "id_rsa", "id_ed25519", "secrets.key",
                                  ".credentials.json", "auth.json", "cert.p12"])
@pytest.mark.parametrize("tool_name", ["Read", "Edit", "Write"])
def test_blocks_secret_files_for_every_file_tool(name, tool_name, tmp_path):
    code, _ = run_guard(tool(tool_name, f"C:\\work\\project\\{name}"), tmp_path)
    assert code == 2


@pytest.mark.parametrize("name", [".env.example", ".env.sample", "config.template", "README.md", "environment.py"])
def test_allows_templates_and_normal_files(name, tmp_path):
    code, stderr = run_guard(tool("Read", f"/repo/{name}"), tmp_path)
    assert code == 0, (name, stderr)


def test_project_big_file_cannot_be_dumped_or_read_whole(tmp_path):
    config = {"big_files": ["TASKS.json"], "big_file_reader": "use task_show.py"}
    code, stderr = run_guard(bash("cat TASKS.json"), tmp_path, config)
    assert code == 2 and "use task_show.py" in stderr
    assert run_guard(tool("Read", "/p/TASKS.json"), tmp_path, config)[0] == 2
    assert run_guard(tool("Read", "/p/TASKS.json", limit=500), tmp_path, config)[0] == 2
    assert run_guard(tool("Read", "/p/TASKS.json", limit=100), tmp_path, config)[0] == 0
    assert run_guard(tool("Read", "/p/other.json"), tmp_path, config)[0] == 0


def test_project_read_only_dir_blocks_writes_but_not_reads(tmp_path):
    config = {"read_only_dirs": ["legacy-archive"]}
    assert run_guard(tool("Edit", "/p/legacy-archive/old.md"), tmp_path, config)[0] == 2
    assert run_guard(tool("Write", "C:\\p\\legacy-archive\\old.md"), tmp_path, config)[0] == 2
    assert run_guard(tool("Read", "/p/legacy-archive/old.md"), tmp_path, config)[0] == 0
    assert run_guard(tool("Edit", "/p/src/new.md"), tmp_path, config)[0] == 0


def test_project_blocked_commands(tmp_path):
    config = {"blocked_commands": [{"pattern": r"rm\s+-rf\s+build", "reason": "never wipe build"}]}
    code, stderr = run_guard(bash("rm -rf build"), tmp_path, config)
    assert code == 2 and "never wipe build" in stderr
    assert run_guard(bash("rm -rf cache"), tmp_path, config)[0] == 0


@pytest.mark.parametrize("raw", ["", "not json", "[]", "null", '"text"', "{"])
def test_malformed_input_fails_closed(raw, tmp_path):
    code, stderr = run_guard(raw, tmp_path)
    assert code == 2
    assert "SOCRATEX_GUARD=0" in stderr


def test_can_be_disabled_for_one_session(tmp_path):
    assert run_guard(bash("git reset --hard"), tmp_path, env={"SOCRATEX_GUARD": "0"})[0] == 0


def test_broken_project_config_does_not_crash_the_guard(tmp_path):
    (tmp_path / ".ai").mkdir()
    (tmp_path / ".ai" / "guard.json").write_text("{ not json", encoding="utf-8")
    assert run_guard(bash("git status"), tmp_path)[0] == 0
    assert run_guard(bash("git reset --hard"), tmp_path)[0] == 2


def test_other_tools_pass_through(tmp_path):
    assert run_guard({"tool_name": "Grep", "tool_input": {"pattern": "x"}}, tmp_path)[0] == 0
