#!/usr/bin/env python3
"""Sync portable AUTO source into a project, preserving its instructions/projection adapters."""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "text"))
from utf8_file_helpers import write_utf8_file

PORTABLE = ("__init__.py", "auto.py", "controller.py", "files.py", "native.py", "selection.py", "roster.py",
            "finalizer.py", "codex_probe.py", "generic_instructions.py", "desktop_bridge.py", "recovery.py", "resume_auto.py", "console_scheduler.py", "watchdog_status.py", "shutdown.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--tools-dir", default="Tools")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve(strict=True)
    target = (root / args.tools_dir / "automation").resolve()
    if not target.is_relative_to(root):
        parser.error("Target must remain inside the explicit project root")
    source = Path(__file__).resolve().parent
    drift = []
    for name in PORTABLE:
        text = (source / name).read_text(encoding="utf-8")
        path = target / name
        if not path.exists() or path.read_text(encoding="utf-8") != text:
            drift.append(name)
            if not args.check:
                write_utf8_file(path, text)
    print(("DRIFT: " if args.check and drift else "OK: ") + (", ".join(drift) or "portable AUTO is in sync"))
    return 1 if args.check and drift else 0


if __name__ == "__main__":
    raise SystemExit(main())
