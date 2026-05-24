#!/usr/bin/env python3
"""Refresh or check code line indexes for active source files."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from shared.repo_helpers import git_lines, normalize_repo_path, repo_root as shared_repo_root  # noqa: E402


CODE_EXTENSIONS = {".gd", ".py", ".bat", ".cmd", ".sh", ".cs", ".js", ".ts"}
EXCLUDED_PREFIXES = ("Tools/Python", "Tools/python-installer", "Tools/tmp/", ".venv/", "build/")

LARGE_FILE_NOTES = {
    "Game/scripts/world/domain/world_traversal_grammar_contract.gd": "Traversal grammar source for generated routes, branch shapes, affordance rules, and terrain-readable structure data. It is large because it currently keeps the route vocabulary and generation constraints together as one explicit contract.",
    "Game/scripts/world/infrastructure/world_generator.gd": "World generator coordinator for deterministic route, chunk, biome, and payload construction. It is large because several generation stages still need a single traceable workflow path while domain_modeling contracts are evolving.",
    "Game/scripts/runtime/application/game_root_controller.gd": "Runtime workflow hub that wires debug capture, camera/runtime coordination, save/report helpers, and high-level gameplay services. It is large because it still owns several cross-cutting runtime integration points that should only be split when a stable boundary is obvious.",
    "Game/scripts/player/domain/player_movement_runtime.gd": "Player movement-state runtime for acceleration, jumping, slopes, contact, and feel-critical movement values. It is large because movement feel is still being tuned and the state transitions need to remain mechanically traceable.",
    "Game/scripts/ui/view/main_menu_controller.gd": "Main menu and character/setup UI controller. It is large because one scene controller still owns several menu modes and input/view transitions.",
    "Game/scripts/player/application/player_controller.gd": "Player movement, combat hooks, input application, and runtime state coordination. It is large because player feel is still under active iteration and premature splitting could obscure the control flow.",
    "Game/scripts/enemies/application/enemy_director.gd": "Enemy spawning, activation, lifecycle, and runtime coordination layer. It is large because enemy workflow still crosses spawn data, pooling, runtime state, and progression-facing behavior.",
    "Game/scripts/world/domain/world_generation_pipeline.gd": "World generation workflow pipeline. It is large because it coordinates route data, biome data, chunk payloads, and deterministic generation contracts.",
    "Game/scripts/world/application/world_runtime_application.gd": "Application-facing world runtime coordinator. It is large because it bridges generated world data, active chunk lifecycle, debug hooks, and presentation/runtime services.",
    "Game/scripts/world/infrastructure/world_procedural_structure_pass.gd": "Procedural structure generation pass for data-backed world dressing and silhouettes. It is large because structure placement still shares deterministic context, biome rules, and payload output in one pass.",
    "Game/scripts/world/application/world_controller.gd": "World scene controller that applies generated data to active runtime nodes. It is large because it coordinates chunk presentation, lifecycle, and world-facing runtime state.",
    "Game/scripts/ui/view/gameplay_hud_controller.gd": "Gameplay HUD controller for player-facing status, overlays, and runtime UI state. It is large because HUD presentation still aggregates several gameplay domains into one screen controller.",
    "Game/scripts/world/domain/world_biome_field_contract.gd": "Biome field contract for deterministic biome sampling and region-level biome data. It is large because it holds the explicit data shape used by generation, diagnostics, and chunk-level consumers.",
    "Game/scripts/world/view/fragments/platform_fragment.gd": "Platform fragment view/runtime script for generated platform presentation and collision behavior. It is large because fragment setup, material/state application, and editor/runtime behavior are still colocated.",
    "Game/test-scripts/terrain_profile_probe.gd": "Terrain profile diagnostic probe for biome terrain shape, slope, and affordance validation. It is large because it collects broad diagnostic summaries rather than serving as runtime gameplay code.",
    "Game/scripts/world/domain/world_biome_region_planner_contract.gd": "Biome region planner contract for macro-region spans, shape scale, centers, and neighbor relationships. It is large because it documents and computes deterministic biome-region planning data in one place.",
    "Game/scripts/world/domain/world_map_runtime.gd": "Runtime map/discovery state for world map data and explored chunk information. It is large because map state currently combines discovery bookkeeping, persistence-facing payloads, and query helpers.",
    "Game/scripts/runtime/application/modes/rift_mode_controller.gd": "Rift gameplay mode controller for mode lifecycle and runtime coordination. It is large because it owns mode-specific setup, transitions, and gameplay-facing services.",
    "Game/scripts/runtime/domain/game_session.gd": "Session progression and run-state domain model. It is large because progression, pickups, upgrades, and run summary state are still represented in one explicit session contract.",
}


def repo_root(start: Path) -> Path:
    return shared_repo_root(start, marker_files=("SCRIPTS.json",), use_git=False)


def code_path(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if Path(normalized).suffix.lower() not in CODE_EXTENSIONS:
        return False
    return not any(normalized.startswith(prefix) for prefix in EXCLUDED_PREFIXES)


def tracked_code_paths(root: Path) -> list[str]:
    return sorted({path for path in [*git_lines(root, ["ls-files"]), *git_lines(root, ["ls-files", "--others", "--exclude-standard"])] if code_path(path)})


def changed_code_paths(root: Path) -> list[str]:
    paths = [
        *git_lines(root, ["diff", "--name-only"]),
        *git_lines(root, ["diff", "--cached", "--name-only"]),
        *git_lines(root, ["ls-files", "--others", "--exclude-standard"]),
    ]
    return sorted({path for path in paths if code_path(path)})


def explicit_code_paths(root: Path, raw_paths: list[str]) -> list[str]:
    paths: set[str] = set()
    root_full = root.resolve()
    for raw_path in raw_paths:
        for candidate in raw_path.split(","):
            text = candidate.strip()
            if not text:
                continue
            full = Path(text)
            if not full.is_absolute():
                full = root_full / full
            resolved = full.resolve()
            try:
                relative = normalize_repo_path(resolved.relative_to(root_full).as_posix())
            except ValueError as exc:
                raise ValueError(f"Path is outside repo: {text}") from exc
            if code_path(relative):
                paths.add(relative)
    return sorted(paths)


def line_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def read_index(path: Path, threshold: int) -> dict[str, Any]:
    if not path.is_file():
        return {"generatedAt": None, "threshold": threshold, "files": []}
    return json.loads(path.read_text(encoding="utf-8"))


def records_from_index(index: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for record in index.get("files", []):
        path = str(record.get("path", ""))
        if path:
            records[path] = {
                "path": path,
                "lines": int(record.get("lines", 0)),
                "extension": str(record.get("extension", "")),
                "large": bool(record.get("large", False)),
            }
    return records


def now_timestamp() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_index_payload(records: dict[str, dict[str, Any]], threshold: int, generated_at: str | None = None) -> dict[str, Any]:
    files = sorted(records.values(), key=lambda record: (-int(record["lines"]), str(record["path"])))
    return {
        "generatedAt": generated_at or now_timestamp(),
        "threshold": threshold,
        "files": files,
    }


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=4) + "\n"


def large_note(path: str) -> str:
    if path in LARGE_FILE_NOTES:
        return LARGE_FILE_NOTES[path]
    extension = Path(path).suffix
    if extension == ".gd":
        return "Runtime script above the size threshold. Keep it documented here until the ownership boundary is clear enough to split without hiding flow."
    if extension == ".py":
        return "Repository helper script above the size threshold. Keep it documented here because it performs non-trivial tooling logic."
    return "Code file above the size threshold. Keep it documented here until it can be reduced or split cleanly."


def build_large_files_document(large_records: list[dict[str, Any]], threshold: int, *, schema: str, tool_display_path: str) -> dict[str, Any]:
    table_lines = [
        f"📊 Current files above {threshold} non-empty code lines.",
        "",
        "| Lines | File | Why It Is Large |",
        "| ---: | --- | --- |",
    ]
    if not large_records:
        table_lines.append("| 0 | _(none)_ | No tracked code files exceed the threshold. |")
    else:
        for record in large_records:
            path = str(record["path"])
            table_lines.append(f"| {int(record['lines'])} | `{path}` | {large_note(path)} |")
    body = {
        "index": ["quick_index", "summary", "large_file_index", "maintenance"],
        "items": {
            "quick_index": {
                "title": "Quick Index",
                "content": "- 📌 Summary\n- 📊 Large File Index\n- 🛠 Maintenance",
            },
            "summary": {
                "title": "📌 Summary",
                "content": f"📌 Generated index of code files above the large-file threshold.\n\n📌 This document is generated from `docs-tech/CODE_LINE_INDEX.json` by `{tool_display_path}`. It tracks code files above {threshold} non-empty lines so large files have an explicit reason to stay large or a visible reason to split later.",
            },
            "large_file_index": {
                "title": "📊 Large File Index",
                "content": "\n".join(table_lines),
            },
            "maintenance": {
                "title": "🛠 Maintenance",
                "content": f"🛠 Update this document through the line-index script instead of editing the table manually.\n\n🛠 Use `python3 -B {tool_display_path}` for a full refresh. Use `python3 -B {tool_display_path} --changed-only` when only changed files need to update their index records from the current git diff.",
            },
        },
        "meta": {
            "document": {
                "title": "📏 Large Files",
                "type": "technical",
                "language": "en",
            },
            "routing": {
                "purpose": "Generated JSON index of code files above the large-file threshold.",
                "read_when": [
                    "When checking large source-owned files or deciding whether a file should be split.",
                    "When code line index tooling is in scope.",
                ],
                "do_not_read_when": [
                    "When the current task is unrelated to repository size, ownership, or tooling.",
                ],
            },
        },
    }
    if schema == "content_metadata":
        body["content"] = body.pop("items")
        body["metadata"] = body.pop("meta")
    return body


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh or check CODE_LINE_INDEX and LARGE_FILES.")
    parser.add_argument("--index-path", "-IndexPath", default="docs-tech/CODE_LINE_INDEX.json")
    parser.add_argument("--large-files-path", "-LargeFilesPath", default="docs-tech/LARGE_FILES.json")
    parser.add_argument("--large-file-threshold", "-LargeFileThreshold", type=int, default=300)
    parser.add_argument("--large-files-schema", choices=["items_meta", "content_metadata"], default="items_meta")
    parser.add_argument("--tool-display-path", default="tools/codebase/update_code_line_index.py")
    parser.add_argument("--paths", "-Paths", nargs="*", default=[])
    parser.add_argument("--root", "-Root", default="")
    parser.add_argument("--changed-only", "-ChangedOnly", action="store_true")
    parser.add_argument("--check", "-Check", action="store_true")
    args = parser.parse_args()

    root = repo_root(Path(args.root) if args.root else Path(__file__).resolve().parents[2])
    if args.paths:
        target_paths = explicit_code_paths(root, args.paths)
    elif args.changed_only:
        target_paths = changed_code_paths(root)
    else:
        target_paths = tracked_code_paths(root)

    index_path = root / args.index_path
    large_path = root / args.large_files_path
    existing_index = read_index(index_path, args.large_file_threshold)
    records = records_from_index(existing_index)
    if not args.changed_only and not args.paths:
        records.clear()

    for path in target_paths:
        count = line_count(root / path)
        if count is None:
            records.pop(path, None)
            continue
        records[path] = {
            "path": path,
            "lines": count,
            "extension": Path(path).suffix,
            "large": count > args.large_file_threshold,
        }

    if args.changed_only and not args.paths:
        for path in list(records.keys()):
            if not (root / path).is_file():
                records.pop(path, None)

    existing_generated_at = existing_index.get("generatedAt")
    compare_payload = build_index_payload(records, args.large_file_threshold, str(existing_generated_at) if existing_generated_at else None)
    compare_index_text = json_text(compare_payload)
    large_records = [record for record in compare_payload["files"] if record["large"]]
    compare_large_text = json_text(build_large_files_document(large_records, args.large_file_threshold, schema=args.large_files_schema, tool_display_path=args.tool_display_path))
    current_index = index_path.read_text(encoding="utf-8").replace("\r\n", "\n") if index_path.is_file() else ""
    current_large = large_path.read_text(encoding="utf-8").replace("\r\n", "\n") if large_path.is_file() else ""
    needs_write = current_index != compare_index_text or current_large != compare_large_text

    if args.check:
        if needs_write:
            print("ERROR: code line index is stale; run tools/codebase/update_code_line_index.py.", file=sys.stderr)
            return 1
        print("OK: code line index is current.")
        return 0

    payload = compare_payload if current_index == compare_index_text else build_index_payload(records, args.large_file_threshold)
    index_text = json_text(payload)
    large_records = [record for record in payload["files"] if record["large"]]
    large_text = json_text(build_large_files_document(large_records, args.large_file_threshold, schema=args.large_files_schema, tool_display_path=args.tool_display_path))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    large_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(index_text, encoding="utf-8", newline="\n")
    large_path.write_text(large_text, encoding="utf-8", newline="\n")
    print(f"OK: indexed {len(payload['files'])} code file(s); {len(large_records)} above {args.large_file_threshold} lines.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
