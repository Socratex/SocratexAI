#!/usr/bin/env python3
"""Interactive first-run wizard for Python-first SocratexPipeline setup."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def ask_default(prompt: str, default: str) -> str:
    answer = input(f"{prompt} [{default}] ").strip()
    return answer or default


def communication_profiles(repo_root: Path) -> list[str]:
    profile_root = repo_root / "core" / "communication-profiles"
    profiles = sorted(path.stem for path in profile_root.glob("*.txt")) if profile_root.is_dir() else []
    return profiles or ["standard"]


def ask_choice(prompt: str, default: str, choices: list[str]) -> str:
    allowed = {choice.lower(): choice for choice in choices}
    allowed["epistemic_skeptic"] = "epistemic"
    while True:
        answer = ask_default(prompt, default)
        key = answer.strip().lower()
        if key in allowed:
            return allowed[key]
        print(f"Unknown communication profile '{answer}'. Available: {', '.join(choices)}")


def run(script: Path, args: list[str]) -> None:
    completed = subprocess.run([sys.executable, str(script), *args], check=False)
    if completed.returncode != 0:
        raise SystemExit(f"{script.name} failed with exit code {completed.returncode}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    print("SocratexPipeline first-run wizard")
    print("Answer in your preferred language after choosing the project language.")
    print()

    profiles = communication_profiles(repo_root)
    language = ask_default("1. Project conversation/status language", "English")
    project_name = ask_default("2. Project name", "Initialized SocratexPipeline Project")
    kind = ask_default("3. Project kind: code, generic, personal, creative, mixed", "code")
    packs = ask_default("4. Active packs, comma-separated", "code" if kind == "code" else "generic")
    ai_mode = ask_default("5. AI mode: Lite, Standard, Enterprise", "Standard")
    first_target = ask_default("6. First concrete target", "Define the first execution pass")
    communication_profile = ask_choice(f"7. Communication profile: {', '.join(profiles)}", "standard", profiles)
    optimize_for = ask_default("8. Optimize for", "correctness")
    avoid = ask_default("9. What should the agent avoid", "unbounded scope")
    artifacts = ask_default("10. Required artifacts after initialization", "default pack artifacts")
    use_changelog = ask_default("11. Use CHANGELOG for shipped history? yes/no", "yes")
    use_git = ask_default("12. Use Git", "yes")
    external = ask_default("13. External tools, folders, accounts, or references", "none")
    success = ask_default("14. Successful first session means", "project initialized and first pass ready")

    ai_may_commit = "no"
    ai_may_push = "no"
    branch_mode = "linear"
    external_changes_possible = "unknown"
    force_ddd_adiv = "yes"
    import_pipeline_package = "no"
    package_manager_detection = "yes"
    directive_mode = "merge"
    project_lifecycle = "TBD"
    test_coverage = "TBD"
    framework = "TBD"
    framework_kind = "TBD"
    linter = "TBD"
    ci = "TBD"
    docs = "TBD"
    team_size = "TBD"
    velocity = "TBD"
    highest_pain = "TBD"
    stack_tags: list[str] = []

    if kind == "code" or "code" in packs:
        print()
        print("Programming context questions:")
        try:
            run(repo_root / "tools" / "setup" / "detect_project_stack.py", ["--target-path", "."])
        except SystemExit as exc:
            print(f"Stack detection failed: {exc}")
        ai_may_commit = ask_default("15. Should AI commit changes", "no")
        ai_may_push = ask_default("16. Should AI push changes", "no")
        project_lifecycle = ask_default("17. Lifecycle: greenfield, early, mature, legacy, sunset", "early")
        test_coverage = ask_default("18. Test coverage: none, smoke-only, partial, comprehensive, tdd", "partial")
        framework = ask_default("19. Framework name or none", "TBD")
        framework_kind = ask_default("20. Framework kind: standard, custom in-house, mixed, none", "standard")
        linter = ask_default("21. Linter/typecheck: enforced, optional, none", "optional")
        ci = ask_default("22. CI/CD: full, partial, none", "partial")
        docs = ask_default("23. Documentation: current, partial, stale, none", "partial")
        team_size = ask_default("24. Team size: solo, small, medium, large", "solo")
        velocity = ask_default("25. Velocity: experimental, iterating, shipping, maintenance", "iterating")
        highest_pain = ask_default("26. Highest current pain", "TBD")
        stack_text = ask_default("27. Stack tags, comma-separated", "TBD")
        stack_tags = [item.strip() for item in stack_text.split(",") if item.strip() and item.strip() != "TBD"]
        branch_mode = ask_default("28. Branch mode: branch_scoped, linear", "branch_scoped")
        external_changes_possible = ask_default("29. Can external changes happen while AI works", "yes")
        force_ddd_adiv = ask_default("30. Force DDD-ADIV", "yes")
        import_pipeline_package = ask_default("31. Import pipeline package/dependency if ecosystem supports it", "no")
        package_manager_detection = ask_default("32. Detect package managers/frameworks, including Composer", "yes")
        directive_mode = ask_default("33. Directive mode: snapshot, merge, replace", "merge")

    print()
    print("Summary:")
    print(f"Language: {language}")
    print(f"Project: {project_name}")
    print(f"Packs: {packs}")
    print(f"AI mode: {ai_mode}")
    print(f"Communication profile: {communication_profile}")
    print(f"Optimize for: {optimize_for}")
    print(f"Avoid: {avoid}")
    print(f"Artifacts: {artifacts}")
    print(f"External: {external}")
    print()
    if ask_default("Proceed with initialization? yes/no", "yes") != "yes":
        print("Initialization cancelled.")
        return 0

    init_args = [
        "--project-name",
        project_name,
        "--language",
        language,
        "--ai-mode",
        ai_mode,
        "--communication-profile",
        communication_profile,
        "--first-target",
        first_target,
        "--first-session-success",
        success,
        "--use-changelog",
        use_changelog,
        "--use-git",
        use_git,
        "--ai-may-commit",
        ai_may_commit,
        "--ai-may-push",
        ai_may_push,
        "--branch-mode",
        branch_mode,
        "--external-changes-possible",
        external_changes_possible,
        "--force-ddd-adiv",
        force_ddd_adiv,
        "--import-pipeline-package",
        import_pipeline_package,
        "--package-manager-detection",
        package_manager_detection,
        "--project-lifecycle",
        project_lifecycle,
        "--test-coverage",
        test_coverage,
        "--framework",
        framework,
        "--framework-kind",
        framework_kind,
        "--linter",
        linter,
        "--ci",
        ci,
        "--docs",
        docs,
        "--team-size",
        team_size,
        "--velocity",
        velocity,
        "--highest-pain",
        highest_pain,
        "--directive-mode",
        directive_mode,
        "--keep-packs",
        packs,
        "--create-files",
        "--compile-agent",
        "--run-audit",
    ]
    if stack_tags:
        init_args.extend(["--stack-tags", *stack_tags])
    if args.dry_run:
        init_args.append("--dry-run")
    run(repo_root / "tools" / "pipeline" / "Initialize-SocratexPipeline.py", init_args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
