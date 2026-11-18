#!/usr/bin/env python3
"""Remove an installed SocratexAI pipeline from a target project."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from pipeline_script_helpers import configure_stdio, write_text


MERGE_LINE = "Primary directive: read and respect `SOCRATEX.md` before following this file. SocratexPipeline is installed under `SocratexAI/`."


def resolve_child(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        raise SystemExit(f"Refusing to operate outside target root: {path}") from None
    return path


def remove_owned(root: Path, relative: str, dry_run: bool) -> None:
    path = resolve_child(root, relative)
    if not path.exists():
        return
    if dry_run:
        print(f"Would remove: {path}")
        return
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    print(f"Removed: {path}")


def restore_directive(root: Path, relative: str, restore_old: bool, dry_run: bool) -> None:
    path = resolve_child(root, relative)
    old_path = Path(str(path) + ".old")
    if restore_old and old_path.exists():
        if dry_run:
            print(f"Would restore directive: {old_path} -> {path}")
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_path, path)
        print(f"Restored directive: {path}")
        return
    if not path.is_file():
        return
    content = path.read_text(encoding="utf-8")
    thin = "Read `SOCRATEX.md` first" in content and "SocratexPipeline is installed under `SocratexAI/`" in content
    if thin:
        if dry_run:
            print(f"Would remove thin SocratexAI directive: {path}")
            return
        path.unlink()
        print(f"Removed thin SocratexAI directive: {path}")
        return
    if MERGE_LINE in content:
        updated = content.replace(MERGE_LINE, "").rstrip()
        if dry_run:
            print(f"Would remove SocratexAI merge directive from: {path}")
            return
        write_text(path, updated)
        print(f"Removed SocratexAI merge directive from: {path}")


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-path", "-TargetPath", default=".")
    parser.add_argument("--directive-files", "-DirectiveFiles", nargs="*", default=["AGENTS.md", "CLAUDE.md", "AI.md", ".github/copilot-instructions.md"])
    parser.add_argument("--restore-old-directives", "-RestoreOldDirectives", action="store_true")
    parser.add_argument("--remove-local-working-files", "-RemoveLocalWorkingFiles", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    target_root = Path(args.target_path).resolve()
    owned = ["SOCRATEX.md", "SocratexAI", ".aiassistant/socratex"]
    if args.remove_local_working_files:
        owned.append("ignored/ai-socratex")

    print("==> removing SocratexAI pipeline")
    print(f"Target: {target_root}")
    for directive in args.directive_files:
        restore_directive(target_root, directive, args.restore_old_directives, args.dry_run)
    for relative in owned:
        remove_owned(target_root, relative, args.dry_run)

    assistant_root = resolve_child(target_root, ".aiassistant")
    if assistant_root.is_dir() and not any(assistant_root.iterdir()):
        if args.dry_run:
            print(f"Would remove empty .aiassistant directory: {assistant_root}")
        else:
            assistant_root.rmdir()
            print(f"Removed empty .aiassistant directory: {assistant_root}")
    print("SocratexAI removal complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
