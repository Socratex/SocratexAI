#!/usr/bin/env python3
"""Render docs/FLOW.md (Polish): the main flow table, layer order, sox commands and directory map, from the real data.

`sox flow doc` writes the page, `sox flow doc --check` exits 1 when the file differs from what the data
(core/flow.json, the sox parser help, DIRECTORY_MAP) would produce, so the page cannot go stale. Stdlib only.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = Path("docs") / "FLOW.md"
UPDATED = "2026-11-22"

LAYERS = (
    ("1", "`defaults/` i `modules/`", "domyślne wartości dostarczone w repo"),
    ("2", "`local/overrides/`", "twoje nadpisania globalne (poza gitem)"),
    ("3", "`.socratex/config.json` w projekcie", "nadpisania projektu (leżą w repo projektu)"),
    ("4", "`local/projects/<projekt>/`", "prywatne nadpisania projektu (poza gitem)"),
)

# (directory, what it holds); tests/test_flowdoc.py checks that every directory exists.
DIRECTORY_MAP = (
    ("core/", "rdzeń: `INIT.md`, `flow.json`, `safety.json`, resolver `core.py`, CLI `sox`, reguły w `rules/`"),
    ("defaults/", "domyślne preferencje (`code`, `communication`) i profile (`solo`, `duo`, `yolo`)"),
    ("modules/stages/", "etapy `review` i `planning`: rejestry sprawdzaczy i ich skrypty"),
    ("modules/engine/", "wspólny silnik review i planning"),
    ("modules/routing/", "role, wielu agentów, eskalacja"),
    ("modules/memory/", "kod pamięci (dane w `state/`)"),
    ("modules/tools/scripts/", "skrypty: install, backup, update, check_leaks, build_index, risk_score, routing_*, skill_learn, subrepos, state"),
    ("modules/gpt/", "narzędzia do rozmów z ChatGPT (link udostępniania, archiwum)"),
    ("modules/extensions/", "manifesty rozszerzeń: pluginy, MCP, mody, skille, paczki referencyjne"),
    ("targets/", "wygenerowane pliki dla agentów (`sox install`), nie edytować"),
    ("tools/", "cienkie przekierowania na stare ścieżki skryptów dla zewnętrznych wywołań (`sox shims`)"),
    ("skills/, claude/, codex/", "skille, agenci, hooki i dodatki per agent"),
    ("templates/project/", "szablon plików dla nowego projektu"),
    ("tests/", "testy rdzenia, resolvera i `sox` (testy modułów leżą obok ich kodu)"),
    ("docs/", "dokumentacja, rejestr usprawnień, specyfikacje"),
    ("state/", "wyjście maszynowe z rotacją, poza gitem"),
    ("local/", "twoja prywatna warstwa, poza gitem"),
)


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _fact(key: str, value: object) -> str:
    if isinstance(value, bool):
        return key if value else f"nie {key}"
    if isinstance(value, list):
        return f"{key} ∈ {{{', '.join(str(v) for v in value)}}}"
    if isinstance(value, dict):
        parts = []
        for op, operand in value.items():
            if op == "not":
                parts.append(f"{key} ≠ {{{', '.join(map(str, operand))}}}" if isinstance(operand, list) else f"{key} ≠ {operand}")
            elif op == "gte":
                parts.append(f"{key} ≥ {operand}")
            elif op == "lte":
                parts.append(f"{key} ≤ {operand}")
            else:
                parts.append(f"{key} {op} {operand}")
        return " i ".join(parts)
    return f"{key} = {value}"


def condition(when: dict) -> str:
    """Polish one-line reading of a `when` condition ({} means always)."""
    if not when:
        return "zawsze"
    parts = []
    for key, value in when.items():
        if key == "any":
            parts.append("(" + " lub ".join(condition(c) for c in value) + ")")
        elif key == "all":
            parts.append("(" + " i ".join(condition(c) for c in value) + ")")
        elif key == "not":
            parts.append("nie (" + condition(value) + ")")
        else:
            parts.append(_fact(key, value))
    return " i ".join(parts)


def flow_rows(root: Path | None = None) -> list[dict]:
    """Steps of core/flow.json only (no local overrides), so the page is the same on every machine."""
    data = json.loads(((root or ROOT) / "core" / "flow.json").read_text(encoding="utf-8"))
    return data["steps"]


def render(commands: list[tuple[str, str]], root: Path | None = None) -> str:
    """The full page. `commands` is [(`sox ...`, help)] taken from the sox parser."""
    lines = [
        "---", "type: doc", "title: Co kiedy odpalać",
        "description: Jedna strona o tym, co odpalać i kiedy - tabela głównego flow, kolejność warstw, komendy sox i mapa katalogów (generowana z danych)",
        f"updated: {UPDATED}", "---", "",
        "# Co kiedy odpalać", "",
        "Ta strona jest generowana: `sox flow doc` zapisuje ją, `sox flow doc --check` wykrywa, że jest nieaktualna. Nie edytuj jej ręcznie.", "",
        "## Główny flow", "",
        "Źródło: `core/flow.json` (jedyne miejsce z kolejnością kroków). Krok, którego warunek zachodzi, jest obowiązkowy. "
        "Fakty i gramatyka: `core/flow.schema.json`; podgląd z faktami: `sox flow show --match task_size=big`.", "",
        "| # | krok | kiedy | wtedy |", "|---|---|---|---|",
    ]
    for number, step in enumerate(flow_rows(root), 1):
        then = ", ".join(f"`{a}`" for a in step["then"])
        lines.append(f"| {number} | `{step['id']}` | {_cell(condition(step['when']))} | {_cell(then)} |")
    lines += ["", "## Kolejność warstw konfiguracji", "", "Wygrywa ostatnia warstwa; `sox config show` pokazuje źródło każdej wartości.", "",
              "| # | warstwa | co |", "|---|---|---|"]
    lines += [f"| {n} | {layer} | {what} |" for n, layer, what in LAYERS]
    lines += ["", "## Komendy sox", "", "Lista z pomocy parsera (`sox <komenda> --help` ma szczegóły).", "",
              "| komenda | po co |", "|---|---|"]
    lines += [f"| `{name}` | {_cell(text)} |" for name, text in commands]
    lines += ["", "## Mapa katalogów", "", "| katalog | co tam leży |", "|---|---|"]
    lines += [f"| `{path}` | {what} |" for path, what in DIRECTORY_MAP]
    return "\n".join(lines) + "\n"


def write(commands: list[tuple[str, str]], root: Path | None = None) -> Path:
    path = (root or ROOT) / DOC_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(commands, root), encoding="utf-8", newline="\n")
    return path


def is_current(commands: list[tuple[str, str]], root: Path | None = None) -> bool:
    path = (root or ROOT) / DOC_PATH
    return path.is_file() and path.read_text(encoding="utf-8") == render(commands, root)
