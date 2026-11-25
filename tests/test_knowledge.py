"""Tests for the project knowledge hub: group layer, project.json, `sox context`, `sox project init|list|show|check|adopt`.

Every test works in a temp copy of the layout; nothing touches the real local/ folder (a clean clone has none)."""

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
import knowledge  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_knowledge", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_knowledge", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(data if isinstance(data, str) else json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture()
def root(tmp_path):
    """A fake SocratexAI checkout with defaults and templates but no local/ at all (a clean clone)."""
    base = tmp_path / "sox"
    write(base / "defaults" / "config.json", {"schema_version": 1, "adapter": "duo", "codex": {"review": False}})
    for name in ("solo", "duo", "yolo"):
        write(base / "defaults" / "adapters" / f"{name}.json", {"schema": "socratex-profile/v1", "schema_version": 1, "name": name,
                                                              "what": name, "config": {"codex": {"enabled": True}}})
    shutil.copytree(REPO / "templates", base / "templates")
    for rel in ("defaults/RULES.md", "defaults/STYLE.md", "defaults/DIRECTIVES.json"):
        write(base / rel, "x\n")
    return base


def repo(tmp_path: Path, name: str = "app", parent: str = "r") -> Path:
    path = tmp_path / parent / name
    path.mkdir(parents=True)
    return path


def pj(root: Path, key: str, **data) -> Path:
    return write(root / "local" / "projects" / key / "project.json", {"schema_version": 1, "name": key, **data})


def files(result: dict) -> list[str]:
    return [Path(r["file"]).name for r in result["rows"]]


# ---------- resolver: group layer ----------

def test_group_layer_sits_between_local_and_project_and_shows_source_group(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", group="g")
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "codex": {"review": True, "delegate": True}})
    write(root / "local" / "groups" / "g" / "config.json", {"schema_version": 1, "codex": {"review": False, "enabled": False}})
    write(project / ".socratex" / "config.json", {"schema_version": 1, "codex": {"enabled": True}})
    prov = core.resolve(project, root)["provenance"]
    assert prov["codex.delegate"]["layer"] == "local"
    assert prov["codex.review"]["layer"] == "group" and prov["codex.review"]["overridden"][-1]["layer"] == "local"
    assert prov["codex.enabled"]["layer"] == "project" and prov["codex.enabled"]["overridden"][-1]["layer"] == "group"
    names = [layer["name"] for layer in core.layers(project, root) if layer["kind"] == "config"]
    assert names == ["defaults", "local", "group", "project", "project-private"]


def test_no_group_means_no_group_layer(root, tmp_path):
    project = repo(tmp_path)
    assert "group" not in [layer["name"] for layer in core.layers(project, root)]


@pytest.mark.parametrize("which", ["project", "group"])
def test_unknown_key_in_project_or_group_json_names_file_and_key(root, tmp_path, which):
    project = repo(tmp_path)
    pj(root, "app", group="g", **({"bogus": 1} if which == "project" else {}))
    write(root / "local" / "groups" / "g" / "group.json", {"schema_version": 1, "name": "g", **({"bogus": 1} if which == "group" else {})})
    with pytest.raises(core.ConfigError) as exc:
        core.resolve(project, root)
    assert f"{which}.json" in str(exc.value) and "unknown key 'bogus'" in str(exc.value)


def test_bad_knowledge_mode_is_an_error(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", knowledge={"mode": "cloud"})
    with pytest.raises(core.ConfigError, match="project.json.*cloud"):
        core.resolve(project, root)


def test_project_private_layer_follows_the_bound_key(root, tmp_path):
    project = repo(tmp_path, "superplan", "proj-a")
    pj(root, "proj-b-superplan", path=str(project))
    write(root / "local" / "projects" / "proj-b-superplan" / "config.json", {"schema_version": 1, "codex": {"delegate": True}})
    assert core.resolve(project, root)["provenance"]["codex.delegate"]["layer"] == "project-private"


# ---------- sox context ----------

def test_context_without_project_lists_only_global_layers(root):
    result = knowledge.build_context(None, root)
    assert {r["layer"] for r in result["rows"]} <= {"socratex", "preference", "global"}
    assert result["errors"] == [] and result["project"]["key"] is None


def test_context_project_without_project_json_says_so(root, tmp_path):
    result = knowledge.build_context(str(repo(tmp_path)), root)
    last = result["rows"][-1]
    assert last["layer"] == "project" and not last["exists"] and "no project knowledge" in last["why"]
    assert result["errors"] == []


def test_context_order_general_to_specific(root, tmp_path):
    project = repo(tmp_path)
    write(project / "AGENTS.md", "x")
    pj(root, "app", group="g")
    (root / "local" / "profile.md").write_text("p", encoding="utf-8")
    write(root / "local" / "groups" / "g" / "GROUP.md", "g")
    write(root / "local" / "groups" / "g" / "rules" / "a.md", "r")
    write(root / "local" / "projects" / "app" / "rules" / "b.md", "r")
    result = knowledge.build_context(str(project), root)
    layers = [r["layer"] for r in result["rows"]]
    order = ["socratex", "preference", "global", "group", "project-repo", "project"]
    assert layers == sorted(layers, key=order.index)
    project_rows = [Path(r["file"]).name for r in result["rows"] if r["layer"] == "project"]
    assert project_rows == ["project.json", "PROJECT.md", "DOMAIN.md", "b.md", "DEVIATIONS.md"]
    assert [Path(r["file"]).name for r in result["rows"] if r["layer"] == "group"] == ["GROUP.md", "a.md"]
    assert files(result)[-1] == "DEVIATIONS.md"
    assert all({"layer", "file", "why", "exists"} <= set(r) for r in result["rows"])


def test_context_modes_repo_and_external_show_the_reference(root, tmp_path):
    project = repo(tmp_path)
    kdir = project / "docs" / "ai"
    write(kdir / "PROJECT.md", "p")
    pj(root, "app", knowledge={"mode": "repo", "path": "docs/ai"})
    result = knowledge.build_context(str(project), root)
    ref = next(r for r in result["rows"] if r["file"].endswith("project.json"))
    assert str(kdir) in ref["why"] and "mode repo" in ref["why"]
    assert next(r for r in result["rows"] if r["file"] == str(kdir / "PROJECT.md"))["exists"]
    assert result["errors"] == []
    external = tmp_path / "elsewhere"
    write(external / "PROJECT.md", "p")
    pj(root, "app", knowledge={"mode": "external", "path": str(external)})
    again = knowledge.build_context(str(project), root)
    assert str(external) in next(r for r in again["rows"] if r["file"].endswith("project.json"))["why"]
    assert str(external / "DEVIATIONS.md") in [r["file"] for r in again["rows"]]


def test_context_missing_knowledge_path_errors_but_still_lists(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", knowledge={"mode": "external", "path": str(tmp_path / "gone")})
    result = knowledge.build_context(str(project), root)
    assert any("app" in e and "gone" in e for e in result["errors"])
    assert result["rows"][-1]["exists"] is False and files(result)[-1] == "DEVIATIONS.md"


def test_context_external_needs_absolute_path_and_repo_needs_a_path(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", knowledge={"mode": "external", "path": "relative/dir"})
    assert any("absolute" in e for e in knowledge.build_context(str(project), root)["errors"])
    pj(root, "app", knowledge={"mode": "repo"})
    assert any("needs knowledge.path" in e for e in knowledge.build_context(str(project), root)["errors"])


def test_context_accepts_a_project_key_instead_of_a_folder(root):
    pj(root, "app", summary="s")
    result = knowledge.build_context("app", root)
    assert result["project"]["key"] == "app" and "PROJECT.md" in files(result)


def test_context_cli_json_and_exit_code(root, tmp_path, capsys):
    project = repo(tmp_path)
    assert sox.main(["context", "--project", str(project), "--json", "--root", str(root)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["rows"] and data["errors"] == []
    pj(root, "app", knowledge={"mode": "external", "path": str(tmp_path / "gone")})
    assert sox.main(["context", "--project", str(project), "--root", str(root)]) == 1
    captured = capsys.readouterr()
    assert "(missing)" in captured.out and "gone" in captured.err


def test_preference_files_relative_to_socratex_root_and_project_prefix(root, tmp_path):
    project = repo(tmp_path)
    write(project / ".socratex" / "config.json", {"schema_version": 1, "preferences": {"mine": {
        "load_when": "always", "files": ["project:docs/style.md", "defaults/RULES.md"]}}})
    rows = knowledge.build_context(str(project), root)["rows"]
    mine = [r for r in rows if "preference mine" in r["why"]]
    assert [r["file"] for r in mine] == [str(project / "docs" / "style.md")]          # RULES.md already listed, not repeated
    assert sum(r["file"].endswith("RULES.md") for r in rows) == 1


# ---------- key resolution and collisions ----------

def test_same_folder_name_bound_to_another_path_is_an_error_with_both_paths(root, tmp_path):
    first, second = repo(tmp_path, "superplan", "a"), repo(tmp_path, "superplan", "b")
    pj(root, "superplan", path=str(first))
    assert knowledge.project_key(first, root) == "superplan"
    with pytest.raises(core.ConfigError) as exc:
        knowledge.project_key(second, root)
    assert str(first) in str(exc.value) and str(second) in str(exc.value)
    pj(root, "b-superplan", path=str(second))
    assert knowledge.project_key(second, root) == "b-superplan"


def test_two_projects_claiming_one_path_is_an_error(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "one", path=str(project))
    pj(root, "two", path=str(project))
    with pytest.raises(core.ConfigError, match="one, two"):
        knowledge.project_key(project, root)


# ---------- sox project init / list / show / check ----------

def test_clean_clone_flow_init_context_check(root, tmp_path, capsys):
    assert not (root / "local").exists()
    project = repo(tmp_path)
    assert sox.main(["project", "check", "--root", str(root)]) == 0                         # no local/: empty hub is fine
    assert sox.main(["project", "init", str(project), "--root", str(root), "--group", "g", "--prefix", "APP", "--summary", "demo"]) == 0
    assert not (root / "local").exists() and not (project / ".socratex").exists()          # dry run writes nothing
    write(root / "local" / "groups" / "g" / "group.json", {"schema_version": 1, "name": "g"})
    assert sox.main(["project", "init", str(project), "--root", str(root), "--write", "--group", "g", "--prefix", "APP", "--summary", "demo"]) == 0
    pdir = root / "local" / "projects" / "app"
    for name in ("project.json", "PROJECT.md", "DOMAIN.md", "DEVIATIONS.md", "rules/README.md"):
        assert (pdir / name).is_file(), name
    assert not (pdir / "config.json").exists()
    data = knowledge.load_project_json(pdir / "project.json")
    assert data["group"] == "g" and data["ticket_prefixes"] == ["APP"] and data["path"] == str(project.resolve())
    assert "{{" not in (pdir / "DEVIATIONS.md").read_text(encoding="utf-8")
    capsys.readouterr()
    assert sox.main(["context", "--project", str(project), "--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert out.index("GROUP.md") < out.index("PROJECT.md") < out.index("DEVIATIONS.md")
    assert sox.main(["project", "check", "--root", str(root)]) == 0
    assert sox.main(["project", "check", str(project), "--root", str(root), "--strict"]) == 0   # repo files and knowledge both pass
    assert (project / ".socratex" / "config.json").is_file()


def test_init_is_idempotent_and_never_overwrites(root, tmp_path):
    project = repo(tmp_path)
    knowledge.init_knowledge(project, True, root)
    write(root / "local" / "projects" / "app" / "PROJECT.md", "mine\n")
    lines = knowledge.init_knowledge(project, True, root)
    assert all(line.startswith("skipped") for line in lines)
    assert (root / "local" / "projects" / "app" / "PROJECT.md").read_text(encoding="utf-8") == "mine\n"


def test_init_refuses_a_key_bound_to_another_repo(root, tmp_path):
    first, second = repo(tmp_path, "superplan", "a"), repo(tmp_path, "superplan", "b")
    knowledge.init_knowledge(first, True, root)
    with pytest.raises(core.ConfigError, match="already bound"):
        knowledge.init_knowledge(second, True, root)
    knowledge.init_knowledge(second, True, root, name="b-superplan")
    assert knowledge.project_key(second, root) == "b-superplan"


def test_list_and_show(root, tmp_path, capsys):
    project = repo(tmp_path)
    pj(root, "app", group="g", summary="the app", knowledge={"mode": "repo", "path": "docs"})
    write(root / "local" / "projects" / "app" / "config.json", {"schema_version": 1, "codex": {"review": True}})
    write(root / "local" / "projects" / "app" / "DEVIATIONS.md", "# d\n- codex review on, because reasons\n")
    rows = knowledge.list_rows(root)
    assert rows == [{"project": "app", "group": "g", "mode": "repo", "overrides": ["codex.review"], "summary": "the app", "error": None}]
    assert sox.main(["project", "list", "--root", str(root)]) == 0
    out = capsys.readouterr().out
    assert "app" in out and "codex.review" in out and "the app" in out
    assert sox.main(["project", "show", "app", "--root", str(root)]) == 0
    shown = capsys.readouterr().out
    assert "codex.review = true" in shown and "relative but the repo folder is unknown" in shown   # repo mode needs the repo path
    pj(root, "app", summary="the app")
    assert sox.main(["project", "show", "app", "--root", str(root)]) == 0
    assert "codex review on, because reasons" in capsys.readouterr().out
    assert sox.main(["project", "show", "nope", "--root", str(root)]) == 2


def test_check_findings(root, tmp_path):
    pj(root, "app", group="missing-group", ticket_prefixes=["APP"], knowledge={"mode": "external", "path": str(tmp_path / "gone")})
    pj(root, "other", ticket_prefixes=["APP"])
    write(root / "local" / "projects" / "bad" / "project.json", {"schema_version": 1, "name": "bad", "oops": 1})
    pj(root, "renamed").write_text(json.dumps({"schema_version": 1, "name": "different"}), encoding="utf-8")
    (root / "local" / "tickets" / "ZZZ" / "ZZZ-1").mkdir(parents=True)
    (root / "local" / "tickets" / "_slugs").mkdir()
    codes = {(f["code"], Path(f["file"]).parent.name if f["code"] != "K-ORPHAN-PREFIX" else Path(f["file"]).name)
             for f in knowledge.check_knowledge(root)}
    assert ("K-GROUP", "missing-group") in codes
    assert any(code == "K-KNOWLEDGE-PATH" for code, _ in codes)
    assert ("K-PREFIX-DUP", "local") in codes
    assert ("K-PROJECT-JSON", "bad") in codes
    assert ("K-NAME", "renamed") in codes
    assert ("K-ORPHAN-PREFIX", "ZZZ") in codes
    assert not any(c == "K-ORPHAN-PREFIX" and n == "_slugs" for c, n in codes)


def test_check_reports_folder_name_collision_with_both_paths(root, tmp_path):
    first, second = repo(tmp_path, "superplan", "a"), repo(tmp_path, "superplan", "b")
    pj(root, "superplan", path=str(first))
    pj(root, "b-superplan", path=str(second))
    hits = [f for f in knowledge.check_knowledge(root) if f["code"] == "K-COLLISION"]
    assert len(hits) == 1 and str(first) in hits[0]["message"] and str(second) in hits[0]["message"]


def test_check_with_a_repo_path_reports_a_collision_error(root, tmp_path, capsys):
    first, second = repo(tmp_path, "superplan", "a"), repo(tmp_path, "superplan", "b")
    pj(root, "superplan", path=str(first))
    assert sox.main(["project", "check", str(second), "--root", str(root)]) == 1
    assert "K-COLLISION" in capsys.readouterr().out


def test_orphan_prefix_is_a_warning_not_a_failure(root, capsys):
    (root / "local" / "tickets" / "ZZZ").mkdir(parents=True)
    assert sox.main(["project", "check", "--root", str(root)]) == 0
    assert "K-ORPHAN-PREFIX" in capsys.readouterr().out
    assert sox.main(["project", "check", "--root", str(root), "--strict"]) == 1


# ---------- sox project adopt ----------

def old_knowledge(tmp_path: Path) -> Path:
    src = tmp_path / "old"
    write(src / "PROJECT.md", "p\n")
    write(src / "notes" / "a.md", "a\n")
    write(src / "legacy" / "x.md", "x\n")
    return src


def test_adopt_plan_writes_nothing_without_yes(root, tmp_path, capsys):
    src = old_knowledge(tmp_path)
    assert sox.main(["project", "adopt", str(src), "--project", "app", "--root", str(root)]) == 0
    assert "Plan only" in capsys.readouterr().out
    assert not (root / "local").exists()


def test_adopt_yes_copies_keeps_conflicts_and_never_deletes(root, tmp_path, capsys):
    src = old_knowledge(tmp_path)
    dest = root / "local" / "projects" / "app"
    write(dest / "PROJECT.md", "different\n")
    write(dest / "keep.md", "untouched\n")
    assert sox.main(["project", "adopt", str(src), "--project", "app", "--root", str(root), "--exclude", "legacy/*", "--yes"]) == 0
    out = capsys.readouterr().out
    assert "1 to copy" in out and "1 conflict" in out
    assert (dest / "notes" / "a.md").read_text(encoding="utf-8") == "a\n"
    assert (dest / "PROJECT.md").read_text(encoding="utf-8") == "different\n"            # conflict kept
    assert (dest / "keep.md").exists() and not (dest / "legacy").exists()
    assert (src / "PROJECT.md").exists()                                                  # the source is never touched
    assert sox.main(["project", "adopt", str(src), "--project", "app", "--root", str(root), "--exclude", "legacy/*", "--yes"]) == 0
    assert "0 to copy, 1 already identical" in capsys.readouterr().out


def test_adopt_include_filter_and_bad_source(root, tmp_path, capsys):
    src = old_knowledge(tmp_path)
    rows = knowledge.adopt_plan(src, "app", root, ["notes/*"], [])
    assert [Path(r["src"]).name for r in rows] == ["a.md"]
    assert sox.main(["project", "adopt", str(tmp_path / "nope"), "--project", "app", "--root", str(root)]) == 2


# ---------- the shipped data ----------

def test_schemas_and_templates_are_shipped():
    for name in ("project.schema.json", "group.schema.json"):
        assert json.loads((CORE_DIR / name).read_text(encoding="utf-8"))["additionalProperties"] is False
    for name in ("PROJECT.md", "DOMAIN.md", "DEVIATIONS.md", "rules/README.md"):
        assert (REPO / "templates" / "knowledge" / name).is_file()


def test_init_md_points_to_sox_context():
    text = (CORE_DIR / "INIT.md").read_text(encoding="utf-8")
    assert "sox context" in text and text.index("sox context") < text.index("sox flow show")


# ---------- group inheritance (extends) and conditional rule files ----------

def gj(root: Path, name: str, **data) -> Path:
    return write(root / "local" / "groups" / name / "group.json", {"schema_version": 1, "name": name, **data})


def test_group_extends_applies_base_first_then_group(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", group="child")
    gj(root, "base")
    gj(root, "child", extends=["base"])
    write(root / "local" / "groups" / "base" / "config.json", {"schema_version": 1, "codex": {"review": True, "delegate": True}})
    write(root / "local" / "groups" / "child" / "config.json", {"schema_version": 1, "codex": {"review": False}})
    values = core.resolve(project, root)
    assert values["values"]["codex"]["review"] is False and values["values"]["codex"]["delegate"] is True
    names = [layer["name"] for layer in core.layers(project, root) if layer["kind"] == "config"]
    assert names == ["defaults", "local", "group", "group", "project", "project-private"]
    write(root / "local" / "groups" / "base" / "GROUP.md", "b")
    write(root / "local" / "groups" / "base" / "rules" / "r.md", "r")
    write(root / "local" / "groups" / "child" / "GROUP.md", "c")
    rows = [(Path(r["file"]).parent.name, Path(r["file"]).name) for r in knowledge.build_context(str(project), root)["rows"] if r["layer"] == "group"]
    assert rows == [("base", "GROUP.md"), ("rules", "r.md"), ("child", "GROUP.md")]


def test_group_extends_diamond_lists_each_base_once(root):
    gj(root, "a")
    gj(root, "b", extends=["a"])
    gj(root, "c", extends=["a"])
    gj(root, "d", extends=["b", "c"])
    assert knowledge.group_chain("d", root) == ["a", "b", "c", "d"]


def test_group_extends_cycle_and_unknown_are_errors_naming_file_and_key(root):
    gj(root, "x", extends=["y"])
    gj(root, "y", extends=["x"])
    with pytest.raises(core.ConfigError, match=r"group\.json.*'extends'.*cycle"):
        knowledge.group_chain("x", root)
    gj(root, "z", extends=["nope"])
    with pytest.raises(core.ConfigError, match=r"z[/\\]group\.json.*'extends'.*unknown group 'nope'"):
        knowledge.group_chain("z", root)


def test_context_cycle_is_reported_not_raised(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", group="x")
    gj(root, "x", extends=["y"])
    gj(root, "y", extends=["x"])
    assert any("cycle" in e for e in knowledge.build_context(str(project), root)["errors"])


def test_rules_with_load_when_are_listed_conditionally(root, tmp_path):
    project = repo(tmp_path)
    pj(root, "app", group="g", rules=[{"file": "own.md", "load_when": "touching the cart"}])
    gj(root, "g", rules=[{"file": "inspect.md", "load_when": "reviewing PHP"}])
    for rel in ("groups/g/rules/inspect.md", "groups/g/rules/plain.md", "projects/app/rules/own.md", "projects/app/rules/p.md"):
        write(root / "local" / rel, "x")
    rows = {Path(r["file"]).name: r for r in knowledge.build_context(str(project), root)["rows"]}
    assert rows["inspect.md"]["load_when"] == "reviewing PHP" and "conditional" in rows["inspect.md"]["why"]
    assert rows["own.md"]["load_when"] == "touching the cart"
    assert "load_when" not in rows["plain.md"] and "load_when" not in rows["p.md"]
    assert any("[load when: reviewing PHP]" in line for line in knowledge.format_context({"rows": list(rows.values())}))
