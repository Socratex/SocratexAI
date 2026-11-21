#!/usr/bin/env python3
"""Config resolver: merges layered config files, validates them and records where every value came from.

Layers, low to high (the later layer wins):
    defaults         defaults/config.json
    local            local/overrides/config.json
    project          <project>/.socratex/config.json
    project-private  local/projects/<project folder name>/config.json

Merge rules (written explicitly in the later layer's file):
    objects deep-merge; scalars and lists replace
    {"$append": [..]}  append to a list      {"$remove": [..]}  drop items from a list (missing items ignored)
    {"$delete": true}  remove the key (a missing key is fine)

Stdlib only. Used by `core/sox config ...`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import state  # noqa: E402

SCHEMA_PATH = ROOT / "core" / "config.schema.json"
SUPPORTED_VERSION = 1
DIRECTIVES = ("$append", "$remove", "$delete")
MIGRATE_HINT = "`sox migrate` is not implemented yet; edit the file by hand"


class ConfigError(Exception):
    """A config file is unreadable, invalid, or has an unknown key."""


def _read_json(path: Path) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigError(f"{path}: cannot read JSON: {exc}") from exc


def layers(project_root: Path | str | None = None, root: Path | None = None) -> list[dict]:
    """Return the ordered layers (low to high) as {name, path, exists}."""
    base = Path(root) if root else ROOT
    found = [
        ("defaults", base / "defaults" / "config.json"),
        ("local", base / "local" / "overrides" / "config.json"),
    ]
    if project_root:
        project = Path(project_root).resolve()
        found.append(("project", project / ".socratex" / "config.json"))
        found.append(("project-private", base / "local" / "projects" / project.name / "config.json"))
    return [{"name": n, "path": p, "exists": p.is_file()} for n, p in found]


# ---------- validation ----------

def _type_ok(value: object, kind: str) -> bool:
    if kind == "object":
        return isinstance(value, dict)
    if kind == "array":
        return isinstance(value, list)
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return True


def _directive(value: object) -> tuple[str, object] | None:
    if isinstance(value, dict) and len(value) == 1:
        key = next(iter(value))
        if key in DIRECTIVES:
            return key, value[key]
    return None


def validate(value: object, schema: dict, where: str, allow_directives: bool = False) -> list[str]:
    """Return error strings for `value` against `schema`; `where` is the dotted key path ('$' = top level)."""
    errors: list[str] = []
    directive = _directive(value) if allow_directives else None
    if directive:
        name, arg = directive
        if name == "$delete":
            if arg is not True:
                errors.append(f"{where}: $delete must be true")
        elif schema.get("type") != "array":
            errors.append(f"{where}: {name} only applies to a list")
        elif not isinstance(arg, list):
            errors.append(f"{where}: {name} needs a list")
        else:
            for i, item in enumerate(arg):
                errors += validate(item, schema.get("items", {}), f"{where}[{i}]")
        return errors
    kind = schema.get("type")
    if kind and not _type_ok(value, kind):
        return [f"{where}: expected {kind}, got {type(value).__name__}"]
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if kind == "array":
        for i, item in enumerate(value):  # type: ignore[arg-type]
            errors += validate(item, schema.get("items", {}), f"{where}[{i}]")
    if kind == "object":
        props = schema.get("properties", {})
        extra = schema.get("additionalProperties", True)
        for key in schema.get("required", []):
            if key not in value:  # type: ignore[operator]
                errors.append(f"missing required key '{key if where == '$' else where + '.' + key}'")
        for key, sub in value.items():  # type: ignore[union-attr]
            path = key if where == "$" else f"{where}.{key}"
            if key in props:
                errors += validate(sub, props[key], path, allow_directives)
            elif isinstance(extra, dict):
                errors += validate(sub, extra, path, allow_directives)
            elif extra is False:
                errors.append(f"unknown key '{path}'")
    return errors


def _schema() -> dict:
    return _read_json(SCHEMA_PATH)  # type: ignore[return-value]


def load_layer_file(path: Path) -> dict:
    """Read one layer file and validate it (directives allowed); errors name the file and key."""
    data = _read_json(path)
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be an object")
    if "schema_version" not in data:
        raise ConfigError(f"{path}: missing required key 'schema_version'")
    version = data["schema_version"]
    if version != SUPPORTED_VERSION:
        raise ConfigError(
            f"{path}: schema_version {version!r} is not supported (expected {SUPPORTED_VERSION}); {MIGRATE_HINT}")
    errors = validate(data, _schema(), "$", allow_directives=True)
    if errors:
        raise ConfigError(f"{path}: " + "; ".join(errors))
    return data


# ---------- merge with provenance ----------

def _drop(prov: dict, prefix: str) -> list[dict]:
    """Remove provenance entries at or under `prefix`; return them."""
    return [prov.pop(k) for k in [k for k in prov if k == prefix or k.startswith(prefix + ".")]]


def _set_leaf(prov: dict, key: str, value: object, layer: str, file: str, previous: list[dict]) -> None:
    overridden: list[dict] = []
    for entry in previous:
        overridden += entry["overridden"] + [{"value": entry["value"], "layer": entry["layer"], "file": entry["file"]}]
    prov[key] = {"value": value, "layer": layer, "file": file, "overridden": overridden}


def _merge(base: dict, prov: dict, over: dict, layer: str, file: str, prefix: str) -> None:
    for key, value in over.items():
        path = f"{prefix}.{key}" if prefix else key
        directive = _directive(value)
        if directive:
            name, arg = directive
            if name == "$delete":
                base.pop(key, None)
                _drop(prov, path)
            elif name == "$append" or key in base:
                current = base[key] if isinstance(base.get(key), list) else []
                previous = _drop(prov, path)
                new = current + list(arg) if name == "$append" else [i for i in current if i not in arg]  # type: ignore[operator]
                base[key] = new
                _set_leaf(prov, path, new, layer, file, previous)
        elif isinstance(value, dict):
            if not isinstance(base.get(key), dict):
                previous = _drop(prov, path)
                base[key] = {}
                if not value:
                    _set_leaf(prov, path, {}, layer, file, previous)
            _merge(base[key], prov, value, layer, file, path)
        else:
            previous = _drop(prov, path)
            base[key] = value
            _set_leaf(prov, path, value, layer, file, previous)


def resolve(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    """Merge all present layers. Returns {values, provenance, sources}; provenance maps each leaf key to its layer, file and overridden values."""
    values: dict = {}
    prov: dict = {}
    sources = []
    for layer in layers(project_root, root):
        if not layer["exists"]:
            continue
        data = load_layer_file(layer["path"])
        sources.append({"layer": layer["name"], "file": str(layer["path"]), "sha256": file_hash(layer["path"])})
        _merge(values, prov, data, layer["name"], str(layer["path"]), "")
    errors = validate(values, _schema(), "$")
    if errors:
        raise ConfigError("resolved config: " + "; ".join(errors))
    return {"values": values, "provenance": prov, "sources": sources}


# ---------- effective.json ----------

def file_hash(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def effective_path(root: Path | None = None) -> Path:
    return state.state_dir(root) / "effective.json"


def write_effective(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    result = resolve(project_root, root)
    result["project"] = str(Path(project_root).resolve()) if project_root else None
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    effective_path(root).write_text(text, encoding="utf-8", newline="\n")
    return result


def _is_fresh(cached: dict, project_root: Path | str | None, root: Path | None) -> bool:
    if cached.get("project") != (str(Path(project_root).resolve()) if project_root else None):
        return False
    current = {str(l["path"]): file_hash(l["path"]) for l in layers(project_root, root) if l["exists"]}
    recorded = {s["file"]: s["sha256"] for s in cached.get("sources", [])}
    return current == recorded


def effective(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    """Return the resolved config from state/effective.json, recomputing it when any source hash differs."""
    path = effective_path(root)
    if path.is_file():
        try:
            cached = json.loads(path.read_text(encoding="utf-8"))
            if _is_fresh(cached, project_root, root):
                return cached
        except ValueError:
            pass
    return write_effective(project_root, root)
