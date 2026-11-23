"""Select for the research stage: find unknowns that facts can settle, pick the executor and record why.

Deterministic, no model. Each candidate is one unknown; its category names the executor (research-codex,
research-scout) or says the research was skipped (research-skipped). No candidates means research is not needed.
Executors follow defaults/ROUTING.json: internet and summaries go to Codex, repo search goes to scout; when Codex is
unavailable, summaries and repo search use scout and internet research is skipped with a note (scout has no web access).
Codex availability: PLANNING_CODEX_AVAILABLE=0|1 overrides the check for the `codex` command.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
# Import with the shared engine folder and this folder first, then take them off again so importing this
# module in-process never shadows same-named modules of the review pipeline.
_added = [str(q) for q in (HERE, HERE.parents[1] / "engine") if str(q) not in sys.path]
sys.path[:0] = _added
try:
    import selectlib  # noqa: E402
    import stage_files  # noqa: E402
finally:
    for _path in _added:
        sys.path.remove(_path)

ROUTING = HERE.parents[2] / "defaults" / "ROUTING.json"
CODEX_ENV = "PLANNING_CODEX_AVAILABLE"
UNKNOWN = re.compile(r"\b(unknown|tbd|to verify|to check|need to check|needs checking|not sure|unclear|find out)\b"
                     r"|niewiadom|do sprawdzenia|nie wiadomo|do ustalenia|sprawdzi[cć]|niejasn|\?\s*$",
                     re.IGNORECASE)
INTERNET = re.compile(r"https?://|\b(docs?|documentation|api|version|library|package|release|pricing|price|online|internet|web)\b"
                      r"|dokumentac|wersj|bibliotek|cennik", re.IGNORECASE)
REPO = re.compile(r"\b\w[\w./-]*\.(py|js|ts|cs|json|md|toml|yml|yaml)\b|\b(repo|repository|codebase|function|module|class|file)\b"
                  r"|\bplik|\bkod\b|funkcj|moduł|repozytori", re.IGNORECASE)
SUMMARY = re.compile(r"\b(summar\w+|compare|comparison|overview|notes)\b|podsumuj|porównaj|przegląd", re.IGNORECASE)


def codex_available() -> bool:
    forced = os.environ.get(CODEX_ENV)
    if forced in ("0", "1"):
        return forced == "1"
    return shutil.which("codex") is not None


def routing_executors() -> dict[str, str]:
    """Executor ids from defaults/ROUTING.json: the Codex family and the cheap Claude agent used for search."""
    routing = json.loads(ROUTING.read_text(encoding="utf-8"))
    scout = next(name for name, tier in routing["claude_agents"].items() if tier == "cheap")
    codex = "codex" if "codex" in routing else ""
    return {"codex": codex, "scout": scout}


def classify(text: str) -> str | None:
    """Kind of fact that would settle the unknown, or None when it is an owner decision rather than a fact."""
    if REPO.search(text):
        return "repo"
    if INTERNET.search(text):
        return "internet"
    if SUMMARY.search(text):
        return "summary"
    return None


def choose(kind: str, codex_ok: bool) -> tuple[str, str]:
    """(executor category, reason) for one kind of unknown, following the routing defaults."""
    if kind == "repo":
        return "research-scout", "repo search goes to scout (cheap, read-only)"
    if codex_ok:
        why = "internet research" if kind == "internet" else "summaries"
        return "research-codex", f"{why} go to Codex by default"
    if kind == "summary":
        return "research-scout", "Codex unavailable, summaries fall back to scout"
    return "research-skipped", "Codex unavailable and scout has no web access, internet research skipped"


def clip(text: str, limit: int = 100) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def main() -> None:
    request = selectlib.load_request()
    executors = routing_executors()
    codex_ok = codex_available() and bool(executors["codex"])
    rows = []
    for rel in selectlib.files_of(request):
        if rel not in (stage_files.ANSWERS, stage_files.PLAN):
            continue
        for number, line in enumerate(selectlib.read_lines(request, rel), 1):
            if not UNKNOWN.search(line) or not selectlib.overlaps(request["chunks"], rel, number, number):
                continue
            kind = classify(line)
            if kind is None:
                continue
            category, reason = choose(kind, codex_ok)
            executor = {"research-codex": "codex", "research-scout": executors["scout"], "research-skipped": "none"}[category]
            rows.append(selectlib.candidate(rel, number, number, category,
                                            f"Unknown ({kind}): {clip(line)} | executor: {executor} | reason: {reason}",
                                            severity="minor", confidence="high"))
    selectlib.emit(rows)


if __name__ == "__main__":
    main()
