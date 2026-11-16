"""Six-state AUTO eligibility and optional prompt relevance, independent of transport."""

from __future__ import annotations

import re


STATUSES = ("test", "progress", "todo", "open", "done", "other")
EXECUTABLE = {"todo", "progress"}
LEGACY = {"ready": "todo", "awaiting_input": "test", "undecided": "open"}


def projection_context(entry: dict) -> str:
    # Old grants stored their human topic only in scope. Never broaden them when
    # switching from a hand-curated list to generated source candidates.
    value = entry.get("prompt_context", entry.get("scope", ""))
    if not isinstance(value, str):
        raise ValueError("Prompt context must be text")
    return value


def status(value: object, *, legacy: bool = False) -> str:
    if not isinstance(value, str):
        raise ValueError("Task status must be one of test/progress/todo/open/done/other")
    normalized = value.casefold()
    if legacy:
        normalized = LEGACY.get(normalized, normalized)
    if normalized not in STATUSES:
        raise ValueError("Invalid task status; use test/progress/todo/open/done/other")
    return normalized


def matches_context(task: dict, context: str) -> bool:
    if not context.strip():
        return True
    assessed = task.get("context_assessment")
    if assessed is not None:
        if (not isinstance(assessed, dict) or assessed.get("context") != context
                or type(assessed.get("matches")) is not bool
                or not isinstance(assessed.get("reason"), str) or not assessed["reason"].strip()):
            raise ValueError("Semantic context assessment requires the exact prompt context, matches boolean and reason")
        return assessed["matches"]
    # A literal helper is useful for keywords; the agent assesses whole natural-language prompts.
    terms = re.findall(r"[\w.-]+", context.casefold())
    values = [task.get(field, "") for field in ("id", "display_id", "module", "description", "steps", "comments", "plan", "title")]
    text = " ".join(str(value) for value in values).casefold()
    return bool(terms) and all(term in text for term in terms)


def unpack_projection(entry: dict, projection: list[dict] | dict) -> tuple[list[dict], str]:
    context = entry.get("prompt_context", "")
    if not isinstance(context, str):
        raise ValueError("Prompt context must be text")
    if isinstance(projection, dict):
        context = projection_context(entry)
        if projection.get("schema_version") != 2 or not isinstance(projection.get("tasks"), list):
            raise ValueError("Unsupported AUTO task projection envelope")
        if projection.get("prompt_context", "") != context:
            raise ValueError("Task projection prompt context is stale")
        from .projection import validate_copy_evidence
        validate_copy_evidence(entry, projection.get("workspace_evidence"))
        return projection["tasks"], context
    if not isinstance(projection, list):
        raise ValueError("Task projection must be an array or a version2 envelope")
    return projection, context
