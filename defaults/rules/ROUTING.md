---
type: rules
title: AI model routing and feedback loop
description: Which model and effort to use, when to delegate or escalate, risk-based verification and the outcome log.
updated: 2026-11-19
---

# 🤖 AI model routing

Source of truth: `defaults/ROUTING.json` (mirrored by `claude/agents/*.md` and `codex/agents/*.toml`, checked by `modules/tools/scripts/tests`). A project overrides tiers with the config key `routing.tier_overrides` (the one path; `.ai/ROUTING.json` is deprecated, `sox project check` warns). Aliases, not pinned model IDs.

## 🧭 Principles
- Plan once with the expensive tier, execute with the cheaper tier, verify with a deterministic gate before trusting the result.
- Send predictable, well-specified steps to the cheapest tier that passes the gate; escalate only the ambiguous remainder.
- Escalate on evidence: a failed gate or a blocked report moves the task one tier up with the evidence; after two failed attempts on a tier, stop and move up or ask the owner.
- Review runs in a separate context from the implementation.
- The session is a router and ALWAYS delegates (owner decision 2026-11-20, replaces the small-things exception of 2026-11-19): it plans, delegates to the tier agents (`scout`, `implementer`, `planner`, `reviewer`; for Codex as main agent `socratex_*`), then integrates and verifies. It does no search, implementation, test run, log reading or review itself. It acts directly only for: answering the owner, simple edits it already fully understands (judged by complexity, not line count), the finalizer/commit, and integrating results. Complex tasks (multi-file, several steps, design, many edge cases) are always delegated. A brief longer than the work is not an excuse; write the short brief. Start delegating at the first step of the first task of a session, not after a reminder. One level of delegation, exact ownership, no full-history forks.
- Watch the mix: high or top tier above about 15 percent of tasks means routing is too conservative.

## 🪜 Tiers
| Tier | Claude | Codex | Use for |
| --- | --- | --- | --- |
| cheap | haiku (`scout`) | Luna / medium (`socratex_quick`) | search, fact gathering, mechanical edits, log summaries |
| standard | sonnet (`implementer`, router session) | Terra / medium (`socratex_standard`) | implementation, docs and tests from a spec, queue tasks |
| high | opus (`planner`, `reviewer`) | Sol / high (`socratex_deep`, `socratex_reviewer`) | plans, architecture, unclear requirements, independent review, hard debugging, escalations |
| top | none by default | Astra | only after owner approval, see below |

- Claude: the router session stays on sonnet; opus runs as a subagent or a separate session. Delegate through `subagent_type`, not a hand-written `model`.
- A subagent starts with a clean context: give it the goal, paths, acceptance criteria and result format. Independent parts run in parallel; dependent ones in order.
- A delegate ends its report with one status: DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT or BLOCKED. BLOCKED or NEEDS_CONTEXT is the evidence that triggers escalation or a better brief; the parent never retries it unchanged.
- Deterministic scripts and the current agent come before delegation for tiny or mechanical work.
- Effort per task type: `defaults/ROUTING.json` `effort_by_task_type`.

## 🧪 Verification by risk
- `modules/tools/scripts/risk_score.py` scores the diff (never the model): sensitive paths, size, code without test changes, cheap tier or retry, learned rules. Default rules: `defaults/RISK-RULES.json`; a project overrides with `.ai/RISK-RULES.json`.
- LIGHT 0-2: fast gate of the changed area. STANDARD 3-5: plus the full project quality gate. FULL 6+: plus an independent `reviewer` on diff and spec and a manual-check request.
- A level may be raised by hand, never lowered below the script. Status: report-only until the owner switches it on in the project's stop gate.

## 🔁 Feedback loop
- Every finished task appends one line to the project's `logs/routing_log.jsonl`: `modules/tools/scripts/routing_log.py --type <type> --tier <tier> --first-pass yes|no --fixes N --commit HEAD`. A fix of an earlier task's bug adds `--regression-of <ref>`.
- Weekly (or inside `usage-optimize`): `modules/tools/scripts/routing_stats.py --out logs/routing_stats_<date>.md`. It only proposes (tier up or down per task type, lower effort, risk points per area, high-tier share), with at least 10 tasks per group. Proposals go to the owner in one form; approved ones change `ROUTING.json` or `RISK-RULES.json` after a backup. Design: `docs/ROUTER-LOOP.md`.

## 🔝 Top tier needs owner approval
Never automatic, not in unattended loops and not because a task is critical. Explain why the high tier is not enough (attempts, evidence, exact scope, expected cost and gain), ask, and wait for an explicit yes. Approval covers analysis only, not implementation, extra agents or xhigh effort.

## ⚖️ Load balancing with a second agent (optional; owner decision 2026-11-19, made opt-in 2026-11-23)
Applies only when a second agent is enabled in config (today `codex.enabled`; `sox config show`). Default is `solo`: one main agent, nothing here applies and nothing breaks. With a second agent, the main agent (the one running the session) is the lead for code and anything mathematical and the second agent is its subcontractor, so load and limits are shared. The main agent writes the brief, gives the orders, integrates and verifies. The subcontractor follows the brief and the parent's instructions, reports with a status (DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED) and never commits, pushes or finalizes.
- Standing rule (second agent enabled): the main agent splits every task before starting, and sends every part from the delegable list below to the second agent. Tests (running suites, gates, long builds), reviews and other expensive work that needs no decision go to the second agent by default; the main agent keeps decisions, code and maths. No small-things exception (owner decision 2026-11-20).
- Second agent by default (Codex via `/codex:rescue` from Claude Code; when Codex is the main agent these just stay there):
  - searching files and the repo, collecting facts across many files
  - research on the internet (sources, docs, how others solve it)
  - 2D and 3D art that is judged by look, not by maths: concept art, textures, sprites, models and renders made by hand or by a generator
  - summaries of long logs and test output, first drafts of docs and translations
  - mechanical edits from a clear pattern (rename, move, boilerplate)
  - running test suites and gates and reporting only failures; independent review of every logic diff (`/codex:review` or `socratex_reviewer`) before commit
  - expensive, non-decision work: long log analysis, broad sweeps, bulk edits
  - rescue after two failed attempts on one tier, or a second diagnosis of a hard bug
- Main agent by default: writing and changing code, algorithms, geometry and other maths (physics, collision, generation formulas), 2D and 3D graphics built on maths (procedural and generated shapes, meshes, noise, shaders, geometry), architecture and plans, integration, finalizer, commits.
- Balance by load: when one vendor is near its limit or slow, move the delegable part to the other. Never move code or maths to the second agent just to save limits.
- A second agent's result is a lead, not proof: the main agent checks it with the gate. Art is judged by the owner.
- Client or sensitive data goes to the second vendor only if the project allows it.

## 🧩 Subcontractor specifics (second agent)
- Parent owns integration, task-ledger updates and finalization. Delegates never commit, push, finalize, start unattended loops or mark tasks complete.
- Tests, gates, architecture approvals and owner acceptance are never relaxed by routing.
