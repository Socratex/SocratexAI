#!/usr/bin/env python3
"""Query compiled knowledge entries from SQLite."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import knowledge_select  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(knowledge_select.main())
