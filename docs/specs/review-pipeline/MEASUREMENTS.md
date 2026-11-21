---
type: spec
title: Pomiary progów pipeline'u review
description: Rozkład wielkości zmian z realnych commitów i uzasadnienie min_changed_lines oraz max_chunk_lines.
updated: 2026-11-21
---

# 📏 Pomiary progów review

## 🎯 Wynik
- `min_changed_lines` = 6 (zmiany poniżej progu są pomijane jako trywialne).
- `max_chunk_lines` = 150 dla sprawdzaczy z modelem, 300 dla `leaks` (sam skrypt, bez kosztu modelu).
- Rejestr: `tools/review/checkers.json` (pola `min_changed_lines`, `default_max_chunk_lines`, `max_chunk_lines`).

## 🔬 Metoda
- Źródło: ostatnie 40 commitów (bez merge) każdego z 8 lokalnych repozytoriów git; SocratexAI osobno, reszta zbiorczo (7 innych projektów, 125 commitów z niepustym diffem po odfiltrowaniu plików wygenerowanych).
- Rozmiar commitu = suma dodanych i usuniętych linii (`git show -U0`), bez plików pasujących do `skip_patterns` z rejestru.
- Rozmiar wycinka = to, co zobaczy sprawdzacz o zakresie `hunk`: zakres dodanych linii plus 3 linie kontekstu z każdej strony, nakładające się zakresy scalone (ta sama funkcja `build_chunks` co w runnerze).
- Pomiar jest jednorazowy i zawiera zniekształcenia: kilka ogromnych commitów w cudzych repozytoriach (zaimportowane zasoby) ciągnie górne percentyle w górę.

## 📊 Rozkład (linie)
| miara | zbiór | p20 | p50 | p75 | p90 | p95 |
|---|---|---|---|---|---|---|
| zmiana na commit | SocratexAI (40) | 6 | 27 | 59 | 104 | 276 |
| zmiana na commit | wszystkie (125) | 6 | 25 | 97 | 276 | 580 |
| wycinek z kontekstem | SocratexAI (234) | 7 | 8 | 14 | 26 | 51 |
| wycinek z kontekstem | wszystkie (3949) | 16 | 50 | 127 | 318 | 481 |

## 🧮 Decyzje
- **`min_changed_lines` = 6:** 20. percentyl zmiany na commit wyszedł tak samo (6) w obu zbiorach, więc próg jest stabilny. Około 1 z 5 commitów to zmiana jednoliniowa lub kosmetyczna i review się jej nie opłaca. Wniosek z danych, nie dowód skuteczności: wartość do rewizji po pierwszych realnych przebiegach.
- **`max_chunk_lines` = 150:** wycinek własnego repozytorium jest mały (p99 = 128), więc 150 obejmuje prawie wszystko. W zbiorze zbiorczym 150 leży między p75 (127) a p90 (318). Surowy p90 = 318 odrzucono: tani model dostałby kilkaset linii na jedno wywołanie, a spec wymaga wąskiego wycinka. Większe wycinki są dzielone, a podział trafia do logu.
- **`leaks` = 300:** to skrypt bez modelu, więc większy wycinek nie kosztuje wywołania.

## ⚠️ Ograniczenia
- Próg i limit zmierzono na historii commitów, a runner działa na zmianach w drzewie roboczym przed commitem; rozkład może się nieco różnić.
- Tylko linie dodane tworzą wycinek; usunięcia liczą się do progu, ale nie do wycinka.
