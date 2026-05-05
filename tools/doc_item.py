import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import docs_slim


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_document(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_document(path: Path, value: Any) -> None:
    docs_slim.write_document(path, value)


def normalize_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("Structured document must be a mapping.")
    if "items" not in document:
        document["items"] = {}
    if not isinstance(document["items"], dict):
        raise ValueError("Document items must be a mapping.")
    return docs_slim.slim_document(document)


def item_keys(document: dict[str, Any]) -> list[str]:
    index = document.get("index")
    if isinstance(index, list):
        return [str(key) for key in index if str(key)]
    if isinstance(index, dict):
        return [str(key) for key in index.keys() if str(key)]
    items = document.get("items", {})
    if isinstance(items, dict):
        return [str(key) for key in items.keys()]
    return []


def reorder_mapping(mapping: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    ordered: dict[str, Any] = {}
    for key in keys:
        if key in mapping:
            ordered[key] = mapping[key]
    for key, value in mapping.items():
        if key not in ordered:
            ordered[key] = value
    return ordered


def place_key(keys: list[str], key: str, position: str, before: str, after: str) -> list[str]:
    result = [candidate for candidate in keys if candidate != key]
    if before:
        if before not in result:
            raise ValueError(f"Before key does not exist: {before}")
        result.insert(result.index(before), key)
    elif after:
        if after not in result:
            raise ValueError(f"After key does not exist: {after}")
        result.insert(result.index(after) + 1, key)
    elif position == "start":
        insertion_index = 1 if result and result[0] == "quick_index" and key != "quick_index" else 0
        result.insert(insertion_index, key)
    elif position == "end":
        result.append(key)
    else:
        raise ValueError("Use --position start/end or --before/--after.")
    return result


def apply_order(document: dict[str, Any], keys: list[str]) -> dict[str, Any]:
    if "quick_index" not in keys:
        keys = ["quick_index"] + keys
    document["index"] = keys
    document["items"] = reorder_mapping(document["items"], keys)
    return docs_slim.slim_document(document)


def read_item_payload(args: argparse.Namespace) -> dict[str, Any]:
    if args.item_file:
        payload = load_document(Path(args.item_file))
        if not isinstance(payload, dict):
            raise ValueError("--item-file must contain a mapping.")
        return copy.deepcopy(payload)

    title = args.title.strip() if args.title else ""
    if not title:
        raise ValueError("--title is required when --item-file is not used.")

    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    else:
        content = args.content or ""

    payload: dict[str, Any] = {"title": title}
    if content:
        payload["content"] = content
    elif args.allow_empty:
        payload["content"] = ""
    else:
        raise ValueError("--content or --content-file is required unless --allow-empty is used.")
    return payload


def read_bulk_payload(path: Path) -> dict[str, dict[str, Any]]:
    payload = load_document(path)
    if isinstance(payload, dict) and isinstance(payload.get("items"), dict):
        payload = payload["items"]
    if not isinstance(payload, dict):
        raise ValueError("--items-file must contain a mapping or an items mapping.")

    items: dict[str, dict[str, Any]] = {}
    for key, item in payload.items():
        item_key = str(key).strip()
        if not item_key:
            raise ValueError("--items-file contains an empty item key.")
        if item_key == "quick_index":
            raise ValueError("Do not bulk-insert quick_index; it is generated from index/items.")
        if not isinstance(item, dict):
            raise ValueError(f"Bulk item must be a mapping: {item_key}")
        if str(item.get("title", "")).strip() == "":
            raise ValueError(f"Bulk item must contain a non-empty title: {item_key}")
        items[item_key] = copy.deepcopy(item)
    if not items:
        raise ValueError("--items-file contains no items.")
    return items


def command_insert(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_document(path))
    items = document["items"]
    if args.key in items and not args.replace:
        raise ValueError(f"Item already exists: {args.key}")
    items[args.key] = read_item_payload(args)
    keys = place_key(item_keys(document), args.key, args.position, args.before, args.after)
    document = apply_order(document, keys)
    write_document(path, document)
    print(f"OK: inserted {args.key} into {path}")


def place_keys(keys: list[str], new_keys: list[str], position: str, before: str, after: str) -> list[str]:
    result = [candidate for candidate in keys if candidate not in new_keys]
    if before:
        if before not in result:
            raise ValueError(f"Before key does not exist: {before}")
        insertion_index = result.index(before)
    elif after:
        if after not in result:
            raise ValueError(f"After key does not exist: {after}")
        insertion_index = result.index(after) + 1
    elif position == "start":
        insertion_index = 1 if result and result[0] == "quick_index" else 0
    elif position == "end":
        insertion_index = len(result)
    else:
        raise ValueError("Use --position start/end or --before/--after.")
    return result[:insertion_index] + new_keys + result[insertion_index:]


def command_bulk_insert(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_document(path))
    items = document["items"]
    bulk_items = read_bulk_payload(Path(args.items_file))
    for key in bulk_items.keys():
        if key in items and not args.replace:
            raise ValueError(f"Item already exists: {key}")

    for key, item in bulk_items.items():
        items[key] = item
    keys = place_keys(item_keys(document), list(bulk_items.keys()), args.position, args.before, args.after)
    document = apply_order(document, keys)
    write_document(path, document)
    print(f"OK: inserted {len(bulk_items)} item(s) into {path}")


def command_move(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_document(path))
    if args.key not in document["items"]:
        raise ValueError(f"Item does not exist: {args.key}")
    keys = place_key(item_keys(document), args.key, args.position, args.before, args.after)
    document = apply_order(document, keys)
    write_document(path, document)
    print(f"OK: moved {args.key} in {path}")


def command_migrate(args: argparse.Namespace) -> None:
    source_path = Path(args.source)
    target_path = Path(args.target)
    source = normalize_document(load_document(source_path))
    target = normalize_document(load_document(target_path))
    if args.key not in source["items"]:
        raise ValueError(f"Source item does not exist: {args.key}")
    if args.key in target["items"] and not args.replace:
        raise ValueError(f"Target item already exists: {args.key}")

    target["items"][args.key] = copy.deepcopy(source["items"][args.key])
    target_keys = place_key(item_keys(target), args.key, args.position, args.before, args.after)
    target = apply_order(target, target_keys)

    if not args.keep_source:
        source["items"].pop(args.key, None)
        source_keys = [key for key in item_keys(source) if key != args.key]
        source = apply_order(source, source_keys)

    write_document(source_path, source)
    write_document(target_path, target)
    action = "copied" if args.keep_source else "migrated"
    print(f"OK: {action} {args.key} from {source_path} to {target_path}")


def add_position_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--position", choices=["start", "end"], default="end")
    parser.add_argument("--before", default="")
    parser.add_argument("--after", default="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Edit slim structured document items while keeping index and quick_index synchronized.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    insert = subparsers.add_parser("insert")
    insert.add_argument("path")
    insert.add_argument("key")
    insert.add_argument("--title", default="")
    insert.add_argument("--content", default="")
    insert.add_argument("--content-file", default="")
    insert.add_argument("--item-file", default="")
    insert.add_argument("--allow-empty", action="store_true")
    insert.add_argument("--replace", action="store_true")
    add_position_arguments(insert)
    insert.set_defaults(func=command_insert)

    bulk_insert = subparsers.add_parser("bulk-insert")
    bulk_insert.add_argument("path")
    bulk_insert.add_argument("items_file")
    bulk_insert.add_argument("--replace", action="store_true")
    add_position_arguments(bulk_insert)
    bulk_insert.set_defaults(func=command_bulk_insert)

    move = subparsers.add_parser("move")
    move.add_argument("path")
    move.add_argument("key")
    add_position_arguments(move)
    move.set_defaults(func=command_move)

    migrate = subparsers.add_parser("migrate")
    migrate.add_argument("source")
    migrate.add_argument("target")
    migrate.add_argument("key")
    migrate.add_argument("--keep-source", action="store_true")
    migrate.add_argument("--replace", action="store_true")
    add_position_arguments(migrate)
    migrate.set_defaults(func=command_migrate)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
