"""Aggregator report: renders findings.json as a short Polish UCE report (result line, emoji bullets, one question)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

CHECKER_NAMES = {"readability": "czytelność", "architecture": "architektura", "test-necessity": "zasadność testów",
                 "comments": "komentarze", "contracts": "kontrakty", "leaks": "wycieki"}


def count(findings: list[dict], status: str, severity: str | None = None) -> int:
    return sum(1 for f in findings if f["status"] == status and (severity is None or f["severity"] == severity))


def skip_reason(reason: str) -> str:
    """Plain wording for a skip reason; never echoes script output, which may hold paths."""
    if reason.startswith("tool "):
        return "brak narzędzia " + reason.split()[1]
    if reason.startswith("select"):
        return "skrypt wyboru zawiódł"
    return "inny powód"


def result_line(findings: list[dict]) -> str:
    if count(findings, "open", "blocker") or count(findings, "reported", "blocker"):
        return "❌ Review: są uwagi blokujące"
    if count(findings, "open") or count(findings, "reported"):
        return "⚠️ Review: część uwag czeka na decyzję"
    return "🏁 Review: czysto, wszystko naprawione albo bez uwag"


def render(doc: dict) -> str:
    findings = doc["findings"]
    open_count = count(findings, "open")
    lines = [result_line(findings)]
    lines.append(f"✅ Naprawione automatycznie: {count(findings, 'fixed')}")
    if open_count:
        lines.append(f"⚠️ Zostało do decyzji: {open_count} (blokujące {count(findings, 'open', 'blocker')}, "
                     f"ważne {count(findings, 'open', 'major')})")
    else:
        lines.append("✅ Nic nie zostało do decyzji")
    if count(findings, "reported"):
        lines.append(f"❌ Cofnięte poprawki, bo psuły testy: {count(findings, 'reported')}")
    skipped = [f"{CHECKER_NAMES.get(c['id'], 'sprawdzacz projektu')} ({skip_reason(c.get('reason', ''))})"
               for c in doc["checkers"] if c["status"] == "skipped"]
    if skipped:
        lines.append(f"🔒 Pominięte sprawdzacze: {', '.join(skipped)}")
    calls = sum(c["model_calls"] for c in doc["checkers"])
    lines.append(f"💡 Koszt: {calls} wywołań modelu, rund napraw: {doc['rounds']}")
    if open_count:
        lines.append("❓ Zająć się teraz pozostałymi uwagami?")
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
