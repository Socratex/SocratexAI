#!/usr/bin/env python3
"""Load project-specific code design context and write its gate marker."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "codebase"))
from context_gate_helpers import configure_stdio, declared_design_reads, git_head  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", "-ProjectRoot", default=".")
    parser.add_argument("--quiet", "-Quiet", action="store_true")
    return parser.parse_args()


def write_gate(project_root: Path, reads: list[str], loaded: list[dict[str, object]], missing: list[str], note: str | None = None) -> None:
    gate = {
        "schema": 1,
        "tool": "project_design_context",
        "loaded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "project_root": str(project_root),
        "repo_head": git_head(project_root),
        "declared_reads": reads,
        "loaded": loaded,
    }
    if missing:
        gate["missing"] = missing
    if note:
        gate["note"] = note
    gate["full_set_loaded"] = len(missing) == 0
    gate_path = project_root / "ignored/project_design_context_gate.json"
    gate_path.parent.mkdir(parents=True, exist_ok=True)
    gate_path.write_text(json.dumps(gate, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def main() -> int:
    configure_stdio()
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    reads = declared_design_reads(project_root)
    if reads is None:
        print(f"ERROR: Project PIPELINE-CONFIG.json not found at: {project_root / '.aiassistant/socratex/PIPELINE-CONFIG.json'}", file=sys.stderr)
        return 1

    if not reads:
        if not args.quiet:
            print("==> project_design_context: no code_design_required_reads declared")
            print(f"Project: {project_root}")
            print("Workspace base rules from knowledge_code_context.py still apply.")
        write_gate(project_root, [], [], [], "Project declares no code_design_required_reads; workspace base rules apply.")
        return 0

    if not args.quiet:
        print(f"==> project_design_context: loading {len(reads)} project-specific design files")
        print(f"Project: {project_root}")
        print("")

    loaded: list[dict[str, object]] = []
    missing: list[str] = []
    for relative in reads:
        path = project_root / relative
        if not path.is_file():
            print(f"WARNING: Missing required read: {relative}", file=sys.stderr)
            missing.append(relative)
            continue
        if not args.quiet:
            print(f"===== {relative} =====")
            print("")
            print(path.read_text(encoding="utf-8", errors="replace"))
            print("")
        stat = path.stat()
        loaded.append(
            {
                "path": relative,
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )

    write_gate(project_root, reads, loaded, missing)
    if not args.quiet:
        gate_path = project_root / "ignored/project_design_context_gate.json"
        print("")
        print(f"Gate file written: {gate_path}")
        if missing:
            print("")
            print(f"WARNING: {len(missing)} declared read(s) missing; gate marked full_set_loaded=false.", file=sys.stderr)
    return 2 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
