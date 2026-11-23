---
type: spec
title: Wiedza o projektach w SocratexAI/local
description: Jedno miejsce prawdy o projektach (zasady, wiedza, tickety, odstępstwa od standardów) w SocratexAI/local, z deterministyczną kolejnością czytania i trybem referencji
updated: 2026-11-23
---

# Wiedza o projektach w SocratexAI/local

## Cel
Agent zawsze dostaje tę samą, uporządkowaną listę plików do przeczytania i nie zastanawia się "czy czegoś jeszcze nie przeczytałem". Wszystko o projektach leży w SocratexAI, łatwo przeglądać który projekt czym się charakteryzuje, dlaczego i jak odbiega od standardów. Na tym komputerze całe `WORK/` (wiedza i tickety) przechodzi do `SocratexAI/local/`. Dla świeżej instalacji to domyślny styl pracy.

## Poza zakresem
- Przeniesienie ciężkich danych generowanych (`_graphs` 4,3 GB, `_tools` 654 MB, `_indexes`, `SocratexAI-workbench` 320 MB) w fazie 1 i 2. Idą w fazie 3 do `local/cache/`.
- Zmiana repo `superplan` (wiedza firmowa, nie ruszamy; projekt dostaje do niego referencję).
- Egzekwowanie czytania kodem. To lista z komendy i hook, model nadal wykonuje tekst.

## Decyzje
1. **Zakres**: wiedza i tickety przenoszone, dane generowane zostają (faza 3: `local/cache/`). Powód: nie mieszać wiedzy z 5 GB cache.
2. **Układ `local/`** (cały poza gitem SocratexAI):
   - `local/projects/<folder repo>/`: `project.json`, `PROJECT.md`, `DOMAIN.md`, `DEVIATIONS.md`, `rules/`, `config.json`
   - `local/tickets/<PREFIX>/<TICKET>/`: STATE, PLAN, `repos.md`, `sql/` (jak dziś w `WORK/<PREFIX>/<TICKET>/`; `_slugs`, `_branches` obok)
   - `local/handovers/`, `local/notes/`, `local/archive/` (stare `legacy/`)
   Powód: jedno miejsce, jedna nazwa, ticket przecina kilka repo więc nie siedzi w projekcie.
4. **Grupa** to nowa warstwa configu i wiedzy. Kolejność od najsłabszej: SocratexAI (`defaults/`, adapter) -> `local/overrides` -> grupa -> projekt w repo (`.socratex`) -> projekt prywatny (`local/projects`). Ostatnia wygrywa: "takie zasady, bo SocratexAI; to ważniejsze, nadpisane; a to per projekt, najważniejsze".
5. **`project.json`** (schema_version 1): `name`, `summary` (jedno zdanie), `group`, `ticket_prefixes`, `knowledge`: `{"mode": "local" | "repo" | "external", "path": "..."}`. Domyślnie `mode: local`. Przy `repo` lub `external` lokalnie leży tylko referencja projekt -> miejsce, a `sox context` czyta ze wskazanej ścieżki. Hybrydowo per projekt.
6. **`sox context --project P [--json]`** drukuje uporządkowaną listę: warstwa, plik, po co, czy istnieje, od najogólniejszego do najważniejszego. Hook startu sesji i `core/INIT.md` wołają tę komendę, więc lista jest zawsze ta sama. Zasada "czytaj w tej kolejności, późniejsze wygrywa przy konflikcie" jest w `INIT.md`, nie w głowie agenta.
7. **Komendy projektu**: `sox project init <ścieżka>` (tworzy szkielet z szablonu, tryb local), `sox project list` (tabela: projekt, grupa, tryb, jakie klucze nadpisuje, podsumowanie), `sox project show <p>` (co i dlaczego odbiega od standardu, z `DEVIATIONS.md`), `sox project check` (spójność plików i configu; dziś "w budowie").
8. **`DEVIATIONS.md`** per projekt: lista odstępstw od standardów SocratexAI, każde z powodem. `sox project list` pokazuje klucze z configu, a `DEVIATIONS.md` tłumaczy dlaczego.
9. **Guard** chroni dziś całe `local/projects/**` (zablokuje agentowi zapis dokumentów). Zawężamy ochronę do plików reguł i configów (`config.json`, `flow.json`, pliki etapów), a dokumenty wiedzy agent może edytować. Zmiana `core/safety.json` tylko ręcznie przez właściciela.
10. **Migracja kopiuje, nie przenosi**: po weryfikacji `WORK/` dostaje znacznik "przeniesione do SocratexAI/local" i zostaje tylko do odczytu. Usunięcie dopiero po wyraźnym "tak" właściciela.
11. **Workspace `CLAUDE.md` i `PLAN-COM-CONVENTIONS.md`**: treść idzie do `local/groups/plan-com/`, a `/home/socratex/PhpstormProjects/CLAUDE.md` zostaje cienkim wskaźnikiem (bo Claude Code ładuje go z drzewa katalogów), który każe wołać `sox context`.
13. **Przenośność**: układ, `sox context`, `sox project ...` i tryb domyślny są kodem w repo SocratexAI (fazy 1 i 4), więc każdy użytkownik i każdy komputer po `git pull` dostaje ten sam deterministyczny sposób czytania. Dane projektów (faza 2 i 3) są per komputer. Do ich wciągnięcia służy ogólna komenda `sox project adopt <folder-ze-starą-wiedzą> --project <repo>` (kopiuje wskazane pliki do `local/projects/<repo>/`, pokazuje plan przed zapisem, nic nie kasuje), a nie skrypt specyficzny dla `WORK/`. Migracja `WORK/` na tym komputerze używa tej samej komendy.
12. **Backup**: `sox backup` obejmuje `local/projects`, `groups`, `tickets`, `handovers`, `notes`, bo po migracji to jedyna kopia wiedzy.

## Fazy
1. Układ, resolver (warstwa grupy), `project.json`, `sox context`, `sox project init|list|show|check`, zawężenie guarda, szablony, testy.
3. Zmiana hooka startu sesji, wskaźnika w workspace `CLAUDE.md`, skryptów z odwołaniami do `WORK/`, przeniesienie danych generowanych do `local/cache/` z poprawą ścieżek narzędzi (graphify, superplan-index).
4. README, `docs/OVERRIDES.md`, INDEX, tryb domyślny dla świeżej instalacji.

## Kryteria akceptacji
2. Projekt z `knowledge.mode: repo` lub `external` jest czytany z podanej ścieżki, a `sox context` pokazuje referencję (projekt -> miejsce).
3. Resolver scala warstwę grupy według tej samej reguły co reszta; `sox config show` pokazuje źródło `group`. Nieznany klucz w `group.json` lub `project.json` to błąd z nazwą pliku i klucza.
4. `sox project list` pokazuje wszystkie projekty z kolumnami: grupa, tryb, nadpisane klucze, podsumowanie. `sox project show <p>` pokazuje odstępstwa z powodami.
5. `sox project init <folder>` tworzy kompletny szkielet, a `sox project check` na nim przechodzi. `sox project adopt` pokazuje plan kopiowania, bez `--yes` niczego nie zapisuje i niczego nie usuwa. Na czystym klonie SocratexAI (bez `local/`) cały przepływ init -> context -> check działa bez żadnych danych z tego komputera.
6. Po migracji każdy plik z `WORK/<P>/` (poza danymi generowanymi i `legacy/`) istnieje pod mapowaną nazwą w `local/`, a sumy kontrolne zgadzają się. Lista niezmapowanych plików jest pusta.
7. Agent (przy `sox install` zastosowanym) zapisuje `local/projects/<p>/PROJECT.md`, ale zapis do `config.json` blokuje guard.
9. `sox backup` kopiuje `local/projects`, `groups`, `tickets`, `handovers`, `notes`.
10. Testy (`sox test`), `sox index --check`, `sox flow check` przechodzą, README opisuje układ `local/` i komendy.

## Przypadki brzegowe
- Projekt bez `project.json`: `sox context` używa tylko warstw globalnych i pisze wprost "brak wiedzy projektu", a nie zgaduje.
- `knowledge.path` wskazuje na nieistniejące miejsce: błąd z nazwą projektu i ścieżką, lista dalej się drukuje z oznaczeniem "brak".
- Ticket z prefiksem bez projektu: `sox project check` ostrzega o osieroconym prefiksie.
- Plik w `WORK/`, którego nie da się zmapować: trafia do raportu migracji i zostaje, nic nie jest gubione.
- Brak `local/` (świeża instalacja): `sox project init` tworzy go; `sox context` bez projektu działa na samych domyślnych.

## Weryfikacja
- `python3 core/sox test`, `python3 core/sox index --check`, `python3 core/sox flow check`.
- Skrypt migracji drukuje raport: plik źródłowy, cel, suma kontrolna, brakujące. Wynik 0 niezmapowanych.

## Ryzyka i założenia
- **ASSUMED**: Claude Code nadal ładuje `CLAUDE.md` z drzewa katalogów, więc wskaźnik w workspace wystarczy. Do potwierdzenia w fazie 3.
- **OPEN**: ścieżki w `preferences.*.files` nie mają potwierdzonej bazy (projekt czy SocratexAI); `sox context` musi to rozstrzygnąć jednoznacznie i opisać.
- Ryzyko: po migracji `local/` jest jedyną kopią wiedzy i leży poza gitem SocratexAI. Mitygacja: punkt 12 (backup) i kopiowanie zamiast przenoszenia do czasu akceptacji.
- Ryzyko: zmiana hooka startu sesji (`~/.claude/hooks`) i guarda to zmiana konfiguracji agenta: tylko po backupie i wyraźnym "tak" właściciela, ręcznie tam, gdzie guard blokuje.
- Ryzyko: ciężkie dane (4,3 GB) w fazie 3 przenosi się w obrębie jednego dysku; narzędzia z twardo wpisanymi ścieżkami przestaną działać do poprawki.
