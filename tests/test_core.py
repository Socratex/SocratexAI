"""Tests for core/core.py (config resolver) and core/sox (CLI)."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

import pytest

CORE_DIR = Path(__file__).resolve().parents[1] / "core"
sys.path.insert(0, str(CORE_DIR))

import core  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


@pytest.fixture()
def env(tmp_path):
    """A fake repo root with defaults, plus a project folder."""
    root = tmp_path / "repo"
    write(root / "defaults" / "config.json", {
        "schema_version": 1, "profile": "duo", "extensions": ["a", "b"],
        "stages": {"review": {"enabled": True}, "planning": {"enabled": True}},
    })
    for name in ("solo", "duo", "yolo"):
        write(root / "defaults" / "profiles" / f"{name}.json", {
            "schema": "socratex-profile/v1", "schema_version": 1, "name": name, "what": name,
            "config": {"codex": {"enabled": name != "solo"}}})
    project = tmp_path / "myproj"
    project.mkdir()
    return root, project


def local(root, data):
    return write(root / "local" / "overrides" / "config.json", {"schema_version": 1, **data})


def proj(project, data):
    return write(project / ".socratex" / "config.json", {"schema_version": 1, **data})


def private(root, project, data):
    return write(root / "local" / "projects" / project.name / "config.json", {"schema_version": 1, **data})


def val(env, key="profile"):
    root, project = env
    return core.resolve(project, root)["values"][key]


def test_layer_order(env):
    root, project = env
    assert [l["name"] for l in core.layers(project, root)] == ["defaults", "profile", "local", "project", "project-private"]


def test_defaults_only_when_layers_absent(env):
    root, project = env
    result = core.resolve(project, root)
    assert result["values"]["profile"] == "duo"
    assert result["provenance"]["profile"]["layer"] == "defaults"
    assert [s["layer"] for s in result["sources"]] == ["defaults", "profile"]


def test_no_project_root_skips_project_layers(env):
    root, _ = env
    assert [l["name"] for l in core.layers(None, root)] == ["defaults", "profile", "local"]


def test_local_overrides_defaults(env):
    root, _ = env
    local(root, {"profile": "solo"})
    assert val(env) == "solo"


def test_project_overrides_local(env):
    root, project = env
    local(root, {"profile": "solo"})
    proj(project, {"profile": "yolo"})
    assert val(env) == "yolo"
    prov = core.resolve(project, root)["provenance"]["profile"]
    assert prov["layer"] == "project"
    assert [o["layer"] for o in prov["overridden"]] == ["defaults", "local"]
    assert [o["value"] for o in prov["overridden"]] == ["duo", "solo"]


def test_private_overrides_project(env):
    root, project = env
    proj(project, {"profile": "yolo"})
    private(root, project, {"profile": "solo"})
    assert val(env) == "solo"
    assert core.resolve(project, root)["provenance"]["profile"]["layer"] == "project-private"


def test_project_overrides_defaults_directly(env):
    root, project = env
    proj(project, {"profile": "solo"})
    assert val(env) == "solo"


def test_private_overrides_defaults_directly(env):
    root, project = env
    private(root, project, {"profile": "solo"})
    assert val(env) == "solo"


def test_deep_merge_keeps_siblings(env):
    root, project = env
    proj(project, {"stages": {"review": {"enabled": False}}})
    stages = val(env, "stages")
    assert stages == {"review": {"enabled": False}, "planning": {"enabled": True}}
    prov = core.resolve(project, root)["provenance"]
    assert prov["stages.review.enabled"]["layer"] == "project"
    assert prov["stages.planning.enabled"]["layer"] == "defaults"


def test_list_replaces_by_default(env):
    root, project = env
    local(root, {"extensions": ["z"]})
    assert val(env, "extensions") == ["z"]


def test_append(env):
    root, project = env
    local(root, {"extensions": {"$append": ["c"]}})
    proj(project, {"extensions": {"$append": ["d"]}})
    assert val(env, "extensions") == ["a", "b", "c", "d"]


def test_append_to_missing_list_creates_it(env):
    root, project = env
    write(root / "defaults" / "config.json", {"schema_version": 1})
    local(root, {"extensions": {"$append": ["x"]}})
    assert val(env, "extensions") == ["x"]


def test_remove_items_and_missing_item_ignored(env):
    root, project = env
    local(root, {"extensions": {"$remove": ["a", "not-there"]}})
    assert val(env, "extensions") == ["b"]


def test_remove_from_missing_list_is_noop(env):
    root, project = env
    write(root / "defaults" / "config.json", {"schema_version": 1})
    local(root, {"extensions": {"$remove": ["a"]}})
    assert "extensions" not in core.resolve(project, root)["values"]


def test_delete_key_and_missing_key(env):
    root, project = env
    local(root, {"profile": {"$delete": True}, "extensions": {"$delete": True}})
    proj(project, {"extensions": {"$delete": True}})
    result = core.resolve(project, root)
    assert "profile" not in result["values"]
    assert "extensions" not in result["values"]
    assert "profile" not in result["provenance"]


def test_delete_nested_key(env):
    root, project = env
    proj(project, {"stages": {"review": {"$delete": True}}})
    assert val(env, "stages") == {"planning": {"enabled": True}}


def test_unknown_key_error_names_file_and_key(env):
    root, project = env
    path = proj(project, {"profil": "solo"})
    with pytest.raises(core.ConfigError) as err:
        core.resolve(project, root)
    assert str(path) in str(err.value)
    assert "profil" in str(err.value)


def test_unknown_nested_key_error(env):
    root, project = env
    local(root, {"stages": {"review": {"enable": True}}})
    with pytest.raises(core.ConfigError, match="stages.review.enable"):
        core.resolve(project, root)


def test_wrong_type_and_enum_errors(env):
    root, project = env
    local(root, {"profile": "turbo"})
    with pytest.raises(core.ConfigError, match="profile"):
        core.resolve(project, root)
    local(root, {"stages": {"review": {"enabled": "yes"}}})
    with pytest.raises(core.ConfigError, match="stages.review.enabled"):
        core.resolve(project, root)


def test_missing_schema_version_error(env):
    root, project = env
    path = write(project / ".socratex" / "config.json", {"profile": "solo"})
    with pytest.raises(core.ConfigError) as err:
        core.resolve(project, root)
    assert str(path) in str(err.value)
    assert "schema_version" in str(err.value)


def test_unsupported_schema_version_error_has_hint(env):
    root, project = env
    path = write(root / "local" / "overrides" / "config.json", {"schema_version": 0})
    with pytest.raises(core.ConfigError) as err:
        core.resolve(project, root)
    assert str(path) in str(err.value)
    assert "sox migrate" in str(err.value)


def test_invalid_json_error_names_file(env):
    root, project = env
    path = project / ".socratex" / "config.json"
    path.parent.mkdir()
    path.write_text("{oops", encoding="utf-8")
    with pytest.raises(core.ConfigError, match="config.json"):
        core.resolve(project, root)


def test_directive_on_non_list_rejected(env):
    root, project = env
    local(root, {"profile": {"$append": ["x"]}})
    with pytest.raises(core.ConfigError, match="profile"):
        core.resolve(project, root)


def test_effective_written_with_hashes_and_recomputed_when_stale(env):
    root, project = env
    local(root, {"profile": "solo"})
    first = core.effective(project, root)
    path = core.effective_path(root)
    assert path.is_file()
    assert first["values"]["profile"] == "solo"
    assert {s["layer"] for s in first["sources"]} == {"defaults", "profile", "local"}
    assert all(len(s["sha256"]) == 64 for s in first["sources"])
    # fresh: served from the cache even if the cached values are tampered with
    cached = json.loads(path.read_text(encoding="utf-8"))
    cached["values"]["profile"] = "CACHED"
    path.write_text(json.dumps(cached), encoding="utf-8")
    assert core.effective(project, root)["values"]["profile"] == "CACHED"
    # stale: a source changed
    local(root, {"profile": "yolo"})
    assert core.effective(project, root)["values"]["profile"] == "yolo"
    assert json.loads(path.read_text(encoding="utf-8"))["values"]["profile"] == "yolo"
    # stale: a new layer file appeared
    proj(project, {"profile": "duo"})
    assert core.effective(project, root)["values"]["profile"] == "duo"


def test_cli_show_lists_every_key_with_source(env, capsys, monkeypatch):
    root, project = env
    local(root, {"profile": "solo"})
    proj(project, {"stages": {"review": {"enabled": False}}})
    monkeypatch.setattr(core, "ROOT", root)
    original = core.layers
    monkeypatch.setattr(core, "layers", lambda project_root=None, root_=None: original(project_root, root))
    assert sox.main(["config", "show", "--project", str(project)]) == 0
    out = capsys.readouterr().out
    result = core.resolve(project, root)
    assert result["provenance"]
    for key, entry in result["provenance"].items():
        line = next(l for l in out.splitlines() if l.startswith(key + " "))
        assert entry["layer"] in line
        assert entry["file"] in line
    review = next(l for l in out.splitlines() if l.startswith("stages.review.enabled"))
    assert "true (defaults)" in review  # overridden value shown in the extra column


def test_cli_show_json_and_error_exit(env, capsys, monkeypatch):
    root, project = env
    monkeypatch.setattr(core, "ROOT", root)
    original = core.layers
    monkeypatch.setattr(core, "layers", lambda project_root=None, root_=None: original(project_root, root))
    assert sox.main(["config", "show", "--project", str(project), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["values"]["profile"] == "duo"
    proj(project, {"bogus": 1})
    assert sox.main(["config", "show", "--project", str(project)]) == 2
    assert "bogus" in capsys.readouterr().err


def test_remove_and_append_in_one_value_drop_first_then_append(env):
    root, project = env
    local(root, {"extensions": {"$remove": ["a"], "$append": ["c", "a"]}})
    assert val(env, "extensions") == ["b", "c", "a"]
    prov = core.resolve(project, root)["provenance"]["extensions"]
    assert prov["layer"] == "local" and prov["overridden"][0]["value"] == ["a", "b"]


def test_combined_directive_is_validated(env):
    root, project = env
    local(root, {"extensions": {"$remove": ["a"], "$append": "c"}})
    with pytest.raises(core.ConfigError, match=r"config.json.*extensions: \$append needs a list"):
        core.resolve(project, root)
    local(root, {"extensions": {"$remove": [1], "$append": []}})
    with pytest.raises(core.ConfigError, match=r"extensions.\$remove\[0\]"):
        core.resolve(project, root)
    local(root, {"stages": {"$remove": [], "$append": []}})
    with pytest.raises(core.ConfigError, match="only applies to a list"):
        core.resolve(project, root)


def test_shipped_defaults_file_is_valid():
    data = core.load_layer_file(core.ROOT / "defaults" / "config.json")
    assert data["profile"] == "duo"
    assert data["stages"]["review"]["enabled"] is True
