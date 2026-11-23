"""Tests for core/safety.json, the guard that reads it, owner-only relaxations, `config show` and the safety log."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "core"))

import core  # noqa: E402

GUARD = REPO / "claude" / "hooks" / "guard.py"
_loader = importlib.machinery.SourceFileLoader("sox_cli", str(REPO / "core" / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture()
def world(tmp_path):
    """A fake SocratexAI folder (shipped rules and defaults) plus a project folder."""
    root = tmp_path / "repo"
    (root / "core").mkdir(parents=True)
    shutil.copy(REPO / "core" / "safety.json", root / "core" / "safety.json")
    shutil.copytree(REPO / "defaults", root / "defaults")
    project = tmp_path / "proj"
    project.mkdir()
    return root, project


def owner(root, data):
    return write(root / "local" / "overrides" / "config.json", {"schema_version": 1, **data})


def project_file(project, data):
    return write(project / ".socratex" / "config.json", {"schema_version": 1, **data})


def guard(payload, root, project, **env):
    environment = {**os.environ, "SOCRATEX_HOME": str(root), "CLAUDE_PROJECT_DIR": str(project), **env}
    for name in ("SOCRATEX_GUARD", "SOCRATEX_GUARD_ALLOW_SAFETY_EDIT"):
        if name not in env:
            environment.pop(name, None)
    run = subprocess.run([sys.executable, "-I", "-B", str(GUARD)], input=json.dumps(payload), capture_output=True,
                         text=True, env=environment, cwd=project)
    return run.returncode, run.stderr


def bash(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def tool(name, path):
    return {"tool_name": name, "tool_input": {"file_path": str(path)}}


# ---------- the rules file ----------

def test_safety_json_matches_its_schema():
    jsonschema = pytest.importorskip("jsonschema")
    data = json.loads((REPO / "core" / "safety.json").read_text(encoding="utf-8"))
    jsonschema.validate(data, json.loads((REPO / "core" / "safety.schema.json").read_text(encoding="utf-8")))
    ids = [rule["id"] for rule in data["rules"]]
    assert len(ids) == len(set(ids))
    assert not next(r for r in data["rules"] if r["id"] == "safety-config-edits")["relaxable"]


def test_yolo_adapter_names_real_rules():
    ids = {rule["id"] for rule in json.loads((REPO / "core" / "safety.json").read_text(encoding="utf-8"))["rules"]}
    yolo = json.loads((REPO / "defaults" / "adapters" / "yolo.json").read_text(encoding="utf-8"))
    assert set(yolo["config"]["safety"]["allow"]) <= ids


def test_guard_reads_its_rules_from_safety_json(world):
    root, project = world
    path = root / "core" / "safety.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    rule = next(r for r in data["rules"] if r["id"] == "destructive-git")
    rule["enforce"][0]["reason"] = "CUSTOM-REASON-FROM-DATA"
    path.write_text(json.dumps(data), encoding="utf-8")
    code, err = guard(bash("git reset --hard"), root, project)
    assert code == 2 and "CUSTOM-REASON-FROM-DATA" in err
    data["rules"] = [r for r in data["rules"] if r["id"] != "destructive-git"]
    path.write_text(json.dumps(data), encoding="utf-8")
    assert guard(bash("git reset --hard"), root, project)[0] == 0


def test_unreadable_safety_json_fails_closed(world):
    root, project = world
    (root / "core" / "safety.json").write_text("{not json", encoding="utf-8")
    code, err = guard(bash("ls"), root, project)
    assert code == 2 and "safety.json" in err


# ---------- relaxation by owner layers ----------

def test_allow_skips_only_that_rule(world):
    root, project = world
    assert guard(bash("git reset --hard"), root, project)[0] == 2
    owner(root, {"safety": {"allow": ["destructive-git"]}})
    assert guard(bash("git reset --hard"), root, project)[0] == 0
    assert guard(bash("git add -A"), root, project)[0] == 2
    assert guard(bash("cat .env"), root, project)[0] == 2


def test_yolo_adapter_relaxes_its_three_rules(world):
    root, project = world
    owner(root, {"adapter": "yolo"})
    assert guard(bash("git reset --hard"), root, project)[0] == 0
    assert guard(bash("cat .env"), root, project)[0] == 0
    assert guard(tool("Read", project / ".env"), root, project)[0] == 0
    assert guard(bash("git add -A"), root, project)[0] == 2


def test_private_project_layer_may_relax(world):
    root, project = world
    write(root / "local" / "projects" / project.name / "config.json", {"schema_version": 1, "safety": {"allow": ["git-add-all"]}})
    assert guard(bash("git add -A"), root, project)[0] == 0


def test_project_file_cannot_relax_and_is_reported(world):
    root, project = world
    project_file(project, {"safety": {"allow": ["destructive-git"]}})
    assert guard(bash("git reset --hard"), root, project)[0] == 2
    result = core.resolve(project, root)
    assert result["safety"]["relaxed"] == []
    assert any("project file is ignored" in line for line in result["safety"]["errors"])
    assert "safety" not in result["values"]


def test_project_file_cannot_select_a_relaxing_adapter(world):
    root, project = world
    project_file(project, {"adapter": "yolo"})
    result = core.resolve(project, root)
    assert result["safety"]["relaxed"] == [] and "allow" not in result["values"].get("safety", {})
    assert any("selected by the project file" in line for line in result["safety"]["errors"])
    assert guard(bash("git reset --hard"), root, project)[0] == 2


def test_unknown_and_unrelaxable_ids_are_errors(world):
    root, project = world
    owner(root, {"safety": {"allow": ["no-such-rule", "safety-config-edits"]}})
    result = core.resolve(project, root)
    assert result["safety"]["relaxed"] == []
    assert len(result["safety"]["errors"]) == 2
    assert guard(tool("Write", root / "core" / "safety.json"), root, project)[0] == 2


def test_relaxation_source_is_the_layer_that_introduced_it(world):
    root, project = world
    owner(root, {"adapter": "yolo", "safety": {"allow": {"$append": ["git-add-all"]}}})
    relaxed = {item["rule"]: item for item in core.resolve(project, root)["safety"]["relaxed"]}
    assert relaxed["destructive-git"]["layer"] == "adapter" and relaxed["destructive-git"]["file"].endswith("yolo.json")
    assert relaxed["git-add-all"]["layer"] == "local"


# ---------- the agent cannot edit the files that relax rules ----------

PROTECTED = ["core/safety.json", "core/safety.schema.json", "local/overrides/config.json", "local/projects/p/config.json",
             "defaults/config.json", "defaults/adapters/yolo.json"]


@pytest.mark.parametrize("relative", PROTECTED)
@pytest.mark.parametrize("name", ["Write", "Edit"])
def test_agent_cannot_edit_safety_files(world, relative, name):
    root, project = world
    code, err = guard(tool(name, root / relative), root, project)
    assert code == 2 and "defines or relaxes safety rules" in err


def test_agent_cannot_edit_a_project_socratex_config(world):
    root, project = world
    assert guard(tool("Write", project / ".socratex" / "config.json"), root, project)[0] == 2


@pytest.mark.parametrize("command", [
    "echo '{}' > {root}/local/overrides/config.json",
    "echo '{}' >> {root}/core/safety.json",
    "cp /tmp/x {root}/local/projects/p/config.json",
    "mv /tmp/x {root}/defaults/adapters/yolo.json",
    "sed -i s/a/b/ {root}/core/safety.json",
    "tee {root}/defaults/config.json",
    "rm {root}/core/safety.json",
    "python -c \"open('{root}/core/safety.json','w').write('x')\"",
    "echo '{}' > {project}/.socratex/config.json",
    "git checkout HEAD~1 -- {root}/core/safety.json",
])
def test_agent_cannot_write_safety_files_from_bash(world, command):
    root, project = world
    code, err = guard(bash(command.replace("{root}", root.as_posix()).replace("{project}", project.as_posix())), root, project)
    assert code == 2 and "safety" in err


@pytest.mark.parametrize("command", [
    "cat {root}/core/safety.json",
    "git add {root}/core/safety.json",
    "cp {root}/core/safety.json /tmp/copy.json",
    "python modules/tools/scripts/json_read.py {root}/core/safety.json rules",
    "echo hi > {root}/notes.txt",
])
def test_reading_and_staging_safety_files_is_fine(world, command):
    root, project = world
    assert guard(bash(command.replace("{root}", root.as_posix())), root, project)[0] == 0
    assert guard(tool("Read", root / "core" / "safety.json"), root, project)[0] == 0


def test_owner_env_switch_allows_editing_the_safety_files(world):
    root, project = world
    assert guard(tool("Write", root / "core" / "safety.json"), root, project, SOCRATEX_GUARD_ALLOW_SAFETY_EDIT="1")[0] == 0
    assert guard(bash(f"echo x > {root.as_posix()}/core/safety.json"), root, project, SOCRATEX_GUARD_ALLOW_SAFETY_EDIT="1")[0] == 0


def test_same_file_names_elsewhere_are_not_protected(world, tmp_path):
    root, project = world
    assert guard(tool("Write", tmp_path / "other" / "core" / "safety.json"), root, project)[0] == 0


# ---------- config show and the log ----------

def run_show(world, monkeypatch, capsys, *extra):
    root, project = world
    original = core.resolve
    monkeypatch.setattr(core, "resolve", lambda project_root=None, base=None: original(project_root, root))
    assert sox.main(["config", "show", "--project", str(project), *extra]) == 0
    return capsys.readouterr().out


def test_config_show_starts_with_the_relaxed_rules_block(world, monkeypatch, capsys):
    out = run_show(world, monkeypatch, capsys)
    assert out.splitlines()[:2] == ["Relaxed safety rules:", "  none"]
    root, _ = world
    owner(root, {"adapter": "yolo"})
    lines = run_show(world, monkeypatch, capsys).splitlines()
    assert lines[0] == "Relaxed safety rules:"
    assert lines[1].startswith("  destructive-git  <- adapter: ") and lines[1].endswith("yolo.json")
    assert {l.split()[0] for l in lines[1:4]} == {"destructive-git", "secret-files", "ledger-dumps"}


def test_config_show_reports_a_project_file_relaxation_as_an_error(world, monkeypatch, capsys):
    _, project = world
    project_file(project, {"safety": {"allow": ["git-add-all"]}})
    lines = run_show(world, monkeypatch, capsys).splitlines()
    assert lines[1] == "  none"
    assert lines[2].startswith("  error: ") and "project file is ignored" in lines[2]


def read_log(root):
    path = root / "state" / "safety-log.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()] if path.is_file() else []


def test_safety_log_gets_one_record_per_change(world):
    root, project = world
    owner(root, {"adapter": "yolo"})
    core.write_effective(project, root)
    core.write_effective(project, root)
    log = read_log(root)
    assert [r["rule"] for r in log] == ["destructive-git", "secret-files", "ledger-dumps"]
    assert all(r["event"] == "relaxed" and r["project"] == str(project.resolve()) and r["time"] and r["source"] for r in log)
    owner(root, {"adapter": "yolo", "safety": {"allow": {"$append": ["git-add-all"]}}})
    core.write_effective(project, root)
    core.write_effective(project, root)
    assert [r["rule"] for r in read_log(root)][3:] == ["git-add-all"]
    owner(root, {})
    core.write_effective(project, root)
    assert {r["rule"] for r in read_log(root) if r["event"] == "restored"} == {"destructive-git", "secret-files", "ledger-dumps", "git-add-all"}
    count = len(read_log(root))
    core.write_effective(project, root)
    assert len(read_log(root)) == count


def test_ignored_project_relaxation_is_logged_once(world):
    root, project = world
    project_file(project, {"safety": {"allow": ["destructive-git"]}})
    core.write_effective(project, root)
    core.write_effective(project, root)
    log = read_log(root)
    assert len(log) == 1 and log[0]["event"] == "rejected" and "project file is ignored" in log[0]["detail"]
