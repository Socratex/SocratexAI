#!/usr/bin/env python3
"""Initialize a SocratexPipeline project with Python-only tooling."""

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
from python_runtime import runtime_report


AI_MODES = {"Lite", "Standard", "Enterprise"}
BRANCH_MODES = {"branch_scoped", "linear", "TBD"}
DIRECTIVE_MODES = {"snapshot", "merge", "replace"}
YES_NO_TBD = {"yes", "no", "TBD"}


def validate_choice(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        raise ValueError(f"{name} must be one of: {', '.join(sorted(allowed))}")


def resolve_communication_profile(root: Path, profile: str) -> str:
    normalized = profile.strip().lower()
    if normalized == "epistemic_skeptic":
        normalized = "epistemic"
    profile_root = root / "core" / "communication-profiles"
    if not (profile_root / f"{normalized}.txt").is_file():
        available = ", ".join(sorted(path.stem for path in profile_root.glob("*.txt")))
        raise ValueError(f"Unknown communication profile '{profile}'. Available profiles: {available}")
    return normalized


def copy_template(root: Path, install_root: Path, template_name: str, destination: str, dry_run: bool) -> None:
    source = root / "templates" / template_name
    target = install_root / destination
    if dry_run:
        print(f"Would copy template: {source} -> {target}")
        return
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def canonical_document(content: OrderedDict[str, Any], title: str, role: str) -> OrderedDict[str, Any]:
    return OrderedDict(
        index=list(content.keys()),
        content=content,
        metadata=OrderedDict(schema="socratex-data-document/v1", title=title, role=role),
    )


def ensure_gitignore(root: Path, dry_run: bool) -> None:
    gitignore = root / ".gitignore"
    comment = "# AI working files in user's prompt language - local-only, not for review"
    ignored = "/ignored"
    if dry_run:
        print("Would ensure .gitignore contains branch-scoped AI working files ignore rule.")
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


def initialize_assistant_layout(root: Path, install_root: Path, project_name: str, dry_run: bool) -> None:
    assistant_root = root / ".aiassistant" / "socratex"
    if dry_run:
        print(f"Would create branch-scoped committed directives under: {assistant_root}")
        return
    assistant_root.mkdir(parents=True, exist_ok=True)
    shutil.copy2(root / "AGENTS.md", assistant_root / "AGENTS.md")
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
    project_file = re.sub(r'[\\/:*?"<>|]', "-", project_name).strip() or "PROJECT"
    write_text(
        root / ".aiassistant" / f"{project_file}.md",
        """# Project Rules

## Summary

Project-specific code generation rules belong here when they are durable and review-facing.
""",
    )


def copy_project_files(root: Path, install_root: Path, keep: set[str], ai_mode: str, use_changelog: str, dry_run: bool) -> None:
    if dry_run:
        print(f"Would copy root controller: {root / 'templates' / 'SOCRATEX.md'} -> {root / 'SOCRATEX.md'}")
    else:
        shutil.copy2(root / "templates" / "SOCRATEX.md", root / "SOCRATEX.md")
    if "code" in keep:
        for template in ["DOCS.json", "STATE.json", "_PLAN.json", "DECISIONS.json", "PIPELINE-CONFIG.json"]:
            copy_template(root, install_root, f"code/{template}", template, dry_run)
    else:
        for template in ["DOCS.json", "STATE.md", "_PLAN.md", "DECISIONS.md", "JOURNAL.md", "REVIEW.md", "PIPELINE-CONFIG.json"]:
            copy_template(root, install_root, template, template, dry_run)
    for template in [
        "WORKFLOW.json",
        "team/product.json",
        "team/technical.json",
        "team/performance.json",
        "team/experience.json",
        "team/pipeline.json",
        "docs-tech/KNOWLEDGE-VIEWS.json",
    ]:
        copy_template(root, install_root, template, template, dry_run)
    if "code" in keep and ai_mode != "Lite":
        for template, destination in [
            ("_PROMPTS.md", "_PROMPTS.md"),
            ("code/_PROMPT-QUEUE.json", "_PROMPT-QUEUE.json"),
            ("_INSTRUCTIONS.md", "_INSTRUCTIONS.md"),
            ("code/_INSTRUCTION-QUEUE.json", "_INSTRUCTION-QUEUE.json"),
            ("code/TODO.json", "TODO.json"),
            ("code/BUGS.json", "BUGS.json"),
            ("code/BUGS-SOLVED.json", "BUGS-SOLVED.json"),
            ("code/context-docs/ENGINEERING.json", "context-docs/ENGINEERING.json"),
            ("code/context-docs/TECHNICAL.json", "context-docs/TECHNICAL.json"),
            ("code/context-docs/FROZEN_LAYERS.json", "context-docs/FROZEN_LAYERS.json"),
            ("logs-.gitkeep", "logs/.gitkeep"),
        ]:
            copy_template(root, install_root, template, destination, dry_run)
        if use_changelog != "no":
            copy_template(root, install_root, "code/CHANGELOG.json", "CHANGELOG.json", dry_run)
    elif "code" in keep:
        copy_template(root, install_root, "code/TODO.json", "TODO.json", dry_run)
        if use_changelog != "no":
            copy_template(root, install_root, "code/CHANGELOG.json", "CHANGELOG.json", dry_run)
    if keep & {"generic", "personal", "creative"}:
        copy_template(root, install_root, "BACKLOG.md", "BACKLOG.md", dry_run)
        copy_template(root, install_root, "ISSUES.md", "ISSUES.md", dry_run)


def run_python(script: Path, args: list[str], dry_run: bool) -> None:
    if dry_run:
        print(f"Would run: {sys.executable} {script} {' '.join(args)}")
        return
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{script.name} failed with exit code {completed.returncode}")


def maybe_run(script: Path, args: list[str], dry_run: bool) -> None:
    if script.is_file():
        run_python(script, args, dry_run)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-name", "-ProjectName", default="Initialized SocratexPipeline Project")
    parser.add_argument("--language", "-Language", default="English")
    parser.add_argument("--ai-mode", "-AiMode", default="Standard")
    parser.add_argument("--first-target", "-FirstTarget", default="TBD")
    parser.add_argument("--first-session-success", "-FirstSessionSuccess", default="TBD")
    parser.add_argument("--communication-profile", "-CommunicationProfile", default="standard")
    parser.add_argument("--use-changelog", "-UseChangelog", default="yes")
    parser.add_argument("--use-git", "-UseGit", default="TBD")
    parser.add_argument("--ai-may-commit", "-AiMayCommit", default="TBD")
    parser.add_argument("--ai-may-push", "-AiMayPush", default="TBD")
    parser.add_argument("--branch-mode", "-BranchMode", default="linear")
    parser.add_argument("--external-changes-possible", "-ExternalChangesPossible", default="TBD")
    parser.add_argument("--force-ddd-adiv", "-ForceDddAdiv", default="TBD")
    parser.add_argument("--import-pipeline-package", "-ImportPipelinePackage", default="TBD")
    parser.add_argument("--package-manager-detection", "-PackageManagerDetection", default="TBD")
    parser.add_argument("--project-lifecycle", "-ProjectLifecycle", default="TBD")
    parser.add_argument("--test-coverage", "-TestCoverage", default="TBD")
    parser.add_argument("--framework", "-Framework", default="TBD")
    parser.add_argument("--framework-kind", "-FrameworkKind", default="TBD")
    parser.add_argument("--linter", "-Linter", default="TBD")
    parser.add_argument("--ci", "-Ci", default="TBD")
    parser.add_argument("--docs", "-Docs", default="TBD")
    parser.add_argument("--team-size", "-TeamSize", default="TBD")
    parser.add_argument("--velocity", "-Velocity", default="TBD")
    parser.add_argument("--highest-pain", "-HighestPain", default="TBD")
    parser.add_argument("--stack-tags", "-StackTags", nargs="*", default=[])
    parser.add_argument("--branch-files-language", "-BranchFilesLanguage", default="prompt-language")
    parser.add_argument("--directive-mode", "-DirectiveMode", default="merge")
    parser.add_argument("--keep-packs", "-KeepPacks", nargs="*", default=["generic"])
    parser.add_argument("--create-files", "-CreateFiles", action="store_true")
    parser.add_argument("--compile-agent", "-CompileAgent", action="store_true")
    parser.add_argument("--run-audit", "-RunAudit", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[2]
    try:
        validate_choice("AiMode", args.ai_mode, AI_MODES)
        validate_choice("UseChangelog", args.use_changelog, YES_NO_TBD)
        validate_choice("BranchMode", args.branch_mode, BRANCH_MODES)
        validate_choice("DirectiveMode", args.directive_mode, DIRECTIVE_MODES)
        communication_profile = resolve_communication_profile(root, args.communication_profile)
        packs = split_values(args.keep_packs)
        known = {path.name.lower() for path in (root / "project").iterdir() if path.is_dir()}
        for pack in packs:
            if pack.lower() not in known:
                raise ValueError(f"Unknown project pack: {pack}")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    install_root = root / "SocratexAI"
    trash_project_dir = root / "temp" / "trash" / "project"
    trash_initializer_dir = root / "temp" / "trash" / "initializer"
    keep = {pack.lower() for pack in packs}
    all_packs = [path for path in (root / "project").iterdir() if path.is_dir()]

    if args.create_files:
        copy_project_files(root, install_root, keep, args.ai_mode, args.use_changelog, args.dry_run)
        config_path = install_root / "PIPELINE-CONFIG.json"
        if not args.dry_run and config_path.is_file():
            runtime_status = runtime_report(root)
            config_content: OrderedDict[str, Any] = OrderedDict(
                summary="Initialized project configuration for SocratexPipeline.",
                language=args.language,
                active_project_packs=packs,
                ai_operating_mode=args.ai_mode,
                git=args.use_git,
                ai_may_commit=args.ai_may_commit,
                ai_may_push=args.ai_may_push,
                branch_workflow=args.branch_mode,
                external_changes_possible=args.external_changes_possible,
                force_ddd_adiv=args.force_ddd_adiv,
                import_pipeline_package=args.import_pipeline_package,
                package_manager_detection=args.package_manager_detection,
                directive_mode=args.directive_mode,
                first_target=args.first_target,
                first_session_success_criteria=args.first_session_success,
                communication=OrderedDict(profile=communication_profile),
                changelog=OrderedDict(enabled=args.use_changelog),
                pipeline=OrderedDict(
                    version="1.1",
                    update_source="TBD",
                    public_bootstrap_url="TBD",
                    update_command=f'python SocratexAI/tools/pipeline/update_pipeline_from_link.py --source "<source>" --packs {",".join(packs)} --reinitialize-new',
                    remove_command="python SocratexAI/tools/pipeline/remove_pipeline.py --target-path .",
                    reinitialize_command="python SocratexAI/tools/pipeline/reinitialize_pipeline.py --target-path .",
                ),
                workflow=OrderedDict(
                    branch_mode=args.branch_mode,
                    branch_files_dir="ignored/ai-socratex",
                    branch_state_file="ignored/ai-socratex/<branch>-STATE.md",
                    branch_plan_file="ignored/ai-socratex/<branch>-PLAN.md",
                    branch_files_language=args.branch_files_language,
                ),
                project_profile=OrderedDict(
                    lifecycle=args.project_lifecycle,
                    test_coverage=args.test_coverage,
                    framework=args.framework,
                    framework_kind=args.framework_kind,
                    linter=args.linter,
                    ci=args.ci,
                    docs=args.docs,
                    team_size=args.team_size,
                    velocity=args.velocity,
                    highest_pain=args.highest_pain,
                    stack=split_values(args.stack_tags),
                ),
                runtime_status=runtime_status,
            )
            write_json(config_path, canonical_document(config_content, "Pipeline Config", "Initialized project configuration for SocratexPipeline."))
        if not args.dry_run and (root / "pipeline_featurelist.json").is_file():
            install_root.mkdir(parents=True, exist_ok=True)
            shutil.copy2(root / "pipeline_featurelist.json", install_root / "pipeline_featurelist.json")
            maybe_run(root / "tools" / "repo" / "sync_pipeline_featurelist.py", ["--target-path", str(root)], args.dry_run)
            maybe_run(root / "tools" / "knowledge" / "knowledge_compile.py", [], args.dry_run)
        if "code" in keep and args.branch_mode == "branch_scoped":
            if args.dry_run:
                print("Would initialize root ignored/ai-socratex branch memory.")
            else:
                run_python(root / "tools" / "pipeline" / "init_branch_memory.py", ["--branch-files-dir", "ignored/ai-socratex", "--ensure-gitignore"], False)
            initialize_assistant_layout(root, install_root, args.project_name, args.dry_run)

    readme_path = root / "README.md"
    if args.dry_run:
        print(f"Would set project name in README.md to: {args.project_name}")
    elif readme_path.is_file():
        write_text(readme_path, readme_path.read_text(encoding="utf-8").replace("# SocratexPipeline", f"# {args.project_name}"))

    for pack_dir in all_packs:
        if pack_dir.name.lower() not in keep:
            target = trash_project_dir / pack_dir.name
            if args.dry_run:
                print(f"Would move project pack: {pack_dir} -> {target}")
            else:
                if target.exists():
                    shutil.rmtree(target)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(pack_dir), str(target))

    initializer = root / "initializer"
    if initializer.exists():
        if args.dry_run:
            print(f"Would move initializer: {initializer} -> {trash_initializer_dir}")
        else:
            if trash_initializer_dir.exists():
                shutil.rmtree(trash_initializer_dir)
            trash_initializer_dir.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(initializer), str(trash_initializer_dir))

    if args.compile_agent:
        run_python(root / "tools" / "pipeline" / "generate_installed_agent_instructions.py", ["--packs", *packs, "--output-path", "AGENTS.md"], args.dry_run)
    if args.run_audit and "code" in keep:
        audit_py = root / "tools" / "documents" / "audit_docs.py"
        if audit_py.is_file():
            run_python(audit_py, ["--initialized"], args.dry_run)
        else:
            print("Audit requested, but no Python audit_docs.py entrypoint is available; skipped instead of invoking legacy shell tooling.")

    print("Initialization cleanup complete.")
    print("Recommended next improvements: configure quality gate command, Git convention, CI integration, frozen layer candidates, and domain-specific context capsules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
