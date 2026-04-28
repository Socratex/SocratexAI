# Context Compaction

## Summary

Use context compaction to keep long AI-assisted sessions accurate and cheap.

## When to Recommend a Hard Reset

Recommend a hard reset when:

- the session has run through several major passes,
- the same subsystem has gone through repeated retry loops,
- broad architecture or ownership changed,
- the live chat contains stale assumptions,
- the agent has to reread too much to continue safely,
- the next task is a new major scope.

## Before Reset

Refresh the compact project memory:

1. active state file: current objective, current pass, next action, blockers, risks.
2. relevant `context-docs/`: current contracts, invariants, source-of-truth paths, known traps.
3. active plan file: only active and future passes.
4. decision log: durable choices only.

## What Not to Store

Do not copy large history into compact memory.

Do not duplicate the same plan across state, plan, backlog, and `context-docs/`.

Do not store scratch notes in `context-docs/`.

## Reset Message

Use a short factual recommendation:

`A hard reset is recommended now because the session has accumulated broad context and the next task is a new scope. STATE/context-docs have been refreshed for continuation.`
