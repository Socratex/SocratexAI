#!/usr/bin/env python3
"""Python document audit entrypoint for the Python-first smoke path."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> int:
    completed = subprocess.run(command, cwd=cwd, check=False)
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit SocratexPipeline JSON document contracts.")
    parser.add_argument("--repo-root", default=".", help="Repository root.")
    parser.add_argument("--strict", action="store_true", help="Reserved for parity with the legacy audit command.")
    parser.add_argument("--initialized", action="store_true", help="Reserved for parity with the legacy audit command.")
    args = parser.parse_args()

    root = Path(args.repo_root).resolve()
    audit_json = root / "tools" / "documents" / "audit_json_docs.py"
    if not audit_json.is_file():
        print(f"ERROR: missing JSON audit engine: {audit_json}", file=sys.stderr)
        return 1
    return run([sys.executable, str(audit_json), "--repo-root", str(root)], root)


if __name__ == "__main__":
    raise SystemExit(main())
