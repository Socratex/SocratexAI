#!/usr/bin/env python3
"""`sox project check | init | explain`: audit a project against the current SocratexAI setup and onboard it.

The rules are data in core/project-check.json (schema core/project-check.schema.json); this module holds one
check function per rule id. `check` only reads; `init` only creates missing files from templates/project and never
overwrites. Stdlib only.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

import core

ROOT = Path(__file__).resolve().parents[1]
RULES_PATH = Path(__file__).resolve().parent / "project-check.json"
RULES_SCHEMA_PATH = Path(__file__).resolve().parent / "project-check.schema.json"
TEMPLATE_DIR = Path("templates") / "project"
# Template files that cannot live in templates/project because the guard protects every .socratex/config.json.
BUILTIN_TEMPLATES = {".socratex/config.json": '{"schema_version": 1}\n'}
PRUNE_DIRS = {".git", "node_modules", "__pycache__"}


def load_rules(path: Path = RULES_PATH) -> dict:
    """Read and validate the rule file; raises core.ConfigError. Every rule id must have a check function."""
    data = core._read_json(path)  # noqa: SLF001
    errors = core.validate(data, core._read_json(RULES_SCHEMA_PATH), "$")  # noqa: SLF001
    if not errors:
        ids = [rule["id"] for rule in data["rules"]]  # type: ignore[index]
        errors += [f"rules: duplicate id '{i}'" for i in sorted({i for i in ids if ids.count(i) > 1})]
        errors += [f"rules: id '{i}' has no check function" for i in ids if i not in CHECKS]
        errors += [f"rules: check function for '{i}' has no rule" for i in CHECKS if i not in ids]
    if errors:
        raise core.ConfigError(f"{path}: " + "; ".join(errors))
    return data  # type: ignore[return-value]


def glob_match(rel: str, pattern: str, fold: bool = False) -> bool:
    """fnmatch on the posix path; `*` crosses `/`; no `/` in the pattern also tries the file name; `dir/` is a prefix."""
    if fold:
        rel, pattern = rel.lower(), pattern.lower()
    if pattern.endswith("/"):
        return rel.startswith(pattern)
    if fnmatch.fnmatchcase(rel, pattern):
        return True
    return "/" not in pattern and fnmatch.fnmatchcase(rel.rsplit("/", 1)[-1], pattern)


def _read_json_quiet(path: Path) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def project_excludes(project: Path, rules: dict, root: Path | None) -> list[str]:
    """Core excludes, config key project_check.exclude, and the read_only_dirs of .ai/guard.json (as folder prefixes)."""
    found = list(rules["exclude"])
    config = project / ".socratex" / "config.json"
    if config.is_file():
        try:
            found += core.resolve(project, root)["values"].get("project_check", {}).get("exclude", [])
        except core.ConfigError:
            raw = _read_json_quiet(config)
            if isinstance(raw, dict) and isinstance(raw.get("project_check"), dict):
                found += [p for p in raw["project_check"].get("exclude", []) if isinstance(p, str)]
    guard = _read_json_quiet(project / ".ai" / "guard.json")
    if isinstance(guard, dict) and isinstance(guard.get("read_only_dirs"), list):
        for item in guard["read_only_dirs"]:
            if isinstance(item, str) and item.strip("/*"):
                found.append(item.replace("\\", "/").removesuffix("/**").strip("/") + "/")
    return found


def list_project_files(project: Path) -> list[str]:
    """Tracked files (git ls-files); a directory walk when the folder is not in a git work tree."""
    try:
        inside = subprocess.run(["git", "-C", str(project), "rev-parse", "--is-inside-work-tree"],
                                capture_output=True, text=True, check=False)
        if inside.returncode == 0 and inside.stdout.strip() == "true":
            out = subprocess.run(["git", "-C", str(project), "-c", "core.quotepath=off", "ls-files", "-z"],
                                 capture_output=True, check=True).stdout.decode("utf-8", errors="replace")
            return sorted(p for p in out.split("\0") if p)
    except (OSError, subprocess.CalledProcessError):
        pass
    found = []
    for folder, dirs, names in os.walk(project):
        dirs[:] = [d for d in dirs if d not in PRUNE_DIRS]
        found += [(Path(folder) / n).relative_to(project).as_posix() for n in names]
    return sorted(found)


class Context:
    """What the checks share: project folder, SocratexAI root, scanned files and the finding list."""

    def __init__(self, project: Path, root: Path, rules: dict) -> None:
        self.project, self.root, self.rules = project, root, rules
        self.max_bytes = rules["max_file_bytes"]
        excludes = project_excludes(project, rules, root)
        self.files: list[str] = []
        for rel in list_project_files(project):
            full = project / rel
            if any(glob_match(rel, p) for p in excludes):
                continue
            try:
                if full.is_file() and full.stat().st_size <= self.max_bytes:
                    self.files.append(rel)
            except OSError:
                continue
        self.findings: list[dict] = []
        self._text: dict[str, list[str] | None] = {}

    def add(self, rule: dict, file: str, line: int, message: str) -> None:
        self.findings.append({"rule": rule["id"], "severity": rule["severity"], "file": file, "line": max(line, 1),
                              "message": message})

    def lines(self, rel: str) -> list[str] | None:
        """Text lines of a project file; None when it is missing, too big or binary."""
        if rel not in self._text:
            full = self.project / rel
            result = None
            try:
                if full.is_file() and full.stat().st_size <= self.max_bytes:
                    raw = full.read_bytes()
                    result = None if b"\0" in raw[:8192] else raw.decode("utf-8", errors="replace").splitlines()
            except OSError:
                pass
            self._text[rel] = result
        return self._text[rel]

    def matching(self, patterns: list[str], fold: bool = False) -> list[str]:
        return [rel for rel in self.files if any(glob_match(rel, p, fold) for p in patterns)]


def _line_of(lines: list[str] | None, needle: str) -> int:
    for number, text in enumerate(lines or [], 1):
        if needle in text:
            return number
    return 1


# ---------- the checks (one per rule id) ----------

def _scan_patterns(ctx: Context, rule: dict, message: str) -> None:
    fold = rule.get("ignore_case", False)
    for rel in ctx.matching(rule["files"]):
        lines = ctx.lines(rel)
        for number, text in enumerate(lines or [], 1):
            haystack = text.lower() if fold else text
            for pattern in rule["patterns"]:
                if (pattern.lower() if fold else pattern) in haystack:
                    ctx.add(rule, rel, number, message.format(pattern=pattern))


def check_legacy_ref(ctx: Context, rule: dict) -> None:
    _scan_patterns(ctx, rule, "refers to the retired v1 setup: '{pattern}'")


def check_dup_rule(ctx: Context, rule: dict) -> None:
    _scan_patterns(ctx, rule, "repeats a core rule ('{pattern}'); point to the core instead")


def check_legacy_file(ctx: Context, rule: dict) -> None:
    for rel in ctx.matching(rule["files"]):
        ctx.add(rule, rel, 1, "file of the retired v1 setup")


def check_no_config(ctx: Context, rule: dict) -> None:
    if not (ctx.project / ".socratex" / "config.json").is_file():
        ctx.add(rule, ".socratex/config.json", 1, "missing; run `sox project init` to create it")


def check_config_invalid(ctx: Context, rule: dict) -> None:
    config = ctx.project / ".socratex" / "config.json"
    if not config.is_file():
        return
    lines = ctx.lines(".socratex/config.json")
    try:
        result = core.resolve(ctx.project, ctx.root)
    except core.ConfigError as exc:
        ctx.add(rule, ".socratex/config.json", 1, " ".join(str(exc).split()))
        return
    for message in result["safety"]["errors"]:
        ctx.add(rule, ".socratex/config.json", _line_of(lines, '"allow"'), " ".join(message.split()))


def check_flow_invalid(ctx: Context, rule: dict) -> None:
    if not (ctx.project / ".socratex" / "flow.json").is_file():
        return
    try:
        errors = core.check_flow(ctx.project, ctx.root)
    except core.ConfigError as exc:
        errors = [str(exc)]
    for message in errors:
        ctx.add(rule, ".socratex/flow.json", 1, " ".join(message.split()))


def check_agents_long(ctx: Context, rule: dict) -> None:
    for name, limit in rule["limits"].items():
        lines = ctx.lines(name)
        if lines is not None and len(lines) > limit:
            ctx.add(rule, name, limit + 1, f"{len(lines)} lines, limit {limit}")


def check_claude_import(ctx: Context, rule: dict) -> None:
    lines = ctx.lines("CLAUDE.md")
    if lines is not None and not any(rule["patterns"][0] in text for text in lines):
        ctx.add(rule, "CLAUDE.md", 1, f"does not contain {rule['patterns'][0]}")


def check_index_schema(ctx: Context, rule: dict) -> None:
    lines = ctx.lines("INDEX.json")
    if lines is None:
        return
    try:
        data = json.loads("\n".join(lines))
    except ValueError as exc:
        ctx.add(rule, "INDEX.json", 1, f"not valid JSON: {exc}")
        return
    if not isinstance(data, dict) or data.get("schema") != rule["patterns"][0]:
        ctx.add(rule, "INDEX.json", _line_of(lines, '"schema"'), f"schema must be {rule['patterns'][0]!r}")
        return
    for key, value in data.items():
        for item in value if isinstance(value, list) else []:
            path = item.get("path") if isinstance(item, dict) else None
            if isinstance(path, str) and not re.search(r"[*?$]|^[a-z]+:|^/", path) and not (ctx.project / path).exists():
                ctx.add(rule, "INDEX.json", _line_of(lines, path), f"{key}: path '{path}' does not exist")


def check_fork_script(ctx: Context, rule: dict) -> None:
    scripts = {p.name for p in (ctx.root / "modules" / "tools" / "scripts").glob("*.py")} - set(rule["patterns"])
    agents = {p.name for p in (ctx.root / "claude" / "agents").glob("*.md")}
    for rel in ctx.files:
        parts = rel.split("/")
        if parts[-1] in scripts:
            ctx.add(rule, rel, 1, f"has the name of the core script {parts[-1]}")
        elif parts[-1] in agents and "agents" in parts[:-1]:
            ctx.add(rule, rel, 1, f"has the name of the core agent {parts[-1]}")


def check_dup_hook(ctx: Context, rule: dict) -> None:
    rel = rule["files"][0]
    data = _read_json_quiet(ctx.project / rel)
    hooks = data.get("hooks", {}).get("PreToolUse", []) if isinstance(data, dict) and isinstance(data.get("hooks"), dict) else []
    for entry in hooks if isinstance(hooks, list) else []:
        for hook in entry.get("hooks", []) if isinstance(entry, dict) else []:
            command = hook.get("command", "") if isinstance(hook, dict) else ""
            names = [t.lower() for t in re.findall(r"[\w.\-]+\.(?:py|sh|js|ps1|cmd|bat)", command)] or [command.lower()]
            if any(p in name for p in rule["patterns"] for name in names):
                ctx.add(rule, rel, _line_of(ctx.lines(rel), command[:40]), f"PreToolUse hook '{command}' duplicates the global guard")


def check_nonstd_override(ctx: Context, rule: dict) -> None:
    for rel in ctx.files:
        parts = rel.split("/")
        if ".ai" not in parts[:-1] and any(glob_match(parts[-1], p, True) for p in rule["patterns"]):
            ctx.add(rule, rel, 1, "non-standard override file; the standard ones live in .ai/")


def check_guard_schema(ctx: Context, rule: dict) -> None:
    for rel, allowed in rule["known_keys"].items():
        lines = ctx.lines(rel)
        if lines is None:
            continue
        try:
            data = json.loads("\n".join(lines))
        except ValueError as exc:
            ctx.add(rule, rel, 1, f"not valid JSON: {exc}")
            continue
        if not isinstance(data, dict):
            ctx.add(rule, rel, 1, "top level must be an object")
            continue
        for key in data:
            if not key.startswith("_") and key not in allowed:
                ctx.add(rule, rel, _line_of(lines, f'"{key}"'), f"unknown key '{key}' (allowed: {', '.join(allowed)})")


def check_routing_legacy(ctx: Context, rule: dict) -> None:
    if (ctx.project / ".ai" / "ROUTING.json").is_file():
        ctx.add(rule, ".ai/ROUTING.json", 1, "deprecated; use config key routing.tier_overrides")


CHECKS = {
    "PRJ-LEGACY-REF": check_legacy_ref, "PRJ-LEGACY-FILE": check_legacy_file, "PRJ-NO-CONFIG": check_no_config,
    "PRJ-CONFIG-INVALID": check_config_invalid, "PRJ-FLOW-INVALID": check_flow_invalid,
    "PRJ-AGENTS-LONG": check_agents_long, "PRJ-CLAUDE-IMPORT": check_claude_import,
    "PRJ-INDEX-SCHEMA": check_index_schema, "PRJ-DUP-RULE": check_dup_rule, "PRJ-FORK-SCRIPT": check_fork_script,
    "PRJ-DUP-HOOK": check_dup_hook, "PRJ-NONSTD-OVERRIDE": check_nonstd_override,
    "PRJ-GUARD-SCHEMA": check_guard_schema, "PRJ-ROUTING-LEGACY": check_routing_legacy,
}


def require_project(path: str | Path) -> Path:
    project = Path(path)
    if not project.is_dir():
        raise core.ConfigError(f"{path}: not a directory")
    return project.resolve()


def run_check(path: str | Path, root: Path | None = None, rules_path: Path = RULES_PATH) -> list[dict]:
    """Return the findings {rule, severity, file, line, message} for a project, in rule order. Reads only."""
    project = require_project(path)
    rules = load_rules(rules_path)
    ctx = Context(project, Path(root) if root else ROOT, rules)
    for rule in rules["rules"]:
        CHECKS[rule["id"]](ctx, rule)
    return ctx.findings


def format_line(finding: dict) -> str:
    mark = "(warning) " if finding["severity"] == "warning" else ""
    return f"{finding['rule']} {finding['file']}:{finding['line']} {mark}{finding['message']}"


def exit_code(findings: list[dict], strict: bool) -> int:
    return 1 if any(f["severity"] == "error" or strict for f in findings) else 0


def counts(findings: list[dict]) -> dict:
    return {s: sum(1 for f in findings if f["severity"] == s) for s in ("error", "warning")}


def template_files(root: Path | None = None) -> dict[str, str]:
    """Relative path -> content of every project template (files in templates/project plus the built-in ones)."""
    base = (Path(root) if root else ROOT) / TEMPLATE_DIR
    found = dict(BUILTIN_TEMPLATES)
    for file in sorted(base.rglob("*")):
        if file.is_file() and "__pycache__" not in file.parts:
            found[file.relative_to(base).as_posix()] = file.read_text(encoding="utf-8")
    return dict(sorted(found.items()))


def init_project(path: str | Path, write: bool, root: Path | None = None) -> list[str]:
    """Plan (or with write=True do) the creation of the missing template files; existing files are never touched."""
    project = require_project(path)
    lines = []
    for rel, content in template_files(root).items():
        target = project / rel
        if target.exists():
            lines.append(f"skipped (exists) {rel}")
            continue
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
        lines.append(f"{'created' if write else 'would create'} {rel}")
    return lines


def explain(rule_id: str) -> list[str]:
    rules = load_rules()["rules"]
    rule = next((r for r in rules if r["id"] == rule_id.upper()), None)
    if rule is None:
        raise core.ConfigError(f"unknown rule '{rule_id}'; known: {', '.join(r['id'] for r in rules)}")
    lines = [f"{rule['id']} ({rule['severity']})", f"  what: {rule['what']}", f"  fix:  {rule['fix']}"]
    for key in ("files", "patterns", "limits", "known_keys"):
        if key in rule:
            lines.append(f"  {key}: {json.dumps(rule[key], ensure_ascii=False)}")
    return lines
