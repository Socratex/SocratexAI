"""Tests for the extension registry (core/extensions.py, `sox ext`): manifests, layers, add, enable, install, startup budget."""

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
sys.path.insert(0, str(REPO / "modules" / "tools" / "scripts"))

import core  # noqa: E402
import extensions  # noqa: E402
import install  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_ext", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_ext", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def manifest(name: str, kind: str = "note", **over: object) -> dict:
    data: dict = {"schema": "socratex-extension/v1", "name": name, "kind": kind, "category": "code",
                  "source": {"id": name, "version": "1"}, "when_to_use": f"use {name} when needed", "status": "adopted",
                  "default_enabled": False, "context_cost": {"level": "none", "note": "n"}, "risks": "r"}
    if kind == "ref":
        data["source"] = {"url": f"https://github.com/o/{name}", "branch": "main", "commit": "a" * 40}
    if kind == "install":
        data["install"] = ["tool one", "tool two"]
    data.update(over)
    return data


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def ledger_doc(*ids: int) -> dict:
    return {"schema": "socratex-improvements/v1", "updated": "2026-01-01",
            "items": [{"id": i, "title": f"t{i}", "status": "adopted"} for i in ids]}


@pytest.fixture()
def root(tmp_path):
    """A fake repo: a few shipped manifests (one default-enabled), a defaults config and a two-entry ledger."""
    base = tmp_path / "repo"
    write(base / "defaults" / "config.json", {"schema_version": 1})
    ship = base / "modules" / "extensions"
    write(ship / "alpha.json", manifest("alpha", default_enabled=True, category="code"))
    write(ship / "beta.json", manifest("beta", "install", category="review", status="trial"))
    write(ship / "gamma.json", manifest("gamma", "ref", category="workflow"))
    write(ship / "delta.json", manifest("delta", category="code", status="rejected"))
    write(base / "docs" / "IMPROVEMENTS.json", ledger_doc(1, 2))
    return base


@pytest.fixture()
def project(tmp_path):
    folder = tmp_path / "myproj"
    folder.mkdir()
    return folder


def enabled(root, project=None) -> list[str]:
    return extensions.enabled_names(root, project)


# ---------- shipped manifests ----------

def test_every_shipped_manifest_is_valid_and_named_after_its_file():
    found = extensions.load_manifests(REPO)
    files = {p.stem for p in (REPO / "modules" / "extensions").glob("*.json") if p.name != "module.json"}
    assert set(found) == files and len(found) >= 40
    assert all(m["_layer"] == "shipped" for m in found.values())


def test_every_shipped_manifest_passes_json_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((CORE_DIR / "extension.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft7Validator.check_schema(schema)
    for path in (REPO / "modules" / "extensions").glob("*.json"):
        if path.name != "module.json":
            jsonschema.validate(json.loads(path.read_text(encoding="utf-8")), schema)


def test_shipped_reference_packs_are_pinned_github_manifests():
    refs = extensions.load_manifests(REPO, kinds=("ref",))
    assert len(refs) == 15 and {"superpowers", "ecc", "anthropic-skills", "awesome-claude-skills"} <= set(refs)
    for m in refs.values():
        assert m["source"]["url"].startswith("https://github.com/") and len(m["source"]["commit"]) == 40
        assert m["default_enabled"] is False and "install" not in m


def test_shipped_local_skills_mods_and_plugins_are_seeded():
    found = extensions.load_manifests(REPO)
    for skill in ("spec", "memory-review", "skill-reflect", "gpt-share-read", "token-efficient-code", "usage-optimize"):
        assert found[skill]["kind"] == "install" and found[skill]["default_enabled"] and "path" in found[skill]["source"]
    assert found["flow-panel"]["kind"] == "install" and found["codex"]["source"]["id"] == "codex@openai-codex"
    assert {"rtk", "ast-grep", "serena", "graphify", "toon", "repomix"} <= set(found)


def test_ledger_links_point_at_entries_with_the_same_status():
    items = {i["id"]: i for i in json.loads((REPO / "docs" / "IMPROVEMENTS.json").read_text(encoding="utf-8"))["items"]}
    linked = [m for m in extensions.load_manifests(REPO).values() if "ledger" in m]
    assert len(linked) >= 25
    for m in linked:
        assert m["ledger"] in items, m["name"]
        assert extensions.STATUS_FROM_LEDGER[items[m["ledger"]]["status"]] == m["status"], m["name"]


def test_real_defaults_fit_the_startup_budget(tmp_path):
    copy = tmp_path / "repo"
    shutil.copytree(REPO / "defaults", copy / "defaults")
    shutil.copytree(REPO / "modules" / "extensions", copy / "modules" / "extensions")
    shutil.copytree(REPO / "skills", copy / "skills")
    shutil.copytree(REPO / "claude" / "skills", copy / "claude" / "skills")
    shutil.copytree(REPO / "claude" / "mods", copy / "claude" / "mods")
    (copy / "core").mkdir()
    shutil.copy(REPO / "core" / "INIT.md", copy / "core" / "INIT.md")
    values = core.resolve(None, copy)["values"]
    assert set(values["extensions"]) == set(extensions.default_enabled(REPO)) and len(values["extensions"]) >= 7
    assert core.init_size(None, copy) <= core.INIT_TOTAL_MAX_BYTES


# ---------- validation errors name file and key ----------

@pytest.mark.parametrize("change, key", [
    ({"surprise": 1}, "unknown key 'surprise'"),
    ({"kind": "plugin"}, "kind"),
    ({"status": "maybe"}, "status"),
    ({"default_enabled": "yes"}, "default_enabled"),
    ({"context_cost": {"level": "huge", "note": "n"}}, "context_cost.level"),
    ({"name": "other"}, "name: 'other' must equal the file name"),
    ({"name": "Bad_Name"}, "name"),
    ({"when_to_use": "line one\nline two"}, "when_to_use"),
    ({"when_to_use": "x" * 201}, "when_to_use"),
    ({"source": {}}, "source: needs one of url, path or id"),
    ({"source": {"id": "x"}}, "source: needs commit or version"),
    ({"source": {"path": "no/such/path"}}, "source.path"),
    ({"install": ["x"]}, "install: kind note has no install commands"),
])
def test_invalid_manifest_names_file_and_key(root, change, key):
    data = manifest("alpha")
    data.update(change)
    if change.get("name") == "Bad_Name":
        target = write(root / "modules" / "extensions" / "Bad_Name.json", data)
    else:
        target = write(root / "modules" / "extensions" / "alpha.json", data)
    with pytest.raises(extensions.ExtensionError) as err:
        extensions.load_manifests(root)
    assert target.name in str(err.value) and key in str(err.value)


def test_missing_key_is_named(root):
    data = manifest("alpha")
    del data["when_to_use"]
    write(root / "modules" / "extensions" / "alpha.json", data)
    with pytest.raises(extensions.ExtensionError, match="alpha.json.*missing required key 'when_to_use'"):
        extensions.load_manifests(root)


def test_kind_rules(root):
    ship = root / "modules" / "extensions"
    cases = {
        "ref-install": manifest("ref-install", "ref", install=["x"]),
        "ref-on": manifest("ref-on", "ref", default_enabled=True),
        "ref-badpin": manifest("ref-badpin", "ref", source={"url": "https://github.com/o/x", "commit": "abc"}),
        "inst-empty": manifest("inst-empty", "install", install=[]),
    }
    for name, data in cases.items():
        write(ship / f"{name}.json", data)
    with pytest.raises(extensions.ExtensionError) as err:
        extensions.load_manifests(root)
    text = str(err.value)
    for needle in ("ref-install.json: install", "ref-on.json: default_enabled", "ref-badpin.json: source.commit", "inst-empty.json: install"):
        assert needle in text


def test_broken_json_is_an_error_not_skipped(root):
    (root / "modules" / "extensions" / "alpha.json").write_text("{nope", encoding="utf-8")
    with pytest.raises(extensions.ExtensionError, match="alpha.json.*cannot read JSON"):
        extensions.load_manifests(root)
    with pytest.raises(core.ConfigError, match="alpha.json"):
        core.resolve(None, root)


def test_local_path_source_must_exist_and_may_exist(root):
    (root / "skills" / "s").mkdir(parents=True)
    write(root / "modules" / "extensions" / "alpha.json", manifest("alpha", source={"path": "skills/s"}))
    assert extensions.load_manifests(root)["alpha"]["source"]["path"] == "skills/s"


# ---------- layers: local overrides shipped ----------

def test_local_manifest_overrides_the_shipped_one_and_adds_new_ones(root):
    write(root / "local" / "extensions" / "alpha.json", manifest("alpha", when_to_use="my own reason", default_enabled=False))
    write(root / "local" / "extensions" / "mine.json", manifest("mine"))
    found = extensions.load_manifests(root)
    assert found["alpha"]["_layer"] == "local" and found["alpha"]["when_to_use"] == "my own reason"
    assert found["mine"]["_layer"] == "local" and found["beta"]["_layer"] == "shipped"
    assert extensions.default_enabled(root) == []   # the local alpha is not default-enabled
    assert enabled(root) == []


def test_default_enabled_seeds_the_config_key_in_the_defaults_layer(root):
    result = core.resolve(None, root)
    assert result["values"]["extensions"] == ["alpha"]
    entry = result["provenance"]["extensions"]
    assert entry["layer"] == "defaults" and entry["file"].endswith("extensions")
    assert core.enabled_extensions(result) == [{"name": "alpha", "layer": "defaults", "file": entry["file"]}]


def test_enabled_name_without_manifest_is_an_error(root):
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "extensions": {"$append": ["ghost"]}})
    with pytest.raises(core.ConfigError, match="extensions: 'ghost' has no manifest"):
        core.resolve(None, root)


def test_changing_a_manifest_refreshes_the_effective_cache(root):
    assert core.effective(None, root)["values"]["extensions"] == ["alpha"]
    write(root / "modules" / "extensions" / "beta.json", manifest("beta", "install", default_enabled=True))
    assert core.effective(None, root)["values"]["extensions"] == ["alpha", "beta"]


# ---------- enable and disable ----------

def test_enable_writes_only_the_local_layer_and_config_show_names_it(root, project):
    msg = extensions.set_enabled("beta", True, root)
    assert "enabled" in msg
    local_file = root / "local" / "overrides" / "config.json"
    assert json.loads(local_file.read_text(encoding="utf-8")) == {"schema_version": 1, "extensions": {"$append": ["beta"]}}
    assert not (root / "local" / "projects").exists()
    assert enabled(root) == ["alpha", "beta"]
    by_name = {e["name"]: e["layer"] for e in core.enabled_extensions(core.resolve(project, root))}
    assert by_name == {"alpha": "defaults", "beta": "local"}


def test_enable_is_reproducible_and_idempotent(root):
    extensions.set_enabled("beta", True, root)
    first = (root / "local" / "overrides" / "config.json").read_text(encoding="utf-8")
    assert "already enabled" in extensions.set_enabled("beta", True, root)
    assert (root / "local" / "overrides" / "config.json").read_text(encoding="utf-8") == first


def test_project_disable_writes_the_project_private_layer_only(root, project):
    extensions.set_enabled("alpha", False, root, project)
    private = root / "local" / "projects" / project.name / "config.json"
    assert json.loads(private.read_text(encoding="utf-8"))["extensions"] == {"$remove": ["alpha"]}
    assert not (root / "local" / "overrides" / "config.json").exists()
    assert enabled(root, project) == [] and enabled(root) == ["alpha"]
    result = core.resolve(project, root)
    assert core.enabled_extensions(result) == []


def test_project_can_enable_what_local_disabled_and_vice_versa(root, project):
    extensions.set_enabled("alpha", False, root)
    assert enabled(root) == [] and enabled(root, project) == []
    extensions.set_enabled("alpha", True, root, project)
    assert enabled(root) == [] and enabled(root, project) == ["alpha"]
    layers = {e["name"]: e["layer"] for e in core.enabled_extensions(core.resolve(project, root))}
    assert layers == {"alpha": "project-private"}


def test_dot_socratex_project_file_can_remove_an_extension(root, project):
    write(project / ".socratex" / "config.json", {"schema_version": 1, "extensions": {"$remove": ["alpha"]}})
    assert enabled(root, project) == [] and enabled(root) == ["alpha"]


def test_disable_then_enable_returns_to_the_default(root):
    extensions.set_enabled("alpha", False, root)
    extensions.set_enabled("alpha", True, root)
    assert enabled(root) == ["alpha"]
    assert "extensions" not in json.loads((root / "local" / "overrides" / "config.json").read_text(encoding="utf-8"))


def test_one_layer_file_can_enable_one_and_disable_another(root):
    extensions.set_enabled("beta", True, root)
    extensions.set_enabled("alpha", False, root)
    data = json.loads((root / "local" / "overrides" / "config.json").read_text(encoding="utf-8"))
    assert data["extensions"] == {"$remove": ["alpha"], "$append": ["beta"]}
    assert enabled(root) == ["beta"]
    extensions.set_enabled("alpha", True, root)
    extensions.set_enabled("beta", False, root)
    assert "extensions" not in json.loads((root / "local" / "overrides" / "config.json").read_text(encoding="utf-8"))
    assert enabled(root) == ["alpha"]


def test_disable_replaces_a_redundant_append_with_a_remove(root):
    path = write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "extensions": {"$append": ["alpha"]}})
    extensions.set_enabled("alpha", False, root)
    assert json.loads(path.read_text(encoding="utf-8"))["extensions"] == {"$remove": ["alpha"]}
    assert enabled(root) == []


def test_a_switch_that_did_not_take_effect_is_restored(root, monkeypatch):
    path = write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "profile": "duo"})
    before = path.read_text(encoding="utf-8")
    monkeypatch.setattr(extensions, "enabled_names", lambda *a, **k: [])
    with pytest.raises(extensions.ExtensionError, match="cannot enable 'beta' in this layer alone"):
        extensions.set_enabled("beta", True, root)
    assert path.read_text(encoding="utf-8") == before


def test_plain_list_in_a_layer_file_is_edited_in_place(root):
    write(root / "local" / "overrides" / "config.json", {"schema_version": 1, "extensions": ["delta"]})
    extensions.set_enabled("beta", True, root)
    assert enabled(root) == ["delta", "beta"]
    extensions.set_enabled("delta", False, root)
    assert enabled(root) == ["beta"]


def test_switching_an_unknown_extension_is_refused(root):
    with pytest.raises(extensions.ExtensionError, match="unknown extension 'nope'"):
        extensions.set_enabled("nope", True, root)
    assert not (root / "local").exists()


# ---------- add ----------

def test_add_creates_a_trial_manifest_and_a_ledger_entry(root):
    path, ledger_id = extensions.add_extension("https://github.com/acme/Cool-Tool.git", root)
    assert path == root / "local" / "extensions" / "cool-tool.json" and ledger_id == 3
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["status"] == "trial" and data["default_enabled"] is False and data["kind"] == "note"
    assert data["when_to_use"] == "unknown" and data["risks"] == "unknown" and data["context_cost"]["level"] == "unknown"
    assert data["category"] == "unknown" and data["source"] == {"url": "https://github.com/acme/Cool-Tool.git", "version": "unknown"}
    assert data["ledger"] == 3
    assert extensions.load_manifests(root)["cool-tool"]["_layer"] == "local"
    ledger = json.loads((root / "docs" / "IMPROVEMENTS.json").read_text(encoding="utf-8"))
    entry = ledger["items"][-1]
    assert entry["id"] == 3 and entry["status"] == "considering" and entry["title"] == "cool-tool"
    assert entry["area"] == "Plugins, MCP, tools" and "TODO" in entry["what"] and "TODO" in entry["why"]
    assert entry["source"] == "sox ext add" and ledger["updated"] == entry["date"]
    assert enabled(root) == ["alpha"]   # trial stays off


def test_add_options_and_install_placeholder(root):
    path, _ = extensions.add_extension("https://example.com/x/y", root, name="why", kind="install", category="research")
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["name"] == "why" and data["category"] == "research" and data["install"] == ["unknown"]
    with pytest.raises(extensions.ExtensionError, match="still 'unknown'"):
        extensions.install_extension("why", True, root)


def test_add_ref_marks_the_pin_unknown(root):
    path, _ = extensions.add_extension("https://github.com/acme/pack", root, kind="ref")
    assert json.loads(path.read_text(encoding="utf-8"))["source"]["commit"] == "unknown"
    assert extensions.load_manifests(root)["pack"]["kind"] == "ref"


def test_add_keeps_the_ledger_line_endings(root):
    ledger = root / "docs" / "IMPROVEMENTS.json"
    ledger.write_bytes(json.dumps(ledger_doc(1), indent=2).replace("\n", "\r\n").encode("utf-8"))
    extensions.add_extension("https://github.com/acme/tool", root)
    raw = ledger.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"")


@pytest.mark.parametrize("url", ["http://example.com/x", "not a url", "https:///nohost", "ftp://x/y"])
def test_add_rejects_bad_urls(root, url):
    with pytest.raises(extensions.ExtensionError, match="https://"):
        extensions.add_extension(url, root)
    assert not (root / "local").exists()


def test_add_rejects_duplicates_bad_names_and_missing_ledger(root):
    with pytest.raises(extensions.ExtensionError, match="already exists"):
        extensions.add_extension("https://github.com/acme/alpha", root)
    with pytest.raises(extensions.ExtensionError, match="lower-case"):
        extensions.add_extension("https://github.com/acme/x", root, name="Bad Name")
    (root / "docs" / "IMPROVEMENTS.json").unlink()
    with pytest.raises(extensions.ExtensionError, match="ledger is missing"):
        extensions.add_extension("https://github.com/acme/fresh", root)
    assert not (root / "local").exists()


# ---------- remove ----------

def test_remove_deletes_a_local_manifest_and_cleans_config_layers(root, project):
    extensions.add_extension("https://github.com/acme/tool", root)
    extensions.set_enabled("tool", True, root)
    extensions.set_enabled("tool", False, root, project)
    touched = extensions.remove_extension("tool", root)
    assert len(touched) == 2 and "tool" not in extensions.load_manifests(root)
    assert enabled(root, project) == ["alpha"]
    ledger = json.loads((root / "docs" / "IMPROVEMENTS.json").read_text(encoding="utf-8"))
    assert ledger["items"][-1]["title"] == "tool"   # history stays


def test_remove_refuses_shipped_and_unknown(root):
    with pytest.raises(extensions.ExtensionError, match="shipped.*disable"):
        extensions.remove_extension("alpha", root)
    with pytest.raises(extensions.ExtensionError, match="unknown extension"):
        extensions.remove_extension("zzz", root)


# ---------- install ----------

@pytest.fixture()
def fakes(monkeypatch):
    calls: list = []
    monkeypatch.setattr(extensions, "BACKUP", lambda label: calls.append(("backup", label)) or Path("fake-backup.zip"))
    monkeypatch.setattr(extensions, "RUN", lambda argv, cwd: calls.append(("run", argv)) or 0)
    return calls


def test_install_without_yes_is_a_dry_run(root, fakes):
    lines = extensions.install_extension("beta", False, root)
    assert fakes == []
    assert "tool one" in "\n".join(lines) and "Dry run" in lines[-1]


def test_install_yes_backs_up_first_then_runs_in_order(root, fakes):
    lines = extensions.install_extension("beta", True, root)
    assert [c[0] for c in fakes] == ["backup", "run", "run"]
    assert fakes[1][1] == ["tool", "one"] and fakes[2][1] == ["tool", "two"]
    assert any("fake-backup.zip" in line for line in lines)


def test_install_python_command_uses_the_current_interpreter(root, fakes):
    write(root / "modules" / "extensions" / "beta.json", manifest("beta", "install", install=["python core/sox install --plan"]))
    extensions.install_extension("beta", True, root)
    assert fakes[1][1][0] == sys.executable and fakes[1][1][1:] == ["core/sox", "install", "--plan"]


def test_failed_command_stops_the_rest(root, monkeypatch):
    ran = []
    monkeypatch.setattr(extensions, "BACKUP", lambda label: Path("b.zip"))
    monkeypatch.setattr(extensions, "RUN", lambda argv, cwd: ran.append(argv) or 3)
    with pytest.raises(extensions.ExtensionError, match="failed; later commands were not run"):
        extensions.install_extension("beta", True, root)
    assert len(ran) == 1


def test_failed_backup_runs_nothing(root, monkeypatch):
    ran = []
    monkeypatch.setattr(extensions, "BACKUP", lambda label: (_ for _ in ()).throw(OSError("disk full")))
    monkeypatch.setattr(extensions, "RUN", lambda argv, cwd: ran.append(argv) or 0)
    with pytest.raises(OSError):
        extensions.install_extension("beta", True, root)
    assert ran == []


@pytest.mark.parametrize("yes", [False, True])
def test_reference_packs_are_never_executed(root, fakes, yes):
    with pytest.raises(extensions.ExtensionError, match="read-only reference pack"):
        extensions.install_extension("gamma", yes, root)
    assert fakes == []


@pytest.mark.parametrize("name, message", [("alpha", "recommendation only"), ("delta", "recommendation only")])
def test_notes_are_never_executed(root, fakes, name, message):
    with pytest.raises(extensions.ExtensionError, match=message):
        extensions.install_extension(name, True, root)
    assert fakes == []


def test_rejected_install_is_refused(root, fakes):
    write(root / "modules" / "extensions" / "beta.json", manifest("beta", "install", status="rejected"))
    with pytest.raises(extensions.ExtensionError, match="status rejected"):
        extensions.install_extension("beta", True, root)
    assert fakes == []


def test_shipped_ref_manifests_cannot_be_installed(fakes):
    with pytest.raises(extensions.ExtensionError, match="never installed or run"):
        extensions.install_extension("superpowers", True, REPO)
    assert fakes == []


# ---------- list and show ----------

def test_list_groups_by_category_with_status_kind_and_state(root, project):
    extensions.set_enabled("beta", True, root, project)
    text = "\n".join(extensions.list_lines(root, project))
    assert text.index("code (2)") < text.index("review (1)") < text.index("workflow (1)")
    alpha = next(line for line in text.splitlines() if "alpha" in line)
    beta = next(line for line in text.splitlines() if "beta" in line)
    delta = next(line for line in text.splitlines() if "delta" in line)
    assert "adopted" in alpha and "note" in alpha and "on" in alpha.split()
    assert "trial" in beta and "install" in beta and "on" in beta.split()
    assert "rejected" in delta and "off" in delta.split()
    assert "off" in next(line for line in extensions.list_lines(root) if "beta" in line).split()   # not enabled outside the project


def test_list_filters_and_marks_local_manifests(root):
    write(root / "local" / "extensions" / "mine.json", manifest("mine", category="code", status="trial"))
    assert [l for l in extensions.list_lines(root, category="review") if l.startswith("  ")][0].split()[0] == "beta"
    only = extensions.list_lines(root, status="trial")
    assert any("beta" in l for l in only) and any("mine" in l and "[local]" in l for l in only) and not any("alpha" in l for l in only)
    assert extensions.list_lines(root, category="nothing") == ["no extension matches"]


def test_show_prints_manifest_layer_and_state(root):
    text = "\n".join(extensions.show_lines("alpha", root))
    assert "shipped manifest" in text and "enabled here: yes" in text and '"when_to_use"' in text
    with pytest.raises(extensions.ExtensionError, match="unknown extension"):
        extensions.show_lines("nope", root)


# ---------- the CLI ----------

def run(root, *argv):
    return sox.main(["ext", "--root", str(root), *argv])


def test_cli_roundtrip(root, project, capsys, monkeypatch):
    assert run(root, "add", "https://github.com/acme/widget", "--category", "code") == 0
    assert "ledger entry 3" in capsys.readouterr().out
    assert run(root, "enable", "widget", "--project", str(project)) == 0
    assert run(root, "list", "--project", str(project), "--category", "code") == 0
    out = capsys.readouterr().out
    assert "widget" in next(line for line in out.splitlines() if "widget" in line and "on" in line.split())
    assert run(root, "show", "widget") == 0
    assert run(root, "install", "widget") == 2
    assert "recommendation only" in capsys.readouterr().err
    assert run(root, "remove", "widget") == 0
    assert run(root, "disable", "widget") == 2


def test_cli_install_dry_run_does_not_back_up(root, capsys, fakes):
    assert run(root, "install", "beta") == 0
    assert "Dry run" in capsys.readouterr().out and fakes == []
    assert run(root, "install", "beta", "--yes") == 0
    assert fakes[0][0] == "backup"


def test_config_show_lists_enabled_extensions_with_their_layer(root, project, capsys, monkeypatch):
    extensions.set_enabled("beta", True, root)
    monkeypatch.setattr(core, "ROOT", root)
    original = core.layers
    monkeypatch.setattr(core, "layers", lambda project_root=None, root_=None: original(project_root, root))
    assert sox.main(["config", "show", "--project", str(project)]) == 0
    out = capsys.readouterr().out
    block = out[out.index("Enabled extensions:"):]
    assert "alpha  <- defaults:" in block and "beta  <- local:" in block
    assert sox.main(["config", "show", "--project", str(project), "--json"]) == 0
    shown = json.loads(capsys.readouterr().out)
    assert [e["name"] for e in shown["enabled_extensions"]] == ["alpha", "beta"]


# ---------- startup budget and generated startup text ----------

def test_budget_counts_the_lines_of_enabled_extensions(root, tmp_path):
    (root / "core").mkdir(exist_ok=True)
    (root / "core" / "INIT.md").write_text("x" * 50, encoding="utf-8")
    before = core.init_size(None, root)
    extensions.set_enabled("beta", True, root)
    line = "beta: use beta when needed"
    assert core.init_size(None, root) == before + len(line) + 1
    extensions.set_enabled("alpha", False, root)
    assert core.init_size(None, root) == before - len("alpha: use alpha when needed") + len(line)


def test_budget_catches_an_oversized_default_set(root):
    (root / "core").mkdir(exist_ok=True)
    (root / "core" / "INIT.md").write_text("x" * 50, encoding="utf-8")
    for n in range(30):
        write(root / "modules" / "extensions" / f"big{n}.json", manifest(f"big{n}", default_enabled=True, when_to_use="y" * 190))
    assert core.init_size(None, root) > core.INIT_TOTAL_MAX_BYTES


def test_generated_startup_text_includes_the_extension_lines(root, monkeypatch):
    monkeypatch.setattr(install, "SOCRATEX", root)
    monkeypatch.setattr(install, "load_rules", lambda: True)
    (root / "core").mkdir(exist_ok=True)
    (root / "core" / "INIT.md").write_text("# init\n", encoding="utf-8")
    block = install.claude_block()
    assert core.EXTENSION_HEADER in block and "alpha: use alpha when needed" in block and "beta:" not in block
    agents = install.codex_agents_md()
    assert "alpha: use alpha when needed" in agents
    extensions.set_enabled("beta", True, root)
    assert "beta: use beta when needed" in install.claude_block()
    assert install.extension_lines()[0] == core.EXTENSION_HEADER


def test_no_extension_lines_when_nothing_is_enabled(root, monkeypatch):
    extensions.set_enabled("alpha", False, root)
    monkeypatch.setattr(install, "SOCRATEX", root)
    assert install.extension_lines() == []
