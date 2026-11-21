---
type: spec
title: Restrukturyzacja SocratexAI (core, defaults, modules, targets, state, local)
description: Docelowa struktura repo, kolejność nadpisywania, flow jako dane i plan migracji bez przerwy w działaniu
updated: 2026-11-21
---

# Restrukturyzacja SocratexAI

## Cel
- Jasne, co leży gdzie, co kiedy się odpala i jaki jest główny flow.
- Domyślnie działa dobrze, a każdy projekt zmienia tylko to, co chce, deterministycznie i bez edycji zasad.
- Do kontekstu na starcie trafia tylko mały `INIT.md`; reszta ładuje się, gdy krok flow jej potrzebuje.

## Poza zakresem
- Zmiana logiki review i planning (przenosimy, nie przepisujemy).
- Nowe checkery, nowe role, nowe skille.
- Zmiana uprawnień samego harnessu Claude Code (settings po stronie harnessu zostają).
- Gwarancja 100%, że model trzyma się flow (twarde są tylko hooki i bramki).

## Decyzje
1. **Kształt: `core / defaults / modules / targets / tests`** (kształt agenta). Wszystkie elementy z propozycji właściciela zostają, tylko w tych katalogach. Powód: `modules/` ma być jednolity (samodzielne zdolności z manifestem), treść osobno, a wygenerowane osobno.
2. **Mapowanie elementów właściciela** (nic nie ginie):

   | Element właściciela | Miejsce docelowe |
   |---|---|
   | core/INIT.md, flow.json, safety.json | `core/` bez zmian |
   | core.py (wyciąga zasady z modules, nadpisuje local) | `core/core.py` (resolver) |
   | sox (jedno CLI) | `core/sox` |
   | modules/tools/scripts | `modules/tools/scripts/` |
   | modules/tools/plugins | `modules/tools/plugins.json` (katalog: kategoria, kiedy użyć, on/off) |
   | modules/preferences/code, communication | `defaults/preferences/code`, `defaults/preferences/communication` |
   | modules/stages/review, planning | `modules/stages/review`, `modules/stages/planning` |
   | modules/profiles | `defaults/profiles/` (solo, duo, yolo) |
   | modules/routing/roles, multi-agent | `modules/routing/roles`, `modules/routing/multi-agent` (+ `escalation`) |
   | modules/memory | `modules/memory/` (kod; dane w `state/`) |
   | modules/adapters/codex, claude | `targets/codex`, `targets/claude` (generowane) |
   | modules/tests | testy obok kodu modułu + `tests/` dla rdzenia |
   | state/ | `state/` poza gitem, z rotacją |
   | local/ (tools, stages, profiles) | `local/overrides/{tools,stages,profiles}` |
   | local/projects | `local/projects/<projekt>/` |

3. **Dodatkowo (z ustaleń):** `modules/engine/` (dziś `tools/pipeline`, wspólny silnik review i planning).
4. **Kolejność nadpisywania** (wygrywa ostatni): `defaults` i `modules` → `local/overrides` (globalnie) → `.socratex/config.json` w projekcie (w repo projektu) → `local/projects/<projekt>` (prywatne).
5. **Reguły scalania** w `core.py`: `replace`, `append`, `remove`, jawnie w pliku nadpisania. Wynik walidowany schematem i zapisywany do `state/effective.json`. `INIT.md` czyta wynik, nie scala sam.
6. **Kolejność kroków tylko w `core/flow.json`** (tabela if → then z odnośnikami do `stages` i `roles`). Katalog `stages/` trzyma implementację, nie kolejność.
7. **`safety.json` można luzować.** Każda reguła ma nazwę, luzuje się wprost (`allow: [nazwa]`), profil `yolo` to gotowy zestaw. Luzowanie widać w `sox config show` i trafia do logu w `state/`. Edytuje je wyłącznie człowiek; agent nigdy sam nie dopisuje luzowań.
8. **Każdy plik konfiguracji ma `schema_version`**; zmiana schematu = migracja w `sox migrate`.
9. **Migracja bez przerwy w działaniu:** stare ścieżki zostają jako cienkie przekierowania do końca migracji; `INDEX.json` generuje się z `module.json`.
10. **Nazwy:** CLI `sox`, resolver `core/core.py` (nazwa właściciela).

## Struktura docelowa
```
SocratexAI/
  core/
    INIT.md  flow.json  safety.json  core.py  sox
  defaults/
    preferences/  code/  communication/
    profiles/     solo.json  duo.json  yolo.json
  modules/                  (każdy z module.json, testy obok kodu)
    stages/       review/  planning/
    routing/      roles/  multi-agent/  escalation/
    memory/
    tools/        scripts/  plugins.json
    engine/
  targets/        codex/  claude/      (generowane, nie edytować)
  tests/                                (rdzeń, core.py, sox)
  docs/  templates/  catalog refs (dawne subrepos)
state/                                  (poza gitem, rotacja)
local/                                  (poza repo)
  overrides/      tools/  stages/  profiles/
  projects/       <projekt>/
```

## Kryteria akceptacji
1. `sox config show` wypisuje wynik końcowy i dla każdej wartości źródło (warstwa i plik).
2. Nadpisanie w każdej z 4 warstw działa, a kolejność wygrywania jest zgodna z decyzją 4 (test na każdej parze warstw).
3. Reguły `replace`/`append`/`remove` mają testy, w tym `remove` nieistniejącego klucza.
4. Plik z błędnym schematem lub literówką w kluczu kończy się czytelnym błędem z nazwą pliku i klucza; nic nie jest po cichu pomijane.
5. Reguła z `safety.json` poluzowana przez człowieka działa; ta sama zmiana wprowadzona przez agenta (poza edycją pliku przez właściciela) jest odrzucona przez hook.
6. `sox config show` na górze listuje wszystkie poluzowane reguły i źródło; luzowanie ma wpis w `state/`.
7. `INIT.md` ma limit rozmiaru sprawdzany testem (start budget), a istniejący `test_startup_budget` przechodzi.
8. `flow.json` jest jedynym miejscem z kolejnością kroków; test wykrywa odwołanie do nieistniejącego `stage` lub `role`.
9. Wszystkie istniejące testy (`tools/tests`, `tools/review/tests`, `tools/planning/tests`) przechodzą po przeniesieniu pod nowymi ścieżkami.
10. `targets/` odtwarza się komendą `sox install` z samych źródeł; ręczna edycja wygenerowanego pliku jest wykrywana (znacznik + hash).
11. `INDEX.json` generuje się z `module.json`; `sox index` nie zostawia różnic w drugim przebiegu.
12. Po każdej fazie migracji hooki i install działają (smoke: `sox install` + jedna sesja z `guard.py`).
13. Profil `solo` wyłącza Codex, `duo` go włącza; zmiana profilu w projekcie zmienia wynik `config show` i nic poza tym.

## Przypadki brzegowe
- Brak `.socratex/config.json` w projekcie → działa na samych defaults i `local`.
- Dwie warstwy ustawiają ten sam klucz → wygrywa późniejsza, `config show` pokazuje obie.
- `remove` zdejmuje regułę, od której zależy inny krok flow → błąd walidacji z nazwą kroku.
- Nadpisanie wskazuje nieistniejący moduł lub rolę → błąd, nie ciche pominięcie.
- `local/` brak (świeża maszyna) → `sox install` tworzy szkielet i pyta o profil raz.
- `schema_version` starszy → `sox migrate` albo czytelny błąd z komendą.
- Plik w repo projektu próbuje poluzować `safety` → odrzucone, luzowanie tylko z warstw właściciela (`local`) lub jawnie zatwierdzone; wpis w logu. (Założenie, patrz niżej.)
- `state/effective.json` nieaktualny względem źródeł → `core.py` przelicza (porównanie hashy).

## Weryfikacja
- Testy: `python -m unittest discover` w `tests/`, `modules/**/tests` (komenda `sox test`).
- Ręczny scenariusz: projekt testowy z nadpisaniem w każdej warstwie, `sox config show`, porównanie z oczekiwaną tabelą.
- Przed i po każdej fazie: `sox index` bez różnic, `check_leaks` czysty.
- Review końcowe w osobnym kontekście (`reviewer`) względem tego pliku: czy każde kryterium ma test.

## Plan migracji (kolejność)
- **Faza 0:** `state/` z rotacją; `flow-debug-*` i `audits` tam; `.gitignore`. Najtaniej i bez ryzyka.
- **Faza 1:** `core.py` + `sox config show` na obecnej strukturze (warstwy, schemat, `effective.json`), testy 1-4.
- **Faza 2:** `module.json` dla review, planning, routing; `INDEX.json` z manifestów (test 11).
- **Faza 3:** przeniesienie `tools/review`, `tools/planning`, `tools/pipeline` do `modules/`; przekierowania; aktualizacja testów i ścieżek (kryteria 9, 12).
- **Faza 4:** `defaults/` (preferences, profiles), `flow.json` jako dane + `INIT.md` (kryteria 7, 8, 13).
- **Faza 5:** `targets/` generowane, `safety.json` z luzowaniem (kryteria 5, 6, 10).
- **Faza 6:** usunięcie przekierowań, sprzątanie, aktualizacja dokumentacji i `INDEX.json`.
Każda faza = osobny commit z zielonymi testami; wykonanie fazy bez nowej sesji tylko po akceptacji.

## Ryzyka i założenia
- ⚠️ Ścieżki w hookach, `install.py`, testach i dokumentach (dziś ok. 500 linii samego instalatora) to główny koszt; stąd przekierowania.
- ⚠️ Model nadal może pominąć krok flow; hooki dociskają tylko krytyczne miejsca.
- ⚠️ Poziom wysiłku subagenta ustawimy tylko tam, gdzie pozwala harness.
- Założenie: poluzować `safety` mogą tylko warstwy właściciela (`local/*`), nie plik w repo projektu (nie zespół). Do potwierdzenia.
- Założenie: nazwa `core.py` zostaje (nie `resolver.py`).
- Założenie: dawne `subrepos.json` trafia do `modules/tools/plugins.json` jako osobna sekcja `refs`.
- Założenie: migracja w jednym repo, na gałęzi, bez drugiej kopii.
