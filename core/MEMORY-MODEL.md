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

## Plan

The plan contains only active and future execution passes.

It is not history.

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

