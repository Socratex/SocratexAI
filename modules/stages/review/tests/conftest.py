"""Shared fixtures: a throwaway git repo, a counting fake model and a fake implementer."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REVIEW_DIR = Path(__file__).resolve().parents[1]
PIPELINE_DIR = REVIEW_DIR.parents[1] / "engine"
REGISTRY_PATH = REVIEW_DIR / "checkers.json"
sys.path.insert(0, str(REVIEW_DIR))
sys.path.insert(0, str(PIPELINE_DIR))
sys.path.insert(0, str(REVIEW_DIR.parents[2] / "modules" / "tools" / "scripts"))

APP_V1 = "def add(a, b):\n    return a + b\n"
APP_V2_COMMENTS = (
    "def add(a, b):\n    return a + b\n\n\n"
    "def total(items):\n"
    "    # old = sum(items)\n"
    "    result = sum(items)\n"
    "    # return the result\n"
    "    return result\n"
)
APP_V2_PLAIN = APP_V1 + "\n\ndef double(x):\n    return x * 2\n"
APP_V2_JUDGE = APP_V1 + "\n\ndef double(x):\n    # keeps totals in sync with the ledger\n    return x * 2\n"
SELECT_ALL = REVIEW_DIR / "tests" / "select_all.py"
SELECT_FAIL = REVIEW_DIR / "tests" / "select_fail.py"


class Repo:
    def __init__(self, path: Path, work: Path) -> None:
        self.path = path
        self.work = work

    def git(self, *args: str) -> str:
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.path,
                              capture_output=True, text=True, encoding="utf-8", check=True)
        return done.stdout

    def write(self, rel: str, text: str | bytes) -> Path:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            target.write_bytes(text)
        else:
            target.write_bytes(text.encode("utf-8"))
        return target

    def read(self, rel: str) -> str:
        return (self.path / rel).read_bytes().decode("utf-8")

    def commit_all(self, message: str = "c") -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def log_events(self, run_id: str) -> list[dict]:
        path = self.run_dir(run_id) / "log.jsonl"
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def run_dir(self, run_id: str) -> Path:
        return self.work / "review" / run_id


@pytest.fixture
def repo(tmp_path: Path, monkeypatch) -> Repo:
    root = tmp_path / "proj"
    root.mkdir()
    work = tmp_path / "work"
    monkeypatch.setenv("SOCRATEX_PIPELINE_DIR", str(work))
    import common
    monkeypatch.setattr(common, "LOCAL_DIR", tmp_path / "local")
    made = Repo(root, work)
    made.git("init", "-q")
    made.git("config", "core.autocrlf", "false")
    made.write("app.py", APP_V1)
    made.commit_all("init")
    return made


class FakeModel:
    """Counts calls; the responder maps a request dict to the raw model text."""

    def __init__(self, responder=None) -> None:
        self.calls: list[dict] = []
        self.responder = responder or (lambda request: "[]")

    def __call__(self, request: dict) -> str:
        self.calls.append(request)
        return self.responder(request)

    def by_checker(self, checker: str) -> list[dict]:
        return [call for call in self.calls if call["checker"] == checker]


def model_finding(request: dict, **overrides) -> str:
    row = {"line_start": request["line_start"], "line_end": request["line_end"], "severity": "minor",
           "kind": "judgment", "confidence": "high", "category": "stale-comment",
           "message": "Comment no longer matches the code."}
    row.update(overrides)
    return json.dumps([row])


class FakeImplementer:
    """Records calls; the action edits the file (or not) to simulate a fix."""

    def __init__(self, action=None, delay: float = 0.0) -> None:
        self.calls: list[dict] = []
        self.action = action
        self.delay = delay

    def __call__(self, request: dict) -> None:
        self.calls.append(request)
        if self.delay:
            time.sleep(self.delay)
        if self.action:
            self.action(Path(request["project_dir"]) / request["file"], request)


def always_ok(project_dir) -> tuple[bool, str]:
    return True, ""


def all_tools(name: str) -> bool:
    return True


@pytest.fixture
def run_kwargs() -> dict:
    return {"min_changed_lines": 0, "tool_available": all_tools, "gate": always_ok}
