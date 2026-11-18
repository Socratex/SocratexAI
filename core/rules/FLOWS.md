---
type: rules
title: Task flows
description: One flow per task type (feature, bug, refactor, review, docs, big task) with research gate, closure evidence and file-based handoff for large work.
updated: 2026-11-16
---

# 🔀 Task flows

Merged value of the legacy FLOWS, WORKFLOW and TASK-WORK documents. Pick the flow by task type, then follow only that flow. Tool and model choices come from `core/rules/ROUTING.md`, gating from `core/rules/TASK-GATING.md`.

## 🧭 Pick the flow
| Task type | Read first | Do | Done when |
|---|---|---|---|
| Question | smallest source that answers it | answer, state uncertainty | answer is sourced or marked as inference |
| Feature | project state or plan, then only the owning source files | research gate, then smallest maintainable change at the owning boundary | project gate passes, closure evidence given |
| Bug | bug report, logs, state | separate observed behavior from hypothesis, reproduce or find evidence, fix the root cause at the owning boundary (no fix before the cause is named), add a diagnostic when confidence is low. After 3 failed fixes stop and question the approach or architecture. Note attempted fixes so none is repeated. Keep the logs until the owner confirms the fix | repro no longer fails, cause named (a failing test that reproduces it comes first where the project has tests) |
| Logs, crash, trace | the supplied logs | extract errors with timestamps, group by cause, then treat as a bug | likely cause named, data separated from inference |
| Refactor | code of the area plus its tests | behavior stays the same, small coherent slices, tests green after each slice | gate passes, no behavior diff |
| Docs or rules edit | the owning document, then the nearest index | edit in the owning place, no duplicate of another document | index updated if a document moved or was added |
| Review | diff or target files | findings first, then verification gaps, no unrelated rewrites | verdict plus list of defects |
| Does not fit | nothing broad yet | state the mismatch, propose goal, scope, verification, ask once | owner approved, unless small, local, reversible |

## 🔬 Research gate (before non-obvious code)
- Obvious small fix: go straight to the change.
- Non-obvious feature, architecture, bug, performance or structural task: research first.
- Skip the research when the plan already holds a researched, named mechanism for this scope.
- Check borrowed and proven options first (engine or framework feature, existing project tool, known pattern).
- Name the mechanism in one line before editing: "using X because Y, rejected Z".
- Building custom instead of borrowing: state the cost in one line.

## ✅ Closure evidence (every non-trivial task, at the end)
- What changed: the changed files, in one line.
- What was checked: the gate or tests that ran, and what did not run.
- What is left: remaining risk, open question or skipped step.
- Any tool that failed mechanically: fix the tool or the input contract, do not keep a manual workaround.
- Complex or risky diff (architecture, hot path, migration): one adversarial pass. Compare what the commit message claims with what the diff really does. Verification depth comes from `tools/risk_score.py`.
- Checks run at boundaries, after all edits of the scope. Not after every small edit.

## 🪜 Big task (file-based state, not chat memory)
Use when at least one holds:
- the needed context is above about 1500 lines of code,
- more than 3 substantial steps,
- it crosses ownership boundaries, a migration or a multi-system bug,
- it may be interrupted or outlive the context window.

How:
- Split into groups, each with one goal and one done condition. The owner approves the groups.
- Inside an approved group run the sub-tasks without asking again, until an escalation condition appears.
- Keep a task file in the project `.ai/` folder: title, source request, done criteria, micro-tasks (pending, active, done, blocked, skipped), risks, questions.
- One micro-task active at a time. Write a short result when it is done.
- After each sub-task write a handoff in the same file: files read, files changed, current hypothesis, risks and assumptions, exact next step, checks already run, whether to continue or stop for the owner.
- The next sub-task reads the handoff first, not the chat history.
- Hard reset (save state to the file, then fresh session) when:
  - retry loops repeat,
  - assumptions look stale,
  - the scope changed,
  - several big passes have run.
- Never copy the chat history into the new session. The file is the bridge.
- Status that must not be edited casually (pass or fail per item) goes in JSON. Prose notes go in Markdown.
- A fresh session starts by reading the file and running a basic check.
- When done: remove the file, or keep only durable facts in the project docs.

## 📝 Spec step (only when it pays)
- Big or risky work: write a short spec, then have the spec itself reviewed before coding (`skill spec`).
- Small, local work: no spec. Plan mode is enough.

## 🛑 Stop and ask when
- scope grows outside the approved group,
- product direction is needed,
- a check changes the plan,
- a step is destructive, external or unusually expensive.
Ask in one form with a recommended default (`core/RULES.md`, Ambiguity).
