"""Aggregator report of the planning pipeline: renders findings.json as a short Polish UCE report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

RESEARCH_ID = "research"
CHECK_ID = "interpretation-check"
CONTRADICTION = "research-contradiction"
EXECUTORS = {
    "research-codex": "Codex, bo internet i podsumowania idą domyślnie do niego",
    "research-scout": "scout, bo szukanie w repo idzie do niego (albo Codex jest niedostępny)",
    "research-skipped": "nikt, bo Codex jest niedostępny, a scout nie ma internetu",
}


def skip_reason(reason: str) -> str:
    """Plain wording for a skip reason; never echoes script output, which may hold paths."""
    if reason.startswith("tool "):
        return "brak narzędzia " + reason.split()[1]
    if reason.startswith("select"):
        return "skrypt wyboru zawiódł"
    return "inny powód"


def research_lines(doc: dict, disabled: set[str]) -> list[str]:
    row = next((c for c in doc["checkers"] if c["id"] == RESEARCH_ID), None)
    if RESEARCH_ID in disabled:
        return ["🔒 Research pominięty: wyłączony w rejestrze"]
    if row is None:
        return ["🔒 Research pominięty: brak wpisu w rejestrze"]
    if row["status"] == "skipped":
        return [f"🔒 Research pominięty: {skip_reason(row.get('reason', ''))}"]
    found = [f for f in doc["findings"] if f["checker"] == RESEARCH_ID]
    if not found:
        return ["✅ Research pominięty: brak niewiadomych do rozstrzygnięcia faktami"]
    lines = [f"🔎 Research potrzebny: niewiadome do rozstrzygnięcia faktami: {len(found)}"]
    for category, why in EXECUTORS.items():
        count = sum(1 for f in found if f["category"] == category)
        if count:
            lines.append(f"▶️ Wykonawca: {why} (niewiadome: {count})")
    return lines


def check_lines(doc: dict, disabled: set[str]) -> list[str]:
    row = next((c for c in doc["checkers"] if c["id"] == CHECK_ID), None)
    if CHECK_ID in disabled:
        return ["🔒 Sprawdzenie pominięte: wyłączone w rejestrze"]
    if row is None:
        return ["🔒 Sprawdzenie pominięte: brak wpisu w rejestrze"]
    if row["status"] == "skipped":
        return [f"🔒 Sprawdzenie pominięte: {skip_reason(row.get('reason', ''))}"]
    open_ = [f for f in doc["findings"] if f["checker"] == CHECK_ID and f["status"] == "open"]
    contradictions = [f for f in open_ if f["category"] == CONTRADICTION]
    lines = []
    if contradictions:
        lines.append(f"⚠️ Research przeczy odpowiedzi właściciela: {len(contradictions)} (decyzja po stronie właściciela)")
    others = len(open_) - len(contradictions)
    if others:
        blockers = sum(1 for f in open_ if f["severity"] == "blocker")
        lines.append(f"⚠️ Niezgodności z intencją i sugestie: {others} (blokujące {blockers})")
    if not open_:
        lines.append("✅ Sprawdzenie: plan zgodny z odpowiedziami, bez uwag")
    return lines


def result_line(doc: dict, disabled: set[str]) -> str:
    open_ = [f for f in doc["findings"] if f["checker"] == CHECK_ID and f["status"] == "open"]
    if any(f["severity"] == "blocker" for f in open_):
        return "❌ Planowanie: są uwagi blokujące"
    if open_:
        return "⚠️ Planowanie: część uwag czeka na decyzję"
    return "🏁 Planowanie: plan zgodny z odpowiedziami, bez uwag"


def render(doc: dict, disabled: set[str] | frozenset[str] = frozenset()) -> str:
    disabled = set(disabled)
    lines = [result_line(doc, disabled)]
    lines += research_lines(doc, disabled)
    lines += check_lines(doc, disabled)
    skipped = [f"{c['id']} ({skip_reason(c.get('reason', ''))})" for c in doc["checkers"]
               if c["status"] == "skipped" and c["id"] not in (RESEARCH_ID, CHECK_ID)]
    if skipped:
        lines.append(f"🔒 Pominięte sprawdzacze projektu: {', '.join(skipped)}")
    calls = sum(c["model_calls"] for c in doc["checkers"])
    lines.append(f"💡 Koszt: {calls} wywołań modelu; raport tylko zgłasza, plan i SPEC.md bez zmian")
    if any(f["checker"] == CHECK_ID and f["status"] == "open" for f in doc["findings"]):
        lines.append("❓ Poprawić plan na podstawie uwag?")
    return "\n".join(lines)


def render_plan(plan: list[dict], disabled: list[str] | set[str] = ()) -> str:
    """Short dry-run summary: the research decision and the predicted model calls (no model was called)."""
    rows = {row["id"]: row for row in plan}
    lines = []
    research = rows.get(RESEARCH_ID)
    if RESEARCH_ID in disabled:
        lines.append("🔒 Research pominięty: wyłączony w rejestrze")
    elif research is None or research["status"] == "skipped":
        lines.append("🔒 Research pominięty: skrypt wyboru nie zadziałał")
    elif research["candidates"]:
        lines.append(f"🔎 Research potrzebny: niewiadome do rozstrzygnięcia faktami: {research['candidates']}")
    else:
        lines.append("✅ Research pominięty: brak niewiadomych do rozstrzygnięcia faktami")
    if CHECK_ID in disabled:
        lines.append("🔒 Sprawdzenie pominięte: wyłączone w rejestrze")
    else:
        lines.append(f"💡 Sprawdzenie: przewidywane wywołania modelu: {rows.get(CHECK_ID, {}).get('predicted_model_calls', 0)}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: report.py PATH_TO_FINDINGS_JSON", file=sys.stderr)
        return 2
    sys.stdout.reconfigure(encoding="utf-8")
    print(render(json.loads(Path(argv[0]).read_text(encoding="utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
