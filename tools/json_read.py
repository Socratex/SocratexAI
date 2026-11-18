#!/usr/bin/env python3
"""Read single fields from a big JSON file instead of dumping the whole file into the agent context.

Usage:
    json_read.py FILE                      # top-level keys with value types and sizes
    json_read.py FILE items[3].title       # one value by dotted path ([n] for list items)
    json_read.py FILE items --keys         # keys (or indexes) of the node, not its content
    json_read.py FILE items --find bug     # paths whose string values contain the text
    json_read.py FILE items --max 2000     # cap printed characters (default 4000)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

TOKEN = re.compile(r"[^.\[\]]+|\[(\d+)\]")


def parse_path(path: str) -> list[str | int]:
    parts: list[str | int] = []
    for match in TOKEN.finditer(path or ""):
        parts.append(int(match.group(1)) if match.group(1) is not None else match.group(0))
    return parts


def resolve(node, parts: list[str | int]):
    for part in parts:
        if isinstance(node, list) and isinstance(part, int):
            node = node[part]
        elif isinstance(node, list) and isinstance(part, str) and part.isdigit():
            node = node[int(part)]
        elif isinstance(node, dict):
            node = node[part]
        else:
            raise KeyError(part)
    return node


def describe(value) -> str:
    if isinstance(value, dict):
        return f"object ({len(value)} keys)"
    if isinstance(value, list):
        return f"list ({len(value)} items)"
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= 80 else text[:77] + "..."


def summary(node) -> list[str]:
    if isinstance(node, dict):
        return [f"{key}: {describe(value)}" for key, value in node.items()]
    if isinstance(node, list):
        return [f"[{index}]: {describe(value)}" for index, value in enumerate(node)]
    return [describe(node)]


def find(node, text: str, prefix: str = "") -> list[str]:
    hits: list[str] = []
    items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else []
    for key, value in items:
        path = f"{prefix}[{key}]" if isinstance(key, int) else (f"{prefix}.{key}" if prefix else str(key))
        if isinstance(value, str) and text.lower() in value.lower():
            hits.append(path)
        elif isinstance(value, (dict, list)):
            hits.extend(find(value, text, path))
    return hits


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read single fields from a big JSON file.")
    parser.add_argument("file")
    parser.add_argument("path", nargs="?", default="")
    parser.add_argument("--keys", action="store_true", help="List keys or indexes with types and sizes.")
    parser.add_argument("--find", help="List paths whose string values contain this text.")
    parser.add_argument("--max", type=int, default=4000, help="Maximum characters to print.")
    args = parser.parse_args(argv)

    data = json.loads(Path(args.file).read_text(encoding="utf-8-sig"))
    try:
        node = resolve(data, parse_path(args.path))
    except (KeyError, IndexError, TypeError) as error:
        print(f"Path not found: {args.path} ({error})", file=sys.stderr)
        return 1

    if args.find:
        lines = find(node, args.find, args.path)
    elif args.keys or not args.path:
        lines = summary(node)
    else:
        lines = [json.dumps(node, ensure_ascii=False, indent=2)]
    text = "\n".join(lines)
    print(text if len(text) <= args.max else text[: args.max] + f"\n... ({len(text) - args.max} more characters)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
