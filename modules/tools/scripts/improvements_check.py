#!/usr/bin/env python3
"""Lists improvements from docs/IMPROVEMENTS.json whose machine check fails on this computer.

Items may carry `verify` (a command as an argument list; exit code 0 means installed) and `scope`
("business" or "game"; no scope means everywhere). The tool only reports. Installing is a separate step
that follows core/rules/SAFETY.md: backup, one form to the owner, wait for the yes.

Usage:
    improvements_check.py                 # all items with a check
    improvements_check.py --scope business
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ITEMS = Path(__file__).resolve().parents[3] / "docs" / "IMPROVEMENTS.json"


def passes(command: list[str]) -> bool:
    """True when the command exists and exits 0. A missing program counts as not installed."""
    program = shutil.which(command[0])
    if program is None:
        return False
    result = subprocess.run([program, *command[1:]], capture_output=True, timeout=60)
    return result.returncode == 0


def missing(items: list[dict], scope: str | None) -> list[dict]:
    wanted = [i for i in items if i.get("verify") and (scope is None or i.get("scope") in (None, scope))]
    return [i for i in wanted if not passes(i["verify"])]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report improvements missing on this computer.")
    parser.add_argument("--scope", choices=("business", "game"), help="Only items for this kind of project.")
    args = parser.parse_args(argv)
    items = json.loads(ITEMS.read_text(encoding="utf-8"))["items"]
    absent = missing(items, args.scope)
    for item in absent:
        print(f"MISSING {item['id']} {item['title']}: {item.get('install', 'see docs/IMPROVEMENTS.json')}")
    print("all checked improvements present" if not absent else f"{len(absent)} missing")
    return 1 if absent else 0


if __name__ == "__main__":
    sys.exit(main())
