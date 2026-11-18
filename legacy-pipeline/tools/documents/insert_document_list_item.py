from __future__ import annotations

import argparse

import document_list_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Insert a checked Markdown list line into a structured document item.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("key", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--key", "-Key", dest="key_option", default="")
    parser.add_argument("--text", "-Text", required=True)
    parser.add_argument("--url", "-Url", default="")
    parser.add_argument("--duplicate-scope", "-DuplicateScope", choices=["item", "document"], default="document")
    parser.add_argument("--create-title", "-CreateTitle", default="")
    parser.add_argument("--allow-duplicate", "-AllowDuplicate", action="store_true")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()
    path = args.path_option or args.path
    key = args.key_option or args.key
    if not path or not key:
        raise SystemExit("--path and --key are required.")
    argv = ["insert", path, key, "--text", args.text, "--scope", args.duplicate_scope]
    if args.url:
        argv.extend(["--url", args.url])
    if args.create_title:
        argv.extend(["--create-title", args.create_title])
    if args.allow_duplicate:
        argv.append("--allow-duplicate")
    return run_module_main(document_list_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())
