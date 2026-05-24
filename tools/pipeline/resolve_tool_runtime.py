#!/usr/bin/env python3
"""Report SocratexPipeline runtime availability with Python-only tooling."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import python_runtime
from pipeline_script_helpers import configure_stdio


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-root", "-SearchRoot", default=".")
    parser.add_argument("--env-var", action="append", default=[], help="Environment variable to check before default Python candidates.")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    root = Path(args.search_root).resolve()
    env_vars = tuple(args.env_var or ["SOCRATEX_PYTHON"])
    python = python_runtime.runtime_report(root, env_vars)["python3"]
    report = {"runtime": {"python3": python}}
    print(json.dumps(report, ensure_ascii=False, indent=4))
    return 1 if args.strict and not python["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
