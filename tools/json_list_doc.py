import argparse
import json
import sys
from pathlib import Path
from typing import Any


KNOWN_COLLECTIONS = ["content", "commands", "passes", "docs", "flows", "subroutines", "items"]

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return data


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def find_collection(data: dict[str, Any], requested: str) -> tuple[dict[str, Any], str | None]:
    if requested in {".", "root"}:
        return data, None

    if requested:
        collection = data.get(requested)
        if not isinstance(collection, dict):
            raise KeyError(f"Collection '{requested}' is missing or is not an object.")
        return collection, requested

    for name in KNOWN_COLLECTIONS:
        collection = data.get(name)
        if isinstance(collection, dict):
            return collection, name

    return data, None


def collection_uses_root_index(collection_name: str | None) -> bool:
    return collection_name in {"content", "commands", "flows", "passes", "items"}


def indexed_keys(data: dict[str, Any], collection: dict[str, Any], collection_name: str | None = None) -> list[str]:
    index = data.get("index")
    if collection_uses_root_index(collection_name) and isinstance(index, list):
        return [str(item) for item in index]
    return [str(key) for key in collection.keys()]


def reorder_collection(data: dict[str, Any], collection_name: str | None, order: list[str]) -> None:
    collection, _ = find_collection(data, collection_name or "")
    ordered: dict[str, Any] = {}
    for key in order:
        if key in collection:
            ordered[key] = collection[key]
    for key, value in collection.items():
        if key not in ordered:
            ordered[key] = value

    if collection_name is None:
        data.clear()
        data.update(ordered)
    else:
        data[collection_name] = ordered
        if collection_uses_root_index(collection_name) and isinstance(data.get("index"), list):
            data["index"] = [key for key in order if key in ordered]


def insertion_index(order: list[str], position: str, reference: str) -> int:
    if position == "start":
        return 0
    if position == "end":
        return len(order)
    if not reference:
        raise ValueError(f"Position '{position}' requires a reference.")
    if reference not in order:
        raise KeyError(f"Reference '{reference}' was not found.")
    index = order.index(reference)
    return index if position == "before" else index + 1


def parse_value(args: argparse.Namespace) -> Any:
    value_sources = []
    value_json = getattr(args, "value_json", "")
    value_json_file = getattr(args, "value_json_file", "")
    value_json_stdin = bool(getattr(args, "value_json_stdin", False))
    text_values = getattr(args, "text", None) or []

    if value_json:
        value_sources.append("--value-json")
    if value_json_file:
        value_sources.append("--value-json-file")
    if value_json_stdin:
        value_sources.append("--value-json-stdin")
    if text_values:
        value_sources.append("--text")

    if len(value_sources) > 1:
        raise ValueError(f"Use only one value input source, got: {', '.join(value_sources)}.")

    if value_json:
        return json.loads(value_json)
    if value_json_file:
        return json.loads(Path(value_json_file).read_text(encoding="utf-8"))
    if value_json_stdin:
        return json.loads(sys.stdin.read())
    return [str(value) for value in text_values]


def require_list(value: Any, key: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"'{key}' must contain a list for line-level edits.")
    return value


def line_reference_index(lines: list[Any], position: str, reference_line: int | None, reference_text: str) -> int:
    if position == "start":
        return 0
    if position == "end":
        return len(lines)
    if reference_line is not None:
        if reference_line < 1 or reference_line > len(lines):
            raise IndexError(f"Reference line {reference_line} is outside 1..{len(lines)}.")
        index = reference_line - 1
    elif reference_text:
        try:
            index = [str(line) for line in lines].index(reference_text)
        except ValueError as exc:
            raise KeyError(f"Reference text was not found: {reference_text}") from exc
    else:
        raise ValueError(f"Position '{position}' requires -ReferenceLine or -ReferenceText.")
    return index if position == "before" else index + 1


def command_read(args: argparse.Namespace) -> None:
    data = load_json(Path(args.path))
    collection, collection_name = find_collection(data, args.collection)

    if not args.key:
        output = {
            "path": args.path,
            "collection": collection_name or ".",
            "index": indexed_keys(data, collection),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return

    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")
    value = collection[args.key]
    if args.line is not None:
        lines = require_list(value, args.key)
        if args.line < 1 or args.line > len(lines):
            raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
        value = lines[args.line - 1]
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_insert_entry(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, collection_name = find_collection(data, args.collection)
    if args.key in collection:
        raise KeyError(f"Key '{args.key}' already exists.")
    order = indexed_keys(data, collection, collection_name)
    index = insertion_index(order, args.position, args.reference)
    order.insert(index, args.key)
    collection[args.key] = parse_value(args)
    reorder_collection(data, collection_name, order)
    if collection_uses_root_index(collection_name) and isinstance(data.get("index"), list):
        data["index"] = list(data[collection_name].keys())
    write_json(path, data)
    print(f"OK: inserted {args.key}")


def command_set_entry(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, collection_name = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")

    new_key = args.new_key or args.key
    order = indexed_keys(data, collection, collection_name)
    if new_key != args.key and new_key in collection:
        raise KeyError(f"New key '{new_key}' already exists.")
    if new_key != args.key:
        collection[new_key] = collection.pop(args.key)
        order = [new_key if key == args.key else key for key in order]

    collection[new_key] = parse_value(args)
    if collection_name is None:
        write_json(path, data)
        print(f"OK: updated {new_key}")
        return

    reorder_collection(data, collection_name, order)
    write_json(path, data)
    print(f"OK: updated {new_key}")


def command_move_entry(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, collection_name = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")

    order = [key for key in indexed_keys(data, collection, collection_name) if key != args.key]
    index = insertion_index(order, args.position, args.reference)
    order.insert(index, args.key)
    reorder_collection(data, collection_name, order)
    if collection_uses_root_index(collection_name) and isinstance(data.get("index"), list):
        data["index"] = list(data[collection_name].keys())
    write_json(path, data)
    print(f"OK: moved {args.key}")


def command_delete_entry(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, collection_name = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")

    order = [key for key in indexed_keys(data, collection, collection_name) if key != args.key]
    del collection[args.key]
    reorder_collection(data, collection_name, order)
    write_json(path, data)
    print(f"OK: deleted {args.key}")


def command_refresh_index(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, collection_name = find_collection(data, args.collection or "content")
    refreshed: dict[str, Any] = {"index": list(collection.keys())}
    for key, value in data.items():
        if key == "index":
            continue
        refreshed[key] = value
    data.clear()
    data.update(refreshed)
    write_json(path, data)
    print(f"OK: refreshed index from {collection_name or '.'}")


def command_migrate_content(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    source_key = args.source_key
    if source_key not in data:
        raise KeyError(f"Source collection '{source_key}' is missing.")
    if "content" in data and source_key != "content":
        raise KeyError("Target collection 'content' already exists.")
    collection = data[source_key]
    if not isinstance(collection, dict):
        raise TypeError(f"Source collection '{source_key}' must be an object.")

    migrated: dict[str, Any] = {"index": list(collection.keys())}
    migrated["content"] = collection
    for key, value in data.items():
        if key in {source_key, "index"}:
            continue
        migrated[key] = value
    data.clear()
    data.update(migrated)
    write_json(path, data)
    print(f"OK: migrated {source_key} to content")


def command_insert_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, _ = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")
    lines = require_list(collection[args.key], args.key)
    index = line_reference_index(lines, args.position, args.reference_line, args.reference_text)
    for offset, text in enumerate(args.text):
        lines.insert(index + offset, text)
    write_json(path, data)
    print(f"OK: inserted {len(args.text)} line(s) into {args.key}")


def command_set_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, _ = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")
    lines = require_list(collection[args.key], args.key)
    if args.line < 1 or args.line > len(lines):
        raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
    lines[args.line - 1] = args.text
    write_json(path, data)
    print(f"OK: updated line {args.line} in {args.key}")


def command_move_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, _ = find_collection(data, args.collection)
    if args.key not in collection:
        raise KeyError(f"Key '{args.key}' was not found.")
    lines = require_list(collection[args.key], args.key)
    if args.line < 1 or args.line > len(lines):
        raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
    value = lines.pop(args.line - 1)
    index = line_reference_index(lines, args.position, args.reference_line, args.reference_text)
    lines.insert(index, value)
    write_json(path, data)
    print(f"OK: moved line {args.line} in {args.key}")


def add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path")
    parser.add_argument("--collection", default="")


def add_position(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--position", choices=["start", "end", "before", "after"], default="end")
    parser.add_argument("--reference", default="")


def add_value(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--value-json", default="")
    parser.add_argument("--value-json-file", default="")
    parser.add_argument("--value-json-stdin", action="store_true")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    read = subparsers.add_parser("read")
    add_common(read)
    read.add_argument("key", nargs="?")
    read.add_argument("--line", type=int)
    read.set_defaults(func=command_read)

    insert_entry = subparsers.add_parser("insert-entry")
    add_common(insert_entry)
    insert_entry.add_argument("key")
    add_position(insert_entry)
    add_value(insert_entry)
    insert_entry.set_defaults(func=command_insert_entry)

    set_entry = subparsers.add_parser("set-entry")
    add_common(set_entry)
    set_entry.add_argument("key")
    set_entry.add_argument("--new-key", default="")
    add_value(set_entry)
    set_entry.set_defaults(func=command_set_entry)

    move_entry = subparsers.add_parser("move-entry")
    add_common(move_entry)
    move_entry.add_argument("key")
    add_position(move_entry)
    move_entry.set_defaults(func=command_move_entry)

    delete_entry = subparsers.add_parser("delete-entry")
    add_common(delete_entry)
    delete_entry.add_argument("key")
    delete_entry.set_defaults(func=command_delete_entry)

    refresh_index = subparsers.add_parser("refresh-index")
    add_common(refresh_index)
    refresh_index.set_defaults(func=command_refresh_index)

    migrate_content = subparsers.add_parser("migrate-content")
    add_common(migrate_content)
    migrate_content.add_argument("source_key")
    migrate_content.set_defaults(func=command_migrate_content)

    insert_line = subparsers.add_parser("insert-line")
    add_common(insert_line)
    insert_line.add_argument("key")
    add_position(insert_line)
    insert_line.add_argument("--reference-line", type=int)
    insert_line.add_argument("--reference-text", default="")
    insert_line.add_argument("--text", action="append", required=True)
    insert_line.set_defaults(func=command_insert_line)

    set_line = subparsers.add_parser("set-line")
    add_common(set_line)
    set_line.add_argument("key")
    set_line.add_argument("--line", type=int, required=True)
    set_line.add_argument("--text", required=True)
    set_line.set_defaults(func=command_set_line)

    move_line = subparsers.add_parser("move-line")
    add_common(move_line)
    move_line.add_argument("key")
    move_line.add_argument("--line", type=int, required=True)
    add_position(move_line)
    move_line.add_argument("--reference-line", type=int)
    move_line.add_argument("--reference-text", default="")
    move_line.set_defaults(func=command_move_line)

    args = parser.parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
