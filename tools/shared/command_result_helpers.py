#!/usr/bin/env python3
"""Shared command step result contract for SocratexPipeline tools."""

from __future__ import annotations

import json
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


STEP_RESULT_SCHEMA = "socratex-command-step-result/v1"
DEFAULT_TAIL_LIMIT = 1800


@dataclass(frozen=True)
class CommandStep:
    step_id: str
    label: str
    command: list[str]
    cwd: Path
    required: bool = True
    recovery_hint: str = ""
    artifact_path: Path | str | None = None
    skip_ok: bool = True


@dataclass
class CommandResult:
    step_id: str
    label: str
    command: list[str]
    cwd: Path
    exit_code: int | None
    required: bool = True
    elapsed_seconds: float = 0.0
    skipped: bool = False
    skip_ok: bool = True
    reason: str = ""
    stdout_tail: str = ""
    stderr_tail: str = ""
    recovery_hint: str = ""
    artifact_path: str = ""

    @property
    def ok(self) -> bool:
        return (self.skipped and self.skip_ok) or self.exit_code == 0

    @property
    def status(self) -> str:
        return command_result_status(self.exit_code, self.skipped, skip_ok=self.skip_ok)


def output_tail(text: str, limit: int = DEFAULT_TAIL_LIMIT) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[-limit:]


def command_result_status(exit_code: int | None, skipped: bool, *, skip_ok: bool = True) -> str:
    if skipped:
        return "skipped" if skip_ok else "fail"
    return "pass" if exit_code == 0 else "fail"


def command_result_payload(result: CommandResult) -> dict[str, Any]:
    return {
        "schema": STEP_RESULT_SCHEMA,
        "id": result.step_id,
        "label": result.label,
        "command": result.command,
        "cwd": str(result.cwd),
        "required": result.required,
        "skipped": result.skipped,
        "skip_ok": result.skip_ok,
        "reason": result.reason,
        "exit_code": result.exit_code,
        "status": result.status,
        "elapsed_seconds": round(result.elapsed_seconds, 2),
        "stdout_tail": result.stdout_tail,
        "stderr_tail": result.stderr_tail,
        "recovery_hint": result.recovery_hint,
        "artifact_path": result.artifact_path,
    }


def command_result_from_step(
    step: CommandStep,
    *,
    exit_code: int | None,
    skipped: bool,
    reason: str = "",
    elapsed_seconds: float = 0.0,
    stdout: str = "",
    stderr: str = "",
) -> CommandResult:
    return CommandResult(
        step_id=step.step_id,
        label=step.label,
        command=step.command,
        cwd=step.cwd,
        exit_code=exit_code,
        required=step.required,
        elapsed_seconds=elapsed_seconds,
        skipped=skipped,
        skip_ok=step.skip_ok,
        reason=reason,
        stdout_tail=output_tail(stdout),
        stderr_tail=output_tail(stderr),
        recovery_hint=step.recovery_hint,
        artifact_path=str(step.artifact_path) if step.artifact_path else "",
    )


def run_command_step(
    step: CommandStep,
    *,
    execute: bool,
    skip_reason: str = "dry-run",
    env: dict[str, str] | None = None,
) -> CommandResult:
    if not execute:
        return command_result_from_step(
            step,
            exit_code=None,
            skipped=True,
            reason=skip_reason,
        )
    started = time.monotonic()
    completed = subprocess.run(
        step.command,
        cwd=str(step.cwd),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return command_result_from_step(
        step,
        exit_code=completed.returncode,
        skipped=False,
        elapsed_seconds=time.monotonic() - started,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def write_json_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")
