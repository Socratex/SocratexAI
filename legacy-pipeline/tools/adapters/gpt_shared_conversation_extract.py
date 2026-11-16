#!/usr/bin/env python3
"""Extract visible user/assistant messages from a public ChatGPT share page."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from adapters.gpt_conversation_core import (  # noqa: E402
    ConversationExtractionError,
    build_payload,
    extract_messages,
    find_conversation_data,
    hydrate_flat_payload,
    render_markdown,
    write_output,
)
from shared.cli_helpers import configure_stdio  # noqa: E402


STREAM_ENQUEUE_RE = re.compile(r"streamController\.enqueue\((\"(?:\\.|[^\"\\])*\")\)")
DEFAULT_USER_AGENT = "Mozilla/5.0 SocratexAI-GPT-Share-Extractor/1.0"


def fetch_html(url: str, timeout_seconds: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, "replace")


def read_source(args: argparse.Namespace) -> tuple[str, str]:
    if args.url:
        return fetch_html(args.url, args.timeout), args.url
    path = Path(args.input_file).resolve()
    return path.read_text(encoding="utf-8"), str(path)


def stream_payloads(html: str) -> list[str]:
    payloads: list[str] = []
    for match in STREAM_ENQUEUE_RE.finditer(html):
        try:
            payloads.append(json.loads(match.group(1)))
        except json.JSONDecodeError:
            continue
    if not payloads:
        raise ConversationExtractionError("No React Router stream payloads found in the page.")
    return payloads


def flat_payload_from_stream(payloads: list[str]) -> list[Any]:
    buffer = ""
    collecting = False
    for payload in payloads:
        stripped = payload.lstrip()
        if not collecting and not stripped.startswith("["):
            continue
        collecting = True
        buffer += payload
        try:
            value = json.loads(buffer)
        except json.JSONDecodeError:
            continue
        if not isinstance(value, list):
            raise ConversationExtractionError("Decoded stream payload is not a flat React Router list.")
        return value
    raise ConversationExtractionError("Could not decode the shared conversation data payload.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url_positional", nargs="?", help="Public https://chatgpt.com/share/... URL.")
    parser.add_argument("--url", "-Url", default="", help="Public https://chatgpt.com/share/... URL.")
    parser.add_argument("--input-file", "-InputFile", default="", help="Saved ChatGPT share HTML file.")
    parser.add_argument("--output", "-Output", default="", help="Write extracted conversation to this file.")
    parser.add_argument("--format", "-Format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--timeout", "-Timeout", type=int, default=30)
    parser.add_argument("--no-metadata", "-NoMetadata", action="store_true")
    parser.add_argument("--include-technical-user-messages", "-IncludeTechnicalUserMessages", action="store_true")
    parser.add_argument("--assistant-mode", "-AssistantMode", choices=["final", "all"], default="final", help="Use final to keep only the last assistant message per user turn; all keeps intermediate assistant status messages.")
    args = parser.parse_args()
    if args.url_positional:
        if args.url:
            parser.error("Use either positional URL or --url, not both.")
        args.url = args.url_positional
    if bool(args.url) == bool(args.input_file):
        parser.error("Use exactly one source: positional URL/--url or --input-file.")
    return args


def main() -> int:
    configure_stdio()
    try:
        args = parse_args()
        html, source = read_source(args)
        flat_payload = flat_payload_from_stream(stream_payloads(html))
        conversation = find_conversation_data(hydrate_flat_payload(flat_payload))
        messages, skipped = extract_messages(conversation, args.include_technical_user_messages, args.assistant_mode)
        payload = build_payload(source, conversation, messages, skipped)
        if args.format == "json":
            output = json.dumps(payload, ensure_ascii=False, indent=4) + "\n"
        else:
            output = render_markdown(payload, include_metadata=not args.no_metadata)
        write_output(output, args.output)
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
