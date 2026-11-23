#!/usr/bin/env python3
"""Build INDEX.json (the map agents read first) from frontmatter, SKILL.md files and tool docstrings.

Sources:
  core/, docs/, claude/, codex/ *.md  -> frontmatter `description` (or the first heading)
  skills/*/SKILL.md, claude/skills/*  -> skill name + description
  claude/agents/*.md                  -> agent name + description
  modules/tools/scripts/*.py, modules/engine/*.py, modules/stages/review/*.py -> first docstring line
  docs/specs/*/*.md                   -> frontmatter `description`
  modules/engine|stages/review|stages/planning/*.json -> `purpose` or `title` (module.json excluded)
  core/*.json                         -> `purpose` or `schema`
  defaults/*.json                     -> fixed description; defaults/adapters and defaults/preferences -> `what`
  core/*.py, core/sox, tests/test_*.py -> docstring / test name
  modules/**/module.json              -> `modules` section (name, kind, what, when, entry, paths); validated first

Usage:
    python modules/tools/scripts/build_index.py           # rewrite INDEX.json
    python modules/tools/scripts/build_index.py --check   # exit 1 when INDEX.json is stale or a manifest is broken
"""

from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "core"))

import core  # noqa: E402

INDEX = ROOT / "INDEX.json"
MODULES_DIR = "modules"
DOC_DIRS = ["core", "defaults", "defaults/rules", "defaults/templates", "docs", "claude", "claude/mods/flow-panel", "codex", "templates/project"]


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


def doc_folders() -> list[str]:
    specs = ROOT / "docs" / "specs"
    return DOC_DIRS + (sorted(rel(p) for p in specs.iterdir() if p.is_dir()) if specs.is_dir() else [])


class ManifestError(Exception):
    """Raised with every manifest problem, one `file: key: message` line each."""


def manifest_files(root: Path = ROOT) -> list[Path]:
    return sorted((root / MODULES_DIR).glob("**/module.json"))


def _overlaps(a: str, b: str, module_dirs: frozenset[str] = frozenset()) -> bool:
    """True when two claimed paths collide; a module folder nested inside another module's path is not a collision."""
    a, b = a.strip("/"), b.strip("/")
    if a == b:
        return True
    inner, outer = (a, b) if a.startswith(b + "/") else (b, a) if b.startswith(a + "/") else ("", "")
    return bool(inner) and inner not in module_dirs


def validate_manifests(root: Path = ROOT) -> tuple[list[dict], list[str]]:
    """Load every module manifest; return (schema-valid manifests, error lines `file: key: message`)."""
    schema = json.loads((root / "core" / "module.schema.json").read_text(encoding="utf-8"))
    errors: list[str] = []
    manifests: list[dict] = []
    claimed: list[tuple[str, str, str]] = []
    module_dirs = frozenset(f.parent.relative_to(root).as_posix() for f in manifest_files(root))
    for file in manifest_files(root):
        label = file.relative_to(root).as_posix()
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{label}: $: cannot read JSON ({exc})")
            continue
        found = core.validate(data, schema, "$")
        errors += [f"{label}: {line}" for line in found]
        if found:
            continue
        manifests.append(data)
        if data["name"] != file.parent.name:
            errors.append(f"{label}: name: '{data['name']}' must equal the folder name '{file.parent.name}'")
        for key in ("paths", "tests"):
            errors += [f"{label}: {key}: '{item}' does not exist" for item in data[key] if not (root / item).exists()]
        for item in data["paths"]:
            errors += [f"{label}: paths: '{item}' overlaps '{other}' of module '{owner}' ({other_label})"
                       for other, owner, other_label in claimed if owner != data["name"] and _overlaps(item, other, module_dirs)]
        claimed += [(item, data["name"], label) for item in data["paths"]]
    names: set[str] = set()
    for data in manifests:
        if data["name"] in names:
            errors.append(f"module name '{data['name']}' is used twice")
        names.add(data["name"])
    for data in manifests:
        errors += [f"module '{data['name']}': requires: unknown module '{dep}'"
                   for dep in data.get("requires", []) if dep not in names]
    return manifests, errors


def load_modules(root: Path = ROOT) -> list[dict]:
    manifests, errors = validate_manifests(root)
    if errors:
        raise ManifestError("\n".join(errors))
    return manifests


def modules_section(root: Path = ROOT) -> list[dict]:
    keep = ("name", "kind", "what", "when", "entry", "paths")
    return [{key: m[key] for key in keep} for m in sorted(load_modules(root), key=lambda m: (m["kind"], m["name"]))]


def default_json_what(path: Path) -> str:
    """One line for a defaults/*.json file: its `purpose`, else a fixed line for config.json, else its schema id."""
    if path.name == "config.json":
        return "Shipped default values of the layered config (lowest layer, read by core/core.py)"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("purpose") or payload.get("schema", path.stem)


def build() -> dict:
    docs = [{"path": rel(p), "what": frontmatter(p)["description"]}
            for folder in doc_folders() if (ROOT / folder).is_dir()
            for p in sorted((ROOT / folder).glob("*.md"))]
    data = []
    for p in sorted((ROOT / "core").glob("*.json")):
        payload = json.loads(p.read_text(encoding="utf-8"))
        data.append({"path": rel(p), "what": payload.get("purpose") or payload.get("schema", p.stem)})
    data += [{"path": rel(p), "what": payload.get("purpose") or payload.get("title", p.stem)}
             for folder in ("stages/review", "engine", "stages/planning")
             for p in sorted((ROOT / "modules" / folder).glob("*.json")) if p.name != "module.json"
             for payload in [json.loads(p.read_text(encoding="utf-8"))]]
    data += [{"path": rel(p), "what": default_json_what(p)} for p in sorted((ROOT / "defaults").glob("*.json"))]
    data += [{"path": rel(p), "what": json.loads(p.read_text(encoding="utf-8"))["what"]}
             for p in sorted((ROOT / "defaults").glob("*/*.json")) + sorted((ROOT / "defaults").glob("preferences/*/*.json"))]
    data += [{"path": rel(p), "what": "Machine-readable list of AI workflow improvements and their status"}
             for p in [ROOT / "docs" / "IMPROVEMENTS.json"] if p.exists()]
    skills = [{"name": frontmatter(p).get("name", p.parent.name), "path": rel(p.parent),
               "for": "claude" if "claude/skills" in rel(p) else "claude+codex", "what": frontmatter(p)["description"]}
              for folder in ("skills", "claude/skills") if (ROOT / folder).is_dir()
              for p in sorted((ROOT / folder).glob("*/SKILL.md"))]
    agents = [{"name": frontmatter(p).get("name", p.stem), "path": rel(p), "what": frontmatter(p)["description"]}
              for p in sorted((ROOT / "claude" / "agents").glob("*.md"))]
    tools = [{"path": rel(p), "what": docstring(p)}
             for p in sorted((ROOT / "modules" / "tools" / "scripts").glob("*.py")) + sorted((ROOT / "modules" / "engine").glob("*.py"))
             + sorted((ROOT / "modules" / "stages" / "review").glob("*.py"))]
    tools += [{"path": rel(p), "what": docstring(p)}
              for p in sorted((ROOT / "core").glob("*.py")) + [ROOT / "core" / "sox"] if p.is_file()]
    tools += [{"path": rel(p), "what": docstring(p)}
              for p in sorted((ROOT / "tests").glob("test_*.py"))]
    tools.append({"path": "claude/hooks/guard.py", "what": docstring(ROOT / "claude" / "hooks" / "guard.py")})
    return {
        "schema": "socratex-index/v1",
        "purpose": "Map of the SocratexAI global AI core. Read this first; open only the entry you need.",
        "generated_by": "modules/tools/scripts/build_index.py (do not edit by hand)",
        "layers": {
            "defaults": "defaults/RULES.md + defaults/STYLE.md: always loaded for Claude and Codex",
            "local": "local/: private, gitignored owner profile and patterns (created from local.example/)",
            "project": "each project's INDEX.json, AGENTS.md/CLAUDE.md and optional .ai/ overrides",
        },
        "docs": docs,
        "data": data,
        "skills": skills,
        "agents": agents,
        "tools": tools,
        "modules": modules_section(),
    }


def run_index(check: bool) -> int:
    """Write INDEX.json, or with `check` only compare it; 1 when stale or a manifest is broken."""
    try:
        text = json.dumps(build(), indent=2, ensure_ascii=False) + "\n"
    except ManifestError as exc:
        print(f"Module manifests are invalid:\n{exc}")
        return 1
    if check:
        current = INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""
        if current != text:
            print("INDEX.json is stale: run python modules/tools/scripts/build_index.py")
            return 1
        print("INDEX.json is current.")
        return 0
    INDEX.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {rel(INDEX)}")
    return 0


def main(argv: list[str]) -> int:
    return run_index("--check" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
