"""Criteria 2-5, 8, 9, 11, 12, 15 and the runner edge cases, on a throwaway git repo with a fake model."""

from __future__ import annotations

import json

from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

import common
import merge
import run
from conftest import (REGISTRY_PATH, REVIEW_DIR, APP_V1, APP_V2_COMMENTS, APP_V2_JUDGE, APP_V2_PLAIN, SELECT_ALL, SELECT_FAIL, FakeImplementer,
                      FakeModel, always_ok, all_tools, model_finding)

from test_registry import GOOD, write_registry


def go(repo, files=("app.py",), run_id="r1", **kwargs):
    kwargs.setdefault("keep", True)
    return run.run_review(repo.path, list(files), run_id=run_id, **kwargs)


def kinds(events, name):
    return [e for e in events if e["event"] == name]


def custom_registry(tmp_path, select_script, **checker):
    entry = {**GOOD, "select": f"{{python}} {select_script.as_posix()}", "tier": "cheap", "autofix": "none",
             "max_chunk_lines": 10, **checker}
    return write_registry(tmp_path / "custom.json", [entry])


def test_no_changes_exits_zero_without_model_call(repo, run_kwargs):
    model = FakeModel()
    result = go(repo, model=model, **run_kwargs)
    assert result["exit_code"] == 0 and model.calls == []
    events = repo.log_events("r1")
    assert len(kinds(events, "empty_diff")) == 1
    assert len(events) == 1  # an empty run is exactly one log line


def test_trivial_change_below_threshold_is_skipped(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    model = FakeModel()
    result = go(repo, model=model, **{**run_kwargs, "min_changed_lines": 100})
    assert result["exit_code"] == 0 and model.calls == []
    assert kinds(repo.log_events("r1"), "trivial_change")


def test_no_candidates_means_zero_model_calls_per_checker(repo, run_kwargs):
    repo.write("app.py", APP_V2_PLAIN)
    model = FakeModel()
    result = go(repo, model=model, **run_kwargs)
    assert result["exit_code"] == 0 and model.calls == []
    cost = kinds(repo.log_events("r1"), "cost")[0]["checkers"]
    assert cost and all(row["model_calls"] == 0 for row in cost.values())


def test_check_phase_leaves_git_status_unchanged_and_each_checker_writes_only_its_file(repo, run_kwargs):
    repo.write("app.py", APP_V2_COMMENTS)
    before = repo.status()
    snapshot = repo.read("app.py")
    model = FakeModel()
    go(repo, model=model, fix=False, **run_kwargs)
    assert repo.status() == before and repo.read("app.py") == snapshot
    names = sorted(p.name for p in repo.run_dir("r1").iterdir())
    registry = common.load_registry(REGISTRY_PATH, None)
    expected = sorted([f"{c['id']}.json" for c in registry["checkers"] if c["enabled"]]
                      + ["findings.json", "log.jsonl", "summary.json"])
    assert names == expected
    for checker in registry["checkers"]:
        doc = json.loads((repo.run_dir("r1") / f"{checker['id']}.json").read_text(encoding="utf-8"))
        assert doc["checker"] == checker["id"] and all(f["checker"] == checker["id"] for f in doc["findings"])


def test_findings_json_matches_schema(repo, run_kwargs):
    repo.write("app.py", APP_V2_COMMENTS)
    go(repo, model=FakeModel(), fix=False, **run_kwargs)
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    schema = json.loads((merge.SCHEMA_PATH).read_text(encoding="utf-8"))
    assert list(Draft202012Validator(schema).iter_errors(doc)) == []
    assert merge.validate(doc) == []
    assert {f["category"] for f in doc["findings"]} >= {"dead-code", "comment-repeats-code"}


def test_mechanical_comment_findings_are_fixed_by_script_without_model(repo, run_kwargs):
    repo.write("app.py", APP_V2_COMMENTS)
    model, implementer = FakeModel(), FakeImplementer()
    go(repo, model=model, implementer=implementer, **run_kwargs)
    assert "#" not in repo.read("app.py") and "def total" in repo.read("app.py")
    assert model.by_checker("comments") == [] and implementer.calls == []
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    assert {f["status"] for f in doc["findings"] if f["checker"] == "comments"} == {"fixed"}


def test_other_sessions_files_are_never_touched(repo, run_kwargs):
    repo.write("other.py", "# old = sum(items)\nvalue = 1\n")
    repo.commit_all("other")
    repo.write("other.py", "# old = sum(items)\nvalue = 2\n")
    repo.write("app.py", APP_V2_COMMENTS)
    other = repo.read("other.py")
    go(repo, model=FakeModel(), **run_kwargs)
    assert repo.read("other.py") == other
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    assert {f["file"] for f in doc["findings"]} == {"app.py"}


def test_binary_and_generated_files_are_skipped(repo, run_kwargs):
    repo.write("logo.png", b"\x89PNG\x00\x01binary")
    repo.write("bundle.min.js", "var a=1;\n// x = foo(1)\n")
    repo.write("blob.dat", b"abc\x00def")
    repo.commit_all("assets")
    repo.write("logo.png", b"\x89PNG\x00\x02changed")
    repo.write("bundle.min.js", "var a=2;\n// x = foo(1)\n")
    repo.write("blob.dat", b"abc\x00xyz")
    model = FakeModel()
    result = go(repo, files=["logo.png", "bundle.min.js", "blob.dat"], model=model, **run_kwargs)
    assert result["exit_code"] == 0 and model.calls == []
    skipped = kinds(repo.log_events("r1"), "empty_diff")[0]["skipped"]
    assert {e["file"] for e in skipped} == {"logo.png", "bundle.min.js", "blob.dat"}
    assert all(e["reason"] for e in skipped)


def test_failing_select_skips_checker_with_reason_and_others_still_run(repo, tmp_path, run_kwargs):
    registry = write_registry(tmp_path / "two.json", [
        {**GOOD, "id": "needs-serena", "select": f"{{python}} {SELECT_FAIL.as_posix()}", "tier": "standard",
         "tool": "none"},
        {**GOOD, "id": "ok-one", "select": f"{{python}} {(REVIEW_DIR / 'select_quality.py').as_posix()} --mode contracts"}])
    repo.write("app.py", APP_V2_PLAIN)
    go(repo, registry_path=registry, model=FakeModel(), **run_kwargs)
    bad = json.loads((repo.run_dir("r1") / "needs-serena.json").read_text(encoding="utf-8"))
    good = json.loads((repo.run_dir("r1") / "ok-one.json").read_text(encoding="utf-8"))
    assert bad["status"] == "skipped" and "serena not installed" in bad["reason"]
    assert good["status"] == "done"
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    skipped = {c["id"]: c for c in doc["checkers"]}["needs-serena"]
    assert skipped["status"] == "skipped" and skipped["reason"]


def test_unavailable_tool_skips_checker_with_reason(repo, run_kwargs):
    repo.write("app.py", APP_V2_PLAIN)
    go(repo, model=FakeModel(), **{**run_kwargs, "tool_available": lambda name: name != "graphify"})
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    row = {c["id"]: c for c in doc["checkers"]}["architecture"]
    assert row["status"] == "skipped" and "graphify" in row["reason"]
    assert {c["id"]: c for c in doc["checkers"]}["contracts"]["status"] == "done"


def test_invalid_model_json_retries_once_at_same_tier_then_skips(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    model = FakeModel(lambda request: "this is not json")
    go(repo, model=model, **run_kwargs)
    calls = model.by_checker("comments")
    assert len(calls) == 2 and {c["tier"] for c in calls} == {"cheap"}
    events = repo.log_events("r1")
    assert kinds(events, "model_invalid_json") and not kinds(events, "escalation")
    row = json.loads((repo.run_dir("r1") / "comments.json").read_text(encoding="utf-8"))
    assert row["cost"]["skipped_chunks"] == 1 and row["findings"] == []


def test_low_confidence_escalates_one_tier_with_logged_reason(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)

    def responder(request):
        return model_finding(request, confidence="low" if request["tier"] == "cheap" else "high")

    model = FakeModel(responder)
    go(repo, model=model, fix=False, **run_kwargs)
    calls = model.by_checker("comments")
    assert [(c["tier"], c["alias"]) for c in calls] == [("cheap", "haiku"), ("standard", "sonnet")]
    escalation = kinds(repo.log_events("r1"), "escalation")
    assert [(e["from_tier"], e["to_tier"], e["reason"]) for e in escalation] == [("cheap", "standard", "confidence_low")]
    row = json.loads((repo.run_dir("r1") / "comments.json").read_text(encoding="utf-8"))
    assert [f["confidence"] for f in row["findings"]] == ["high"]


def test_no_escalation_when_confidence_is_fine(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    model = FakeModel(lambda request: model_finding(request))
    go(repo, model=model, fix=False, **run_kwargs)
    assert len(model.by_checker("comments")) == 1
    assert not kinds(repo.log_events("r1"), "escalation")


def test_chunks_never_exceed_limit_and_splits_are_logged(repo, tmp_path, run_kwargs):
    registry = custom_registry(tmp_path, SELECT_ALL, scope="file")
    repo.write("big.py", "".join(f"v{i} = {i}\n" for i in range(35)))
    seen = []

    def responder(request):
        seen.append(request["line_end"] - request["line_start"] + 1)
        return "[]"

    go(repo, files=["big.py"], registry_path=registry, model=FakeModel(responder), **run_kwargs)
    assert seen and max(seen) <= 10 and len(seen) == 4
    splits = kinds(repo.log_events("r1"), "chunk_split")
    assert splits and splits[0]["parts"] == 4 and splits[0]["limit"] == 10


def test_cost_log_has_calls_tier_and_input_size_per_checker(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    go(repo, model=FakeModel(lambda request: "[]"), **run_kwargs)
    cost = kinds(repo.log_events("r1"), "cost")[0]["checkers"]
    assert cost["comments"]["model_calls"] == 1 and cost["comments"]["tier"] == "cheap"
    assert cost["comments"]["input_chunks"] == 1 and cost["comments"]["input_lines"] >= 1
    assert cost["leaks"]["model_calls"] == 0 and cost["leaks"]["tier"] == "script"
    summary = json.loads((repo.run_dir("r1") / "summary.json").read_text(encoding="utf-8"))
    assert summary["cost"]["comments"] == cost["comments"] and summary["model_calls"] == 1


def judge_model(request):
    return model_finding(request)


def test_agent_fixes_run_one_file_at_a_time_without_overlap(repo, run_kwargs):
    for name in ("a.py", "b.py", "c.py"):
        repo.write(name, APP_V1)
    repo.commit_all("more")
    for name in ("a.py", "b.py", "c.py"):
        repo.write(name, APP_V2_JUDGE)

    def fix(path, request):
        path.write_bytes(path.read_bytes().replace(b"    # keeps totals in sync with the ledger\n", b""))

    implementer = FakeImplementer(fix, delay=0.03)
    go(repo, files=["a.py", "b.py", "c.py"], model=FakeModel(judge_model), implementer=implementer, **run_kwargs)
    assert sorted(c["file"] for c in implementer.calls) == ["a.py", "b.py", "c.py"]
    events = repo.log_events("r1")
    starts = {e["file"]: e["t"] for e in kinds(events, "fix_start")}
    ends = {e["file"]: e["t"] for e in kinds(events, "fix_end")}
    spans = sorted((starts[f], ends[f]) for f in starts)
    assert all(a_end <= b_start for (_, a_end), (b_start, _) in zip(spans, spans[1:]))
    assert all("started" in e and "ended" in e for e in kinds(events, "fix_end"))
    assert "keeps totals" not in repo.read("a.py")


def test_agent_brief_contains_only_that_files_findings(repo, run_kwargs):
    repo.write("a.py", APP_V1)
    repo.commit_all("a")
    repo.write("a.py", APP_V2_JUDGE)
    repo.write("app.py", APP_V2_JUDGE)
    implementer = FakeImplementer()
    go(repo, files=["a.py", "app.py"], model=FakeModel(judge_model), implementer=implementer, **run_kwargs)
    by_file = {c["file"]: c for c in implementer.calls}
    assert "app.py" not in by_file["a.py"]["brief"].replace("a.py", "") and len(by_file["a.py"]["findings"]) == 1


def test_fix_that_breaks_gate_is_reverted_and_reported_with_escalation(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    original = repo.read("app.py")
    implementer = FakeImplementer(lambda path, request: path.write_bytes(path.read_bytes() + b"BROKEN\n"))

    def gate(project_dir):
        text = (project_dir / "app.py").read_text(encoding="utf-8")
        return ("BROKEN" not in text), "tests failed"

    kwargs = {**run_kwargs, "gate": gate}
    result = go(repo, model=FakeModel(judge_model), implementer=implementer, **kwargs)
    assert result["exit_code"] == 0 and repo.read("app.py") == original
    assert [c["tier"] for c in implementer.calls] == ["standard", "high"]
    events = repo.log_events("r1")
    assert [e["reason"] for e in kinds(events, "escalation")] == ["gate_failed"]
    assert len(kinds(events, "revert")) == 2
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    finding = [f for f in doc["findings"] if f["checker"] == "comments"][0]
    assert finding["status"] == "reported" and "reverted" in finding["note"]


def test_reverted_fix_keeps_foreign_edits_in_other_files(repo, run_kwargs):
    repo.write("other.py", "value = 1\n")
    repo.commit_all("other")
    repo.write("other.py", "value = 2\n")
    repo.write("app.py", APP_V2_JUDGE)
    implementer = FakeImplementer(lambda path, request: path.write_bytes(path.read_bytes() + b"BROKEN\n"))
    gate = lambda project_dir: (b"BROKEN" not in (project_dir / "app.py").read_bytes(), "")
    go(repo, model=FakeModel(judge_model), implementer=implementer, **{**run_kwargs, "gate": gate})
    assert repo.read("other.py") == "value = 2\n"


def test_runner_stops_after_two_fix_rounds_even_with_open_findings(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    implementer = FakeImplementer()
    result = go(repo, model=FakeModel(judge_model), implementer=implementer, **run_kwargs)
    assert result["exit_code"] == 0 and len(implementer.calls) == 2
    events = repo.log_events("r1")
    assert len(kinds(events, "round_start")) == 2 and kinds(events, "rounds_exhausted")
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    assert doc["rounds"] == 2
    assert [f["status"] for f in doc["findings"] if f["checker"] == "comments"] == ["open"]


def test_implementer_exception_is_contained(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)

    def boom(path, request):
        raise RuntimeError("agent crashed")

    original = repo.read("app.py")
    result = go(repo, model=FakeModel(judge_model), implementer=FakeImplementer(boom), **run_kwargs)
    assert result["exit_code"] == 0 and repo.read("app.py") == original


def test_findings_outside_the_given_files_or_lines_are_dropped_or_clamped(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)

    def wild(request):
        return json.dumps([{"line_start": 1, "line_end": 999, "message": "m", "severity": "bogus"}])

    go(repo, model=FakeModel(wild), fix=False, **run_kwargs)
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    finding = [f for f in doc["findings"] if f["checker"] == "comments"][0]
    assert finding["line_end"] <= len(APP_V2_JUDGE.splitlines()) and finding["severity"] in merge.SEVERITIES


def test_readability_findings_are_always_judgment_without_script_fix(repo, run_kwargs):
    body = "".join(f"    x{i} = {i}\n" for i in range(50))
    repo.write("long.py", "def big():\n" + body)

    def model(request):
        return model_finding(request, kind="mechanical", fix={"type": "script", "command_or_patch": "rm -rf"},
                             category="long-function")

    go(repo, files=["long.py"], model=FakeModel(model), fix=False, **run_kwargs)
    doc = json.loads((repo.run_dir("r1") / "findings.json").read_text(encoding="utf-8"))
    found = [f for f in doc["findings"] if f["checker"] == "readability"]
    assert found and all(f["kind"] == "judgment" and f["fix"]["type"] != "script" for f in found)


def test_dry_run_reports_plan_without_model_or_writes(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    model = FakeModel()
    result = go(repo, model=model, dry_run=True, **run_kwargs)
    assert result["exit_code"] == 0 and model.calls == [] and not repo.work.exists()
    plan = {row["id"]: row for row in result["plan"]}
    assert plan["comments"]["predicted_model_calls"] == 1 and plan["leaks"]["predicted_model_calls"] == 0
    assert plan["comments"]["candidates"] == 1 and plan["comments"]["chunks"] >= 1


def test_cli_dry_run_and_empty_diff(repo, capsys):
    assert run.main(["--project-dir", str(repo.path), "--files", "app.py", "--dry-run", "--run-id", "x"]) == 0
    assert "no changes" in capsys.readouterr().out.lower()


def test_files_outside_project_are_rejected(repo, tmp_path, run_kwargs):
    result = go(repo, files=[str(tmp_path / "elsewhere.py")], model=FakeModel(), **run_kwargs)
    assert result["exit_code"] == 0
    assert kinds(repo.log_events("r1"), "empty_diff")[0]["skipped"][0]["reason"].startswith("outside")


def test_default_helpers_exist():
    assert callable(run.default_model) and callable(run.default_implementer) and callable(always_ok) and all_tools("x")


def test_run_files_live_outside_the_repo_and_repo_stays_clean(repo, run_kwargs):
    repo.write("app.py", APP_V2_PLAIN)
    before = repo.status()
    result = go(repo, model=FakeModel(), fix=False, **run_kwargs)
    assert result["run_dir"] == repo.run_dir("r1") and result["run_dir"].is_dir()
    assert repo.path.resolve() not in result["run_dir"].resolve().parents
    assert repo.status() == before and not (repo.path / "review").exists()


def test_default_work_base_is_the_temp_folder(repo, monkeypatch, tmp_path):
    import engine
    import tempfile
    monkeypatch.delenv(engine.WORK_DIR_ENV)
    assert engine.work_root() == Path(tempfile.gettempdir()) / "socratex-pipeline"
    assert engine.work_root(tmp_path / "x") == tmp_path / "x"


def test_run_folder_is_removed_after_the_run_unless_kept(repo, run_kwargs):
    repo.write("app.py", APP_V2_PLAIN)
    result = go(repo, run_id="gone", keep=False, model=FakeModel(), **run_kwargs)
    assert result["exit_code"] == 0 and result["run_dir"] is None and not repo.run_dir("gone").exists()
    assert result["summary"]["model_calls"] == 0 and result["doc"]["findings"] == []
    go(repo, run_id="kept", keep=True, model=FakeModel(), **run_kwargs)
    assert (repo.run_dir("kept") / "findings.json").is_file()


def test_work_base_argument_overrides_environment(repo, run_kwargs, tmp_path):
    repo.write("app.py", APP_V2_PLAIN)
    base = tmp_path / "custom-base"
    result = go(repo, work_base=base, model=FakeModel(), **run_kwargs)
    assert result["run_dir"] == base / "review" / "r1"


def test_stale_run_folders_of_the_pipeline_are_pruned(repo, run_kwargs):
    import os
    old = repo.run_dir("old")
    old.mkdir(parents=True)
    stamp = old.stat().st_mtime - 30 * 86400
    os.utime(old, (stamp, stamp))
    fresh = repo.run_dir("fresh")
    fresh.mkdir(parents=True)
    repo.write("app.py", APP_V2_PLAIN)
    go(repo, model=FakeModel(), **run_kwargs)
    assert not old.exists() and fresh.exists()


def test_cli_prints_uce_report_and_keeps_findings_with_keep(repo, capsys):
    repo.write("app.py", APP_V2_COMMENTS)
    code = run.main(["--project-dir", str(repo.path), "--files", "app.py", "--min-changed-lines", "0", "--run-id", "cli",
                     "--keep", "--no-fix"])
    out = capsys.readouterr().out
    assert code == 0 and "Review" in out and "❓" in out
    assert (repo.run_dir("cli") / "findings.json").is_file()
