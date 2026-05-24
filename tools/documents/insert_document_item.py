from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from document_wrapper_helpers import repo_root


def run_json_list_doc(arguments: list[str]) -> int:
    root = repo_root()
    sys.path.insert(0, str(root / "tools" / "json"))
    import json_list_doc  # type: ignore

    old_argv = sys.argv
    sys.argv = [str(root / "tools" / "json" / "json_list_doc.py"), *arguments]
    try:
        return int(json_list_doc.main() or 0)
    finally:
        sys.argv = old_argv


def position_arguments(position: str, before: str, after: str) -> list[str]:
    if before:
        return ["--position", "before", "--reference", before]
    if after:
        return ["--position", "after", "--reference", after]
    return ["--position", position]


def main() -> int:
    parser = argparse.ArgumentParser(description="Insert or replace a structured document item.")
    parser.add_argument("path", nargs="?")
    parser.add_argument("key", nargs="?")
    parser.add_argument("--path", "-Path", dest="path_option", default="")
    parser.add_argument("--key", "-Key", dest="key_option", default="")
    parser.add_argument("--title", "-Title", default="")
    parser.add_argument("--content", "-Content", default="")
    parser.add_argument("--content-file", "-ContentFile", default="")
    parser.add_argument("--item-file", "-ItemFile", default="")
    parser.add_argument("--position", "-Position", choices=["start", "end"], default="end")
    parser.add_argument("--before", "-Before", default="")
    parser.add_argument("--after", "-After", default="")
    parser.add_argument("--allow-empty", "-AllowEmpty", action="store_true")
    parser.add_argument("--replace", "-Replace", action="store_true")
    parser.add_argument("--no-post-edit", "-NoPostEdit", action="store_true", help="Accepted for legacy CLI parity; no post-edit hook is run by this entrypoint.")
    args = parser.parse_args()

    path = args.path_option or args.path
    key = args.key_option or args.key
    if not path or not key:
        raise SystemExit("--path and --key are required.")

    command = "set-entry" if args.replace else "insert-entry"
    argv = [command, path, key]
    if not args.replace:
        argv.extend(position_arguments(args.position, args.before, args.after))

    if args.item_file:
        argv.extend(["--value-json-file", args.item_file])
        return run_json_list_doc(argv)

    content = args.content
    if args.content_file:
        content = Path(args.content_file).read_text(encoding="utf-8")
    if not args.title and not content and not args.allow_empty:
        raise SystemExit("--title, --content, --content-file, --item-file, or --allow-empty is required.")

    payload: dict[str, str] = {}
    if args.title:
        payload["title"] = args.title
    if content or args.allow_empty:
        payload["content"] = content

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        temp_path = Path(handle.name)
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    try:
        argv.extend(["--value-json-file", str(temp_path)])
        return run_json_list_doc(argv)
    finally:
        temp_path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
