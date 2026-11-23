"""Tests for the flow table, adapters, preference indexes and the initializer budget (core/core.py, core/sox)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "core"
sys.path.insert(0, str(CORE_DIR))

import core  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_flow", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_flow", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def step(sid: str, when: dict | None = None, then: list | None = None) -> dict:
    return {"id": sid, "when": when or {}, "then": ["ask"] if then is None else then, "why": "test"}


def flow_doc(*steps: dict) -> dict:
    return {"schema": "socratex-flow/v1", "steps": list(steps)}


def override(*, append=None, remove=None, delete=None) -> dict:
    ops = {k: v for k, v in (("$append", append), ("$remove", remove), ("$delete", delete)) if v is not None}
    return {"schema": "socratex-flow/v1", "steps": ops}


@pytest.fixture()
def repo(tmp_path):
    """A fake repo root where every kind of flow target exists."""
    root = tmp_path / "repo"
    (root / "modules" / "stages" / "review").mkdir(parents=True)
    (root / "claude" / "agents").mkdir(parents=True)
    (root / "claude" / "agents" / "scout.md").write_text("x", encoding="utf-8")
    (root / "defaults" / "rules").mkdir(parents=True)
    (root / "defaults" / "rules" / "A.md").write_text("x", encoding="utf-8")
    (root / "tools").mkdir()
    (root / "tools" / "t.py").write_text("x", encoding="utf-8")
    write(root / "defaults" / "flow.json", flow_doc(
        step("first", {}, ["stage:review"]),
        step("second", {"task_size": "big"}, ["role:scout", "rule:defaults/rules/A.md", "tool:tools/t.py", "gate:fast"]),
        step("third", {"touches": ["auth"]}, ["ask"])))
    project = tmp_path / "proj"
    project.mkdir()
    return root, project


def ids(root, project=None):
    return [s["id"] for s in core.load_flow(project, root)["steps"]]


# ---------- shipped flow ----------

def test_shipped_flow_is_valid_and_references_exist():
    assert core.check_flow() == []


def test_shipped_flow_covers_the_required_phases():
    present = {s["id"] for s in core.load_flow()["steps"]}
    required = {"session_start", "classify", "spec", "plan", "implement", "gate_fast", "review_stage",
                "review_independent", "escalate_to_high", "commit", "log"}
    assert required <= present


def test_shipped_flow_ids_unique_and_actions_cover_every_kind():
    steps = core.load_flow()["steps"]
    assert len({s["id"] for s in steps}) == len(steps)
    kinds = {a.partition(":")[0] for s in steps for a in s["then"]}
    assert kinds == {"ask", "stage", "role", "rule", "gate", "tool"}


# ---------- grammar and evaluation ----------

FACTS = core._flow_schema()["x-facts"]


@pytest.mark.parametrize("cond", [
    {}, {"task_size": "big"}, {"task_size": ["big", "medium"]}, {"task_size": {"not": "trivial"}},
    {"touches": ["auth"]}, {"unclear_requirements": True}, {"attempts_on_tier": {"gte": 2}},
    {"any": [{"risk": "full"}, {"all": [{"gate": "failed"}, {"not": {"tier": "top"}}]}]},
])
def test_valid_conditions(cond):
    assert core.check_condition(cond, FACTS) == []


@pytest.mark.parametrize("cond,text", [
    ({"nope": 1}, "unknown fact 'nope'"),
    ({"task_size": "huge"}, "'huge' is not one of"),
    ({"unclear_requirements": "yes"}, "true or false"),
    ({"attempts_on_tier": 2}, "gte"),
    ({"any": []}, "non-empty"),
    ({"touches": []}, "empty list"),
    ("always", "must be an object"),
])
def test_invalid_conditions(cond, text):
    errors = core.check_condition(cond, FACTS)
    assert errors and text in errors[0]


def test_matches_semantics():
    known = {"task_size": "big", "touches": ["auth", "data"], "attempts_on_tier": 2, "unclear_requirements": False}
    assert core.matches({}, known)
    assert core.matches({"task_size": ["big", "medium"]}, known)
    assert core.matches({"touches": "data"}, known)  # set fact: contains
    assert not core.matches({"touches": "saves"}, known)
    assert core.matches({"touches": {"not": "saves"}}, known)
    assert core.matches({"attempts_on_tier": {"gte": 2}}, known)
    assert not core.matches({"attempts_on_tier": {"lt": 2}}, known)
    assert core.matches({"unclear_requirements": False}, known)
    assert core.matches({"any": [{"task_size": "small"}, {"touches": "auth"}]}, known)
    assert not core.matches({"all": [{"task_size": "big"}, {"touches": "saves"}]}, known)
    assert core.matches({"not": {"task_size": "small"}}, known)


def test_unknown_fact_matches_nothing_but_not_is_true():
    assert not core.matches({"risk": "full"}, {})
    assert not core.matches({"attempts_on_tier": {"gte": 0}}, {})
    assert core.matches({"risk": {"not": "full"}}, {})


# ---------- flow check: broken references and grammar ----------

def test_check_clean_fake_repo(repo):
    root, project = repo
    assert core.check_flow(project, root) == []


def test_missing_stage_role_rule_tool_name_file_and_step(repo):
    root, project = repo
    path = write(root / "defaults" / "flow.json", flow_doc(
        step("a", {}, ["stage:nope"]), step("b", {}, ["role:ghost"]),
        step("c", {}, ["rule:defaults/rules/missing.md"]), step("d", {}, ["tool:tools/missing.py"]),
        step("e", {}, ["rule:project:docs/x.md"])))
    errors = core.check_flow(project, root)
    assert len(errors) == 4
    for sid, word in (("a", "stage 'nope'"), ("b", "role 'ghost'"), ("c", "rule path"), ("d", "tool path")):
        assert any(str(path) in e and f"step {sid}:" in e and word in e for e in errors)


def test_role_may_live_in_modules_routing_roles(repo):
    root, project = repo
    (root / "modules" / "routing" / "roles").mkdir(parents=True)
    (root / "modules" / "routing" / "roles" / "tester.md").write_text("x", encoding="utf-8")
    write(root / "defaults" / "flow.json", flow_doc(step("a", {}, ["role:tester"])))
    assert core.check_flow(project, root) == []


def test_grammar_errors_name_file_and_step(repo):
    root, project = repo
    path = write(root / "defaults" / "flow.json", flow_doc(
        step("a", {"bogus": 1}), step("b", {}, ["gate:slow"]), step("c", {}, ["run:thing"]),
        step("d", {}, []), step("a")))
    errors = core.check_flow(project, root)
    text = "\n".join(errors)
    assert all(str(path) in e for e in errors)
    for needle in ("step a: when: unknown fact 'bogus'", "step b: gate 'slow'", "step c: action 'run:thing'",
                   "step d: then is empty", "step a: duplicate id"):
        assert needle in text


def test_schema_errors_name_file_and_key(repo):
    root, project = repo
    path = write(root / "defaults" / "flow.json", {"schema": "socratex-flow/v1", "steps": [{"id": "x", "when": {}}]})
    errors = core.check_flow(project, root)
    assert any(str(path) in e and "then" in e for e in errors)


def test_missing_flow_file_is_an_error(repo):
    root, project = repo
    (root / "defaults" / "flow.json").unlink()
    assert "flow table is missing" in core.check_flow(project, root)[0]


def test_cli_flow_check_exit_codes(repo, capsys, monkeypatch):
    root, project = repo
    monkeypatch.setattr(core, "ROOT", root)
    assert sox.main(["flow", "check"]) == 0
    write(root / "defaults" / "flow.json", flow_doc(step("broken", {}, ["stage:nope"])))
    assert sox.main(["flow", "check"]) == 1
    err = capsys.readouterr().err
    assert "flow.json" in err and "step broken" in err


def test_cli_flow_show_and_match(repo, capsys, monkeypatch):
    root, project = repo
    monkeypatch.setattr(core, "ROOT", root)
    assert sox.main(["flow", "show"]) == 0
    out = capsys.readouterr().out
    assert [l.split()[1] for l in out.splitlines() if l[:3].strip().rstrip(".").isdigit()] == ["first", "second", "third"]
    assert sox.main(["flow", "show", "--match", "task_size=small"]) == 0
    out = capsys.readouterr().out
    assert "first" in out and "second" not in out
    assert sox.main(["flow", "show", "--match", "task_size=big", "touches=auth,data", "--json"]) == 0
    assert [s["id"] for s in json.loads(capsys.readouterr().out)["steps"]] == ["first", "second", "third"]


# ---------- flow layers (override by step id) ----------

def test_layer_files(repo):
    root, project = repo
    got = core.flow_layers(project, root)
    assert [l["name"] for l in got] == ["core", "local", "project", "project-private"]
    assert got[2]["path"] == project.resolve() / ".socratex" / "flow.json"
    assert [l["name"] for l in core.flow_layers(None, root)] == ["core", "local"]


def test_remove_ignores_missing_and_delete_is_strict(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json", override(remove=["second", "ghost"]))
    assert ids(root) == ["first", "third"]
    write(root / "local" / "overrides" / "flow.json", override(delete=["ghost"]))
    with pytest.raises(core.FlowError, match="step ghost: \\$delete"):
        core.load_flow(None, root)
    write(root / "local" / "overrides" / "flow.json", override(delete=["third"]))
    assert ids(root) == ["first", "second"]


def test_append_default_end_and_before_after(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json", override(append=[
        step("end"), {**step("pre"), "before": "second"}, {**step("post"), "after": "second"}]))
    assert ids(root) == ["first", "pre", "second", "post", "third", "end"]


def test_append_existing_id_and_unknown_anchor_are_errors(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json", override(append=[step("first")]))
    with pytest.raises(core.FlowError, match="step first: id already exists"):
        core.load_flow(None, root)
    write(root / "local" / "overrides" / "flow.json", override(append=[{**step("n"), "after": "ghost"}]))
    with pytest.raises(core.FlowError, match="step n: before/after names unknown step 'ghost'"):
        core.load_flow(None, root)


def test_remove_plus_append_replaces_a_step(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json",
          override(remove=["second"], append=[{**step("second", {"task_size": "small"}, ["ask"]), "after": "first"}]))
    flow = core.load_flow(None, root)
    assert [s["id"] for s in flow["steps"]] == ["first", "second", "third"]
    assert flow["steps"][1]["when"] == {"task_size": "small"}
    assert flow["origin"]["second"]["layer"] == "local" and flow["origin"]["first"]["layer"] == "core"


def test_layers_apply_low_to_high_and_later_layer_sees_earlier_steps(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json", override(append=[step("from_local")]))
    write(project / ".socratex" / "flow.json", override(remove=["from_local"], append=[step("from_project")]))
    write(root / "local" / "projects" / project.name / "flow.json", override(remove=["first"], append=[{**step("private"), "before": "second"}]))
    flow = core.load_flow(project, root)
    assert [s["id"] for s in flow["steps"]] == ["private", "second", "third", "from_project"]
    assert {i: o["layer"] for i, o in flow["origin"].items()} == {
        "private": "project-private", "second": "core", "third": "core", "from_project": "project"}


def test_override_with_broken_step_names_file_and_step(repo):
    root, project = repo
    path = write(project / ".socratex" / "flow.json", override(append=[step("bad", {"task_size": "huge"}, ["ask"])]))
    errors = core.check_flow(project, root)
    assert any(str(path) in e and "step bad" in e for e in errors)


def test_override_top_level_typo_is_an_error(repo):
    root, project = repo
    write(root / "local" / "overrides" / "flow.json", {"schema": "socratex-flow/v1", "step": {}})
    with pytest.raises(core.FlowError, match="unknown key 'step'"):
        core.load_flow(None, root)


def test_override_reference_to_missing_stage_is_reported_with_its_file(repo):
    root, project = repo
    path = write(project / ".socratex" / "flow.json", override(append=[step("x", {}, ["stage:ghost"])]))
    errors = core.check_flow(project, root)
    assert len(errors) == 1 and str(path) in errors[0] and "step x" in errors[0]


# ---------- adapters ----------

@pytest.fixture()
def shipped(tmp_path):
    """A copy of the shipped defaults as a repo root, plus a project folder."""
    root = tmp_path / "repo"
    shutil.copytree(REPO / "defaults", root / "defaults")
    project = tmp_path / "proj"
    project.mkdir()
    return root, project


def set_adapter(project, name):
    write(project / ".socratex" / "config.json", {"schema_version": 1, "adapter": name})


def flat(values: dict, prefix: str = "") -> dict:
    out = {}
    for key, value in values.items():
        path = f"{prefix}.{key}" if prefix else key
        out.update(flat(value, path) if isinstance(value, dict) else {path: value})
    return out


def test_layer_order_has_adapter_between_defaults_and_local(shipped):
    root, project = shipped
    names = [l["name"] for l in core.layers(project, root)]
    # three preference indexes and defaults/config.json are all "defaults", then the adapter, then the owner layers
    assert names == ["defaults"] * 4 + ["adapter", "local", "project", "project-private"]


def test_adapter_layer_is_below_local_and_above_defaults(shipped):
    root, project = shipped
    assert core.resolve(project, root)["values"]["codex"]["enabled"] is True  # duo from defaults
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "codex": {"enabled": False}})
    result = core.resolve(project, root)
    assert result["values"]["codex"]["enabled"] is False
    prov = result["provenance"]["codex.enabled"]
    assert prov["layer"] == "local" and [o["layer"] for o in prov["overridden"]] == ["adapter"]


def test_adapter_choice_follows_the_highest_layer(shipped):
    root, project = shipped
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "adapter": "solo"})
    assert core.resolve(None, root)["values"]["codex"]["enabled"] is False
    set_adapter(project, "duo")
    assert core.resolve(project, root)["values"]["codex"]["enabled"] is True


def test_switching_solo_duo_changes_only_codex_keys(shipped):
    root, project = shipped
    set_adapter(project, "solo")
    solo = flat(core.resolve(project, root)["values"])
    set_adapter(project, "duo")
    duo = flat(core.resolve(project, root)["values"])
    changed = {k for k in solo.keys() | duo.keys() if solo.get(k) != duo.get(k)}
    assert changed == {"codex.enabled", "codex.review", "codex.delegate"} | {"adapter"}
    assert {k for k in changed if not k.startswith("codex.")} == {"adapter"}
    assert solo["codex.enabled"] is False and duo["codex.enabled"] is True


def test_config_show_adapter_switch_changes_only_codex_rows(shipped, capsys, monkeypatch):
    root, project = shipped
    monkeypatch.setattr(core, "ROOT", root)
    original = core.layers
    monkeypatch.setattr(core, "layers", lambda project_root=None, root_=None: original(project_root, root))
    rows = {}
    for name in ("solo", "duo"):
        set_adapter(project, name)
        assert sox.main(["config", "show", "--project", str(project), "--json"]) == 0
        rows[name] = flat(json.loads(capsys.readouterr().out)["values"])
    assert {k for k in rows["solo"] if rows["solo"][k] != rows["duo"][k]} == {
        "adapter", "codex.enabled", "codex.review", "codex.delegate"}


def test_yolo_adds_only_safety_allow_on_top_of_duo(shipped):
    root, project = shipped
    set_adapter(project, "duo")
    duo = flat(core.resolve(project, root)["values"])
    (project / ".socratex" / "config.json").unlink()
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "adapter": "yolo"})  # only an owner layer may pick it
    yolo = flat(core.resolve(project, root)["values"])
    assert {k for k in yolo.keys() | duo.keys() if yolo.get(k) != duo.get(k)} == {"adapter", "safety.allow"}


def test_missing_adapter_file_is_an_error(shipped):
    root, project = shipped
    (root / "defaults" / "adapters" / "duo.json").unlink()
    with pytest.raises(core.ConfigError, match="duo.json.*no file"):
        core.resolve(project, root)


def test_bad_adapter_value_reports_the_enum_not_a_missing_file(shipped):
    root, project = shipped
    set_adapter(project, "turbo")
    with pytest.raises(core.ConfigError, match="turbo.*not one of"):
        core.resolve(project, root)


def test_adapter_file_typo_and_directive_are_errors(shipped):
    root, project = shipped
    path = root / "defaults" / "adapters" / "duo.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["config"]["codex"]["enable"] = True
    write(path, data)
    with pytest.raises(core.ConfigError, match="codex.enable"):
        core.resolve(project, root)
    data["config"] = {"codex": {"enabled": {"$delete": True}}}
    write(path, data)
    with pytest.raises(core.ConfigError, match="codex.enabled"):
        core.resolve(project, root)


def test_shipped_adapters_are_valid_and_named_after_their_file():
    for name in ("solo", "duo", "yolo"):
        path = REPO / "defaults" / "adapters" / f"{name}.json"
        assert json.loads(path.read_text(encoding="utf-8"))["name"] == name
        assert core.load_adapter_file(path)["codex"]["enabled"] is (name != "solo")


# ---------- preferences ----------

def test_preference_indexes_point_to_existing_documents():
    for name in ("code", "commits", "communication"):
        path = REPO / "defaults" / "preferences" / name / f"{name}.json"
        layer = core.load_preferences_file(path)["preferences"][name]
        assert layer["load_when"] and layer["files"]
        assert all((REPO / f).is_file() for f in layer["files"])


def test_preferences_are_layered_config_with_provenance(shipped):
    root, project = shipped
    prefs = core.resolve(project, root)["values"]["preferences"]
    assert prefs["code"]["files"] == ["defaults/rules/CODE-STYLE.md"]
    assert prefs["commits"]["files"] == ["defaults/rules/COMMITS.md"]
    assert prefs["communication"]["files"] == ["defaults/STYLE.md"]
    write(project / ".socratex" / "config.json",
          {"schema_version": 1, "preferences": {"code": {"files": {"$append": ["docs/PROJECT-STYLE.md"]}}}})
    write(root / "local" / "overrides" / "config.json",
          {"schema_version": 1, "preferences": {"communication": {"files": {"$remove": ["defaults/STYLE.md"]}}}})
    result = core.resolve(project, root)
    assert result["values"]["preferences"]["code"]["files"] == ["defaults/rules/CODE-STYLE.md", "docs/PROJECT-STYLE.md"]
    assert result["values"]["preferences"]["communication"]["files"] == []
    prov = result["provenance"]["preferences.code.files"]
    assert prov["layer"] == "project" and prov["overridden"][0]["layer"] == "defaults"
    assert result["provenance"]["preferences.code.load_when"]["file"].endswith("code.json")


def test_preference_typo_names_file_and_key(shipped):
    root, project = shipped
    path = root / "defaults" / "preferences" / "code" / "code.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    del data["load_when"]
    write(path, data)
    with pytest.raises(core.ConfigError, match="code.json.*load_when"):
        core.resolve(project, root)


# ---------- initializer budget (criterion 7) ----------

def test_init_md_is_small_and_has_frontmatter():
    text = (CORE_DIR / "INIT.md").read_text(encoding="utf-8")
    assert text.startswith("---\n") and "\ntype: init\n" in text
    assert len(text.splitlines()) <= 35
    assert (CORE_DIR / "INIT.md").stat().st_size <= core.INIT_MAX_BYTES


def test_init_budget_includes_enabled_extension_summaries():
    assert core.init_size() <= core.INIT_TOTAL_MAX_BYTES


def test_init_size_counts_one_line_per_enabled_extension(tmp_path):
    root = tmp_path / "repo"
    (root / "core").mkdir(parents=True)
    (root / "core" / "INIT.md").write_text("x" * 100, encoding="utf-8")
    write(root / "defaults" / "config.json", {"schema_version": 1, "extensions": ["alpha", "beta"]})
    write(root / "modules" / "extensions" / "alpha.json", ext_manifest("alpha", "when A"))
    write(root / "modules" / "extensions" / "beta.json", ext_manifest("beta", "when B"))
    values = {"extensions": ["alpha", "beta", "alpha"]}
    assert core.extension_summaries(values, root) == ["alpha: when A", "beta: when B"]
    assert core.extension_block(values, root) == [core.EXTENSION_HEADER, "alpha: when A", "beta: when B"]
    lines = [core.EXTENSION_HEADER, "alpha: when A", "beta: when B"]
    assert core.init_size(None, root) == 100 + sum(len(line) + 1 for line in lines)


def test_extension_summaries_keep_a_bare_name_without_manifest(tmp_path):
    assert core.extension_summaries({"extensions": ["ghost"]}, tmp_path) == ["ghost"]


def ext_manifest(name: str, when: str) -> dict:
    return {"schema": "socratex-extension/v1", "name": name, "kind": "note", "category": "c", "source": {"id": name, "version": "1"},
            "when_to_use": when, "status": "adopted", "default_enabled": False,
            "context_cost": {"level": "none", "note": "n"}, "risks": "r"}


def test_commits_preference_can_be_overridden_by_the_project(shipped):
    root, project = shipped
    write(project / ".socratex" / "config.json",
          {"schema_version": 1, "preferences": {"commits": {"files": ["docs/OUR-COMMITS.md"]}}})
    result = core.resolve(project, root)
    assert result["values"]["preferences"]["commits"]["files"] == ["docs/OUR-COMMITS.md"]
    assert result["provenance"]["preferences.commits.files"]["layer"] == "project"
    assert result["values"]["preferences"]["commits"]["load_when"]


# ---------- legacy `profile` key ----------

def test_legacy_profile_key_is_an_alias_for_adapter_with_a_warning(shipped, capsys):
    root, project = shipped
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "profile": "solo"})
    result = core.resolve(project, root)
    assert result["values"]["adapter"] == "solo" and "profile" not in result["values"]
    assert result["provenance"]["adapter"]["layer"] == "local"
    assert "`profile` was renamed to `adapter`" in capsys.readouterr().err
