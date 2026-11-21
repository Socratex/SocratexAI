"""Criteria 1 and 10: registry validation and the per-project override."""

from __future__ import annotations

import json

import pytest

import common
import run
from conftest import REGISTRY_PATH

GOOD = {"id": "x", "pipeline": "review", "concern": "c", "scope": "hunk", "select": "{python} {here}/select_quality.py --mode contracts",
        "tool": "none", "tier": "cheap", "autofix": "none", "enabled": True}


def write_registry(path, checkers, **top):
    doc = {"schema": "socratex-checker-registry/v1", "pipeline": "review", "skip_patterns": [], "min_changed_lines": 0,
           "default_max_chunk_lines": 50, "checkers": checkers, **top}
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_real_registry_is_valid_and_complete():
    registry = common.load_registry(REGISTRY_PATH, None)
    ids = [c["id"] for c in registry["checkers"]]
    assert ids == ["readability", "architecture", "test-necessity", "comments", "contracts", "leaks"]
    for checker in registry["checkers"]:
        for field in ("id", "pipeline", "concern", "scope", "max_chunk_lines", "select", "tool", "tier", "autofix", "enabled"):
            assert field in checker, (checker["id"], field)
    assert isinstance(registry["min_changed_lines"], int)


@pytest.mark.parametrize("missing", ["id", "pipeline", "scope", "select", "tier", "autofix"])
def test_checker_without_required_field_is_rejected_with_readable_error(tmp_path, missing):
    bad = {k: v for k, v in GOOD.items() if k != missing}
    path = write_registry(tmp_path / "r.json", [bad])
    with pytest.raises(common.RegistryError) as err:
        common.load_registry(path, None)
    assert missing in str(err.value)


def test_invalid_values_and_whole_diff_without_reason_are_rejected(tmp_path):
    for bad in ({**GOOD, "tier": "turbo"}, {**GOOD, "autofix": "magic"}, {**GOOD, "scope": "whole_diff"},
                {**GOOD, "autofix": "script"}):
        with pytest.raises(common.RegistryError):
            common.load_registry(write_registry(tmp_path / "r.json", [bad]), None)
    ok = {**GOOD, "scope": "whole_diff", "scope_reason": "needs the full picture"}
    assert common.load_registry(write_registry(tmp_path / "r.json", [ok]), None)["checkers"][0]["scope"] == "whole_diff"


def test_duplicate_ids_are_rejected(tmp_path):
    with pytest.raises(common.RegistryError):
        common.load_registry(write_registry(tmp_path / "r.json", [GOOD, GOOD]), None)


def test_runner_cli_rejects_bad_registry_with_exit_2(tmp_path, repo, capsys):
    bad = {k: v for k, v in GOOD.items() if k != "select"}
    path = write_registry(tmp_path / "r.json", [bad])
    code = run.main(["--project-dir", str(repo.path), "--files", "app.py", "--registry", str(path), "--run-id", "t"])
    assert code == 2
    assert "select" in capsys.readouterr().err


def test_project_override_disables_and_retiers_without_touching_global(repo):
    before = REGISTRY_PATH.read_bytes()
    repo.write(".ai/review.json", json.dumps({"checkers": {"comments": {"enabled": False},
                                                          "contracts": {"tier": "standard"}}}))
    merged = common.load_registry(REGISTRY_PATH, repo.path)
    by_id = {c["id"]: c for c in merged["checkers"]}
    assert by_id["comments"]["enabled"] is False and by_id["contracts"]["tier"] == "standard"
    assert REGISTRY_PATH.read_bytes() == before
    fresh = {c["id"]: c for c in common.load_registry(REGISTRY_PATH, None)["checkers"]}
    assert fresh["comments"]["enabled"] is True and fresh["contracts"]["tier"] == "cheap"


def test_project_override_can_add_checker_and_rejects_unknown_id(repo):
    repo.write(".ai/review.json", json.dumps({"add": [GOOD]}))
    assert "x" in [c["id"] for c in common.load_registry(REGISTRY_PATH, repo.path)["checkers"]]
    repo.write(".ai/review.json", json.dumps({"checkers": {"nope": {"enabled": False}}}))
    with pytest.raises(common.RegistryError):
        common.load_registry(REGISTRY_PATH, repo.path)


def test_tier_alias_comes_from_routing_json_and_can_be_overridden():
    assert common.tier_alias("cheap", {}) == "haiku"
    assert common.tier_alias("standard", {}) == "sonnet"
    assert common.tier_alias("cheap", {"cheap": "custom"}) == "custom"


def test_registry_schema_name_pipeline_and_optional_stage(tmp_path):
    path = write_registry(tmp_path / "r.json", [{**GOOD, "stage": "interpret"}])
    assert common.load_registry(path, None)["checkers"][0]["stage"] == "interpret"
    assert common.load_registry(path, None)["pipeline"] == "review"
    assert json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))["schema"] == "socratex-checker-registry/v1"
    wrong_schema = write_registry(tmp_path / "s.json", [GOOD], schema="socratex-review-registry/v1")
    with pytest.raises(common.RegistryError):
        common.load_registry(wrong_schema, None)


@pytest.mark.parametrize("bad", [{"pipeline": "other"}, {"pipeline": "planning"}])
def test_pipeline_must_be_known_and_match_the_registry(tmp_path, bad):
    with pytest.raises(common.RegistryError):
        common.load_registry(write_registry(tmp_path / "r.json", [{**GOOD, **bad}]), None)


def test_here_placeholder_points_at_the_registry_folder(tmp_path):
    path = write_registry(tmp_path / "r.json", [GOOD])
    assert common.load_registry(path, None)["checkers"][0]["here"] == tmp_path.resolve()
