---
type: audit
title: SocratexAI vs pstack vs ECC
description: Porównanie naszego rdzenia AI z pstack (poteto) i Everything Claude Code (ECC); co pożyczyć, czego nie instalować.
updated: 2026-11-16
---

# 🔍 Audyt: SocratexAI vs pstack vs ECC

Zapisany, żeby nie powtarzać. Przed ponownym audytem sprawdź sekcję "Kiedy odświeżyć".

## 📏 Metoda i pewność
- Źródło: README obu projektów (WebSearch + WebFetch, 2026-11-16) oraz lokalny przegląd SocratexAI (`core/`, `claude/`, `skills/`, `docs/IMPROVEMENTS.json`).
- Nie instalowano ani nie czytano kodu hooków pstack/ECC. Wnioski o jakości działania to hipotezy; fakty to tylko opisy z README.
- ECC README przeczytane do znaku 100000 z 139919 (końcówka nieprzeczytana).

## 🧱 Czym są
- **SocratexAI**: mały rdzeń reguł (~11 KB zawsze ładowane), 4 agenci tierowi, 5 skilli, 1 hook (guard), narzędzia py (risk_score, routing_log, backup, skill_learn), DIRECTIVES jako indeks "co robię -> która reguła".
- **pstack** (Lauren Tan / poteto, port z cursor/plugins/pstack; forki: backnotprop, michael-denyer, painhardcore, zbeyens, mdsmithaustin): filozofia "rygor ponad przepustowość". Router `/poteto-mode`, 23 playbooki, ok. 50 skilli, 24 zasady, 2 agenci. README nie opisuje hooków (poza forkiem michael-denyer: SessionStart wstrzykuje mandat routingu).
- **ECC** (affaan-m/ECC, dawniej everything-claude-code, MIT): "agent harness" - 71 agentów, 314 skilli, 98 shimów komend, hooki, rules, Memory Vault, instincts z confidence, AgentShield (skan konfiguracji). Hasło: optymalizuj okno kontekstu, resztę persystuj.

## 📊 Porównanie
| Obszar | SocratexAI | pstack | ECC |
|---|---|---|---|
| Rozmiar kontekstu startowego | bardzo mały, celowo | mały (zasady indeksowane inline w routerze) | duży ryzyko: rules zawsze ładowane, katalog reklamowany modelowi |
| Routing modeli | tiery + eskalacja na dowodach, jedno źródło JSON | role -> modele przez `/setup-pstack`, panel review wielu modeli | słabo opisany w README |
| Weryfikacja | bramki deterministyczne, risk_score, osobny reviewer | `prove-it-works`, `explain-the-number`, `interrogate` (zostają tylko findings potwierdzone uruchomieniem), formal verification | tdd-workflow, code/security-reviewer, e2e-runner |
| Playbooki typów zadań | brak (TASK-GATING + spec) | 23 (bug, feature, refactor, perf, ship, babysit PR...) | wiele komend /plan /tdd /build-fix |
| Pamięć / uczenie | auto-memory, skill_learn -> skill-reflect, memory-review, AI-PRACTICES | `recall`, `why`, `show-me-your-work` (TSV decyzji) | instincts z confidence, Memory Vault, continuous-learning-v2 |
| Bezpieczeństwo | guard.py, deny na sekrety, backup przed zmianą configu, zgoda właściciela | brak opisu | AgentShield; ale sam niesie ryzyka (niżej) |
| Hooki | PreToolUse guard, opcjonalny Stop gate | brak w upstream | wiele (session-start, suggest-compact, evaluate-session) |

## ✅ Mocne strony SocratexAI (nie ruszać)
- Zasada "borrow before inventing" i kryterium dodania funkcji (pozycja 54 w IMPROVEMENTS) - chroni przed rozrostem, który widać w ECC.
- Eskalacja na dowodach i separacja generatora od reviewera - zgodne z kierunkiem pstack (`interrogate`).
- Oszczędność kontekstu jako reguła pierwszej klasy.

## 🕳️ Luki w SocratexAI (hipotezy do oceny)
1. Brak reguły "dowód działania": kiedy mówię "zrobione", co musi być uruchomione na prawdziwym artefakcie (pstack `prove-it-works`).
2. Brak reguły weryfikacji liczb/pomiarów przed raportem (pstack `explain-the-number`) - istotne przy perf-scan i FPS w projektach gier.
3. Reviewer nie wymaga, by finding był potwierdzony uruchomieniem (pstack `interrogate`) - mniej fałszywych alarmów.
4. Brak playbooków per typ zadania (bug/refactor/ship). Może wystarczyć jeden krótki plik, nie 23.
5. Brak skilla odtwarzania stanu sesji ("recall/session pickup"); częściowo pokrywa pamięć projektu.
6. Uczenie: `skill_learn` nie ma licznika powtórzeń/pewności jak instincts ECC (mała poprawka, nie nowy system).

## 🚫 Czego nie instalować
- **ECC w całości**: ryzyko rozdęcia kontekstu (sprzeczne z pozycją 25), duplikacja hooków przy stackowaniu instalacji, otwarte błędy na natywnym Windows (observer daemon, zapis pamięci - ECC #2489, #2626), nieoficjalne forki mogą zawierać malware (ostrzeżenie z README), `/astra-review` wysyła diffy do OpenAI, płatny tier Pro.
- **pstack w całości**: domyślny panel review zakłada modele/vendorów, których nie używamy (pozycje 16, 17 = N); `/poteto-mode` jako router przejąłby rolę naszego DIRECTIVES. Formal verification (TLA+) - nieadekwatne do gry Unity.

## 💡 Rekomendacja
Pożyczać idee jako 3-4 krótkie reguły tekstowe, nie pakiety:
1. `prove-it-works` + `explain-the-number` -> dopisać do `core/rules/REVIEW.md` i TASK-GATING (najtańsze, największy zwrot).
2. `interrogate` -> w `reviewer.md`: finding bez powtarzalnego dowodu oznaczać jako PLAUSIBLE, nie CONFIRMED.
3. Jeden `core/rules/PLAYBOOKS.md` (bug / feature / refactor / ship) po ~10 linii każdy, podpięty w DIRECTIVES.
4. Jednorazowy, tylko do odczytu skan AgentShield (`ecc-agentshield`) na naszej konfiguracji - wymaga zgody właściciela (instalacja narzędzia z npm).
Wdrożenie punktów 1-3: zadanie na ok. godzinę, bez nowych zależności.

## 🔁 Kiedy odświeżyć
- Gdy pstack lub ECC wyda duży release, albo gdy IMPROVEMENTS.json urośnie o >10 pozycji.
- Przy ponownym audycie: nie powtarzaj zbierania opisów; sprawdź tylko zmiany po 2026-11-16 (releases ECC: 2.2.x; pstack upstream: cursor/plugins/pstack) i status punktów 1-4 powyżej.
- Nie zweryfikowano: jakości hooków, realnego kosztu tokenów ECC po instalacji, zachowania pstack na Windows.

## 📎 Źródła
- https://github.com/backnotprop/pstack
- https://github.com/michael-denyer/pstack-claude
- https://github.com/painhardcore/pstack
- https://github.com/affaan-m/everything-claude-code
