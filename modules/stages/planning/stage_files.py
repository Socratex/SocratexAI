"""File names and slice assembly shared by the planning runner and the select scripts."""

from __future__ import annotations

ANSWERS = "answers.md"
PLAN = "plan.md"
RESEARCH = "research.md"
SLICE = "slice.md"

SLICE_HEADINGS = (("# Owner answers", ANSWERS), ("# Plan", PLAN), ("# Research notes", RESEARCH))


def build_slice(parts: dict[str, str]) -> str:
    """The only input of the check stage: owner answers, plan and optional research notes, never the conversation."""
    blocks = []
    for heading, name in SLICE_HEADINGS:
        text = parts.get(name)
        if text is not None:
            blocks.append(f"{heading}\n\n{text.strip()}\n")
    return "\n".join(blocks)
