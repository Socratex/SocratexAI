---
type: spec
title: Pipeline review z mikro-sprawdzaczami
description: Rejestr tanich, oskryptowanych sprawdzaczy (po jednym na zagadnienie), które tylko zgłaszają; poprawki robi jeden wykonawca; zbiera osobna sesja.
updated: 2026-11-21
status: draft
---

# Pipeline review z mikro-sprawdzaczami

## Cel
Zastąpić "pamiętaj 100 zasad review" kilkoma tanimi sprawdzaczami, z których każdy ma jedno zagadnienie, własny skrypt i wąski wycinek kodu. Jakość ma wynikać ze skryptów i bramek, nie z pamięci agenta ani z drogiego modelu.

## Poza zakresem
- Pipeline planowania (tabela do edycji, research, sprawdzenie interpretacji). To osobna specyfikacja; dzieli z tą tylko format rejestru.
- Pisanie samych skryptów sprawdzaczy poza pierwszym zestawem z kryteriów akceptacji.
- Zmiana agenta `reviewer` (zostaje jako eskalacja i ręczne review całości).
- Automatyczny push, merge, PR.
- Ocena stylu wizualnego i sztuki (idzie do Codexa wg `core/rules/ROUTING.md`).

## Decyzje
1. **Wyzwalacz: automatycznie na końcu cyklu zmian.** Cykl jest stały: planowanie i rozmowa z właścicielem, potem praca z testami automatycznymi, potem cykl review. Agent decyduje, kiedy cykl się skończył, ale uruchomienie review jest krokiem tego cyklu zapisanym w `core/DIRECTIVES.json` ("kończę serię zmian -> `tools/review/run.py`"), a nie rzeczą do zapamiętania. Powód: reguła, która polega na pamięci, nie przetrwa.
2. **Sprawdzacze tylko zgłaszają.** Żaden nie edytuje plików. Powód: równoległe edycje tych samych plików się nadpisują.
3. **Naprawy:** mechaniczne (pewne, bez oceny) robi skrypt naprawczy; reszta idzie do jednego `implementer`, po jednym pliku naraz. Powód: tanio tam, gdzie wynik jest pewny, i zero konfliktów.
4. **Model per sprawdzacz wg routingu** (`core/ROUTING.json`), z nadpisaniem per projekt w `.ai/review.json`. Proste, "głupie" zadania na najtańszym poziomie (haiku lub sam skrypt), ocena (czytelność, architektura) na sonnet, opus tylko na eskalację po jawnym powodzie (nieudana bramka, sprawdzacz zgłosił "niepewne"). Powód: ta sama zasada co reszta routingu, jedno miejsce prawdy.
5. **Agregacja:** osobna sesja czyta scalony `findings.json`, deduplikuje, szereguje i raportuje w UCE. Główna sesja routera nie czyta surowych zgłoszeń.
6. **Skrypt najpierw, model potem.** Każdy sprawdzacz ma skrypt wybierający kandydatów (`rg`, Serena, graphify, czytanie diffa grepem). Brak kandydatów oznacza brak wywołania modelu i koszt zero.
7. **Chunking:** sprawdzacz dostaje tylko swój wycinek (plik lub hunk diffa plus minimalny kontekst), nigdy cały diff. Limit wielkości wycinka jest polem rejestru.
8. **Format danych:** JSON dla skryptów (rejestr, zgłoszenia); Markdown tylko dla tego, co czyta człowiek (raport agregatora).

## Rejestr sprawdzaczy
Plik `tools/review/checkers.json` (globalny) plus opcjonalne `.ai/review.json` w projekcie (dopisuje, wyłącza, zmienia model). Schemat rejestru jest wspólny dla review i planowania: `socratex-checker-registry/v1`, z wymaganym polem `pipeline` (`review` lub `planning`) i opcjonalnym `stage`. Planowanie ma własny plik w `tools/planning/`. Wspólny silnik (runner, scalacz, walidacja schematem, chunking, logi) jest w `tools/pipeline/`; `tools/review/run.py` to cienka nakładka, a runner przyjmuje ścieżkę rejestru jako argument. Pola sprawdzacza:

| pole | znaczenie |
|---|---|
| `id` | krótki unikalny identyfikator, np. `comments` |
| `concern` | jedno zdanie: co ten sprawdzacz ocenia |
| `scope` | co dostaje: `file`, `hunk`, `symbol`, `whole_diff` (ostatnie wymaga uzasadnienia) |
| `max_chunk_lines` | twardy limit wycinka |
| `select` | komenda skryptu wybierającego kandydatów (wyjście: lista wycinków JSON) |
| `tool` | `rg`, `serena`, `graphify`, `diff-grep`, `none` |
| `tier` | `script` (bez modelu), `cheap`, `standard`, `high` |
| `autofix` | `none`, `script`, `agent` |
| `fix_script` | komenda dla `autofix: script` (musi być idempotentna) |
| `enabled` | włączony domyślnie |

Pierwszy zestaw:

| id | zagadnienie | tier | autofix |
|---|---|---|---|
| `readability` | czy kod czyta się jak książka (nazwy, długość funkcji, zagnieżdżenie) | standard | agent |
| `architecture` | czy zmiana zgadza się z architekturą i granicami modułów (Serena, graphify) | standard | none |
| `test-necessity` | czy test jest zasadny i nie nadmiarowy (brak asercji, duplikat, testuje implementację) | cheap | agent |
| `comments` | czy komentarz jest zasadny (powtarza kod, nieaktualny, martwy kod w komentarzu) | cheap | script dla martwego kodu i powtórzeń, reszta agent |
| `contracts` | jawne kontrakty, brak połkniętych błędów | cheap | none |
| `leaks` | sekrety i dane osobiste (istniejący `tools/check_leaks.py`) | script | none |

## Format zgłoszeń
Pliki robocze są tymczasowe i leżą POZA repozytorium: `<katalog tymczasowy systemu>/socratex-pipeline/<pipeline>/<run_id>/` (runner je tworzy i sprząta; flaga `--keep` zostawia je do debugowania). Każdy sprawdzacz zapisuje własny plik `<checker_id>.json` (bez wspólnego pliku do zapisu, więc brak konfliktów). Scalacz łączy je w `findings.json` w tym samym katalogu. Poza repo trafia tylko zagregowany raport: runner po sprzątaniu drukuje raport UCE z pamięci (`--report-file` zapisuje go też do pliku); osobna sesja agregatora czyta `findings.json` tylko po uruchomieniu z `--keep`. Pola zgłoszenia:

- `id`, `checker`, `file`, `line_start`, `line_end`
- `severity`: `blocker`, `major`, `minor`, `nit`
- `kind`: `mechanical` (pewna poprawka bez oceny) lub `judgment`
- `confidence`: `high`, `medium`, `low`
- `message`: jedno zdanie, co jest nie tak
- `fix`: `{type: "script"|"patch"|"none", command_or_patch}`
- `status`: `open`, `fixed`, `reported`, `superseded`, `rejected`

## Przebieg
1. Runner (`tools/pipeline/`, uruchamiany przez `tools/review/run.py`) ustala zmienione pliki i dzieli je na wycinki.
2. Każdy włączony sprawdzacz: `select` zwraca kandydatów; dla `tier: script` wynik to od razu zgłoszenia; inaczej tani model ocenia tylko kandydatów. Sprawdzacze są tylko do odczytu i mogą działać równolegle.
3. Scalacz łączy pliki, usuwa duplikaty (to samo miejsce, ten sam problem), przy nakładaniu zostawia wyższą wagę, resztę oznacza `superseded`.
4. Skrypty naprawcze (`kind: mechanical`) uruchamiane sekwencyjnie, po jednym pliku.
5. Pozostałe `open` z `autofix: agent`: jeden `implementer`, po jednym pliku, z briefem zawierającym tylko zgłoszenia tego pliku.
6. Po poprawkach: ponowne uruchomienie skryptów `select` dla dotkniętych plików i bramek projektu (testy). Maksymalnie 2 rundy napraw.
7. Osobna sesja agregatora czyta `findings.json` i pisze raport UCE: co naprawione, co zostało, co wymaga decyzji właściciela.
8. Wynik trafia do logu (`tools/routing_log.py`) razem z kosztem per sprawdzacz.

## Kryteria akceptacji
1. `tools/review/checkers.json` jest poprawnym JSON-em, a runner odrzuca sprawdzacz bez pól wymaganych (`id`, `scope`, `select`, `tier`, `autofix`) z czytelnym błędem.
2. Dla repozytorium testowego (fixture) bez zmian runner kończy się z kodem 0, bez żadnego wywołania modelu.
3. Dla fixture ze zmianą, w której `select` nie znajduje kandydatów, liczba wywołań modelu danego sprawdzacza wynosi 0 (sprawdzane licznikiem w logu).
4. Żaden sprawdzacz nie modyfikuje plików: po fazie sprawdzania `git status` jest identyczny jak przed.
5. Każdy sprawdzacz zapisuje wyłącznie własny plik; scalacz tworzy `findings.json` zgodny ze schematem (walidacja schematem w teście).
6. Duplikaty (to samo `file`, nakładające się linie, ta sama kategoria) są scalane do jednego zgłoszenia; pozostałe dostają `superseded`.
7. Skrypt naprawczy uruchomiony drugi raz nie zmienia już pliku (idempotencja), co test sprawdza dla każdego `fix_script` z rejestru.
8. Poprawki agentowe są wykonywane po jednym pliku naraz (log pokazuje brak nakładania się przedziałów czasowych na ten sam plik).
9. Wycinek przekazany sprawdzaczowi nie przekracza `max_chunk_lines`; większy jest dzielony, a log to odnotowuje.
10. `.ai/review.json` w projekcie może wyłączyć sprawdzacz i zmienić `tier`; test pokazuje, że globalny rejestr pozostaje nietknięty.
11. Eskalacja `tier` o jeden poziom zachodzi tylko po jawnym powodzie (`confidence: low` lub nieudana bramka) i jest zapisana w logu z powodem.
12. Po 2 rundach napraw runner kończy się, nawet jeśli zostają zgłoszenia `open`; trafiają one do raportu, nie do trzeciej rundy.
13. Raport agregatora ma format UCE (pierwsza linia wynik, 3-6 punktów, najwyżej jedno pytanie) i nie zawiera ścieżek ani identyfikatorów.
14. `core/DIRECTIVES.json` zawiera wpis uruchamiający review na końcu serii zmian, a nowe narzędzia i dokument są dopisane do najbliższego `INDEX.json`.
15. Log kosztu zawiera, dla każdego sprawdzacza: liczbę wywołań modelu, tier, wielkość wejścia w wycinkach.

## Przypadki brzegowe
- **Pusty diff:** runner kończy się od razu, kod 0, jedna linia w logu.
- **Plik binarny lub wygenerowany:** pomijany (lista wzorców w rejestrze), bez zgłoszeń.
- **Dwa sprawdzacze zgłaszają to samo miejsce:** zostaje wyższa waga, drugie `superseded`; poprawka jest wykonana raz.
- **Poprawka psuje bramkę (testy):** zmiana tego pliku jest cofnięta (tylko własne poprawki runnera, bez destrukcyjnego git), zgłoszenie dostaje `reported` z notatką, runner idzie dalej.
- **Skrypt `select` pada (brak Serena lub graphify):** sprawdzacz oznaczony jako pominięty z powodem w raporcie; reszta działa. Nie wolno udawać, że sprawdzono.
- **Model zwraca nieprawidłowy JSON:** jedna ponowna próba tym samym tierem; potem zgłoszenie pominięte i odnotowane, bez eskalacji w ciemno.
- **Niepewny sprawdzacz (`confidence: low`):** tylko eskalacja o jeden tier, nie zgadywanie.
- **Zmiany innych sesji w drzewie:** runner bierze tylko pliki z listy przekazanej przez właściciela cyklu; cudzych niezatwierdzonych zmian nie dotyka.
- **Wycinek większy niż limit:** dzielony na części; zgłoszenia przechodzące przez granicę są scalane po stronie scalacza.
- **Brak `.ai/review.json`:** używany sam globalny rejestr.
- **Projekt bez Sereny i graphify:** sprawdzacze, które ich wymagają, wyłączone domyślnie w tym projekcie, reszta (rg, diff) działa.

## Weryfikacja
- Testy runnera i scalacza na repozytorium fixture, napisane przed implementacją: `python -m pytest tools/review/tests -q` (kryteria 1-12).
- Test idempotencji skryptów naprawczych: ten sam pakiet testów, parametryzowany po rejestrze (kryterium 7).
- Przebieg próbny: `python tools/review/run.py --dry-run --files <lista>` pokazuje sprawdzacze, wycinki i przewidywaną liczbę wywołań modelu bez ich wykonania.
- Kontrola kosztu: po przebiegu na realnej serii zmian porównać z jednym wywołaniem `reviewer` na cały diff (liczba tokenów wejścia) i zapisać wynik w `docs/AI-PRACTICES.md`.
- Review wdrożenia w osobnym kontekście (`reviewer` lub `/codex:review`) względem tej specyfikacji: czy każde kryterium jest zrobione i czy przypadki brzegowe mają testy, bez uwag o stylu.

## Ryzyka i założenia
- **Założenie:** Serena i graphify są dostępne tylko w części projektów, więc sprawdzacze muszą działać z samym `rg` i diffem.
- **Ryzyko: fałszywe alarmy** tanich modeli w sprawdzaczach oceny. Mitygacja: `confidence`, skrypt najpierw, eskalacja o jeden tier; metryka odrzuconych zgłoszeń w logu.
- **Ryzyko: czytelność "jak książka" jest oceną**, nie testem. Zgłoszenia tego sprawdzacza zawsze `kind: judgment`, nigdy autofix skryptem.
- **Ryzyko: koszt rośnie z liczbą sprawdzaczy.** Mitygacja: chunking, brak kandydatów równa się brak wywołania, limit rund, licznik w logu.
- **Ryzyko: automatyczny wyzwalacz irytuje przy drobnych zmianach.** Mitygacja: runner pomija próg trywialnych zmian (pole `min_changed_lines` w rejestrze; wartość ustalić na pierwszym przebiegu).
- **Założenie:** kolejna specyfikacja (planowanie) użyje tego samego formatu rejestru i znajdzie się w `docs/specs/planning-pipeline/`.
- **Do ustalenia przy implementacji:** dokładny próg `min_changed_lines` i limity `max_chunk_lines` (zmierzyć na realnych diffach, nie zgadywać).
