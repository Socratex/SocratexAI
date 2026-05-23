#!/usr/bin/env python3
"""Append a JSON or Markdown changelog entry."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from repo_tool_helpers import read_json, repo_root, write_json


def parse_date(text: str) -> datetime:
    if len(text.strip()) == 10:
        return datetime.strptime(text.strip(), "%Y-%m-%d")
    return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")


def valid_timestamp(text: str) -> bool:
    if not text.strip():
        return True
    try:
        datetime.strptime(text.strip(), "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False


def append_json(path: Path, entry_date: datetime, feature: str, version: str, summary: list[str], why: str) -> None:
    document = read_json(path)
    changelog: dict[str, Any] = document.get("content", document) if isinstance(document, dict) else {}
    entries = changelog.get("entries")
    if not isinstance(entries, list):
        raise SystemExit("JSON changelog must contain entries field either at top-level or under content.")
    if entries and isinstance(entries[-1], dict) and str(entries[-1].get("date", "")).strip():
        last_date = parse_date(str(entries[-1]["date"]))
        if entry_date.date() < last_date.date():
            raise SystemExit(
                f"Refusing to append an older JSON changelog date. Last entry is {last_date:%Y-%m-%d}; requested {entry_date:%Y-%m-%d}."
            )
    change = " ".join(summary).strip()
    if why.strip():
        change = f"{change} Why: {why.strip()}"
    entries.append({"version": version, "date": entry_date.strftime("%Y-%m-%d"), "feature": feature, "change": change})
    write_json(path, document)
    print(f"OK: appended JSON changelog entry for {feature}.")


def append_markdown(path: Path, entry_date: datetime, summary: list[str], why: str, auto_timestamp: bool) -> None:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("# Changelog"):
        raise SystemExit("Changelog must start with '# Changelog'.")
    headings = [line.strip().removeprefix("## ").strip() for line in content.splitlines() if line.startswith("## ")]
    if headings:
        last_date = parse_date(headings[-1])
        if auto_timestamp and entry_date < last_date:
            entry_date = last_date + timedelta(minutes=1)
        if entry_date < last_date:
            raise SystemExit(
                f"Refusing to append an older changelog timestamp. Last entry is {last_date:%Y-%m-%d %H:%M}; requested {entry_date:%Y-%m-%d %H:%M}."
            )
    lines = [f"## {entry_date:%Y-%m-%d %H:%M}", *[f"- {line}" for line in summary]]
    if why.strip():
        lines.append(f"- Why: {why.strip()}")
    path.write_text(content.rstrip() + "\n\n" + "\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    print(f"OK: appended changelog entry at {entry_date:%Y-%m-%d %H:%M}.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Append a changelog entry.")
    parser.add_argument("--summary", "-Summary", nargs="*", default=[])
    parser.add_argument("--why", "-Why", default="")
    parser.add_argument("--feature", "-Feature", default="manual_changelog_entry")
    parser.add_argument("--version", "-Version", default="0.2.0-alpha")
    parser.add_argument("--timestamp", "-Timestamp", default="")
    parser.add_argument("--path", "-Path", default="CHANGELOG.json")
    parser.add_argument("--repo-root", default="")
    args = parser.parse_args()

    if not valid_timestamp(args.timestamp):
        raise SystemExit(
            f"Invalid --timestamp value '{args.timestamp}'. If this was intended as another summary line, pass --summary as explicit repeated values."
        )
    summary = [line.strip() for line in args.summary if line.strip()]
    if not summary:
        raise SystemExit("At least one non-empty --summary line is required.")

    root = repo_root(Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve())
    path = Path(args.path)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        raise SystemExit(f"Missing changelog file: {args.path}")

    auto_timestamp = not args.timestamp.strip()
    entry_date = datetime.now() if auto_timestamp else parse_date(args.timestamp)
    if path.suffix.lower() == ".json":
        append_json(path, entry_date, args.feature, args.version, summary, args.why)
    else:
        append_markdown(path, entry_date, summary, args.why, auto_timestamp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
