# Code Registries

## Summary

This file defines programming-only registry rules.

## Bug Registry

`BUGS.yaml` is the active bug registry.

Each active bug should have a stable number:

```yaml
bugs:
  bug_1:
    title: Short title
    status: active
    observed_behavior: TBD
    expected_behavior: TBD
    reproduction: TBD
    evidence: TBD
    current_hypothesis: TBD
    attempted_fixes: []
    verification: not_verified
    next_action: TBD
```

Rules:

- Do not renumber active bugs.
- Do not move a bug to `BUGS-SOLVED.yaml` until the user or reliable verification confirms it is resolved.
- If a fix attempt fails, update the hypothesis and prefer targeted diagnostics over broad speculative edits.
- Preserve all still-relevant evidence when merging duplicate bug entries.

## Solved Bug Registry

`BUGS-SOLVED.yaml` stores confirmed resolved bugs.

Rules:

- Preserve the original bug number.
- Include the resolved status, fix summary, and verification.
- Do not use it for active diagnostics.

## TODO Registry

`TODO.yaml` stores actionable code backlog not yet promoted into `_PLAN.yaml`.

Rules:

- Keep items future-facing.
- Prefer clear ownership and expected outcome.
- Promote only when the item becomes part of the active execution sequence.
- Do not store completed work here.

## Changelog Registry

`CHANGELOG.yaml` stores shipped user-visible behavior changes and major fixes.

Rules:

- Do not use it as a work queue.
- Do not record tiny internal churn unless it materially affects users, maintainers, architecture, or risk.
- Completed-pass history belongs here, not in `_PLAN.yaml`.

## Decision Registry

`DECISIONS.yaml` stores durable programming decisions.

Use it for:

- architecture boundaries,
- source-of-truth choices,
- persistence or schema decisions,
- public API contracts,
- significant tradeoffs,
- non-obvious constraints.

Do not use it for ordinary implementation notes.
