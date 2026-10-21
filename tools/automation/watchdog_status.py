"""Durable console change detection; a changing countdown is not a status change."""

from __future__ import annotations

import json
import math
import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .files import write_projection


def local_time(timestamp: float) -> str:
    try:
        zone = ZoneInfo(os.environ.get("SOCRATEX_AUTO_TIMEZONE", "Europe/Warsaw"))
    except ZoneInfoNotFoundError:
        zone = None
    return datetime.fromtimestamp(timestamp, zone).astimezone(zone).strftime("%Y-%m-%d %H:%M:%S")


def changes(report: dict, previous: dict) -> tuple[list[str], dict]:
    current = {}
    lines = []
    labels = {"inactive": "AUTO nieaktywne lub zakonczone", "terminal_or_needs_input": "STOP lub potrzebna decyzja",
              "thread_not_idle": "AUTO pracuje lub nie jest gotowe", "project_busy": "projekt zajety",
              "project_reserved": "projekt zarezerwowany", "delivery_pending": "oczekuje na potwierdzenie wysylki",
              "backoff": "oczekuje na dozwolona probe", "batch_finished_or_invalid": "partia zakonczona lub bledna"}
    for row in report["results"]:
        identity = row["thread_id"]
        fingerprint = {key: row.get(key) for key in ("action", "reason", "error", "limit_reset_at", "delivery_id", "prompt")}
        current[identity] = fingerprint
        old = previous.get(identity)
        if old == fingerprint or (old is None and row.get("reason") == "inactive"):
            continue
        if row.get("reason") == "account_limit":
            reset = row.get("limit_reset_at")
            detail = "limit konta; "
            if reset is None:
                detail += "czas odnowienia nieznany; kontrola za 10 min"
            else:
                minutes = max(0, math.ceil((reset - report["observed_at"]) / 60))
                detail += f"odnowienie {local_time(reset)} (pozostalo {minutes} min); kontrola za 10 min"
        elif row["action"] == "sent":
            detail = "wyslano " + row.get("prompt", "CONTINUE-AUTO")
        elif row["action"] in {"blocked", "delivery_unknown"}:
            detail = "BLAD: " + row.get("error", row["action"])
        else:
            detail = labels.get(row.get("reason"), row["action"])
        lines.append(f"[{local_time(report['observed_at'])}] {identity}: {detail}")
    if "scheduler" in previous and "scheduler" not in current:
        lines.insert(0, f"[{local_time(report['observed_at'])}] scheduler: kontrola ponownie dziala")
    return lines, current


def print_changes(home: Path, report: dict) -> None:
    path = home / "watchdog-status.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    lines, current = changes(report, previous)
    write_projection(path, json.dumps(current, ensure_ascii=False, indent=4) + "\n")
    if lines:
        print("\n".join(lines), flush=True)
