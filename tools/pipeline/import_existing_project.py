#!/usr/bin/env python3
"""Import SocratexPipeline into an existing project with Python-only tooling."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

from pipeline_script_helpers import configure_stdio, split_values, write_json, write_text

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.repo_helpers import git_lines  # noqa: E402


def run_python(script: Path, args: list[str]) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{script.name} failed with exit code {completed.returncode}")


def canonical_document(content: OrderedDict[str, Any], title: str, role: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        index=list(content.keys()),
        content=content,
        metadata=OrderedDict(schema="socratex-data-document/v1", title=title, role=role),
    )


def copy_item_safe(source: Path, destination: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"Would copy: {source} -> {destination}")
        return
    if destination.exists():
        print(f"Skip existing: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def current_branch(root: Path) -> str:
    lines = git_lines(root, ["branch", "--show-current"], allow_failure=True)
    if lines:
        return re.sub(r'[\\/:*?"<>|]', "-", lines[0]) or "unknown-branch"
    return "unknown-branch"


def ensure_gitignore(root: Path, dry_run: bool) -> None:
    gitignore = root / ".gitignore"
    comment = "# AI working files in user's prompt language - local-only, not for review"
    ignored = "/ignored"
    if dry_run:
        print(f"Would ensure .gitignore contains: {ignored}")
        return
    content = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    lines = content.splitlines()
    changed = False
    if comment not in lines:
        lines.append(comment)
        changed = True
    if not any(line.rstrip("/") == ignored for line in lines):
        lines.append(ignored)
        changed = True
    if changed:
        write_text(gitignore, "\n".join(lines).rstrip() + "\n")


def initialize_assistant_layout(source_root: Path, target_root: Path, install_root: Path, dry_run: bool) -> None:
    assistant_root = target_root / ".aiassistant" / "socratex"
    if dry_run:
        print(f"Would create branch-scoped committed directives under: {assistant_root}")
        return
    assistant_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_root / "AGENTS.md", assistant_root / "AGENTS.md")
    write_text(
        assistant_root / "DOCS.md",
        """# SocratexAI Documents

## Summary

Committed SocratexAI project directives live here.

Local branch working memory lives under `ignored/ai-socratex/` when branch-scoped mode is active.
""",
    )
    config_path = install_root / "PIPELINE-CONFIG.json"
    if config_path.is_file():
        shutil.copy2(config_path, assistant_root / "PIPELINE-CONFIG.json")
    write_text(
        target_root / ".aiassistant" / "PROJECT.md",
        """# Project Rules

## Summary

Project-specific code generation rules belong here when they are durable and review-facing.
""",
    )


def content_of(value: Any) -> Any:
    if isinstance(value, dict) and isinstance(value.get("content"), dict):
        return value["content"]
    return value


def should_write_config(path: Path) -> bool:
    if not path.is_file():
        return True
    try:
        content = content_of(json.loads(path.read_text(encoding="utf-8")))
        return str(content.get("language", "")) == "TBD" if isinstance(content, dict) else True
    except Exception:
        return True


def template_map(has_code_pack: bool) -> dict[str, str]:
    if has_code_pack:
        return {
            "code/DOCS.json": "DOCS.json",
            "code/STATE.json": "STATE.json",
            "code/_PLAN.json": "_PLAN.json",
            "code/TODO.json": "TODO.json",
            "code/DECISIONS.json": "DECISIONS.json",
            "code/CHANGELOG.json": "CHANGELOG.json",
            "code/BUGS.json": "BUGS.json",
            "code/BUGS-SOLVED.json": "BUGS-SOLVED.json",
            "_PROMPTS.md": "_PROMPTS.md",
            "code/_PROMPT-QUEUE.json": "_PROMPT-QUEUE.json",
            "_INSTRUCTIONS.md": "_INSTRUCTIONS.md",
            "code/_INSTRUCTION-QUEUE.json": "_INSTRUCTION-QUEUE.json",
            "code/PIPELINE-CONFIG.json": "PIPELINE-CONFIG.json",
            "WORKFLOW.json": "WORKFLOW.json",
            "docs-tech/KNOWLEDGE-VIEWS.json": "docs-tech/KNOWLEDGE-VIEWS.json",
            "team/product.json": "team/product.json",
            "team/technical.json": "team/technical.json",
            "team/performance.json": "team/performance.json",
            "team/experience.json": "team/experience.json",
            "team/pipeline.json": "team/pipeline.json",
            "code/context-docs/ENGINEERING.json": "context-docs/ENGINEERING.json",
            "code/context-docs/TECHNICAL.json": "context-docs/TECHNICAL.json",
            "code/context-docs/FROZEN_LAYERS.json": "context-docs/FROZEN_LAYERS.json",
            "logs-.gitkeep": "logs/.gitkeep",
        }
    return {
        "DOCS.json": "DOCS.json",
        "STATE.md": "STATE.md",
        "_PLAN.md": "_PLAN.md",
        "BACKLOG.md": "BACKLOG.md",
        "DECISIONS.md": "DECISIONS.md",
        "ISSUES.md": "ISSUES.md",
        "JOURNAL.md": "JOURNAL.md",
        "REVIEW.md": "REVIEW.md",
        "PIPELINE-CONFIG.json": "PIPELINE-CONFIG.json",
        "WORKFLOW.json": "WORKFLOW.json",
        "docs-tech/KNOWLEDGE-VIEWS.json": "docs-tech/KNOWLEDGE-VIEWS.json",
        "team/product.json": "team/product.json",
        "team/technical.json": "team/technical.json",
        "team/performance.json": "team/performance.json",
        "team/experience.json": "team/experience.json",
        "team/pipeline.json": "team/pipeline.json",
    }


def maybe_run_optional_py(script: Path, args: list[str]) -> None:
    if script.is_file():
        run_python(script, args)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", "-TargetPath", required=True)
    parser.add_argument("--packs", "-Packs", nargs="*", default=["code"])
    parser.add_argument("--profile", "-Profile", default="")
    parser.add_argument("--ai-mode", "-AiMode", choices=("Lite", "Standard", "Enterprise"), default="Standard")
    parser.add_argument("--language", "-Language", default="English")
    parser.add_argument("--branch-mode", "-BranchMode", choices=("branch_scoped", "linear"), default="linear")
    parser.add_argument("--create-project-files", "-CreateProjectFiles", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    source_root = Path(__file__).resolve().parents[2]
    target_root = Path(args.target_path).resolve()
    install_root = target_root / "SocratexAI"
    packs = split_values(args.packs)
    profile = args.profile or ("SocratexGamedev" if "gamedev" in packs else "")

    print("==> importing SocratexPipeline into existing project")
    print(f"Target: {target_root}")
    print(f"Install root: {install_root}")

    sync_args = [
        "--source-root",
        str(source_root),
        "--install-root",
        str(install_root),
        "--project-root",
        str(target_root),
        "--prune-unmanaged",
    ]
    if profile:
        sync_args.extend(["--profile", profile, "--apply-project-profile"])
    if args.dry_run:
        sync_args.append("--dry-run")
    run_python(source_root / "tools" / "pipeline" / "sync_managed_pipeline_package.py", sync_args)

    if not args.dry_run:
        (install_root / "project").mkdir(parents=True, exist_ok=True)
    for pack in packs:
        source_pack = source_root / "project" / pack
        if not source_pack.exists():
            raise SystemExit(f"Unknown pack: {pack}")
        copy_item_safe(source_pack, install_root / "project" / pack, args.dry_run)

    for source, destination in [
        (source_root / "AGENTS.md", install_root / "AGENTS.md"),
        (source_root / "RECOMMENDATION.md", install_root / "RECOMMENDATION.md"),
        (source_root / "PUBLIC-BOOTSTRAP.md", install_root / "PUBLIC-BOOTSTRAP.md"),
        (source_root / "templates" / "SOCRATEX.md", target_root / "SOCRATEX.md"),
    ]:
        copy_item_safe(source, destination, args.dry_run)

    has_code_pack = "code" in packs
    if args.create_project_files:
        for template, destination in template_map(has_code_pack).items():
            copy_item_safe(source_root / "templates" / template, install_root / destination, args.dry_run)
        if has_code_pack and args.branch_mode == "branch_scoped":
            branch = current_branch(target_root)
            branch_root = target_root / "ignored" / "ai-socratex"
            copy_item_safe(source_root / "templates" / "code" / "branch" / "BRANCH-TODO.md", branch_root / "TODO.md", args.dry_run)
            copy_item_safe(source_root / "templates" / "code" / "branch" / "BRANCH-STATE.md", branch_root / f"{branch}-STATE.md", args.dry_run)
            copy_item_safe(source_root / "templates" / "code" / "branch" / "BRANCH-PLAN.md", branch_root / f"{branch}-PLAN.md", args.dry_run)
            ensure_gitignore(target_root, args.dry_run)
            initialize_assistant_layout(source_root, target_root, install_root, args.dry_run)

    if not args.dry_run:
        maybe_run_optional_py(install_root / "tools" / "repo" / "sync_pipeline_featurelist.py", ["--target-path", str(target_root)])
        config_path = install_root / "PIPELINE-CONFIG.json"
        if should_write_config(config_path):
            config_content: OrderedDict[str, Any] = OrderedDict(
                summary="Imported SocratexPipeline configuration.",
                language=args.language,
                active_project_packs=packs,
                ai_operating_mode=args.ai_mode,
                communication=OrderedDict(profile="standard"),
                branch_workflow=args.branch_mode,
                pipeline=OrderedDict(
                    version="1.1",
                    update_source="TBD",
                    public_bootstrap_url="TBD",
                    update_command=f'python SocratexAI/tools/pipeline/update_pipeline_from_link.py --source "<source>" --packs {",".join(packs)} --reinitialize-new',
                    remove_command="python SocratexAI/tools/pipeline/remove_pipeline.py --target-path .",
                    reinitialize_command="python SocratexAI/tools/pipeline/reinitialize_pipeline.py --target-path .",
                ),
            )
            if has_code_pack:
                config_content["changelog"] = OrderedDict(enabled="yes")
                config_content["workflow"] = OrderedDict(
                    branch_mode=args.branch_mode,
                    branch_files_dir="ignored/ai-socratex",
                    branch_state_file="ignored/ai-socratex/<branch>-STATE.md",
                    branch_plan_file="ignored/ai-socratex/<branch>-PLAN.md",
                    branch_files_language="prompt-language",
                )
                config_content["project_profile"] = OrderedDict(
                    lifecycle="TBD",
                    test_coverage="TBD",
                    framework="TBD",
                    framework_kind="TBD",
                    linter="TBD",
                    ci="TBD",
                    docs="TBD",
                    team_size="TBD",
                    velocity="TBD",
                    highest_pain="TBD",
                    stack=[],
                )
                config_content["runtime_status"] = OrderedDict(python3=OrderedDict(ok="TBD", version="TBD", install_hint="TBD"))
            write_json(config_path, canonical_document(config_content, "Pipeline Config", "Imported SocratexPipeline configuration."))
        maybe_run_optional_py(install_root / "tools" / "documents" / "build_document_cache.py", [])
        maybe_run_optional_py(install_root / "tools" / "knowledge" / "knowledge_compile.py", [])

    print("Import complete. SocratexAI is now active for this project; future sessions should start from SOCRATEX.md.")
    print("Review SOCRATEX.md and run SocratexAI/tools/documents/audit_docs.py when ready.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
