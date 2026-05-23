#!/usr/bin/env python3
"""Create branch-scoped SocratexAI memory files from templates."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

from pipeline_script_helpers import configure_stdio, package_root, write_text


def current_branch(root: Path) -> str:
    completed = subprocess.run(["git", "branch", "--show-current"], cwd=root, check=False, capture_output=True, text=True)
    if completed.returncode == 0 and completed.stdout.strip():
        return completed.stdout.strip()
    return "unknown-branch"


def safe_branch_name(value: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "-", value).strip() or "unknown-branch"


def copy_template(source: Path, destination: Path, dry_run: bool) -> None:
    if not source.is_file():
        raise SystemExit(f"Missing branch template: {source}")
    if dry_run:
        print(f"Would create: {destination}")
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")


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


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch", "-Branch", default="")
    parser.add_argument("--branch-files-dir", "-BranchFilesDir", default="ignored/ai-socratex")
    parser.add_argument("--template-dir", "-TemplateDir", default="")
    parser.add_argument("--ensure-gitignore", "-EnsureGitignore", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    root = package_root()
    template_dir = Path(args.template_dir).resolve() if args.template_dir else root / "templates" / "code" / "branch"
    branch = safe_branch_name(args.branch or current_branch(root))
    target = root / args.branch_files_dir
    paths = {
        "state": target / f"{branch}-STATE.md",
        "plan": target / f"{branch}-PLAN.md",
        "todo": target / "TODO.md",
    }
    if args.ensure_gitignore:
        ensure_gitignore(root, args.dry_run)
    copy_template(template_dir / "BRANCH-STATE.md", paths["state"], args.dry_run)
    copy_template(template_dir / "BRANCH-PLAN.md", paths["plan"], args.dry_run)
    copy_template(template_dir / "BRANCH-TODO.md", paths["todo"], args.dry_run)
    print("Branch memory ready:")
    print(f"  state: {paths['state']}")
    print(f"  plan:  {paths['plan']}")
    print(f"  todo:  {paths['todo']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
