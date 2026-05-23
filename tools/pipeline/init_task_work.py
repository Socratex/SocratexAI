#!/usr/bin/env python3
"""Create the current task work file from the SocratexPipeline template."""

from __future__ import annotations

import argparse
from pathlib import Path

from pipeline_script_helpers import configure_stdio, content_of, package_root, read_json, write_json


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", "-Path", default="docs-tech/cache/current_task.json")
    parser.add_argument("--title", "-Title", default="TBD")
    parser.add_argument("--source-request", "-SourceRequest", default="TBD")
    parser.add_argument("--force", "-Force", action="store_true")
    parser.add_argument("--dry-run", "-DryRun", action="store_true")
    args = parser.parse_args()

    root = package_root()
    target = root / args.path
    template = root / "templates" / "code" / "current_task.json"
    if not template.is_file():
        raise SystemExit(f"Missing task work template: {template}")
    if target.exists() and not args.force:
        print(f"Task work file already exists: {target}")
        return 0
    if args.dry_run:
        print(f"Would create task work file: {target}")
        return 0
    document = read_json(template)
    task_document = content_of(document)
    if isinstance(task_document, dict) and isinstance(task_document.get("task"), dict):
        task_document["task"]["title"] = args.title
        task_document["task"]["source_request"] = args.source_request
    write_json(target, document)
    print(f"Created task work file: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
