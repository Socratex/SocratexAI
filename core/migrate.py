#!/usr/bin/env python3
"""Schema migrations for the config files that carry `schema_version` (`sox migrate`).

MIGRATIONS maps (schema name, from_version) to a function that takes the parsed file and returns it at from_version + 1
(it must set `schema_version` itself). Schema names are the layer kinds of core.layers(): `config`, `profile`,
`preferences`. There are no migrations today (schema_version 1 is the only version), so `sox migrate --check` reports
"nothing to do"; the registry and the runner exist so the first schema change is a function plus a test, not a new tool.

`sox migrate --check` lists files whose schema_version is older than core.SUPPORTED_VERSION and the steps that would run.
`sox migrate` applies the complete chains, writing `<file>.pre-migrate.bak` next to each file first; a file with a gap in
its chain is reported and left alone. A file newer than supported is reported, never changed.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable

import core

Migration = Callable[[dict], dict]
MIGRATIONS: dict[tuple[str, int], Migration] = {}


def chain(schema: str, version: int, target: int | None = None) -> tuple[list[int], int | None]:
    """Return (versions whose migration would run, first version with no migration or None when the chain is complete)."""
    target = core.SUPPORTED_VERSION if target is None else target
    steps: list[int] = []
    current = version
    while current < target:
        if (schema, current) not in MIGRATIONS:
            return steps, current
        steps.append(current)
        current += 1
    return steps, None


def candidate_files(project_root: Path | str | None = None, root: Path | None = None) -> list[tuple[str, Path]]:
    """(schema name, path) of every existing layer file plus every shipped profile, without duplicates."""
    base = Path(root) if root else core.ROOT
    found = [(layer["kind"], Path(layer["path"])) for layer in core.layers(project_root, root) if layer["exists"]]
    found += [("profile", path) for path in sorted((base / "defaults" / "profiles").glob("*.json"))]
    seen: set[Path] = set()
    unique = []
    for kind, path in found:
        if path not in seen:
            seen.add(path)
            unique.append((kind, path))
    return unique


def scan(project_root: Path | str | None = None, root: Path | None = None) -> list[dict]:
    """One row per file that is not at the supported version: {file, schema, version, status, steps, missing}.

    status: `outdated` (a complete chain exists), `no-migration` (a gap: `missing` is the version without one),
    `newer` (written by a newer SocratexAI), `unreadable` (not JSON or no integer schema_version)."""
    rows = []
    for kind, path in candidate_files(project_root, root):
        row = {"file": str(path), "schema": kind, "version": None, "status": "unreadable", "steps": [], "missing": None}
        try:
            version = json.loads(path.read_text(encoding="utf-8"))["schema_version"]
        except (OSError, ValueError, KeyError, TypeError):
            rows.append(row)
            continue
        row["version"] = version
        if not isinstance(version, int) or isinstance(version, bool):
            rows.append(row)
        elif version == core.SUPPORTED_VERSION:
            continue
        elif version > core.SUPPORTED_VERSION:
            rows.append({**row, "status": "newer"})
        else:
            steps, missing = chain(kind, version)
            rows.append({**row, "status": "outdated" if missing is None else "no-migration", "steps": steps, "missing": missing})
    return rows


def describe(row: dict) -> str:
    where = f"{row['file']}: {row['schema']} schema_version {row['version']!r}"
    if row["status"] == "outdated":
        steps = ", ".join(f"{row['schema']} v{v} -> v{v + 1}" for v in row["steps"])
        return f"{where}; would run {steps}"
    if row["status"] == "no-migration":
        return f"{where}; no migration is registered for {row['schema']} v{row['missing']}, edit the file by hand"
    if row["status"] == "newer":
        return f"{where} is newer than supported ({core.SUPPORTED_VERSION}); update SocratexAI"
    return f"{where}: cannot read schema_version"


def apply(rows: list[dict]) -> list[str]:
    """Run the complete chains of `outdated` rows (backup first). Returns one line per file touched."""
    lines = []
    for row in rows:
        if row["status"] != "outdated":
            continue
        path = Path(row["file"])
        data = json.loads(path.read_text(encoding="utf-8"))
        for version in row["steps"]:
            data = MIGRATIONS[(row["schema"], version)](data)
        shutil.copy2(path, path.with_name(path.name + ".pre-migrate.bak"))
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        lines.append(f"migrated {path} to schema_version {data.get('schema_version')!r} (backup: {path.name}.pre-migrate.bak)")
    return lines
