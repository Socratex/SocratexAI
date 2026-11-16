from __future__ import annotations

import argparse

import document_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Move a structured document item.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("key", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--key", "-Key", dest="key_option", default="")
    parser.add_argument("--position", "-Position", choices=["start", "end"], default="end")
    parser.add_argument("--before", "-Before", default="")
    parser.add_argument("--after", "-After", default="")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()
    path = args.path_option or args.path
    key = args.key_option or args.key
    if not path or not key:
        raise SystemExit("--path and --key are required.")
    argv = ["move", path, key, "--position", args.position]
    if args.before:
        argv.extend(["--before", args.before])
    if args.after:
        argv.extend(["--after", args.after])
    return run_module_main(document_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())
