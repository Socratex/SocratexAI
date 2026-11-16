#!/usr/bin/env python3
"""Claude Code Stop hook: check that the final reply follows the UCE shape (core/STYLE.md).

Deterministic checks only (no judgment calls):
  1. Every top-level line starts with an emoji (a bullet "- " followed by an emoji is fine).
  2. Indented sub-bullets, code blocks, tables and quotes are exempt.
  3. No line is longer than MAX_LINE characters (one thought per line).
On a violation the hook exits 2 once, so Claude rewrites the reply; the second stop is always allowed
(stop_hook_active), so it can never loop. Opt out with SOCRATEX_UCE=0.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

MAX_LINE = 220
EMOJI = re.compile("^[←-⯿\U0001F000-\U0001FAFF]")
BULLET = re.compile(r"^[-*]\s+")


def last_assistant_text(data: dict) -> str:
    direct = data.get("last_assistant_message")
    if isinstance(direct, str) and direct.strip():
        return direct
    path = data.get("transcript_path")
    if not path or not Path(path).exists():
        return ""
    text = ""
    for raw in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if entry.get("type") != "assistant":
            continue
        content = (entry.get("message") or {}).get("content")
        if isinstance(content, str):
            parts = [content]
        else:
            parts = [b.get("text", "") for b in content or [] if isinstance(b, dict) and b.get("type") == "text"]
        joined = "\n".join(p for p in parts if p.strip())
        if joined.strip():
            text = joined
    return text


def violations(text: str) -> list[str]:
    found: list[str] = []
    in_code = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith(("|", ">")):
            continue
        indented = line[:1] in (" ", "\t")
        if indented and BULLET.match(stripped):
            continue
        if len(stripped) > MAX_LINE:
            found.append(f"too long ({len(stripped)} chars): {stripped[:50]}...")
            continue
        body = BULLET.sub("", stripped, count=1)
        if not EMOJI.match(body):
            found.append(f"no emoji at start: {stripped[:50]}")
    return found


def main() -> int:
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    if os.environ.get("SOCRATEX_UCE") == "0":
        return 0
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0
    if data.get("stop_hook_active"):
        return 0
    found = violations(last_assistant_text(data))
    if not found:
        return 0
    shown = "; ".join(found[:3])
    sys.stderr.write(
        "UCE check failed (core/STYLE.md): every top-level line starts with an emoji, "
        f"one thought per line. Rewrite the reply once. Problems: {shown}\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
