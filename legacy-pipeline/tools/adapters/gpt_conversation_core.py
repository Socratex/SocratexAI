#!/usr/bin/env python3
"""Shared extraction/rendering helpers for ChatGPT conversation tools."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TECHNICAL_USER_MESSAGES = {"Original custom instructions no longer available"}


class ConversationExtractionError(RuntimeError):
    """Raised when ChatGPT conversation data cannot be decoded."""


def hydrate_flat_payload(flat: list[Any]) -> Any:
    sys.setrecursionlimit(max(20000, len(flat) * 4))
    seen: dict[int, Any] = {}

    def hydrate(value: Any) -> Any:
        if isinstance(value, int):
            if value < 0:
                return None
            if value in seen:
                return seen[value]
            if value >= len(flat):
                return value
            raw = flat[value]
            if isinstance(raw, dict):
                result: dict[Any, Any] = {}
                seen[value] = result
                for key, child in raw.items():
                    resolved_key: Any = key
                    if isinstance(key, str) and key.startswith("_") and key[1:].isdigit():
                        resolved_key = hydrate(int(key[1:]))
                    result[resolved_key] = hydrate(child)
                return result
            if isinstance(raw, list):
                result_list: list[Any] = []
                seen[value] = result_list
                result_list.extend(hydrate(item) for item in raw)
                return result_list
            return raw
        if isinstance(value, list):
            return [hydrate(item) for item in value]
        if isinstance(value, dict):
            return {key: hydrate(child) for key, child in value.items()}
        return value

    return hydrate(0)


def is_conversation_data(value: Any) -> bool:
    return isinstance(value, dict) and (
        isinstance(value.get("linear_conversation"), list)
        or isinstance(value.get("mapping"), dict)
    )


def find_conversation_data(root: Any) -> dict[str, Any]:
    if not isinstance(root, dict):
        raise ConversationExtractionError("Decoded conversation root is not an object.")
    loader_data = root.get("loaderData")
    if isinstance(loader_data, dict):
        for route_data in loader_data.values():
            if not isinstance(route_data, dict):
                continue
            server_response = route_data.get("serverResponse")
            data = server_response.get("data") if isinstance(server_response, dict) else None
            if is_conversation_data(data):
                return data
    found = find_conversation_data_recursive(root)
    if found is None:
        raise ConversationExtractionError("Could not find conversation data in decoded payload.")
    return found


def find_conversation_data_recursive(value: Any) -> dict[str, Any] | None:
    if is_conversation_data(value):
        return value
    if isinstance(value, dict):
        for child in value.values():
            found = find_conversation_data_recursive(child)
            if found is not None:
                return found
    if isinstance(value, list):
        for child in value:
            found = find_conversation_data_recursive(child)
            if found is not None:
                return found
    return None


def content_text(content: Any) -> str:
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if not isinstance(parts, list):
        return ""
    rendered_parts: list[str] = []
    for part in parts:
        if isinstance(part, str):
            rendered_parts.append(part)
        elif isinstance(part, dict):
            if isinstance(part.get("text"), str):
                rendered_parts.append(part["text"])
            else:
                rendered_parts.append(json.dumps(part, ensure_ascii=False, indent=2))
        elif part is not None:
            rendered_parts.append(str(part))
    return "\n\n".join(item for item in rendered_parts if item is not None).strip()


def message_from_linear_item(item: Any) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None
    message = item.get("message")
    if isinstance(message, dict):
        return message
    if "author" in item and "content" in item:
        return item
    return None


def ordered_mapping_items(conversation: dict[str, Any]) -> list[Any]:
    mapping = conversation.get("mapping")
    if not isinstance(mapping, dict):
        return []
    current_node = conversation.get("current_node")
    if isinstance(current_node, str) and current_node in mapping:
        chain: list[Any] = []
        seen: set[str] = set()
        node_id: str | None = current_node
        while node_id and node_id in mapping and node_id not in seen:
            seen.add(node_id)
            node = mapping[node_id]
            chain.append(node)
            parent = node.get("parent") if isinstance(node, dict) else None
            node_id = parent if isinstance(parent, str) else None
        return list(reversed(chain))
    return list(mapping.values())


def visible_text_message(message: dict[str, Any], include_technical_user_messages: bool) -> dict[str, Any] | None:
    author = message.get("author")
    role = author.get("role") if isinstance(author, dict) else None
    if role not in {"user", "assistant"}:
        return None
    content = message.get("content")
    if not isinstance(content, dict):
        return None
    content_type = content.get("content_type")
    if content_type not in {"text", "multimodal_text"}:
        return None
    text = content_text(content)
    if not text:
        return None
    if not include_technical_user_messages and role == "user" and text in TECHNICAL_USER_MESSAGES:
        return None
    return {
        "id": message.get("id", ""),
        "role": role,
        "content_type": content_type,
        "create_time": message.get("create_time"),
        "text": text,
    }


def collapse_assistant_turns(messages: list[dict[str, Any]], mode: str) -> tuple[list[dict[str, Any]], int]:
    if mode == "all":
        return messages, 0
    if mode != "final":
        raise ConversationExtractionError("assistant_mode must be 'final' or 'all'.")
    collapsed: list[dict[str, Any]] = []
    pending_assistant: list[dict[str, Any]] = []
    dropped = 0

    def flush_assistant() -> None:
        nonlocal dropped
        if not pending_assistant:
            return
        collapsed.append(pending_assistant[-1])
        dropped += max(0, len(pending_assistant) - 1)
        pending_assistant.clear()

    for message in messages:
        if message.get("role") == "assistant":
            pending_assistant.append(message)
            continue
        flush_assistant()
        collapsed.append(message)
    flush_assistant()
    return collapsed, dropped


def extract_messages(
    conversation: dict[str, Any],
    include_technical_user_messages: bool = False,
    assistant_mode: str = "final",
) -> tuple[list[dict[str, Any]], Counter[str]]:
    messages: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    linear = conversation.get("linear_conversation")
    items = linear if isinstance(linear, list) else ordered_mapping_items(conversation)

    for item in items:
        message = message_from_linear_item(item)
        if not message:
            skipped["non_message"] += 1
            continue
        extracted = visible_text_message(message, include_technical_user_messages)
        if extracted is None:
            author = message.get("author") if isinstance(message.get("author"), dict) else {}
            skipped[str(author.get("role", "unknown"))] += 1
            continue
        messages.append(extracted)
    messages, dropped_assistant_intermediate = collapse_assistant_turns(messages, assistant_mode)
    if dropped_assistant_intermediate:
        skipped["assistant_intermediate"] += dropped_assistant_intermediate
    return messages, skipped


def role_label(role: str) -> str:
    return {"user": "User", "assistant": "Assistant"}.get(role, role.title() or "Message")


def timestamp_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_payload(source: str, conversation: dict[str, Any], messages: list[dict[str, Any]], skipped: Counter[str]) -> dict[str, Any]:
    role_counts = Counter(str(message["role"]) for message in messages)
    return {
        "title": conversation.get("title") or "",
        "conversation_id": conversation.get("conversation_id") or conversation.get("id") or "",
        "create_time": conversation.get("create_time"),
        "update_time": conversation.get("update_time"),
        "source": source,
        "extracted_at": timestamp_now(),
        "message_count": len(messages),
        "role_counts": dict(sorted(role_counts.items())),
        "skipped_total": sum(skipped.values()),
        "skipped_by_kind": dict(sorted(skipped.items())),
        "messages": messages,
    }


def render_markdown(payload: dict[str, Any], include_metadata: bool = True) -> str:
    lines: list[str] = []
    title = payload.get("title") or "ChatGPT Conversation"
    messages = payload["messages"]
    if include_metadata:
        lines.extend(
            [
                f"# {title}",
                "",
                f"- Source: {payload.get('source', '')}",
                f"- Extracted at: {payload.get('extracted_at', '')}",
                f"- Visible messages: {len(messages)}",
                f"- Skipped technical entries: {payload.get('skipped_total', 0)}",
                "",
            ]
        )
    for index, message in enumerate(messages, start=1):
        lines.append(f"## {index}. {role_label(str(message['role']))}")
        lines.append("")
        lines.append(str(message["text"]).rstrip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_output(value: str, output_path: str) -> None:
    if output_path:
        Path(output_path).resolve().write_text(value, encoding="utf-8", newline="\n")
        return
    print(value, end="")
