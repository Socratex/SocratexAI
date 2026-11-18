#!/usr/bin/env python3
"""Build INDEX.json (the map agents read first) from frontmatter, SKILL.md files and tool docstrings.

Sources:
  core/, docs/, claude/, codex/ *.md  -> frontmatter `description` (or the first heading)
  skills/*/SKILL.md, claude/skills/*  -> skill name + description
  claude/agents/*.md                  -> agent name + description
  tools/*.py                          -> first docstring line
  core/*.json                         -> `purpose` or `schema`

Usage:
    python tools/build_index.py           # rewrite INDEX.json
    python tools/build_index.py --check   # exit 1 when INDEX.json is stale
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "INDEX.json"
DOC_DIRS = ["core", "core/rules", "core/templates", "docs", "claude", "claude/mods/flow-panel", "codex", "templates/project"]


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
    meta = {}
    if match:
        for line in match.group(1).splitlines():
            key, sep, value = line.partition(":")
            if sep:
                meta[key.strip()] = value.strip().strip('"')
    if "description" not in meta:
        heading = re.search(r"(?m)^#\s+(.+)$", text)
        meta["description"] = heading.group(1).strip() if heading else path.stem
    return meta


def docstring(path: Path) -> str:
    try:
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    except SyntaxError:
        doc = None
    return (doc or path.stem).strip().splitlines()[0]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build() -> dict:
    docs = [{"path": rel(p), "what": frontmatter(p)["description"]}
            for folder in DOC_DIRS if (ROOT / folder).is_dir()
            for p in sorted((ROOT / folder).glob("*.md"))]
    data = []
    for p in sorted((ROOT / "core").glob("*.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        data.append({"path": rel(p), "what": payload.get("purpose") or payload.get("schema", p.stem)})
    data += [{"path": rel(p), "what": "Machine-readable list of AI workflow improvements and their status"}
             for p in [ROOT / "docs" / "IMPROVEMENTS.json"] if p.exists()]
    skills = [{"name": frontmatter(p).get("name", p.parent.name), "path": rel(p.parent),
               "for": "claude" if "claude/skills" in rel(p) else "claude+codex", "what": frontmatter(p)["description"]}
              for folder in ("skills", "claude/skills") if (ROOT / folder).is_dir()
              for p in sorted((ROOT / folder).glob("*/SKILL.md"))]
    agents = [{"name": frontmatter(p).get("name", p.stem), "path": rel(p), "what": frontmatter(p)["description"]}
              for p in sorted((ROOT / "claude" / "agents").glob("*.md"))]
    tools = [{"path": rel(p), "what": docstring(p)} for p in sorted((ROOT / "tools").glob("*.py"))]
    tools.append({"path": "claude/hooks/guard.py", "what": docstring(ROOT / "claude" / "hooks" / "guard.py")})
    return {
        "schema": "socratex-index/v1",
        "purpose": "Map of the SocratexAI global AI core. Read this first; open only the entry you need.",
        "generated_by": "tools/build_index.py (do not edit by hand)",
        "layers": {
            "core": "core/RULES.md + core/STYLE.md: always loaded for Claude and Codex",
            "local": "local/: private, gitignored owner profile and patterns (created from local.example/)",
            "project": "each project's INDEX.json, AGENTS.md/CLAUDE.md and optional .ai/ overrides",
            "legacy": "legacy-pipeline/: the full older framework, enabled per project by flag (see core/RULES.md)",
        },
        "docs": docs,
        "data": data,
        "skills": skills,
        "agents": agents,
        "tools": tools,
    }


def main(argv: list[str]) -> int:
    text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    if "--check" in argv:
        current = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if current != text:
            print("INDEX.json is stale: run python tools/build_index.py")
            return 1
        print("INDEX.json is current.")
        return 0
    INDEX.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {rel(INDEX)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
