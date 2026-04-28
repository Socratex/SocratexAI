# Memory Model

## Active State

The active state is the first file an agent reads after initialization.

It should stay short:

- current objective,
- current pass,
- next action,
- blockers,
- risks,
- non-regression reminders.

## Branch-Scoped Active State

Branch-scoped active state is local working memory for one Git branch.

Use it when the project config sets `workflow.branch_mode` to `branch_scoped`.

It normally lives under `ignored/ai-socratex/<branch>-STATE.md`.

It may use the user's prompt language because it is local-only working memory.

It stores branch facts:

- findings,
- root causes,
- changes made,
- verification,
- current blockers,
- durable findings that may need promotion.

It should not replace durable project memory.

## Plan

The plan contains only active and future execution passes.

It is not history.

In branch-scoped mode, the branch plan lives under `ignored/ai-socratex/<branch>-PLAN.md`.

It contains next steps only and should be updated continuously during the branch.

## Backlog

The backlog contains valuable work that is not yet committed to the active execution sequence.

## Decisions

The decision log records durable choices that future agents should not silently reverse.

Record:

- decision,
- context,
- rationale,
- consequences,
- verification or revisit condition.

## Context Capsules

Context capsules store compact, current-state knowledge.

Use them for:

- invariants,
- ownership contracts,
- known traps,
- source-of-truth paths,
- performance or process heuristics.

Do not use them for:

- history,
- scratch notes,
- duplicated backlog,
- speculative future roadmaps.
