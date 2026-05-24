from __future__ import annotations

import argparse

import document_read_cache_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="List structured document keys.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--json", "-Json", action="store_true")
    args = parser.parse_args()
    path = args.path_option or args.path
    if not path:
        raise SystemExit("--path or positional path is required.")
    argv = ["keys", path]
    if args.json:
        argv.append("--json")
    return run_module_main(document_read_cache_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())
