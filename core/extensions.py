#!/usr/bin/env python3
"""Extension registry: manifests of plugins, MCP servers, mods, skills and reference packs, and the `sox ext` actions.

Manifests (schema core/extension.schema.json, id socratex-extension/v1):
    modules/extensions/<name>.json   shipped with the repo (layer `shipped`)
    local/extensions/<name>.json     the owner's own (layer `local`); a same-named one overrides the shipped manifest

Kinds: `ref` read-only reference pack (never run), `install` plugin/MCP/mod/skill (changes the agent config, so it runs
only with `install --yes`, after a backup), `note` recommendation only.

Enabling is plain config: the config key `extensions` is the list of enabled names (core.py seeds it from every manifest
with `default_enabled`, then the layers' $append/$remove apply). `enable` and `disable` edit that key in one layer file.

Stdlib only. Used by core/core.py, core/sox and modules/tools/scripts/subrepos.py.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import core

ROOT = core.ROOT
SCHEMA_PATH = Path(__file__).resolve().parent / "extension.schema.json"
SCHEMA_ID = "socratex-extension/v1"
KINDS = ("ref", "install", "note")
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
UNKNOWN = "unknown"
WHEN_MAX = 200
LEDGER_AREA = "Plugins, MCP, tools"
# The ledger (docs/IMPROVEMENTS.json) says `considering` where manifests say `recommended`; `trial` has no ledger twin.
LEDGER_FROM_STATUS = {"adopted": "adopted", "rejected": "rejected", "recommended": "considering", "trial": "considering"}
STATUS_FROM_LEDGER = {"adopted": "adopted", "rejected": "rejected", "considering": "recommended"}


class ExtensionError(core.ConfigError):
    """A manifest is invalid or an extension action cannot be done; the message names the file and key."""


# ---------- hooks the tests replace ----------

def _real_backup(label: str) -> Path:
    sys.path.insert(0, str(ROOT / "modules" / "tools" / "scripts"))
    import backup
    return backup.backup(label)


def _real_run(command: list[str], cwd: Path) -> int:
    return subprocess.run(command, cwd=cwd, check=False).returncode


BACKUP = _real_backup   # (label) -> path of the backup; replaced in tests
RUN = _real_run         # (argv, cwd) -> exit code; replaced in tests


# ---------- locations and loading ----------

def _base(root: Path | str | None) -> Path:
    return Path(root) if root else core.ROOT


def manifest_dirs(root: Path | str | None = None) -> list[tuple[str, Path]]:
    base = _base(root)
    return [("shipped", base / "modules" / "extensions"), ("local", base / "local" / "extensions")]


def has_manifests(root: Path | str | None = None) -> bool:
    return any(folder.is_dir() for _, folder in manifest_dirs(root))


def _schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_manifest(path: Path, data: object, root: Path | str | None = None) -> list[str]:
    """Return error lines `file: key: message` for one manifest (schema first, then the kind and source rules)."""
    errors = [f"{path}: {line}" for line in core.validate(data, _schema(), "$")]
    if errors:
        return errors
    data = dict(data)  # type: ignore[arg-type]
    name, kind, source = data["name"], data["kind"], data["source"]
    if not NAME_RE.match(name):
        errors.append(f"{path}: name: '{name}' must be lower-case letters, digits and hyphens")
    if name != path.stem:
        errors.append(f"{path}: name: '{name}' must equal the file name '{path.stem}'")
    when = data["when_to_use"]
    if not when.strip() or "\n" in when or len(when) > WHEN_MAX:
        errors.append(f"{path}: when_to_use: must be one sentence on one line, 1-{WHEN_MAX} characters")
    if not any(source.get(key) for key in ("url", "path", "id")):
        errors.append(f"{path}: source: needs one of url, path or id")
    if (source.get("url") or source.get("id")) and not (source.get("commit") or source.get("version")):
        errors.append(f"{path}: source: needs commit or version next to url/id (use 'unknown' when not pinned yet)")
    if source.get("url") and not source["url"].startswith(("https://", "http://")) and source["url"] != UNKNOWN:
        errors.append(f"{path}: source.url: must start with https://")
    local_path = source.get("path")
    if local_path and not Path(local_path).is_absolute() and not (_base(root) / local_path).exists():
        errors.append(f"{path}: source.path: '{local_path}' does not exist")
    if kind == "ref":
        if not source.get("url"):
            errors.append(f"{path}: source.url: required for kind ref")
        if source.get("commit", UNKNOWN) != UNKNOWN and not COMMIT_RE.match(source["commit"]):
            errors.append(f"{path}: source.commit: must be 40 hex characters or '{UNKNOWN}'")
        if "install" in data:
            errors.append(f"{path}: install: a reference pack is never installed or run")
        if data["default_enabled"]:
            errors.append(f"{path}: default_enabled: must be false for kind ref")
    elif kind == "install":
        if not data.get("install"):
            errors.append(f"{path}: install: kind install needs a non-empty list of commands")
    elif "install" in data:
        errors.append(f"{path}: install: kind note has no install commands (use kind install)")
    return errors


def load_manifests(root: Path | str | None = None, kinds: tuple[str, ...] | None = None) -> dict[str, dict]:
    """Every manifest by name; a local manifest replaces the shipped one of the same name. Each carries `_layer` and `_file`.
    Any invalid manifest raises ExtensionError listing every problem."""
    found: dict[str, dict] = {}
    errors: list[str] = []
    for layer, folder in manifest_dirs(root):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.json")):
            if path.name == "module.json":
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as exc:
                errors.append(f"{path}: $: cannot read JSON ({exc})")
                continue
            problems = validate_manifest(path, data, root)
            errors += problems
            if not problems:
                found[data["name"]] = {**data, "_layer": layer, "_file": str(path)}
    if errors:
        raise ExtensionError("\n".join(errors))
    return {n: m for n, m in sorted(found.items()) if kinds is None or m["kind"] in kinds}


def default_enabled(root: Path | str | None = None) -> list[str]:
    """Names of the manifests with default_enabled, sorted: the base value of the config key `extensions`."""
    return [name for name, manifest in load_manifests(root).items() if manifest["default_enabled"]]


def fingerprint(root: Path | str | None = None) -> dict | None:
    """One pseudo source for state/effective.json: a hash over all manifest files, so a changed manifest refreshes the cache."""
    digest = hashlib.sha256()
    seen = False
    for layer, folder in manifest_dirs(root):
        for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
            digest.update(f"{layer}/{path.name}\0".encode() + path.read_bytes() + b"\0")
            seen = True
    return {"layer": "defaults", "file": str(manifest_dirs(root)[0][1]), "sha256": digest.hexdigest()} if seen else None


def enabled_names(root: Path | str | None = None, project: Path | str | None = None) -> list[str]:
    """The effective list of enabled extension names (no duplicates, in order)."""
    values = core.resolve(project, Path(root) if root else None)["values"]
    return list(dict.fromkeys(values.get("extensions", [])))


# ---------- list and show ----------

def list_lines(root: Path | str | None = None, project: Path | str | None = None,
               category: str | None = None, status: str | None = None) -> list[str]:
    """`sox ext list`: manifests grouped by category with status, kind and whether the project has them enabled."""
    manifests = load_manifests(root)
    on = set(enabled_names(root, project))
    lines: list[str] = []
    categories = sorted({m["category"] for m in manifests.values()})
    for cat in categories:
        rows = [m for m in manifests.values() if m["category"] == cat and (not category or cat == category)
                and (not status or m["status"] == status)]
        if not rows:
            continue
        lines.append(f"{cat} ({len(rows)})")
        for m in rows:
            mark = "on " if m["name"] in on else "off"
            local = " [local]" if m["_layer"] == "local" else ""
            lines.append(f"  {m['name']:<26} {m['status']:<11} {m['kind']:<8} {mark}{local}  {m['when_to_use'][:70]}")
    return lines or ["no extension matches"]


def show_lines(name: str, root: Path | str | None = None, project: Path | str | None = None) -> list[str]:
    manifests = load_manifests(root)
    if name not in manifests:
        raise ExtensionError(f"unknown extension '{name}' (see `sox ext list`)")
    manifest = manifests[name]
    shown = {k: v for k, v in manifest.items() if not k.startswith("_")}
    on = name in enabled_names(root, project)
    return [f"{name}: {manifest['_layer']} manifest {manifest['_file']}",
            f"enabled here: {'yes' if on else 'no'}", json.dumps(shown, indent=2, ensure_ascii=False)]


# ---------- the ledger ----------

def ledger_path(root: Path | str | None = None) -> Path:
    return _base(root) / "docs" / "IMPROVEMENTS.json"


def _read_ledger(root: Path | str | None) -> tuple[dict, str]:
    path = ledger_path(root)
    if not path.is_file():
        raise ExtensionError(f"{path}: the improvements ledger is missing")
    text = path.read_bytes().decode("utf-8")
    try:
        return json.loads(text),"\r\n" if "\r\n" in text else "\n"
    except ValueError as exc:
        raise ExtensionError(f"{path}: cannot read JSON: {exc}") from exc


def _write_ledger(root: Path | str | None, data: dict, eol: str) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=False).replace("\n", eol)
    ledger_path(root).write_text(text, encoding="utf-8", newline="")


def add_ledger_entry(root: Path | str | None, name: str, url: str) -> int:
    """Append a `considering` entry for a new extension in the ledger's own entry format; returns its id.
    Fields only the owner or a later evaluation can fill carry TODO markers."""
    data, eol = _read_ledger(root)
    today = time.strftime("%Y-%m-%d")
    entry_id = max((item["id"] for item in data["items"]), default=0) + 1
    data["items"].append({
        "id": entry_id, "tag": "?", "area": LEDGER_AREA, "title": name, "status": "considering", "decided": "recommended",
        "what": f"TODO: say what {name} does. Source: {url}",
        "date": today, "source": "sox ext add",
        "why": "TODO: why it was added",
        "expected_result": "TODO: what it promises",
        "result": "Not evaluated yet (trial entry created by `sox ext add`).",
        "result_evidence": "",
    })
    data["updated"] = today
    _write_ledger(root, data, eol)
    return entry_id


# ---------- add, remove ----------

def derive_name(url: str) -> str:
    last = urlparse(url).path.rstrip("/").split("/")[-1]
    last = last[:-4] if last.endswith(".git") else last
    return re.sub(r"[^a-z0-9]+", "-", last.lower()).strip("-")


def _write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")


def add_extension(url: str, root: Path | str | None = None, name: str | None = None, kind: str = "note",
                  category: str | None = None) -> tuple[Path, int]:
    """Create local/extensions/<name>.json (status trial, off) and its ledger entry. Returns (manifest path, ledger id)."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ExtensionError(f"url '{url}' must be an https:// address")
    name = name or derive_name(url)
    if not NAME_RE.match(name):
        raise ExtensionError(f"name '{name}' must be lower-case letters, digits and hyphens (pass --name)")
    if kind not in KINDS:
        raise ExtensionError(f"kind '{kind}' is not one of {', '.join(KINDS)}")
    if name in load_manifests(root):
        raise ExtensionError(f"extension '{name}' already exists (see `sox ext show {name}`)")
    source = {"url": url, "commit": UNKNOWN} if kind == "ref" else {"url": url, "version": UNKNOWN}
    manifest: dict = {
        "schema": SCHEMA_ID, "name": name, "kind": kind, "category": category or UNKNOWN, "source": source,
        "when_to_use": UNKNOWN, "status": "trial", "default_enabled": False,
        "context_cost": {"level": UNKNOWN, "note": UNKNOWN}, "risks": UNKNOWN}
    if kind == "install":
        manifest["install"] = [UNKNOWN]
    path = _base(root) / "local" / "extensions" / f"{name}.json"
    if not ledger_path(root).is_file():
        raise ExtensionError(f"{ledger_path(root)}: the improvements ledger is missing; `sox ext add` records the trial there")
    ledger_id = add_ledger_entry(root, name, url)
    manifest["ledger"] = ledger_id
    _write_json(path, manifest)
    return path, ledger_id


def _layer_config_files(root: Path | str | None) -> list[Path]:
    base = _base(root) / "local"
    return [base / "overrides" / "config.json"] + sorted((base / "projects").glob("*/config.json"))


def remove_extension(name: str, root: Path | str | None = None) -> list[Path]:
    """Delete a local manifest and drop the name from the owner's config layers. Shipped manifests cannot be removed."""
    manifests = load_manifests(root)
    if name not in manifests:
        raise ExtensionError(f"unknown extension '{name}' (see `sox ext list`)")
    manifest = manifests[name]
    if manifest["_layer"] != "local":
        raise ExtensionError(f"'{name}' is shipped with the repo; use `sox ext disable {name}` instead")
    Path(manifest["_file"]).unlink()
    touched = []
    for file in _layer_config_files(root):
        if not file.is_file():
            continue
        data = json.loads(file.read_text(encoding="utf-8"))
        ext = data.get("extensions")
        new = _without(ext, name)
        if new != ext:
            if new is None:
                data.pop("extensions", None)
            else:
                data["extensions"] = new
            _write_json(file, data)
            touched.append(file)
    return touched


def _without(ext: object, name: str) -> object:
    """The `extensions` value of a layer file with `name` dropped from its list or directive lists."""
    if isinstance(ext, list):
        return [i for i in ext if i != name]
    parts = _parts(ext)
    if parts is None:
        return ext
    return _directive_value([i for i in parts[0] if i != name], [i for i in parts[1] if i != name])


# ---------- enable, disable ----------

def layer_config_path(root: Path | str | None, project: Path | str | None) -> Path:
    base = _base(root) / "local"
    if project:
        return base / "projects" / Path(project).resolve().name / "config.json"
    return base / "overrides" / "config.json"


def _parts(current: object) -> tuple[list, list] | None:
    """(append, remove) lists of a directive value of the `extensions` key; None when it is a plain list or $delete."""
    if current is None:
        return [], []
    if isinstance(current, dict) and set(current) <= {"$append", "$remove"}:
        return list(current.get("$append", [])), list(current.get("$remove", []))
    return None


def _directive_value(append: list, remove: list) -> object:
    if append and remove:
        return {"$remove": remove, "$append": append}
    return {"$append": append} if append else {"$remove": remove} if remove else None


def _toggle(current: object, name: str, want: bool, add: bool = True) -> object:
    """New value of the `extensions` key of one layer file so that `name` is on (want) or off. None drops the key.
    With `add` False it only lifts this layer's own opposite entry ($remove when enabling, $append when disabling)."""
    parts = _parts(current)
    if parts is None:
        if isinstance(current, list):
            kept = [i for i in current if i != name]
            return current if want and name in current else kept + [name] if want else kept
        return [name] if want else current   # $delete cleared the list; a plain list restarts it
    append, remove = parts
    if want:
        remove = [i for i in remove if i != name]
        if add and name not in append:
            append.append(name)
    else:
        append = [i for i in append if i != name]
        if add and name not in remove:
            remove.append(name)
    return _directive_value(append, remove)


def set_enabled(name: str, want: bool, root: Path | str | None = None, project: Path | str | None = None) -> str:
    """Turn `name` on or off in ONE layer file (local/overrides, or local/projects/<project> with a project) through
    $append/$remove, then check the effective config really changed. Returns a one-line report; the file is restored on failure."""
    if name not in load_manifests(root):
        raise ExtensionError(f"unknown extension '{name}' (see `sox ext list`)")
    path = layer_config_path(root, project)
    verb = "enabled" if want else "disabled"
    old_text = path.read_text(encoding="utf-8") if path.is_file() else None
    data = json.loads(old_text) if old_text else {"schema_version": 1}
    current = data.get("extensions")
    if (name in enabled_names(root, project)) == want and (not _mentions(path, name) or _toggle(current, name, want) == current):
        return f"{name} is already {verb} here; nothing written"
    try:
        # First only lift this layer's own opposite entry; the name is added to the layer only if that is not enough.
        for add in (False, True):
            new = _toggle(current, name, want, add)
            if new is None:
                data.pop("extensions", None)
            else:
                data["extensions"] = new
            _write_json(path, data)
            if (name in enabled_names(root, project)) == want:
                return f"{name} {verb} in {path}"
    except core.ConfigError:
        _restore(path, old_text)
        raise
    _restore(path, old_text)
    raise ExtensionError(f"{path}: cannot {'enable' if want else 'disable'} '{name}' in this layer alone "
                         "(a higher layer decides); edit it by hand")


def _mentions(path: Path, name: str) -> bool:
    """Whether a layer file names the extension in its `extensions` value (list, $append or $remove)."""
    if not path.is_file():
        return False
    ext = json.loads(path.read_text(encoding="utf-8")).get("extensions")
    parts = _parts(ext) if isinstance(ext, dict) else None
    items = ext if isinstance(ext, list) else (parts[0] + parts[1] if parts else [])
    return name in items


def _restore(path: Path, old_text: str | None) -> None:
    if old_text is None:
        path.unlink(missing_ok=True)
    else:
        path.write_text(old_text, encoding="utf-8", newline="")


# ---------- install ----------

def install_extension(name: str, yes: bool, root: Path | str | None = None) -> list[str]:
    """Print the install commands (dry run) or, with `yes`, back up the agent config and then run them.
    Only kind install is ever executed. Returns the lines to print; raises ExtensionError on a refusal or a failed command."""
    manifests = load_manifests(root)
    if name not in manifests:
        raise ExtensionError(f"unknown extension '{name}' (see `sox ext list`)")
    manifest = manifests[name]
    if manifest["kind"] == "ref":
        raise ExtensionError(f"'{name}' is a read-only reference pack (kind ref): it is never installed or run; "
                             "read it through modules/tools/scripts/subrepos.py")
    if manifest["kind"] == "note":
        raise ExtensionError(f"'{name}' is a recommendation only (kind note): it has no install commands")
    if manifest["status"] == "rejected":
        raise ExtensionError(f"'{name}' has status rejected; change its status first")
    commands = manifest["install"]
    if any(command.strip() == UNKNOWN for command in commands):
        raise ExtensionError(f"{manifest['_file']}: install: still '{UNKNOWN}'; fill in the commands first")
    lines = [f"{name}: {len(commands)} install command(s), run in this order:"] + [f"  {c}" for c in commands]
    if not yes:
        return lines + ["Dry run: nothing was backed up or executed. Run `sox ext install " + name + " --yes` after the owner's yes."]
    lines.append(f"Backup: {BACKUP('pre-ext-install')}")
    for command in commands:
        argv = shlex.split(command)
        if argv and argv[0] in ("python", "python3"):
            argv[0] = sys.executable
        code = RUN(argv, _base(root))
        lines.append(f"ran (exit {code}): {command}")
        if code != 0:
            raise ExtensionError("\n".join(lines + [f"stopped: '{command}' failed; later commands were not run"]))
    return lines + [f"Done. Status stays '{manifest['status']}'; enable it with `sox ext enable {name}` when it should load."]
