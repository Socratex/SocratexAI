"""Test kit and the `project` fixture. There is no conftest.py here on purpose: the review tests import the module
named conftest, so a second conftest in another folder would shadow theirs."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

PLANNING_DIR = Path(__file__).resolve().parents[1]
PIPELINE_DIR = PLANNING_DIR.parents[1] / "engine"
REGISTRY_PATH = PLANNING_DIR / "checkers.json"
sys.path.append(str(PIPELINE_DIR))
sys.path.append(str(PLANNING_DIR))


def load_module(name: str, path: Path):
    """Load a module under a unique name, so same-named review modules (run, report) never collide."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


planning_run = load_module("planning_run", PLANNING_DIR / "run.py")

ANSWERS = "Q: Which storage? A: SQLite\nQ: Target platform? A: Windows only\n"
PLAN = (
    "# Plan\n"
    "- Use SQLite for storage.\n"
    "- Unknown: which version of the sqlite library supports JSON functions (check the docs)?\n"
    "- Unknown: where does the repo define the config loader function?\n"
    "- Ship for Windows and Linux.\n"
)
PLAN_NO_UNKNOWNS = "# Plan\n- Use SQLite for storage.\n- Ship for Windows only.\n"


class Project:
    def __init__(self, path: Path, work: Path) -> None:
        self.path = path
        self.work = work

    def git(self, *args: str) -> str:
        done = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", *args], cwd=self.path,
                              capture_output=True, text=True, encoding="utf-8", check=True)
        return done.stdout

    def write(self, rel: str, text: str) -> Path:
        target = self.path / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(text.encode("utf-8"))
        return target

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def run_dir(self, run_id: str) -> Path:
        return self.work / "planning" / run_id


@pytest.fixture
def project(tmp_path: Path, monkeypatch) -> Project:
    work = tmp_path / "work"
    monkeypatch.setenv("SOCRATEX_PIPELINE_DIR", str(work))
    monkeypatch.setenv("PLANNING_CODEX_AVAILABLE", "1")
    import common
    monkeypatch.setattr(common, "LOCAL_DIR", tmp_path / "local")
    made = Project(tmp_path / "proj", work)
    made.path.mkdir()
    made.git("init", "-q")
    made.git("config", "core.autocrlf", "false")
    made.write("answers.md", ANSWERS)
    made.write("plan.md", PLAN)
    made.write("SPEC.md", "# Spec\nUntouched.\n")
    made.git("add", "-A")
    made.git("commit", "-q", "-m", "init")
    return made


class FakeModel:
    """Counts calls; the responder maps a request dict to the raw model text."""

    def __init__(self, responder=None) -> None:
        self.calls: list[dict] = []
        self.responder = responder or (lambda request: "[]")

    def __call__(self, request: dict) -> str:
        self.calls.append(request)
        return self.responder(request)


def all_tools(name: str) -> bool:
    return True


def go(project: Project, *, run_id: str | None = "r1", answers: str = "answers.md", plan: str = "plan.md",
       **kwargs) -> dict:
    kwargs.setdefault("model", FakeModel())
    kwargs.setdefault("tool_available", all_tools)
    return planning_run.run_planning(project.path, answers, plan, run_id=run_id, **kwargs)
