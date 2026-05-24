#!/usr/bin/env python3
"""Select compiled knowledge entries from the JSON file fallback."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_select  # noqa: E402


def main() -> int:
    if "--file-fallback" not in sys.argv:
        sys.argv.append("--file-fallback")
    return knowledge_select.main()


if __name__ == "__main__":
    raise SystemExit(main())
