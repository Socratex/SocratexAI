#!/usr/bin/env python3
"""List, search, index, and read local ChatGPT conversation exports/caches."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

_TOOLS_ROOT = Path(__file__).resolve().parents[1]
if str(_TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(_TOOLS_ROOT))

from adapters.gpt_conversation_core import (  # noqa: E402
    build_payload,
    extract_messages,
    render_markdown,
    timestamp_now,
    write_output,
)
from shared.cli_helpers import configure_stdio  # noqa: E402


class ArchiveError(RuntimeError):
    """Raised when a local ChatGPT archive operation cannot be completed."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_source(path_text: str) -> Path:
    path = Path(path_text).expanduser().resolve()
    if not path.exists():
        raise ArchiveError(f"Source does not exist: {path}")
    if path.is_dir():
        preferred = path / "conversations.json"
        if preferred.is_file():
            return preferred
        candidates = sorted(path.glob("*.json"))
        if len(candidates) == 1:
            return candidates[0]
        raise ArchiveError("Directory source must contain conversations.json or exactly one .json file.")
    return path


def raw_conversations(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if isinstance(value.get("conversations"), list):
            return [item for item in value["conversations"] if isinstance(item, dict)]
        if isinstance(value.get("messages"), list):
            return [value]
        if isinstance(value.get("mapping"), dict) or isinstance(value.get("linear_conversation"), list):
            return [value]
    raise ArchiveError("Unsupported archive JSON shape. Expected ChatGPT conversations.json, generated archive JSON, or one conversation object.")


def simple_metadata(conversation: dict[str, Any]) -> dict[str, str]:
    keys = [
        "id",
        "conversation_id",
        "title",
        "create_time",
        "update_time",
        "project_id",
        "project_name",
        "project_title",
        "workspace_id",
    ]
    result: dict[str, str] = {}
    for key in keys:
        value = conversation.get(key)
        if isinstance(value, (str, int, float)):
            result[key] = str(value)
    project = conversation.get("project")
    if isinstance(project, dict):
        for key in ("id", "name", "title"):
            value = project.get(key)
            if isinstance(value, (str, int, float)):
                result[f"project_{key}"] = str(value)
    elif isinstance(project, str):
        result["project"] = project
    return result


def normalize_conversation(conversation: dict[str, Any], source: str, position: int, assistant_mode: str) -> dict[str, Any]:
    if isinstance(conversation.get("messages"), list):
        messages = [message for message in conversation["messages"] if isinstance(message, dict)]
        skipped = Counter(conversation.get("skipped_by_kind", {}))
        payload = dict(conversation)
        payload.setdefault("source", source)
        payload.setdefault("conversation_id", conversation.get("conversation_id") or conversation.get("id") or f"conversation-{position}")
        payload.setdefault("title", conversation.get("title") or "")
        payload.setdefault("message_count", len(messages))
        payload["messages"] = messages
    else:
        messages, skipped = extract_messages(conversation, assistant_mode=assistant_mode)
        payload = build_payload(source, conversation, messages, skipped)
        payload["conversation_id"] = payload.get("conversation_id") or conversation.get("id") or f"conversation-{position}"
    payload["archive_position"] = position
    payload["metadata"] = simple_metadata(conversation)
    payload["search_text"] = searchable_text(payload)
    return payload


def load_archive(source_text: str, assistant_mode: str = "final") -> list[dict[str, Any]]:
    source_path = resolve_source(source_text)
    raw = raw_conversations(load_json(source_path))
    return [normalize_conversation(item, str(source_path), index, assistant_mode) for index, item in enumerate(raw, start=1)]


def searchable_text(payload: dict[str, Any]) -> str:
    parts = [str(payload.get("title", "")), json.dumps(payload.get("metadata", {}), ensure_ascii=False)]
    for message in payload.get("messages", []):
        if isinstance(message, dict):
            parts.append(str(message.get("text", "")))
    return "\n".join(parts).lower()


def terms(query: str) -> list[str]:
    return [part.lower() for part in re.findall(r"\S+", query) if part.strip()]


def matches(payload: dict[str, Any], query: str, any_term: bool, project: str) -> bool:
    text = payload.get("search_text") or searchable_text(payload)
    if project and project.lower() not in text:
        return False
    query_terms = terms(query)
    if not query_terms:
        return True
    if any_term:
        return any(term in text for term in query_terms)
    return all(term in text for term in query_terms)


def display_text(payload: dict[str, Any]) -> str:
    parts = [str(payload.get("title", ""))]
    for message in payload.get("messages", []):
        if isinstance(message, dict):
            parts.append(str(message.get("text", "")))
    return "\n".join(parts).lower()


def snippet(payload: dict[str, Any], query: str, max_chars: int) -> str:
    text = display_text(payload)
    query_terms = terms(query)
    start = 0
    for term in query_terms:
        index = text.find(term)
        if index >= 0:
            start = max(0, index - max_chars // 4)
            break
    value = " ".join(text[start:start + max_chars].split())
    return value


def summarize(payload: dict[str, Any], query: str = "", max_snippet_chars: int = 220) -> dict[str, Any]:
    messages = payload.get("messages", [])
    return {
        "conversation_id": payload.get("conversation_id", ""),
        "archive_position": payload.get("archive_position"),
        "title": payload.get("title", ""),
        "create_time": payload.get("create_time"),
        "update_time": payload.get("update_time"),
        "message_count": len(messages),
        "role_counts": payload.get("role_counts", {}),
        "metadata": payload.get("metadata", {}),
        "snippet": snippet(payload, query, max_snippet_chars) if query else "",
    }


def output_records(records: list[dict[str, Any]], output_format: str, output_path: str) -> None:
    if output_format == "json":
        write_output(json.dumps(records, ensure_ascii=False, indent=4) + "\n", output_path)
        return
    lines: list[str] = []
    for index, record in enumerate(records, start=1):
        title = record.get("title") or "Untitled"
        cid = record.get("conversation_id") or record.get("archive_position")
        lines.append(f"{index}. {title} [{cid}] messages={record.get('message_count', 0)}")
        if record.get("snippet"):
            lines.append(f"   {record['snippet']}")
    write_output("\n".join(lines).rstrip() + "\n", output_path)


def command_list(args: argparse.Namespace) -> int:
    conversations = load_archive(args.source, args.assistant_mode)
    records = [summarize(item) for item in conversations[: args.limit]]
    output_records(records, args.format, args.output)
    return 0


def command_search(args: argparse.Namespace) -> int:
    conversations = load_archive(args.source, args.assistant_mode)
    matched = [item for item in conversations if matches(item, args.query, args.any_term, args.project)]
    records = [summarize(item, args.query, args.max_snippet_chars) for item in matched[: args.limit]]
    output_records(records, args.format, args.output)
    return 0


def select_conversation(conversations: list[dict[str, Any]], args: argparse.Namespace) -> dict[str, Any]:
    if args.conversation_id:
        for item in conversations:
            if str(item.get("conversation_id")) == args.conversation_id:
                return item
        raise ArchiveError(f"Conversation id not found: {args.conversation_id}")
    if args.position:
        for item in conversations:
            if int(item.get("archive_position", -1)) == args.position:
                return item
        raise ArchiveError(f"Conversation position not found: {args.position}")
    if args.title_contains:
        value = args.title_contains.lower()
        found = [item for item in conversations if value in str(item.get("title", "")).lower()]
        if len(found) == 1:
            return found[0]
        if not found:
            raise ArchiveError(f"No conversation title contains: {args.title_contains}")
        raise ArchiveError(f"Title selector matched {len(found)} conversations; use --conversation-id or --position.")
    raise ArchiveError("Use --conversation-id, --position, or --title-contains.")


def command_read(args: argparse.Namespace) -> int:
    conversations = load_archive(args.source, args.assistant_mode)
    payload = select_conversation(conversations, args)
    payload = dict(payload)
    payload.pop("search_text", None)
    if args.format == "json":
        output = json.dumps(payload, ensure_ascii=False, indent=4) + "\n"
    else:
        output = render_markdown(payload, include_metadata=not args.no_metadata)
    write_output(output, args.output)
    return 0


def command_index(args: argparse.Namespace) -> int:
    conversations = load_archive(args.source, args.assistant_mode)
    payload = {
        "source": str(resolve_source(args.source)),
        "indexed_at": timestamp_now(),
        "conversation_count": len(conversations),
        "conversations": [
            {key: value for key, value in conversation.items() if key != "search_text"}
            for conversation in conversations
        ],
    }
    write_output(json.dumps(payload, ensure_ascii=False, indent=4) + "\n", args.output)
    return 0


def add_common_source(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", "-Source", required=True, help="ChatGPT conversations.json, generated archive JSON, or a directory containing conversations.json.")
    parser.add_argument("--output", "-Output", default="", help="Write output to this file.")
    parser.add_argument("--assistant-mode", "-AssistantMode", choices=["final", "all"], default="final", help="Use final to keep only the last assistant message per user turn; all keeps intermediate assistant status messages.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="List local archive conversations.")
    add_common_source(list_parser)
    list_parser.add_argument("--limit", "-Limit", type=int, default=50)
    list_parser.add_argument("--format", "-Format", choices=["text", "json"], default="text")
    list_parser.set_defaults(func=command_list)

    search_parser = subparsers.add_parser("search", help="Search local archive conversations.")
    add_common_source(search_parser)
    search_parser.add_argument("--query", "-Query", required=True)
    search_parser.add_argument("--project", "-Project", default="", help="Optional project metadata/title/content filter.")
    search_parser.add_argument("--limit", "-Limit", type=int, default=20)
    search_parser.add_argument("--any-term", "-AnyTerm", action="store_true")
    search_parser.add_argument("--max-snippet-chars", "-MaxSnippetChars", type=int, default=220)
    search_parser.add_argument("--format", "-Format", choices=["text", "json"], default="text")
    search_parser.set_defaults(func=command_search)

    read_parser = subparsers.add_parser("read", help="Read one conversation as Markdown or JSON.")
    add_common_source(read_parser)
    read_parser.add_argument("--conversation-id", "-ConversationId", default="")
    read_parser.add_argument("--position", "-Position", type=int, default=0)
    read_parser.add_argument("--title-contains", "-TitleContains", default="")
    read_parser.add_argument("--format", "-Format", choices=["markdown", "json"], default="markdown")
    read_parser.add_argument("--no-metadata", "-NoMetadata", action="store_true")
    read_parser.set_defaults(func=command_read)

    index_parser = subparsers.add_parser("index", help="Normalize a local archive into reusable extracted JSON.")
    add_common_source(index_parser)
    index_parser.set_defaults(func=command_index)
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    try:
        args = parse_args()
        return int(args.func(args))
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
