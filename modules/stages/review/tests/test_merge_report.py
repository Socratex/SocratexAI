"""Criteria 5, 6, 13, 14: the merger, the UCE report and the wiring into directives and index."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

import common
import merge
import report

ROOT = Path(__file__).resolve().parents[4]


def finding(fid, checker="comments", file="a.py", start=1, end=3, severity="minor", category="stale", **extra):
    base = {"id": fid, "checker": checker, "file": file, "line_start": start, "line_end": end, "severity": severity,
            "kind": "judgment", "confidence": "high", "message": "Something is off.", "fix": {"type": "none",
            "command_or_patch": ""}, "status": "open", "category": category}
    base.update(extra)
    return base


def by_id(items):
    return {f["id"]: f for f in items}


def test_overlapping_same_category_is_merged_keeping_higher_severity():
    merged = by_id(merge.dedupe([finding("a-1", severity="minor", start=1, end=5),
                                 finding("b-1", checker="readability", severity="major", start=4, end=8)]))
    assert merged["b-1"]["status"] == "open" and merged["a-1"]["status"] == "superseded"
    assert merged["a-1"]["superseded_by"] == "b-1"
    assert (merged["b-1"]["line_start"], merged["b-1"]["line_end"]) == (1, 8)


def test_different_category_file_or_distant_lines_are_not_merged():
    items = [finding("a-1"), finding("a-2", category="other"), finding("a-3", file="b.py"),
             finding("a-4", start=10, end=12)]
    assert {f["status"] for f in merge.dedupe(items)} == {"open"}


def test_split_chunk_boundary_findings_are_merged_when_adjacent():
    parts = [finding("a-1", start=1, end=10, chunk_split=True), finding("a-2", start=11, end=14, chunk_split=True)]
    merged = by_id(merge.dedupe(parts))
    assert sorted(f["status"] for f in merged.values()) == ["open", "superseded"]
    kept = [f for f in merged.values() if f["status"] == "open"][0]
    assert (kept["line_start"], kept["line_end"]) == (1, 14)
    plain = [finding("a-1", start=1, end=10), finding("a-2", start=11, end=14)]
    assert {f["status"] for f in merge.dedupe(plain)} == {"open"}


def test_equal_severity_keeps_higher_confidence_then_earlier():
    merged = by_id(merge.dedupe([finding("a-1", confidence="low"), finding("b-1", confidence="high")]))
    assert merged["b-1"]["status"] == "open" and merged["a-1"]["status"] == "superseded"


def test_merge_run_reads_only_checker_files_and_validates(tmp_path):
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    for name, row in (("comments", finding("comments-1")), ("readability", finding("readability-1", severity="major",
                                                                                      checker="readability"))):
        (run_dir / f"{name}.json").write_text(json.dumps({"checker": name, "status": "done", "tier": "cheap",
                                                          "cost": {"model_calls": 1}, "findings": [row]}), encoding="utf-8")
    (run_dir / "log.jsonl").write_text("{}\n", encoding="utf-8")
    doc = merge.merge_run(run_dir, "r")
    assert (run_dir / "findings.json").exists() and merge.validate(doc) == []
    assert sorted(f["status"] for f in doc["findings"]) == ["open", "superseded"]
    assert {c["id"] for c in doc["checkers"]} == {"comments", "readability"}


def test_invalid_document_is_rejected_by_schema():
    doc = {"schema": "socratex-review-findings/v1", "run_id": "r", "rounds": 0, "checkers": [],
           "findings": [finding("a-1", severity="catastrophic")]}
    assert merge.validate(doc)
    with pytest.raises(merge.SchemaError):
        merge.write_document(Path("unused"), doc)


def sample_doc():
    rows = [finding("comments-1", file="src/secret_dir/app.py", status="fixed"),
            finding("comments-2", file="src/secret_dir/app.py", severity="major", start=20, end=30),
            finding("readability-1", checker="readability", file="lib/util.py", severity="blocker", start=5, end=9),
            finding("contracts-1", checker="contracts", file="lib/io.py", status="reported",
                    note="fix broke the gate; reverted")]
    checkers = [{"id": "comments", "status": "done", "tier": "cheap", "model_calls": 2, "input_chunks": 2,
                 "input_lines": 20}, {"id": "architecture", "status": "skipped", "reason": "tool graphify unavailable",
                                      "tier": "standard", "model_calls": 0, "input_chunks": 0, "input_lines": 0}]
    return {"schema": "socratex-review-findings/v1", "run_id": "20261121-101500", "rounds": 2, "checkers": checkers,
            "findings": rows}


def test_report_is_uce_without_paths_or_ids():
    doc = sample_doc()
    text = report.render(doc)
    lines = [line for line in text.splitlines() if line.strip()]
    assert not lines[0][0].isascii(), "first line starts with an emoji"
    bullets = lines[1:]
    assert 3 <= len(bullets) <= 6
    assert all(not line[0].isascii() for line in bullets), "every line starts with an emoji"
    questions = [line for line in lines if "❓" in line]
    assert len(questions) <= 1 and (not questions or lines[-1] == questions[0])
    for forbidden in ("src/secret_dir", "app.py", "util.py", "comments-1", "readability-1", "20261121", "/", "\\"):
        assert forbidden not in text, forbidden


def test_report_for_clean_run_has_no_question_and_still_three_bullets():
    doc = {"schema": "socratex-review-findings/v1", "run_id": "r", "rounds": 0, "checkers": [], "findings": []}
    lines = [line for line in report.render(doc).splitlines() if line.strip()]
    assert 4 <= len(lines) <= 7 and not any("❓" in line for line in lines)


def test_report_cli_reads_findings_file(tmp_path, capsys):
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(sample_doc()), encoding="utf-8")
    assert report.main([str(path)]) == 0
    assert capsys.readouterr().out.strip()


def test_directives_has_review_row_and_index_lists_new_tools_and_doc():
    directives = json.loads((ROOT / "core" / "DIRECTIVES.json").read_text(encoding="utf-8"))
    rows = [r for r in directives["rows"] if "modules/stages/review/run.py" in r["follow"]]
    assert rows and "SPEC.md" in rows[0]["follow"]
    index = json.loads((ROOT / "INDEX.json").read_text(encoding="utf-8"))
    tool_paths = {t["path"] for t in index["tools"]}
    assert {"modules/stages/review/run.py", "modules/stages/review/report.py", "modules/engine/engine.py",
            "modules/engine/merge.py", "modules/engine/common.py"} <= tool_paths
    assert "modules/stages/review/tests/conftest.py" not in tool_paths
    assert any(d["path"] == "docs/specs/review-pipeline/SPEC.md" for d in index["docs"])
    assert any(d["path"] == "modules/stages/review/checkers.json" for d in index["data"])
    assert any(d["path"] == "modules/engine/findings.schema.json" for d in index["data"])


def test_index_is_current():
    sys.path.insert(0, str(ROOT / "modules" / "tools" / "scripts"))
    import build_index
    expected = json.dumps(build_index.build(), indent=2, ensure_ascii=False) + "\n"
    assert (ROOT / "INDEX.json").read_text(encoding="utf-8") == expected


def test_no_private_references_in_review_files():
    sys.path.insert(0, str(ROOT / "modules" / "tools" / "scripts"))
    import check_leaks
    files = [p for folder in ("stages/review", "engine") for p in (ROOT / "modules" / folder).rglob("*")
             if p.is_file() and "__pycache__" not in p.parts]
    files += list((ROOT / "docs" / "specs" / "review-pipeline").glob("*.md"))
    assert check_leaks.scan(files, check_leaks.patterns()) == []


def test_report_script_prints_utf8_even_on_a_legacy_console(tmp_path):
    import subprocess
    path = tmp_path / "findings.json"
    path.write_text(json.dumps(sample_doc()), encoding="utf-8")
    done = subprocess.run([sys.executable, str(ROOT / "modules" / "stages" / "review" / "report.py"), str(path)], capture_output=True,
                          env={**__import__("os").environ, "PYTHONIOENCODING": "cp1250", "PYTHONUTF8": "0"})
    assert done.returncode == 0 and done.stdout.decode("utf-8").startswith("❌")
