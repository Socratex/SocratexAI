#!/usr/bin/env python3
"""Project knowledge hub: layout of local/projects and local/groups, project keys, `sox context` and `sox project ...`.

Layout (everything under <root>/local, outside git):
    projects/<key>/   project.json, PROJECT.md, DOMAIN.md, DEVIATIONS.md, rules/, config.json
    groups/<group>/   group.json, GROUP.md, rules/, config.json
    tickets/<PREFIX>/ ticket working memory (read by `check` for orphan prefixes only)

The key of a project is the name of its folder by default. A project.json with a `path` binds that repo folder to its
key, so two repos with the same folder name can live side by side under different keys (`name` = key = folder name in
local/projects). Stdlib only; used by core/core.py (resolver) and core/sox.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from pathlib import Path

import core

ROOT = core.ROOT
KNOWLEDGE_TEMPLATES = Path("templates") / "knowledge"
KNOWLEDGE_FILES = ("PROJECT.md", "DOMAIN.md", "DEVIATIONS.md")
MODES = ("local", "repo", "external")
PREFIX_RE = re.compile(r"^[A-Z]{2,}$")


def _base(root: Path | None) -> Path:
    return Path(root) if root else ROOT


def projects_dir(root: Path | None = None) -> Path:
    return _base(root) / "local" / "projects"


def groups_dir(root: Path | None = None) -> Path:
    return _base(root) / "local" / "groups"


def tickets_dir(root: Path | None = None) -> Path:
    return _base(root) / "local" / "tickets"


def _resolved(path: object) -> Path | None:
    try:
        return Path(str(path)).expanduser().resolve() if path else None
    except (OSError, RuntimeError):
        return None


# ---------- project.json / group.json ----------

def load_project_json(path: Path) -> dict:
    """Read and validate a project.json; ConfigError names the file and the key."""
    return core._check_file_header(path, core._read_json(path), "project.schema.json")  # noqa: SLF001


def load_group_json(path: Path) -> dict:
    return core._check_file_header(path, core._read_json(path), "group.schema.json")  # noqa: SLF001


def _quiet_project(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def project_entries(root: Path | None = None) -> list[dict]:
    """Every folder of local/projects as {key, dir, data, error}; data is the validated project.json or None."""
    found = []
    folder = projects_dir(root)
    for sub in sorted(folder.iterdir()) if folder.is_dir() else []:
        if not sub.is_dir():
            continue
        entry = {"key": sub.name, "dir": sub, "data": None, "error": None}
        if (sub / "project.json").is_file():
            try:
                entry["data"] = load_project_json(sub / "project.json")
            except core.ConfigError as exc:
                entry["error"] = str(exc)
        found.append(entry)
    return found


def project_key(project_root: Path | str | None, root: Path | None = None) -> str | None:
    """The key (folder name in local/projects) of a project repo folder.

    1. a project.json whose `path` is this folder wins; two of them is a collision error
    2. else the folder name; if local/projects/<name>/project.json binds that key to another path, error naming both paths
    """
    if not project_root:
        return None
    repo = Path(project_root).resolve()
    bound = [e for e in project_entries(root) if e["data"] and _resolved(e["data"].get("path")) == repo]
    if len(bound) > 1:
        raise core.ConfigError(f"projects {', '.join(e['key'] for e in bound)} all claim the path {repo}; "
                               "fix the `path` fields in their project.json")
    if bound:
        return bound[0]["key"]
    declared = _quiet_project(projects_dir(root) / repo.name / "project.json")
    other = _resolved(declared.get("path")) if declared else None
    if other and other != repo:
        raise core.ConfigError(
            f"project key '{repo.name}' is bound to {other} in local/projects/{repo.name}/project.json, but this folder is {repo}; "
            f"give one of them its own key: `sox project init {repo} --name <other-key>` (the name field is the key)")
    return repo.name


def project_group(key: str | None, root: Path | None = None) -> str | None:
    """The group named in local/projects/<key>/project.json (validated; a bad file is a ConfigError)."""
    path = projects_dir(root) / (key or "") / "project.json"
    if not key or not path.is_file():
        return None
    group = load_project_json(path).get("group")
    gjson = groups_dir(root) / group / "group.json" if group else None
    if gjson and gjson.is_file():
        load_group_json(gjson)   # an unknown key in group.json is an error naming file and key
    return group


def group_config_path(group: str, root: Path | None = None) -> Path:
    return groups_dir(root) / group / "config.json"


# ---------- sox context ----------

def _row(layer: str, path: Path, why: str) -> dict:
    return {"layer": layer, "file": str(path), "why": why, "exists": path.is_file()}


def _rule_rows(layer: str, folder: Path, label: str) -> list[dict]:
    return [_row(layer, p, f"{label} rule") for p in sorted(folder.glob("*.md")) if p.name.lower() != "readme.md"]


def _split_project_arg(arg: str | None) -> tuple[Path | None, str | None]:
    """`--project` is a repo folder (preferred) or a project key; returns (repo folder or None, given key or None)."""
    if not arg:
        return None, None
    path = Path(arg).expanduser()
    return (path.resolve(), None) if path.is_dir() else (None, arg)


def knowledge_dir(key: str, data: dict, repo: Path | None, root: Path | None) -> tuple[Path, str, str | None]:
    """(directory holding the knowledge files, mode, error). The project.json always stays in local/projects/<key>."""
    spec = data.get("knowledge") or {}
    mode = spec.get("mode", "local")
    if mode == "local":
        return projects_dir(root) / key, mode, None
    if not spec.get("path"):
        return projects_dir(root) / key, mode, f"project {key}: knowledge.mode '{mode}' needs knowledge.path in project.json"
    target = Path(spec["path"]).expanduser()
    if not target.is_absolute():
        repo = repo or _resolved(data.get("path"))
        if mode == "external" or repo is None:
            reason = "must be absolute for mode external" if mode == "external" else "is relative but the repo folder is unknown (pass the repo folder or set `path`)"
            return projects_dir(root) / key, mode, f"project {key}: knowledge.path {spec['path']!r} {reason}"
        target = repo / target
    return target, mode, None


def build_context(project: str | None = None, root: Path | None = None) -> dict:
    """The ordered read list, general to most important: {project, rows: [{layer, file, why, exists}], errors}.

    Layers: socratex (defaults), preference (index of documents per kind of work), global (local/), group, project-repo,
    project. A later row wins over an earlier one on conflict. Preference paths are relative to the SocratexAI root;
    `project:<path>` means relative to the project repo folder; an absolute path is taken as is."""
    base = _base(root)
    errors: list[str] = []
    repo, given_key = _split_project_arg(project)
    key = given_key
    if repo is not None:
        try:
            key = project_key(repo, root)
        except core.ConfigError as exc:
            errors.append(str(exc))
            key = repo.name
    rows = [_row("socratex", base / "defaults" / "RULES.md", "core rules"),
            _row("socratex", base / "defaults" / "STYLE.md", "reply style"),
            _row("socratex", base / "defaults" / "DIRECTIVES.json", "which rule document applies to what you do")]
    try:
        prefs = core.resolve(repo, root)["values"].get("preferences", {})
    except core.ConfigError as exc:
        prefs = {}
        errors.append(f"config: {exc}")
    for name in sorted(prefs):
        for item in prefs[name].get("files", []):
            if item.startswith("project:"):
                path = (repo / item[len("project:"):]) if repo else Path(item[len("project:"):])
            else:
                path = Path(item) if Path(item).is_absolute() else base / item
            if not any(r["file"] == str(path) for r in rows):   # a file already listed (e.g. STYLE.md) keeps its first row
                rows.append(_row("preference", path, f"preference {name}: load when {prefs[name].get('load_when', '')}"))
    rows.append(_row("global", base / "local" / "profile.md", "owner profile (language, owner facts)"))
    group = None
    info = {"key": key, "repo": str(repo) if repo else None, "group": None, "mode": None, "knowledge_dir": None}
    pdir = projects_dir(root) / key if key else None
    data = None
    if pdir and (pdir / "project.json").is_file():
        try:
            data = load_project_json(pdir / "project.json")
        except core.ConfigError as exc:
            errors.append(str(exc))
    if data:
        group = data.get("group")
        info["group"] = group
    if group:
        gdir = groups_dir(root) / group
        if not gdir.is_dir():
            errors.append(f"project {key}: group '{group}' has no folder {gdir}")
        rows.append(_row("group", gdir / "GROUP.md", f"group {group}: shared facts"))
        rows += _rule_rows("group", gdir / "rules", f"group {group}")
    if repo:
        rows.append(_row("project-repo", repo / "AGENTS.md", "project rules kept in the repo"))
        rows.append(_row("project-repo", repo / "INDEX.json", "project map kept in the repo"))
    if key and data is None and not errors:
        rows.append(_row("project", pdir / "project.json", f"no project knowledge for '{key}' (no project.json): only the global layers apply"))
    elif key and data:
        kdir, mode, problem = knowledge_dir(key, data, repo, root)
        info.update(mode=mode, knowledge_dir=str(kdir))
        spec = data.get("knowledge") or {}
        why = f"reference: knowledge mode {mode}" + (f" -> {kdir}" if mode != "local" else " (in this folder)")
        rows.append(_row("project", pdir / "project.json", why))
        if problem:
            errors.append(problem)
        elif mode != "local" and not kdir.is_dir():
            errors.append(f"project {key}: knowledge.path {kdir} does not exist")
        rows.append(_row("project", kdir / "PROJECT.md", f"facts about {key}"))
        rows.append(_row("project", kdir / "DOMAIN.md", f"business reasons behind {key}"))
        rows += _rule_rows("project", kdir / "rules", f"project {key}")
        rows.append(_row("project", kdir / "DEVIATIONS.md", f"where {key} differs from the SocratexAI standards, and why (most specific)"))
    return {"project": info, "rows": rows, "errors": errors}


def format_context(result: dict) -> list[str]:
    lines = []
    for number, row in enumerate(result["rows"], 1):
        lines.append(f"{number:>2}. [{row['layer']}] {row['file']}  - {row['why']}" + ("" if row["exists"] else "  (missing)"))
    return lines


# ---------- sox project init / adopt ----------

def _stamp(text: str, name: str) -> str:
    return text.replace("{{name}}", name).replace("{{date}}", time.strftime("%Y-%m-%d"))


def knowledge_templates(root: Path | None = None) -> dict[str, str]:
    base = _base(root) / KNOWLEDGE_TEMPLATES
    return {p.relative_to(base).as_posix(): p.read_text(encoding="utf-8") for p in sorted(base.rglob("*")) if p.is_file()}


def init_knowledge(repo: Path, write: bool, root: Path | None = None, name: str | None = None, group: str | None = None,
                   prefixes: list[str] | None = None, summary: str | None = None) -> list[str]:
    """Plan (or do) the skeleton of local/projects/<key>/ for a repo folder; existing files are never overwritten."""
    key = name or repo.name
    pdir = projects_dir(root) / key
    declared = _quiet_project(pdir / "project.json")
    other = _resolved(declared.get("path")) if declared else None
    if other and other != repo:
        raise core.ConfigError(f"project key '{key}' is already bound to {other}; this folder is {repo}. Use --name to give one a different key")
    project_json = {"schema_version": 1, "name": key, "summary": summary or "", "path": str(repo),
                    "knowledge": {"mode": "local"}}
    if group:
        project_json["group"] = group
    if prefixes:
        project_json["ticket_prefixes"] = prefixes
    files = {"project.json": json.dumps(project_json, indent=2, ensure_ascii=False) + "\n"}
    files.update({rel: _stamp(text, key) for rel, text in knowledge_templates(root).items()})
    lines = []
    for rel, content in files.items():
        target = pdir / rel
        if target.exists():
            lines.append(f"skipped (exists) {target}")
            continue
        if write:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8", newline="\n")
        lines.append(f"{'created' if write else 'would create'} {target}")
    return lines


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def adopt_plan(source: Path, key: str, root: Path | None, include: list[str], exclude: list[str]) -> list[dict]:
    """One row per file under `source`: {src, dst, action, sha}; action is copy, same (already there) or conflict (differs, kept)."""
    from project_check import glob_match

    dest = projects_dir(root) / key
    rows = []
    for src in sorted(p for p in source.rglob("*") if p.is_file()):
        rel = src.relative_to(source).as_posix()
        if include and not any(glob_match(rel, g) for g in include):
            continue
        if any(glob_match(rel, g) for g in exclude) or "__pycache__" in rel.split("/") or rel.startswith(".git/"):
            continue
        dst = dest / rel
        if not dst.exists():
            action = "copy"
        else:
            action = "same" if dst.is_file() and _sha(dst) == _sha(src) else "conflict"
        rows.append({"src": str(src), "dst": str(dst), "action": action, "sha": _sha(src)})
    return rows


def adopt_apply(rows: list[dict]) -> int:
    """Copy the rows marked copy; never overwrites, never deletes. Returns how many files were written."""
    done = 0
    for row in rows:
        if row["action"] == "copy":
            Path(row["dst"]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(row["src"], row["dst"])
            done += 1
    return done


# ---------- sox project list / show / check ----------

def _leaf_keys(data: object, prefix: str = "") -> list[str]:
    if isinstance(data, dict):
        out = []
        for key, value in data.items():
            if key == "schema_version":
                continue
            out += _leaf_keys(value, f"{prefix}.{key}" if prefix else key) if isinstance(value, dict) and value else [f"{prefix}.{key}" if prefix else key]
        return out
    return [prefix]


def override_keys(key: str, root: Path | None = None) -> list[str]:
    path = projects_dir(root) / key / "config.json"
    data = _quiet_project(path)
    return sorted(_leaf_keys(data)) if data else []


def list_rows(root: Path | None = None) -> list[dict]:
    rows = []
    for entry in project_entries(root):
        data = entry["data"] or {}
        rows.append({"project": entry["key"], "group": data.get("group", ""), "mode": (data.get("knowledge") or {}).get("mode", "local") if data else "",
                     "overrides": override_keys(entry["key"], root), "summary": data.get("summary", ""),
                     "error": entry["error"]})
    return rows


def resolve_key(arg: str, root: Path | None = None) -> str:
    """A key as given, or the key of a repo folder."""
    repo, given = _split_project_arg(arg)
    return project_key(repo, root) if repo else given  # type: ignore[return-value]


def show_lines(arg: str, root: Path | None = None) -> list[str]:
    key = resolve_key(arg, root)
    pdir = projects_dir(root) / key
    if not (pdir / "project.json").is_file():
        raise core.ConfigError(f"{pdir / 'project.json'}: no such project '{key}' (see `sox project list`)")
    data = load_project_json(pdir / "project.json")
    kdir, mode, problem = knowledge_dir(key, data, None, root)
    lines = [f"project:   {key}", f"summary:   {data.get('summary', '')}", f"group:     {data.get('group', '-')}",
             f"repo path: {data.get('path', '-')}", f"prefixes:  {', '.join(data.get('ticket_prefixes', [])) or '-'}",
             f"knowledge: {mode} -> {kdir}" + (f"  ({problem})" if problem else "")]
    config = _quiet_project(pdir / "config.json") or {}
    lines.append("overrides (local/projects config.json):" + ("" if config else " none"))
    for leaf in override_keys(key, root):
        value: object = config
        for part in leaf.split("."):
            value = value[part] if isinstance(value, dict) else None
        lines.append(f"  {leaf} = {json.dumps(value, ensure_ascii=False)}")
    deviations = kdir / "DEVIATIONS.md"
    lines.append("")
    lines.append(f"deviations ({deviations}):")
    lines.append(deviations.read_text(encoding="utf-8").rstrip() if deviations.is_file() else "  (no DEVIATIONS.md)")
    return lines


def check_knowledge(root: Path | None = None, only: str | None = None) -> list[dict]:
    """Consistency findings {code, severity, file, message} of the hub; `only` limits project checks to one key."""
    out: list[dict] = []

    def add(code: str, severity: str, file: object, message: str) -> None:
        out.append({"code": code, "severity": severity, "file": str(file), "message": message})

    entries = project_entries(root)
    claimed: dict[str, list[str]] = {}
    paths: dict[str, list[tuple[str, Path]]] = {}
    for entry in entries:
        key, data, pdir = entry["key"], entry["data"], entry["dir"]
        if entry["error"]:
            add("K-PROJECT-JSON", "error", pdir / "project.json", entry["error"])
        if not data:
            continue
        for prefix in data.get("ticket_prefixes", []):
            claimed.setdefault(prefix, []).append(key)
        if data.get("path"):
            paths.setdefault(Path(data["path"]).name, []).append((key, Path(data["path"])))
        if only and key != only:
            continue
        if data["name"] != key:
            add("K-NAME", "error", pdir / "project.json", f"name '{data['name']}' must equal the folder name '{key}' (the name is the key)")
        group = data.get("group")
        if group:
            gjson = groups_dir(root) / group / "group.json"
            if not (groups_dir(root) / group).is_dir():
                add("K-GROUP", "error", gjson, f"project {key}: group '{group}' has no folder")
            else:
                try:
                    load_group_json(gjson) if gjson.is_file() else add("K-GROUP", "warning", gjson, f"group '{group}' has no group.json")
                except core.ConfigError as exc:
                    add("K-GROUP", "error", gjson, str(exc))
        kdir, mode, problem = knowledge_dir(key, data, None, root)
        if problem:
            add("K-KNOWLEDGE-PATH", "error", pdir / "project.json", problem)
        elif mode != "local" and not kdir.is_dir():
            add("K-KNOWLEDGE-PATH", "error", kdir, f"project {key}: knowledge.path {kdir} does not exist")
        elif kdir.is_dir():
            for name in ("PROJECT.md", "DEVIATIONS.md"):
                if not (kdir / name).is_file():
                    add("K-FILES", "warning", kdir / name, f"project {key}: {name} is missing (`sox project init` creates it)")
        config = pdir / "config.json"
        if config.is_file():
            try:
                core.load_layer_file(config)
            except core.ConfigError as exc:
                add("K-CONFIG", "error", config, str(exc))
    if not only:
        for prefix, keys in sorted(claimed.items()):
            if len(keys) > 1:
                add("K-PREFIX-DUP", "error", projects_dir(root), f"ticket prefix {prefix} is claimed by {', '.join(keys)}")
        for folder, items in sorted(paths.items()):
            distinct = {str(p) for _, p in items}
            if len(distinct) > 1 and any(k == folder for k, _ in items):
                add("K-COLLISION", "error", projects_dir(root),
                    f"repo folders named '{folder}' collide: " + " and ".join(sorted(distinct)) +
                    f"; the key '{folder}' must stay with one of them, give the other a different `name` in its project.json")
        known = set(claimed)
        tickets = tickets_dir(root)
        for sub in sorted(tickets.iterdir()) if tickets.is_dir() else []:
            if sub.is_dir() and PREFIX_RE.match(sub.name) and sub.name not in known:
                add("K-ORPHAN-PREFIX", "warning", sub, f"ticket prefix {sub.name} has no project (add it to ticket_prefixes in a project.json)")
    return out
