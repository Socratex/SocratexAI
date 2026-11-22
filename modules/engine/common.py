"""Shared pipeline engine helpers: registry loading, git change ranges, chunking, select and fix script execution, run log."""

from __future__ import annotations

import copy
import fnmatch
import json
import re
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ROUTING = ROOT / "core" / "ROUTING.json"
LOCAL_DIR = ROOT / "local"
REGISTRY_SCHEMA = "socratex-checker-registry/v1"
PIPELINES = ("review", "planning")

TIERS = ("cheap", "standard", "high")
CHECKER_TIERS = ("script",) + TIERS
SCOPES = ("file", "hunk", "symbol", "whole_diff")
AUTOFIX = ("none", "script", "agent")
TOOLS = ("rg", "serena", "graphify", "diff-grep", "none")
REQUIRED_FIELDS = ("id", "pipeline", "scope", "select", "tier", "autofix")
MAX_FIX_ROUNDS = 2
CONTEXT_LINES = 3
SELECT_TIMEOUT_SECONDS = 120


class RegistryError(ValueError):
    """The registry (global or project override) is malformed."""


class SelectError(RuntimeError):
    """A select script failed or returned something that is not a candidate list."""


def posix(path: Path | str) -> str:
    return Path(path).as_posix()


def tier_alias(tier: str, overrides: dict[str, str] | None) -> str:
    if overrides and tier in overrides:
        return overrides[tier]
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    return routing["claude"][tier]["alias"]


def next_tier(tier: str) -> str | None:
    """One tier up, or None when the tier is already the highest one the pipeline may use on its own."""
    if tier not in TIERS or tier == TIERS[-1]:
        return None
    return TIERS[TIERS.index(tier) + 1]


def override_path(pipeline: str) -> Path:
    return Path(".ai") / f"{pipeline}.json"


def validate_checker(raw: dict, position: int) -> dict:
    label = f"checker #{position} ({raw.get('id', '?')!r})"
    missing = [name for name in REQUIRED_FIELDS if not raw.get(name)]
    if missing:
        raise RegistryError(f"{label}: missing required field(s): {', '.join(missing)}")
    checker = {"concern": "", "tool": "none", "enabled": True, "fix_script": None, "autofix_fallback": "none", **raw}
    for field, allowed in (("pipeline", PIPELINES), ("scope", SCOPES), ("tier", CHECKER_TIERS), ("autofix", AUTOFIX),
                           ("autofix_fallback", AUTOFIX), ("tool", TOOLS)):
        if checker[field] not in allowed:
            raise RegistryError(f"{label}: {field}={checker[field]!r} is not one of {', '.join(allowed)}")
    if checker["scope"] == "whole_diff" and not checker.get("scope_reason"):
        raise RegistryError(f"{label}: scope whole_diff needs a non-empty scope_reason")
    if checker["autofix"] == "script" and not checker["fix_script"]:
        raise RegistryError(f"{label}: autofix script needs fix_script")
    if "stage" in checker and not isinstance(checker["stage"], str):
        raise RegistryError(f"{label}: stage must be a string")
    if "max_chunk_lines" in checker and not (isinstance(checker["max_chunk_lines"], int) and checker["max_chunk_lines"] > 0):
        raise RegistryError(f"{label}: max_chunk_lines must be a positive integer")
    return checker


def override_layers(pipeline: str, project_dir: Path | None) -> list[tuple[str, Path, Path]]:
    """Override files in merge order after the stage's own registry: (label, file, folder `{here}` of its added checkers).

    Order: local/overrides/stages/<pipeline>.json, the project file `.ai/<pipeline>.json`, then the private
    local/projects/<project folder name>/<pipeline>.json. Files that do not exist are skipped by the loader.
    """
    layers = [(f"local/overrides/stages/{pipeline}.json", LOCAL_DIR / "overrides" / "stages" / f"{pipeline}.json",
               LOCAL_DIR / "overrides" / "stages")]
    if project_dir is not None:
        project = Path(project_dir).resolve()
        layers.append((override_path(pipeline).as_posix(), project / override_path(pipeline), project))
        private = LOCAL_DIR / "projects" / project.name
        layers.append((f"local/projects/{project.name}/{pipeline}.json", private / f"{pipeline}.json", private))
    return layers


def load_registry(path: Path, project_dir: Path | None) -> dict:
    """Load a registry with its override layers; see `load_registry_with_provenance` (this drops the change list)."""
    return load_registry_with_provenance(path, project_dir)[0]


def _change_kind(field: str, value: object) -> str:
    if field == "enabled":
        return "enabled" if value else "disabled"
    return {"tier": "retiered", "max_chunk_lines": "max_chunk_lines"}.get(field, "changed")


def load_registry_with_provenance(path: Path, project_dir: Path | None) -> tuple[dict, list[dict]]:
    """Load and validate a registry, then apply the override layers (see `override_layers`) on a copy; nothing is written.

    Returns (registry, provenance). Each provenance row is {checker, kind, field, from, to, layer, file}: kind is
    `added` for an appended checker, else `disabled`, `enabled`, `retiered`, `max_chunk_lines` or `changed`; layer and
    file name the override that did it. Only real value changes are listed. The registry is what `load_registry` returns.

    Each layer may change fields of existing checkers (`checkers`, including `enabled`, `tier`, `max_chunk_lines`),
    append new ones (`add`) and set the registry-wide keys; later layers win. `{here}` in select and fix commands
    resolves to the folder of the registry file, or to the layer's folder for checkers a layer added.
    """
    path = Path(path)
    try:
        base = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as err:
        raise RegistryError(f"cannot read registry {path}: {err}") from err
    if base.get("schema") != REGISTRY_SCHEMA:
        raise RegistryError(f"registry schema must be {REGISTRY_SCHEMA!r}, got {base.get('schema')!r}")
    pipeline = base.get("pipeline")
    if pipeline not in PIPELINES:
        raise RegistryError(f"registry pipeline must be one of {', '.join(PIPELINES)}, got {pipeline!r}")
    checkers = copy.deepcopy(base.get("checkers", []))
    here = path.resolve().parent
    added_here: dict[str, Path] = {}
    skip_patterns = list(base.get("skip_patterns", []))
    settings = {key: base[key] for key in ("min_changed_lines", "gates", "implementer_tier") if key in base}
    aliases: dict = {}
    provenance: list[dict] = []
    for label, source, layer_here in override_layers(pipeline, project_dir):
        if not source.is_file():
            continue
        try:
            override = json.loads(source.read_text(encoding="utf-8"))
        except json.JSONDecodeError as err:
            raise RegistryError(f"{label} is not valid JSON: {err}") from err
        by_id = {c.get("id"): c for c in checkers}
        for checker_id, changes in override.get("checkers", {}).items():
            if checker_id not in by_id:
                raise RegistryError(f"{label}: unknown checker {checker_id!r}")
            for field, value in changes.items():
                before = by_id[checker_id].get(field, True if field == "enabled" else None)
                if before != value:
                    provenance.append({"checker": checker_id, "kind": _change_kind(field, value), "field": field,
                                       "from": before, "to": value, "layer": label, "file": str(source)})
            by_id[checker_id].update(changes)
        added = copy.deepcopy(override.get("add", []))
        provenance += [{"checker": raw.get("id"), "kind": "added", "field": None, "from": None, "to": None,
                        "layer": label, "file": str(source)} for raw in added]
        checkers += added
        added_here.update({raw.get("id"): layer_here for raw in added})
        skip_patterns += override.get("skip_patterns", [])
        aliases.update(override.get("aliases", {}))
        settings.update({key: override[key] for key in ("min_changed_lines", "gates", "implementer_tier") if key in override})
    validated = [validate_checker(raw, number) for number, raw in enumerate(checkers, 1)]
    ids = [c["id"] for c in validated]
    if len(set(ids)) != len(ids):
        raise RegistryError(f"duplicate checker ids: {sorted({i for i in ids if ids.count(i) > 1})}")
    default_chunk = int(base.get("default_max_chunk_lines", 100))
    for checker in validated:
        if checker["pipeline"] != pipeline:
            raise RegistryError(f"checker {checker['id']!r}: pipeline {checker['pipeline']!r} does not match the "
                                f"registry pipeline {pipeline!r}")
        checker.setdefault("max_chunk_lines", default_chunk)
        checker["here"] = added_here.get(checker["id"], here)
    return {
        "pipeline": pipeline,
        "checkers": validated,
        "skip_patterns": skip_patterns,
        "min_changed_lines": int(settings.get("min_changed_lines", 0)),
        "aliases": aliases,
        "gates": list(settings.get("gates", [])),
        "implementer_tier": settings.get("implementer_tier", "standard"),
    }, provenance


class RunLog:
    """Append-only JSONL log; safe to use from the parallel check threads."""

    def __init__(self, path: Path | None) -> None:
        self.path = path
        self.events: list[dict] = []
        self._lock = threading.Lock()

    def reset(self) -> None:
        """Drop everything logged so far (used to collapse an empty run into one line)."""
        with self._lock:
            self.events.clear()
            if self.path is not None:
                self.path.write_text("", encoding="utf-8")

    def event(self, name: str, **fields) -> dict:
        row = {"event": name, "ts": datetime.now().isoformat(timespec="milliseconds"), "t": time.time(), **fields}
        with self._lock:
            self.events.append(row)
            if self.path is not None:
                with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row


def git(project_dir: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=project_dir, capture_output=True, text=True, encoding="utf-8",
                          errors="replace")


def read_text_lines(path: Path) -> list[str]:
    return path.read_bytes().decode("utf-8", errors="replace").splitlines()


def is_binary(path: Path) -> bool:
    with path.open("rb") as handle:
        return b"\0" in handle.read(8192)


def skip_reason(project_dir: Path, rel: str, patterns: list[str]) -> str | None:
    full = project_dir / rel
    if not full.is_file():
        return "missing file"
    for pattern in patterns:
        if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(Path(rel).name, pattern):
            return f"generated or ignored by pattern {pattern}"
    if is_binary(full):
        return "binary file"
    return None


def changed_ranges(project_dir: Path, rel: str) -> tuple[list[tuple[int, int]], int]:
    """Changed line ranges (new side) and the changed-line count of one file against HEAD.

    Untracked files and repositories without HEAD count as fully changed.
    """
    full = project_dir / rel
    total = len(read_text_lines(full))
    tracked = git(project_dir, "ls-files", "--error-unmatch", "--", rel).returncode == 0
    has_head = git(project_dir, "rev-parse", "--verify", "-q", "HEAD").returncode == 0
    if not (tracked and has_head):
        return ([(1, total)] if total else []), total
    diff = git(project_dir, "diff", "-U0", "--no-color", "HEAD", "--", rel).stdout
    ranges: list[tuple[int, int]] = []
    count = 0
    for match in re.finditer(r"^@@ -\d+(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", diff, re.MULTILINE):
        removed = int(match.group(1)) if match.group(1) is not None else 1
        start = int(match.group(2))
        added = int(match.group(3)) if match.group(3) is not None else 1
        count += added + removed
        if added:
            ranges.append((start, start + added - 1))
    return ranges, count


def merge_ranges(ranges: list[tuple[int, int]]) -> list[tuple[int, int]]:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if merged and start <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])
    return [(a, b) for a, b in merged]


def build_chunks(rel: str, scope: str, ranges: list[tuple[int, int]], total_lines: int, limit: int) -> tuple[list[dict], int]:
    """Cut one file into chunks of at most `limit` lines; returns the chunks and how many ranges had to be split."""
    if scope == "file":
        wanted = [(1, total_lines)] if ranges else []
    else:
        wanted = merge_ranges([(max(1, s - CONTEXT_LINES), min(total_lines, e + CONTEXT_LINES)) for s, e in ranges])
    chunks: list[dict] = []
    splits = 0
    for start, end in wanted:
        parts = [(a, min(a + limit - 1, end)) for a in range(start, end + 1, limit)]
        splits += len(parts) > 1
        for a, b in parts:
            changed = [[max(s, a), min(e, b)] for s, e in ranges if s <= b and e >= a]
            chunks.append({"file": rel, "line_start": a, "line_end": b, "split": len(parts) > 1, "changed": changed})
    return chunks, splits


def expand_command(template: str, here: Path) -> list[str]:
    return shlex.split(template.replace("{python}", posix(sys.executable)).replace("{here}", posix(here)))


def run_select(checker: dict, chunks: list[dict], project_dir: Path) -> list[dict]:
    """Run a checker's select script over chunks; candidates are clamped into the chunk they came from."""
    payload = json.dumps({"project_dir": posix(project_dir), "chunks": chunks,
                          "max_chunk_lines": checker["max_chunk_lines"]})
    try:
        done = subprocess.run(expand_command(checker["select"], checker["here"]), input=payload, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", cwd=project_dir, timeout=SELECT_TIMEOUT_SECONDS)
    except (OSError, subprocess.TimeoutExpired) as err:
        raise SelectError(f"select could not run: {err}") from err
    if done.returncode != 0:
        raise SelectError(f"select failed (exit {done.returncode}): {done.stderr.strip()[-300:] or 'no message'}")
    try:
        rows = json.loads(done.stdout or "[]")
    except json.JSONDecodeError as err:
        raise SelectError(f"select output is not JSON: {err}") from err
    if not isinstance(rows, list) or not all(isinstance(r, dict) and {"file", "line_start", "line_end"} <= r.keys()
                                             for r in rows):
        raise SelectError("select output must be a list of {file, line_start, line_end, ...}")
    return clamp_candidates(rows, chunks)


def clamp_candidates(rows: list[dict], chunks: list[dict]) -> list[dict]:
    clamped = []
    for row in rows:
        for chunk in chunks:
            if chunk["file"] != row["file"]:
                continue
            start, end = max(row["line_start"], chunk["line_start"]), min(row["line_end"], chunk["line_end"])
            if start <= end:
                clamped.append({**row, "line_start": start, "line_end": end, "chunk_split": chunk["split"]})
    return clamped


def run_fix_script(command: str, path: Path, project_dir: Path, here: Path,
                   lines: list[tuple[int, int]] | None = None) -> subprocess.CompletedProcess:
    """Run a fix script on one file; `lines` (1-based, inclusive) restricts it to those ranges via --lines S-E,S-E."""
    only = ["--lines", ",".join(f"{a}-{b}" for a, b in lines)] if lines else []
    return subprocess.run([*expand_command(command, here), *only, posix(path)], cwd=project_dir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=SELECT_TIMEOUT_SECONDS)
