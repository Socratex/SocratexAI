#!/usr/bin/env python3
"""Create a diagnostics JSON summary from recent files under a logs directory."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


TEXT_EXTENSIONS = {".log", ".txt", ".json", ".xml", ".csv", ".md"}


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


def tail_text(path: Path, line_count: int) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("description_arg", nargs="?", default="")
    parser.add_argument("--description", "-Description", default="")
    parser.add_argument("--logs-path", "-LogsPath", default="logs")
    parser.add_argument("--tail-lines", "-TailLines", type=int, default=160)
    parser.add_argument("--output-path", "-OutputPath", default="DIAGNOSTICS-SUMMARY.json")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    description = args.description or args.description_arg
    if not description:
        print("ERROR: log_summary.py requires --description.", file=sys.stderr)
        return 2

    repo_root = Path(__file__).resolve().parents[2]
    logs_path = (repo_root / args.logs_path).resolve() if not Path(args.logs_path).is_absolute() else Path(args.logs_path)
    summary_path = (repo_root / args.output_path).resolve() if not Path(args.output_path).is_absolute() else Path(args.output_path)
    logs_path.mkdir(parents=True, exist_ok=True)
    (logs_path / ".gitkeep").touch(exist_ok=True)

    files = sorted(
        [path for path in logs_path.rglob("*") if path.is_file() and path.name != ".gitkeep"],
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    evidence: list[dict[str, object]] = []
    if not files:
        evidence.append({"path": None, "modified": None, "preview": f"No diagnostic files found under {args.logs_path}."})
    else:
        for path in files[:5]:
            try:
                relative_path = path.relative_to(repo_root).as_posix()
            except ValueError:
                relative_path = path.as_posix()
            preview = "Binary or unsupported text preview; inspect manually if relevant."
            if path.suffix.lower() in TEXT_EXTENSIONS:
                preview = tail_text(path, args.tail_lines)
            evidence.append(
                {
                    "path": relative_path,
                    "modified": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds"),
                    "preview": preview,
                }
            )

    summary = {
        "summary": "Diagnostics summary",
        "description": description,
        "logs_path": args.logs_path,
        "evidence": evidence,
        "observed_facts": [],
        "current_hypothesis": "TBD",
        "smallest_source_owned_fix_or_diagnostic_step": "TBD",
        "verification": "TBD",
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"Wrote diagnostics summary: {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
