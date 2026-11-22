"""Tests for `sox project check | init | explain` (core/project_check.py, core/project-check.json). Fixtures live in temp dirs."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "core"
sys.path.insert(0, str(CORE_DIR))

import core  # noqa: E402
import project_check  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_project", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_project", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)

CLEAN = {
    ".socratex/config.json": '{"schema_version": 1}\n',
    "AGENTS.md": "# Project\n- facts only\n",
    "CLAUDE.md": "@AGENTS.md\n\n# Claude notes\n",
    "INDEX.json": json.dumps({"schema": "project-index/v1", "docs": [{"path": "AGENTS.md", "what": "rules"}]}),
}


def make(tmp_path: Path, files: dict | None = None, git: bool = True, base: dict | None = None) -> Path:
    project = tmp_path / "proj"
    project.mkdir(parents=True)
    for rel, content in {**(CLEAN if base is None else base), **(files or {})}.items():
        target = project / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            target.write_bytes(content)
        else:
            target.write_text(content, encoding="utf-8", newline="\n")
    if git:
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        subprocess.run(["git", "add", "-A"], cwd=project, check=True)
    return project


def ids(project: Path) -> list[str]:
    return [f["rule"] for f in project_check.run_check(project)]


def found(project: Path, rule: str) -> list[dict]:
    return [f for f in project_check.run_check(project) if f["rule"] == rule]


# ---------- rules file ----------

def test_rules_file_validates_and_matches_the_checks():
    data = project_check.load_rules()
    assert [r["id"] for r in data["rules"]] == list(project_check.CHECKS)
    assert core.validate(data, json.loads((CORE_DIR / "project-check.schema.json").read_text(encoding="utf-8")), "$") == []


def test_rules_file_rejects_a_bad_severity_and_a_missing_check(tmp_path):
    data = project_check.load_rules()
    data["rules"][0]["severity"] = "fatal"
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(core.ConfigError, match="fatal"):
        project_check.load_rules(bad)
    data = project_check.load_rules()
    data["rules"].append({"id": "PRJ-NEW", "severity": "error", "what": "x", "fix": "y"})
    bad.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(core.ConfigError, match="no check function"):
        project_check.load_rules(bad)


def test_the_expected_rule_ids_exist():
    expected = {"PRJ-LEGACY-REF", "PRJ-LEGACY-FILE", "PRJ-NO-CONFIG", "PRJ-CONFIG-INVALID", "PRJ-FLOW-INVALID",
                "PRJ-AGENTS-LONG", "PRJ-CLAUDE-IMPORT", "PRJ-INDEX-SCHEMA", "PRJ-DUP-RULE", "PRJ-FORK-SCRIPT",
                "PRJ-DUP-HOOK", "PRJ-NONSTD-OVERRIDE", "PRJ-GUARD-SCHEMA", "PRJ-ROUTING-LEGACY"}
    assert set(project_check.CHECKS) == expected
    warnings = {r["id"] for r in project_check.load_rules()["rules"] if r["severity"] == "warning"}
    assert warnings == {"PRJ-DUP-RULE", "PRJ-DUP-HOOK", "PRJ-ROUTING-LEGACY"}


# ---------- one test per rule: positive and negative ----------

def test_clean_project_has_no_findings(tmp_path):
    assert project_check.run_check(make(tmp_path)) == []


@pytest.mark.parametrize("text", ["legacy-pipeline", "SocratexPipeline", ".aiassistant/x", "$SOCRATEX_HOME/tools/a.py",
                                  "SocratexAI/tools/a.py", "see AI-compiled", "SOCRATEX.md"])
def test_legacy_ref_positive(tmp_path, text):
    project = make(tmp_path, {"docs/notes.md": f"line one\nuses {text} here\n"})
    hits = found(project, "PRJ-LEGACY-REF")
    assert [(h["file"], h["line"]) for h in hits] == [("docs/notes.md", 2)]


def test_legacy_ref_negative_for_binary_and_non_text_files(tmp_path):
    project = make(tmp_path, {"docs/clean.md": "nothing here\n", "data.bin": b"\0\0 legacy-pipeline", "src/a.cs": "// SOCRATEX.md"})
    assert found(project, "PRJ-LEGACY-REF") == []


@pytest.mark.parametrize("rel", ["SOCRATEX.md", ".aiassistant/socratex/rules.md", "SocratexAI/PIPELINE-CONFIG.json"])
def test_legacy_file_positive(tmp_path, rel):
    project = make(tmp_path, {rel: "x"})
    assert [h["file"] for h in found(project, "PRJ-LEGACY-FILE")] == [rel]


def test_legacy_file_negative(tmp_path):
    assert found(make(tmp_path, {"docs/SOCRATEX-notes.txt": "x"}), "PRJ-LEGACY-FILE") == []


def test_no_config(tmp_path):
    project = make(tmp_path, base={"AGENTS.md": "x\n"})
    assert [h["file"] for h in found(project, "PRJ-NO-CONFIG")] == [".socratex/config.json"]
    assert found(make(tmp_path / "ok", {}), "PRJ-NO-CONFIG") == []


def test_config_invalid_unknown_key_and_version(tmp_path):
    project = make(tmp_path, {".socratex/config.json": '{"schema_version": 1, "bogus": true}'})
    hits = found(project, "PRJ-CONFIG-INVALID")
    assert len(hits) == 1 and "bogus" in hits[0]["message"]
    project2 = make(tmp_path / "v2", {".socratex/config.json": '{"schema_version": 9}'})
    assert found(project2, "PRJ-CONFIG-INVALID")


def test_config_invalid_project_safety_allow(tmp_path):
    project = make(tmp_path, {".socratex/config.json": '{"schema_version": 1, "safety": {"allow": ["x"]}}'})
    hits = found(project, "PRJ-CONFIG-INVALID")
    assert len(hits) == 1 and "ignored" in hits[0]["message"] and hits[0]["line"] == 1


def test_flow_invalid(tmp_path):
    bad = {"schema_version": 1, "steps": [{"id": "x", "when": {}, "then": ["stage:nope"], "why": "w"}]}
    project = make(tmp_path, {".socratex/flow.json": json.dumps(bad)})
    assert found(project, "PRJ-FLOW-INVALID")
    assert found(make(tmp_path / "n", {}), "PRJ-FLOW-INVALID") == []


def test_agents_long(tmp_path):
    project = make(tmp_path, {"AGENTS.md": "line\n" * 81, "CLAUDE.md": "@AGENTS.md\n" + "line\n" * 50})
    hits = found(project, "PRJ-AGENTS-LONG")
    assert sorted((h["file"], h["line"]) for h in hits) == [("AGENTS.md", 81), ("CLAUDE.md", 51)]


def test_agents_long_at_the_limit_is_fine(tmp_path):
    project = make(tmp_path, {"AGENTS.md": "line\n" * 80, "CLAUDE.md": "@AGENTS.md\n" + "line\n" * 49})
    assert found(project, "PRJ-AGENTS-LONG") == []


def test_claude_import(tmp_path):
    assert [h["file"] for h in found(make(tmp_path, {"CLAUDE.md": "# no import\n"}), "PRJ-CLAUDE-IMPORT")] == ["CLAUDE.md"]
    assert found(make(tmp_path / "x", {}), "PRJ-CLAUDE-IMPORT") == []


def test_index_schema_wrong_schema_bad_json_and_missing_path(tmp_path):
    wrong = make(tmp_path, {"INDEX.json": json.dumps({"schema": "v0", "docs": []})})
    assert [h["file"] for h in found(wrong, "PRJ-INDEX-SCHEMA")] == ["INDEX.json"]
    broken = make(tmp_path / "b", {"INDEX.json": "{not json"})
    assert "not valid JSON" in found(broken, "PRJ-INDEX-SCHEMA")[0]["message"]
    index = {"schema": "project-index/v1", "docs": [{"path": "AGENTS.md"}, {"path": "docs/gone.md"}], "tools": [{"path": "bin/*"}]}
    missing = make(tmp_path / "m", {"INDEX.json": json.dumps(index)})
    hits = found(missing, "PRJ-INDEX-SCHEMA")
    assert len(hits) == 1 and "docs/gone.md" in hits[0]["message"]


def test_dup_rule_is_a_warning_in_entry_files_and_docs_only(tmp_path):
    project = make(tmp_path, {"AGENTS.md": "# P\nReply profile UCE applies\nnever reset --hard\n", "docs/a.md": "All code 100% English\n",
                              "src/readme.md": "reset --hard"})
    hits = found(project, "PRJ-DUP-RULE")
    assert {(h["file"], h["severity"]) for h in hits} == {("AGENTS.md", "warning"), ("docs/a.md", "warning")}
    assert len(hits) == 3


def test_fork_script_positive_and_negative(tmp_path):
    project = make(tmp_path, {"scripts/risk_score.py": "x", ".claude/agents/reviewer.md": "x", "docs/reviewer.md": "x",
                              "tools/install.py": "x", "tools/mine.py": "x"})
    assert sorted(h["file"] for h in found(project, "PRJ-FORK-SCRIPT")) == [".claude/agents/reviewer.md", "scripts/risk_score.py"]


def test_dup_hook(tmp_path):
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "python .claude/hooks/pretool_guard.py"}]}],
                          "PostToolUse": [{"hooks": [{"type": "command", "command": "python guard.py"}]}]}}
    project = make(tmp_path, {".claude/settings.json": json.dumps(settings, indent=2)})
    hits = found(project, "PRJ-DUP-HOOK")
    assert len(hits) == 1 and hits[0]["severity"] == "warning" and hits[0]["file"] == ".claude/settings.json"
    other = {"hooks": {"PreToolUse": [{"hooks": [{"type": "command", "command": "python lint_check.py"}]}]}}
    assert found(make(tmp_path / "n", {".claude/settings.json": json.dumps(other)}), "PRJ-DUP-HOOK") == []


def test_nonstd_override(tmp_path):
    project = make(tmp_path, {"config/MODEL-ROUTING.json": "{}", "RISK-RULES.json": "{}", "tools/guard.json": "{}",
                              ".ai/RISK-RULES.json": "{}", ".ai/guard.json": "{}", "data/other.json": "{}"})
    assert sorted(h["file"] for h in found(project, "PRJ-NONSTD-OVERRIDE")) == ["RISK-RULES.json", "config/MODEL-ROUTING.json", "tools/guard.json"]


def test_guard_schema(tmp_path):
    project = make(tmp_path, {".ai/guard.json": json.dumps({"_about": "n", "big_files": [], "bogus": 1}, indent=2),
                              ".ai/review.json": json.dumps({"checkers": {}, "skip_patterns": []}),
                              ".ai/planning.json": "{broken"})
    hits = found(project, "PRJ-GUARD-SCHEMA")
    assert sorted((h["file"], h["line"]) for h in hits) == [(".ai/guard.json", 4), (".ai/planning.json", 1)]


def test_routing_legacy_is_a_warning(tmp_path):
    hits = found(make(tmp_path, {".ai/ROUTING.json": "{}"}), "PRJ-ROUTING-LEGACY")
    assert [(h["file"], h["severity"]) for h in hits] == [(".ai/ROUTING.json", "warning")]


# ---------- scanning and exclusions ----------

def test_excluded_areas_are_not_scanned(tmp_path):
    marker = "uses legacy-pipeline\n"
    project = make(tmp_path, {"audits/archive/a.md": marker, ".claude/worktrees/w/b.md": marker, "node_modules/p/c.md": marker,
                              "docs/big.md": marker + "x" * 1_100_000, "kept.md": marker})
    assert [h["file"] for h in found(project, "PRJ-LEGACY-REF")] == ["kept.md"]


def test_config_exclude_and_guard_read_only_dirs(tmp_path):
    marker = "uses legacy-pipeline\n"
    project = make(tmp_path, {".socratex/config.json": '{"schema_version": 1, "project_check": {"exclude": ["generated/*"]}}',
                              ".ai/guard.json": '{"read_only_dirs": ["frozen/"]}',
                              "generated/g.md": marker, "frozen/f.md": marker, "live/l.md": marker})
    assert [h["file"] for h in found(project, "PRJ-LEGACY-REF")] == ["live/l.md"]


def test_config_schema_knows_project_check_exclude():
    schema = json.loads((CORE_DIR / "config.schema.json").read_text(encoding="utf-8"))
    assert core.validate({"schema_version": 1, "project_check": {"exclude": ["a/*"]}}, schema, "$") == []
    assert core.validate({"schema_version": 1, "project_check": {"other": 1}}, schema, "$")


def test_untracked_files_are_not_scanned_in_git_but_walk_without_git(tmp_path):
    project = make(tmp_path, {"a.md": "legacy-pipeline\n"})
    (project / "late.md").write_text("legacy-pipeline\n", encoding="utf-8")   # untracked
    assert [h["file"] for h in found(project, "PRJ-LEGACY-REF")] == ["a.md"]
    plain = make(tmp_path / "w", {"a.md": "legacy-pipeline\n", "node_modules/x.md": "legacy-pipeline\n"}, git=False)
    assert [h["file"] for h in found(plain, "PRJ-LEGACY-REF")] == ["a.md"]


def test_check_does_not_write_anything(tmp_path):
    project = make(tmp_path, {"SOCRATEX.md": "x"})
    before = sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if ".git" not in p.parts)
    project_check.run_check(project)
    assert before == sorted(p.relative_to(project).as_posix() for p in project.rglob("*") if ".git" not in p.parts)


# ---------- the sox commands ----------

def test_cli_exit_codes_and_output(tmp_path, capsys):
    clean = make(tmp_path)
    assert sox.main(["project", "check", str(clean)]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out
    warn = make(tmp_path / "w", {".ai/ROUTING.json": "{}"})
    assert sox.main(["project", "check", str(warn)]) == 0
    out = capsys.readouterr().out
    assert "PRJ-ROUTING-LEGACY .ai/ROUTING.json:1 (warning)" in out
    assert sox.main(["project", "check", str(warn), "--strict"]) == 1
    capsys.readouterr()
    bad = make(tmp_path / "e", {"SOCRATEX.md": "x"})
    assert sox.main(["project", "check", str(bad)]) == 1
    assert "PRJ-LEGACY-FILE SOCRATEX.md:1" in capsys.readouterr().out
    assert sox.main(["project", "check", str(tmp_path / "missing")]) == 2
    assert "not a directory" in capsys.readouterr().err
    with pytest.raises(SystemExit) as exc:
        sox.main(["project", "check"])
    assert exc.value.code == 2


def test_cli_json_output(tmp_path, capsys):
    project = make(tmp_path, {".ai/ROUTING.json": "{}", "SOCRATEX.md": "x"})
    assert sox.main(["project", "check", str(project), "--json"]) == 1
    data = json.loads(capsys.readouterr().out)
    assert data["counts"] == {"error": 1, "warning": 1} and data["exit"] == 1 and data["strict"] is False
    assert {f["rule"] for f in data["findings"]} == {"PRJ-LEGACY-FILE", "PRJ-ROUTING-LEGACY"}
    assert set(data["findings"][0]) == {"rule", "severity", "file", "line", "message"}


def test_explain(capsys):
    assert sox.main(["project", "explain", "PRJ-AGENTS-LONG"]) == 0
    out = capsys.readouterr().out
    assert "PRJ-AGENTS-LONG (error)" in out and "fix:" in out and "80" in out
    assert sox.main(["project", "explain", "PRJ-NOPE"]) == 2
    assert "PRJ-NO-CONFIG" in capsys.readouterr().err


def test_init_dry_run_write_and_idempotency(tmp_path, capsys):
    project = tmp_path / "new"
    project.mkdir()
    assert sox.main(["project", "init", str(project)]) == 0
    out = capsys.readouterr().out
    assert "would create .socratex/config.json" in out and "would create .ai/guard.json" in out
    assert list(project.iterdir()) == []                              # dry run writes nothing
    assert sox.main(["project", "init", str(project), "--write"]) == 0
    assert "created .socratex/config.json" in capsys.readouterr().out
    assert json.loads((project / ".socratex" / "config.json").read_text(encoding="utf-8")) == {"schema_version": 1}
    guard = json.loads((project / ".ai" / "guard.json").read_text(encoding="utf-8"))
    assert guard["big_files"] == [] and guard["read_only_dirs"] == [] and guard["blocked_commands"] == []
    allowed = project_check.load_rules()["rules"][-2]["known_keys"][".ai/guard.json"]
    assert {k for k in guard if not k.startswith("_")} <= set(allowed)
    (project / "AGENTS.md").write_text("mine\n", encoding="utf-8")
    first = {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}
    assert sox.main(["project", "init", str(project), "--write"]) == 0
    assert "created" not in capsys.readouterr().out
    assert first == {p.relative_to(project).as_posix(): p.read_bytes() for p in project.rglob("*") if p.is_file()}


def test_init_never_overwrites_an_existing_file(tmp_path, capsys):
    project = tmp_path / "p"
    (project / ".socratex").mkdir(parents=True)
    (project / ".socratex" / "config.json").write_text('{"schema_version": 1, "profile": "solo"}', encoding="utf-8")
    sox.main(["project", "init", str(project), "--write"])
    assert "skipped (exists) .socratex/config.json" in capsys.readouterr().out
    assert '"solo"' in (project / ".socratex" / "config.json").read_text(encoding="utf-8")


def test_init_output_passes_the_check(tmp_path):
    project = tmp_path / "fresh"
    project.mkdir()
    project_check.init_project(project, True)
    assert project_check.run_check(project) == []


def test_init_on_a_missing_folder_is_a_usage_error(tmp_path):
    assert sox.main(["project", "init", str(tmp_path / "nope")]) == 2
