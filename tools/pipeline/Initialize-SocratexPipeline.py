#!/usr/bin/env python3
"""Dry-run SocratexPipeline project initialization without PowerShell."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


AI_MODES = {"Lite", "Standard", "Enterprise"}
BRANCH_MODES = {"branch_scoped", "linear", "TBD"}
DIRECTIVE_MODES = {"snapshot", "merge", "replace"}
YES_NO_TBD = {"yes", "no", "TBD"}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def split_values(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item and item not in result:
                result.append(item)
    return result


def validate_choice(name: str, value: str, allowed: set[str]) -> None:
    if value not in allowed:
        options = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {options}")


def resolve_communication_profile(root: Path, profile: str) -> str:
    normalized = profile.strip().lower()
    if normalized == "epistemic_skeptic":
        normalized = "epistemic"
    profile_root = root / "core" / "communication-profiles"
    if not (profile_root / f"{normalized}.txt").is_file():
        available = ", ".join(sorted(path.stem for path in profile_root.glob("*.txt")))
        raise ValueError(f"Unknown communication profile '{profile}'. Available profiles: {available}")
    return normalized


def known_packs(root: Path) -> set[str]:
    project_dir = root / "project"
    return {path.name.lower() for path in project_dir.iterdir() if path.is_dir()}


def template_copy_lines(root: Path, install_root: Path, keep: set[str], ai_mode: str, use_changelog: str) -> list[str]:
    template_dir = root / "templates"

    def copy(template_name: str, destination: str) -> str:
        return f"Would copy template: {template_dir / template_name} -> {install_root / destination}"

    def copy_code(template_name: str, destination: str) -> str:
        return copy(str(Path("code") / template_name), destination)

    lines: list[str] = [
        f"Would copy root controller: {template_dir / 'SOCRATEX.md'} -> {root / 'SOCRATEX.md'}",
    ]
    if "code" in keep:
        lines.extend(
            [
                copy_code("DOCS.json", "DOCS.json"),
                copy_code("STATE.json", "STATE.json"),
                copy_code("_PLAN.json", "_PLAN.json"),
                copy_code("DECISIONS.json", "DECISIONS.json"),
                copy_code("PIPELINE-CONFIG.json", "PIPELINE-CONFIG.json"),
            ]
        )
    else:
        lines.extend(
            [
                copy("DOCS.json", "DOCS.json"),
                copy("STATE.md", "STATE.md"),
                copy("_PLAN.md", "_PLAN.md"),
                copy("DECISIONS.md", "DECISIONS.md"),
                copy("JOURNAL.md", "JOURNAL.md"),
                copy("REVIEW.md", "REVIEW.md"),
                copy("PIPELINE-CONFIG.json", "PIPELINE-CONFIG.json"),
            ]
        )

    lines.extend(
        [
            copy("WORKFLOW.json", "WORKFLOW.json"),
            copy(str(Path("team") / "product.json"), str(Path("team") / "product.json")),
            copy(str(Path("team") / "technical.json"), str(Path("team") / "technical.json")),
            copy(str(Path("team") / "performance.json"), str(Path("team") / "performance.json")),
            copy(str(Path("team") / "experience.json"), str(Path("team") / "experience.json")),
            copy(str(Path("team") / "pipeline.json"), str(Path("team") / "pipeline.json")),
            copy(str(Path("docs-tech") / "KNOWLEDGE-VIEWS.json"), str(Path("docs-tech") / "KNOWLEDGE-VIEWS.json")),
        ]
    )

    if "code" in keep and ai_mode != "Lite":
        lines.extend(
            [
                copy("_PROMPTS.md", "_PROMPTS.md"),
                copy_code("_PROMPT-QUEUE.json", "_PROMPT-QUEUE.json"),
                copy("_INSTRUCTIONS.md", "_INSTRUCTIONS.md"),
                copy_code("_INSTRUCTION-QUEUE.json", "_INSTRUCTION-QUEUE.json"),
                copy_code("TODO.json", "TODO.json"),
                copy_code("BUGS.json", "BUGS.json"),
                copy_code("BUGS-SOLVED.json", "BUGS-SOLVED.json"),
            ]
        )
        if use_changelog != "no":
            lines.append(copy_code("CHANGELOG.json", "CHANGELOG.json"))
        lines.extend(
            [
                copy_code(str(Path("context-docs") / "ENGINEERING.json"), str(Path("context-docs") / "ENGINEERING.json")),
                copy_code(str(Path("context-docs") / "TECHNICAL.json"), str(Path("context-docs") / "TECHNICAL.json")),
                copy_code(str(Path("context-docs") / "FROZEN_LAYERS.json"), str(Path("context-docs") / "FROZEN_LAYERS.json")),
                copy("logs-.gitkeep", str(Path("logs") / ".gitkeep")),
            ]
        )
    elif "code" in keep:
        lines.append(copy_code("TODO.json", "TODO.json"))
        if use_changelog != "no":
            lines.append(copy_code("CHANGELOG.json", "CHANGELOG.json"))

    if keep & {"generic", "personal", "creative"}:
        lines.extend([copy("BACKLOG.md", "BACKLOG.md"), copy("ISSUES.md", "ISSUES.md")])
    return lines


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dry-run SocratexPipeline project initialization.")
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
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    root = repo_root()
    try:
        validate_choice("AiMode", args.ai_mode, AI_MODES)
        validate_choice("UseChangelog", args.use_changelog, YES_NO_TBD)
        validate_choice("BranchMode", args.branch_mode, BRANCH_MODES)
        validate_choice("DirectiveMode", args.directive_mode, DIRECTIVE_MODES)
        communication_profile = resolve_communication_profile(root, args.communication_profile)
        packs = split_values(args.keep_packs)
        known = known_packs(root)
        for pack in packs:
            if pack.lower() not in known:
                raise ValueError(f"Unknown project pack: {pack}")
        if not args.dry_run:
            raise ValueError("Python initializer currently supports --dry-run only; use the legacy initializer for writes until the full port lands.")
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    install_root = root / "SocratexAI"
    trash_project_dir = root / "temp" / "trash" / "project"
    trash_initializer_dir = root / "temp" / "trash" / "initializer"
    keep = {pack.lower() for pack in packs}

    print("==> SocratexPipeline initialization dry run")
    print(f"Project root: {root}")
    print(f"Project name: {args.project_name}")
    print(f"Language: {args.language}")
    print(f"AI mode: {args.ai_mode}")
    print(f"Communication profile: {communication_profile}")
    print(f"Keep packs: {', '.join(packs)}")
    print(f"Directive mode: {args.directive_mode}")

    if args.create_files:
        for line in template_copy_lines(root, install_root, keep, args.ai_mode, args.use_changelog):
            print(line)
        if "code" in keep and args.branch_mode == "branch_scoped":
            print("Would initialize root ignored/ai-socratex branch memory.")
            print(f"Would create branch-scoped committed directives under: {root / '.aiassistant' / 'socratex'}")

    print(f"Would set project name in README.md to: {args.project_name}")
    for pack_dir in sorted((root / "project").iterdir()):
        if pack_dir.is_dir() and pack_dir.name.lower() not in keep:
            print(f"Would move project pack: {pack_dir} -> {trash_project_dir / pack_dir.name}")
    if (root / "initializer").is_dir():
        print(f"Would move initializer: {root / 'initializer'} -> {trash_initializer_dir}")
    if args.compile_agent:
        print(f"Would compile AGENTS.md for packs: {', '.join(packs)}")
    if args.run_audit and "code" in keep:
        print("Would run initialized code audit.")

    print("Initialization cleanup complete.")
    print("Recommended next improvements: configure quality gate command, Git convention, CI integration, frozen layer candidates, and domain-specific context capsules.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
