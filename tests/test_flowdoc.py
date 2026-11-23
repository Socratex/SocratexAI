"""Tests for `sox flow doc`: docs/FLOW.md is generated from defaults/flow.json, the parser help and the directory map."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CORE_DIR = REPO / "core"
sys.path.insert(0, str(CORE_DIR))

import flowdoc  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_flowdoc", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_flowdoc", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def test_flow_doc_check_passes_on_the_repo(capsys):
    assert sox.main(["flow", "doc", "--check"]) == 0
    assert "up to date" in capsys.readouterr().out


def test_flow_doc_has_a_row_per_step_with_its_then():
    text = (REPO / "docs" / "FLOW.md").read_text(encoding="utf-8")
    steps = json.loads((REPO / "defaults" / "flow.json").read_text(encoding="utf-8"))["steps"]
    for step in steps:
        row = next(line for line in text.splitlines() if line.startswith("|") and f"`{step['id']}`" in line)
        assert all(f"`{action}`" in row for action in step["then"])
    assert text.startswith("---\ntype: doc\n") and "\nupdated: " in text


def test_flow_doc_check_detects_a_stale_page(monkeypatch, tmp_path, capsys):
    flow_file = tmp_path / "defaults" / "flow.json"
    flow_file.parent.mkdir()
    flow_file.write_text((REPO / "defaults" / "flow.json").read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(flowdoc, "ROOT", tmp_path)
    assert sox.main(["flow", "doc", "--check"]) == 1          # no page yet
    assert "stale" in capsys.readouterr().err
    assert sox.main(["flow", "doc"]) == 0
    page = tmp_path / "docs" / "FLOW.md"
    assert page.is_file() and sox.main(["flow", "doc", "--check"]) == 0
    page.write_text(page.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8")
    assert sox.main(["flow", "doc", "--check"]) == 1
    assert sox.main(["flow", "doc"]) == 0
    flow = json.loads(flow_file.read_text(encoding="utf-8"))   # a data change makes the page stale too
    flow["steps"][1]["id"] = "renamed"
    flow_file.write_text(json.dumps(flow), encoding="utf-8")
    assert sox.main(["flow", "doc", "--check"]) == 1


def test_condition_reading():
    assert flowdoc.condition({}) == "zawsze"
    assert flowdoc.condition({"task_size": {"not": "trivial"}, "codex": True}) == "task_size ≠ trivial i codex"
    assert flowdoc.condition({"attempts_on_tier": {"gte": 2}}) == "attempts_on_tier ≥ 2"
    assert flowdoc.condition({"any": [{"a": "x"}, {"b": ["y", "z"]}]}) == "(a = x lub b ∈ {y, z})"


def test_command_help_lists_every_command_with_its_help():
    rows = dict(sox.command_help(sox.build_parser()))
    for name in ("sox flow doc", "sox shims", "sox flow check", "sox config show", "sox ext list", "sox index", "sox test"):
        assert rows.get(name), name


def test_directory_map_points_to_existing_directories():
    for path, _ in flowdoc.DIRECTORY_MAP:
        for part in (p.strip() for p in path.split(",")):
            assert (REPO / part).is_dir(), part


def test_every_top_level_directory_is_in_the_map():
    mapped = " ".join(path for path, _ in flowdoc.DIRECTORY_MAP)
    for entry in REPO.iterdir():
        if entry.is_dir() and not entry.name.startswith((".", "__")) and entry.name not in ("audits", "local.example", "subrepos"):
            assert f"{entry.name}/" in mapped, entry.name
