---
type: spec
title: Pętla samodoskonalenia (podpowiedzi narzędzi z rejestru)
description: Gdy agent trafi na blokadę albo właściciel narzeka na brak możliwości, agent sprawdza listę usprawnień i podpowiada pasujące narzędzie.
updated: 2026-11-24
---

# Pętla samodoskonalenia

## Cel
Gdy agent mówi "nie mogę tego zrobić", obchodzi problem kolejnym obejściem albo właściciel narzeka na brak możliwości, SocratexAI sprawdza własny rejestr rozwiązań (narzędzia, frameworki, metody, skille, skrypty, MCP, pluginy; typ nie ma znaczenia) i podpowiada pasujące w kontekście bieżącego projektu. Dzięki temu lista usprawnień pracuje na bieżąco, a nie tylko leży.

Powiązane: `docs/IMPROVEMENTS.json` (rejestr), pozycja 86 (hook zbierający tarcia skilli; osobna sprawa, termin ponownej oceny około 2026-12-16), `modules/extensions/*.json`, `defaults/DIRECTIVES.json`.

## Poza zakresem
- Hook wychwytujący frazy (to pozycja 86).
- Instalowanie czegokolwiek. Pętla tylko podpowiada.
- Wyszukiwanie w sieci bez pytania właściciela.
- Realne włączanie lub wyłączanie narzędzi per projekt (osobna decyzja z 2026-11-24).
- Dopasowanie przez embeddingi lub LLM. Dopasowanie jest tekstowe i deterministyczne.

## Decyzje
1. **Wyzwalacz: reguła + skrypt.** Nowy wiersz w `defaults/DIRECTIVES.json` każe agentowi przy blokadzie, powtarzanym obejściu lub narzekaniu właściciela wywołać `sox ledger find`. Powód: wyszukiwanie ma być powtarzalne i tanie w tokenach przy 130 pozycjach, a hook byłby zaszumiony i dotykałby konfiguracji agenta.
2. **Dopasowanie: nowe opcjonalne pole `keywords`** (lista małych liter) w pozycjach rejestru; skrypt szuka po `keywords`, tytule, opisie i obszarze, z największą wagą dla `keywords`. Pozycje bez pola działają po tekście. Powód: lepsza trafność przy niskim koszcie schematu.
3. **Moment: od razu, jedną linią** w stylu UCE, np. "💡 w tym projekcie może pomóc X (pozycja N, status)". Najwyżej raz na pozycję w sesji. Nigdy nie instaluje.
4. **Źródło: rejestr lokalny, potem pytanie o sieć.** Kandydaci to pozycje rejestru i manifesty rozszerzeń. Odrzuconych nigdy nie podpowiada. Gdy rejestr nic nie ma, agent pyta właściciela: "w rejestrze nie znalazłem nic, a zauważyłem, że robisz coś, na co może istnieć gotowe rozwiązanie. Poszukać?" Szuka w sieci dopiero po zgodzie.
   - "Rozwiązanie" to cokolwiek, co usuwa problem: narzędzie, plugin, MCP, skill, framework, metoda, skrypt lub zmiana workflow. Nie tylko plugin. Rejestr i wyszukiwanie nie zakładają typu.
5. **Wynik wyszukiwania** zależy od statusu: wdrożone i włączone w projekcie (przypomnij, jak użyć), wdrożone ale wyłączone (zaproponuj włączenie przez właściciela), do rozważenia (podaj wynik i warunek wejścia), odrzucone (pomijane).

## Kryteria akceptacji
1. `sox ledger find "<tekst>"` zwraca do 3 pozycji, posortowanych po trafności, każda z id, tytułem, statusem i jednolinijkowym wynikiem.
2. Pozycje o statusie `rejected` nie pojawiają się domyślnie; pojawiają się tylko z `--all`.
3. Dopasowanie po `keywords` wygrywa z dopasowaniem tylko po opisie.
4. Pozycja wdrożona, której rozszerzenie jest wyłączone w danym projekcie (`--project`), jest oznaczona jako "wdrożone, wyłączone".
5. Brak trafień daje pusty wynik i kod wyjścia 1, bez błędu i bez zgadywania.
6. Schemat `socratex-improvements/v1` akceptuje opcjonalne `keywords`, a walidacja i `improvements_check.py` nadal przechodzą.
7. `keywords` są uzupełnione dla wszystkich pozycji `considering` i `adopted`; `rejected` nie wymaga.
8. `defaults/DIRECTIVES.json` ma nowy wiersz o blokadach i narzekaniach, wskazujący komendę i regułę; reguła opisuje format linii, limit "raz na pozycję w sesji", zakaz instalowania i pytanie przed szukaniem w sieci.
9. `INDEX.json` zawiera nowe dokumenty i skrypt (`sox index`), a `sox test` oraz `sox project check` przechodzą.

## Przypadki brzegowe
- Pusty lub jednowyrazowy zapytanie: zwraca błąd użycia, nie losowe trafienia.
- Zapytanie po polsku, rejestr po angielsku: dopasowanie po `keywords` ma zawierać polskie odpowiedniki tylko tam, gdzie to ma sens; brak trafień prowadzi do pytania o sieć, nie do zgadywania.
- Ta sama pozycja trafia ponownie w sesji: agent nie powtarza podpowiedzi (dyscyplina reguły, skrypt tego nie pilnuje).
- Właściciel odrzucił pozycję w trakcie sesji: status w rejestrze zmienia się na `rejected` i pozycja znika z wyników.
- Wiele pozycji o podobnej trafności: pokazane maksymalnie 3, reszta pomijana.

## Weryfikacja
- Testy w `modules/tools/scripts/tests/` dla `ledger find`: trafienie po `keywords`, wykluczenie `rejected`, `--all`, wdrożone-wyłączone z `--project`, brak trafień (kod 1), błędne zapytanie. Testy pisane przed implementacją.
- `python3 core/sox test`, `python3 core/sox project check`, `python3 modules/tools/scripts/improvements_check.py`.
- Ręcznie: w osobnej sesji powiedz "nie mogę z tym zrobić X" dla znanego tematu (np. sterowanie aplikacją desktopową) i sprawdź, czy agent wywoła komendę i pokaże jedną linię z pozycjami 83, 127 i 129.
- Po dwóch tygodniach: przejrzeć wpisy `skill_learn` typu `misfire` i ocenić, czy agent pamięta o wywołaniu. Jeśli nie, wrócić do pozycji 86 (hook).

## Ryzyka i założenia
- Główne ryzyko: agent nie wywoła komendy, bo to dyscyplina modelu, a nie hook. Mitygacja: pomiar po dwóch tygodniach, ewentualnie hook z pozycji 86.
- Fałszywe podpowiedzi psują zaufanie: limit 3 trafień, raz na pozycję w sesji, jedna linia.
- Założenie: 130 pozycji i około 55 manifestów mieści się w prostym wyszukiwaniu tekstowym bez indeksu.
- Założenie: uzupełnienie `keywords` to jednorazowa praca (około 100 pozycji), wykonana przez tańszy model i sprawdzona próbką.
- Zmiana `defaults/DIRECTIVES.json` i reguł to zmiana konfiguracji agenta w repo SocratexAI: kopia zapasowa (`modules/tools/scripts/backup.py`) przed zmianą.
