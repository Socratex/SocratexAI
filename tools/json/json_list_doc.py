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


def path_parts(path_text: str) -> list[str]:
    separator = "/" if "/" in path_text else "."
    parts = [part for part in path_text.strip(separator).split(separator) if part]
    if not parts:
        raise ValueError("Node path must not be empty.")
    return parts


def node_parts(node_path: str) -> list[str]:
    return path_parts(node_path)


def resolve_node_parent(data: dict[str, Any], node_path: str) -> tuple[Any, str, list[str]]:
    parts = node_parts(node_path)
    current: Any = data
    for part in parts[:-1]:
        if not isinstance(current, dict):
            raise TypeError(f"Node path '{node_path}' cannot descend through non-object value before '{part}'.")
        if part not in current:
            raise KeyError(f"Node path '{node_path}' is missing segment '{part}'.")
        current = current[part]
    if not isinstance(current, dict):
        raise TypeError(f"Node path '{node_path}' parent is not an object.")
    return current, parts[-1], parts[:-1]


def resolve_node(data: dict[str, Any], node_path: str) -> Any:
    parent, key, _ = resolve_node_parent(data, node_path)
    if key not in parent:
        raise KeyError(f"Node path '{node_path}' was not found.")
    return parent[key]


def root_index_collection(parent_parts: list[str]) -> str | None:
    if len(parent_parts) == 1 and parent_parts[0] in {"content", "commands", "flows", "passes", "items"}:
        return parent_parts[0]
    return None


def sync_root_index(data: dict[str, Any], parent_parts: list[str], parent: dict[str, Any]) -> None:
    collection_name = root_index_collection(parent_parts)
    if collection_name and isinstance(data.get("index"), list):
        data["index"] = list(parent.keys())


def reference_key_for_parent(reference_node: str, expected_parent_parts: list[str]) -> str:
    if not reference_node:
        return ""
    parts = node_parts(reference_node)
    if parts[:-1] != expected_parent_parts:
        raise ValueError(
            f"Reference node '{reference_node}' must share parent node "
            f"'{'.'.join(expected_parent_parts)}'."
        )
    return parts[-1]


def insert_mapping_key(parent: dict[str, Any], key: str, value: Any, position: str, reference_key: str, replace: bool = False) -> None:
    if key in parent and not replace:
        raise KeyError(f"Node '{key}' already exists.")
    order = [candidate for candidate in parent.keys() if candidate != key]
    index = insertion_index(list(order), position, reference_key)
    ordered: dict[str, Any] = {}
    for candidate in list(order)[:index]:
        ordered[candidate] = parent[candidate]
    ordered[key] = value
    for candidate in list(order)[index:]:
        ordered[candidate] = parent[candidate]
    parent.clear()
    parent.update(ordered)


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


def command_read_node(args: argparse.Namespace) -> None:
    data = load_json(Path(args.path))
    value = resolve_node(data, args.node)
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_insert_node(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    parent, key, parent_parts = resolve_node_parent(data, args.node)
    reference_key = reference_key_for_parent(args.reference_node, parent_parts)
    insert_mapping_key(parent, key, parse_value(args), args.position, reference_key, args.replace)
    sync_root_index(data, parent_parts, parent)
    write_json(path, data)
    print(f"OK: inserted {args.node}")


def command_set_node(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    parent, key, _ = resolve_node_parent(data, args.node)
    if key not in parent:
        raise KeyError(f"Node path '{args.node}' was not found.")
    parent[key] = parse_value(args)
    write_json(path, data)
    print(f"OK: updated {args.node}")


def command_move_node(args: argparse.Namespace) -> None:
    source_path = Path(args.path)
    target_path = Path(args.target_path) if args.target_path else source_path
    source_data = load_json(source_path)
    target_data = source_data if target_path == source_path else load_json(target_path)

    source_parent, source_key, source_parent_parts = resolve_node_parent(source_data, args.node)
    if source_key not in source_parent:
        raise KeyError(f"Node path '{args.node}' was not found.")

    target_node = args.target_node or args.node
    target_parent, target_key, target_parent_parts = resolve_node_parent(target_data, target_node)
    reference_key = reference_key_for_parent(args.reference_node, target_parent_parts)
    value = source_parent[source_key]

    same_parent = source_data is target_data and source_parent is target_parent
    if not same_parent:
        del source_parent[source_key]
        sync_root_index(source_data, source_parent_parts, source_parent)
    else:
        del source_parent[source_key]

    insert_mapping_key(target_parent, target_key, value, args.position, reference_key, args.replace or same_parent)
    sync_root_index(target_data, target_parent_parts, target_parent)

    write_json(source_path, source_data)
    if target_data is not source_data:
        write_json(target_path, target_data)
    print(f"OK: moved {args.node} to {target_path}:{target_node}")


def command_delete_node(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    parent, key, parent_parts = resolve_node_parent(data, args.node)
    if key not in parent:
        raise KeyError(f"Node path '{args.node}' was not found.")
    del parent[key]
    sync_root_index(data, parent_parts, parent)
    write_json(path, data)
    print(f"OK: deleted {args.node}")


def node_line_list(data: dict[str, Any], node_path: str) -> list[Any]:
    return require_list(resolve_node(data, node_path), node_path)


def command_insert_node_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    lines = node_line_list(data, args.node)
    index = line_reference_index(lines, args.position, args.reference_line, args.reference_text)
    for offset, text in enumerate(args.text):
        lines.insert(index + offset, text)
    write_json(path, data)
    print(f"OK: inserted {len(args.text)} line(s) into {args.node}")


def command_set_node_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    lines = node_line_list(data, args.node)
    if args.line < 1 or args.line > len(lines):
        raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
    lines[args.line - 1] = args.text
    write_json(path, data)
    print(f"OK: updated line {args.line} in {args.node}")


def command_move_node_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    lines = node_line_list(data, args.node)
    if args.line < 1 or args.line > len(lines):
        raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
    value = lines.pop(args.line - 1)
    index = line_reference_index(lines, args.position, args.reference_line, args.reference_text)
    lines.insert(index, value)
    write_json(path, data)
    print(f"OK: moved line {args.line} in {args.node}")


def require_list(value: Any, key: str) -> list[Any]:
    if not isinstance(value, list):
        raise TypeError(f"'{key}' must contain a list for line-level edits.")
    return value


def resolve_field_path(value: Any, field_path: str) -> Any:
    current = value
    if not field_path:
        return current
    for part in path_parts(field_path):
        if not isinstance(current, dict):
            raise TypeError(f"Field path '{field_path}' cannot descend through non-object value before '{part}'.")
        if part not in current:
            raise KeyError(f"Field path '{field_path}' is missing segment '{part}'.")
        current = current[part]
    return current


def selected_list(collection: dict[str, Any], key: str, field_path: str) -> list[Any]:
    if key not in collection:
        raise KeyError(f"Key '{key}' was not found.")
    value = resolve_field_path(collection[key], field_path)
    label = f"{key}.{field_path}" if field_path else key
    return require_list(value, label)


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
    if args.field_path:
        value = resolve_field_path(value, args.field_path)
    if args.line is not None:
        label = f"{args.key}.{args.field_path}" if args.field_path else args.key
        lines = require_list(value, label)
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
    lines = selected_list(collection, args.key, args.field_path)
    index = line_reference_index(lines, args.position, args.reference_line, args.reference_text)
    for offset, text in enumerate(args.text):
        lines.insert(index + offset, text)
    write_json(path, data)
    print(f"OK: inserted {len(args.text)} line(s) into {args.key}")


def command_set_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, _ = find_collection(data, args.collection)
    lines = selected_list(collection, args.key, args.field_path)
    if args.line < 1 or args.line > len(lines):
        raise IndexError(f"Line {args.line} is outside 1..{len(lines)}.")
    lines[args.line - 1] = args.text
    write_json(path, data)
    print(f"OK: updated line {args.line} in {args.key}")


def command_move_line(args: argparse.Namespace) -> None:
    path = Path(args.path)
    data = load_json(path)
    collection, _ = find_collection(data, args.collection)
    lines = selected_list(collection, args.key, args.field_path)
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


def add_node_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path")
    parser.add_argument("node")


def add_node_value(parser: argparse.ArgumentParser) -> None:
    add_value(parser)


def add_node_position(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--position", choices=["start", "end", "before", "after"], default="end")
    parser.add_argument("--reference-node", default="")


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    read = subparsers.add_parser("read")
    add_common(read)
    read.add_argument("key", nargs="?")
    read.add_argument("--line", type=int)
    read.add_argument("--field-path", default="")
    read.set_defaults(func=command_read)

    read_node = subparsers.add_parser("read-node")
    add_node_common(read_node)
    read_node.set_defaults(func=command_read_node)

    insert_node = subparsers.add_parser("insert-node")
    add_node_common(insert_node)
    add_node_position(insert_node)
    add_node_value(insert_node)
    insert_node.add_argument("--replace", action="store_true")
    insert_node.set_defaults(func=command_insert_node)

    set_node = subparsers.add_parser("set-node")
    add_node_common(set_node)
    add_node_value(set_node)
    set_node.set_defaults(func=command_set_node)

    move_node = subparsers.add_parser("move-node")
    add_node_common(move_node)
    add_node_position(move_node)
    move_node.add_argument("--target-path", default="")
    move_node.add_argument("--target-node", default="")
    move_node.add_argument("--replace", action="store_true")
    move_node.set_defaults(func=command_move_node)

    delete_node = subparsers.add_parser("delete-node")
    add_node_common(delete_node)
    delete_node.set_defaults(func=command_delete_node)

    insert_node_line = subparsers.add_parser("insert-node-line")
    add_node_common(insert_node_line)
    add_node_position(insert_node_line)
    insert_node_line.add_argument("--reference-line", type=int)
    insert_node_line.add_argument("--reference-text", default="")
    insert_node_line.add_argument("--text", action="append", required=True)
    insert_node_line.set_defaults(func=command_insert_node_line)

    set_node_line = subparsers.add_parser("set-node-line")
    add_node_common(set_node_line)
    set_node_line.add_argument("--line", type=int, required=True)
    set_node_line.add_argument("--text", required=True)
    set_node_line.set_defaults(func=command_set_node_line)

    move_node_line = subparsers.add_parser("move-node-line")
    add_node_common(move_node_line)
    move_node_line.add_argument("--line", type=int, required=True)
    add_node_position(move_node_line)
    move_node_line.add_argument("--reference-line", type=int)
    move_node_line.add_argument("--reference-text", default="")
    move_node_line.set_defaults(func=command_move_node_line)

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
    insert_line.add_argument("--field-path", default="")
    insert_line.add_argument("--reference-line", type=int)
    insert_line.add_argument("--reference-text", default="")
    insert_line.add_argument("--text", action="append", required=True)
    insert_line.set_defaults(func=command_insert_line)

    set_line = subparsers.add_parser("set-line")
    add_common(set_line)
    set_line.add_argument("key")
    set_line.add_argument("--field-path", default="")
    set_line.add_argument("--line", type=int, required=True)
    set_line.add_argument("--text", required=True)
    set_line.set_defaults(func=command_set_line)

    move_line = subparsers.add_parser("move-line")
    add_common(move_line)
    move_line.add_argument("key")
    move_line.add_argument("--field-path", default="")
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
