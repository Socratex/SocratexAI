from __future__ import annotations

import argparse

import document_list_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Read structured document items by title or key.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("titles", nargs="*")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--titles", "-Titles", nargs="+", dest="titles_option", default=[])
    parser.add_argument("--json", "-Json", action="store_true")
    args = parser.parse_args()
    path = args.path_option or args.path
    titles = args.titles_option or args.titles
    if not path or not titles:
        raise SystemExit("--path and --titles are required.")
    argv = ["read-titles", path, "--titles", *titles]
    if args.json:
        argv.append("--json")
    return run_module_main(document_list_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())

