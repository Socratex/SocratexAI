#!/usr/bin/env python3
"""Thread AUTO CLI: dry-run pilot and explicitly granted native background execution."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from automation.controller import Registry, render_needs  # noqa: E402
from automation.codex_probe import AppServerProbe  # noqa: E402
from automation.native import authorize, control_handoff, scheduler_request, snapshot  # noqa: E402
from automation.roster import complete_inventory, read_roster  # noqa: E402
from utf8_file_helpers import write_utf8_file  # noqa: E402


def read_json(path: str) -> object:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--state-dir", type=Path, help="Local registry directory; default outside the checkout")
    sub = cli.add_subparsers(dest="command", required=True)
    start = sub.add_parser("start", help="Register a thread grant; native mode permits scheduled scoped work")
    start.add_argument("--repo", required=True)
    start.add_argument("--scope", required=True, help="Explicit approved thematic scope, not a new product mandate")
    start.add_argument("--prompt-context", default="", help="Optional user prompt context; empty means all TODO/PROGRESS within the grant")
    start.add_argument("--sources", nargs="+", required=True, help="Approved canonical project-relative source files")
    start.add_argument("--batch-size", type=int, default=3)
    start.add_argument("--mode", choices=("pilot", "native"), default="pilot")
    start.add_argument("--wake-transport", choices=("heartbeat", "manual"), default="manual")
    for name in ("start", "stop", "status", "finalize", "tick", "watch", "probe", "attach-scheduler", "confirm-wake", "report",
                 "native-snapshot", "native-begin", "scheduler-request", "control-handoff", "project-roster", "context", "import-progress", "project-tasks", "use-manual-transport"):
        cmd = start if name == "start" else sub.add_parser(name)
        cmd.add_argument("--thread-id", default=os.environ.get("CODEX_THREAD_ID"), help="Required identity; never guessed from recency")
        if name in {"finalize", "attach-scheduler", "confirm-wake", "native-begin", "control-handoff", "import-progress", "use-manual-transport"}:
            cmd.add_argument("--run-id", required=True)
        if name == "finalize":
            cmd.add_argument("--repo", required=True)
            cmd.add_argument("--report-file", required=True)
        if name in {"tick", "watch", "native-begin"}:
            cmd.add_argument("--snapshot-file", required=True, help="Fresh observation JSON; stale data fails closed")
            cmd.add_argument("--tasks-file", help="Ordered projection JSON array; never a second backlog owner")
        if name == "watch":
            cmd.add_argument("--interval", type=int, default=60)
            cmd.add_argument("--ticks", type=int, default=1, help="Bounded pilot; never an unbounded background loop")
        if name == "probe":
            cmd.add_argument("--codex", default="codex")
            cmd.add_argument("--output", type=Path)
        if name in {"attach-scheduler", "confirm-wake"}:
            cmd.add_argument("--scheduler-id", required=True)
        if name == "native-begin":
            cmd.add_argument("--scheduler-id", help="Required for heartbeat grants; omitted for manual transport")
            cmd.add_argument("--wake-id", required=True)
            cmd.add_argument("--prompt-context", help="Optional narrower context from this human CONTINUE-AUTO prompt")
        if name == "project-tasks":
            cmd.add_argument("--prompt-context", help="Optional current prompt context; defaults to START context")
            cmd.add_argument("--output", type=Path, help="Disposable source-backed projection outside the repository")
        if name == "native-snapshot":
            cmd.add_argument("--threads-file", required=True)
            cmd.add_argument("--limits-file", required=True)
            cmd.add_argument("--observed-at", type=float, required=True)
            cmd.add_argument("--list-limit", type=int, default=1000)
            cmd.add_argument("--interrupted-by-limit", action="store_true")
            cmd.add_argument("--output", type=Path, required=True)
            cmd.add_argument("--roster-file")
            cmd.add_argument("--statuses-file")
        if name == "project-roster":
            cmd.add_argument("--database", type=Path)
            cmd.add_argument("--output", type=Path, required=True)
        if name == "scheduler-request":
            cmd.add_argument("--retry-at", type=float)
            cmd.add_argument("--pause", action="store_true", help="Consume the wake without stopping the AUTO grant")
        if name == "control-handoff":
            cmd.add_argument("--control-thread-id", required=True)
        if name == "context":
            cmd.add_argument("--scheduler-id", help="Trusted heartbeat identity when CODEX_THREAD_ID is unavailable")
        if name == "report":
            cmd.add_argument("--needs-only", action="store_true")
        if name == "import-progress":
            cmd.add_argument("--report-files", nargs="+", required=True)
    return cli


def execute(args: argparse.Namespace) -> object:
    registry = Registry(args.state_dir)
    command = args.command
    if command == "context":
        return registry.context(args.thread_id, args.scheduler_id)
    if not args.thread_id or not args.thread_id.strip():
        raise ValueError("--thread-id is required when CODEX_THREAD_ID is unavailable; never use the latest chat")
    if command == "start":
        from automation.console_scheduler import start_for_grant
        entry = registry.start(args.thread_id, args.repo, args.scope, args.sources, args.batch_size, args.mode, args.prompt_context, args.wake_transport)
        entry["console_scheduler"] = start_for_grant(entry, registry.home, Path(__file__).resolve().parents[2] / "AUTO scheduler.bat")
        return entry
    if command == "status":
        return registry.get(args.thread_id)
    if command == "use-manual-transport":
        return registry.use_manual_transport(args.thread_id, args.run_id)
    if command == "stop":
        result = registry.stop(args.thread_id)
        return {"action": "stopped", "scheduler_id_to_pause": result["scheduler_id"], "run_id": result["run_id"]}
    if command == "attach-scheduler":
        registry.attach_scheduler(args.thread_id, args.run_id, args.scheduler_id)
        return {"action": "scheduler_attached", "dispatch": False}
    if command == "confirm-wake":
        return registry.confirm_wake(args.thread_id, args.run_id, args.scheduler_id)
    if command == "finalize":
        from automation.finalizer import handoff_result
        result = registry.finalize(args.thread_id, args.run_id, read_json(args.report_file), args.repo)
        return handoff_result(registry, args.thread_id, args.run_id, result)
    if command == "report":
        entry = registry.get(args.thread_id)
        from automation.files import paths, progress_record
        if args.needs_only:
            return render_needs(progress_record(entry)["needs"])
        located = paths(registry.home, entry["thread_id"], entry["run_id"])
        return Path(located["summary"]).read_text(encoding="utf-8")
    if command == "import-progress":
        return registry.import_progress(args.thread_id, args.run_id, [(str(Path(path).resolve()), read_json(path)) for path in args.report_files])
    if command == "scheduler-request":
        return scheduler_request(registry.get(args.thread_id), args.retry_at, pause=args.pause)
    if command == "control-handoff":
        return control_handoff(registry, args.thread_id, args.run_id, args.control_thread_id)
    if command == "native-snapshot":
        entry = registry.get(args.thread_id)
        threads = read_json(args.threads_file)
        if bool(args.roster_file) != bool(args.statuses_file):
            raise ValueError("Project roster and native status results are required together")
        if args.roster_file:
            threads = complete_inventory(entry, read_json(args.roster_file), read_json(args.statuses_file), threads, time.time())
        result = snapshot(entry, threads, read_json(args.limits_file),
                          args.observed_at, args.list_limit, args.interrupted_by_limit)
        write_utf8_file(args.output, json.dumps(result, ensure_ascii=False, indent=4))
        return {"action": "native_observation_saved", "path": str(args.output)}
    if command == "project-roster":
        result = read_roster(registry.get(args.thread_id)["repo"], args.database)
        write_utf8_file(args.output, json.dumps(result, ensure_ascii=False, indent=4))
        return {"action": "project_identities_saved", "count": len(result["threads"]), "path": str(args.output)}
    if command == "project-tasks":
        if not Path(__file__).with_name("projection.py").exists():
            raise ValueError("No project task-export adapter installed; supply a source-backed --tasks-file to native-begin")
        from automation.projection import build_projection
        result = build_projection(registry.get(args.thread_id), args.prompt_context)
        if args.output:
            write_utf8_file(args.output, json.dumps(result, ensure_ascii=False, indent=4))
            return {"action": "task_projection_saved", "path": str(args.output), "tasks": len(result["tasks"]),
                    "feedback_changes": len(result["pending_diff"]["changes"]), "conflicts": len(result["pending_diff"]["conflicts"])}
        return result
    if command == "native-begin":
        tasks = read_json(args.tasks_file) if args.tasks_file else []
        return authorize(registry, args.thread_id, args.run_id, args.scheduler_id, args.wake_id,
                         read_json(args.snapshot_file), tasks, prompt_context=args.prompt_context)
    if command == "probe":
        with AppServerProbe(args.codex) as probe:
            observed = probe.observe(args.thread_id)
        if args.output:
            write_utf8_file(args.output, json.dumps(observed, ensure_ascii=False, indent=4))
        return observed
    if command == "watch" and (args.interval < 60 or not 1 <= args.ticks <= 60):
        raise ValueError("Pilot watch requires interval >=60 seconds and 1..60 ticks")
    results = []
    for index in range(args.ticks if command == "watch" else 1):
        if index:
            time.sleep(args.interval)
        tasks = read_json(args.tasks_file) if args.tasks_file else []
        results.append(registry.tick(args.thread_id, read_json(args.snapshot_file), tasks))
    return results if command == "watch" else results[0]


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    try:
        result = execute(parser().parse_args(argv))
        print(result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=4))
        return 0
    except (ValueError, KeyError, OSError, RuntimeError, TimeoutError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "dispatch": False}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
