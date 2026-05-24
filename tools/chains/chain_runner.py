#!/usr/bin/env python3
"""Shared runner for documented SocratexPipeline command chains."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA = "socratex-chain-report/v1"


@dataclass(frozen=True)
class ChainStep:
    step_id: str
    label: str
    command: list[str]
    cwd: Path
    required: bool = True
    recovery_hint: str = ""
    artifact_path: Path | None = None


def output_tail(text: str, limit: int = 1800) -> str:
    stripped = text.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[-limit:]


def print_step(step: ChainStep, *, dry_run: bool) -> None:
    mode = "DRY-RUN" if dry_run else "RUN"
    required = "required" if step.required else "optional"
    print()
    print(f"{mode}: {step.step_id} - {step.label} ({required})")
    print(f"  cwd: {step.cwd}")
    print(f"  cmd: {' '.join(step.command)}")
    if step.recovery_hint:
        print(f"  recovery_hint: {step.recovery_hint}")


def result_status(exit_code: int | None, skipped: bool) -> str:
    if skipped:
        return "skipped"
    return "pass" if exit_code == 0 else "fail"


def step_result(
    step: ChainStep,
    *,
    exit_code: int | None,
    skipped: bool,
    reason: str = "",
    elapsed_seconds: float = 0.0,
    stdout: str = "",
    stderr: str = "",
) -> dict[str, Any]:
    return {
        "id": step.step_id,
        "label": step.label,
        "command": step.command,
        "cwd": str(step.cwd),
        "required": step.required,
        "skipped": skipped,
        "reason": reason,
        "exit_code": exit_code,
        "status": result_status(exit_code, skipped),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "stdout_tail": output_tail(stdout),
        "stderr_tail": output_tail(stderr),
        "recovery_hint": step.recovery_hint,
        "artifact_path": str(step.artifact_path) if step.artifact_path else "",
    }


def run_step(step: ChainStep, *, dry_run: bool) -> dict[str, Any]:
    print_step(step, dry_run=dry_run)
    if dry_run:
        return step_result(step, exit_code=None, skipped=True, reason="dry-run")
    started = time.monotonic()
    completed = subprocess.run(
        step.command,
        cwd=str(step.cwd),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.stdout:
        print(completed.stdout.rstrip())
    if completed.stderr:
        print(completed.stderr.rstrip(), file=sys.stderr)
    return step_result(
        step,
        exit_code=completed.returncode,
        skipped=False,
        elapsed_seconds=time.monotonic() - started,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def run_chain(
    name: str,
    steps: list[ChainStep],
    *,
    dry_run: bool = False,
    keep_going: bool = False,
    report_path: Path | None = None,
) -> int:
    results: list[dict[str, Any]] = []
    for step in steps:
        result = run_step(step, dry_run=dry_run)
        results.append(result)
        if result["status"] == "fail" and step.required and not keep_going:
            break

    failed_required = [result for result in results if result["required"] and result["status"] == "fail"]
    report = {
        "schema": SCHEMA,
        "name": name,
        "mode": "dry-run" if dry_run else "execute",
        "status": "fail" if failed_required else "pass",
        "steps": results,
    }
    if report_path:
        write_report(report_path, report)
        print()
        print(f"report: {report_path}")
    print()
    print(f"SUMMARY: {report['status']} ({report['mode']})")
    for result in results:
        print(f"- {result['id']}: {result['status']} exit={result['exit_code']} required={result['required']}")
    return 0 if report["status"] == "pass" else 1


def add_chain_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo-root", default=".", help="Repository or package root for the chain.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after failing required steps.")
    parser.add_argument("--report-path", default="", help="Optional JSON report path.")


def report_path_from(value: str) -> Path | None:
    return Path(value).expanduser().resolve() if value else None


def git_root_for(start: Path) -> Path:
    completed = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode == 0 and completed.stdout.strip():
        return Path(completed.stdout.strip()).resolve()
    return start


def self_test_steps() -> list[ChainStep]:
    return [
        ChainStep(
            step_id="intentional_failure",
            label="intentional failure contract probe",
            command=[sys.executable, "-c", "import sys; print('contract probe'); sys.exit(7)"],
            cwd=Path.cwd(),
            recovery_hint="This is expected in --self-test-failure; verify the report exposes command, cwd, exit code, and hint.",
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or probe SocratexPipeline command chains.")
    parser.add_argument("--self-test-failure", action="store_true", help="Emit a known failing structured report.")
    parser.add_argument("--expect-failure", action="store_true", help="Return zero only if the self-test failure is observed.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them.")
    parser.add_argument("--keep-going", action="store_true", help="Continue after failing required steps.")
    parser.add_argument("--report-path", default="", help="Optional JSON report path.")
    args = parser.parse_args()
    if not args.self_test_failure:
        parser.error("Pass --self-test-failure or use a concrete chain entrypoint.")
    code = run_chain(
        "chain_runner_self_test_failure",
        self_test_steps(),
        dry_run=args.dry_run,
        keep_going=args.keep_going,
        report_path=report_path_from(args.report_path),
    )
    if args.expect_failure:
        return 0 if code != 0 else 1
    return code


if __name__ == "__main__":
    raise SystemExit(main())
