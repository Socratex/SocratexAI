# Feature request — branch mode + project profile + ROI bias + script fallback

**Adresat:** AI rozwijające pipeline SocratexAI (źródła w tym repo).
**Autor:** pipeline maintainer.
**Data:** 2026-04-28.
**Charakter:** development prompt — modyfikujesz źródła pipeline'u (`core/`, `project/code/`, `templates/`, `initializer/FIRST-RUN.md`, `PUBLIC-BOOTSTRAP.md`, `tools/`), nie konkretny projekt klienta.

Cztery niezależne features do dodania. Każdą z nich można wdrożyć osobno, ale są ze sobą powiązane semantycznie. Czytaj każdą sekcję jako osobny PR-scope, a na końcu zsumuj zmiany w `CHANGELOG.yaml` i bumpnij `VERSION`.

---

## Feature 1 — tryb "Work on Branch" (konwencja .aiassistant + ignored)

### Skąd to się bierze

Konwencja z dojrzałego projektu referencyjnego okazała się bardzo dobra w praktyce i chcę ją skodyfikować jako wbudowaną opcję pipeline'u. Wzorzec:

```
<project>/
├── .aiassistant/                       # version-controlled, EN-only
│   ├── socratex/AGENTS.md              # working rules, role, code standards
│   ├── socratex/DOCS.md                # document roles
│   ├── socratex/PIPELINE-CONFIG.yaml
│   └── <project>.md                    # project-specific code-gen rules
├── ignored/ai-socratex/                # gitignored, prompt-language
│   ├── <branch>-STATE.md               # what we know on this branch
│   ├── <branch>-PLAN.md                # what's left to do on this branch
│   └── TODO.md                         # ad-hoc backlog
├── CLAUDE.md / AGENTS.md / AI.md       # root directives, point to .aiassistant + global pipeline
```

Pomysł: directives projektu (które mogą być commitowane) żyją w `.aiassistant/`, a bieżąca praca nad konkretnym branchem (która jest ulotna i prompt-language) żyje w `ignored/ai-socratex/`. Każdy branch ma swój komplet `<branch>-STATE.md` + `<branch>-PLAN.md`. Żaden ślad bieżącej pracy nie wycieka do mastera.

### Co zmienić w pipeline

1. **Nowa odpowiedź w `PUBLIC-BOOTSTRAP.md`** — pytanie 3 ("Do you work on branches?") niech **wybiera tryb**, nie tylko odpowiedź tak/nie. Tryby:
   - `branch_scoped` (domyślny gdy user pracuje na branchach) — generuj layout opisany powyżej
   - `linear` (gdy nie ma branchy lub trunk-based bez separacji) — `STATE.yaml` + `_PLAN.yaml` w `.aiassistant/socratex/` jak jest dziś

2. **Per-branch memory layer w `core/MEMORY-MODEL.md` i `PROMOTION-RULES.md`** — dopisz oddzielną warstwę "branch-scoped active state" obok globalnego `STATE.yaml`. Reguła promocji: gdy branch zostaje zmergowany, wartościowe `<branch>-STATE.md` findings promowane są do `context-docs/` lub `DECISIONS.yaml`; reszta zostaje jako referencja.

3. **Nowa sekcja w `project/code/WORKFLOW.md`** — "Branch-Scoped Workflow":
   - Session start: detect branch → look for `ignored/ai-socratex/<branch>-STATE.md` + `<branch>-PLAN.md` → read or create
   - Update STATE/PLAN continuously, nie na końcu
   - STATE = facts: findings, root causes, changes, what's verified
   - PLAN = next steps only, no history
   - Branch end: opcjonalna promocja do trwałych warstw

4. **Język files w `ignored/ai-socratex/`** — match user's prompt language (nie hardcoded English). To jest celowe odstępstwo od reguły "everything in `.aiassistant/` is English only". Powód: te pliki są ulotne i dla mnie, nie dla zespołu. **Jeśli interface language ≠ English — pipeline musi automatycznie zaproponować dodanie `/ignored` (lub odpowiednika) do `.gitignore` z komentarzem typu**:
   ```
   # AI working files in user's prompt language — local-only, not for review
   /ignored
   ```
   Jeśli już jest w gitignore — sprawdzić, dopisać komentarz jeśli go brakuje.

5. **Templates do dodania w `templates/code/branch/`**:
   - `BRANCH-STATE.md` (nie YAML — markdown bo prompt-language i pisany ręcznie)
   - `BRANCH-PLAN.md`
   - `BRANCH-TODO.md`
   Każdy ze szkieletem sekcji.

6. **Nowy plik `project/code/BRANCH-MODE.md`** — dedykowany doc dla tego trybu, do czytania przy `WORKFLOW` na branch projects. Schema, lifecycle, promotion rules.

7. **`PIPELINE-CONFIG.yaml` schema** — dodać klucze:
   ```yaml
   workflow:
     branch_mode: branch_scoped | linear
     branch_files_dir: ignored/ai-socratex
     branch_state_file: ignored/ai-socratex/<branch>-STATE.md
     branch_plan_file: ignored/ai-socratex/<branch>-PLAN.md
     branch_files_language: prompt-language | english
   ```

8. **Adapter docs (`adapters/claude/CLAUDE.md`, `adapters/codex/AGENTS.md`, `adapters/chatgpt/INSTRUCTIONS.md`)** — krótka wzmianka o tym że jeśli `branch_mode == branch_scoped`, agent zaczyna każdą sesję od detect branch + read branch-STATE/PLAN.

### Acceptance dla F1
- Bootstrap procedure pyta o branch mode i instaluje odpowiedni layout.
- Templates dla branch files istnieją i są używane przez initializer.
- Nowy `BRANCH-MODE.md` jest spójny z `MEMORY-MODEL.md` i `PROMOTION-RULES.md`.
- Pipeline automatycznie modyfikuje `.gitignore` (z komentarzem) gdy język ≠ EN.
- Istniejący tryb linear działa bez zmian (backwards-compatible).

---

## Feature 2 — Pre-Bootstrap Project Profile Interview

### Skąd to się bierze

Obecny bootstrap pyta o decyzje (commit/push, branches, DDD, merge mode). Brakuje pytań **o naturę projektu**. Bez tej wiedzy pipeline nie wie, jakich known-solutions szukać. Dla legacy CodeIgniter 5.6 nie szukamy "Hexagonal Architecture w Symfonii" — szukamy "jak modernizować legacy bez wybuchu", "wzorców wstrzykiwania testów do legacy", "strategy pattern dla branchowania zachowań". Charakterystyka projektu zmienia search space known-solutions.

### Co zmienić w pipeline

1. **Nowa sekcja w `PUBLIC-BOOTSTRAP.md`: "Project Profile Interview"** — uruchamiana **po** language detection i context identification, **przed** pytaniami programmingowymi. Pytania (programming context):

   - Project age / lifecycle stage: `greenfield | early | mature | legacy | sunset`
   - Test coverage: `none | smoke-only | partial | comprehensive | tdd`
   - Framework: `standard (name) | custom in-house | mixed | none`
   - Linter / typecheck: `enforced | optional | none`
   - CI/CD: `full | partial | none`
   - Documentation state: `current | partial | stale | none`
   - Team size: `solo | small (2-5) | medium (6-20) | large (>20)`
   - Velocity expectation: `experimental | iterating | shipping | maintenance`
   - Highest current pain: free text — co najbardziej boli (open question)
   - Stack tags: `php-5.6, codeigniter, gearman, docker` etc. — auto-suggest na podstawie `detect_project_stack.ps1`, user weryfikuje

2. **Zapis profilu w `PIPELINE-CONFIG.yaml`**:
   ```yaml
   project_profile:
     lifecycle: legacy
     test_coverage: smoke-only
     framework: codeigniter-2
     framework_kind: standard
     linter: optional
     ci: partial
     docs: stale
     team_size: small
     velocity: maintenance
     highest_pain: "Bad legacy/modern boundary, no DI in legacy code"
     stack: [php-5.6, codeigniter, gearman, docker]
   ```

3. **Nowy plik `core/PROJECT-PROFILE.md`** — definicja każdej osi profilu, dozwolone wartości, wpływ na zachowanie agenta. Wymagana lektura przed `WORKFLOW` jeśli profil istnieje.

4. **Modyfikacja `core/AGENT-CONTRACT.md` — Known-Solutions Directive**:
   Dodać piąty check obok Known solutions / Architecture archetypes / Build-vs-borrow / Future-fit:
   - **Profile-fit check**: search space dla known-solutions musi być filtrowany przez `project_profile`. Dla legacy + custom framework: szukaj wzorców legacy modernization, strangler fig, anti-corruption layer, adapters bridging old/new. Dla greenfield: czystych modeli DDD, hexagonal. Dla no-tests: characterization tests, golden master, scratch refactoring, seam introduction. Dla custom framework: wzorce dla ekstrakcji portu, izolacji frameworka, identyfikacji injection seams.

5. **Aktualizacja `project/code/PACK.md`** — sekcja "Profile-Aware Defaults":
   - legacy → preferuj minimal-invasive changes, characterization tests, seam introduction przed refactorem
   - no-tests → przed jakąkolwiek nietrywialną zmianą, zaproponuj golden master test lub manual reproduction script
   - custom framework → szukaj abstrakcji za adapterem, nie modyfikuj framework core
   - mature standard framework → preferuj wbudowane mechanizmy frameworka, nie własne

6. **Bootstrap initializer (`initializer/FIRST-RUN.md`)** — instruuje agenta by przeprowadził Project Profile Interview, zapisał odpowiedzi w `PIPELINE-CONFIG.yaml`, i wymienił 3 najbardziej trafne known-solutions dla tego profilu jako pierwszą rekomendację.

### Acceptance dla F2
- Bootstrap zadaje 9-10 pytań profilowych przed instalacją.
- `PIPELINE-CONFIG.yaml` zawiera sekcję `project_profile`.
- Agent w każdej sesji czyta `project_profile` i filtruje known-solutions search space.
- `PACK.md` ma sekcję profile-aware defaults z konkretnymi mapowaniami.

---

## Feature 3 — Generic ROI Bias

### Skąd to się bierze

Pipeline dziś dobrze identyfikuje co jest known-solution albo czy DDD-ADIV pasuje. Ale **nie szereguje rekomendacji według ROI**. Wynik: dostaję często trafną listę 8 ulepszeń, z których realnie tylko 2 mają teraz sens. Chcę żeby agent zawsze miał oś "ile to kosztuje × ile to daje" i podawał co się **opłaca teraz** w kategoriach: jakość, prędkość, diagnozowalność, prawdomówność (czyli: jak łatwo zweryfikować że coś działa / jak łatwo wykryć że coś jest zepsute).

### Co zmienić w pipeline

1. **Nowy plik `core/ROI-BIAS.md`** — operacyjny dokument o priorytetyzacji. Definiuje:
   - Cztery osie wartości: **Quality** (poprawność / mniej bugów), **Speed** (velocity rozwoju), **Diagnosability** (jak łatwo zrozumieć co się stało), **Truthfulness** (jak łatwo zweryfikować że twierdzenia o systemie są prawdziwe — testy, asercje, schema, monitoring).
   - Trzy osie kosztu: **Effort** (nakład pracy), **Risk** (ryzyko zepsucia czegoś), **Reversibility** (jak łatwo cofnąć).
   - Reguła ROI: rekomendacja jest "warta teraz" gdy `(impact_on_value_axes × profile_weight) / (effort × risk × (1 / reversibility))` jest wysokie.
   - Profile weight: legacy projekt waży Diagnosability i Truthfulness wyżej niż greenfield. Greenfield waży Quality i Speed.
   - Anti-pattern: rekomendacja, która adresuje "co najlepiej wygląda w abstrakcji", a nie "co realnie boli ten projekt". Pipeline musi to flagować.

2. **Modyfikacja `core/AGENT-CONTRACT.md`** — sekcja "Communication Rules" dostaje nowe wymaganie reportingowe:
   Każdy raport z analizy / review / planowania kończy się sekcją **"ROI Picks"**: 1-3 konkretnych ulepszeń **wartych teraz**, z explicitnym oznaczeniem osi wartości i kosztu:
   ```
   ## 💰 ROI Picks
   1. <improvement> — value: Truthfulness++, Diagnosability+ | cost: Effort=S, Risk=L | why now: <one line>
   2. ...
   ```
   Skala wartości: ++ duża, + zauważalna, ~ marginalna. Skala kosztu: S/M/L/XL effort, L/M/H risk.

3. **Modyfikacja `project/code/WORKFLOW.md`** — komenda `REVIEW` musi obowiązkowo kończyć się sekcją ROI Picks. Komenda `PLAN` — przed promocją z BACKLOG do PLAN, każdy item dostaje ROI score; promocja preferuje wysokie ROI.

4. **`templates/code/_PLAN.yaml`** — każdy pass dostaje opcjonalne pola:
   ```yaml
   passes:
     pass_X:
       ...existing fields...
       roi:
         value_axes: [diagnosability, truthfulness]
         effort: S
         risk: L
         why_now: "..."
   ```

5. **Modyfikacja `core/AGENT-CONTRACT.md` — Operating Principles** — dopisać:
   - "Prefer high-ROI improvements over comprehensive but low-impact passes."
   - "When suggesting multiple improvements, rank them by ROI and call out the top 1-3 explicitly."
   - "Distinguish 'looks good in abstraction' from 'pays off for this project's profile'. The latter wins."

### Acceptance dla F3
- Każdy raport z `REVIEW` / `PLAN` / `FINISH` zawiera sekcję ROI Picks.
- `_PLAN.yaml` schema wspiera ROI metadata.
- `ROI-BIAS.md` definiuje osie wartości / kosztu i regułę ważenia per profile.
- Agent flaguje rekomendacje "abstract-pretty" ale "low-ROI for this profile".

---

## Feature 4 — Script Fallback Discipline

### Skąd to się bierze

Dziś jeśli skrypt z `tools/` nie da się odpalić (np. brak `pwsh`, brak `pyyaml`, brak Pythona), agent ma trzy złe opcje: (a) udawać że odpalił, (b) ręcznie zrobić to samo bez skryptu, (c) zignorować. Wszystkie psują dyscyplinę "script-first". Dobra opcja: **najpierw zaproponować naprawę systemu** (zainstaluj brakującą zależność), dopiero gdy user świadomie odmówi — fallback do ręcznej pracy lub skip. To jest "system-improvement-first" approach: traktujemy brak runtime jak realny bug w setupie, nie jak nieusuwalną przeszkodę.

### Co zmienić w pipeline

1. **Nowy plik `core/SCRIPT-FALLBACK.md`** — protokół:
   - Krok 0: **prerequisites check** przed odpaleniem skryptu (czy istnieje `pwsh`, `python3`, wymagane biblioteki, uprawnienia). To powinno być w `tools/` jako helper `check_runtime.ps1` / `check_runtime.py`.
   - Krok 1: jeśli runtime jest — uruchom skrypt.
   - Krok 2: jeśli brak — **propose system improvement first**: konkretna komenda instalacyjna dla wykrytej platformy (apt/brew/pip/snap), uzasadnienie ("ten skrypt jest używany przez X workflowów, instalacja kosztuje 30s i odblokowuje cały tooling"), prośba o explicitną decyzję user'a.
   - Krok 3: tylko gdy user świadomie odmówi — fallback do `WriteFile` / manual edit, z wyraźnym oznaczeniem w raporcie: "executed manually, script `X` skipped due to missing `Y`, system improvement declined by user".
   - Krok 4: nigdy nie udawaj że skrypt został odpalony.

2. **Modyfikacja `core/AGENT-CONTRACT.md` — Safety Rules** — dopisać:
   - "Never silently fall back from a script to manual work without informing the user."
   - "If a script cannot run due to missing runtime, propose installing the runtime before falling back."
   - "Treat missing tooling runtime as a system bug worth fixing, not as a permanent constraint."

3. **Modyfikacja `project/code/WORKFLOW.md` — "Script-First Execution" sekcja** — dopisać krok przed "Use the script":
   - "Before running a script, verify its runtime is available. If not, propose a system improvement (install command + justification) before falling back to manual."

4. **Helper `tools/check_runtime.py`** — sprawdza dostępność: `python3`, `pwsh` (opcjonalny), wymagane libs (`pyyaml`), zwraca raport stanu w formacie:
   ```yaml
   runtime:
     python3: { ok: true, version: "3.12.1" }
     pwsh: { ok: false, install_hint: "sudo snap install powershell --classic" }
     pyyaml: { ok: false, install_hint: "pip install --user pyyaml" }
   ```
   Pipeline wywołuje to przed pierwszym użyciem `tools/`.

5. **`PUBLIC-BOOTSTRAP.md`** — po Project Profile Interview pipeline odpala `check_runtime.py`, raportuje brakujące rzeczy, proponuje instalację. Bez instalacji — bootstrap kontynuuje, ale `PIPELINE-CONFIG.yaml` zapisuje `runtime_status` żeby przyszłe sesje wiedziały co jest dostępne i czego brakuje.

6. **Adapter docs (`adapters/*/`)** — każdy adapter dostaje krótką wzmiankę: "If a tools/ script cannot run, follow `core/SCRIPT-FALLBACK.md` — never silently bypass."

### Acceptance dla F4
- `core/SCRIPT-FALLBACK.md` istnieje i jest spójny z `WORKFLOW.md` script-first directive.
- `tools/check_runtime.py` raportuje runtime status.
- Bootstrap odpala check_runtime i zapisuje wynik w `PIPELINE-CONFIG.yaml`.
- Agent przy braku runtime'u **najpierw** proponuje instalację, dopiero potem fallback.
- Safety Rules zaktualizowane w `AGENT-CONTRACT.md`.

---

## Cross-cutting wymagania

1. **Backwards compatibility** — istniejące projekty z `0.1.0-alpha` muszą działać po upgrade. Stare `STATE.yaml` + `_PLAN.yaml` w `linear` mode bez zmian. Brak `project_profile` = pipeline pyta przy pierwszej okazji, ale nie krzyczy.

2. **Documentation** — wszystkie nowe pliki czytane są w odpowiednich miejscach `WORKFLOW.md` "Read order". Brak orphaned dokumentów.

3. **Templates spójne z core** — każde nowe pole w `PIPELINE-CONFIG.yaml` ma reprezentację w `templates/code/PIPELINE-CONFIG.yaml`.

4. **Audit** — `tools/audit_yaml_docs.py` sprawdza obecność wymaganych nowych sekcji (`project_profile`, `runtime_status`, `workflow.branch_mode`).

5. **Changelog + version bump** — wpis w `CHANGELOG.yaml` per feature, bump `VERSION` na `0.2.0-alpha` (minor — features, nie breaking).

6. **PUBLIC-BOOTSTRAP.md update** — nowa sekwencja: language → context → **project profile** (F2) → **runtime check** (F4) → programming questions (z F1 branch mode) → directive merge → installation → first useful work pass z **ROI Picks** (F3).

## Kolejność implementacji (sugerowana)

1. F2 (project profile) — fundament, bo F3 (ROI) i F1 (branch mode) korzystają z `project_profile`.
2. F4 (script fallback) — niezależna, ale wpływa na bootstrap UX, więc lepiej przed F1.
3. F1 (branch mode) — buduje na profile + correct gitignore handling.
4. F3 (ROI) — wymaga profile do ważenia osi, więc na końcu.

## Pytania, które możesz mi zadać przed implementacją

Tylko te, których odpowiedź zmienia kształt rozwiązania. Nie pytaj o kosmetykę czy nazewnictwo — wybierz sensownie i jedź.
