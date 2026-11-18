---
type: audit
title: SocratexAI vs pstack vs ECC
description: Comparison of our AI core with pstack (poteto) and Everything Claude Code (ECC); what to borrow, what not to install.
updated: 2026-11-18
---

# 🔍 Audit: SocratexAI vs pstack vs ECC

Saved so it is not repeated. Before auditing again, read the section "When to refresh".

## 📏 Method and confidence
- Source: the READMEs of both projects (WebSearch + WebFetch, 2026-11-16) and a local review of SocratexAI (`core/`, `claude/`, `skills/`, `docs/IMPROVEMENTS.json`).
- The pstack/ECC hook code was neither installed nor read. Conclusions about how well they work are hypotheses; only the README descriptions are facts.
- The ECC README was read up to character 100000 of 139919 (the tail was not read).

## 🧱 What they are
- **SocratexAI**: a small rule core (~19 KB always loaded), 4 tiered agents, 5 skills, 1 hook (guard), Python tools (risk_score, routing_log, backup, skill_learn), DIRECTIVES as an index "what I do -> which rule applies".
- **pstack** (Lauren Tan / poteto, port of cursor/plugins/pstack; forks: backnotprop, michael-denyer, painhardcore, zbeyens, mdsmithaustin): philosophy "rigor over throughput". Router `/poteto-mode`, 23 playbooks, about 50 skills, 24 rules, 2 agents. The README does not describe hooks (except the michael-denyer fork: SessionStart injects a routing mandate).
- **ECC** (affaan-m/ECC, formerly everything-claude-code, MIT): an "agent harness" - 71 agents, 314 skills, 98 command shims, hooks, rules, Memory Vault, instincts with confidence, AgentShield (config scan). Motto: optimize the context window, persist the rest.

## 📊 Comparison
| Area | SocratexAI | pstack | ECC |
|---|---|---|---|
| Startup context size | very small, on purpose | small (rules indexed inline in the router) | risk of large: rules always loaded, catalog advertised to the model |
| Model routing | tiers + escalation on evidence, one JSON source | roles -> models via `/setup-pstack`, multi-model review panel | poorly described in the README |
| Verification | deterministic gates, risk_score, separate reviewer | `prove-it-works`, `explain-the-number`, `interrogate` (only findings confirmed by running stay), formal verification | tdd-workflow, code/security-reviewer, e2e-runner |
| Task-type playbooks | none (TASK-GATING + spec) | 23 (bug, feature, refactor, perf, ship, babysit PR...) | many commands /plan /tdd /build-fix |
| Memory / learning | auto-memory, skill_learn -> skill-reflect, memory-review, AI-PRACTICES | `recall`, `why`, `show-me-your-work` (decision TSV) | instincts with confidence, Memory Vault, continuous-learning-v2 |
| Security | guard.py, deny on secrets, backup before config change, owner consent | not described | AgentShield; but it carries its own risks (below) |
| Hooks | PreToolUse guard, optional Stop gate | none upstream | many (session-start, suggest-compact, evaluate-session) |

## ✅ SocratexAI strengths (do not touch)
- The "borrow before inventing" rule and the criterion for adding a feature (item 54 in IMPROVEMENTS) - protects against the bloat visible in ECC.
- Escalation on evidence and separating the generator from the reviewer - in line with the pstack direction (`interrogate`).
- Context economy as a first-class rule.

## 🕳️ SocratexAI gaps (hypotheses to assess)
1. No "proof it works" rule: when I say "done", what must have run on the real artifact (pstack `prove-it-works`).
2. No rule to verify numbers/measurements before reporting (pstack `explain-the-number`) - matters for perf-scan and FPS in game projects.
3. The reviewer does not require a finding to be confirmed by running (pstack `interrogate`) - fewer false alarms.
4. No per-task-type playbooks (bug/refactor/ship). One short file may be enough, not 23.
5. No skill for restoring session state ("recall/session pickup"); partly covered by project memory.
6. ~~Learning: no repeat counter~~ **AUDIT ERROR**: `skill_learn.py` already has a counter (merging similar entries, `count`, READY on a repeated correction). Only expiry of old entries and automatic collection are missing - not implemented, not needed now.

## 🚫 What not to install
- **ECC as a whole**: risk of context bloat (contradicts item 25), duplicated hooks when stacking installs, open bugs on native Windows (observer daemon, memory writes - ECC #2489, #2626), unofficial forks may contain malware (README warning), `/astra-review` sends diffs to OpenAI, paid Pro tier.
- **pstack as a whole**: the default review panel assumes models/vendors we do not use (items 16, 17 = N); `/poteto-mode` as a router would take over the role of our DIRECTIVES. Formal verification (TLA+) - not suited to a Unity game.

## 💡 Recommendation (revised after owner feedback, 2026-11-16)
Originally 4 points were proposed; after verification:
1. ~~`prove-it-works` + `explain-the-number`~~ **REJECTED.** Already covered by: Stop hook / `verify` (deterministic, 0 model tokens), task status "test" (a human closes it), "Say no evidence instead of inventing test results" in RULES, manual check in FULL (REVIEW.md). A text rule will not give the agent a "feel" for the game; risk of ceremonial "verified" without real verification (hypothesis, no evidence).
2. `interrogate` -> in `reviewer.md`: a finding without repeatable proof = PLAUSIBLE, not CONFIRMED. **APPROVED by the owner.**
3. ~~PLAYBOOKS.md~~ **REJECTED.** The old legacy pipeline's `FLOWS.json` (12 flows by intent type; now only on the git branch `legacy`) did this already, heavier and script-driven; in projects the core's TASK-GATING is enough.
4. AgentShield scan: optional, needs consent (npm).
Other ideas to consider: see the section "Additional ideas".

## ✅ Implemented 2026-11-16
- laziness-protocol -> `core/rules/CODE-STYLE.md`.
- why -> a row in `core/DIRECTIVES.json` (git history before reading code).
- never-block-on-the-human -> reversed at the owner's request: for unknowns, a form with defaults first (`core/RULES.md`, Ambiguity).
- Reply style for fast skimming (simple messages without numbers and paths) -> `core/STYLE.md`.
- security-review only for business projects -> `core/rules/SECURITY-REVIEW.md` + a row in DIRECTIVES. Game dev: a security check on the roadmap before multiplayer or release (owner's task).

## 🧩 Additional ideas (from READMEs, not verified in use)
- pstack `laziness-protocol` / `subtract-before-you-add`: one sentence in CODE-STYLE (smallest change, remove before you add) - works against slop, costs ~20 tokens.
- pstack `never-block-on-the-human`: decide on defaults and list the assumptions - fits "standby is friction"; partly already in the Ambiguity rule (limit of 4 questions).
- pstack `why`: answer from commit/PR history instead of code - cheap, no new infrastructure.
- ECC injection limits (`ECC_SESSION_START_MAX_CHARS`, max instincts): the idea of a character budget for startup context; check our session-start size with a script.
- ECC `security-review` fired only on a trigger (auth, secrets, payments, user input): fits B2B, low cost because it is conditional.
- ECC instincts with confidence: a repeat counter in `skill_learn` (small change).

## 🔁 When to refresh
- When pstack or ECC ships a big release, or when IMPROVEMENTS.json grows by more than 10 items.
- On a repeat audit: do not collect the descriptions again; check only changes after 2026-11-16 (ECC releases: 2.2.x; pstack upstream: cursor/plugins/pstack) and the status of points 1-4 above.
- Not verified: hook quality, the real token cost of ECC after install, pstack behavior on Windows.

## 📎 Sources
- https://github.com/backnotprop/pstack
- https://github.com/michael-denyer/pstack-claude
- https://github.com/painhardcore/pstack
- https://github.com/affaan-m/everything-claude-code
