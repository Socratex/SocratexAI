"""Acceptance criteria and edge cases of docs/specs/planning-pipeline/SPEC.md."""

from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path

import pytest

# planning_testkit first: it puts modules/engine and modules/stages/planning on sys.path.
from planning_testkit import PLAN_NO_UNKNOWNS, PLANNING_DIR, REGISTRY_PATH, FakeModel, go, planning_run, project  # noqa: F401 (fixture)

import common  # noqa: E402
import engine  # noqa: E402
import merge  # noqa: E402
import planning_report  # noqa: E402
import select_research  # noqa: E402
import stage_files  # noqa: E402

ENTRY_FIELDS = {"id", "pipeline", "stage", "concern", "scope", "max_chunk_lines", "select", "tool", "tier", "autofix",
                "fix_script", "enabled"}
# Built from parts so this file does not match its own grep.
OLD_NAMES = [re.compile(p) for p in (r"model" + r"_tier", r"input" + r"_scope", r"""["']scr""" + r"""ipt["']\s*:""",
                                     r"""["']autofix["']\s*:\s*(true|false|"yes"|"no")""")]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def contradiction(request: dict) -> str:
    return json.dumps([{"line_start": request["line_start"], "line_end": request["line_start"], "severity": "major",
                        "confidence": "high", "category": "research-contradiction",
                        "message": "Research says Linux is unsupported, the owner answered Windows only."}])


def with_patch(request: dict) -> str:
    return json.dumps([{"line_start": request["line_start"], "line_end": request["line_end"], "severity": "minor",
                        "confidence": "high", "category": "suggestion", "message": "Rewrite it.", "patch": "REPLACED"}])


def write_registry(path: Path, top: dict | None = None, **changes) -> Path:
    """Copy of the real registry with absolute select paths and per-id field changes."""
    doc = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    for checker in doc["checkers"]:
        checker["select"] = checker["select"].replace("{here}", PLANNING_DIR.as_posix())
        checker.update(changes.get(checker["id"], {}))
    doc.update(top or {})
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def stage_events(run_dir: Path) -> list[dict]:
    lines = (run_dir / "log.jsonl").read_text(encoding="utf-8").splitlines()
    return [e for e in map(json.loads, lines) if e["event"].startswith("stage_")]


# --- criteria 2, 3, 4, 8: registry and shared engine ---------------------------------------------------------------

def test_registry_validates_and_has_both_stages_with_autofix_none():
    registry = common.load_registry(REGISTRY_PATH, None)
    assert registry["pipeline"] == "planning"
    assert [(c["id"], c["stage"]) for c in registry["checkers"]] == [("research", "research"),
                                                                      ("interpretation-check", "check")]
    raw = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    assert raw["schema"] == "socratex-checker-registry/v1"
    for entry in raw["checkers"]:
        assert set(entry) == ENTRY_FIELDS, entry["id"]
        assert entry["pipeline"] == "planning" and entry["autofix"] == "none" and entry["fix_script"] is None


def test_no_old_field_names_in_planning_folder():
    hits = []
    for path in PLANNING_DIR.rglob("*"):
        if path.suffix in (".py", ".json") and "__pycache__" not in path.parts:
            text = path.read_text(encoding="utf-8")
            hits += [f"{path.name}: {p.pattern}" for p in OLD_NAMES if p.search(text)]
    assert hits == []


def test_runner_uses_the_shared_engine_without_its_own_copy():
    assert planning_run.engine is engine and planning_run.merge is merge and planning_run.common is common
    for path in PLANNING_DIR.glob("*.py"):
        assert "def run_pipeline" not in path.read_text(encoding="utf-8"), path.name


def test_findings_use_the_review_format_and_validate(project):
    result = go(project, keep=True, model=FakeModel(contradiction))
    doc = result["doc"]
    assert merge.validate(doc) == [] and doc["schema"] == merge.DOC_SCHEMA
    on_disk = json.loads((result["run_dir"] / "findings.json").read_text(encoding="utf-8"))
    assert on_disk == doc and merge.validate(on_disk) == []
    assert {f["checker"] for f in doc["findings"]} == {"research", "interpretation-check"}


# --- criteria 1, 6, 7: research stage ------------------------------------------------------------------------------

def test_research_records_executor_and_reason_per_unknown(project):
    doc = go(project)["doc"]
    research = [f for f in doc["findings"] if f["checker"] == "research"]
    by_category = {f["category"]: f["message"] for f in research}
    assert set(by_category) == {"research-codex", "research-scout"}
    assert "executor: codex" in by_category["research-codex"] and "reason:" in by_category["research-codex"]
    assert "executor: scout" in by_category["research-scout"]
    text = planning_report.render(doc)
    assert "Wykonawca: Codex" in text and "Wykonawca: scout" in text


def test_no_unknowns_skips_research_and_report_says_why(project):
    project.write("plan.md", PLAN_NO_UNKNOWNS)
    doc = go(project)["doc"]
    assert [f for f in doc["findings"] if f["checker"] == "research"] == []
    assert "Research pominięty: brak niewiadomych do rozstrzygnięcia faktami" in planning_report.render(doc)


def test_codex_unavailable_falls_back_to_scout_or_skips_with_a_note(project, monkeypatch):
    monkeypatch.setenv("PLANNING_CODEX_AVAILABLE", "0")
    project.write("plan.md", "- Unknown: current price of the hosting API (see the online docs)?\n"
                             "- Unknown: please summarize the notes of the last meeting?\n")
    doc = go(project)["doc"]
    categories = {f["category"] for f in doc["findings"] if f["checker"] == "research"}
    assert categories == {"research-skipped", "research-scout"}
    skipped = next(f for f in doc["findings"] if f["category"] == "research-skipped")
    assert "scout has no web access" in skipped["message"]
    assert "nikt, bo Codex jest niedostępny" in planning_report.render(doc)


def test_executor_names_come_from_the_routing_file():
    assert select_research.routing_executors() == {"codex": "codex", "scout": "scout"}
    assert select_research.classify("verify the repo function name") == "repo"
    assert select_research.classify("check the docs for the api version") == "internet"
    assert select_research.classify("which color do you prefer") is None


# --- criteria 5, 10: check stage -----------------------------------------------------------------------------------

def test_check_model_sees_only_answers_and_plan_slice(project):
    project.write("conversation.md", "SECRET-CONVERSATION-LINE\n")
    model = FakeModel()
    go(project, model=model)
    assert len(model.calls) == 1
    call = model.calls[0]
    assert call["checker"] == "interpretation-check" and call["file"] == stage_files.SLICE
    assert "planning review" in call["prompt"] and "Never rewrite the plan" in call["prompt"]
    assert "A: Windows only" in call["prompt"] and "Ship for Windows and Linux." in call["prompt"]
    assert "SECRET-CONVERSATION-LINE" not in call["prompt"] and "Untouched" not in call["prompt"]


def test_research_notes_reach_the_check_and_contradiction_is_flagged(project):
    project.write("notes.md", "Research: the library has no Linux build.\n")
    model = FakeModel(contradiction)
    result = go(project, research_notes="notes.md", model=model)
    assert "no Linux build" in model.calls[0]["prompt"]
    text = planning_report.render(result["doc"])
    assert "Research przeczy odpowiedzi właściciela: 1 (decyzja po stronie właściciela)" in text
    assert "❓" in text


def test_check_stage_leaves_plan_answers_and_spec_byte_identical(project):
    names = ("plan.md", "answers.md", "SPEC.md")
    before = {name: digest(project.path / name) for name in names}
    go(project, keep=True, model=FakeModel(with_patch), run_id="a")
    go(project, model=FakeModel(), run_id="b")
    assert {name: digest(project.path / name) for name in names} == before


def test_check_findings_are_reported_never_fixed(project):
    doc = go(project, model=FakeModel(contradiction))["doc"]
    assert all(f["status"] == "open" for f in doc["findings"]) and doc["rounds"] == 0


# --- criterion 9, run folder lifecycle -----------------------------------------------------------------------------

def test_run_files_live_in_the_temp_folder_and_are_removed(project):
    before = project.status()
    kept = go(project, run_id="kept", keep=True)
    assert kept["run_dir"] == project.run_dir("kept") and (kept["run_dir"] / "findings.json").is_file()
    assert (kept["run_dir"] / "log.jsonl").is_file() and not (kept["run_dir"] / ".running").exists()
    assert project.path.resolve() not in kept["run_dir"].resolve().parents
    gone = go(project, run_id="gone")
    assert gone["run_dir"] is None and not project.run_dir("gone").exists()
    assert project.status() == before and not (project.path / "planning").exists()
    # Engine cost summaries are redirected into the run folder: nothing is left behind outside it.
    assert [p.name for p in (project.work / "planning").iterdir()] == ["kept"]
    import shutil
    shutil.rmtree(kept["run_dir"])
    assert list((project.work / "planning").rglob("*")) == []


def test_default_base_is_the_temp_folder_under_socratex_pipeline(monkeypatch):
    import tempfile
    monkeypatch.delenv(engine.WORK_DIR_ENV, raising=False)
    assert engine.work_root() / "planning" == Path(tempfile.gettempdir()) / "socratex-pipeline" / "planning"


def test_folder_is_removed_when_the_run_fails(project):
    def boom(request):
        raise KeyboardInterrupt
    with pytest.raises(KeyboardInterrupt):
        go(project, run_id="boom", model=boom)
    assert not project.run_dir("boom").exists()


def test_killed_run_folder_is_cleaned_by_the_next_run(project):
    stale = project.run_dir("killed")
    stale.mkdir(parents=True)
    (stale / ".running").write_text("x", encoding="utf-8")
    (stale / "log.jsonl").write_text("{}\n", encoding="utf-8")
    old = time.time() - 2 * 3600
    os.utime(stale / ".running", (old, old))
    live = project.run_dir("live")
    live.mkdir(parents=True)
    (live / ".running").write_text("x", encoding="utf-8")
    go(project, run_id="next")
    assert not stale.exists() and live.exists()


def test_two_runs_of_the_same_plan_get_separate_run_ids(project):
    first, second = go(project, run_id=None, keep=True), go(project, run_id=None, keep=True)
    assert first["doc"]["run_id"] != second["doc"]["run_id"]
    assert first["run_dir"] != second["run_dir"] and first["run_dir"].is_dir() and second["run_dir"].is_dir()
    with pytest.raises(planning_run.InputError) as err:
        go(project, run_id=first["doc"]["run_id"])
    assert "already in use" in str(err.value)


# --- registry entries: missing tool, fix_script, disabled ----------------------------------------------------------

def test_missing_tool_names_the_entry_id(project, tmp_path):
    registry = write_registry(tmp_path / "r.json", **{"research": {"tool": "graphify"}})
    with pytest.raises(common.RegistryError) as err:
        go(project, registry_path=registry, tool_available=lambda name: False)
    assert "research" in str(err.value) and "graphify" in str(err.value)
    assert not project.run_dir("r1").exists()


def test_missing_fix_script_names_the_entry_id(project, tmp_path):
    registry = write_registry(tmp_path / "r.json", **{"interpretation-check": {"fix_script": "{python} /nowhere/fix.py"}})
    with pytest.raises(common.RegistryError) as err:
        go(project, registry_path=registry)
    assert "interpretation-check" in str(err.value) and "fix_script" in str(err.value)


def test_missing_select_script_names_the_entry_id(project, tmp_path):
    registry = write_registry(tmp_path / "r.json", **{"research": {"select": "{python} /nowhere/select.py"}})
    with pytest.raises(common.RegistryError) as err:
        go(project, registry_path=registry)
    assert "research" in str(err.value)


def test_disabled_entry_is_skipped_and_noted(project, tmp_path):
    registry = write_registry(tmp_path / "r.json", **{"research": {"enabled": False}})
    model = FakeModel()
    result = go(project, registry_path=registry, model=model)
    assert result["disabled"] == ["research"]
    assert [c["id"] for c in result["doc"]["checkers"]] == ["interpretation-check"]
    assert "Research pominięty: wyłączony w rejestrze" in planning_report.render(result["doc"], result["disabled"])
    assert len(model.calls) == 1


def test_project_override_applies_to_planning(project):
    project.write(".ai/planning.json", json.dumps({"checkers": {"interpretation-check": {"enabled": False}}}))
    model = FakeModel()
    result = go(project, model=model)
    assert model.calls == [] and result["disabled"] == ["interpretation-check"]


# --- dry-run, CLI, documented form rules ---------------------------------------------------------------------------

def test_dry_run_calls_no_model_and_leaves_nothing(project):
    def never(request):
        raise AssertionError("model called in dry run")
    lines: list[str] = []
    result = go(project, dry_run=True, model=never, out=lines.append)
    assert result["exit_code"] == 0 and result["run_dir"] is None and not project.run_dir("r1").exists()
    assert any("interpretation-check" in line and "predicted_model_calls=1" in line for line in lines)
    assert "Research potrzebny" in planning_report.render_plan(result["plan"], result["disabled"])


def test_cli_prints_uce_report_in_dry_run(project, capsys):
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "plan.md",
                              "--dry-run"])
    out = capsys.readouterr().out
    assert code == 0 and "Research potrzebny" in out and "Sprawdzenie" in out


def test_cli_reports_bad_input_with_exit_2(project, capsys):
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "missing.md"])
    assert code == 2 and "plan file not found" in capsys.readouterr().err
    project.write("empty.md", "  \n")
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "empty.md"])
    assert code == 2 and "empty" in capsys.readouterr().err


def test_cli_bad_registry_entry_exits_2_and_names_it(project, tmp_path, capsys):
    registry = write_registry(tmp_path / "r.json", **{"research": {"select": "{python} /nowhere/select.py"}})
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "plan.md",
                              "--registry", str(registry)])
    assert code == 2 and "research" in capsys.readouterr().err


def test_form_rules_are_documented_in_the_runner_not_faked_in_code():
    text = (PLANNING_DIR / "run.py").read_text(encoding="utf-8")
    assert "at most 4 questions per round" in text and "more than 4 gaps" in text and 'marked "assumed"' in text
    for path in PLANNING_DIR.glob("*.py"):
        code = path.read_text(encoding="utf-8")
        assert path.name == "run.py" or "gaps" not in code


# --- review fixes: order, heartbeat, run id, race, added entries, all skipped -----------------------------------------

def test_research_runs_before_check_and_its_notes_reach_the_check_slice(project):
    seen = {}

    def model(request):
        seen["at"] = time.time()
        seen["prompt"] = request["prompt"]
        return "[]"
    result = go(project, keep=True, model=model)
    events = stage_events(result["run_dir"])
    assert [(e["event"], e["stage"]) for e in events] == [("stage_start", "research"), ("stage_end", "research"),
                                                           ("stage_start", "check"), ("stage_end", "check")]
    research_end = events[1]["t"]
    assert seen["at"] >= research_end and events[2]["t"] >= research_end
    assert "Research decision" in seen["prompt"] and "executor: scout" in seen["prompt"]
    slice_text = (result["run_dir"] / "input" / stage_files.SLICE).read_text(encoding="utf-8")
    assert "# Research notes" in slice_text


def test_research_notes_option_overrides_the_automatic_notes(project):
    project.write("notes.md", "Real research result: sqlite 3.45 has JSON.\n")
    model = FakeModel()
    go(project, research_notes="notes.md", model=model)
    prompt = model.calls[0]["prompt"]
    assert "sqlite 3.45 has JSON" in prompt and "Research decision" not in prompt


def test_heartbeat_keeps_a_long_live_run_and_orphans_need_a_stale_heartbeat(project, monkeypatch):
    monkeypatch.setattr(planning_run, "HEARTBEAT_SECONDS", 0.05)
    monkeypatch.setattr(planning_run, "ORPHAN_SECONDS", 0.5)
    young_orphan = project.run_dir("orphan")
    young_orphan.mkdir(parents=True)
    (young_orphan / ".running").write_text("x", encoding="utf-8")
    stamp = time.time() - 3
    os.utime(young_orphan / ".running", (stamp, stamp))
    seen = {}

    def slow(request):
        marker = project.run_dir("live") / ".running"
        first = marker.stat().st_mtime
        time.sleep(0.9)
        planning_run.sweep_orphans(project.work / "planning")
        seen.update(alive=project.run_dir("live").exists(), beat=marker.stat().st_mtime > first)
        return "[]"
    go(project, run_id="live", model=slow)
    assert seen == {"alive": True, "beat": True} and not young_orphan.exists()


@pytest.mark.parametrize("bad", ["../x", "a/b", "a\\b", "..", ".hidden", "", "a b", "x..y"])
def test_bad_run_id_is_rejected_with_exit_2(project, capsys, bad):
    with pytest.raises(planning_run.InputError):
        go(project, run_id=bad)
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "plan.md",
                              "--run-id", bad])
    assert code == 2 and "run id" in capsys.readouterr().err
    assert not (project.work / "planning").exists() or list((project.work / "planning").iterdir()) == []


def test_run_id_race_is_a_clean_error(project, monkeypatch, capsys):
    def sneaky(pipeline_dir):
        project.run_dir("race").mkdir(parents=True)
    monkeypatch.setattr(planning_run, "sweep_orphans", sneaky)
    with pytest.raises(planning_run.InputError) as err:
        go(project, run_id="race")
    assert "already in use" in str(err.value)
    project.run_dir("race").rmdir()
    project.run_dir("race").parent.rmdir()
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "plan.md",
                              "--run-id", "race"])
    assert code == 2 and "already in use" in capsys.readouterr().err


def add_entry(project, **fields) -> None:
    entry = {"id": "extra", "pipeline": "planning", "stage": "check", "scope": "file", "tier": "script",
             "autofix": "none", **fields}
    project.write(".ai/planning.json", json.dumps({"add": [entry]}))


def test_added_entry_with_here_or_relative_script_is_rejected_naming_the_id(project):
    for select in ("{python} {here}/select_check.py", "{python} select_check.py"):
        add_entry(project, select=select)
        with pytest.raises(common.RegistryError) as err:
            go(project)
        assert "'extra'" in str(err.value)
    add_entry(project, select="{python} " + (PLANNING_DIR / "select_check.py").as_posix(), fix_script="{python} fix.py")
    with pytest.raises(common.RegistryError) as err:
        go(project)
    assert "'extra'" in str(err.value) and "fix_script" in str(err.value)


def test_added_entry_with_absolute_script_runs_from_the_run_folder(project):
    add_entry(project, select="{python} " + (PLANNING_DIR / "select_check.py").as_posix())
    doc = go(project)["doc"]
    assert "extra" in [c["id"] for c in doc["checkers"]] and any(f["checker"] == "extra" for f in doc["findings"])


def test_all_inputs_skipped_exits_non_zero_with_a_message(project, tmp_path, capsys):
    registry = write_registry(tmp_path / "r.json", top={"skip_patterns": ["*.md"]})
    for dry in (False, True):
        result = go(project, registry_path=registry, dry_run=dry)
        assert result["exit_code"] == 3 and "skipped" in result["message"] and "doc" not in result
    code = planning_run.main(["--project-dir", str(project.path), "--answers", "answers.md", "--plan", "plan.md",
                              "--registry", str(registry)])
    assert code == 3 and "skipped" in capsys.readouterr().err
    assert list((project.work / "planning").rglob("*")) == []


def test_review_and_planning_modules_do_not_shadow_each_other():
    import sys
    assert "run" not in sys.modules or sys.modules["run"].__file__ != (PLANNING_DIR / "run.py").as_posix()
    assert str(PLANNING_DIR) not in sys.path[:1]
