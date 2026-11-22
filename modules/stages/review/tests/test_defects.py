"""Regression tests for the reviewer's defects: scoped comment fixes, trivial-change leaks, fix escalation, reports."""

from __future__ import annotations

import json
import os

import common
import report
import run
from conftest import SELECT_ALL, APP_V1, APP_V2_COMMENTS, APP_V2_JUDGE, FakeImplementer, FakeModel, model_finding
from test_registry import GOOD, write_registry
from test_run_flow import go, judge_model, kinds

OLD_COMMENT = "# old = foo(1)"


def load(repo, name, run_id="r1"):
    return json.loads((repo.run_dir(run_id) / name).read_text(encoding="utf-8"))


def test_comment_fix_touches_only_the_flagged_changed_lines(repo, run_kwargs):
    repo.write("app.py", APP_V1 + f"\n\ndef old():\n    {OLD_COMMENT}\n    return 1\n")
    repo.commit_all("with old comment")
    repo.write("app.py", repo.read("app.py") + "\n\ndef new():\n    # old = bar(2)\n    return 2\n")
    go(repo, model=FakeModel(), **run_kwargs)
    text = repo.read("app.py")
    assert OLD_COMMENT in text and "# old = bar(2)" not in text


def test_trivial_change_still_runs_script_checkers_without_a_model(repo, run_kwargs):
    secret = "sk-ant-" + "A" * 24
    repo.write("app.py", APP_V1 + f"KEY = '{secret}'\n")
    model = FakeModel()
    result = go(repo, model=model, **{**run_kwargs, "min_changed_lines": 6})
    assert model.calls == []
    assert any(f["checker"] == "leaks" for f in result["doc"]["findings"])
    assert kinds(repo.log_events("r1"), "trivial_change")


def test_no_higher_tier_after_gate_failure_stops_and_reports(repo, tmp_path, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    original = repo.read("app.py")
    implementer = FakeImplementer(lambda path, request: path.write_bytes(path.read_bytes() + b"BROKEN\n"))
    gate = lambda project_dir: (b"BROKEN" not in (project_dir / "app.py").read_bytes(), "tests failed")
    registry = write_registry(tmp_path / "high.json", [{**GOOD, "id": "comments", "tier": "cheap", "autofix": "agent",
                                                      "select": f"{{python}} {SELECT_ALL.as_posix()}"}])
    raw = json.loads(registry.read_text(encoding="utf-8"))
    raw["implementer_tier"] = "high"
    registry.write_text(json.dumps(raw), encoding="utf-8")
    result = go(repo, registry_path=registry, model=FakeModel(judge_model), implementer=implementer,
                **{**run_kwargs, "gate": gate})
    assert [c["tier"] for c in implementer.calls] == ["high"]
    assert repo.read("app.py") == original and not kinds(repo.log_events("r1"), "escalation")
    findings = [f for f in result["doc"]["findings"] if f["checker"] == "comments"]
    assert findings and all(f["status"] == "reported" and "reverted" in f["note"] for f in findings)


def test_skip_reasons_reach_the_report_without_keep(repo, run_kwargs):
    repo.write("app.py", APP_V1 + "\n\ndef double(x):\n    return x * 2\n")
    result = go(repo, run_id="nokeep", keep=False, model=FakeModel(),
                **{**run_kwargs, "tool_available": lambda name: name != "graphify"})
    assert result["run_dir"] is None and not repo.run_dir("nokeep").exists()
    text = report.render(result["doc"])
    skipped = [line for line in text.splitlines() if "Pominięte" in line]
    assert skipped and "graphify" in skipped[0]
    assert "nokeep" not in text and str(repo.work) not in text


def test_failed_select_is_named_in_the_report_without_script_output(repo, tmp_path, run_kwargs):
    from conftest import SELECT_FAIL
    registry = write_registry(tmp_path / "bad.json", [
        {**GOOD, "id": "needs-serena", "select": f"{{python}} {SELECT_FAIL.as_posix()}", "tier": "standard", "tool": "none"}])
    repo.write("app.py", APP_V1 + "x = 1\n")
    result = go(repo, registry_path=registry, keep=False, model=FakeModel(), **run_kwargs)
    line = [line for line in report.render(result["doc"]).splitlines() if "Pominięte" in line][0]
    assert "wyboru" in line and "serena" not in line.lower() and str(tmp_path) not in line


def test_cost_summary_survives_cleanup_and_is_pruned_after_seven_days(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    result = go(repo, run_id="cost1", keep=False, model=FakeModel(lambda request: "[]"), **run_kwargs)
    path = repo.work / "review" / "summaries" / "cost1.json"
    assert result["run_dir"] is None and path.is_file()
    data = json.loads(path.read_text(encoding="utf-8"))
    row = data["cost"]["comments"]
    assert row["model_calls"] == 1 and row["tier"] == "cheap" and row["input_chunks"] == 1
    assert row["escalations"] == 0 and row["rejected"] == 0
    stamp = path.stat().st_mtime - 30 * 86400
    os.utime(path, (stamp, stamp))
    go(repo, run_id="cost2", keep=False, model=FakeModel(), **run_kwargs)
    assert not path.exists() and (repo.work / "review" / "summaries" / "cost2.json").is_file()


def test_dry_run_writes_no_cost_summary(repo, run_kwargs):
    repo.write("app.py", APP_V2_JUDGE)
    go(repo, dry_run=True, model=FakeModel(), **run_kwargs)
    assert not (repo.work / "review").exists()


def test_cli_stdout_has_no_run_id_or_run_folder_and_stderr_has_the_hint(repo, capsys):
    repo.write("app.py", APP_V2_JUDGE)
    code = run.main(["--project-dir", str(repo.path), "--files", "app.py", "--min-changed-lines", "0", "--run-id", "secretid",
                     "--keep", "--no-fix"])
    captured = capsys.readouterr()
    assert code == 0 and "secretid" not in captured.out and "socratex-pipeline" not in captured.out
    assert str(repo.work) not in captured.out and "routing_log" not in captured.out
    assert "routing_log" in captured.err and "cost summary" in captured.err


def test_agent_fix_that_leaves_the_flagged_comment_is_reported_not_fixed(repo, run_kwargs):
    repo.write("app.py", APP_V2_COMMENTS)

    def touch_only(path, request):
        path.write_bytes(path.read_bytes() + b"\n# unrelated\n")

    registry = write_registry(repo.work.parent / "recheck.json", [{
        **GOOD, "id": "comments", "tier": "cheap", "autofix": "agent",
        "select": f"{{python}} {(run.HERE / 'select_comments.py').as_posix()}"}])
    implementer = FakeImplementer(touch_only)
    result = go(repo, registry_path=registry, model=FakeModel(), implementer=implementer, **run_kwargs)
    findings = [f for f in result["doc"]["findings"] if f["checker"] == "comments"]
    assert implementer.calls and findings and all(f["status"] != "fixed" for f in findings)
    assert any(f["status"] == "reported" and "still flags" in f["note"] for f in findings)


def test_here_of_a_project_checker_is_the_project_dir(repo, tmp_path):
    ai = repo.path / ".ai"
    ai.mkdir()
    (ai / "review.json").write_text(json.dumps({"add": [{**GOOD, "id": "mine", "select": "{python} {here}/x.py"}]}),
                                   encoding="utf-8")
    registry = common.load_registry(run.DEFAULT_REGISTRY, repo.path)
    by_id = {c["id"]: c for c in registry["checkers"]}
    assert by_id["mine"]["here"] == repo.path.resolve()
    assert by_id["comments"]["here"] == run.HERE
