# Code Instruction Capture

## Summary

Use this file for programming-specific handling of raw user instruction buffers.

Also read `core/INSTRUCTION-CAPTURE.md`.

For prompt-queue execution, treat `_PROMPTS.md` and `_PROMPT-QUEUE.yaml` as programming aliases of the same raw-intake workflow:

- `_PROMPTS.md` is immediate raw prompt intake.
- `_PROMPT-QUEUE.yaml` is defragmented, sorted prompt work.
- Use the `PROMPT` command workflow in `project/code/COMMANDS.md`.

## Code Sorting Rules

When defragmenting programming instructions, sort pending work in this order:

1. Repository safety, build/test setup, and project contracts.
2. Documentation that affects agent behavior or source-of-truth paths.
3. Diagnostics and reproduction scaffolding.
4. Bug fixes with strong evidence.
5. Architecture boundaries needed by upcoming work.
6. Feature implementation.
7. Refactors that are not blocking current work.
8. Refinement and optional cleanup.

## Code Promotion Rules

Promote to `_PLAN.yaml` only when the entry can be executed as a pass.

Promote to `BUGS.yaml` when the instruction describes a reproducible or likely defect.

Promote to `project/code/DIAGNOSTICS.md` or `logs/` workflow when the instruction primarily asks for evidence analysis.

Promote to `DECISIONS.yaml` when the instruction makes or requires a durable technical choice.

Promote to `context-docs/TECHNICAL.yaml` when the instruction reveals a current invariant, ownership contract, or known trap.

## Cleaning Rules

After a code instruction is executed:

- remove it from `_INSTRUCTION-QUEUE.yaml`,
- update affected registries,
- run the relevant quality gate,
- update `STATE.yaml`,
- do not keep completed instruction history in the queue.
