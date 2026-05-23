from __future__ import annotations

import argparse

import document_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Bulk insert structured document items.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("items_file", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--items-file", "-ItemsFile", dest="items_file_option", default="")
    parser.add_argument("--position", "-Position", choices=["start", "end"], default="end")
    parser.add_argument("--before", "-Before", default="")
    parser.add_argument("--after", "-After", default="")
    parser.add_argument("--replace", "-Replace", action="store_true")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()
    path = args.path_option or args.path
    items_file = args.items_file_option or args.items_file
    if not path or not items_file:
        raise SystemExit("--path and --items-file are required.")
    argv = ["bulk-insert", path, items_file, "--position", args.position]
    if args.before:
        argv.extend(["--before", args.before])
    if args.after:
        argv.extend(["--after", args.after])
    if args.replace:
        argv.append("--replace")
    return run_module_main(document_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())

