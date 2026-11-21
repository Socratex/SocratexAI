---
type: spec
title: Pipeline planowania z mikro-agentami
description: Planowanie w trzech tanich etapach (formularz, research, sprawdzenie interpretacji) na wspólnym rejestrze z pipeline'em review.
updated: 2026-11-21
---

# 🧭 Pipeline planowania

## 🎯 Cel
- Plan powstaje z kilku małych, tanich i oskryptowanych etapów, a nie z jednego długiego rozumowania opartego na pamięci reguł.
- Reguły siedzą w skryptach i rejestrze, nie w głowie agenta.
- Powiązane: pipeline review (`docs/specs/review-pipeline/SPEC.md`), wspólny rejestr.

## 🚫 Poza zakresem
- Tabela edytowalna (plik MD lub artefakt HTML). Właściciel odrzucił: formularz `AskUserQuestion` wystarcza.
- Implementacja runnera i rejestru (to robi osobna sesja po akceptacji obu specyfikacji).
- Pipeline review (osobny spec).
- Automatyczna zmiana planu bez akceptacji właściciela.

## 🧱 Decyzje
1. Etap 1, pytania: formularz `AskUserQuestion`, do 4 pytań na rundę, rekomendacja pierwsza (zgodnie ze skillem `spec`). Powód: właściciel uznał formularze za dobre, tabela nie wnosi nic ponad nie.
2. Etap 2, research: opcjonalny, uruchamiany tylko gdy niewiadoma da się rozstrzygnąć faktami. Wykonawcę wybiera router według `core/ROUTING.json` i może to różnić się per projekt. Domyślnie: internet i podsumowania do Codexa, szukanie w repo do `scout`. Przykład: Riftbound, Codex dla internetu, scout dla repo.
3. Etap 3, sprawdzenie: osobny agent w osobnym kontekście czyta odpowiedzi właściciela i plan, wypisuje niezgodności z intencją i sugestie. Tylko raport do pliku, bez zmian planu. Powód: ryzyko cichej zmiany intencji.
4. Rejestr: jeden wspólny plik JSON dla review i planowania, pole `pipeline` (`review` | `planning`) i pole `stage`. Wspólny runner i wspólny format zgłoszeń (findings). Schemat uzgodniony ze specem review.
5. Każdy mikro-agent w rejestrze ma pola: `id`, `pipeline`, `stage`, `script`, `model_tier`, `input_scope` (chunk), `autofix` (tak/nie), `output`. Skrypt znajduje kandydatów, model ocenia tylko ich.
6. Mikro-agenci tylko zgłaszają (findings JSON). Jeden wykonawca na końcu stosuje poprawki mechaniczne, żeby nie było równoległych edycji tych samych plików.
7. Etap 1 prowadzi główna sesja (router), bo rozmawia z właścicielem. Etapy 2 i 3 idą do tańszych agentów.

## ✅ Kryteria akceptacji
1. Plan dla zadania powyżej godziny przechodzi etapy w kolejności: formularz, research (jeśli potrzebny), sprawdzenie.
2. Każdy etap ma wpis w rejestrze z `pipeline: planning` i własnym `stage`.
3. Etap 3 zapisuje raport do pliku findings i nie modyfikuje planu ani SPEC.md.
4. Brak niewiadomych wymagających faktów: etap 2 jest pominięty i raport mówi dlaczego.
5. Wybór wykonawcy research jest zapisany w raporcie (kto, dlaczego), zgodnie z routingiem.
6. Runner uruchamia agenty z rejestru bez ręcznego wskazywania skryptów.
7. Format findings jest identyczny z pipeline'em review (jeden parser).
8. Agent etapu 3 dostaje tylko potrzebny wycinek (odpowiedzi i plan), nie całą rozmowę.

## ⚠️ Przypadki brzegowe
- Właściciel nie odpowiada na pytanie: plan używa rekomendacji z oznaczeniem "założone".
- Więcej niż 4 luki: pytamy o 4 najważniejsze, reszta ma domyślne wartości wypisane jako założone.
- Codex niedostępny (limit): research przechodzi na `scout` lub jest pominięty z adnotacją.
- Research przeczy odpowiedzi właściciela: raport etapu 3 flaguje to, decyzja po stronie właściciela.
- Rejestr wskazuje nieistniejący skrypt: runner kończy się błędem z nazwą agenta, bez cichego pominięcia.
- Ten sam plan uruchomiony dwa razy: findings nadpisywane per przebieg (id przebiegu), bez duplikatów.

## 🔍 Weryfikacja
- Test rejestru: schemat JSON przechodzi walidację dla wpisów `review` i `planning`.
- Test runnera na przykładowym zadaniu z trzema etapami: powstaje plik findings zgodny ze schematem.
- Test etapu 3: plan przed i po jest identyczny (hash).
- Przegląd w osobnym kontekście (`reviewer`) względem tego SPEC.md: czy każde kryterium i przypadek brzegowy ma test.

## 🧪 Ryzyka i założenia
- Założenie: schemat rejestru zostanie uzgodniony ze specem review, zanim ktokolwiek zacznie implementację.
- Ryzyko: etap 3 mylnie zgłasza niezgodności (fałszywe alarmy); łagodzi to raport bez automatycznych zmian.
- Ryzyko: za dużo etapów dla małych zadań; zadania poniżej godziny pomijają pipeline (jak w skillu `spec`).
- Założenie: Codex bywa niedostępny, dlatego zawsze jest zapasowy wykonawca research.
