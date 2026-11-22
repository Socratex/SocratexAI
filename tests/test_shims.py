"""Tests for the tools/ redirect shims and `sox shims`: forwarding, usage log, failure silence, template drift."""

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

import shims  # noqa: E402

_loader = importlib.machinery.SourceFileLoader("sox_cli_shims", str(CORE_DIR / "sox"))
_spec = importlib.util.spec_from_loader("sox_cli_shims", _loader)
sox = importlib.util.module_from_spec(_spec)
_loader.exec_module(sox)

TARGET_BODY = "import sys\nprint('args:' + ','.join(sys.argv[1:]))\nsys.exit(7)\n"


def fake_root(tmp_path: Path, name: str = "risk_score") -> Path:
    """A repo-shaped folder with one shim and a tiny target script that echoes its args and exits 7."""
    (tmp_path / "tools").mkdir()
    (tmp_path / "tools" / f"{name}.py").write_text(shims.render(name), encoding="utf-8")
    target = tmp_path / "modules" / "tools" / "scripts"
    target.mkdir(parents=True)
    (target / f"{name}.py").write_text(TARGET_BODY, encoding="utf-8")
    return tmp_path


def run_shim(root: Path, name: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-B", str(root / "tools" / f"{name}.py"), *args], capture_output=True, text=True)


def test_shims_in_repo_match_the_template():
    assert shims.problems() == []


def test_every_shim_marks_its_target():
    for name in shims.SHIM_NAMES:
        text = (REPO / "tools" / f"{name}.py").read_text(encoding="utf-8")
        assert f"# REDIRECT to modules/tools/scripts/{name}.py; kept for external callers" in text
        assert len(text.splitlines()) <= 20


def test_shim_forwards_argv_and_exit_code(tmp_path):
    root = fake_root(tmp_path)
    result = run_shim(root, "risk_score", "--commit", "HEAD")
    assert result.returncode == 7
    assert "args:--commit,HEAD" in result.stdout


def test_shim_appends_one_usage_line_per_call(tmp_path):
    root = fake_root(tmp_path)
    run_shim(root, "risk_score")
    run_shim(root, "risk_score", "x")
    rows = [json.loads(line) for line in (root / "state" / "shim-usage.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [r["shim"] for r in rows] == ["risk_score", "risk_score"]
    assert set(rows[0]) == {"ts", "shim", "argv0"}
    assert rows[0]["argv0"].endswith("risk_score.py")


def test_shim_never_fails_when_state_is_unwritable(tmp_path):
    root = fake_root(tmp_path)
    (root / "state").write_text("a file where the folder should be", encoding="utf-8")
    result = run_shim(root, "risk_score", "a")
    assert result.returncode == 7 and "args:a" in result.stdout
    assert result.stderr == ""


def test_usage_counts_per_shim_and_skips_bad_lines(tmp_path):
    state = tmp_path / "state"
    state.mkdir()
    lines = [json.dumps({"ts": "2026-01-01 10:00:00", "shim": "backup", "argv0": "tools/backup.py"}),
             "not json", json.dumps({"ts": "2026-01-02 10:00:00", "shim": "backup", "argv0": "/x/tools/backup.py"}),
             json.dumps({"shim": "unknown"}), json.dumps({"ts": "t", "shim": "update", "argv0": "u"})]
    (state / "shim-usage.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    counts = shims.usage(tmp_path)
    assert counts["backup"]["calls"] == 2 and counts["backup"]["last"] == "2026-01-02 10:00:00"
    assert counts["backup"]["callers"] == ["tools/backup.py", "/x/tools/backup.py"]
    assert counts["update"]["calls"] == 1 and counts["risk_score"]["calls"] == 0


def test_problems_reports_missing_edited_and_stray_files(tmp_path):
    root = fake_root(tmp_path)
    (root / "tools" / "risk_score.py").write_text("# edited\n", encoding="utf-8")
    (root / "tools" / "stray.py").write_text("x", encoding="utf-8")
    found = shims.problems(root)
    assert "shim differs from its template: tools/risk_score.py" in found
    assert "unexpected file in tools/: stray.py" in found
    assert "missing shim: tools/backup.py" in found


def test_regenerate_writes_every_shim_once(tmp_path):
    changed = shims.regenerate(tmp_path)
    assert len(changed) == len(shims.SHIM_NAMES)
    assert shims.regenerate(tmp_path) == []


def test_sox_shims_lists_and_counts(monkeypatch, tmp_path, capsys):
    (tmp_path / "state").mkdir()
    (tmp_path / "state" / "shim-usage.jsonl").write_text(
        json.dumps({"ts": "2026-02-03 04:05:06", "shim": "json_read", "argv0": "tools/json_read.py"}) + "\n", encoding="utf-8")
    monkeypatch.setattr(shims, "ROOT", tmp_path)
    assert sox.main(["shims"]) == 0
    both = capsys.readouterr().out
    assert "tools/json_read.py  ->  modules/tools/scripts/json_read.py  calls: 1  last: 2026-02-03 04:05:06" in both
    assert sox.main(["shims", "--list"]) == 0
    listing = capsys.readouterr().out
    assert "->" in listing and "calls:" not in listing
    assert sox.main(["shims", "--usage"]) == 0
    counts = capsys.readouterr().out
    assert "calls: 1" in counts and "->" not in counts
    assert f"{len(shims.SHIM_NAMES) - 1} of {len(shims.SHIM_NAMES)} shims were never called" in counts


def test_sox_shims_regenerate_writes_into_the_root(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(shims, "ROOT", tmp_path)
    assert sox.main(["shims", "--regenerate"]) == 0
    assert f"Rewrote {len(shims.SHIM_NAMES)} shim(s)." in capsys.readouterr().out
    assert shims.problems(tmp_path) == [f"shim target missing: modules/tools/scripts/{n}.py" for n in shims.SHIM_NAMES]


@pytest.mark.parametrize("name", ["json_read", "improvements_check"])
def test_real_shim_runs_the_real_script(name):
    result = subprocess.run([sys.executable, "-B", str(REPO / "tools" / f"{name}.py"), "--help"], capture_output=True, text=True)
    assert result.returncode == 0 and "usage" in result.stdout.lower()


def test_installer_writes_hooks_with_the_new_paths():
    text = (REPO / "modules" / "tools" / "scripts" / "install.py").read_text(encoding="utf-8")
    assert '/modules/tools/scripts/install.py" --sync' in text
    assert '/modules/tools/scripts/check_leaks.py"' in text
    assert '/tools/install.py' not in text.replace("/modules/tools/scripts/install.py", "")
