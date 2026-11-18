#!/usr/bin/env python3
"""Shared runner for documented SocratexPipeline command chains."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.command_result_helpers import (
    CommandStep,
    command_result_from_step,
    command_result_payload,
    command_result_status,
    output_tail,
    run_command_step,
    write_json_report,
)
from shared.repo_helpers import repo_root as shared_repo_root

SCHEMA = "socratex-chain-report/v1"
ChainStep = CommandStep


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
    return command_result_status(exit_code, skipped)


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
    return command_result_payload(
        command_result_from_step(
            step,
            exit_code=exit_code,
            skipped=skipped,
            reason=reason,
            elapsed_seconds=elapsed_seconds,
            stdout=stdout,
            stderr=stderr,
        )
    )


def run_step(step: ChainStep, *, dry_run: bool) -> dict[str, Any]:
    print_step(step, dry_run=dry_run)
    result = run_command_step(step, execute=not dry_run)
    if result.stdout_tail:
        print(result.stdout_tail)
    if result.stderr_tail:
        print(result.stderr_tail, file=sys.stderr)
    return command_result_payload(result)


def write_report(path: Path, report: dict[str, Any]) -> None:
    write_json_report(path, report)


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
    return shared_repo_root(start, marker_files=(), use_git=True)


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
