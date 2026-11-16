#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "pipeline"))
import python_runtime  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Report SocratexAI tooling runtime availability.")
    parser.add_argument("--root-key", default="runtime", help="JSON root key to emit.")
    parser.add_argument("--profile", default="", help="Optional project profile label for callers that store runtime status by profile.")
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when the required Python runtime is missing or too old.")
    parser.add_argument("--json", action="store_true", help="Accepted for caller readability; output is always JSON.")
    args = parser.parse_args()

    status = python_runtime.runtime_report(Path.cwd())
    if args.profile:
        status["profile"] = args.profile
    print(json.dumps({args.root_key: status}, ensure_ascii=False, indent=4))
    return 1 if args.strict and not status["python3"]["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
