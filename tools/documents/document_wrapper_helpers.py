from __future__ import annotations

import sys
from pathlib import Path


def repo_root(start: Path | None = None) -> Path:
    current = (start or Path(__file__)).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / "SCRIPTS.json").is_file() and (candidate / "tools").is_dir():
            return candidate
    return Path(__file__).resolve().parents[2]


def run_module_main(module: object, argv: list[str]) -> int:
    old_argv = sys.argv
    sys.argv = [getattr(module, "__file__", module.__class__.__name__), *argv]
    try:
        result = module.main()
        return int(result or 0)
    finally:
        sys.argv = old_argv


def split_values(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        for part in value.split(","):
            trimmed = part.strip()
            if trimmed:
                result.append(trimmed)
    return result


def add_bool_alias(parser, *flags: str, dest: str) -> None:
    parser.add_argument(*flags, action="store_true", dest=dest)

