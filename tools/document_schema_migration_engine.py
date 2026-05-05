import argparse
import copy
import json
from pathlib import Path
from typing import Any

import document_structure_normalizer_engine as document_structure


EXCLUDED_PARTS = {".git", "Tools/Python312", "Tools/python-installer", "Tools/tmp"}
META_KEYS = ["document", "routing"]
CONTENT_KEYS = ["sections", "current", "checkpoint", "immediate_focus", "non_regression_reminders", "risks", "read_next_if_needed"]
REDUNDANT_LEGACY_INDEX_KEYS = ["pass_index", "bug_index"]


def load_document(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_document(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=4) + "\n", encoding="utf-8", newline="\n")


def repo_relative(path: Path, repo_root: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def is_excluded(path: Path, repo_root: Path) -> bool:
    relative = repo_relative(path, repo_root)
    return any(relative == part or relative.startswith(f"{part}/") for part in EXCLUDED_PARTS)


def iter_document_paths(repo_root: Path, patterns: list[str]) -> list[Path]:
    paths: set[Path] = set()
    for pattern in patterns:
        for path in repo_root.glob(pattern):
            if path.is_file() and path.suffix in {".json", ".json", ".json"} and not is_excluded(path, repo_root):
                paths.add(path.resolve())
    return sorted(paths)


def normalize_title(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return fallback


def compact_document_meta(data: dict[str, Any]) -> dict[str, Any]:
    document = data.get("document")
    routing = data.get("routing")
    meta: dict[str, Any] = {}
    if isinstance(document, dict):
        useful_document = {
            key: document[key]
            for key in ["title", "type", "language"]
            if key in document and document[key] not in ["", None]
        }
        if useful_document:
            meta["document"] = useful_document
    if isinstance(routing, dict):
        meta["routing"] = copy.deepcopy(routing)
    return meta


def index_from_old_toc(data: dict[str, Any]) -> list[dict[str, Any]]:
    toc = data.get("toc")
    index: list[dict[str, Any]] = []
    if isinstance(toc, list):
        for item in toc:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key", "")).strip()
            if not key:
                continue
            index.append({"key": key, "title": normalize_title(item.get("title"), key)})
    return index


def add_item(items: dict[str, Any], key: str, title: str, data: Any) -> None:
    if not key:
        return
    payload = copy.deepcopy(data)
    if isinstance(payload, dict):
        payload.setdefault("key", key)
        payload.pop("title", None)
    items[key] = {
        "title": title,
        "data": payload,
    }


def items_from_sections(data: dict[str, Any]) -> dict[str, Any]:
    items: dict[str, Any] = {}
    sections = data.get("sections")
    if isinstance(sections, dict):
        for key, section in sections.items():
            title = key
            if isinstance(section, dict):
                title = normalize_title(section.get("title"), key)
            add_item(items, str(key), title, section)
    for key in CONTENT_KEYS:
        if key == "sections" or key not in data:
            continue
        if key in items:
            continue
        add_item(items, key, key.replace("_", " ").title(), data[key])
    return items


def ensure_index(data: dict[str, Any], items: dict[str, Any]) -> list[dict[str, Any]]:
    index = index_from_old_toc(data)
    seen = {item["key"] for item in index}
    for key, item in items.items():
        if key not in seen:
            index.append({"key": key, "title": normalize_title(item.get("title"), key)})
    return index


def migrate_document(data: Any) -> Any:
    if not isinstance(data, dict):
        return data
    if "index" in data and "items" in data:
        return data

    items = items_from_sections(data)
    migrated: dict[str, Any] = {
        "index": ensure_index(data, items),
        "items": items,
    }
    meta = compact_document_meta(data)
    if meta:
        migrated["meta"] = meta

    passthrough = {
        key: copy.deepcopy(value)
        for key, value in data.items()
        if key not in set(META_KEYS + ["toc", "sections"] + CONTENT_KEYS + REDUNDANT_LEGACY_INDEX_KEYS)
    }
    if passthrough:
        migrated["extra"] = passthrough
    return document_structure.slim_document(migrated)


def command_migrate(args: argparse.Namespace) -> None:
    repo_root = Path(args.repo_root).resolve()
    paths = iter_document_paths(repo_root, args.paths)
    changed: list[str] = []
    for path in paths:
        original = load_document(path)
        migrated = migrate_document(original)
        if migrated == original:
            continue
        changed.append(repo_relative(path, repo_root))
        if not args.check:
            write_document(path, migrated)
    for path in changed:
        print(path)
    if args.check and changed:
        raise SystemExit(1)
    print(f"OK: {'would migrate' if args.check else 'migrated'} {len(changed)} structured document(s).")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate structured JSON documents to the slim index/items/meta layout.")
    parser.add_argument("paths", nargs="*", default=["**/*.json"])
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    command_migrate(args)


if __name__ == "__main__":
    main()
