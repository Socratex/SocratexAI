# Code Workflow

## Summary

This file is the compact workflow classifier for programming projects.

Read it after `STATE.yaml` when the user gives a code-project command or asks for implementation work.

## Read Order

For ordinary code work:

1. `AGENTS.md`
2. `STATE.yaml`
3. `_PLAN.yaml`
4. smallest relevant file under `context-docs/`
5. source files in the touched ownership slice

For broad architecture, ownership, persistence, API, build, toolchain, or registry work, also read:

1. `core/PROMOTION-RULES.md`
2. `project/code/DDD-ADIV.md`
3. `project/code/GIT.md`
4. `project/code/FROZEN-LAYERS.md`

For raw user instruction buffers, also read:

1. `core/INSTRUCTION-CAPTURE.md`
2. `project/code/INSTRUCTION-CAPTURE.md`

For logs, traces, crashes, console output, and evidence-driven debugging, also read:

1. `project/code/DIAGNOSTICS.md`

## Command Classifier

`CONTINUE`: execute the next active pass from `_PLAN.yaml`.

`PLAN`: promote selected `TODO.yaml` or backlog work into explicit passes.

`BUG`: select and work the best active entry from `BUGS.yaml`.

`REVIEW`: inspect code, diff, plan, or architecture for risks first.

`AUDIT`: run `tools/audit_docs.ps1`.

`FINISH`: run quality checks, audit changed memory, update state, and report residual risk.

`COMMIT`: create a bounded Git commit with explicit paths.

`LOG`: inspect supplied diagnostics and apply the smallest source-owned fix or diagnostic step.

`DIAGNOSTICS`: summarize newest diagnostic evidence, identify the highest-leverage issue, and choose the next source-owned fix or evidence step.

`INSTRUCTIONS`: defragment raw user instructions, sort them by dependency/future-change cost, promote them into the correct layer, and clear completed intake.

## General Workflow

1. Start from the smallest state source that answers the question.
2. Identify the ownership slice.
3. Check existing scripts and project automation before doing repeatable work manually.
4. Check whether a known solution, pattern, or tool is cheaper than custom design.
5. Implement within the scoped boundary.
6. Verify with the strongest practical gate.
7. Update only the memory layers whose current truth changed.
8. Finish with concrete changed files, verification, and residual risk.

## Script-First Execution

For programming work, prefer project scripts whenever practical.

Use `tools/` helpers for pipeline tasks, package-manager scripts for ecosystem tasks, and framework CLIs for framework-native work.

Do not manually duplicate a script's behavior unless the script is unavailable, unsafe for the current scope, broken, or explicitly rejected by the user.

## Context Cost Control

Use `core/CONTEXT-COMPACTION.md` when a session becomes long, after several major passes, or after repeated retry loops.

Prefer a hard reset after compacting `STATE.yaml` and relevant `context-docs/` over carrying stale live context indefinitely.
