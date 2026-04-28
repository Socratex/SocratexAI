# Lite Option

## Summary

Use this option when the AI agent has strict context, tool, cost, or runtime limits.

## When to Use

Use Lite when:

- the AI plan has small context limits,
- the project is exploratory,
- the user wants low administrative overhead,
- the agent cannot reliably run tools,
- the project does not need full registry and audit behavior yet.

Use Standard or Pro when:

- the AI environment is enterprise-grade,
- long sessions are expected,
- code quality gates are available,
- Git and CI matter,
- the project has durable architecture or user-facing risk.

## Lite Code Files

Recommended minimum for code:

- `AGENTS.md`
- `STATE.yaml`
- `_PLAN.yaml`
- `TODO.yaml`
- `DECISIONS.yaml`

Optional:

- `CHANGELOG.yaml`
- `BUGS.yaml`

## Tradeoff

Lite reduces friction and context cost, but it weakens auditability, registry discipline, and long-session continuity.
