from __future__ import annotations

import argparse

import document_read_cache_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Read a structured document item or selector.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("selector", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--selector", "-Selector", dest="selector_option", default="")
    parser.add_argument("--json", "-Json", action="store_true")
    args = parser.parse_args()
    path = args.path_option or args.path
    selector = args.selector_option or args.selector
    if not path or not selector:
        raise SystemExit("--path and --selector are required.")
    argv = ["read", path, selector]
    if args.json:
        argv.append("--json")
    return run_module_main(document_read_cache_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())
