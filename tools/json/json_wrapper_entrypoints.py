#!/usr/bin/env python3
"""Native JSON wrapper entrypoints around json_list_doc.py."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import json_list_doc


POSITION_CHOICES = ["start", "end", "before", "after"]


def run_json_list_doc(arguments: list[str]) -> int:
    old_argv = sys.argv
    sys.argv = [str(Path(__file__).with_name("json_list_doc.py")), *arguments]
    try:
        return json_list_doc.main()
    finally:
        sys.argv = old_argv


def split_csv(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            item = part.strip()
            if item:
                result.append(item)
    return result


def add_path(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path", nargs="?", default="")
    parser.add_argument("--path", dest="path_option", default="")


def resolve_path(args: argparse.Namespace) -> str:
    path = args.path_option or args.path
    if not path:
        raise SystemExit("--path or positional path is required.")
    return path


def add_collection(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--collection", default="")


def add_position(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--position", choices=POSITION_CHOICES, default="end")
    parser.add_argument("--reference", default="")


def add_value(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--text", action="append", default=[])
    parser.add_argument("--value-json", default="")
    parser.add_argument("--value-json-file", default="")
    parser.add_argument("--value-json-stdin", action="store_true")


def append_collection(arguments: list[str], collection: str) -> None:
    if collection:
        arguments.extend(["--collection", collection])


def append_position(arguments: list[str], args: argparse.Namespace) -> None:
    arguments.extend(["--position", args.position])
    if args.reference:
        arguments.extend(["--reference", args.reference])


def append_value(arguments: list[str], args: argparse.Namespace) -> None:
    for text in args.text:
        arguments.extend(["--text", text])
    if args.value_json:
        arguments.extend(["--value-json", args.value_json])
    if args.value_json_file:
        arguments.extend(["--value-json-file", args.value_json_file])
    if args.value_json_stdin:
        arguments.append("--value-json-stdin")


def main_json_read() -> int:
    parser = argparse.ArgumentParser(description="Read a JSON document collection, item, field, or line.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    add_collection(parser)
    parser.add_argument("--key", dest="key_option", default="")
    parser.add_argument("--field-path", default="")
    parser.add_argument("--line", type=int, default=0)
    args = parser.parse_args()

    arguments = ["read", resolve_path(args)]
    key = args.key_option or args.key
    if key:
        arguments.append(key)
    append_collection(arguments, args.collection)
    if args.field_path:
        arguments.extend(["--field-path", args.field_path])
    if args.line > 0:
        arguments.extend(["--line", str(args.line)])
    return run_json_list_doc(arguments)


def main_json_item_insert() -> int:
    parser = argparse.ArgumentParser(description="Insert a keyed entry into a JSON document collection.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    add_position(parser)
    add_value(parser)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["insert-entry", resolve_path(args), key]
    append_collection(arguments, args.collection)
    append_position(arguments, args)
    append_value(arguments, args)
    return run_json_list_doc(arguments)


def main_json_item_set() -> int:
    parser = argparse.ArgumentParser(description="Set or rename a keyed entry in a JSON document collection.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    parser.add_argument("--new-key", default="")
    add_collection(parser)
    add_value(parser)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["set-entry", resolve_path(args), key]
    append_collection(arguments, args.collection)
    if args.new_key:
        arguments.extend(["--new-key", args.new_key])
    append_value(arguments, args)
    return run_json_list_doc(arguments)


def main_json_item_move() -> int:
    parser = argparse.ArgumentParser(description="Move a keyed entry in a JSON document collection.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    add_position(parser)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["move-entry", resolve_path(args), key]
    append_collection(arguments, args.collection)
    append_position(arguments, args)
    return run_json_list_doc(arguments)


def main_json_item_delete() -> int:
    parser = argparse.ArgumentParser(description="Delete a keyed entry from a JSON document collection.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["delete-entry", resolve_path(args), key]
    append_collection(arguments, args.collection)
    return run_json_list_doc(arguments)


def main_json_line_insert() -> int:
    parser = argparse.ArgumentParser(description="Insert line(s) into a list field under a JSON document entry.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    add_position(parser)
    parser.add_argument("--field-path", default="")
    parser.add_argument("--reference-line", type=int, default=0)
    parser.add_argument("--reference-text", default="")
    parser.add_argument("--text", action="append", required=True)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["insert-line", resolve_path(args), key]
    append_collection(arguments, args.collection)
    append_position(arguments, args)
    if args.field_path:
        arguments.extend(["--field-path", args.field_path])
    if args.reference_line > 0:
        arguments.extend(["--reference-line", str(args.reference_line)])
    if args.reference_text:
        arguments.extend(["--reference-text", args.reference_text])
    for text in args.text:
        arguments.extend(["--text", text])
    return run_json_list_doc(arguments)


def main_json_line_set() -> int:
    parser = argparse.ArgumentParser(description="Set one line in a list field under a JSON document entry.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    parser.add_argument("--field-path", default="")
    parser.add_argument("--line", type=int, required=True)
    parser.add_argument("--text", required=True)
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["set-line", resolve_path(args), key, "--line", str(args.line), "--text", args.text]
    append_collection(arguments, args.collection)
    if args.field_path:
        arguments.extend(["--field-path", args.field_path])
    return run_json_list_doc(arguments)


def main_json_line_move() -> int:
    parser = argparse.ArgumentParser(description="Move one line in a list field under a JSON document entry.")
    add_path(parser)
    parser.add_argument("key", nargs="?", default="")
    parser.add_argument("--key", dest="key_option", default="")
    add_collection(parser)
    parser.add_argument("--field-path", default="")
    parser.add_argument("--line", type=int, required=True)
    add_position(parser)
    parser.add_argument("--reference-line", type=int, default=0)
    parser.add_argument("--reference-text", default="")
    args = parser.parse_args()

    key = args.key_option or args.key
    if not key:
        raise SystemExit("--key or positional key is required.")
    arguments = ["move-line", resolve_path(args), key, "--line", str(args.line)]
    append_collection(arguments, args.collection)
    if args.field_path:
        arguments.extend(["--field-path", args.field_path])
    append_position(arguments, args)
    if args.reference_line > 0:
        arguments.extend(["--reference-line", str(args.reference_line)])
    if args.reference_text:
        arguments.extend(["--reference-text", args.reference_text])
    return run_json_list_doc(arguments)


def main_json_refresh_index() -> int:
    parser = argparse.ArgumentParser(description="Refresh a JSON document root index from a collection.")
    add_path(parser)
    add_collection(parser)
    args = parser.parse_args()

    arguments = ["refresh-index", resolve_path(args)]
    append_collection(arguments, args.collection or "content")
    return run_json_list_doc(arguments)


def main_json_migrate_content() -> int:
    parser = argparse.ArgumentParser(description="Migrate a JSON object collection into canonical content/index shape.")
    add_path(parser)
    parser.add_argument("source_key", nargs="?", default="")
    parser.add_argument("--source-key", dest="source_key_option", default="")
    args = parser.parse_args()

    source_key = args.source_key_option or args.source_key
    if not source_key:
        raise SystemExit("--source-key or positional source_key is required.")
    return run_json_list_doc(["migrate-content", resolve_path(args), source_key])


def main_json_node_edit() -> int:
    parser = argparse.ArgumentParser(description="Edit JSON by full node path.")
    parser.add_argument(
        "operation",
        nargs="?",
        choices=["read", "insert", "set", "move", "delete", "insert-line", "set-line", "move-line"],
        default="",
    )
    parser.add_argument("--operation", dest="operation_option", choices=["read", "insert", "set", "move", "delete", "insert-line", "set-line", "move-line"], default="")
    add_path(parser)
    parser.add_argument("node", nargs="?", default="")
    parser.add_argument("--node", dest="node_option", default="")
    parser.add_argument("--target-path", default="")
    parser.add_argument("--target-node", default="")
    parser.add_argument("--position", choices=POSITION_CHOICES, default="end")
    parser.add_argument("--reference-node", default="")
    parser.add_argument("--line", type=int, default=0)
    parser.add_argument("--reference-line", type=int, default=0)
    parser.add_argument("--reference-text", default="")
    parser.add_argument("--replace", action="store_true")
    add_value(parser)
    args = parser.parse_args()

    operation = args.operation_option or args.operation
    if not operation:
        raise SystemExit("--operation or positional operation is required.")
    node = args.node_option or args.node
    if not node:
        raise SystemExit("--node or positional node is required.")
    command_by_operation = {
        "read": "read-node",
        "insert": "insert-node",
        "set": "set-node",
        "move": "move-node",
        "delete": "delete-node",
        "insert-line": "insert-node-line",
        "set-line": "set-node-line",
        "move-line": "move-node-line",
    }
    arguments = [command_by_operation[operation], resolve_path(args), node]
    if operation in {"insert", "move", "insert-line", "move-line"}:
        arguments.extend(["--position", args.position])
        if args.reference_node:
            arguments.extend(["--reference-node", args.reference_node])
    if operation == "move":
        if args.target_path:
            arguments.extend(["--target-path", args.target_path])
        if args.target_node:
            arguments.extend(["--target-node", args.target_node])
        if args.replace:
            arguments.append("--replace")
    if operation in {"insert", "set"}:
        if args.replace and operation == "insert":
            arguments.append("--replace")
        append_value(arguments, args)
    if operation == "insert-line":
        if args.reference_line > 0:
            arguments.extend(["--reference-line", str(args.reference_line)])
        if args.reference_text:
            arguments.extend(["--reference-text", args.reference_text])
        for text in args.text:
            arguments.extend(["--text", text])
    if operation == "set-line":
        if args.line <= 0:
            raise SystemExit("--line is required for set-line.")
        if not args.text:
            raise SystemExit("--text is required for set-line.")
        arguments.extend(["--line", str(args.line), "--text", args.text[-1]])
    if operation == "move-line":
        if args.line <= 0:
            raise SystemExit("--line is required for move-line.")
        arguments.extend(["--line", str(args.line)])
        if args.reference_line > 0:
            arguments.extend(["--reference-line", str(args.reference_line)])
        if args.reference_text:
            arguments.extend(["--reference-text", args.reference_text])
    return run_json_list_doc(arguments)
