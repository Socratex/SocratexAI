#!/usr/bin/env python3
"""Strict knowledge tier check using the Python report engine."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_tier_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate context_tier metadata on knowledge entries.")
    parser.add_argument("--repo-root", default=".", help="Repository root to scan.")
    parser.add_argument("--include-templates", action="store_true")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    report = knowledge_tier_report.scan_repo(Path(args.repo_root).resolve(), args.include_templates)
    if args.format == "json":
        import json

        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(knowledge_tier_report.format_markdown(report, show_entries=True))
    summary = report["summary"]
    return 1 if summary["missing_context_tier"] or summary["invalid_context_tier"] or summary["parse_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
