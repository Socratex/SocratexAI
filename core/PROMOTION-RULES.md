# Promotion Rules

## Summary

Project memory should move through explicit layers instead of being duplicated across files.

## BACKLOG to PLAN

Promote backlog into the plan only when the work becomes part of the active execution sequence.

Before promotion, ensure the item has:

- clear outcome,
- ownership boundary,
- known dependencies,
- verification path,
- reason it should happen now.

After promotion, preserve unresolved scope in the active plan file and remove or shrink the source backlog item so the same work is not tracked twice.

For code projects, use YAML project memory such as `_PLAN.yaml`, `TODO.yaml`, and `DECISIONS.yaml`.

For non-code user-facing project memory, Markdown remains acceptable unless the file is an AI-only mega-file.

## PLAN to STATE

The active state file should contain only the compact active checkpoint.

Move from the active plan file to the active state file only as:

- current active pass,
- next action,
- blocker,
- risk,
- non-regression reminder.

Do not copy full pass definitions into active state.

## PLAN to CHANGELOG

When a pass is completed and it shipped meaningful functionality, fixed a major issue, or changed durable behavior, record the outcome in the completion log.

Then remove the completed pass from the active plan file.

Do not keep completed-pass history in the active plan file.

## PLAN or BACKLOG to DECISIONS

Move information to the decision log when it becomes a durable choice that future work should respect.

Record:

- decision,
- context,
- rationale,
- consequences,
- verification or revisit condition.

Do not record every task as a decision.

## PLAN or IMPLEMENTATION to context-docs

Use `context-docs/` only for current technical or domain memory that prevents repeated rediscovery.

Valid content:

- invariants,
- ownership contracts,
- source-of-truth paths,
- known traps,
- performance heuristics,
- debugging heuristics.

Invalid content:

- changelog history,
- scratch notes,
- duplicated backlog,
- broad future roadmap,
- implementation diary.

## STATE to PLAN

If active state contains future work that is larger than the next immediate action, demote it back to the active plan or backlog.

Active state must stay small enough to read first in every session.

## DECISIONS to PLAN

A decision can create follow-up work, but the work belongs in the active plan or backlog, not inside the decision entry.
