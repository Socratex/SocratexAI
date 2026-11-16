---
type: rules
title: AI model routing and feedback loop
description: Which model and effort to use, when to delegate or escalate, risk-based verification and the outcome log.
updated: 2026-11-16
---

# 🤖 AI model routing (Claude and Codex)

Source of truth: `core/ROUTING.json` (mirrored by `claude/agents/*.md` and `codex/agents/*.toml`, checked by `tools/tests`). A project may override tiers in its own `.ai/ROUTING.json`. Aliases, not pinned model IDs.

## 🧭 Principles
- Plan once with the expensive tier, execute with the cheaper tier, verify with a deterministic gate before trusting the result.
- Send predictable, well-specified steps to the cheapest tier that passes the gate; escalate only the ambiguous remainder.
- Escalate on evidence: a failed gate or a blocked report moves the task one tier up with the evidence; after two failed attempts on a tier, stop and move up or ask the owner.
- Review runs in a separate context from the implementation.
- Single agent by default; delegate only when handoff plus verification costs clearly less than doing it in place. One level of delegation, exact ownership, no full-history forks.
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
- Deterministic scripts and the current agent come before delegation for tiny or mechanical work.
- Effort per task type: `core/ROUTING.json` `effort_by_task_type`.

## 🧪 Verification by risk
- `tools/risk_score.py` scores the diff (never the model): sensitive paths, size, code without test changes, cheap tier or retry, learned rules. Default rules: `core/RISK-RULES.json`; a project overrides with `.ai/RISK-RULES.json`.
- LIGHT 0-2: fast gate of the changed area. STANDARD 3-5: plus the full project quality gate. FULL 6+: plus an independent `reviewer` on diff and spec and a manual-check request.
- A level may be raised by hand, never lowered below the script. Status: report-only until the owner switches it on in the project's stop gate.

## 🔁 Feedback loop
- Every finished task appends one line to the project's `audits/routing_log.jsonl`: `tools/routing_log.py --type <type> --tier <tier> --first-pass yes|no --fixes N --commit HEAD`. A fix of an earlier task's bug adds `--regression-of <ref>`.
- Weekly (or inside `usage-optimize`): `tools/routing_stats.py --out audits/routing_stats_<date>.md`. It only proposes (tier up or down per task type, lower effort, risk points per area, high-tier share), with at least 10 tasks per group. Proposals go to the owner in one form; approved ones change `ROUTING.json` or `RISK-RULES.json` after a backup. Design: `docs/ROUTER-LOOP.md`.

## 🔝 Top tier needs owner approval
Never automatic, not in unattended loops and not because a task is critical. Explain why the high tier is not enough (attempts, evidence, exact scope, expected cost and gain), ask, and wait for an explicit yes. Approval covers analysis only, not implementation, extra agents or xhigh effort.

## 🧩 Codex specifics
- Parent owns integration, task-ledger updates and finalization. Delegates never commit, push, finalize, start unattended loops or mark tasks complete.
- Tests, gates, architecture approvals and owner acceptance are never relaxed by routing.
