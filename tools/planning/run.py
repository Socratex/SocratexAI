#!/usr/bin/env python3
"""Planning pipeline CLI: runs the shared engine (tools/pipeline) with tools/planning/checkers.json and prints the UCE report.

Usage:
    python tools/planning/run.py --answers answers.md --plan plan.md [--research-notes notes.md] [--project-dir DIR]
        [--dry-run] [--keep] [--run-id ID] [--registry PATH] [--report-file PATH]

Stage 1 (questions) is the normal AskUserQuestion form led by the main session and has no code here. This runner
does stage 2 (research: find unknowns that facts can settle, record the executor and the reason) and then stage 3
(check: a cheap agent reads ONLY the owner answers, the plan and the research notes and reports mismatches).
The stages run as two sequential engine invocations; the research decision is fed into the check slice automatically,
and --research-notes replaces it with real research results. Both stages only report: the answers, plan and SPEC.md
files are read, never written.

Form rules that live with the main session, not in code (skill `spec`): at most 4 questions per round with the
recommendation first; with more than 4 gaps ask the 4 that matter and list defaults for the rest as "assumed";
an unanswered question uses the recommendation, marked "assumed" in the plan.

Run files (slice, engine run folders, cost summaries, log) live outside the repo in
<temp>/socratex-pipeline/planning/<run id>/ (base overridable with SOCRATEX_PIPELINE_DIR) and the whole folder is
removed after the run, also after an error. A heartbeat file keeps a live run marked; a folder whose heartbeat is
stale (killed run) is removed by the next run. --keep leaves findings.json and log.jsonl. Entries added in the
project override .ai/planning.json must use absolute script paths without {here}.
Spec: docs/specs/planning-pipeline/SPEC.md
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Put the shared engine and this folder first while importing, then take them off again: the module names here are
# unique, but `run` itself must not shadow the review pipeline's `run` for code imported later.
_added = [str(p) for p in (HERE, HERE.parent / "pipeline") if str(p) not in sys.path]
sys.path[:0] = _added
try:
    import common  # noqa: E402
    import engine  # noqa: E402
    import merge  # noqa: E402
    import planning_report  # noqa: E402
    import stage_files  # noqa: E402
finally:
    for _path in _added:
        sys.path.remove(_path)

DEFAULT_REGISTRY = HERE / "checkers.json"
PIPELINE_NAME = "planning"
INPUT_DIR = "input"
ENGINE_DIR = "engine"
MARKER = ".running"
HEARTBEAT_SECONDS = 15
ORPHAN_SECONDS = 120
RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
STAGE_ORDER = ("research", "check")
LOCAL_TOOLS = ("rg", "serena", "graphify")
EXIT_ALL_SKIPPED = 3
PROMPT = """You are the "{checker}" micro-checker of a planning review. Concern: {concern}
You see ONLY the slice below (lines {start}-{end}): the owner's answers, the plan and optional research notes.
You only report. Never rewrite the plan. Report concrete problems, not style opinions.
Answer with a JSON array and nothing else. Each item: {{"line_start": int, "line_end": int,
"severity": "blocker|major|minor|nit", "confidence": "high|medium|low",
"category": "intent-mismatch|missing-coverage|research-contradiction|suggestion",
"message": "one sentence, what is wrong", "patch": ""}}.
Use "research-contradiction" when a research note contradicts an owner answer (the owner decides).
Use "confidence": "low" when unsure. Empty array when the plan matches the answers.
Hint from the pre-filter: {hint}

```
{code}
```
"""


class InputError(ValueError):
    """The answers or plan file is missing or unusable, or the run id is bad or taken."""


def script_of(command: str, here: Path) -> Path | None:
    """The script file a select or fix command runs (first argument after the interpreter), if it names one."""
    tokens = common.expand_command(command, here)
    return next((Path(t) for t in tokens[1:] if not t.startswith("-") and t.endswith((".py", ".sh", ".js"))), None)


def preflight(registry: dict, registry_dir: Path, tool_available) -> None:
    """Fail with the entry id when an enabled entry has no stage, a missing tool, or a select/fix script that is missing
    or would resolve differently at run time (the engine runs from the run folder, not from the project)."""
    for checker in registry["checkers"]:
        if not checker["enabled"]:
            continue
        label = f"checker {checker['id']!r}"
        if not checker.get("stage"):
            raise common.RegistryError(f"{label}: planning entries need a stage")
        if checker["tool"] in LOCAL_TOOLS and not tool_available(checker["tool"]):
            raise common.RegistryError(f"{label}: tool {checker['tool']!r} is not available")
        added = checker["here"] != registry_dir
        for field in ("select", "fix_script"):
            command = checker.get(field)
            if not command:
                continue
            if added and "{here}" in command:
                raise common.RegistryError(f"{label}: {field} of a project-added entry must not use {{here}}; use an absolute path")
            script = script_of(command, checker["here"])
            if script is None:
                continue
            if not script.is_absolute():
                raise common.RegistryError(f"{label}: {field} script {script.as_posix()!r} must be an absolute path or use {{here}}")
            if not script.is_file():
                raise common.RegistryError(f"{label}: {field} script {script.name!r} does not exist")


def sweep_orphans(pipeline_dir: Path) -> None:
    """Remove run folders of killed runs: a heartbeat file that has not been touched for ORPHAN_SECONDS."""
    if not pipeline_dir.is_dir():
        return
    limit = time.time() - ORPHAN_SECONDS
    for child in pipeline_dir.iterdir():
        marker = child / MARKER
        if child.is_dir() and marker.is_file() and marker.stat().st_mtime < limit:
            shutil.rmtree(child, ignore_errors=True)


class Heartbeat:
    """Touches the run's marker file every HEARTBEAT_SECONDS so a live run is never mistaken for an orphan."""

    def __init__(self, marker: Path) -> None:
        self.marker = marker
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def touch(self) -> None:
        try:
            self.marker.write_text(str(time.time()), encoding="utf-8")
        except OSError:
            pass

    def _loop(self) -> None:
        while not self._stop.wait(HEARTBEAT_SECONDS):
            self.touch()

    def start(self) -> None:
        self.touch()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join()


def read_input(path: str | Path, label: str, base: Path, required: bool = True) -> str:
    full = Path(path) if Path(path).is_absolute() else base / path
    if not full.is_file():
        raise InputError(f"{label} file not found: {path}")
    text = full.read_bytes().decode("utf-8", errors="replace")
    if required and not text.strip():
        raise InputError(f"{label} file is empty: {path}")
    return text


def write_slice(staging: Path, parts: dict[str, str]) -> None:
    """(Re)write the check slice: owner answers, plan and research notes, never the conversation."""
    (staging / stage_files.SLICE).write_text(stage_files.build_slice(parts), encoding="utf-8", newline="\n")


def stage_run(run_dir: Path, project_dir: Path, parts: dict[str, str]) -> Path:
    """Write the input files and the project override into <run dir>/input; returns that folder."""
    staging = run_dir / INPUT_DIR
    staging.mkdir(parents=True, exist_ok=True)
    for name, text in parts.items():
        (staging / name).write_text(text, encoding="utf-8", newline="\n")
    write_slice(staging, parts)
    override = project_dir / common.override_path(PIPELINE_NAME)
    if override.is_file():
        target = staging / common.override_path(PIPELINE_NAME)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(override, target)
    return staging


def new_run_id() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:6]


def check_run_id(run_id: str) -> str:
    if not RUN_ID_PATTERN.match(run_id) or ".." in run_id:
        raise InputError(f"bad run id {run_id!r}: use letters, digits, '.', '_' and '-' only (no separators, no '..')")
    return run_id


def quiet_err(text: str) -> None:
    """Engine progress lines go to stderr; the review-only routing hint is dropped."""
    if not text.startswith("Router log:"):
        print(text.replace("Review ", "Planning ", 1), file=sys.stderr)


def stages_of(registry: dict) -> list[str]:
    """Stages that have an enabled entry: research, then check, then any project-added stage in order of appearance."""
    present = [c["stage"] for c in registry["checkers"] if c["enabled"]]
    extras = [s for s in dict.fromkeys(present) if s not in STAGE_ORDER]
    return [s for s in STAGE_ORDER if s in present] + extras


def research_notes_from(doc: dict, research_ids: set[str]) -> str | None:
    """The research decision (unknowns, executor, reason) as notes for the check slice."""
    rows = [f"- {f['message']}" for f in doc["findings"] if f["checker"] in research_ids]
    return "Research decision (who settles which unknown):\n" + "\n".join(rows) if rows else None


def run_planning(project_dir, answers, plan, *, research_notes=None, registry_path=None, run_id: str | None = None,
                 dry_run: bool = False, keep: bool = False, work_base: Path | str | None = None, model=None,
                 tool_available=None, out=print, err=None) -> dict:
    """Run research, then the check; returns {exit_code, run_dir, disabled, plan?, doc?, message?}.

    Raises common.RegistryError for a bad registry or missing tool/script, InputError for bad input, a bad run id or
    a used run id. exit_code is EXIT_ALL_SKIPPED when every input file was skipped.
    """
    if run_id is not None:
        check_run_id(run_id)
    project_dir = Path(project_dir).resolve()
    registry_path = Path(registry_path or DEFAULT_REGISTRY)
    available = tool_available or (lambda name: shutil.which(name) is not None)
    parts = {stage_files.ANSWERS: read_input(answers, "answers", project_dir, required=False),
             stage_files.PLAN: read_input(plan, "plan", project_dir)}
    notes_override = read_input(research_notes, "research notes", project_dir) if research_notes else None
    registry = common.load_registry(registry_path, project_dir)
    preflight(registry, registry_path.resolve().parent, available)
    disabled = sorted(c["id"] for c in registry["checkers"] if not c["enabled"])
    research_ids = {c["id"] for c in registry["checkers"] if c["stage"] == "research"}
    pipeline_dir = engine.work_root(work_base) / registry["pipeline"]
    sweep_orphans(pipeline_dir)
    engine.prune_stale(pipeline_dir)
    run_id = check_run_id(run_id or new_run_id())
    run_dir = pipeline_dir / run_id
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    try:
        run_dir.mkdir()
    except FileExistsError:
        raise InputError(f"run id {run_id!r} is already in use; every run needs its own run id") from None
    beat = Heartbeat(run_dir / MARKER)
    beat.start()
    log = common.RunLog(run_dir / "log.jsonl")
    finished = False
    try:
        staging = stage_run(run_dir, project_dir, parts)
        if notes_override:
            parts[stage_files.RESEARCH] = notes_override
            write_slice(staging, parts)
        docs: list[dict] = []
        plans: list[dict] = []
        outcome = {"exit_code": 0}
        for stage in stages_of(registry):
            beat.touch()
            log.event("stage_start", stage=stage)
            result = engine.run_pipeline(
                registry_path, staging, [stage_files.ANSWERS, stage_files.PLAN, stage_files.SLICE], run_id=run_id,
                dry_run=dry_run, min_changed_lines=0, fix=False, keep=True, work_base=run_dir / ENGINE_DIR / stage,
                model=model or engine.default_model, tool_available=available, out=out, err=err or quiet_err,
                stage=stage, prompt=PROMPT)
            log.event("stage_end", stage=stage)
            if "doc" not in result and "plan" not in result:
                outcome = {"exit_code": EXIT_ALL_SKIPPED, "message": "all input files were skipped (see skip_patterns "
                                                                      "in the registry); nothing was checked"}
                break
            outcome["exit_code"] = max(outcome["exit_code"], result["exit_code"])
            if "doc" in result:
                docs.append(result["doc"])
                if stage == STAGE_ORDER[0] and not notes_override:
                    notes = research_notes_from(result["doc"], research_ids)
                    if notes:
                        parts[stage_files.RESEARCH] = notes
                        write_slice(staging, parts)
            if "plan" in result:
                plans += result["plan"]
        if docs:
            doc = {"schema": merge.DOC_SCHEMA, "run_id": run_id, "rounds": 0,
                   "checkers": [c for d in docs for c in d["checkers"]], "findings": [f for d in docs for f in d["findings"]]}
            merge.write_document(run_dir, doc)
            outcome["doc"] = doc
        if dry_run and plans:
            outcome["plan"] = plans
        finished = True
    finally:
        beat.stop()
        if dry_run or not keep or not finished:
            shutil.rmtree(run_dir, ignore_errors=True)
    (run_dir / MARKER).unlink(missing_ok=True)
    outcome["run_dir"] = run_dir if run_dir.exists() else None
    outcome["disabled"] = disabled
    return outcome


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Run the planning pipeline (research decision, then interpretation check).")
    parser.add_argument("--answers", required=True, help="File with the owner's answers (read only).")
    parser.add_argument("--plan", required=True, help="Plan file to check (read only, never changed).")
    parser.add_argument("--research-notes", help="Research notes to use in the check instead of the automatic decision notes.")
    parser.add_argument("--project-dir", default=".")
    parser.add_argument("--run-id", help="Letters, digits, '.', '_' and '-' only.")
    parser.add_argument("--registry", help="Registry path (default: tools/planning/checkers.json).")
    parser.add_argument("--dry-run", action="store_true", help="Show the research decision and predicted model calls only.")
    parser.add_argument("--keep", action="store_true", help="Keep the run folder (findings.json, log) after the run.")
    parser.add_argument("--report-file", help="Also write the UCE report to this file.")
    args = parser.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = run_planning(args.project_dir, args.answers, args.plan, research_notes=args.research_notes,
                              registry_path=args.registry, run_id=args.run_id, dry_run=args.dry_run, keep=args.keep)
    except (common.RegistryError, merge.SchemaError, InputError) as err:
        print(f"planning: {err}", file=sys.stderr)
        return 2
    if result.get("message"):
        print(f"planning: {result['message']}", file=sys.stderr)
    if result.get("doc"):
        text = planning_report.render(result["doc"], result["disabled"])
        print(text)
        if args.report_file:
            Path(args.report_file).write_text(text + "\n", encoding="utf-8", newline="\n")
        if result.get("run_dir"):
            print(f"Run files kept in: {result['run_dir']}", file=sys.stderr)
    elif result.get("plan") is not None:
        print(planning_report.render_plan(result["plan"], result["disabled"]))
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
