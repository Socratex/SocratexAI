---
type: spec
title: Pipeline planowania z mikro-agentami
description: Planowanie w trzech tanich etapach (formularz, research, sprawdzenie interpretacji) na wspólnym schemacie rejestru i wspólnym runnerze z pipeline'em review.
updated: 2026-11-21
---

# 🧭 Pipeline planowania

## 🎯 Cel
- Plan powstaje z kilku małych, tanich i oskryptowanych etapów, a nie z jednego długiego rozumowania opartego na pamięci reguł.
- Reguły siedzą w skryptach i rejestrze, nie w głowie agenta.
- Powiązane: pipeline review (`docs/specs/review-pipeline/SPEC.md`), wspólny schemat rejestru i wspólny runner.

## 🚫 Poza zakresem
- Tabela edytowalna (plik MD lub artefakt HTML). Właściciel odrzucił: formularz `AskUserQuestion` wystarcza, więc nie ma pliku tabeli dla człowieka.
- Implementacja runnera i wspólnego kodu (`tools/pipeline/`); robi to sesja budująca review.
- Pipeline review (osobny spec).
- Automatyczna zmiana planu bez akceptacji właściciela.

## 🧱 Decyzje
1. Etap 1, pytania: formularz `AskUserQuestion`, do 4 pytań na rundę, rekomendacja pierwsza (zgodnie ze skillem `spec`). Powód: właściciel uznał formularze za dobre, tabela nie wnosi nic ponad nie.
2. Etap 2, research: opcjonalny, uruchamiany tylko gdy niewiadoma da się rozstrzygnąć faktami. Wykonawcę wybiera router według `core/ROUTING.json` i może to różnić się per projekt. Domyślnie: internet i podsumowania do Codexa, szukanie w repo do `scout`. Przykład: Riftbound, Codex dla internetu, scout dla repo.
3. Etap 3, sprawdzenie: osobny agent w osobnym kontekście czyta odpowiedzi właściciela i plan, wypisuje niezgodności z intencją i sugestie. Tylko raport, bez zmian planu. Powód: ryzyko cichej zmiany intencji.
4. Rejestry: osobny plik na pipeline. Review: `tools/review/checkers.json` (istnieje). Planowanie: `tools/planning/checkers.json`. Wspólny schemat `socratex-checker-registry/v1` i wspólny runner; kod współdzielony w `tools/pipeline/` (buduje sesja `local_b63339be-95e0-449b-98be-d5983958eaa5`).
5. Pola wpisu rejestru takie jak w review: `id`, `pipeline` (`planning`), `stage`, `concern`, `scope`, `max_chunk_lines`, `select`, `tool`, `tier`, `autofix` (`none` | `agent` | `script`), `fix_script`, `enabled`. Skrypt (`tool`, `select`) znajduje kandydatów, model ocenia tylko ich. Etapy planowania mają `autofix: none`.
6. Mikro-agenci tylko zgłaszają. Plan zmienia wyłącznie główna sesja po akceptacji właściciela.
7. Pliki pośrednie (findings, szkice, notatki z researchu) leżą poza repo: `<tempdir>/socratex-pipeline/planning/<run-id>/`. Runner tworzy ten katalog i go sprząta. Jedyny plik trwały to wynik dla człowieka (plan / SPEC.md).
8. Etap 1 prowadzi główna sesja (router), bo rozmawia z właścicielem. Etapy 2 i 3 idą do tańszych agentów.

## ✅ Kryteria akceptacji
1. Plan dla zadania powyżej godziny przechodzi etapy w kolejności: formularz, research (jeśli potrzebny), sprawdzenie.
2. `tools/planning/checkers.json` ma wpisy z `pipeline: planning`, własnym `stage` i `autofix: none`, zgodne ze schematem `socratex-checker-registry/v1`.
3. Pola wpisów to dokładnie te z decyzji 5; stare nazwy (`model_tier`, `input_scope`, `script`, `autofix` tak/nie) nie występują.
4. Planowanie używa wspólnego runnera z `tools/pipeline/`, bez własnej kopii.
5. Etap 3 zapisuje raport w katalogu pośrednim i nie modyfikuje planu ani SPEC.md.
6. Brak niewiadomych wymagających faktów: etap 2 jest pominięty i raport mówi dlaczego.
7. Wybór wykonawcy research jest zapisany w raporcie (kto, dlaczego), zgodnie z routingiem.
8. Format findings jest identyczny z pipeline'em review (jeden parser).
9. Pliki pośrednie powstają tylko w `<tempdir>/socratex-pipeline/planning/<run-id>/`, żaden nie trafia do repo, a po przebiegu runner usuwa katalog.
10. Agent etapu 3 dostaje tylko potrzebny wycinek (odpowiedzi i plan), nie całą rozmowę.

## ⚠️ Przypadki brzegowe
- Właściciel nie odpowiada na pytanie: plan używa rekomendacji z oznaczeniem "założone".
- Więcej niż 4 luki: pytamy o 4 najważniejsze, reszta ma domyślne wartości wypisane jako założone.
- Codex niedostępny (limit): research przechodzi na `scout` lub jest pominięty z adnotacją.
- Research przeczy odpowiedzi właściciela: raport etapu 3 flaguje to, decyzja po stronie właściciela.
- Wpis rejestru wskazuje nieistniejący `tool` lub `fix_script`: runner kończy się błędem z `id` wpisu, bez cichego pominięcia.
- Wpis z `enabled: false`: runner go pomija i zapisuje to w raporcie.
- Przebieg przerwany w połowie: katalog pośredni zostaje do następnego uruchomienia, które go sprząta; nic nie trafia do repo.
- Ten sam plan uruchomiony dwa razy: osobny `<run-id>`, bez kolizji plików.

## 🔍 Weryfikacja
- Walidacja `tools/planning/checkers.json` względem schematu `socratex-checker-registry/v1`.
- Test runnera na przykładowym zadaniu z trzema etapami: findings zgodne ze schematem, zapisane w katalogu tymczasowym, katalog sprzątnięty po przebiegu.
- Test: po przebiegu `git status` nie pokazuje nowych plików pośrednich.
- Test etapu 3: plan przed i po jest identyczny (hash).
- Grep: brak starych nazw pól w `tools/planning/`.
- Przegląd w osobnym kontekście (`reviewer`) względem tego SPEC.md: czy każde kryterium i przypadek brzegowy ma test.

## 🧪 Ryzyka i założenia
- Założenie: schemat `socratex-checker-registry/v1` i `tools/pipeline/` powstają w buildzie review; planowanie czeka na nie z implementacją.
- Ryzyko: etap 3 mylnie zgłasza niezgodności (fałszywe alarmy); łagodzi to raport bez automatycznych zmian.
- Ryzyko: za dużo etapów dla małych zadań; zadania poniżej godziny pomijają pipeline (jak w skillu `spec`).
- Założenie: Codex bywa niedostępny, dlatego zawsze jest zapasowy wykonawca research.
