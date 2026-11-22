#!/usr/bin/env python3
"""Update SocratexAI and the reference packs as two independent steps.

Usage:
    python modules/tools/scripts/update.py self    # git pull --ff-only in SocratexAI (the post-merge hook then regenerates configs)
    python modules/tools/scripts/update.py refs    # fast path to `subrepos.py update`: pinned commits, one try per pack
    python modules/tools/scripts/update.py all     # both; a failure in one never skips the other
Every step prints ok / skipped / error and the exit code is 1 on any error, so a stale checkout is never silent.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))

import subrepos  # noqa: E402


def update_self() -> int:
    try:
        done = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, capture_output=True, text=True, timeout=300)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"[error  ] SocratexAI: {error.__class__.__name__}: {error}")
        return 1
    if done.returncode != 0:
        print(f"[error  ] SocratexAI: pull failed ({(done.stderr or done.stdout).strip()[:200]})")
        return 1
    print(f"[ok     ] SocratexAI: {done.stdout.strip().splitlines()[-1] if done.stdout.strip() else 'done'}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Update SocratexAI and/or the reference packs.")
    parser.add_argument("target", choices=["self", "refs", "all"])
    args = parser.parse_args(argv)
    codes = []
    if args.target in ("self", "all"):
        codes.append(update_self())
    if args.target in ("refs", "all"):
        codes.append(subrepos.cmd_update([]))
    return 1 if any(codes) else 0


if __name__ == "__main__":
    sys.exit(main())
