---
type: rules
title: Review gates
description: What to run and check before reporting a change as done.
updated: 2026-11-16
---

# 🔍 Review gates

- Non-trivial changes to domain logic, UI, input, persistence or runtime flow, and any finished refactor: run the project's quality gate (named in its INDEX.json or AGENTS.md). Not after every tiny edit during active iteration.
- Parse errors, failed lint, formatting violations and compiler or analyzer warnings are must-fix unless the owner approves an exception.
- Proof before "done": a claim that something works or passes needs fresh output of the command that proves it, from this turn, read in full (exit code, failure count). No output, no claim; say what was not run.
- A check skipped because a tool is missing: say so in the report.
- A repo tool that exists but is not found on PATH is a tooling defect: fix the bootstrap script now or record it as the next task.
- Verification depth comes from `modules/tools/scripts/risk_score.py` (LIGHT / STANDARD / FULL); FULL adds an independent reviewer (high tier, separate context, gets only diff and spec) and a manual-check request.
- Review heuristics: hard-to-trace state, hidden side effects, implicit control flow; names that do not communicate intent; comments that restate code; outdated patterns with a clear stable alternative.
- The spec is binding by default, but challenge it directly when it is weak, contradictory or likely to cause long-term harm.
