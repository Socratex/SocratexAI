#!/usr/bin/env python3
"""Generate installed AGENTS.md instructions for selected project packs."""

from __future__ import annotations

import argparse

from pipeline_script_helpers import configure_stdio, package_root, split_values, write_text


BASE_LINES = [
    "# Agent Instructions",
    "",
    "Read `core/AGENT-CONTRACT.json` first.",
    "",
    "Read `PIPELINE-CONFIG.json` when present, then read `core/communication-profiles/<communication.profile>.txt`. If the selected profile is missing, read `core/communication-profiles/standard.txt` and report the missing profile.",
    "",
    "Read `DOCS.json` before reading, creating, renaming, or updating project documents. Use it to choose what to read and where to write new information.",
    "",
    "Then read the active state file as the compact active project state. For code projects, use `STATE.json`; for non-code user-facing memory, use `STATE.md`.",
    "",
    "Read `core/MEMORY-MODEL.json` for active state, branch-scoped state, plans, decisions, and context capsules.",
    "",
    "Use `core/ACTIVATION-CHECK.json` after the first prompt handled under an installed pipeline to verify the rules are loaded.",
    "",
    "Use `core/UPDATE-PROTOCOL.json` when the user asks to update, refresh, reinstall, or pull the latest pipeline.",
    "",
    "Use `core/REMOVAL-PROTOCOL.json` when the user asks to remove, uninstall, delete, or disable the pipeline.",
    "",
    "Read `core/PROMOTION-RULES.json` before moving work between memory layers.",
    "",
    "Read `core/PROJECT-PROFILE.json` when `PIPELINE-CONFIG.json` contains `project_profile`.",
    "",
    "Read `core/ROI-BIAS.json` before ranking recommendations, planning work, or reviewing tradeoffs.",
    "",
    "Read `core/SCRIPT-FALLBACK.json` before bypassing any script that cannot run.",
    "",
    "Use `core/CONTEXT-COMPACTION.json` during long or drift-prone sessions.",
    "",
    "## Active Project Packs",
    "",
]

CODE_READS = [
    "project/code/WORKFLOW.json",
    "project/code/BRANCH-MODE.json",
    "project/code/COMMANDS.json",
    "project/code/REGISTRIES.json",
    "project/code/DDD-ADIV.json",
    "project/code/GIT.json",
    "project/code/FROZEN-LAYERS.json",
    "project/code/INSTRUCTION-CAPTURE.json",
    "project/code/DIAGNOSTICS.json",
]


def main() -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packs", "-Packs", nargs="*", default=["generic"])
    parser.add_argument("--output-path", "-OutputPath", default="AGENTS.md")
    args = parser.parse_args()

    root = package_root()
    packs = split_values(args.packs)
    lines = list(BASE_LINES)
    for pack in packs:
        pack_path = root / "project" / pack / "PACK.json"
        if not pack_path.is_file():
            raise SystemExit(f"Unknown or unavailable pack: {pack}")
        lines.append(f"- `project/{pack}/PACK.json`")
    if "code" in packs:
        lines.extend(["", "## Code Project Reads", ""])
        lines.extend(f"- `{path}`" for path in CODE_READS)
    output = root / args.output_path
    write_text(output, "\n".join(lines))
    print(f"Compiled agent instructions: {args.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
