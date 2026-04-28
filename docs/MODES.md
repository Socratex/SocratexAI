# Operating Modes

## Summary

SocratexPipeline supports Lite, Standard, and Enterprise operating modes.

## Lite

Use Lite when AI context, tool use, budget, or reliability is limited.

Lite favors fewer files and lower ceremony.

Recommended code files:

- `AGENTS.md`
- `STATE.yaml`
- `_PLAN.yaml`
- `TODO.yaml`
- `DECISIONS.yaml`

## Standard

Use Standard for normal coding-agent work.

Standard keeps registry discipline, quality gates, and context continuity without maximal ceremony.

## Enterprise

Use Enterprise for high-context, high-tooling, long-session projects.

Enterprise favors:

- full registries,
- diagnostics workflow,
- document audit,
- Git safety,
- context compaction,
- frozen-layer protocol,
- stricter verification.
