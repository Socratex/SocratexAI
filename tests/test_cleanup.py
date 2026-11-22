"""Tests for the cleanup phase: sox state/backup/test/migrate, checker provenance, flow `needs`, routing config keys."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "core"
sys.path.insert(0, str(CORE_DIR))
sys.path.insert(0, str(REPO / "modules" / "tools" / "scripts"))

import core  # noqa: E402
import migrate  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_cleanup", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_cleanup", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def age(path: Path, days: float) -> None:
    stamp = time.time() - days * 86400
    os.utime(path, (stamp, stamp))


# ---------- sox state ----------

def test_sox_state_rotate_and_adopt_logs(tmp_path, capsys):
    logs = tmp_path / "state" / "flow-debug"
    logs.mkdir(parents=True)
    old = logs / "old.log"
    old.write_text("x", encoding="utf-8")
    age(old, 40)
    assert sox.main(["state", "--root", str(tmp_path), "rotate", "--dry-run"]) == 0
    assert "would remove 1 file(s)" in capsys.readouterr().out and old.exists()
    assert sox.main(["state", "--root", str(tmp_path), "rotate"]) == 0
    assert "removed 1 file(s)" in capsys.readouterr().out and not old.exists()

    (tmp_path / "local").mkdir()
    legacy = tmp_path / "local" / "flow-debug-1234abcd.log"
    legacy.write_text("hello", encoding="utf-8")
    assert sox.main(["state", "--root", str(tmp_path), "adopt-logs"]) == 0
    assert "1 legacy log(s)" in capsys.readouterr().out and legacy.exists()
    assert sox.main(["state", "--root", str(tmp_path), "adopt-logs", "--yes"]) == 0
    assert not legacy.exists() and (logs / legacy.name).read_text(encoding="utf-8") == "hello"


def test_write_effective_triggers_daily_rotation(tmp_path):
    write(tmp_path / "defaults" / "config.json", {"schema_version": 1})
    logs = tmp_path / "state" / "flow-debug"
    logs.mkdir(parents=True)
    old = logs / "old.log"
    old.write_text("x", encoding="utf-8")
    age(old, 40)
    core.write_effective(None, tmp_path)
    assert not old.exists() and (tmp_path / "state" / ".rotated").is_file()


# ---------- checker provenance ----------

@pytest.fixture()
def stage_root(tmp_path):
    root = tmp_path / "repo"
    (root / "modules" / "engine").mkdir(parents=True)
    shutil.copy(REPO / "modules" / "engine" / "common.py", root / "modules" / "engine" / "common.py")
    shutil.copytree(REPO / "modules" / "stages" / "review", root / "modules" / "stages" / "review",
                    ignore=shutil.ignore_patterns("tests", "__pycache__"))
    project = tmp_path / "proj"
    project.mkdir()
    return root, project


def test_stage_provenance_without_overrides_is_empty(stage_root):
    root, project = stage_root
    assert core.stage_provenance(project, root) == {"review": {"changes": [], "error": None}}


def test_stage_provenance_names_layer_and_file(stage_root):
    root, project = stage_root
    write(root / "local" / "overrides" / "stages" / "review.json", {"checkers": {"comments": {"enabled": False}}})
    write(project / ".ai" / "review.json", {
        "checkers": {"contracts": {"tier": "high"}, "readability": {"max_chunk_lines": 80, "tier": "standard"}},
        "add": [{"id": "extra", "pipeline": "review", "scope": "file", "select": "echo", "tier": "cheap", "autofix": "none"}]})
    write(root / "local" / "projects" / "proj" / "review.json", {"checkers": {"comments": {"enabled": True}}})
    changes = core.stage_provenance(project, root)["review"]["changes"]
    brief = [(c["checker"], c["kind"], c["layer"]) for c in changes]
    assert ("comments", "disabled", "local/overrides/stages/review.json") in brief
    assert ("contracts", "retiered", ".ai/review.json") in brief
    assert ("readability", "max_chunk_lines", ".ai/review.json") in brief
    assert ("extra", "added", ".ai/review.json") in brief
    assert ("comments", "enabled", "local/projects/proj/review.json") in brief
    assert not any(c["checker"] == "readability" and c["kind"] == "retiered" for c in changes)  # same tier: no change
    assert all(Path(c["file"]).is_absolute() for c in changes)


def test_stage_provenance_reports_a_broken_registry(stage_root):
    root, project = stage_root
    write(project / ".ai" / "review.json", {"checkers": {"nope": {"enabled": False}}})
    info = core.stage_provenance(project, root)["review"]
    assert info["changes"] == [] and "unknown checker" in info["error"]


def test_load_registry_result_is_the_same_with_provenance():
    spec = importlib.util.spec_from_file_location("eng_common_t", REPO / "modules" / "engine" / "common.py")
    engine = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(engine)
    path = REPO / "modules" / "stages" / "review" / "checkers.json"
    registry, changes = engine.load_registry_with_provenance(path, None)
    assert isinstance(changes, list)
    assert registry == engine.load_registry(path, None)


def test_config_show_prints_stage_registries(capsys):
    assert sox.main(["config", "show"]) == 0
    assert "Stage registries:" in capsys.readouterr().out
    assert sox.main(["config", "show", "--json"]) == 0
    assert "stage_registries" in json.loads(capsys.readouterr().out)


def test_print_stage_registries_lines(capsys):
    sox.print_stage_registries({"review": {"error": None, "changes": [
        {"checker": "comments", "kind": "disabled", "field": "enabled", "from": True, "to": False,
         "layer": ".ai/review.json", "file": "/p/.ai/review.json"}]}})
    out = capsys.readouterr().out
    assert "comments  disabled (enabled: true -> false)  <- .ai/review.json: /p/.ai/review.json" in out


# ---------- flow needs ----------

def flow_repo(tmp_path, steps):
    root = tmp_path / "repo"
    write(root / "core" / "flow.json", {"schema": "socratex-flow/v1", "steps": steps})
    project = tmp_path / "proj"
    project.mkdir(exist_ok=True)
    return root, project


def step(sid, needs=None):
    s = {"id": sid, "when": {}, "then": ["ask"], "why": "t"}
    if needs is not None:
        s["needs"] = needs
    return s


def test_shipped_flow_needs_resolve():
    steps = {s["id"]: s for s in core.load_flow()["steps"]}
    assert steps["plan_check"]["needs"] == ["plan"]
    assert core.check_flow() == []


def test_needs_satisfied_and_removed_step_is_an_error(tmp_path):
    root, project = flow_repo(tmp_path, [step("a"), step("b", ["a"])])
    assert core.check_flow(project, root) == []
    write(project / ".socratex" / "flow.json", {"schema": "socratex-flow/v1", "steps": {"$remove": ["a"]}})
    errors = core.check_flow(project, root)
    assert len(errors) == 1
    assert "core" in errors[0] and "flow.json: step b: needs step 'a', which does not exist" in errors[0]


def test_needs_must_point_backwards_and_be_a_list(tmp_path):
    root, project = flow_repo(tmp_path, [step("a", ["b"]), step("b"), step("c", ["c"])])
    errors = core.check_flow(project, root)
    assert any("step a: needs step 'b', which does not come before it" in e for e in errors)
    assert any("step c: needs step 'c'" in e for e in errors)
    root, project = flow_repo(tmp_path / "two", [step("a", "b")])
    assert any("needs: expected array" in e for e in core.check_flow(project, root))


def test_override_step_may_declare_needs(tmp_path):
    root, project = flow_repo(tmp_path, [step("a")])
    write(project / ".socratex" / "flow.json", {"schema": "socratex-flow/v1", "steps": {"$append": [step("z", ["a"])]}})
    assert core.check_flow(project, root) == []
    write(project / ".socratex" / "flow.json", {"schema": "socratex-flow/v1", "steps": {"$append": [step("z", ["ghost"])]}})
    assert any("step z: needs step 'ghost'" in e for e in core.check_flow(project, root))


# ---------- sox backup / test ----------

def test_sox_backup_delegates_to_tools_backup(monkeypatch):
    import backup

    seen = []
    monkeypatch.setattr(backup, "main", lambda argv=None: seen.append(argv) or 0)
    assert sox.main(["backup"]) == 0
    assert sox.main(["backup", "--list"]) == 0
    assert sox.main(["backup", "--restore", "x.zip"]) == 0
    assert seen == [[], ["--list"], ["--restore", "x.zip"]]


def test_pytest_command_uses_uv_when_present():
    with_uv = sox.pytest_command([], which=lambda name: "/bin/uv")
    assert with_uv == ["/bin/uv", "run", "--with", "pytest", "--with", "jsonschema", "python", "-m", "pytest", "-q",
                       "tests", "modules"]
    without = sox.pytest_command(["tests/test_core.py"], which=lambda name: None)
    assert without == [sys.executable, "-m", "pytest", "-q", "tests/test_core.py"]


def test_sox_test_runs_the_command(monkeypatch):
    import subprocess

    calls = []

    class Done:
        returncode = 3

    monkeypatch.setattr(subprocess, "run", lambda cmd, cwd=None: calls.append((cmd, cwd)) or Done())
    assert sox.main(["test", "tests/test_core.py"]) == 3
    assert calls[0][0][-1] == "tests/test_core.py" and calls[0][1] == REPO


# ---------- sox migrate ----------

@pytest.fixture()
def fake_migration(monkeypatch):
    monkeypatch.setattr(core, "SUPPORTED_VERSION", 2)
    monkeypatch.setitem(migrate.MIGRATIONS, ("config", 1), lambda d: {**d, "schema_version": 2, "migrated": True})


def test_no_migrations_registered_today():
    assert migrate.MIGRATIONS == {}
    assert migrate.scan() == []


def test_migrate_check_lists_outdated_files_and_steps(tmp_path, fake_migration):
    path = write(tmp_path / "local" / "overrides" / "config.json", {"schema_version": 1})
    row = next(r for r in migrate.scan(None, tmp_path) if r["file"] == str(path))
    assert row["status"] == "outdated" and row["steps"] == [1]
    assert "would run config v1 -> v2" in migrate.describe(row)


def test_migrate_applies_chain_with_backup_and_reports_gaps(tmp_path, fake_migration):
    path = write(tmp_path / "local" / "overrides" / "config.json", {"schema_version": 1, "profile": "duo"})
    prof = write(tmp_path / "defaults" / "profiles" / "duo.json", {"schema_version": 1, "name": "duo"})
    rows = migrate.scan(None, tmp_path)
    by_file = {r["file"]: r for r in rows}
    assert by_file[str(prof)]["status"] == "no-migration" and by_file[str(prof)]["missing"] == 1
    assert len(migrate.apply(rows)) == 1
    assert json.loads(path.read_text(encoding="utf-8")) == {"schema_version": 2, "profile": "duo", "migrated": True}
    assert json.loads(path.with_name("config.json.pre-migrate.bak").read_text(encoding="utf-8"))["schema_version"] == 1
    assert json.loads(prof.read_text(encoding="utf-8"))["schema_version"] == 1  # gap: untouched


def test_migrate_reports_newer_and_unreadable(tmp_path):
    write(tmp_path / "local" / "overrides" / "config.json", {"schema_version": 9})
    (tmp_path / "defaults" / "profiles").mkdir(parents=True)
    (tmp_path / "defaults" / "profiles" / "duo.json").write_text("{not json", encoding="utf-8")
    statuses = {Path(r["file"]).name: r["status"] for r in migrate.scan(None, tmp_path)}
    assert statuses == {"config.json": "newer", "duo.json": "unreadable"}


def test_sox_migrate_clean_repo(capsys):
    assert sox.main(["migrate", "--check"]) == 0
    assert "Nothing to migrate" in capsys.readouterr().out


def test_unsupported_version_hint_points_to_migrate(tmp_path):
    older = write(tmp_path / "old.json", {"schema_version": 0})
    with pytest.raises(core.ConfigError, match=r"sox migrate --check"):
        core.load_layer_file(older)
    newer = write(tmp_path / "new.json", {"schema_version": 9})
    with pytest.raises(core.ConfigError, match="newer than this SocratexAI"):
        core.load_layer_file(newer)


# ---------- routing config keys ----------

def test_routing_tier_overrides_validate_against_routing_tiers():
    routing = json.loads((REPO / "core" / "ROUTING.json").read_text(encoding="utf-8"))
    schema = json.loads((REPO / "core" / "config.schema.json").read_text(encoding="utf-8"))
    allowed = schema["properties"]["routing"]["properties"]["tier_overrides"]["additionalProperties"]["enum"]
    assert set(allowed) == set(routing["claude"]) - {"top"}  # top needs an explained owner yes, never a config value
    assert core.validate({"schema_version": 1, "routing": {"tier_overrides": {"scout": "cheap"}}}, schema, "$") == []
    assert core.validate({"schema_version": 1, "routing": {"tier_overrides": {"scout": "top"}}}, schema, "$")
    assert core.validate({"schema_version": 1, "routing": {"other": 1}}, schema, "$")


def test_routing_key_flows_through_resolve(tmp_path):
    root = tmp_path / "repo"
    write(root / "defaults" / "config.json", {"schema_version": 1})
    write(root / "local" / "overrides" / "config.json",
          {"schema_version": 1, "routing": {"tier_overrides": {"reviewer": "standard"}}})
    assert core.resolve(None, root)["values"]["routing"]["tier_overrides"] == {"reviewer": "standard"}
