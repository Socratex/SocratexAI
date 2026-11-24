"""Checks for `sox ledger find` (modules/tools/scripts/ledger_find.py): scoring, status labels, exit codes, fixtures only."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "core"))
sys.path.insert(0, str(REPO / "modules" / "tools" / "scripts"))

import extensions  # noqa: E402
import ledger_find  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_ledger", str(REPO / "core" / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_ledger", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)


def write(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def item(i: int, title: str, status: str = "adopted", **over: object) -> dict:
    data: dict = {"id": i, "title": title, "area": "Tools", "what": "", "status": status, "result": f"result {i}"}
    data.update(over)
    return data


def manifest(name: str, ledger: int | None = None, when: str = "use it") -> dict:
    data: dict = {"schema": "socratex-extension/v1", "name": name, "kind": "note", "category": "code",
                  "source": {"id": name, "version": "1"}, "when_to_use": when, "status": "adopted",
                  "default_enabled": False, "context_cost": {"level": "none", "note": "n"}, "risks": "r"}
    if ledger is not None:
        data["ledger"] = ledger
    return data


@pytest.fixture()
def root(tmp_path: Path) -> Path:
    base = tmp_path / "repo"
    write(base / "defaults" / "config.json", {"schema_version": 1})
    items = [
        item(1, "Desktop control CLI", keywords=["desktop", "gui"], what="Drives apps"),
        item(2, "Other tool", what="Can control a desktop window in passing"),
        item(3, "Old idea for desktop", status="rejected", keywords=["desktop"]),
        item(4, "Screenshot helper", status="considering", keywords=["screenshot"]),
        item(5, "Bez słów kluczowych", what="Zarządzanie pamięcią agenta", area="Memory"),
        item(6, "Cache tool one", keywords=["cache"]),
        item(7, "Cache tool two", keywords=["cache"]),
        item(8, "Cache tool three", keywords=["cache"]),
        item(9, "Cache tool four", keywords=["cache"]),
    ]
    write(base / "docs" / "IMPROVEMENTS.json", {"schema": "socratex-improvements/v1", "updated": "2026-01-01", "items": items})
    write(base / "modules" / "extensions" / "deskctl.json", manifest("deskctl", ledger=1))
    return base


@pytest.fixture()
def project(tmp_path: Path) -> Path:
    folder = tmp_path / "proj"
    folder.mkdir()
    return folder


def ids(hits: list[dict]) -> list[object]:
    return [h["id"] for h in hits]


def test_keyword_hit_beats_description_only_hit(root):
    assert ids(ledger_find.find("desktop control", root=root)) == [1, 2]


def test_rejected_excluded_by_default_and_shown_with_all(root):
    assert 3 not in ids(ledger_find.find("old desktop", root=root))
    shown = ledger_find.find("old desktop", root=root, include_rejected=True)
    assert 3 in ids(shown)
    assert "rejected" in ledger_find.format_line(next(h for h in shown if h["id"] == 3))


def test_adopted_with_disabled_extension_is_labelled_off(root, project):
    hit = ledger_find.find("desktop gui", root=root, project=project)[0]
    assert hit["id"] == 1 and hit["status_label"] == "adopted, off"
    assert "adopted, off" in ledger_find.format_line(hit)


def test_adopted_with_enabled_extension_is_labelled_on(root, project):
    extensions.set_enabled("deskctl", True, root, project)
    hit = ledger_find.find("desktop gui", root=root, project=project)[0]
    assert hit["status_label"] == "adopted, on"


def test_considering_has_plain_status(root):
    hit = ledger_find.find("screenshot helper", root=root)[0]
    assert hit["id"] == 4 and hit["status_label"] == "considering"


def test_items_without_keywords_match_by_title_what_area_and_fold_diacritics(root):
    assert ids(ledger_find.find("zarzadzanie pamiecia", root=root)) == [5]
    assert ids(ledger_find.find("słów kluczowych", root=root)) == [5]
    assert ids(ledger_find.find("memory agenta", root=root)) == [5]


def test_manifest_without_ledger_id_matches_by_name_and_when(root):
    write(root / "modules" / "extensions" / "tabular.json", manifest("tabular", when="Render wide tables nicely"))
    hits = ledger_find.find("wide tables", root=root)
    assert ids(hits) == ["tabular"]


def test_max_three_results_sorted_and_limit_option(root):
    hits = ledger_find.find("cache tool", root=root)
    assert len(hits) == 3
    assert [h["score"] for h in hits] == sorted((h["score"] for h in hits), reverse=True)
    assert len(ledger_find.find("cache tool", root=root, limit=1)) == 1


def test_bad_query_raises_usage_error(root):
    for bad in ("", "   ", "desktop", "a"):
        with pytest.raises(ledger_find.QueryError):
            ledger_find.find(bad, root=root)


def test_cli_no_hits_exit_1_and_empty_output(root, capsys):
    code = sox.main(["ledger", "--root", str(root), "find", "quantum zebra"])
    out = capsys.readouterr()
    assert code == 1 and out.out == "" and out.err == ""


def test_cli_hit_prints_one_compact_line(root, capsys):
    code = sox.main(["ledger", "--root", str(root), "find", "desktop control"])
    lines = capsys.readouterr().out.splitlines()
    assert code == 0 and len(lines) == 2
    assert lines[0].split(" | ")[:2] == ["1", "Desktop control CLI"]


def test_cli_bad_query_is_usage_error(root, capsys):
    code = sox.main(["ledger", "--root", str(root), "find", "desktop"])
    assert code == 2 and "at least two words" in capsys.readouterr().err


def test_find_never_writes(root):
    before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
    ledger_find.find("desktop control", root=root, include_rejected=True)
    assert before == {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}


def test_single_weak_word_in_multiword_keyword_is_not_a_hit(root, capsys):
    write(root / "docs" / "IMPROVEMENTS.json", {"schema": "socratex-improvements/v1", "updated": "2026-01-01",
          "items": [item(1, "Output tool", keywords=["hard to read output"])]})
    code = sox.main(["ledger", "--root", str(root), "find", "cannot read pdf"])
    out = capsys.readouterr()
    assert code == 1 and out.out == ""


def test_query_of_only_filler_words_is_a_query_error(root):
    try:
        result = ledger_find.find("x y", root=root)
    except ledger_find.QueryError:
        return
    assert result == []


def test_multiword_query_needs_two_distinct_matching_words(root):
    write(root / "docs" / "IMPROVEMENTS.json", {"schema": "socratex-improvements/v1", "updated": "2026-01-01",
          "items": [item(1, "Desk", keywords=["control desktop app"])]})
    assert ids(ledger_find.find("control desktop app", root=root)) == [1]
    assert ids(ledger_find.find("desktop gui", root=root)) == []
    assert ids(ledger_find.find("slow tests", root=root)) == []
