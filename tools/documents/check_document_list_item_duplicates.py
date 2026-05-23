from __future__ import annotations

import argparse

import document_list_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Check duplicate list lines or review candidate document items.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--key", "-Key", default="")
    parser.add_argument("--scope", "-Scope", choices=["item", "document"], default="document")
    parser.add_argument("--text", "-Text", default="")
    parser.add_argument("--url", "-Url", default="")
    parser.add_argument("--terms", "-Terms", nargs="*", default=[])
    parser.add_argument("--limit", "-Limit", type=int, default=12)
    parser.add_argument("--json", "-Json", action="store_true")
    parser.add_argument("--fail-on-duplicate", "-FailOnDuplicate", action="store_true")
    args = parser.parse_args()
    path = args.path_option or args.path
    if not path:
        raise SystemExit("--path or positional path is required.")
    argv = ["check", path, "--scope", args.scope]
    if args.key:
        argv.extend(["--key", args.key])
    if args.text:
        argv.extend(["--text", args.text])
    if args.url:
        argv.extend(["--url", args.url])
    if args.terms:
        argv.extend(["--terms", *args.terms])
    if args.limit != 12:
        argv.extend(["--limit", str(args.limit)])
    if args.json:
        argv.append("--json")
    if args.fail_on_duplicate:
        argv.append("--fail-on-duplicate")
    return run_module_main(document_list_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())

