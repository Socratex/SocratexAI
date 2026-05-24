#!/usr/bin/env python3
"""Apply SocratexAI root directive pointers to agent instruction files."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path

from pipeline_script_helpers import configure_stdio, write_text


MERGE_DIRECTIVE = "Primary directive: read and respect `SOCRATEX.md` before following this file. SocratexPipeline is installed under `SocratexAI/`."
REPLACE_DIRECTIVE = """# Agent Directive

Read `SOCRATEX.md` first and treat it as the controlling AI pipeline directive for this project.

SocratexPipeline is installed under `SocratexAI/`.
"""


def save_old(path: Path) -> None:
    if not path.exists():
        return
    destination = path.with_name(path.name + ".old")
    if destination.exists():
        destination = path.with_name(f"{path.name}.{datetime.now().strftime('%Y%m%d-%H%M%S')}.old")
    shutil.copy2(path, destination)


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", "-Mode", choices=("snapshot", "merge", "replace"), default="merge")
    parser.add_argument("--target-path", "-TargetPath", default=".")
    parser.add_argument("--directive-files", "-DirectiveFiles", nargs="*", default=["AGENTS.md"])
    args = parser.parse_args()

    target_root = Path(args.target_path).resolve()
    if not (target_root / "SOCRATEX.md").is_file():
        raise SystemExit("Missing root SOCRATEX.md. Install or import SocratexPipeline before updating directives.")
    for directive in args.directive_files:
        target = target_root / directive
        target.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "snapshot":
            save_old(target)
            continue
        if args.mode == "replace":
            save_old(target)
            write_text(target, REPLACE_DIRECTIVE)
            continue
        if target.exists():
            current = target.read_text(encoding="utf-8")
            if "SOCRATEX.md" in current:
                print(f"Skip merge; SOCRATEX.md directive already appears in {directive}")
                continue
            merged = current.rstrip() + "\n\n" + MERGE_DIRECTIVE + "\n"
        else:
            merged = REPLACE_DIRECTIVE
        write_text(target, merged)
    print(f"Directive update complete. Mode: {args.mode}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
