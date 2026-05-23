from __future__ import annotations

import argparse

import document_item_edit_engine
from document_wrapper_helpers import run_module_main


def main() -> int:
    parser = argparse.ArgumentParser(description="Move or copy a structured item between document files.")
    parser.add_argument("source", nargs="?")
    parser.add_argument("target", nargs="?")
    parser.add_argument("key", nargs="?")
    parser.add_argument("--source", "-Source", dest="source_option", default="")
    parser.add_argument("--target", "-Target", dest="target_option", default="")
    parser.add_argument("--key", "-Key", dest="key_option", default="")
    parser.add_argument("--position", "-Position", choices=["start", "end"], default="end")
    parser.add_argument("--before", "-Before", default="")
    parser.add_argument("--after", "-After", default="")
    parser.add_argument("--keep-source", "-KeepSource", action="store_true")
    parser.add_argument("--replace", "-Replace", action="store_true")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()
    source = args.source_option or args.source
    target = args.target_option or args.target
    key = args.key_option or args.key
    if not source or not target or not key:
        raise SystemExit("--source, --target, and --key are required.")
    argv = ["migrate", source, target, key, "--position", args.position]
    if args.before:
        argv.extend(["--before", args.before])
    if args.after:
        argv.extend(["--after", args.after])
    if args.keep_source:
        argv.append("--keep-source")
    if args.replace:
        argv.append("--replace")
    return run_module_main(document_item_edit_engine, argv)


if __name__ == "__main__":
    raise SystemExit(main())

