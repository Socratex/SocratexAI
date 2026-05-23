from __future__ import annotations

import argparse
import sys

from utf8_file_helpers import write_utf8_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Write a file as UTF-8 without BOM.")
    parser.add_argument("--path", required=True, help="Target file path.")
    parser.add_argument(
        "--value",
        action="append",
        help="Text value to write. May be repeated; when omitted, stdin is used.",
    )
    parser.add_argument("--no-newline", action="store_true", help="Do not append a final newline.")
    parser.add_argument("--line-ending", choices=["Preserve", "LF", "CRLF"], default="LF")
    args = parser.parse_args()

    value = args.value if args.value is not None else sys.stdin.read()
    write_utf8_file(args.path, value, no_newline=args.no_newline, line_ending=args.line_ending)
    print(f"OK: wrote UTF-8 file {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
