import argparse
import copy
import sys
from pathlib import Path
from typing import Any

import yaml

import docs_slim


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def write_yaml(path: Path, value: Any) -> None:
    rendered = yaml.dump(value, Dumper=docs_slim.SlimYamlDumper, allow_unicode=True, sort_keys=False, width=1000)
    path.write_text(rendered, encoding="utf-8")


def normalize_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("YAML document must be a mapping.")
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
        payload = load_yaml(Path(args.item_file))
        if not isinstance(payload, dict):
            raise ValueError("--item-file must contain a YAML mapping.")
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


def command_insert(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_yaml(path))
    items = document["items"]
    if args.key in items and not args.replace:
        raise ValueError(f"Item already exists: {args.key}")
    items[args.key] = read_item_payload(args)
    keys = place_key(item_keys(document), args.key, args.position, args.before, args.after)
    document = apply_order(document, keys)
    write_yaml(path, document)
    print(f"OK: inserted {args.key} into {path}")


def command_move(args: argparse.Namespace) -> None:
    path = Path(args.path)
    document = normalize_document(load_yaml(path))
    if args.key not in document["items"]:
        raise ValueError(f"Item does not exist: {args.key}")
    keys = place_key(item_keys(document), args.key, args.position, args.before, args.after)
    document = apply_order(document, keys)
    write_yaml(path, document)
    print(f"OK: moved {args.key} in {path}")


def command_migrate(args: argparse.Namespace) -> None:
    source_path = Path(args.source)
    target_path = Path(args.target)
    source = normalize_document(load_yaml(source_path))
    target = normalize_document(load_yaml(target_path))
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

    write_yaml(source_path, source)
    write_yaml(target_path, target)
    action = "copied" if args.keep_source else "migrated"
    print(f"OK: {action} {args.key} from {source_path} to {target_path}")


def add_position_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--position", choices=["start", "end"], default="end")
    parser.add_argument("--before", default="")
    parser.add_argument("--after", default="")


def main() -> None:
    parser = argparse.ArgumentParser(description="Edit slim YAML document items while keeping index and quick_index synchronized.")
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
