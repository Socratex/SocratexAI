from __future__ import annotations

import sys
from pathlib import Path

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from shared.cli_helpers import split_values as split_cli_values  # noqa: E402


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
    return split_cli_values(values, unique=False)


def add_bool_alias(parser, *flags: str, dest: str) -> None:
    parser.add_argument(*flags, action="store_true", dest=dest)
