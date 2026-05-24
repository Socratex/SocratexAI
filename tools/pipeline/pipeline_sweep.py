import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEFAULT_SMOKE = [
    "feature_contracts",
    "docs_audit",
    "compiled_context",
    "tier_check",
    "git_clean",
]


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
        if self.skipped:
            return "skipped" if self.skip_ok else "fail"
        return "pass" if self.exit_code == 0 else "fail"


@dataclass
class Project:
    name: str
    path: Path
    role: str = "child"
    update: bool = True
    profile: str = ""
    packs: list[str] = field(default_factory=list)
    directive_mode: str = ""
    directive_files: list[str] = field(default_factory=list)
    reinitialize_new: bool = False
    full_verify: bool = False
    smoke: list[str] = field(default_factory=lambda: list(DEFAULT_SMOKE))
    finalize: list[list[str]] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    if isinstance(data.get("content"), dict) and (
        "projects" in data["content"] or "source" in data["content"]
    ):
        content = data["content"]
        if "defaults" not in content and isinstance(data.get("metadata"), dict):
            content = dict(content)
            content.setdefault("metadata", data["metadata"])
        return content
    return data


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    raise ValueError(f"Expected a string or list, got {type(value).__name__}.")


def tail(text: str, limit: int = 1800) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[-limit:]


def resolve_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "tools").is_dir() and (candidate / "SCRIPTS.json").is_file():
            return candidate
    return start.resolve()


def load_projects(config: dict[str, Any], cli_projects: list[str]) -> tuple[Path | None, list[Project]]:
    defaults = config.get("defaults") if isinstance(config.get("defaults"), dict) else {}
    source = config.get("source")
    source_path = Path(source).expanduser().resolve() if source else None
    projects: list[Project] = []

    for raw in config.get("projects", []):
        if not isinstance(raw, dict):
            raise ValueError("Every configured project must be an object.")
        project_defaults = dict(defaults)
        project_defaults.update(raw)
        projects.append(project_from_mapping(project_defaults))

    for value in cli_projects:
        if "=" not in value:
            raise ValueError("--project must use NAME=PATH.")
        name, raw_path = value.split("=", 1)
        role = "child"
        if ":" in name:
            role_prefix, project_name = name.split(":", 1)
            if role_prefix in {"source", "child"}:
                role = role_prefix
                name = project_name
        projects.append(
            Project(
                name=name.strip(),
                path=Path(raw_path).expanduser().resolve(),
                role=role,
                update=role != "source",
                smoke=list(DEFAULT_SMOKE),
            )
        )

    return source_path, projects


def project_from_mapping(raw: dict[str, Any]) -> Project:
    name = str(raw.get("name", "")).strip()
    path = str(raw.get("path", "")).strip()
    if not name or not path:
        raise ValueError("Project entries require name and path.")
    smoke = normalize_list(raw.get("smoke", DEFAULT_SMOKE))
    return Project(
        name=name,
        path=Path(path).expanduser().resolve(),
        role=str(raw.get("role", "child")).strip() or "child",
        update=bool(raw.get("update", True)),
        profile=str(raw.get("profile", "")).strip(),
        packs=normalize_list(raw.get("packs", [])),
        directive_mode=str(raw.get("directive_mode", "")).strip(),
        directive_files=normalize_list(raw.get("directive_files", [])),
        reinitialize_new=bool(raw.get("reinitialize_new", False)),
        full_verify=bool(raw.get("full_verify", False)),
        smoke=smoke,
        finalize=normalize_command_list(raw.get("finalize", [])),
    )


def normalize_command_list(value: Any) -> list[list[str]]:
    if value in (None, ""):
        return []
    if not isinstance(value, list):
        raise ValueError("finalize must be a list of command arrays.")
    commands: list[list[str]] = []
    for item in value:
        if isinstance(item, list):
            commands.append([str(part) for part in item])
        else:
            raise ValueError("finalize commands must be arrays, not shell strings.")
    return commands


def run_command(
    step_id: str,
    label: str,
    command: list[str],
    cwd: Path,
    execute: bool,
    required: bool = True,
    recovery_hint: str = "",
    env: dict[str, str] | None = None,
) -> CommandResult:
    if not execute:
        return CommandResult(
            step_id=step_id,
            label=label,
            command=command,
            cwd=cwd,
            exit_code=None,
            required=required,
            skipped=True,
            reason="dry-run",
            recovery_hint=recovery_hint,
        )
    started = time.monotonic()
    completed = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    return CommandResult(
        step_id=step_id,
        label=label,
        command=command,
        cwd=cwd,
        exit_code=completed.returncode,
        required=required,
        elapsed_seconds=time.monotonic() - started,
        stdout_tail=tail(completed.stdout),
        stderr_tail=tail(completed.stderr),
        recovery_hint=recovery_hint,
    )


def git_status(project: Project, execute: bool) -> list[CommandResult]:
    return [
        run_command(
            "git_branch",
            "git branch",
            ["git", "branch", "--show-current"],
            project.path,
            execute,
            recovery_hint="Verify this path is a Git checkout before running the sweep.",
        ),
        run_command(
            "git_head",
            "git head",
            ["git", "rev-parse", "--short", "HEAD"],
            project.path,
            execute,
            recovery_hint="Verify this path is a Git checkout before comparing commit drift.",
        ),
        run_command(
            "git_status",
            "git status",
            ["git", "status", "--short"],
            project.path,
            execute,
            required=False,
            recovery_hint="Review uncommitted project changes before applying managed updates.",
        ),
    ]


def update_command(project: Project, source_root: Path, python: str) -> list[str]:
    command = [
        python,
        str(source_root / "tools" / "pipeline" / "update_pipeline_from_link.py"),
        "--source",
        str(source_root),
        "--source-mode",
        "LocalPath",
        "--target-path",
        str(project.path),
    ]
    if project.profile:
        command += ["--profile", project.profile]
    if project.packs:
        command += ["--packs", *project.packs]
    if project.directive_mode:
        command += ["--directive-mode", project.directive_mode]
    if project.directive_files:
        command += ["--directive-files", *project.directive_files]
    if project.reinitialize_new:
        command += ["--reinitialize-new"]
    if project.full_verify:
        command += ["--full-verify"]
    return command


def script_root_for(project: Project) -> Path:
    if project.role == "source":
        return project.path
    installed = project.path / "SocratexAI"
    if installed.is_dir():
        return installed
    return project.path


def smoke_command(project: Project, smoke: str, python: str) -> tuple[str, list[str], Path, str, str]:
    root = script_root_for(project)
    mapping: dict[str, tuple[Path, list[str]]] = {
        "feature_contracts": (
            root / "tools" / "repo" / "check_pipeline_feature_contracts.py",
            ["--repo-root", str(root)],
        ),
        "docs_audit": (
            root / "tools" / "documents" / "audit_docs.py",
            ["--repo-root", str(root)],
        ),
        "compiled_context": (
            root / "tools" / "pipeline" / "check_ai_compiled_context.py",
            ["--repo-root", str(root)],
        ),
        "tier_check": (
            root / "tools" / "knowledge" / "knowledge_tier_check.py",
            ["--repo-root", str(root), "--include-templates"],
        ),
    }
    if smoke == "git_clean":
        return smoke, ["git", "diff", "--quiet"], project.path, "", "Review and commit intended changes, or discard only changes created by this task."
    if smoke not in mapping:
        raise ValueError(f"Unknown smoke check '{smoke}' for {project.name}.")
    script, extra = mapping[smoke]
    hints = {
        "feature_contracts": "Update pipeline_featurelist.json or restore missing source-managed artifacts.",
        "docs_audit": "Fix the reported document contract issue before syncing children.",
        "compiled_context": "Rebuild compiled context or inspect stale compiled artifacts.",
        "tier_check": "Repair the reported tier/source contract before finalizing the sweep.",
    }
    if not script.is_file():
        return smoke, [], root, f"missing script: {script}", hints.get(smoke, "Restore the missing smoke script.")
    return smoke, [python, str(script), *extra], root, "", hints.get(smoke, "Fix the failing smoke check before declaring the project clean.")


def print_result(result: CommandResult, json_mode: bool) -> None:
    if json_mode:
        return
    command_text = " ".join(result.command) if result.command else "(no command)"
    prefix = "SKIP" if result.skipped else ("OK" if result.ok else "FAIL")
    elapsed = "" if result.skipped else f" [{result.elapsed_seconds:.1f}s]"
    print(f"{prefix}: {result.label}{elapsed}")
    print(f"  cwd: {result.cwd}")
    print(f"  cmd: {command_text}")
    if result.reason:
        print(f"  reason: {result.reason}")
    if result.recovery_hint:
        print(f"  recovery_hint: {result.recovery_hint}")
    if result.stdout_tail:
        print(f"  stdout: {result.stdout_tail}")
    if result.stderr_tail:
        print(f"  stderr: {result.stderr_tail}")


def project_report(project: Project, results: list[CommandResult]) -> dict[str, Any]:
    failures = [result for result in results if not result.ok]
    manual_attention = []
    for result in failures:
        manual_attention.append(f"{result.label} exited {result.exit_code}")
    return {
        "name": project.name,
        "path": str(project.path),
        "role": project.role,
        "status": "pass" if not failures else "fail",
        "manual_attention": manual_attention,
        "results": [
            {
                "id": result.step_id,
                "label": result.label,
                "command": result.command,
                "cwd": str(result.cwd),
                "required": result.required,
                "status": result.status,
                "exit_code": result.exit_code,
                "skipped": result.skipped,
                "skip_ok": result.skip_ok,
                "reason": result.reason,
                "elapsed_seconds": round(result.elapsed_seconds, 2),
                "stdout_tail": result.stdout_tail,
                "stderr_tail": result.stderr_tail,
                "recovery_hint": result.recovery_hint,
                "artifact_path": result.artifact_path,
            }
            for result in results
        ],
    }


def run_project(
    project: Project,
    source_root: Path,
    python: str,
    execute: bool,
    include_update: bool,
    include_smoke: bool,
    include_finalize: bool,
    stop_on_failure: bool,
    json_mode: bool,
) -> dict[str, Any]:
    if not project.path.is_dir():
        result = CommandResult(
            step_id="project_exists",
            label="project exists",
            command=[],
            cwd=project.path,
            exit_code=1,
            required=True,
            reason="project path does not exist",
            recovery_hint="Fix the project path in the sweep config or remove the project from this run.",
        )
        print_result(result, json_mode)
        return project_report(project, [result])

    results: list[CommandResult] = []
    for result in git_status(project, execute):
        results.append(result)
        print_result(result, json_mode)

    if include_update and project.role != "source" and project.update:
        result = run_command(
            "pipeline_update",
            "pipeline update",
            update_command(project, source_root, python),
            project.path,
            execute,
            recovery_hint="Inspect update output for local overrides or missing source paths before rerunning with execute.",
        )
        results.append(result)
        print_result(result, json_mode)
        if stop_on_failure and not result.ok:
            return project_report(project, results)

    if include_smoke:
        for smoke in project.smoke:
            label, command, cwd, skip_reason, recovery_hint = smoke_command(project, smoke, python)
            result = (
                CommandResult(
                    step_id=smoke,
                    label=label,
                    command=command,
                    cwd=cwd,
                    exit_code=None,
                    required=True,
                    skipped=True,
                    skip_ok=False,
                    reason=skip_reason,
                    recovery_hint=recovery_hint,
                )
                if skip_reason
                else run_command(smoke, label, command, cwd, execute, recovery_hint=recovery_hint)
            )
            results.append(result)
            print_result(result, json_mode)
            if stop_on_failure and not result.ok:
                return project_report(project, results)

    if include_finalize:
        for index, command in enumerate(project.finalize, start=1):
            result = run_command(
                f"finalize_{index}",
                f"finalize {index}",
                command,
                project.path,
                execute,
                recovery_hint="Fix the project-specific finalizer failure before relying on this sweep result.",
            )
            results.append(result)
            print_result(result, json_mode)
            if stop_on_failure and not result.ok:
                return project_report(project, results)

    return project_report(project, results)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sweep SocratexPipeline updates and smoke checks across source and child projects."
    )
    parser.add_argument("--config", help="JSON config with source/defaults/projects.")
    parser.add_argument("--source", help="SocratexAI source root; defaults to the current tool repository.")
    parser.add_argument("--project", action="append", default=[], help="Add a project as NAME=PATH.")
    parser.add_argument("--execute", action="store_true", help="Run commands. Without this, only print the plan.")
    parser.add_argument("--update", action="store_true", help="Run update phase.")
    parser.add_argument("--smoke", action="store_true", help="Run smoke phase.")
    parser.add_argument("--finalize", action="store_true", help="Run configured finalizer commands.")
    parser.add_argument("--all", action="store_true", help="Run update and smoke phases.")
    parser.add_argument("--stop-on-failure", action="store_true", help="Stop a project after the first failing phase.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON summary.")
    parser.add_argument("--write-report", default="", help="Optional JSON summary report output path.")
    args = parser.parse_args()

    tool_root = resolve_repo_root(Path(__file__).resolve())
    config: dict[str, Any] = {}
    if args.config:
        config = read_json(Path(args.config).expanduser().resolve())

    configured_source, projects = load_projects(config, args.project)
    source_root = Path(args.source).expanduser().resolve() if args.source else configured_source or tool_root
    if not source_root.is_dir():
        raise SystemExit(f"Source root does not exist: {source_root}")
    if not projects:
        raise SystemExit("No projects configured. Use --config or --project NAME=PATH.")

    python = os.environ.get("SOCRATEX_PYTHON", "") or sys.executable
    if not python:
        raise SystemExit("Python is required. Install Python 3.10+ or set SOCRATEX_PYTHON.")

    include_update = args.all or args.update
    include_smoke = args.all or args.smoke or not (args.update or args.finalize)
    include_finalize = args.finalize

    reports = [
        run_project(
            project=project,
            source_root=source_root,
            python=python,
            execute=args.execute,
            include_update=include_update,
            include_smoke=include_smoke,
            include_finalize=include_finalize,
            stop_on_failure=args.stop_on_failure,
            json_mode=args.json,
        )
        for project in projects
    ]

    summary = {
        "schema": "socratex-pipeline-sweep-report/v1",
        "mode": "execute" if args.execute else "dry-run",
        "source": str(source_root),
        "projects": reports,
        "status": "pass" if all(report["status"] == "pass" for report in reports) else "fail",
    }
    if args.write_report:
        report_path = Path(args.write_report).expanduser().resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("")
        print(f"SUMMARY: {summary['status']} ({summary['mode']})")
        for report in reports:
            attention = "; ".join(report["manual_attention"]) or "none"
            print(f"- {report['name']}: {report['status']}; manual_attention={attention}")
    return 0 if summary["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
