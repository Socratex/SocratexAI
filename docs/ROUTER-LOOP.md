---
type: design
title: Router Loop
description: Risk-based verification levels (LIGHT/STANDARD/FULL) and a learning loop that tunes model routing from logged task outcomes.
updated: 2026-11-16
---

# Design: risk-based verification + router learning loop (state 2026-11-16)

Status (2026-11-16): **steps 1, 2 and 4 are implemented in report-only mode** (`modules/tools/scripts/risk_score.py`, `modules/tools/scripts/routing_log.py`, `modules/tools/scripts/routing_stats.py`, default rules in `defaults/RISK-RULES.json`; a project can override them with `.ai/RISK-RULES.json`). The risk level is only reported for now. Step 3 (wiring the levels into the project's stop gate) waits for owner review after about a week of comparisons. The log is a separate script called by the router, not part of the project's finalizer. This closes two gaps against the scheme "router -> model + effort -> verify by risk -> escalate / learned".

Before this design: the router ran on fixed rules (`defaults/ROUTING.json`, the model tiers), escalation on evidence worked, but verification had one level "at discretion" and task outcomes did not flow back to the router.

## 1. Risk-based verification (LIGHT / STANDARD / FULL)

**Principle:** a script computes the verification level from the diff, not the model. Deterministic, cheap, repeatable.

### 1.1 Risk score (0-10)

`modules/tools/scripts/risk_score.py` reads `git diff --numstat` of the changed paths and sums points according to the rules file (`defaults/RISK-RULES.json`, or the project override `.ai/RISK-RULES.json`):

| Signal | Points (initial, to be calibrated) |
|---|---|
| Sensitive path: game/data saves, auth, payments, build, hooks, settings, permissions | +4 |
| Core path (architecture, runtime flow, world generation) | +2 |
| Size: more than 150 changed lines or more than 5 files | +2 |
| No tests for the changed area | +2 |
| Written by the cheap tier, or this is the second attempt after a failure | +1 |
| Path with a regression history (from the loop, section 2) | +1..+3 |
| Documentation / text only | -3 (minimum 0) |

### 1.2 Levels

| Score | Level | What runs |
|---|---|---|
| 0-2 | **LIGHT** | fast gate of the changed area (compile + area tests), executor self-check |
| 3-5 | **STANDARD** | + the project's full quality gate |
| 6+ | **FULL** | + independent `reviewer` (high tier, separate context, gets only diff + spec) + a request for a manual test / playtest |

Rules: the level can be raised manually, never lowered below the script's score; on a gate failure escalate as today (a tier up, with evidence); the report to the owner contains one line "verification: LEVEL (score)".

### 1.3 Where it plugs in

- `modules/tools/scripts/risk_score.py` (reads the diff + rules file, prints JSON `{score, level, reasons}`).
- The project's stop gate: runs the gate according to the level instead of a constant (step 3, pending).
- The finalizer / router report: writes the level and score to the log from section 2.
- A rule in the directives index: "finishing a code change -> verification level from `risk_score`".

## 2. Learning loop (LEARNED / FEEDBACK)

**Principle:** every task outcome leaves one data row; once a week a script computes statistics and **proposes** routing changes. The router never changes itself: every change to `defaults/ROUTING.json` / the risk rules goes to the owner by form, after a backup.

### 2.1 Outcome log (this is also the "quality diary", item 27 of `IMPROVEMENTS.json`)

File `audits/routing_log.jsonl` in each project, one row per task, appended by `modules/tools/scripts/routing_log.py` (called by the router):

```json
{"date":"2026-11-16","task":"a1b2c3","type":"implementation","domain":"ui","tier":"standard","agent":"implementer","effort":"medium","risk":4,"level":"STANDARD","first_pass":true,"fixes":0,"escalated":false,"regression_of":null}
```

- `type` from a small fixed list: search, implementation, refactor, docs, debug, review, plan.
- `regression_of`: when a bug later appears in that area, the fix entry points to the source task (manually, or via the commit that touched it).

### 2.2 Analysis (`modules/tools/scripts/routing_stats.py`, weekly or inside a usage-optimize run)

| Signal (minimum 10 tasks in the group type + tier) | Proposal |
|---|---|
| Cheap/standard tier: first_pass >= 90% | keep, or move this type one tier down |
| Tier: first_pass < 70% or frequent escalations | default to a tier up for this type |
| High tier > 15% of tasks | routing too conservative, review the types |
| Regression after LIGHT/STANDARD on a path | +1 risk point for that path in the risk rules |
| FULL with no defects found over 10+ tasks on a path | -1 risk point (cheaper verification) |
| Effort: same result at lower effort | lower the effort for the type |

### 2.3 Closing the loop

1. The script writes a report `audits/routing_stats_<date>.md` (numbers + proposals).
2. The router shows 3-6 proposals in one form.
3. After "yes": backup, change `defaults/ROUTING.json` / the risk rules, run the consistency test of agents against the file, add an entry to `AI-PRACTICES.md`.

## 3. Effort AUTO

Effort goes into `defaults/ROUTING.json` as a field per task type (for example search=low, implementation=medium, debug=high) and is set at delegation. The loop from section 2 calibrates it the same way as the tier. **[?]** check whether the Claude agent frontmatter accepts `effort`; if not, effort applies only on the Codex side and to sessions.

## 4. Implementation order

1. Outcome log written by the router script (collects data immediately, changes no behavior). Done.
2. `risk_score.py` + risk rules in "report only" mode for a week (compare with manual judgement). Done, running.
3. Wire the levels into the project's stop gate. Pending owner review after about a week.
4. `routing_stats.py` after collecting about 30-50 entries. Done (report-only).

## 5. Risks

- Too little data: thresholds apply only with at least 10 tasks in a group, otherwise no proposal.
- Gaming the metric (the model understates risk): the score is computed by the script from the diff, the model does not supply it.
- The loop destabilises routing: changes only with consent, after a backup, one step at a time.
