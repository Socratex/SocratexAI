from __future__ import annotations

import argparse
import sys

import insert_document_list_item


def main() -> int:
    parser = argparse.ArgumentParser(description="Insert a checked list item. Python port does not run task/finalizer gates.")
    parser.add_argument("--path", "-Path", required=True)
    parser.add_argument("--key", "-Key", required=True)
    parser.add_argument("--text", "-Text", required=True)
    parser.add_argument("--url", "-Url", default="")
    parser.add_argument("--duplicate-scope", "-DuplicateScope", choices=["item", "document"], default="document")
    parser.add_argument("--create-title", "-CreateTitle", default="")
    parser.add_argument("--allow-duplicate", "-AllowDuplicate", action="store_true")
    parser.add_argument("--audit", "-Audit", action="store_true")
    parser.add_argument("--markdown-emoji", "-MarkdownEmoji", action="store_true")
    parser.add_argument("--no-line-index", "-NoLineIndex", action="store_true")
    parser.add_argument("--no-normalize", "-NoNormalize", action="store_true")
    parser.add_argument("--no-stat", "-NoStat", action="store_true")
    parser.add_argument("--no-status", "-NoStatus", action="store_true")
    args = parser.parse_args()

    argv = ["--path", args.path, "--key", args.key, "--text", args.text, "--duplicate-scope", args.duplicate_scope]
    if args.url:
        argv.extend(["--url", args.url])
    if args.create_title:
        argv.extend(["--create-title", args.create_title])
    if args.allow_duplicate:
        argv.append("--allow-duplicate")

    old_argv = sys.argv
    sys.argv = [insert_document_list_item.__file__, *argv]
    try:
        return int(insert_document_list_item.main() or 0)
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    raise SystemExit(main())

