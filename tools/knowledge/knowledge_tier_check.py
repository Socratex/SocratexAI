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
    parser.add_argument("--repo-root", "-RepoRoot", default=".", help="Repository root to scan.")
    parser.add_argument("--include-templates", "-IncludeTemplates", action="store_true")
    parser.add_argument("--format", "-Format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--backend", "-Backend", choices=knowledge_tier_report.BACKENDS, default="documents", help="Tier metadata backend.")
    parser.add_argument("--db", default=knowledge_tier_report.DEFAULT_DB_PATH, help="SQLite knowledge database path relative to repo root.")
    parser.add_argument("--file-dir", default=knowledge_tier_report.DEFAULT_FILE_DIR, help="Knowledge file fallback directory relative to repo root.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    report = knowledge_tier_report.scan_repo(repo_root, args.include_templates, args.backend, Path(args.db), Path(args.file_dir))
    if args.format == "json":
        import json

        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(knowledge_tier_report.format_markdown(report, show_entries=True))
    summary = report["summary"]
    return 1 if summary["missing_context_tier"] or summary["invalid_context_tier"] or summary["parse_errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
