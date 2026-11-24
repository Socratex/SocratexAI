---
type: doc
title: Co kiedy odpalać
description: Jedna strona o tym, co odpalać i kiedy - tabela głównego flow, kolejność warstw, komendy sox i mapa katalogów (generowana z danych)
updated: 2026-11-22
---

# Co kiedy odpalać

Ta strona jest generowana: `sox flow doc` zapisuje ją, `sox flow doc --check` wykrywa, że jest nieaktualna. Nie edytuj jej ręcznie.

## Główny flow

Źródło: `defaults/flow.json` (jedyne miejsce z kolejnością kroków). Krok, którego warunek zachodzi, jest obowiązkowy. Fakty i gramatyka: `core/flow.schema.json`; podgląd z faktami: `sox flow show --match task_size=big`.

| # | krok | kiedy | wtedy |
|---|---|---|---|
| 1 | `session_start` | zawsze | `rule:defaults/DIRECTIVES.json` |
| 2 | `classify` | zawsze | `rule:defaults/rules/TASK-GATING.md` |
| 3 | `ask_unclear` | unclear_requirements | `ask` |
| 4 | `spec` | (task_size = big lub touches ∈ {auth, data, saves, payments, architecture} lub unclear_requirements) | `rule:skills/spec/SKILL.md` |
| 5 | `safe_config` | touches = agent_config | `rule:defaults/rules/SAFETY.md`, `ask` |
| 6 | `plan` | (task_size ∈ {medium, big} lub touches ∈ {auth, data, saves, payments, architecture}) | `role:planner`, `rule:defaults/rules/TASK-GATING.md` |
| 7 | `plan_check` | owner_answers i task_size ∈ {medium, big} | `stage:planning` |
| 8 | `search` | task_size ≠ trivial | `role:scout` |
| 9 | `delegate_codex` | codex i task_size ≠ trivial | `rule:defaults/rules/ROUTING.md` |
| 10 | `code_style` | task_type ∈ {feature, bug, refactor} | `rule:defaults/rules/CODE-STYLE.md` |
| 11 | `implement` | task_size ≠ trivial | `role:implementer` |
| 12 | `risk` | zawsze | `tool:modules/tools/scripts/risk_score.py` |
| 13 | `gate_fast` | zawsze | `gate:fast` |
| 14 | `gate_full` | risk ∈ {standard, full} | `gate:full` |
| 15 | `escalate_to_standard` | gate = failed i attempts_on_tier ≥ 2 i tier = cheap | `role:implementer` |
| 16 | `escalate_to_high` | gate = failed i attempts_on_tier ≥ 2 i tier = standard | `role:planner` |
| 17 | `escalate_to_owner` | gate = failed i attempts_on_tier ≥ 2 i tier ∈ {high, top} | `ask` |
| 18 | `review_stage` | task_size ≠ trivial i gate ≠ failed | `stage:review` |
| 19 | `review_independent` | risk = full | `role:reviewer`, `rule:defaults/rules/REVIEW.md` |
| 20 | `security_review` | touches ∈ {auth, payments} | `rule:defaults/rules/SECURITY-REVIEW.md` |
| 21 | `commit` | gate ≠ failed | `rule:defaults/rules/COMMITS.md` |
| 22 | `log` | zawsze | `tool:modules/tools/scripts/risk_score.py`, `tool:modules/tools/scripts/routing_log.py` |

## Kolejność warstw konfiguracji

Wygrywa ostatnia warstwa; `sox config show` pokazuje źródło każdej wartości.

| # | warstwa | co |
|---|---|---|
| 1 | `defaults/` i `modules/` | domyślne wartości dostarczone w repo |
| 2 | `local/overrides/` | twoje nadpisania globalne (poza gitem) |
| 3 | `.socratex/config.json` w projekcie | nadpisania projektu (leżą w repo projektu) |
| 4 | `local/projects/<projekt>/` | prywatne nadpisania projektu (poza gitem) |

## Komendy sox

Lista z pomocy parsera (`sox <komenda> --help` ma szczegóły).

| komenda | po co |
|---|---|
| `sox config show` | print resolved values with their source |
| `sox config resolve` | write state/effective.json |
| `sox flow show` | print the steps in order |
| `sox flow check` | exit 1 when a step points to a missing stage, role, rule or tool, or the grammar is broken |
| `sox flow doc` | write docs/FLOW.md (what to run when) from the flow table, commands and directory map |
| `sox index` | regenerate INDEX.json from files and module manifests |
| `sox install` | generate targets/ and plan, check or apply the agent config install |
| `sox state rotate` | delete old and surplus files in the known state subdirectories (modules/tools/scripts/state.py) |
| `sox state adopt-logs` | move legacy local/flow-debug-*.log into state/flow-debug/ (never deletes) |
| `sox backup` | zip the agent config (modules/tools/scripts/backup.py); list or restore backups |
| `sox test` | run this repo's test suite the way it is normally run |
| `sox migrate` | upgrade config files whose schema_version is older than supported |
| `sox shims` | list the tools/ redirect shims and how often external callers used them |
| `sox modules` | list modules by kind: what, when to run, entry commands |
| `sox ext list` | extensions grouped by category with status, kind and on/off for the project |
| `sox ext show` | print one manifest |
| `sox ext add` | create a trial manifest in local/extensions and an entry in docs/IMPROVEMENTS.json |
| `sox ext enable` | enable an extension in one config layer file |
| `sox ext disable` | disable an extension in one config layer file |
| `sox ext remove` | delete a local manifest and drop it from the owner's config layers |
| `sox ext install` | kind install only: print the commands; with --yes back up the agent config, then run them |
| `sox ledger find` | up to 3 ledger items or extensions matching the text; exit 1 when none |
| `sox context` | ordered list of files to read for a project, general to most important |
| `sox project check` | read-only audit: with a repo path the repo files plus its knowledge; without a path the whole hub; exit 1 on errors |
| `sox project init` | create the missing project files from templates (repo files and the knowledge skeleton); dry run unless --write |
| `sox project list` | all projects: group, knowledge mode, overridden keys, summary |
| `sox project show` | one project: summary, group, overrides and its DEVIATIONS.md |
| `sox project adopt` | copy old knowledge files into a project's knowledge folder (plan only unless --yes; never overwrites or deletes) |
| `sox project explain` | print one project-check rule and how to fix it |

## Mapa katalogów

| katalog | co tam leży |
|---|---|
| `core/` | rdzeń (kod): `INIT.md`, `safety.json`, resolver `core.py`, CLI `sox`, schematy `*.schema.json` |
| `defaults/` | domyślne dane i dokumenty: `RULES.md`, `STYLE.md`, `flow.json`, `ROUTING.json`, reguły w `rules/`, preferencje (`code`, `commits`, `communication`) i adaptery (`solo`, `duo`, `yolo`) |
| `modules/stages/` | etapy `review` i `planning`: rejestry sprawdzaczy i ich skrypty |
| `modules/engine/` | wspólny silnik review i planning |
| `modules/routing/` | role, wielu agentów, eskalacja |
| `modules/memory/` | kod pamięci (dane w `state/`) |
| `modules/tools/scripts/` | skrypty: install, backup, update, check_leaks, build_index, risk_score, routing_*, skill_learn, subrepos, state |
| `modules/extensions/gpt/` | narzędzia do rozmów z ChatGPT (link udostępniania, archiwum) |
| `modules/extensions/` | manifesty rozszerzeń: pluginy, MCP, mody, skille, paczki referencyjne |
| `targets/` | wygenerowane pliki dla agentów (`sox install`), nie edytować |
| `tools/` | cienkie przekierowania na stare ścieżki skryptów dla zewnętrznych wywołań (`sox shims`) |
| `skills/, claude/, codex/` | skille, agenci, hooki i dodatki per agent |
| `templates/project/` | szablon plików dla nowego projektu |
| `tests/` | testy rdzenia, resolvera i `sox` (testy modułów leżą obok ich kodu) |
| `docs/` | dokumentacja, rejestr usprawnień, specyfikacje |
| `state/` | wyjście maszynowe z rotacją, poza gitem |
| `local/` | twoja prywatna warstwa, poza gitem |
