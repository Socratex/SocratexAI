#!/usr/bin/env python3
"""Create a diagnostics JSON summary from recent files under a logs directory."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402


TEXT_EXTENSIONS = {".log", ".txt", ".json", ".xml", ".csv", ".md"}


def tail_text(path: Path, line_count: int) -> str:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def resolve_path(repo_root: Path, value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else repo_root / path


def get_property(value: Any, name: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(name, default)
    return default


def format_summary_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return f"count={len(value)}"
    if isinstance(value, dict):
        return "object"
    return str(value)


def add_metadata_field(fields: list[str], name: str, value: Any) -> None:
    formatted = format_summary_value(value)
    if formatted.strip():
        fields.append(f"{name}={formatted}")


def description_tokens(description: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9_]+", description.lower()) if len(token) >= 3]


def score_log_name(path: Path, tokens: list[str]) -> int:
    name = path.stem.lower()
    return sum(1 for token in tokens if token in name)


def file_timestamp(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def print_debug_dumps(logs_root: Path, description: str, latest: bool, max_items: int) -> None:
    tokens = description_tokens(description)
    json_logs = sorted(logs_root.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not latest and tokens:
        json_logs = sorted(json_logs, key=lambda path: (-score_log_name(path, tokens), -path.stat().st_mtime))
    json_logs = json_logs[:max_items]

    print()
    print("## Debug Dumps")
    if not json_logs:
        print("(none)")
        return

    for log in json_logs:
        png_path = log.with_suffix(".png")
        png_status = "png=yes" if png_path.exists() else "png=no"
        print(f"{file_timestamp(log)} {log.name} {png_status}")
        try:
            payload = read_json(log)
            metadata: list[str] = []
            system = get_property(payload, "system", {})
            add_metadata_field(metadata, "schema", get_property(payload, "schema_version"))
            add_metadata_field(metadata, "created_at_utc", get_property(payload, "created_at_utc"))
            add_metadata_field(metadata, "mode", get_property(payload, "game_mode"))
            add_metadata_field(metadata, "biome", get_property(system, "biome"))
            add_metadata_field(metadata, "fps", get_property(system, "fps"))
            add_metadata_field(metadata, "player_position", get_property(system, "player_position"))
            add_metadata_field(metadata, "runtime_events", get_property(payload, "runtime_events"))
            if metadata:
                print(f"  {'; '.join(metadata)}")
            for suffix in ("console_tail.txt", "runtime_tail.log"):
                sidecar_path = log.with_name(f"{log.stem}_{suffix}")
                if sidecar_path.exists():
                    print(f"  sidecar={sidecar_path.name} bytes={sidecar_path.stat().st_size}")
        except Exception:
            print("  metadata=parse-failed")


def iter_jsonl(path: Path) -> list[Any]:
    entries: list[Any] = []
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not raw_line.strip():
            continue
        try:
            entries.append(json.loads(raw_line))
        except json.JSONDecodeError:
            continue
    return entries


def print_session_debug_dumps(logs_root: Path, max_items: int) -> None:
    session_logs = sorted(logs_root.glob("*_f4_debug.jsonl"), key=lambda path: path.stat().st_mtime, reverse=True)[:max_items]
    print()
    print("## Session Debug Dumps")
    if not session_logs:
        print("(none)")
        return

    for session_log in session_logs:
        print(f"{file_timestamp(session_log)} {session_log.name}")
        for entry in iter_jsonl(session_log)[-max_items:]:
            payload = get_property(entry, "payload", {})
            debug_payload = get_property(payload, "debug_payload", {})
            screenshot_file = str(get_property(payload, "screenshot_file", "") or "")
            screenshot_path = session_log.parent / screenshot_file if screenshot_file.strip() else None
            png_status = "png=yes" if screenshot_path and screenshot_path.exists() else "png=no"
            metadata: list[str] = []
            system = get_property(debug_payload, "system", {})
            add_metadata_field(metadata, "title", get_property(entry, "title"))
            add_metadata_field(metadata, "name", get_property(payload, "name"))
            add_metadata_field(metadata, "created_at_utc", get_property(debug_payload, "created_at_utc"))
            add_metadata_field(metadata, "mode", get_property(debug_payload, "game_mode"))
            add_metadata_field(metadata, "biome", get_property(system, "biome"))
            add_metadata_field(metadata, "fps", get_property(system, "fps"))
            add_metadata_field(metadata, "player_position", get_property(system, "player_position"))
            print(f"  {png_status}; {'; '.join(metadata)}")


def print_diagnostics(logs_diagnostics_root: Path, max_items: int) -> None:
    print()
    print("## Diagnostics")
    if not logs_diagnostics_root.exists():
        print("(none)")
        return

    diagnostics = [
        path
        for path in sorted(logs_diagnostics_root.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True)
        if path.is_file() and path.name not in {".gitkeep", "desktop.ini"}
    ][:max_items]
    if not diagnostics:
        print("(none)")
        return
    for path in diagnostics:
        print(f"{file_timestamp(path)} {path.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("description_arg", nargs="?", default="")
    parser.add_argument("--description", "-Description", default="")
    parser.add_argument("--repo-root", default="")
    parser.add_argument("--mode", choices=("json", "dump-list"), default="json")
    parser.add_argument("--logs-path", "-LogsPath", default="logs")
    parser.add_argument("--logs-diagnostics-path", default="logs-diagnostics")
    parser.add_argument("--tail-lines", "-TailLines", type=int, default=160)
    parser.add_argument("--output-path", "-OutputPath", default="DIAGNOSTICS-SUMMARY.json")
    parser.add_argument("--latest", "-Latest", action="store_true", help="Sort debug dumps only by newest timestamp.")
    parser.add_argument("--max-items", "-MaxItems", type=int, default=8, help="Maximum rows per dump-list section.")
    return parser.parse_args()


def write_json_summary(repo_root: Path, description: str, logs_path: Path, output_path: Path, logs_path_label: str, tail_lines: int) -> int:
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
                preview = tail_text(path, tail_lines)
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
        "logs_path": logs_path_label,
        "evidence": evidence,
        "observed_facts": [],
        "current_hypothesis": "TBD",
        "smallest_source_owned_fix_or_diagnostic_step": "TBD",
        "verification": "TBD",
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=4), encoding="utf-8")
    print(f"Wrote diagnostics summary: {output_path}")
    return 0


def print_dump_list(description: str, logs_path: Path, logs_diagnostics_path: Path, latest: bool, max_items: int) -> int:
    print("# Log Summary")
    print(f"Description: {description}")
    print(f"Generated: {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}")

    if not logs_path.exists():
        print()
        print("logs/ is missing.")
        return 0

    print_debug_dumps(logs_path, description, latest, max_items)
    print_session_debug_dumps(logs_path, max_items)
    print_diagnostics(logs_diagnostics_path, max_items)
    return 0


def main() -> int:
    configure_stdio()
    args = parse_args()
    description = (args.description or args.description_arg).strip()
    if not description:
        print("ERROR: log_summary.py requires --description.", file=sys.stderr)
        return 2

    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    logs_path = resolve_path(repo_root, args.logs_path)
    logs_diagnostics_path = resolve_path(repo_root, args.logs_diagnostics_path)
    output_path = resolve_path(repo_root, args.output_path)
    if args.mode == "dump-list":
        return print_dump_list(description, logs_path, logs_diagnostics_path, args.latest, args.max_items)
    return write_json_summary(repo_root, description, logs_path, output_path, args.logs_path, args.tail_lines)


if __name__ == "__main__":
    raise SystemExit(main())
