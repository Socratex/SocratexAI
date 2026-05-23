#!/usr/bin/env python3
"""Update grouped-task handoff state and optional next-subtask prompt."""

from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sys import path as sys_path

sys_path.insert(0, str(Path(__file__).resolve().parents[1] / "repo"))
from repo_tool_helpers import split_values, write_json  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_state(path: Path, task_id: str, group_id: str, subtask_id: str) -> OrderedDict[str, Any]:
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=OrderedDict)
        if not isinstance(data, OrderedDict):
            raise SystemExit(f"Existing handoff file is not a JSON object: {path}")
        return data
    return OrderedDict(
        schema="socratex-grouped-task-handoff/v1",
        metadata=OrderedDict(
            task_id=task_id,
            current_group_id=group_id,
            current_subtask_id=subtask_id,
            updated_at_utc=utc_now(),
            model="User approves groups; subtasks inside an approved group can run automatically through file handoff.",
        ),
        groups=OrderedDict(),
    )


def resolve_path(root: Path, value: str, default_relative: str) -> Path:
    path = Path(value) if value.strip() else root / default_relative
    return path if path.is_absolute() else root / path


def main() -> int:
    parser = argparse.ArgumentParser(description="Write grouped-task handoff JSON.")
    parser.add_argument("--task-id", "-TaskId", required=True)
    parser.add_argument("--group-id", "-GroupId", required=True)
    parser.add_argument("--subtask-id", "-SubtaskId", required=True)
    parser.add_argument("--project-root", "-ProjectRoot", default=".")
    parser.add_argument("--status", "-Status", choices=["planned", "active", "done", "blocked"], default="done")
    parser.add_argument("--group-goal", "-GroupGoal", default="")
    parser.add_argument("--subtask-goal", "-SubtaskGoal", default="")
    parser.add_argument("--handoff-summary", "-HandoffSummary", default="")
    parser.add_argument("--inspected-files", "-InspectedFiles", nargs="*", default=[])
    parser.add_argument("--changed-files", "-ChangedFiles", nargs="*", default=[])
    parser.add_argument("--verification", "-Verification", nargs="*", default=[])
    parser.add_argument("--risks", "-Risks", nargs="*", default=[])
    parser.add_argument("--next-files", "-NextFiles", nargs="*", default=[])
    parser.add_argument("--next-commands", "-NextCommands", nargs="*", default=[])
    parser.add_argument("--next-subtask-id", "-NextSubtaskId", default="")
    parser.add_argument("--next-subtask-goal", "-NextSubtaskGoal", default="")
    parser.add_argument("--handoff-path", "-HandoffPath", default="")
    parser.add_argument("--prompt-path", "-PromptPath", default="")
    parser.add_argument("--no-prompt", "-NoPrompt", action="store_true")
    parser.add_argument("--print-json", "-PrintJson", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).resolve()
    handoff_path = resolve_path(root, args.handoff_path, "docs-tech/cache/grouped_task_handoff.json")
    prompt_path = resolve_path(root, args.prompt_path, "docs-tech/cache/next_subtask_prompt.md")
    state = read_state(handoff_path, args.task_id, args.group_id, args.subtask_id)
    state.setdefault("metadata", OrderedDict())
    state.setdefault("groups", OrderedDict())
    state["metadata"]["task_id"] = args.task_id
    state["metadata"]["current_group_id"] = args.group_id
    state["metadata"]["current_subtask_id"] = args.subtask_id
    state["metadata"]["updated_at_utc"] = utc_now()

    groups = state["groups"]
    if args.group_id not in groups:
        groups[args.group_id] = OrderedDict(goal=args.group_goal, status="active", subtasks=OrderedDict(), handoff_for_next=OrderedDict())
    group = groups[args.group_id]
    if args.group_goal.strip():
        group["goal"] = args.group_goal
    group.setdefault("subtasks", OrderedDict())
    group.setdefault("handoff_for_next", OrderedDict())

    record = OrderedDict(
        id=args.subtask_id,
        status=args.status,
        goal=args.subtask_goal,
        completed_at_utc=utc_now(),
        summary=args.handoff_summary,
        inspected_files=split_values(args.inspected_files),
        changed_files=split_values(args.changed_files),
        verification=split_values(args.verification),
        risks=split_values(args.risks),
        next=OrderedDict(
            subtask_id=args.next_subtask_id,
            goal=args.next_subtask_goal,
            files=split_values(args.next_files),
            commands=split_values(args.next_commands),
        ),
    )
    group["subtasks"][args.subtask_id] = record
    group["handoff_for_next"] = record["next"]
    if args.status == "blocked":
        group["status"] = "blocked"
    elif args.next_subtask_id.strip():
        group["status"] = "active"
    elif args.status == "done":
        group["status"] = "done"

    write_json(handoff_path, state)

    if not args.no_prompt:
        def rel(path: Path) -> str:
            try:
                return path.relative_to(root).as_posix()
            except ValueError:
                return path.as_posix()

        lines = [
            "# Next Grouped Subtask Prompt",
            "",
            f"Task: {args.task_id}",
            f"Group: {args.group_id}",
            f"Previous subtask: {args.subtask_id}",
        ]
        if args.next_subtask_id.strip():
            lines.append(f"Next subtask: {args.next_subtask_id}")
        if args.next_subtask_goal.strip():
            lines.extend(["", f"Next goal: {args.next_subtask_goal}"])
        lines.extend(["", "Read the project startup context by tier, then read:", f"- {rel(handoff_path)}", "", "Previous handoff summary:", args.handoff_summary, "", "Risks to preserve:"])
        lines.extend(f"- {risk}" for risk in split_values(args.risks))
        lines.extend(["", "Suggested files:"])
        lines.extend(f"- {file}" for file in split_values(args.next_files))
        lines.extend(["", "Suggested commands:"])
        lines.extend(f"- {command}" for command in split_values(args.next_commands))
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    if args.print_json:
        print(json.dumps(state, ensure_ascii=False, indent=4))
    else:
        print("OK: grouped task handoff updated")
        print(f"handoff: {handoff_path.relative_to(root).as_posix() if handoff_path.is_relative_to(root) else handoff_path}")
        if not args.no_prompt:
            print(f"next_prompt: {prompt_path.relative_to(root).as_posix() if prompt_path.is_relative_to(root) else prompt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

