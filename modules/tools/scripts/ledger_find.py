#!/usr/bin/env python3
"""`sox ledger find`: deterministic text search of docs/IMPROVEMENTS.json and the extension manifests.

Read-only: it never installs, enables or writes anything. Scoring per query word: a `keywords` hit weighs
KEYWORD_WEIGHT, a title hit TITLE_WEIGHT, a hit in what/area/manifest text 1. Matching is case-insensitive and
folds diacritics (Polish included). Items rejected in the ledger are skipped unless `include_rejected`.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "core"))

import extensions  # noqa: E402

KEYWORD_WEIGHT = 10
TITLE_WEIGHT = 4
TEXT_WEIGHT = 1
DEFAULT_LIMIT = 3
RESULT_MAX = 100


class QueryError(ValueError):
    """The query is empty or has fewer than two words."""


def fold(text: str) -> str:
    """Lower-case and strip diacritics (ł counts as l)."""
    text = text.lower().replace("ł", "l")
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


def words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", fold(text))


def _score(query: list[str], keywords: list[str], title: str, text: str) -> int:
    kw = [fold(k) for k in keywords]
    title_words, text_words = set(words(title)), set(words(text))
    total = 0
    for word in dict.fromkeys(query):
        if any(word == k or word in words(k) or (len(word) >= 4 and word in k) for k in kw):
            total += KEYWORD_WEIGHT
        elif word in title_words:
            total += TITLE_WEIGHT
        elif word in text_words:
            total += TEXT_WEIGHT
    return total


def _one_line(text: str) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= RESULT_MAX else text[: RESULT_MAX - 3] + "..."


def _candidates(root: Path | str | None, project: Path | str | None) -> list[dict]:
    data, _ = extensions._read_ledger(root)
    manifests = extensions.load_manifests(root)
    on = set(extensions.enabled_names(root, project))
    by_ledger = {m["ledger"]: m for m in manifests.values() if "ledger" in m}
    rows: list[dict] = []
    for it in data.get("items", []):
        man = by_ledger.get(it["id"])
        status = it.get("status", "considering")
        label = status
        if status == "adopted" and man:
            label = "adopted, on" if man["name"] in on else "adopted, off"
        text = " ".join(str(it.get(k, "")) for k in ("what", "area")) + (f" {man['name']} {man['when_to_use']}" if man else "")
        rows.append({"id": it["id"], "title": it.get("title", ""), "status": status, "status_label": label,
                     "result": _one_line(it.get("result") or it.get("expected_result") or it.get("what", "")),
                     "keywords": it.get("keywords", []), "text": text})
    for man in manifests.values():
        if "ledger" in man:
            continue
        status = man["status"]
        label = "considering" if status in ("recommended", "trial") else status
        if status == "adopted":
            label = "adopted, on" if man["name"] in on else "adopted, off"
        rows.append({"id": man["name"], "title": man["name"], "status": status, "status_label": label,
                     "result": _one_line(man["when_to_use"]), "keywords": [], "text": f"{man['name']} {man['when_to_use']} {man['category']}"})
    return rows


def find(query: str, root: Path | str | None = None, project: Path | str | None = None,
         include_rejected: bool = False, limit: int = DEFAULT_LIMIT) -> list[dict]:
    """Best matches, highest score first (ties: ledger ids before extension names, then id). Raises QueryError."""
    q = words(query)
    if len(q) < 2:
        raise QueryError("query needs at least two words, for example: sox ledger find \"control desktop app\"")
    hits = []
    for row in _candidates(root, project):
        if row["status"] == "rejected" and not include_rejected:
            continue
        score = _score(q, row["keywords"], row["title"], row["text"])
        if score > 0:
            hits.append({**row, "score": score})
    hits.sort(key=lambda h: (-h["score"], isinstance(h["id"], str), str(h["id"]).zfill(8)))
    return hits[: max(limit, 0)]


def format_line(hit: dict) -> str:
    return f"{hit['id']} | {hit['title']} | {hit['status_label']} | {hit['result']}"
