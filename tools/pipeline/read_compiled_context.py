#!/usr/bin/env python3
"""Read source compiled instructions or compact source context by alias."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import configure_stdio  # noqa: E402


ALIASES = {
    "entrypoint": "codex/ENTRYPOINT.md",
    "rules": "codex/RULES.compiled.md",
    "workflow": "codex/WORKFLOW.compiled.md",
    "contextual_workflow": "codex/CONTEXTUAL-WORKFLOW.compiled.md",
    "team": "codex/TEAM.compiled.md",
    "bootstrap": "docs-tech/PIPELINE-BOOTSTRAP.json",
    "pipeline_bootstrap": "docs-tech/PIPELINE-BOOTSTRAP.json",
    "docs": "DOCS.json",
    "scripts": "SCRIPTS.json",
    "script": "SCRIPTS.json",
    "commands": "COMMANDS.json",
    "command": "COMMANDS.json",
    "flows": "FLOWS.json",
    "flow": "FLOWS.json",
    "engineering": "context-docs/ENGINEERING.json",
    "agent_contract": "core/AGENT-CONTRACT.json",
}

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized_hash_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    normalized = "\n".join(lines).rstrip("\n")
    return normalized + "\n" if normalized else ""


def sha256_file(path: Path) -> str:
    return hashlib.sha256(normalized_hash_text(read_text(path)).encode("utf-8")).hexdigest()


def relative_to_or_none(path: Path, root: Path) -> str | None:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return None


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def resolve_target(repo_root: Path, compiled_root: Path, document: str) -> tuple[Path, str | None]:
    requested = document.strip()
    relative_path = ALIASES.get(requested.lower(), requested)
    candidates = [compiled_root / relative_path, repo_root / relative_path]
    for candidate in candidates:
        if candidate.is_file():
            target = candidate.resolve()
            return target, relative_to_or_none(target, compiled_root)
    known = ", ".join(
        [
            "entrypoint",
            "rules",
            "workflow",
            "contextual_workflow",
            "team",
            "bootstrap",
            "docs",
            "scripts",
            "commands",
            "flows",
            "engineering",
            "agent_contract",
        ]
    )
    raise ValueError(f"No compiled/source context document matches '{document}'. Known aliases: {known}.")


def check_stale(compiled_root: Path, target_path: Path, compiled_relative_path: str | None) -> None:
    if not compiled_relative_path:
        return
    checksum_path = compiled_root / "checksum.json"
    if not checksum_path.is_file():
        return
    checksum = load_json(checksum_path)
    output_hashes = checksum.get("output_hashes", {})
    if not isinstance(output_hashes, dict) or compiled_relative_path not in output_hashes:
        return
    expected_hash = str(output_hashes[compiled_relative_path])
    current_hash = sha256_file(target_path)
    if current_hash != expected_hash:
        raise ValueError(
            f"Compiled context for '{compiled_relative_path}' is stale. "
            "Run tools/pipeline/rebuild_ai_compiled_context.py before reading compiled context."
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("document", nargs="?")
    parser.add_argument("--document", "-Document", dest="document_option", default="")
    parser.add_argument("--compiled-root", default="")
    parser.add_argument("--allow-stale", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    compiled_root = Path(args.compiled_root).resolve() if args.compiled_root else repo_root / "AI-compiled"
    if not compiled_root.is_dir():
        raise FileNotFoundError(f"Compiled root does not exist: {compiled_root}")

    document = args.document_option or args.document
    if not document:
        raise SystemExit("--document or positional document is required.")
    target_path, compiled_relative_path = resolve_target(repo_root, compiled_root.resolve(), document)
    if not args.allow_stale:
        check_stale(compiled_root.resolve(), target_path, compiled_relative_path)

    content = read_text(target_path)
    if args.json:
        print(
            json.dumps(
                {
                    "document": document,
                    "path": str(target_path),
                    "compiled_path": compiled_relative_path,
                    "content": content,
                },
                ensure_ascii=False,
                indent=4,
            )
        )
        return 0
    sys.stdout.write(content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
