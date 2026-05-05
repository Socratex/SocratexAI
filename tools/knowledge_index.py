import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "socratex-knowledge-index/v3"
COMPILER_VERSION = "3"
DEFAULT_DB_PATH = "AI-compiled/project/knowledge.sqlite"
DEFAULT_MANIFEST_PATH = "AI-compiled/project/knowledge-manifest.json"
DEFAULT_FILE_DIR = "AI-compiled/project/knowledge-files"
DEFAULT_VIEWS_PATH = "docs-tech/KNOWLEDGE-VIEWS.json"

TAG_DESCRIPTIONS = {
    "adapters": "Scene/runtime adapter boundaries.",
    "architecture": "Durable architecture and ownership rules.",
    "borrowed-before-bespoke": "Prefer proven external patterns before custom systems when they reduce risk.",
    "coding": "Code readability and implementation rules.",
    "comments": "Comment policy and documentation-in-code rules.",
    "compiled-context": "Compiled context, generated knowledge, and instruction cache workflows.",
    "csharp": "C# domain and validation rules.",
    "data-first": "Data owns truth before scene projection.",
    "debugging": "Interactive debugging and failure investigation.",
    "diagnostics": "Logging, debug, and observability rules.",
    "documentation": "Documentation and durable memory file rules.",
    "docs-workflow": "Documentation workflow, source-of-truth, and finalizer rules.",
    "engineering": "General engineering standards.",
    "explicit-flow": "Explicit control/data/state flow.",
    "gamedev": "Game-development-specific engineering rules for the gamedev pack.",
    "knowledge": "Compiled knowledge index, tag query, and note-selection rules.",
    "maintainability": "Long-term maintenance and traceability rules.",
    "ownership": "Source-of-truth and subsystem ownership rules.",
    "performance": "Runtime cost, budgets, and profiling rules.",
    "persistence": "Save/load, durable state, and reload rules.",
    "planning": "Planning, pass selection, and priority sequencing rules.",
    "readability": "Human and agent readability rules.",
    "runtime": "Runtime lifecycle and gameplay execution rules.",
    "session-start": "Knowledge that should be loaded at the beginning of session context building.",
    "tests": "Automated or manual verification rules.",
    "top-down": "Top-down source organization.",
    "verification": "Verification strategy and quality gates.",
    "domain_modeling": "Domain modeling, generated-state, and durable state rules.",
}


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text_if_changed(path: Path, content: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and read_text(path) == content:
        return False
    path.write_text(content, encoding="utf-8", newline="\n")
    return True


def normalized_hash_text(text: str) -> str:
    if text.startswith("\ufeff"):
        text = text[1:]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip(" \t") for line in text.split("\n")]
    normalized = "\n".join(lines).rstrip("\n")
    if normalized:
        return normalized + "\n"
    return ""


def sha256_text(text: str) -> str:
    return hashlib.sha256(normalized_hash_text(text).encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    return sha256_text(read_text(path))


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(read_text(path))


def load_structured(path: Path) -> Any:
    return load_json(path)


def is_structured_source(path: Path) -> bool:
    return path.suffix.lower() in {".json", ".json", ".json"}


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def normalize_tags(raw: Any) -> list[str]:
    if raw is None:
        return []
    raw_values = [raw] if isinstance(raw, str) else list(raw)
    tags: list[str] = []
    for value in raw_values:
        tag = str(value).strip().lower()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def normalize_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        return raw.strip().lower() in ("1", "true", "yes", "y")
    return bool(raw)


def scalar_text(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw.strip()
    return json.dumps(raw, ensure_ascii=False, sort_keys=True)


def should_skip_source(relative_path: str) -> bool:
    path = normalize_path(relative_path)
    return (
        path.startswith("AI-compiled/")
        or path.startswith("docs-tech/cache/")
        or path.startswith("ignored/")
        or path.startswith("templates/")
        or path.startswith("tools/tmp/")
        or path.endswith("/manifest.json")
        or path.endswith("/stale-report.json")
        or path
        in {
            "docs-tech/CODE_LINE_INDEX.json",
            "docs-tech/LARGE_FILES.json",
        }
    )


def discover_structured_sources(repo_root: Path) -> list[Path]:
    paths: list[Path] = []
    for pattern in ("*.json", "*.json", "*.json"):
        for path in repo_root.rglob(pattern):
            relative = normalize_path(str(path.relative_to(repo_root)))
            if not should_skip_source(relative):
                paths.append(path)
    return sorted(set(paths), key=lambda value: normalize_path(str(value.relative_to(repo_root))))


def find_tagged_entries(value: Any, selector: str) -> list[tuple[str, dict[str, Any]]]:
    found: list[tuple[str, dict[str, Any]]] = []
    if isinstance(value, dict):
        if is_knowledge_entry(value):
            found.append((selector, value))
            return found
        for key, child in value.items():
            child_selector = f"{selector}.{key}" if selector else str(key)
            found.extend(find_tagged_entries(child, child_selector))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            child_selector = f"{selector}.{index}" if selector else str(index)
            found.extend(find_tagged_entries(child, child_selector))
    return found


def is_knowledge_entry(value: dict[str, Any]) -> bool:
    return (
        isinstance(value.get("id"), str)
        and isinstance(value.get("type"), str)
        and "tags" in value
        and ("rule" in value or "body" in value or "summary" in value)
    )


def normalize_entry(raw: dict[str, Any], document_path: str, selector: str) -> dict[str, Any]:
    tags = normalize_tags(raw.get("tags"))
    if not tags:
        raise ValueError(f"Knowledge entry has no tags: {raw.get('id')}")
    name = str(raw.get("name") or raw.get("id") or raw.get("title")).strip()
    if not name:
        raise ValueError(f"Knowledge entry has no name/id in {document_path}:{selector}")
    entry = {
        "document_path": document_path,
        "name": name,
        "type": normalize_type(raw["type"]),
        "subtype": scalar_text(raw.get("subtype")),
        "title": scalar_text(raw.get("title") or name),
        "summary": scalar_text(raw.get("summary")),
        "body": scalar_text(raw.get("rule") or raw.get("body")),
        "rationale": scalar_text(raw.get("rationale")),
        "priority": scalar_text(raw.get("priority") or "should"),
        "source_of_truth": normalize_path(str(raw.get("source_of_truth") or document_path)),
        "load_at_start": normalize_bool(raw.get("load_at_start", False)),
        "stability": scalar_text(raw.get("stability") or "durable"),
        "source_selector": selector,
        "tags": tags,
        "sources": normalize_sources(raw, document_path, selector),
    }
    entry["compiled_content"] = compile_entry_content(entry)
    return entry


def normalize_type(raw: Any) -> str:
    value = str(raw).strip().lower()
    legacy_map = {
        "engineering_rule": "rule",
        "architecture_rule": "rule",
        "coding_rule": "rule",
        "verification_rule": "rule",
        "workflow_rule": "workflow",
    }
    return legacy_map.get(value, value)


def normalize_sources(raw: dict[str, Any], document_path: str, selector: str) -> list[dict[str, Any]]:
    source_refs = raw.get("source_refs") or []
    if isinstance(source_refs, dict):
        source_refs = [source_refs]
    sources: list[dict[str, Any]] = []
    if not source_refs:
        sources.append({"path": document_path, "selector": selector, "is_duplicate": False, "note": "record source"})
    else:
        for index, ref in enumerate(source_refs):
            if isinstance(ref, str):
                sources.append({"path": normalize_path(ref), "selector": "", "is_duplicate": index > 0, "note": ""})
            elif isinstance(ref, dict):
                sources.append(
                    {
                        "path": normalize_path(str(ref.get("path") or document_path)),
                        "selector": str(ref.get("selector") or ""),
                        "is_duplicate": normalize_bool(ref.get("is_duplicate", index > 0)),
                        "note": str(ref.get("note") or ""),
                    }
                )
    for duplicate in raw.get("duplicates") or []:
        if isinstance(duplicate, str):
            sources.append({"path": normalize_path(duplicate), "selector": "", "is_duplicate": True, "note": "duplicate"})
        elif isinstance(duplicate, dict):
            sources.append(
                {
                    "path": normalize_path(str(duplicate.get("path") or "")),
                    "selector": str(duplicate.get("selector") or ""),
                    "is_duplicate": True,
                    "note": str(duplicate.get("note") or "duplicate"),
                }
            )
    return [source for source in sources if source.get("path")]


def compile_entry_content(entry: dict[str, Any]) -> str:
    lines = [
        f"## {entry['name']} - {entry['title']}",
        "",
        f"- document: `{entry['document_path']}`",
        f"- type: `{entry['type']}`",
        f"- priority: `{entry['priority']}`",
        f"- load_at_start: `{str(entry['load_at_start']).lower()}`",
        f"- tags: {', '.join(f'`{tag}`' for tag in entry['tags'])}",
        f"- source_of_truth: `{entry['source_of_truth']}`",
        "",
    ]
    if entry["subtype"]:
        lines.insert(5, f"- subtype: `{entry['subtype']}`")
    if entry["summary"]:
        lines += [entry["summary"], ""]
    if entry["body"]:
        lines += [entry["body"], ""]
    if entry["rationale"]:
        lines += [f"Rationale: {entry['rationale']}", ""]
    if entry["sources"]:
        lines.append("Sources:")
        for source in entry["sources"]:
            duplicate = " duplicate" if source["is_duplicate"] else ""
            selector = f" `{source['selector']}`" if source["selector"] else ""
            note = f" - {source['note']}" if source["note"] else ""
            lines.append(f"- `{source['path']}`{selector}{duplicate}{note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def collect_document_entries(repo_root: Path, document_path: str) -> tuple[str, list[dict[str, Any]], dict[str, str]]:
    relative = normalize_path(document_path)
    path = repo_root / relative
    if not path.exists():
        raise FileNotFoundError(f"Knowledge source document is missing: {relative}")
    document_hash = sha256_file(path) or ""
    if not is_structured_source(path):
        return document_hash, [], {relative: document_hash}
    document = load_structured(path)
    entries = [normalize_entry(raw, relative, selector) for selector, raw in find_tagged_entries(document, "")]
    document_hashes = {relative: document_hash}
    for entry in entries:
        for source in entry["sources"]:
            source_path = normalize_path(source["path"])
            if should_skip_source(source_path):
                continue
            absolute_source = repo_root / source_path
            if absolute_source.exists() and absolute_source.is_file():
                document_hashes[source_path] = sha256_file(absolute_source) or ""
    return document_hash, entries, document_hashes


def collect_all_entries(repo_root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    entries: list[dict[str, Any]] = []
    document_hashes: dict[str, str] = {}
    for path in discover_structured_sources(repo_root):
        relative = normalize_path(str(path.relative_to(repo_root)))
        document_hash, document_entries, source_hashes = collect_document_entries(repo_root, relative)
        document_hashes[relative] = document_hash
        if document_entries:
            entries.extend(document_entries)
        document_hashes.update(source_hashes)
    entries.sort(key=lambda entry: (entry["document_path"], entry["name"]))
    return entries, dict(sorted(document_hashes.items()))


def load_view_configs(repo_root: Path) -> list[dict[str, Any]]:
    views_path = repo_root / DEFAULT_VIEWS_PATH
    if not views_path.exists():
        return []
    document = load_structured(views_path)
    raw_views = []
    selector_prefix = "views"
    if isinstance(document, dict):
        content = document.get("content")
        if isinstance(content, dict) and isinstance(content.get("views"), list):
            raw_views = content.get("views")
            selector_prefix = "content.views"
        elif isinstance(document.get("metadata"), dict) and isinstance(document["metadata"].get("views"), list):
            raw_views = document["metadata"].get("views")
            selector_prefix = "metadata.views"
        else:
            raw_views = document.get("views")
    if not isinstance(raw_views, list):
        raise ValueError(f"{DEFAULT_VIEWS_PATH} must contain `views`, `content.views`, or `metadata.views`.")
    configs: list[dict[str, Any]] = []
    for index, raw in enumerate(raw_views):
        if not isinstance(raw, dict):
            raise ValueError(f"Knowledge view at index {index} must be a mapping.")
        view_id = str(raw.get("id") or "").strip()
        if not view_id:
            raise ValueError(f"Knowledge view at index {index} has no id.")
        match_mode = str(raw.get("match") or "all").strip().lower()
        if match_mode not in ("all", "any"):
            raise ValueError(f"Knowledge view `{view_id}` has invalid match: {match_mode}")
        configs.append(
            {
                "view_id": view_id,
                "title": scalar_text(raw.get("title") or view_id),
                "description": scalar_text(raw.get("description")),
                "tags": normalize_tags(raw.get("tags")),
                "match": match_mode,
                "type": normalize_type(raw.get("type")) if raw.get("type") else "",
                "load_at_start": normalize_bool(raw.get("load_at_start", False)),
                "source_path": DEFAULT_VIEWS_PATH,
                "source_selector": f"{selector_prefix}.{index}",
            }
        )
    return configs


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    ensure_schema(connection)
    return connection


def repo_root_from_db_path(db_path: Path) -> Path:
    expected_suffix = normalize_path(DEFAULT_DB_PATH)
    normalized_db = normalize_path(str(db_path))
    if normalized_db.endswith(expected_suffix):
        root_text = normalized_db[: -len(expected_suffix)].rstrip("/")
        if root_text:
            return Path(root_text)
    return Path.cwd()


def ensure_schema(connection: sqlite3.Connection) -> None:
    connection.execute("pragma foreign_keys = on")
    connection.executescript(
        """
        create table if not exists metadata (
            key text primary key,
            value text not null
        );
        create table if not exists documents (
            path text primary key,
            hash text not null,
            compiled_at text not null
        );
        create table if not exists tags (
            tag text primary key,
            description text not null
        );
        create table if not exists entries (
            document_path text not null,
            name text not null,
            type text not null,
            subtype text not null default '',
            title text not null,
            summary text not null,
            compiled_content text not null,
            priority text not null,
            source_of_truth text not null,
            load_at_start integer not null,
            stability text not null,
            source_selector text not null,
            compiled_at text not null,
            primary key (document_path, name),
            foreign key (document_path) references documents(path) on delete cascade
        );
        create table if not exists entry_tags (
            document_path text not null,
            entry_name text not null,
            tag text not null,
            primary key (document_path, entry_name, tag),
            foreign key (document_path, entry_name) references entries(document_path, name) on delete cascade,
            foreign key (tag) references tags(tag)
        );
        create table if not exists entry_sources (
            document_path text not null,
            entry_name text not null,
            path text not null,
            selector text not null,
            is_duplicate integer not null,
            note text not null,
            foreign key (document_path, entry_name) references entries(document_path, name) on delete cascade
        );
        create table if not exists views (
            view_id text primary key,
            title text not null,
            description text not null,
            match_mode text not null,
            type_filter text not null,
            tag_filter text not null,
            load_at_start_only integer not null,
            source_path text not null,
            source_selector text not null,
            compiled_at text not null
        );
        create table if not exists view_entries (
            view_id text not null,
            document_path text not null,
            entry_name text not null,
            order_index integer not null,
            primary key (view_id, document_path, entry_name),
            foreign key (view_id) references views(view_id) on delete cascade,
            foreign key (document_path, entry_name) references entries(document_path, name) on delete cascade
        );
        create index if not exists idx_entry_tags_tag on entry_tags(tag);
        create index if not exists idx_entries_type on entries(type);
        create index if not exists idx_entries_load_at_start on entries(load_at_start);
        create index if not exists idx_entry_sources_path on entry_sources(path);
        create index if not exists idx_view_entries_view on view_entries(view_id);
        """
    )
    ensure_column(connection, "entries", "subtype", "text not null default ''")
    connection.executemany(
        "insert or ignore into tags(tag, description) values (?, ?)",
        sorted(TAG_DESCRIPTIONS.items()),
    )
    connection.executemany(
        "insert or replace into metadata(key, value) values (?, ?)",
        [
            ("schema", SCHEMA),
            ("compiler_version", COMPILER_VERSION),
        ],
    )
    connection.commit()


def ensure_column(connection: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    columns = {str(row["name"]) for row in connection.execute(f"pragma table_info({table})")}
    if column not in columns:
        connection.execute(f"alter table {table} add column {column} {definition}")


def reset_database(db_path: Path) -> None:
    if db_path.exists():
        try:
            db_path.unlink()
        except PermissionError as error:
            raise PermissionError(
                f"Cannot rebuild knowledge DB because it is locked: {normalize_path(str(db_path))}. "
                "Close any SQLite viewer, then rerun tools/knowledge_compile.ps1."
            ) from error


def upsert_document(connection: sqlite3.Connection, path: str, document_hash: str, entries: list[dict[str, Any]], related_hashes: dict[str, str]) -> None:
    now = utc_now()
    all_document_hashes = dict(related_hashes)
    all_document_hashes[path] = document_hash
    for document_path, current_hash in sorted(all_document_hashes.items()):
        connection.execute(
            "insert into documents(path, hash, compiled_at) values (?, ?, ?) on conflict(path) do update set hash = excluded.hash, compiled_at = excluded.compiled_at",
            (document_path, current_hash, now),
        )
    connection.execute("delete from entries where document_path = ?", (path,))
    for entry in entries:
        connection.execute(
            """
            insert into entries(
                document_path, name, type, subtype, title, summary, compiled_content, priority,
                source_of_truth, load_at_start, stability, source_selector, compiled_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry["document_path"],
                entry["name"],
                entry["type"],
                entry["subtype"],
                entry["title"],
                entry["summary"],
                entry["compiled_content"],
                entry["priority"],
                entry["source_of_truth"],
                1 if entry["load_at_start"] else 0,
                entry["stability"],
                entry["source_selector"],
                now,
            ),
        )
        for tag in entry["tags"]:
            connection.execute(
                "insert or ignore into tags(tag, description) values (?, ?)",
                (tag, TAG_DESCRIPTIONS.get(tag, "")),
            )
            connection.execute(
                "insert into entry_tags(document_path, entry_name, tag) values (?, ?, ?)",
                (entry["document_path"], entry["name"], tag),
            )
        for source in entry["sources"]:
            connection.execute(
                "insert into entry_sources(document_path, entry_name, path, selector, is_duplicate, note) values (?, ?, ?, ?, ?, ?)",
                (
                    entry["document_path"],
                    entry["name"],
                    source["path"],
                    source["selector"],
                    1 if source["is_duplicate"] else 0,
                    source["note"],
                ),
            )
    connection.commit()
    refresh_views(connection)


def refresh_views(connection: sqlite3.Connection) -> None:
    repo_root = repo_root_from_db_path(Path(connection.execute("pragma database_list").fetchone()["file"]).resolve())
    view_configs = load_view_configs(repo_root)
    now = utc_now()
    connection.execute("delete from view_entries")
    connection.execute("delete from views")
    for view in view_configs:
        connection.execute(
            """
            insert into views(
                view_id, title, description, match_mode, type_filter, tag_filter,
                load_at_start_only, source_path, source_selector, compiled_at
            ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                view["view_id"],
                view["title"],
                view["description"],
                view["match"],
                view["type"],
                ",".join(view["tags"]),
                1 if view["load_at_start"] else 0,
                view["source_path"],
                view["source_selector"],
                now,
            ),
        )
        entries = select_entries_from_connection(
            connection,
            tags=view["tags"],
            match=view["match"],
            entry_type=view["type"],
            load_at_start=view["load_at_start"],
            source_path="",
            document_path="",
            name="",
            view_id="",
        )
        for order_index, entry in enumerate(entries):
            connection.execute(
                "insert into view_entries(view_id, document_path, entry_name, order_index) values (?, ?, ?, ?)",
                (view["view_id"], entry["document_path"], entry["name"], order_index),
            )


def rebuild_database(repo_root: Path, db_path: Path, manifest_path: Path) -> None:
    entries, document_hashes = collect_all_entries(repo_root)
    reset_database(db_path)
    connection = connect(db_path)
    try:
        by_document: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            by_document.setdefault(entry["document_path"], []).append(entry)
        for document_path, document_entries in sorted(by_document.items()):
            upsert_document(connection, document_path, document_hashes[document_path], document_entries, document_hashes)
        refresh_views(connection)
        connection.execute(
            "insert or replace into metadata(key, value) values (?, ?)",
            ("signature", build_signature(connection)),
        )
        connection.commit()
    finally:
        connection.close()
    write_manifest(db_path, manifest_path)
    print("Rebuilt compiled knowledge database.")
    print(f"knowledge entries: {len(entries)}")
    print(f"knowledge documents: {len(document_hashes)}")


def upsert_paths(repo_root: Path, db_path: Path, manifest_path: Path, paths: list[str]) -> None:
    connection = connect(db_path)
    try:
        changed_entries = 0
        for document_path in paths:
            relative = normalize_path(document_path)
            document_hash, entries, related_hashes = collect_document_entries(repo_root, relative)
            upsert_document(connection, relative, document_hash, entries, related_hashes)
            changed_entries += len(entries)
            print(f"Upserted {relative}: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
        refresh_views(connection)
        connection.execute(
            "insert or replace into metadata(key, value) values (?, ?)",
            ("signature", build_signature(connection)),
        )
        connection.commit()
    finally:
        connection.close()
    write_manifest(db_path, manifest_path)
    print(f"Upsert complete: {changed_entries} entr{'y' if changed_entries == 1 else 'ies'}")


def delete_entry_or_document(db_path: Path, manifest_path: Path, document_path: str, entry_name: str) -> None:
    connection = connect(db_path)
    try:
        relative = normalize_path(document_path)
        if entry_name:
            connection.execute("delete from entries where document_path = ? and name = ?", (relative, entry_name))
            print(f"Deleted entry {relative}::{entry_name}")
        else:
            connection.execute("delete from documents where path = ?", (relative,))
            print(f"Deleted document {relative}")
        refresh_views(connection)
        connection.execute(
            "insert or replace into metadata(key, value) values (?, ?)",
            ("signature", build_signature(connection)),
        )
        connection.commit()
    finally:
        connection.close()
    write_manifest(db_path, manifest_path)


def rename_document(db_path: Path, manifest_path: Path, old_path: str, new_path: str) -> None:
    connection = connect(db_path)
    try:
        old_relative = normalize_path(old_path)
        new_relative = normalize_path(new_path)
        row = connection.execute("select path, hash, compiled_at from documents where path = ?", (old_relative,)).fetchone()
        if row is None:
            raise ValueError(f"Document not found in knowledge DB: {old_relative}")
        connection.commit()
        connection.execute("pragma foreign_keys = off")
        connection.execute(
            "insert into documents(path, hash, compiled_at) values (?, ?, ?) on conflict(path) do update set hash = excluded.hash, compiled_at = excluded.compiled_at",
            (new_relative, row["hash"], row["compiled_at"]),
        )
        connection.execute("update entries set document_path = ? where document_path = ?", (new_relative, old_relative))
        connection.execute("update entry_tags set document_path = ? where document_path = ?", (new_relative, old_relative))
        connection.execute("update entry_sources set document_path = ? where document_path = ?", (new_relative, old_relative))
        connection.execute("update entry_sources set path = ? where path = ?", (new_relative, old_relative))
        connection.execute("update entries set source_of_truth = ? where source_of_truth = ?", (new_relative, old_relative))
        connection.execute("delete from documents where path = ?", (old_relative,))
        violations = connection.execute("pragma foreign_key_check").fetchall()
        if violations:
            details = "; ".join(str(dict(violation)) for violation in violations)
            raise ValueError(f"Knowledge DB rename left foreign-key violations: {details}")
        connection.execute("pragma foreign_keys = on")
        refresh_views(connection)
        connection.execute(
            "insert or replace into metadata(key, value) values (?, ?)",
            ("signature", build_signature(connection)),
        )
        connection.commit()
        print(f"Renamed knowledge document {old_relative} -> {new_relative}")
    finally:
        connection.close()
    write_manifest(db_path, manifest_path)


def build_signature(connection: sqlite3.Connection) -> str:
    payload = {
        "schema": SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "documents": [dict(row) for row in connection.execute("select path, hash from documents order by path")],
        "entries": [dict(row) for row in connection.execute("select document_path, name, compiled_content from entries order by document_path, name")],
        "tags": [dict(row) for row in connection.execute("select document_path, entry_name, tag from entry_tags order by document_path, entry_name, tag")],
        "views": [dict(row) for row in connection.execute("select view_id, title, tag_filter, type_filter, load_at_start_only from views order by view_id")],
    }
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def write_manifest(db_path: Path, manifest_path: Path) -> None:
    connection = connect(db_path)
    try:
        manifest = {
            "schema": f"{SCHEMA}-manifest",
            "compiler_version": COMPILER_VERSION,
            "database_path": normalize_path(str(db_path)),
            "generated_at": utc_now(),
            "documents": [dict(row) for row in connection.execute("select path, hash, compiled_at from documents order by path")],
            "entries": [dict(row) for row in connection.execute("select document_path, name, type, subtype, load_at_start from entries order by document_path, name")],
            "tags": [dict(row) for row in connection.execute("select tag, description from tags order by tag")],
            "views": [dict(row) for row in connection.execute("select view_id, title, match_mode, type_filter, tag_filter, load_at_start_only from views order by view_id")],
        }
    finally:
        connection.close()
    write_text_if_changed(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def check_database(repo_root: Path, db_path: Path) -> int:
    if not db_path.exists():
        print(f"Knowledge DB missing: {normalize_path(str(db_path))}")
        print("Run: tools/knowledge_compile.ps1")
        return 1
    connection = connect(db_path)
    problems: list[str] = []
    try:
        rows = connection.execute("select path, hash from documents order by path").fetchall()
        if not rows:
            problems.append("Knowledge DB has no source documents.")
        db_paths = {str(row["path"]) for row in rows}
        for row in rows:
            path = str(row["path"])
            expected_hash = str(row["hash"])
            source_path = repo_root / path
            if not source_path.exists():
                problems.append(f"missing source document: {path}")
                continue
            actual_hash = sha256_file(source_path) or ""
            if actual_hash != expected_hash:
                problems.append(f"stale source document: {path} db={expected_hash[:12]} file={actual_hash[:12]}")
        referenced_paths = {
            str(row["path"])
            for row in connection.execute("select distinct path from entry_sources order by path").fetchall()
            if str(row["path"]) and not should_skip_source(str(row["path"]))
        }
        missing_references = sorted(referenced_paths - db_paths)
        for path in missing_references:
            source_path = repo_root / path
            if source_path.exists():
                problems.append(f"referenced source not tracked in documents table: {path}")
    finally:
        connection.close()
    if problems:
        print("Knowledge DB is not current:")
        for problem in problems:
            print(f"- {problem}")
        print("")
        print("Recommended repair:")
        print("- Run `tools/knowledge_upsert.ps1 -Path <document>` for stale tracked documents.")
        print("- Run `tools/knowledge_compile.ps1` for a full rebuild.")
        print("- Run `tools/knowledge_delete.ps1 -Path <document>` for intentionally removed documents.")
        return 1
    print("OK: knowledge DB document hashes match source files.")
    return 0


def file_table_paths(file_dir: Path) -> dict[str, Path]:
    return {
        "metadata": file_dir / "metadata.json",
        "documents": file_dir / "documents.json",
        "entries": file_dir / "entries.json",
        "tags": file_dir / "tags.json",
        "entry_tags": file_dir / "entry_tags.json",
        "entry_sources": file_dir / "entry_sources.json",
        "manifest": file_dir / "manifest.json",
    }


def table_sort_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(row.get(key, "")) for key in ("path", "document_path", "entry_name", "name", "tag", "key"))


def normalize_file_store(store: dict[str, Any]) -> dict[str, Any]:
    for table in ("documents", "entries", "tags", "entry_tags", "entry_sources"):
        store.setdefault(table, [])
        store[table] = sorted(store[table], key=table_sort_key)
    store.setdefault("metadata", {})
    return store


def build_file_store(entries: list[dict[str, Any]], document_hashes: dict[str, str]) -> dict[str, Any]:
    now = utc_now()
    tags = dict(TAG_DESCRIPTIONS)
    entry_rows: list[dict[str, Any]] = []
    entry_tag_rows: list[dict[str, Any]] = []
    entry_source_rows: list[dict[str, Any]] = []
    for entry in entries:
        entry_rows.append(
            {
                "document_path": entry["document_path"],
                "name": entry["name"],
                "type": entry["type"],
                "subtype": entry["subtype"],
                "title": entry["title"],
                "summary": entry["summary"],
                "compiled_content": entry["compiled_content"],
                "priority": entry["priority"],
                "source_of_truth": entry["source_of_truth"],
                "load_at_start": bool(entry["load_at_start"]),
                "stability": entry["stability"],
                "source_selector": entry["source_selector"],
                "compiled_at": now,
            }
        )
        for tag in entry["tags"]:
            tags.setdefault(tag, "")
            entry_tag_rows.append({"document_path": entry["document_path"], "entry_name": entry["name"], "tag": tag})
        for source in entry["sources"]:
            entry_source_rows.append(
                {
                    "document_path": entry["document_path"],
                    "entry_name": entry["name"],
                    "path": source["path"],
                    "selector": source["selector"],
                    "is_duplicate": bool(source["is_duplicate"]),
                    "note": source["note"],
                }
            )
    store = {
        "metadata": {
            "schema": f"{SCHEMA}-file",
            "compiler_version": COMPILER_VERSION,
            "compiled_at": now,
        },
        "documents": [
            {"path": path, "hash": current_hash, "compiled_at": now}
            for path, current_hash in sorted(document_hashes.items())
        ],
        "entries": entry_rows,
        "tags": [{"tag": tag, "description": description} for tag, description in sorted(tags.items())],
        "entry_tags": entry_tag_rows,
        "entry_sources": entry_source_rows,
    }
    store = normalize_file_store(store)
    store["metadata"]["signature"] = build_file_signature(store)
    return store


def build_file_signature(store: dict[str, Any]) -> str:
    payload = {
        "schema": store.get("metadata", {}).get("schema", f"{SCHEMA}-file"),
        "compiler_version": store.get("metadata", {}).get("compiler_version", COMPILER_VERSION),
        "documents": [
            {"path": row["path"], "hash": row["hash"]}
            for row in store.get("documents", [])
        ],
        "entries": [
            {"document_path": row["document_path"], "name": row["name"], "compiled_content": row["compiled_content"]}
            for row in store.get("entries", [])
        ],
        "tags": [
            {"document_path": row["document_path"], "entry_name": row["entry_name"], "tag": row["tag"]}
            for row in store.get("entry_tags", [])
        ],
    }
    return sha256_text(json.dumps(payload, ensure_ascii=False, sort_keys=True))


def write_file_store(file_dir: Path, store: dict[str, Any]) -> None:
    file_dir.mkdir(parents=True, exist_ok=True)
    store = normalize_file_store(store)
    store["metadata"]["signature"] = build_file_signature(store)
    paths = file_table_paths(file_dir)
    for table in ("metadata", "documents", "entries", "tags", "entry_tags", "entry_sources"):
        write_text_if_changed(paths[table], json.dumps(store[table], ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    manifest = {
        "schema": f"{SCHEMA}-file-manifest",
        "compiler_version": COMPILER_VERSION,
        "generated_at": utc_now(),
        "file_dir": normalize_path(str(file_dir)),
        "tables": {
            table: normalize_path(str(paths[table]))
            for table in ("metadata", "documents", "entries", "tags", "entry_tags", "entry_sources")
        },
        "documents": store["documents"],
        "entries": [
            {
                "document_path": row["document_path"],
                "name": row["name"],
                "type": row["type"],
                "subtype": row.get("subtype", ""),
                "load_at_start": row["load_at_start"],
            }
            for row in store["entries"]
        ],
        "tags": store["tags"],
    }
    write_text_if_changed(paths["manifest"], json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def read_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(read_text(path))


def read_file_store(file_dir: Path) -> dict[str, Any]:
    paths = file_table_paths(file_dir)
    store = {
        "metadata": read_json_file(paths["metadata"], {}),
        "documents": read_json_file(paths["documents"], []),
        "entries": read_json_file(paths["entries"], []),
        "tags": read_json_file(paths["tags"], []),
        "entry_tags": read_json_file(paths["entry_tags"], []),
        "entry_sources": read_json_file(paths["entry_sources"], []),
    }
    return normalize_file_store(store)


def rebuild_file_store(repo_root: Path, file_dir: Path) -> None:
    entries, document_hashes = collect_all_entries(repo_root)
    store = build_file_store(entries, document_hashes)
    write_file_store(file_dir, store)
    print("Rebuilt compiled knowledge file fallback.")
    print(f"knowledge entries: {len(entries)}")
    print(f"knowledge documents: {len(document_hashes)}")


def check_file_store(repo_root: Path, file_dir: Path) -> int:
    paths = file_table_paths(file_dir)
    missing_tables = [
        table
        for table in ("metadata", "documents", "entries", "tags", "entry_tags", "entry_sources")
        if not paths[table].exists()
    ]
    if missing_tables:
        print(f"Knowledge file fallback missing table(s): {', '.join(missing_tables)}")
        print("Run: tools/knowledge_file_compile.ps1")
        return 1
    store = read_file_store(file_dir)
    problems: list[str] = []
    rows = store["documents"]
    if not rows:
        problems.append("Knowledge file fallback has no source documents.")
    file_paths = {str(row["path"]) for row in rows}
    for row in rows:
        path = str(row["path"])
        expected_hash = str(row["hash"])
        source_path = repo_root / path
        if not source_path.exists():
            problems.append(f"missing source document: {path}")
            continue
        actual_hash = sha256_file(source_path) or ""
        if actual_hash != expected_hash:
            problems.append(f"stale source document: {path} file-cache={expected_hash[:12]} file={actual_hash[:12]}")
    referenced_paths = {
        str(row["path"])
        for row in store["entry_sources"]
        if str(row["path"]) and not should_skip_source(str(row["path"]))
    }
    for path in sorted(referenced_paths - file_paths):
        source_path = repo_root / path
        if source_path.exists():
            problems.append(f"referenced source not tracked in documents table: {path}")
    if problems:
        print("Knowledge file fallback is not current:")
        for problem in problems:
            print(f"- {problem}")
        print("")
        print("Recommended repair:")
        print("- Run `tools/knowledge_file_upsert.ps1 -Path <document>` for stale tracked documents.")
        print("- Run `tools/knowledge_file_compile.ps1` for a full rebuild.")
        print("- Run `tools/knowledge_file_delete.ps1 -Path <document>` for intentionally removed documents.")
        return 1
    print("OK: knowledge file fallback document hashes match source files.")
    return 0


def upsert_file_paths(repo_root: Path, file_dir: Path, paths: list[str]) -> None:
    store = read_file_store(file_dir)
    now = utc_now()
    changed_entries = 0
    document_rows = {row["path"]: row for row in store["documents"]}
    for document_path in paths:
        relative = normalize_path(document_path)
        document_hash, entries, related_hashes = collect_document_entries(repo_root, relative)
        store["entries"] = [row for row in store["entries"] if row["document_path"] != relative]
        store["entry_tags"] = [row for row in store["entry_tags"] if row["document_path"] != relative]
        store["entry_sources"] = [row for row in store["entry_sources"] if row["document_path"] != relative]
        for tracked_path, current_hash in sorted({**related_hashes, relative: document_hash}.items()):
            document_rows[tracked_path] = {"path": tracked_path, "hash": current_hash, "compiled_at": now}
        partial = build_file_store(entries, {relative: document_hash})
        store["entries"].extend(partial["entries"])
        store["entry_tags"].extend(partial["entry_tags"])
        store["entry_sources"].extend(partial["entry_sources"])
        existing_tags = {row["tag"]: row for row in store["tags"]}
        for tag_row in partial["tags"]:
            existing_tags[tag_row["tag"]] = tag_row
        store["tags"] = list(existing_tags.values())
        changed_entries += len(entries)
        print(f"Upserted file fallback {relative}: {len(entries)} entr{'y' if len(entries) == 1 else 'ies'}")
    store["documents"] = list(document_rows.values())
    store["metadata"] = {"schema": f"{SCHEMA}-file", "compiler_version": COMPILER_VERSION, "compiled_at": now}
    write_file_store(file_dir, store)
    print(f"File fallback upsert complete: {changed_entries} entr{'y' if changed_entries == 1 else 'ies'}")


def delete_file_entry_or_document(file_dir: Path, document_path: str, entry_name: str) -> None:
    store = read_file_store(file_dir)
    relative = normalize_path(document_path)
    if entry_name:
        store["entries"] = [row for row in store["entries"] if not (row["document_path"] == relative and row["name"] == entry_name)]
        store["entry_tags"] = [row for row in store["entry_tags"] if not (row["document_path"] == relative and row["entry_name"] == entry_name)]
        store["entry_sources"] = [row for row in store["entry_sources"] if not (row["document_path"] == relative and row["entry_name"] == entry_name)]
        print(f"Deleted file fallback entry {relative}::{entry_name}")
    else:
        store["documents"] = [row for row in store["documents"] if row["path"] != relative]
        store["entries"] = [row for row in store["entries"] if row["document_path"] != relative]
        store["entry_tags"] = [row for row in store["entry_tags"] if row["document_path"] != relative]
        store["entry_sources"] = [row for row in store["entry_sources"] if row["document_path"] != relative]
        print(f"Deleted file fallback document {relative}")
    write_file_store(file_dir, store)


def rename_file_document(file_dir: Path, old_path: str, new_path: str) -> None:
    store = read_file_store(file_dir)
    old_relative = normalize_path(old_path)
    new_relative = normalize_path(new_path)
    found = False
    for row in store["documents"]:
        if row["path"] == old_relative:
            row["path"] = new_relative
            found = True
    if not found:
        raise ValueError(f"Document not found in knowledge file fallback: {old_relative}")
    for row in store["entries"]:
        if row["document_path"] == old_relative:
            row["document_path"] = new_relative
        if row.get("source_of_truth") == old_relative:
            row["source_of_truth"] = new_relative
    for table in ("entry_tags", "entry_sources"):
        for row in store[table]:
            if row["document_path"] == old_relative:
                row["document_path"] = new_relative
    for row in store["entry_sources"]:
        if row["path"] == old_relative:
            row["path"] = new_relative
    write_file_store(file_dir, store)
    print(f"Renamed file fallback knowledge document {old_relative} -> {new_relative}")


def select_file_entries(
    file_dir: Path,
    tags: list[str],
    match: str,
    entry_type: str,
    load_at_start: bool,
    source_path: str,
    document_path: str,
    name: str,
    view_id: str,
) -> list[dict[str, Any]]:
    if view_id:
        raise ValueError("File fallback does not support named views. Query tags/type/load-at-start instead.")
    store = read_file_store(file_dir)
    tag_rows_by_entry: dict[tuple[str, str], list[str]] = {}
    for row in store["entry_tags"]:
        tag_rows_by_entry.setdefault((row["document_path"], row["entry_name"]), []).append(row["tag"])
    source_rows_by_entry: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in store["entry_sources"]:
        source_rows_by_entry.setdefault((row["document_path"], row["entry_name"]), []).append(dict(row))
    normalized_tags = normalize_tags(tags)
    normalized_source = normalize_path(source_path) if source_path else ""
    normalized_document = normalize_path(document_path) if document_path else ""
    normalized_type = normalize_type(entry_type) if entry_type else ""
    results: list[dict[str, Any]] = []
    for row in store["entries"]:
        entry_tags = sorted(tag_rows_by_entry.get((row["document_path"], row["name"]), []))
        entry_sources = source_rows_by_entry.get((row["document_path"], row["name"]), [])
        if normalized_type and row["type"] != normalized_type:
            continue
        if load_at_start and not bool(row["load_at_start"]):
            continue
        if normalized_document and row["document_path"] != normalized_document:
            continue
        if name and row["name"] != name:
            continue
        if normalized_source and normalized_source not in {source["path"] for source in entry_sources}:
            continue
        if normalized_tags:
            if match == "all" and any(tag not in entry_tags for tag in normalized_tags):
                continue
            if match == "any" and not any(tag in entry_tags for tag in normalized_tags):
                continue
        entry = dict(row)
        entry["load_at_start"] = bool(entry["load_at_start"])
        entry["tags"] = entry_tags
        entry["sources"] = entry_sources
        for source in entry["sources"]:
            source["is_duplicate"] = bool(source["is_duplicate"])
        results.append(entry)
    priority_order = {"must": 0, "should": 1, "prefer": 2, "avoid": 3}
    return sorted(results, key=lambda entry: (priority_order.get(entry["priority"], 4), entry["document_path"], entry["name"]))


def select_entries(
    db_path: Path,
    tags: list[str],
    match: str,
    entry_type: str,
    load_at_start: bool,
    source_path: str,
    document_path: str,
    name: str,
    view_id: str,
) -> list[dict[str, Any]]:
    connection = connect(db_path)
    try:
        return select_entries_from_connection(connection, tags, match, entry_type, load_at_start, source_path, document_path, name, view_id)
    finally:
        connection.close()


def select_entries_from_connection(
    connection: sqlite3.Connection,
    tags: list[str],
    match: str,
    entry_type: str,
    load_at_start: bool,
    source_path: str,
    document_path: str,
    name: str,
    view_id: str,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    order_params: list[Any] = []
    order_prefix = ""
    if view_id:
        clauses.append("exists (select 1 from view_entries ve where ve.view_id = ? and ve.document_path = e.document_path and ve.entry_name = e.name)")
        params.append(view_id)
        order_prefix = "coalesce((select ve.order_index from view_entries ve where ve.view_id = ? and ve.document_path = e.document_path and ve.entry_name = e.name), 999999),"
        order_params.append(view_id)
    if entry_type:
        clauses.append("e.type = ?")
        params.append(normalize_type(entry_type))
    if load_at_start:
        clauses.append("e.load_at_start = 1")
    if document_path:
        clauses.append("e.document_path = ?")
        params.append(normalize_path(document_path))
    if name:
        clauses.append("e.name = ?")
        params.append(name)
    if source_path:
        clauses.append("exists (select 1 from entry_sources es where es.document_path = e.document_path and es.entry_name = e.name and es.path = ?)")
        params.append(normalize_path(source_path))
    normalized_tags = normalize_tags(tags)
    if normalized_tags:
        if match == "all":
            for tag in normalized_tags:
                clauses.append("exists (select 1 from entry_tags et where et.document_path = e.document_path and et.entry_name = e.name and et.tag = ?)")
                params.append(tag)
        else:
            placeholders = ",".join("?" for _ in normalized_tags)
            clauses.append(f"exists (select 1 from entry_tags et where et.document_path = e.document_path and et.entry_name = e.name and et.tag in ({placeholders}))")
            params.extend(normalized_tags)
    where = " where " + " and ".join(clauses) if clauses else ""
    rows = connection.execute(
        f"""
        select e.*
        from entries e
        {where}
        order by
            {order_prefix}
            case e.priority when 'must' then 0 when 'should' then 1 when 'prefer' then 2 when 'avoid' then 3 else 4 end,
            e.document_path,
            e.name
        """,
        params + order_params,
    ).fetchall()
    results: list[dict[str, Any]] = []
    for row in rows:
        entry = dict(row)
        entry["load_at_start"] = bool(entry["load_at_start"])
        entry["tags"] = [
            tag_row["tag"]
            for tag_row in connection.execute(
                "select tag from entry_tags where document_path = ? and entry_name = ? order by tag",
                (entry["document_path"], entry["name"]),
            )
        ]
        entry["sources"] = [
            dict(source_row)
            for source_row in connection.execute(
                "select path, selector, is_duplicate, note from entry_sources where document_path = ? and entry_name = ? order by is_duplicate, path, selector",
                (entry["document_path"], entry["name"]),
            )
        ]
        for source in entry["sources"]:
            source["is_duplicate"] = bool(source["is_duplicate"])
        results.append(entry)
    return results


def render_select(entries: list[dict[str, Any]], output_format: str) -> str:
    if output_format == "json":
        return json.dumps(entries, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if not entries:
        return "No knowledge entries matched the query.\n"
    return "\n".join(entry["compiled_content"].rstrip() for entry in entries) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "mode",
        choices=[
            "compile",
            "rebuild",
            "check",
            "select",
            "query",
            "upsert",
            "delete",
            "rename",
            "file-compile",
            "file-rebuild",
            "file-check",
            "file-select",
            "file-query",
            "file-upsert",
            "file-delete",
            "file-rename",
        ],
    )
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--db", default=DEFAULT_DB_PATH)
    parser.add_argument("--manifest", default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--file-dir", default=DEFAULT_FILE_DIR)
    parser.add_argument("--path", action="append", default=[])
    parser.add_argument("--old-path", default="")
    parser.add_argument("--new-path", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--tags", nargs="*", default=[])
    parser.add_argument("--match", choices=["all", "any"], default="all")
    parser.add_argument("--type", default="")
    parser.add_argument("--view", default="")
    parser.add_argument("--load-at-start", action="store_true")
    parser.add_argument("--source-path", default="")
    parser.add_argument("--document-path", default="")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    db_path = (repo_root / args.db).resolve()
    manifest_path = (repo_root / args.manifest).resolve()
    file_dir = (repo_root / args.file_dir).resolve()

    if args.mode in ("compile", "rebuild"):
        rebuild_database(repo_root, db_path, manifest_path)
        return
    if args.mode in ("file-compile", "file-rebuild"):
        rebuild_file_store(repo_root, file_dir)
        return
    if args.mode == "check":
        raise SystemExit(check_database(repo_root, db_path))
    if args.mode == "file-check":
        raise SystemExit(check_file_store(repo_root, file_dir))
    if args.mode in ("select", "query"):
        entries = select_entries(
            db_path,
            args.tags,
            args.match,
            args.type,
            args.load_at_start,
            args.source_path,
            args.document_path,
            args.name,
            args.view,
        )
        sys.stdout.write(render_select(entries, args.format))
        return
    if args.mode in ("file-select", "file-query"):
        entries = select_file_entries(
            file_dir,
            args.tags,
            args.match,
            args.type,
            args.load_at_start,
            args.source_path,
            args.document_path,
            args.name,
            args.view,
        )
        sys.stdout.write(render_select(entries, args.format))
        return
    if args.mode == "upsert":
        if not args.path:
            raise SystemExit("upsert requires --path")
        upsert_paths(repo_root, db_path, manifest_path, args.path)
        return
    if args.mode == "file-upsert":
        if not args.path:
            raise SystemExit("file-upsert requires --path")
        upsert_file_paths(repo_root, file_dir, args.path)
        return
    if args.mode == "delete":
        if not args.path:
            raise SystemExit("delete requires --path")
        for path in args.path:
            delete_entry_or_document(db_path, manifest_path, path, args.name)
        return
    if args.mode == "file-delete":
        if not args.path:
            raise SystemExit("file-delete requires --path")
        for path in args.path:
            delete_file_entry_or_document(file_dir, path, args.name)
        return
    if args.mode == "rename":
        if not args.old_path or not args.new_path:
            raise SystemExit("rename requires --old-path and --new-path")
        rename_document(db_path, manifest_path, args.old_path, args.new_path)
        return
    if args.mode == "file-rename":
        if not args.old_path or not args.new_path:
            raise SystemExit("file-rename requires --old-path and --new-path")
        rename_file_document(file_dir, args.old_path, args.new_path)
        return


if __name__ == "__main__":
    main()
