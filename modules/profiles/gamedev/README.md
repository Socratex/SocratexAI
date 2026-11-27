---
type: doc
title: Profil gamedev
description: Warstwa reguł dla projektów gier (silnik, zapisy, generowanie świata), włączana kluczem profiles w konfiguracji
updated: 2026-11-27
---

# Profil gamedev
- Profil to paczka reguł dla jednego rodzaju projektu, trzymana w `modules/profiles/<nazwa>/`.
- Dziś zawiera `RISK-RULES.json`: pliki projektu silnika, dane zapisu, przepływ uruchomienia, generowanie świata.
- Domyślne `defaults/RISK-RULES.json` jest neutralne; profil dokłada reguły na wierzch.
- Włączenie w projekcie: `"profiles": ["gamedev"]` w `.socratex/config.json` albo w `local/projects/<klucz>/config.json`.
- Kolejność scalania: defaults, potem profile, potem pliki z klucza `risk_rules` (ścieżki względem korzenia projektu albo bezwzględne).
- Listy dopisują się bez duplikatów; reguła o tej samej nazwie łączy globy; bloki skalarne (progi, punkty) wygrywa późniejsza warstwa.
- Stary `.ai/RISK-RULES.json` nadal podmienia całość, ale tylko gdy żaden z kluczy nie jest ustawiony.
- Sprawdzenie: `sox config show --project <ścieżka>` pokazuje oba klucze i ich źródło.
- Opis: `docs/OVERRIDES.md`, projekt oceny ryzyka: `docs/ROUTER-LOOP.md`.
