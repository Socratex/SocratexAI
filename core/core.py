#!/usr/bin/env python3
"""Config resolver: merges layered config files, validates them and records where every value came from.

Layers, low to high (the later layer wins):
    defaults         defaults/preferences/*/*.json (index of documents per kind of work), then defaults/config.json
    profile          defaults/profiles/<name>.json, <name> = the last `profile` value set by any other layer
    local            local/overrides/config.json
    project          <project>/.socratex/config.json
    project-private  local/projects/<project folder name>/config.json

Merge rules (written explicitly in the later layer's file):
    objects deep-merge; scalars and lists replace
    {"$append": [..]}  append to a list      {"$remove": [..]}  drop items from a list (missing items ignored)
    {"$remove": [..], "$append": [..]}  both in one value: drop first, then append
    {"$delete": true}  remove the key (a missing key is fine)

The flow table (core/flow.json) has its own overrides in the same places, see the flow section below.

Stdlib only. Used by `core/sox config ...` and `core/sox flow ...`.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import state  # noqa: E402

SCHEMA_PATH = ROOT / "core" / "config.schema.json"
SHIPPED_SAFETY = Path(__file__).resolve().parent / "safety.json"   # rule ids when a fake root has no core/safety.json
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


def _config_layers(project_root: Path | str | None, base: Path) -> list[dict]:
    found = [("defaults", base / "defaults" / "config.json"), ("local", base / "local" / "overrides" / "config.json")]
    if project_root:
        project = Path(project_root).resolve()
        found.append(("project", project / ".socratex" / "config.json"))
        found.append(("project-private", base / "local" / "projects" / project.name / "config.json"))
    return [{"name": n, "path": p, "exists": p.is_file(), "kind": "config"} for n, p in found]


def _profile_choice(project_root: Path | str | None, root: Path | None) -> tuple[str | None, str | None]:
    """Return (profile name, name of the layer that set it): the last `profile` string of a present config layer."""
    name = chosen_by = None
    for layer in _config_layers(project_root, Path(root) if root else ROOT):
        if not layer["exists"]:
            continue
        data = _read_json(layer["path"])
        if isinstance(data, dict) and "profile" in data:
            value = data["profile"]
            if isinstance(value, str):
                name, chosen_by = value, layer["name"]
            elif _directive(value):
                name = chosen_by = None
    return name, chosen_by


def selected_profile(project_root: Path | str | None = None, root: Path | None = None) -> str | None:
    """Return the profile name: the last `profile` string set by a present config layer (a $delete clears it)."""
    return _profile_choice(project_root, root)[0]


def layers(project_root: Path | str | None = None, root: Path | None = None) -> list[dict]:
    """Return the ordered layers (low to high) as {name, path, exists, kind}; kind is config, profile or preferences."""
    base = Path(root) if root else ROOT
    configs = _config_layers(project_root, base)
    prefs = [{"name": "defaults", "path": p, "exists": True, "kind": "preferences"}
             for p in sorted((base / "defaults" / "preferences").glob("*/*.json"))]
    profile = selected_profile(project_root, root)
    middle = []
    if profile:
        path = base / "defaults" / "profiles" / f"{profile}.json"
        middle = [{"name": "profile", "path": path, "exists": path.is_file(), "kind": "profile"}]
    return prefs + configs[:1] + middle + configs[1:]


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
    if isinstance(value, dict) and set(value) == {"$append", "$remove"}:
        return "$both", value
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
        elif name == "$both":
            for part in ("$remove", "$append"):
                if not isinstance(arg[part], list):  # type: ignore[index]
                    errors.append(f"{where}: {part} needs a list")
                else:
                    errors += [e for i, item in enumerate(arg[part]) for e in validate(item, schema.get("items", {}), f"{where}.{part}[{i}]")]  # type: ignore[index]
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


def _core_schema(name: str) -> dict:
    return _read_json(Path(__file__).resolve().parent / name)  # type: ignore[return-value]


def _check_file_header(path: Path, data: object, schema_name: str, allow_directives: bool = False) -> dict:
    """Validate a whole layer-like file against core/<schema_name>; errors name the file and key."""
    if not isinstance(data, dict):
        raise ConfigError(f"{path}: top level must be an object")
    if "schema_version" not in data:
        raise ConfigError(f"{path}: missing required key 'schema_version'")
    if data["schema_version"] != SUPPORTED_VERSION:
        raise ConfigError(f"{path}: schema_version {data['schema_version']!r} is not supported "
                          f"(expected {SUPPORTED_VERSION}); {MIGRATE_HINT}")
    errors = validate(data, _core_schema(schema_name), "$", allow_directives=allow_directives)
    if errors:
        raise ConfigError(f"{path}: " + "; ".join(errors))
    return data


def _profile_config_schema() -> dict:
    schema = dict(_schema())
    schema["required"] = []
    schema["properties"] = {k: v for k, v in schema["properties"].items() if k not in ("profile", "schema_version")}
    return schema


def load_layer_file(path: Path) -> dict:
    """Read one layer file and validate it (directives allowed); errors name the file and key."""
    data = _read_json(path)
    return _check_file_header(path, data, "config.schema.json", allow_directives=True)


def load_profile_file(path: Path) -> dict:
    """Read a profile file; return its config bundle as a layer dict (no schema_version: the config layers carry it)."""
    data = _check_file_header(path, _read_json(path), "profile.schema.json")
    errors = validate(data["config"], _profile_config_schema(), "config")
    if errors:
        raise ConfigError(f"{path}: " + "; ".join(errors))
    return dict(data["config"])


def load_preferences_file(path: Path) -> dict:
    """Read a preference index; return it as a config layer dict {preferences: {name: {load_when, files}}}."""
    data = _check_file_header(path, _read_json(path), "preferences.schema.json")
    return {"preferences": {data["name"]: {"load_when": data["load_when"], "files": data["files"]}}}


_LOADERS = {"config": load_layer_file, "profile": load_profile_file, "preferences": load_preferences_file}


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
            elif name != "$remove" or key in base:
                current = base[key] if isinstance(base.get(key), list) else []
                previous = _drop(prov, path)
                if name == "$both":
                    new = [i for i in current if i not in arg["$remove"]] + list(arg["$append"])  # type: ignore[index]
                else:
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


def _drop_project_relaxations(layer: dict, data: dict, chosen_by: str | None, project_file: object) -> str | None:
    """Remove safety.allow that a project file sets (or selects through a profile); return the error line, if any."""
    safety = data.get("safety")
    if layer["name"] == "project" and layer["kind"] == "config" and isinstance(safety, dict) and "allow" in safety:
        del safety["allow"]
        if not safety:
            del data["safety"]
        return f"{layer['path']}: safety.allow in a project file is ignored; only owner layers may relax safety rules"
    if layer["kind"] == "profile" and chosen_by == "project" and isinstance(safety, dict) and safety.get("allow"):
        del data["safety"]
        return (f"{layer['path']}: profile selected by the project file {project_file} relaxes safety rules; "
                "ignored (an owner layer must select it)")
    return None


def _safety_rules(base: Path) -> dict[str, dict]:
    path = base / "core" / "safety.json"
    data = _read_json(path if path.is_file() else SHIPPED_SAFETY)
    return {rule["id"]: rule for rule in data["rules"]}  # type: ignore[index]


def _relaxed_rules(values: dict, prov: dict, base: Path) -> tuple[list[dict], list[str]]:
    known = _safety_rules(base)
    relaxed: list[dict] = []
    errors: list[str] = []
    for rule in dict.fromkeys(values.get("safety", {}).get("allow", [])):
        if rule not in known:
            errors.append(f"safety.allow: unknown rule id '{rule}' (ids are listed in core/safety.json)")
        elif not known[rule]["relaxable"]:
            errors.append(f"safety.allow: rule '{rule}' cannot be relaxed")
        else:
            relaxed.append({"rule": rule, **_list_origin(prov["safety.allow"], rule)})
    return relaxed, errors


def resolve(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    """Merge all present layers. Returns {values, provenance, sources, safety}: provenance maps each leaf key to its layer,
    file and overridden values; safety lists the relaxed rules (rule, layer, file) and the error lines of ignored relaxations."""
    values: dict = {}
    prov: dict = {}
    sources = []
    loaded = []
    missing_profile = None
    all_layers = layers(project_root, root)
    chosen_by = _profile_choice(project_root, root)[1]
    project_file = next((l["path"] for l in all_layers if l["name"] == "project"), None)
    safety_errors: list[str] = []
    for layer in all_layers:
        if not layer["exists"]:
            missing_profile = layer["path"] if layer["name"] == "profile" else missing_profile
            continue
        data = _LOADERS[layer["kind"]](layer["path"])
        problem = _drop_project_relaxations(layer, data, chosen_by, project_file)
        if problem:
            safety_errors.append(problem)
        loaded.append((layer, data))
    if missing_profile:  # reported after the other files so a bad `profile` value shows its own error first
        raise ConfigError(f"{missing_profile}: the selected profile has no file")
    base_extensions = _extension_base(root)
    if base_extensions:
        sources.append(base_extensions[0])
        _merge(values, prov, {"extensions": base_extensions[1]}, "defaults", base_extensions[0]["file"], "")
    for layer, data in loaded:
        sources.append({"layer": layer["name"], "file": str(layer["path"]), "sha256": file_hash(layer["path"])})
        _merge(values, prov, data, layer["name"], str(layer["path"]), "")
    errors = validate(values, _schema(), "$")
    errors += _unknown_extensions(values, root)
    if errors:
        raise ConfigError("resolved config: " + "; ".join(errors))
    relaxed, unusable = _relaxed_rules(values, prov, Path(root) if root else ROOT)
    return {"values": values, "provenance": prov, "sources": sources,
            "safety": {"relaxed": relaxed, "errors": safety_errors + unusable}}


def _extension_base(root: Path | None) -> tuple[dict, list[str]] | None:
    """The lowest `extensions` value: every manifest with default_enabled (None when the root has no manifests)."""
    import extensions
    root = Path(root) if root else ROOT
    if not extensions.has_manifests(root):
        return None
    names = extensions.default_enabled(root)
    fingerprint = extensions.fingerprint(root)
    return (fingerprint, names) if names and fingerprint else None


def _unknown_extensions(values: dict, root: Path | None) -> list[str]:
    """Enabled names that have no manifest (only checked once the root has manifests at all)."""
    import extensions
    root = Path(root) if root else ROOT
    if not extensions.has_manifests(root):
        return []
    known = extensions.load_manifests(root)
    return [f"extensions: '{name}' has no manifest (modules/extensions or local/extensions); "
            f"remove it with `sox ext disable {name}` or add the manifest"
            for name in dict.fromkeys(values.get("extensions", [])) if name not in known]


def _list_origin(entry: dict, member: object) -> dict:
    """Layer and file where `member` entered a list value: the oldest layer of the unbroken run that still holds it."""
    chain = entry["overridden"] + [entry]
    index = max(i for i, item in enumerate(chain) if member in item["value"])
    while index > 0 and member in chain[index - 1]["value"]:
        index -= 1
    return {"layer": chain[index]["layer"], "file": chain[index]["file"]}


def enabled_extensions(result: dict) -> list[dict]:
    """The enabled extensions of a resolve() result as {name, layer, file}: the layer that switched each one on."""
    entry = result["provenance"].get("extensions")
    if not entry:
        return []
    return [{"name": name, **_list_origin(entry, name)} for name in dict.fromkeys(entry["value"])]


def relaxed_rule_ids(project_root: Path | str | None = None, root: Path | None = None) -> set[str]:
    """Ids of the safety rules the effective config relaxes (what the guard skips)."""
    return {item["rule"] for item in resolve(project_root, root)["safety"]["relaxed"]}


# ---------- safety log ----------

def _log_state(path: Path, project: str | None) -> dict[tuple, str]:
    """Replay state/safety-log.jsonl: the relaxations and rejections currently on record for one project."""
    current: dict[tuple, str] = {}
    if not path.is_file():
        return current
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("project") != project:
            continue
        kind = "relaxed" if record["event"] in ("relaxed", "restored") else "rejected"
        key = (kind, record["rule"], record.get("detail", ""))
        if record["event"] in ("relaxed", "rejected"):
            current[key] = record["source"]
        else:
            current.pop(key, None)
    return current


def log_safety(result: dict, project_root: Path | str | None = None, root: Path | None = None) -> list[dict]:
    """Append one record per relaxed rule (or ignored relaxation) to state/safety-log.jsonl, only when it changed since the
    last record for this project; a rule that stopped being relaxed gets a `restored` or `cleared` record. Returns what was appended."""
    project = str(Path(project_root).resolve()) if project_root else None
    path = state.state_dir(root) / "safety-log.jsonl"
    desired = {("relaxed", item["rule"], ""): f"{item['layer']}: {item['file']}" for item in result["safety"]["relaxed"]}
    for message in result["safety"]["errors"]:
        desired[("rejected", "safety.allow", message)] = message.split(": ", 1)[0]
    current = _log_state(path, project)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    records = []
    for key, source in desired.items():
        if current.get(key) != source:
            records.append({"time": now, "project": project, "event": key[0], "rule": key[1], "source": source,
                            **({"detail": key[2]} if key[2] else {})})
    for key, source in current.items():
        if key not in desired:
            records.append({"time": now, "project": project, "event": "restored" if key[0] == "relaxed" else "cleared",
                            "rule": key[1], "source": source, **({"detail": key[2]} if key[2] else {})})
    if records:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.writelines(json.dumps(record, ensure_ascii=False) + "\n" for record in records)
    return records


# ---------- effective.json ----------

def file_hash(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def effective_path(root: Path | None = None) -> Path:
    return state.state_dir(root) / "effective.json"


def write_effective(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    result = resolve(project_root, root)
    result["project"] = str(Path(project_root).resolve()) if project_root else None
    log_safety(result, project_root, root)
    text = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    effective_path(root).write_text(text, encoding="utf-8", newline="\n")
    return result


def _is_fresh(cached: dict, project_root: Path | str | None, root: Path | None) -> bool:
    if cached.get("project") != (str(Path(project_root).resolve()) if project_root else None):
        return False
    current = {str(l["path"]): file_hash(l["path"]) for l in layers(project_root, root) if l["exists"]}
    base_extensions = _extension_base(root)
    if base_extensions:
        current[base_extensions[0]["file"]] = base_extensions[0]["sha256"]
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


# ---------- flow table ----------

FLOW_SCHEMA_PATH = ROOT / "core" / "flow.schema.json"
ACTION_PREFIXES = ("stage", "role", "rule", "gate", "tool")


class FlowError(ConfigError):
    """The flow table or one of its override files is invalid; `errors` holds one `file: step <id>: message` line each."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def flow_layers(project_root: Path | str | None = None, root: Path | None = None) -> list[dict]:
    """Return the flow files, low to high: core/flow.json, then flow.json in the local, project and project-private layers."""
    base = Path(root) if root else ROOT
    found = [("core", base / "core" / "flow.json"), ("local", base / "local" / "overrides" / "flow.json")]
    if project_root:
        project = Path(project_root).resolve()
        found.append(("project", project / ".socratex" / "flow.json"))
        found.append(("project-private", base / "local" / "projects" / project.name / "flow.json"))
    return [{"name": n, "path": p, "exists": p.is_file()} for n, p in found]


def _flow_schema() -> dict:
    return _read_json(FLOW_SCHEMA_PATH)  # type: ignore[return-value]


def check_condition(cond: object, facts: dict, where: str = "when") -> list[str]:
    """Return grammar errors of one `when` condition (see x-condition-grammar in core/flow.schema.json)."""
    if not isinstance(cond, dict):
        return [f"{where}: a condition must be an object"]
    errors: list[str] = []
    for key, value in cond.items():
        if key in ("all", "any"):
            if not isinstance(value, list) or not value:
                errors.append(f"{where}.{key}: needs a non-empty list of conditions")
            else:
                for i, sub in enumerate(value):
                    errors += check_condition(sub, facts, f"{where}.{key}[{i}]")
        elif key == "not":
            errors += check_condition(value, facts, f"{where}.not")
        elif key not in facts:
            errors.append(f"{where}: unknown fact '{key}'")
        else:
            error = _check_operand(key, facts[key], value)
            if error:
                errors.append(f"{where}: {error}")
    return errors


def _check_operand(fact: str, spec: dict, value: object) -> str | None:
    kind = spec["type"]
    if kind == "integer":
        if isinstance(value, dict) and len(value) == 1:
            op, limit = next(iter(value.items()))
            if op in ("gte", "lt") and isinstance(limit, int) and not isinstance(limit, bool):
                return None
        return f"fact '{fact}' takes {{\"gte\": n}} or {{\"lt\": n}}"
    if kind == "boolean":
        return None if isinstance(value, bool) else f"fact '{fact}' takes true or false"
    if isinstance(value, dict):
        if set(value) != {"not"} or isinstance(value["not"], dict):
            return f"fact '{fact}' takes a value, a list or {{\"not\": value-or-list}}"
        value = value["not"]
    items = value if isinstance(value, list) else [value]
    bad = [i for i in items if i not in spec["values"]]
    if not items:
        return f"fact '{fact}': empty list"
    return f"fact '{fact}': {bad[0]!r} is not one of {spec['values']}" if bad else None


def _fact_holds(value: object, spec: dict, actual: object) -> bool:
    if isinstance(value, dict) and set(value) == {"not"}:
        return not _fact_holds(value["not"], spec, actual)
    if actual is None:
        return False
    if spec["type"] == "integer":
        op, limit = next(iter(value.items()))  # type: ignore[union-attr]
        return actual >= limit if op == "gte" else actual < limit  # type: ignore[operator]
    wanted = value if isinstance(value, list) else [value]
    if spec["type"] == "set":
        have = actual if isinstance(actual, (list, set, tuple)) else [actual]
        return any(w in have for w in wanted)
    return actual in wanted


def _holds(cond: dict, facts: dict, known: dict) -> bool:
    for key, value in cond.items():
        if key == "all":
            ok = all(_holds(c, facts, known) for c in value)
        elif key == "any":
            ok = any(_holds(c, facts, known) for c in value)
        elif key == "not":
            ok = not _holds(value, facts, known)
        else:
            ok = _fact_holds(value, facts[key], known.get(key))
        if not ok:
            return False
    return True


def matches(when: dict, known: dict, schema: dict | None = None) -> bool:
    """Evaluate a `when` condition against known facts {name: value}; a missing fact matches nothing."""
    return _holds(when, (schema or _flow_schema())["x-facts"], known)


def check_action(action: str, gates: dict) -> str | None:
    """Return an error for a malformed action string, else None (existence is checked by check_flow)."""
    if action == "ask":
        return None
    prefix, sep, target = action.partition(":")
    if not sep or prefix not in ACTION_PREFIXES or not target:
        return f"action {action!r} is not 'ask' or one of {', '.join(p + ':<x>' for p in ACTION_PREFIXES)}"
    if prefix == "gate" and target not in gates:
        return f"gate '{target}' is not one of {sorted(gates)}"
    return None


def _override_schema(schema: dict) -> dict:
    step = json.loads(json.dumps(schema["properties"]["steps"]["items"]))
    step["properties"].update({"before": {"type": "string"}, "after": {"type": "string"}})
    ids = {"type": "array", "items": {"type": "string"}}
    return {"type": "object", "required": ["schema"], "additionalProperties": False, "properties": {
        "schema": schema["properties"]["schema"], "purpose": {"type": "string"},
        "steps": {"type": "object", "additionalProperties": False, "properties": {
            "$append": {"type": "array", "items": step}, "$remove": ids, "$delete": ids}}}}


def _check_flow_file(path: Path, data: object, schema: dict, override: bool) -> list[str]:
    """Schema, condition and action grammar of one flow file; each error names the file and the step id."""
    if not isinstance(data, dict):
        return [f"{path}: top level must be an object"]
    errors = [f"{path}: {e}" for e in validate(data, _override_schema(schema) if override else schema, "$")]
    if errors:
        return errors
    steps = data.get("steps", {}).get("$append", []) if override else data["steps"]
    seen: set[str] = set()
    for step in steps:
        sid = step["id"]
        if sid in seen:
            errors.append(f"{path}: step {sid}: duplicate id")
        seen.add(sid)
        errors += [f"{path}: step {sid}: {e}" for e in check_condition(step["when"], schema["x-facts"])]
        if not step["then"]:
            errors.append(f"{path}: step {sid}: then is empty")
        errors += [f"{path}: step {sid}: {e}" for a in step["then"] if (e := check_action(a, schema["x-gates"]))]
    return errors


def _apply_override(steps: list[dict], origin: dict, ops: dict, layer: dict) -> list[str]:
    """Apply $remove, $delete, then $append of one override file in place; return error lines."""
    errors: list[str] = []
    file = str(layer["path"])
    existing = {s["id"] for s in steps}
    errors += [f"{file}: step {sid}: $delete names a step that does not exist" for sid in ops.get("$delete", []) if sid not in existing]
    gone = set(ops.get("$remove", [])) | set(ops.get("$delete", []))
    steps[:] = [s for s in steps if s["id"] not in gone]
    for sid in gone:
        origin.pop(sid, None)
    for new in ops.get("$append", []):
        new = dict(new)
        before, after = new.pop("before", None), new.pop("after", None)
        anchor = before or after
        if any(s["id"] == new["id"] for s in steps):
            errors.append(f"{file}: step {new['id']}: id already exists (use $remove first to replace it)")
            continue
        position = len(steps)
        if anchor:
            index = next((i for i, s in enumerate(steps) if s["id"] == anchor), None)
            if index is None:
                errors.append(f"{file}: step {new['id']}: before/after names unknown step '{anchor}'")
                continue
            position = index if before else index + 1
        steps.insert(position, new)
        origin[new["id"]] = {"layer": layer["name"], "file": file}
    return errors


def load_flow(project_root: Path | str | None = None, root: Path | None = None) -> dict:
    """Merge core/flow.json with the override files present. Returns {steps, origin, sources}; raises FlowError."""
    schema = _flow_schema()
    steps: list[dict] = []
    origin: dict[str, dict] = {}
    sources: list[dict] = []
    errors: list[str] = []
    for layer in flow_layers(project_root, root):
        is_core = layer["name"] == "core"
        if not layer["exists"]:
            if is_core:
                raise FlowError([f"{layer['path']}: flow table is missing"])
            continue
        try:
            data = _read_json(layer["path"])
        except ConfigError as exc:
            errors.append(str(exc))
            continue
        problems = _check_flow_file(layer["path"], data, schema, override=not is_core)
        if problems:
            errors += problems
            continue
        sources.append({"layer": layer["name"], "file": str(layer["path"]), "sha256": file_hash(layer["path"])})
        if is_core:
            steps = list(data["steps"])  # type: ignore[index]
            origin = {s["id"]: {"layer": "core", "file": str(layer["path"])} for s in steps}
        else:
            errors += _apply_override(steps, origin, data.get("steps", {}), layer)  # type: ignore[union-attr]
    if errors:
        raise FlowError(errors)
    return {"steps": steps, "origin": origin, "sources": sources}


def _known_roles(base: Path) -> set[str]:
    roles = {p.stem for p in (base / "claude" / "agents").glob("*.md")}
    return roles | {p.stem for p in (base / "modules" / "routing" / "roles").glob("*")}


def check_flow(project_root: Path | str | None = None, root: Path | None = None) -> list[str]:
    """Return every problem of the merged flow: grammar errors plus actions that point to something missing."""
    base = Path(root) if root else ROOT
    try:
        flow = load_flow(project_root, root)
    except FlowError as exc:
        return exc.errors
    roles = _known_roles(base)
    errors: list[str] = []
    for step in flow["steps"]:
        where = f"{flow['origin'][step['id']]['file']}: step {step['id']}"
        for action in step["then"]:
            kind, _, target = action.partition(":")
            if kind == "stage" and not (base / "modules" / "stages" / target).is_dir():
                errors.append(f"{where}: stage '{target}' does not exist (modules/stages/{target})")
            elif kind == "role" and target not in roles:
                errors.append(f"{where}: role '{target}' does not exist (claude/agents, modules/routing/roles)")
            elif kind in ("rule", "tool") and not target.startswith("project:") and not (base / target).is_file():
                errors.append(f"{where}: {kind} path '{target}' does not exist")
    return errors


# ---------- initializer budget ----------

INIT_MAX_BYTES = 2500            # core/INIT.md alone; measured 1915 bytes on 2026-11-22, headroom for small edits
INIT_TOTAL_MAX_BYTES = 4000      # INIT.md plus the generated block: one summary line per enabled extension


def extension_summaries(values: dict, root: Path | None = None) -> list[str]:
    """One line per enabled extension: `name: when_to_use` from its manifest, or just the name while no manifest exists."""
    base = Path(root) if root else ROOT
    lines = []
    for name in dict.fromkeys(values.get("extensions", [])):
        text = name
        for folder in (base / "local" / "extensions", base / "modules" / "extensions"):
            manifest = folder / f"{name}.json"
            if manifest.is_file():
                text = f"{name}: {_read_json(manifest).get('when_to_use', '')}"  # type: ignore[union-attr]
                break
        lines.append(text)
    return lines


EXTENSION_HEADER = "Enabled extensions (`sox ext show <name>` for details):"


def extension_block(values: dict, root: Path | None = None) -> list[str]:
    """The generated startup lines for the enabled extensions: a header, then one `name: when_to_use` line each (empty when none)."""
    lines = extension_summaries(values, root)
    return [EXTENSION_HEADER] + lines if lines else []


def init_size(project_root: Path | str | None = None, root: Path | None = None) -> int:
    """Bytes the initializer costs at session start: core/INIT.md plus the generated extension lines."""
    base = Path(root) if root else ROOT
    values = resolve(project_root, root)["values"]
    lines = extension_block(values, root)
    return (base / "core" / "INIT.md").stat().st_size + sum(len(line.encode("utf-8")) + 1 for line in lines)
