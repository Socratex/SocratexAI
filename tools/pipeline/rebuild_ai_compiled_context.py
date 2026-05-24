#!/usr/bin/env python3
"""Rebuild generated SocratexAI compiled instructions with Python-only tooling."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402
from shared.file_helpers import normalized_hash_text, read_text, sha256_text, write_text  # noqa: E402


DEFAULT_PACKS = ["code", "generic", "personal", "creative", "gamedev"]

SOURCE_PATHS = [
    "AGENTS.md",
    "README.md",
    "PUBLIC-BOOTSTRAP.md",
    "DOCS.json",
    "WORKFLOW.json",
    "COMMANDS.json",
    "FLOWS.json",
    "SCRIPTS.json",
    "docs-tech/PIPELINE-BOOTSTRAP.json",
    "core/AGENT-CONTRACT.json",
    "core/CONTEXT-TIERS.json",
    "core/MEMORY-MODEL.json",
    "core/PROMOTION-RULES.json",
    "core/FILE-FORMATS.json",
    "core/ROI-BIAS.json",
    "core/TASK-WORK.json",
    "core/SCRIPT-FALLBACK.json",
    "context-docs/ENGINEERING.json",
    "docs-tech/KNOWLEDGE-VIEWS.json",
    "tools/knowledge/knowledge_index.py",
    "tools/knowledge/context_tags.py",
    "tools/knowledge/knowledge_select.py",
    "tools/knowledge/knowledge_compile.py",
    "tools/knowledge/knowledge_check.py",
    "tools/knowledge/knowledge_file_compile.py",
    "tools/knowledge/knowledge_file_check.py",
    "tools/knowledge/knowledge_file_select.py",
    "tools/pipeline/pipeline_bootstrap_index.py",
    "tools/pipeline/compile_pipeline_context.py",
    "tools/pipeline/rebuild_ai_compiled_context.py",
    "tools/pipeline/check_ai_compiled_context.py",
    "templates/WORKFLOW.json",
    "templates/docs-tech/KNOWLEDGE-VIEWS.json",
    "templates/code/context-docs/ENGINEERING.json",
    "templates/team/product.json",
    "templates/team/technical.json",
    "templates/team/performance.json",
    "templates/team/experience.json",
    "templates/team/pipeline.json",
]

def relative_hash(repo_root: Path, relative_path: str) -> str | None:
    path = repo_root / relative_path
    if not path.is_file():
        return None
    return sha256_text(read_text(path))


def repo_text(repo_root: Path, relative_path: str) -> str:
    path = repo_root / relative_path
    if not path.is_file():
        return ""
    return read_text(path)


def load_json(repo_root: Path, relative_path: str) -> Any:
    return json.loads(repo_text(repo_root, relative_path))


def resolve_selector(document: Any, selector: str) -> Any:
    if selector in {"", "."}:
        return document
    if isinstance(document, dict):
        content = document.get("content")
        if isinstance(content, dict):
            if selector in content:
                return content[selector]
            if selector.startswith("content.") and selector[8:] in content:
                return content[selector[8:]]
        items = document.get("items")
        if isinstance(items, dict) and selector in items:
            value = items[selector]
            if isinstance(value, dict) and "data" in value:
                return value["data"]
            return value
        index = document.get("index")
        if isinstance(index, dict) and selector in index and isinstance(items, dict) and selector in items:
            value = items[selector]
            if isinstance(value, dict) and "data" in value:
                return value["data"]
            return value
        docs = document.get("docs")
        if isinstance(docs, dict) and selector in docs:
            return docs[selector]
        commands = document.get("commands")
        if isinstance(commands, dict) and selector in commands:
            return commands[selector]
    current = document
    for part in selector.split("."):
        if isinstance(current, dict):
            if part not in current:
                raise KeyError(f"Missing path part '{part}' in selector '{selector}'")
            current = current[part]
        elif isinstance(current, list):
            current = current[int(part)]
        else:
            raise KeyError(f"Cannot descend into scalar at '{part}' in selector '{selector}'")
    return current


def section_text(repo_root: Path, relative_path: str, selector: str) -> str:
    path = repo_root / relative_path
    if not path.is_file():
        return ""
    value = resolve_selector(json.loads(read_text(path)), selector)
    return json.dumps(value, ensure_ascii=False, indent=4) + "\n"


def communication_profiles_text(repo_root: Path) -> str:
    profile_root = repo_root / "core" / "communication-profiles"
    if not profile_root.is_dir():
        return ""
    blocks: list[str] = []
    for path in sorted(profile_root.glob("*.txt"), key=lambda value: value.name):
        blocks.extend([f"### {path.stem}", "", read_text(path).strip(), ""])
    return "\n".join(blocks).strip()


def existing_packs(repo_root: Path, candidates: list[str]) -> list[str]:
    result: list[str] = []
    for pack in candidates:
        name = str(pack).strip()
        if name and (repo_root / "project" / name / "PACK.json").is_file():
            result.append(name)
    return result


def source_manifest(repo_root: Path, pack_names: list[str]) -> OrderedDict[str, str]:
    sources: OrderedDict[str, str] = OrderedDict()
    for relative_path in SOURCE_PATHS:
        digest = relative_hash(repo_root, relative_path)
        if digest:
            sources[relative_path] = digest
    profile_root = repo_root / "core" / "communication-profiles"
    if profile_root.is_dir():
        for path in sorted(profile_root.glob("*.txt"), key=lambda value: value.name):
            relative_path = f"core/communication-profiles/{path.name}"
            digest = relative_hash(repo_root, relative_path)
            if digest:
                sources[relative_path] = digest
    for pack in pack_names:
        for relative_path in (f"project/{pack}/PACK.json", f"project/{pack}/WORKFLOW.json"):
            digest = relative_hash(repo_root, relative_path)
            if digest:
                sources[relative_path] = digest
    return sources


def compiled_file(relative_path: str, content: str) -> tuple[str, str]:
    if any(token in relative_path for token in ("WORKFLOW", "TEAM", "README", "compile-report")) and len(content.strip()) < 20:
        raise ValueError(f"Compiled file content was unexpectedly short for {relative_path} (length={len(content)}).")
    return relative_path, content.rstrip() + "\n"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def generate_compiled_files(repo_root: Path, packs: list[str]) -> list[tuple[str, str]]:
    pack_names = existing_packs(repo_root, packs)
    manifest = source_manifest(repo_root, pack_names)
    source_hash_text = "\n".join(f"{key}={value}" for key, value in sorted(manifest.items()))
    generated_at = "source-" + sha256_text(source_hash_text)[:12]

    feature_list = repo_text(repo_root, "pipeline_featurelist.json")
    agent_contract_purpose = section_text(repo_root, "core/AGENT-CONTRACT.json", "purpose")
    agent_contract_principles = section_text(repo_root, "core/AGENT-CONTRACT.json", "operating_principles")
    memory_layers = section_text(repo_root, "core/AGENT-CONTRACT.json", "project_memory_layers")
    context_tiers = repo_text(repo_root, "core/CONTEXT-TIERS.json")
    tool_first_json = section_text(repo_root, "core/AGENT-CONTRACT.json", "tool_first_json")
    communication_profiles = communication_profiles_text(repo_root)
    code_workflow_read_order = section_text(repo_root, "project/code/WORKFLOW.json", "read_order")
    code_workflow_general = section_text(repo_root, "project/code/WORKFLOW.json", "general_workflow")
    code_workflow_verification = section_text(repo_root, "project/code/WORKFLOW.json", "verification_boundary")

    entry = f"""# Compiled Codex Entrypoint

Generated: {generated_at}

This directory is generated. Do not edit it by hand.
Edit source instructions, then run:

~~~bash
python -B tools/pipeline/rebuild_ai_compiled_context.py
~~~

Primary rule: use these compiled files for fast agent orientation, then read source files only when exact details or edits are needed.

Read order for Codex:

1. `AI-compiled/codex/RULES.compiled.md`
2. `AI-compiled/codex/WORKFLOW.compiled.md`
3. `docs-tech/PIPELINE-BOOTSTRAP.json` for source-pipeline routing indexes
4. `AI-compiled/codex/CONTEXTUAL-WORKFLOW.compiled.md` only when priority steering matters
5. `AI-compiled/codex/TEAM.compiled.md` only when a role is requested or routed
6. Source files referenced by the compiled layer when implementation requires exact detail

Generated checksum data lives in `AI-compiled/checksum.json`.
"""

    rules = f"""# Compiled Rules for Codex

Generated: {generated_at}

## Source of Truth

- Source instructions remain authoritative.
- `AI-compiled/` is a generated read-optimized cache.
- Do not edit compiled files manually.
- Recompile after source instruction, workflow, template, or pack changes.

## Core Contract Extracts

{agent_contract_purpose}

{agent_contract_principles}

{memory_layers}

## Context Tiers

~~~json
{context_tiers}
~~~

## Communication Profiles

Source of truth: `core/communication-profiles/*.txt`.

{communication_profiles}

## Tool Discipline

{tool_first_json}

## Feature Manifest

~~~json
{feature_list}
~~~
"""

    compiled_workflow_content = f"""# Compiled Workflow for Codex

Generated: {generated_at}

## Code Read Order

{code_workflow_read_order}

## General Workflow

{code_workflow_general}

## Verification Boundary

{code_workflow_verification}

## Recompile Command

Use this command after changing source instructions, templates, core docs, project packs, or compiled-output rules:

~~~bash
python -B tools/pipeline/rebuild_ai_compiled_context.py
~~~

Use this command to check for drift:

~~~bash
python -B tools/pipeline/rebuild_ai_compiled_context.py --check
~~~
"""

    workflow = f"""# Compiled Contextual Workflow Rules

Generated: {generated_at}

`WORKFLOW.json` is opt-in priority context, not default context.

Read it when:

- planning, priority, roadmap, broad feature triage, or project-risk judgment is needed
- a user request may conflict with a higher-priority active pain point
- work must be routed to active plan, backlog, issue registry, or decision log

Do not read it for narrow local fixes without priority or planning impact.

Installed projects get `WORKFLOW.json` from `templates/WORKFLOW.json`.
"""
    if len(compiled_workflow_content.strip()) < 100 or len(workflow.strip()) < 100:
        raise ValueError("Compiled workflow content was unexpectedly short.")

    team_blocks: list[str] = []
    for role in ("product", "technical", "performance", "experience", "pipeline"):
        text = repo_text(repo_root, f"templates/team/{role}.json").strip()
        if text:
            team_blocks.extend([f"## {role}", "", "```json", text, "```", ""])
    team_body = "\n".join(team_blocks)
    team = f"""# Compiled Team Role Lenses

Generated: {generated_at}

Team files are on-demand decision lenses. Load only when the user names a role, asks for team-style review, or `WORKFLOW.json` routes the task to that role.

{team_body}
"""
    if len(team.strip()) < 100:
        raise ValueError("Compiled team content was unexpectedly short.")

    report = OrderedDict(
        [
            ("schema", "socratex-compiled-agent-instructions/v1"),
            ("generated_at", generated_at),
            ("role", "generated_agent_cache"),
            ("source_of_truth", "source instruction files outside AI-compiled"),
            ("do_not_edit_manually", True),
            ("targets", ["codex"]),
            ("packs", pack_names),
            (
                "files",
                [
                    "codex/ENTRYPOINT.md",
                    "codex/RULES.compiled.md",
                    "codex/WORKFLOW.compiled.md",
                    "codex/CONTEXTUAL-WORKFLOW.compiled.md",
                    "codex/TEAM.compiled.md",
                ],
            ),
            ("recompile_command", "python -B tools/pipeline/rebuild_ai_compiled_context.py"),
            ("check_command", "python -B tools/pipeline/rebuild_ai_compiled_context.py --check"),
            ("sources", manifest),
        ]
    )

    readme = """# AI-compiled

Generated read-optimized agent instructions.

Do not edit this directory manually. Edit source instructions and run:

~~~bash
python -B tools/pipeline/rebuild_ai_compiled_context.py
~~~

Codex starts at `codex/ENTRYPOINT.md`.
"""
    index_payload = OrderedDict(
        [
            ("schema", "socratex-compiled-agent-index/v1"),
            ("role", "generated_agent_cache"),
            ("generated_at", generated_at),
            ("do_not_edit_manually", True),
            ("targets", ["codex"]),
            ("entrypoints", OrderedDict([("codex", "codex/ENTRYPOINT.md")])),
            ("recompile_command", "python -B tools/pipeline/rebuild_ai_compiled_context.py"),
            ("check_command", "python -B tools/pipeline/rebuild_ai_compiled_context.py --check"),
        ]
    )

    files = [
        compiled_file("README.md", readme),
        compiled_file("INDEX.json", json_text(index_payload)),
        compiled_file("codex/ENTRYPOINT.md", entry),
        compiled_file("codex/RULES.compiled.md", rules),
        compiled_file("codex/WORKFLOW.compiled.md", compiled_workflow_content),
        compiled_file("codex/CONTEXTUAL-WORKFLOW.compiled.md", workflow),
        compiled_file("codex/TEAM.compiled.md", team),
    ]
    checksums: OrderedDict[str, str] = OrderedDict((relative_path, sha256_text(content)) for relative_path, content in files)
    checksum_payload = OrderedDict(
        [
            ("schema", "socratex-compiled-agent-checksum/v1"),
            ("generated_at", generated_at),
            ("source_hashes", manifest),
            ("output_hashes", checksums),
        ]
    )
    files.append(compiled_file("compile-report.json", json_text(report)))
    files.append(compiled_file("checksum.json", json_text(checksum_payload)))
    return files


def run_knowledge_tool(repo_root: Path, mode: str) -> int:
    tool = _TOOLS_ROOT / "knowledge" / "knowledge_index.py"
    completed = subprocess.run(
        [sys.executable, "-B", str(tool), mode, "--repo-root", str(repo_root)],
        cwd=repo_root,
        check=False,
    )
    return completed.returncode


def compile_knowledge(repo_root: Path) -> int:
    db_code = run_knowledge_tool(repo_root, "compile")
    if db_code != 0:
        print(f"WARNING: SQLite knowledge compile failed with exit code {db_code}. Falling back to compiled JSON table files.", file=sys.stderr)
        return run_knowledge_tool(repo_root, "file-compile")
    return run_knowledge_tool(repo_root, "file-compile")


def check_knowledge(repo_root: Path) -> int:
    db_code = run_knowledge_tool(repo_root, "check")
    if db_code == 0:
        return 0
    print(f"WARNING: SQLite knowledge check failed with exit code {db_code}. Checking compiled JSON table fallback.", file=sys.stderr)
    file_code = run_knowledge_tool(repo_root, "file-check")
    return 0 if file_code == 0 else db_code


def is_installed_child_package(repo_root: Path) -> bool:
    return repo_root.name == "SocratexAI" and (repo_root.parent / "Tools").is_dir()


def check_compiled_files(output_root: Path, files: list[tuple[str, str]]) -> int:
    drift: list[str] = []
    for relative_path, content in files:
        path = output_root / relative_path
        if not path.is_file():
            drift.append(f"missing: {relative_path}")
            continue
        if read_text(path) != content:
            drift.append(f"stale: {relative_path}")
    if not drift:
        return 0
    print("ERROR: compiled agent instructions are stale.")
    for item in drift:
        print(f" - {item}")
    print("Run: python -B tools/pipeline/rebuild_ai_compiled_context.py")
    return 1


def clear_generated_instruction_files(output_root: Path) -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    for relative_path, _ in generate_static_output_file_list():
        path = output_root / relative_path
        if path.is_file():
            path.unlink()
    codex_dir = output_root / "codex"
    if codex_dir.is_dir():
        shutil.rmtree(codex_dir)


def generate_static_output_file_list() -> list[tuple[str, str]]:
    return [
        ("README.md", ""),
        ("INDEX.json", ""),
        ("checksum.json", ""),
        ("compile-report.json", ""),
    ]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rebuild generated SocratexAI compiled instructions.")
    parser.add_argument("--repo-root", default="", help="Repository root. Defaults to this script's package root.")
    parser.add_argument("--output-dir", default="AI-compiled", help="Output directory relative to the repository root.")
    parser.add_argument("--packs", nargs="*", default=DEFAULT_PACKS, help="Project packs to include when present.")
    parser.add_argument("--check", action="store_true", help="Check generated outputs without writing files.")
    parser.add_argument(
        "--skip-knowledge",
        action="store_true",
        help="Do not compile/check AI-compiled/project knowledge artifacts. Auto-enabled for installed child packages.",
    )
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[2]
    output_root = repo_root / args.output_dir
    skip_knowledge = bool(args.skip_knowledge or is_installed_child_package(repo_root))
    files = generate_compiled_files(repo_root, list(args.packs))

    if args.check:
        compiled_code = check_compiled_files(output_root, files)
        if compiled_code != 0:
            return compiled_code
        if not skip_knowledge:
            knowledge_code = check_knowledge(repo_root)
            if knowledge_code != 0:
                return knowledge_code
        print("OK: compiled agent instructions are current.")
        return 0

    clear_generated_instruction_files(output_root)
    for relative_path, content in files:
        write_text(output_root / relative_path, content)
    if not skip_knowledge:
        knowledge_code = compile_knowledge(repo_root)
        if knowledge_code != 0:
            return knowledge_code
    print(f"OK: recompiled AI instructions into {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
