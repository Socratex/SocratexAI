---
type: doc
title: Nadpisania w projekcie
description: Standardowy format nadpisań SocratexAI per projekt - które pliki, jakie klucze, reguły scalania i przykłady
updated: 2026-11-22
---

# Nadpisania w projekcie

Projekt trzyma tylko własne fakty i nadpisania. Ogólne zasady przychodzą z SocratexAI. Wszystko, co niżej, sprawdzisz komendą `sox config show --project <ścieżka>` (wartość i plik, z którego pochodzi).

## Kolejność warstw (wygrywa ostatnia)
1. `defaults/` i `modules/` (w repo SocratexAI, nie edytujesz)
2. profil (`defaults/profiles/<profil>.json`, wybierany kluczem `profile`)
3. `local/overrides/` (Twoje, globalnie, poza repo)
4. `<projekt>/.socratex/config.json` (w repo projektu, widzi zespół)
5. `local/projects/<nazwa folderu projektu>/` (Twoje, prywatne, poza repo)

Luzować bezpieczeństwo (`safety.allow`) wolno tylko z warstw 2-3 i 5, nie z pliku projektu (4). Taki wpis w projekcie jest ignorowany i zgłaszany jako błąd.

## Pliki w projekcie

| Plik | Do czego |
|---|---|
| `.socratex/config.json` | główna konfiguracja (klucze niżej) |
| `.socratex/flow.json` | zmiany w tabeli flow (kroki dopisz, usuń) |
| `.ai/guard.json` | własne wzorce dla hooka bezpieczeństwa |
| `.ai/review.json`, `.ai/planning.json` | nadpisania sprawdzaczy etapów review i planning |
| `.ai/RISK-RULES.json` | własne reguły oceny ryzyka diffa |
| `AGENTS.md`, `CLAUDE.md`, `INDEX.json` | tylko fakty i reguły projektu; start z `templates/project/` |

Każdy plik konfiguracji ma `schema_version` (dziś `1`). Nieznany klucz to błąd z nazwą pliku i klucza, nic nie jest po cichu pomijane.

## `.socratex/config.json`

| Klucz | Znaczenie |
|---|---|
| `schema_version` | wymagany, `1` |
| `profile` | `solo`, `duo` albo `yolo` (komplet wartości domyślnych) |
| `codex` | `enabled`, `review`, `delegate` (czy używać Codexa) |
| `stages` | `{"review": {"enabled": false}}` wyłącza etap |
| `routing.tier_overrides` | `{"rola": "cheap" / "standard" / "high"}` |
| `extensions` | lista włączonych rozszerzeń (zmiany przez `$append`, `$remove`) |
| `preferences` | `{"code": {"files": [...], "load_when": "..."}}` |
| `startup.load_rules` | czy `RULES.md` ładuje się na starcie |
| `safety.allow` | luzowanie reguł bezpieczeństwa (tylko warstwy właściciela) |

Przykład:
```json
{
  "schema_version": 1,
  "profile": "duo",
  "codex": {"enabled": true, "review": false, "delegate": true},
  "stages": {"planning": {"enabled": false}},
  "extensions": {"$append": ["serena"], "$remove": ["usage-optimize"]},
  "routing": {"tier_overrides": {"implementer": "high"}}
}
```

## Reguły scalania
- Obiekty scalają się w głąb, a wartości proste i listy się podmieniają.
- `{"$append": [..]}` dopisuje do listy, `{"$remove": [..]}` zdejmuje wskazane elementy (brak elementu nie jest błędem). Oba można dać naraz: najpierw `$remove`, potem `$append`.
- `{"$delete": true}` usuwa cały klucz (usunięcie nieistniejącego klucza nie jest błędem).

## Sprawdzacze review i planning (`.ai/review.json`, `.ai/planning.json`)
Warstwy rejestru: `checkers.json` etapu, potem `local/overrides/stages/<etap>.json`, potem plik projektu, potem `local/projects/<projekt>/<etap>.json`. Później wygrywa.
```json
{
  "checkers": {"comments": {"enabled": false}, "readability": {"tier": "high", "max_chunk_lines": 100}},
  "add": [{"id": "godot-api", "concern": "...", "scope": "hunk"}],
  "skip_patterns": ["*.generated.cs"]
}
```
Zmiany widać w sekcji "Stage registries" w `sox config show`.

## Flow (`.socratex/flow.json`)
`steps` jest obiektem: `$remove` (lista id, brak id jest ignorowany), `$delete` (lista id, brak id to błąd) i `$append` (pełne kroki, opcjonalnie `before` lub `after` z id kroku). Usunięcie i dopisanie tego samego id podmienia krok. Krok, od którego zależy inny (`needs`), nie może zniknąć. Sprawdzenie: `sox flow check`.

## Guard (`.ai/guard.json`)
```json
{
  "big_files": ["TASKS.json"],
  "read_only_dirs": ["archive"],
  "blocked_commands": [{"pattern": "godot.*\\.exe", "reason": "uruchamiaj tylko przez skrypt projektu"}],
  "big_file_reader": "jak czytać duże pliki"
}
```
Wzorce projektu dopisują się do reguł rdzenia, nie zastępują ich.

## Weryfikacja
- `sox config show --project <ścieżka>`: wynik końcowy ze źródłem każdej wartości
- `sox flow check`: poprawność flow
- `sox project check <ścieżka>`: zgodność projektu ze standardem (komenda w budowie)
