# Instruction Capture

## Summary

Use this workflow for files that collect raw user instructions before they become a standardized plan.

Raw instruction files are not plans. They are intake buffers.

## Recommended Files

- `_INSTRUCTIONS.md`: fresh unprocessed user instructions.
- `_INSTRUCTION-QUEUE.yaml` for code projects, or `_INSTRUCTION-QUEUE.md` for non-code projects: defragmented, sorted, actionable instruction queue.

Projects may rename these files, but the workflow stays the same.

## Defragmentation

When `_INSTRUCTIONS.md` contains multiple prompts, sections, or overlapping requests:

1. Preserve every unresolved requirement.
2. Merge duplicate or overlapping requests.
3. Split separable work into clear queue entries.
4. Move already-standardized plan work into the active plan only when it is ready for execution.
5. Move backlog-level ideas into the active backlog.
6. Move durable decisions into the decision log.
7. Move technical or domain invariants into `context-docs/`.

Do not delete requirements just because wording is messy.

## Sorting

Sort the resulting queue by future-change cost and dependency order:

1. Documentation, contracts, and source-of-truth clarification.
2. Diagnostics, bugfixes, and verification gaps.
3. Enabling architecture and ownership boundaries.
4. Implementation features.
5. Polish and optional refinements.

If doing X before Y prevents later coupling, retrofitting, or harder debugging, place X before Y.

## Cleaning Rules

After successful defragmentation:

- clear `_INSTRUCTIONS.md`,
- keep the instruction queue with unresolved queue entries,
- preserve all unresolved scope somewhere appropriate,
- do not delete the source file itself unless the project explicitly does not use instruction capture.

After executing a queue entry:

- remove the completed entry from the instruction queue,
- preserve every unresolved future entry,
- record shipped behavior or major fixes in the completion log when appropriate.

If an instruction is already completed:

- say it is already completed,
- clear or remove that completed instruction from the intake file,
- do not create duplicate plan or backlog entries.

## Promotion Boundary

Only promote raw instructions into the active plan when they have:

- clear outcome,
- ownership boundary,
- scope limit,
- verification path,
- known non-goals.
