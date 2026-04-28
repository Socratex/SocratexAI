# Code Commands

## Summary

This file defines programming-only commands for the code project pack.

These commands apply only when `project/code` is active.

Before executing any command manually, check whether a matching script exists in `tools/` or the project's package/task runner and use it when practical.

## CONTINUE

Execute the next active pass from `_PLAN.yaml`.

Order:

1. Read `STATE.yaml`.
2. Read `_PLAN.yaml`.
3. Select the first active pass.
4. Read only the smallest relevant context files.
5. Implement the scoped change.
6. Run the relevant quality gate.
7. Update `STATE.yaml`.
8. Remove completed passes from `_PLAN.yaml`.
9. Record shipped user-visible changes or major fixes in `CHANGELOG.yaml`.

If no active pass exists, propose the next code target from `TODO.yaml`; do not silently add it to `_PLAN.yaml` unless the workflow or user authorizes planning.

## PLAN

Promote selected code backlog into executable passes.

Each pass must define:

- goal,
- touched domains,
- scope boundaries,
- expected outcome,
- verification,
- what it intentionally does not do yet.

## BUG

Work from `BUGS.yaml`.

Order:

1. Read `BUGS.yaml`.
2. Select the highest-leverage active bug using reproduction likelihood, current project focus, diagnostic readiness, and future-change cost.
3. Apply the smallest source-owned fix or diagnostic improvement.
4. Run the relevant quality gate.
5. Update the bug entry with observation, hypothesis, attempted fix, and verification.
6. Ask for confirmation before moving the bug to `BUGS-SOLVED.yaml`.

Never renumber active bugs unless explicitly requested.

## REVIEW

Review code, plan, or diff as a reviewer.

Lead with:

- bugs,
- regressions,
- security risks,
- data-loss risks,
- missing verification,
- unclear ownership.

Keep findings tied to concrete files, functions, contracts, or behavior.

## AUDIT

Run the code-project document consistency audit.

Default command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_docs.ps1
```

Use `-Strict` when warnings should fail the audit.

Use `-Initialized` after first-run setup.

## FINISH

Close the current programming task.

Order:

1. Run the strongest practical quality gate.
2. Run `tools/audit_docs.ps1` when project memory changed.
3. Update `STATE.yaml`.
4. Update `_PLAN.yaml` if passes were completed or reshaped.
5. Update `CHANGELOG.yaml` for shipped behavior or major fixes.
6. Report changed files and unverified areas.

Default helper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/finish_task.ps1
```

Use `-Quality` to run the detected or configured quality gate.

## COMMIT

Create a bounded source-control commit when the project uses Git.

Rules:

- stage only explicit paths,
- avoid generated or temporary files unless intentionally part of the change,
- do not commit unrelated user changes,
- mention skipped verification.

Default helper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/commit_task.ps1 -Message "<message>" -Paths <explicit paths>
```

## LOG

Analyze a supplied diagnostic log, crash log, trace, test output, or runtime dump.

Order:

1. Identify the freshest relevant evidence.
2. Extract the highest-leverage current error.
3. Form one concrete hypothesis.
4. Apply the smallest source-owned fix or add targeted diagnostics.
5. Run the relevant quality gate.
6. Update the related registry entry if one exists.

## DIAGNOSTICS

Analyze diagnostic evidence from `logs/` or a supplied file.

Order:

1. Read `project/code/DIAGNOSTICS.md`.
2. Ensure root-level `logs/` exists if diagnostics will be collected.
3. Run `tools/log_summary.ps1 -Description "<description>"` when practical.
4. Inspect the freshest relevant evidence.
5. Identify the smallest source-owned fix or the smallest useful diagnostic addition.
6. Run the relevant quality gate.
7. Update `BUGS.yaml`, `ISSUES.yaml`, `STATE.yaml`, or `context-docs/TECHNICAL.yaml` only when current truth changed.

## INSTRUCTIONS

Defragment raw user instruction files.

Order:

1. Read `core/INSTRUCTION-CAPTURE.md`.
2. Read `project/code/INSTRUCTION-CAPTURE.md`.
3. Inspect `_INSTRUCTIONS.md` first.
4. Merge duplicates and split separable work into `_INSTRUCTION-QUEUE.yaml`.
5. Promote executable passes into `_PLAN.yaml` only when they meet the pass contract.
6. Move bugs, decisions, diagnostics, and context facts into the correct registry.
7. Clear `_INSTRUCTIONS.md` after successful defragmentation.
8. Remove completed entries from `_INSTRUCTION-QUEUE.yaml` after execution.
