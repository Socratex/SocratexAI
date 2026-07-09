#!/usr/bin/env python3
"""Thin adapter entrypoint for local ChatGPT conversation archive search/read."""

from __future__ import annotations

import runpy
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "adapters" / "gpt_conversation_archive.py"


if __name__ == "__main__":
    runpy.run_path(str(SCRIPT), run_name="__main__")
