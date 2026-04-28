# Code Projects

## Summary

This guide explains the programming-specific SocratexPipeline workflow.

## Required Reads

For code projects, the agent reads:

- `core/AGENT-CONTRACT.md`
- `core/FILE-FORMATS.md`
- `core/PROMOTION-RULES.md`
- `core/CONTEXT-COMPACTION.md`
- `core/INSTRUCTION-CAPTURE.md`
- `project/code/WORKFLOW.md`
- `project/code/COMMANDS.md`
- `project/code/REGISTRIES.md`
- `project/code/DDD-ADIV.md`
- `project/code/GIT.md`
- `project/code/FROZEN-LAYERS.md`
- `project/code/INSTRUCTION-CAPTURE.md`
- `project/code/DIAGNOSTICS.md`

## Main Commands

- `CONTINUE`: execute the next active pass.
- `PLAN`: promote backlog into executable passes.
- `BUG`: work the best active bug.
- `REVIEW`: inspect risk and defects first.
- `AUDIT`: check document consistency.
- `FINISH`: run checks and close the task.
- `COMMIT`: stage explicit paths and commit.
- `DIAGNOSTICS`: inspect logs and evidence.
- `INSTRUCTIONS`: defragment raw user instruction intake.

## Helper Scripts

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_snapshot.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/finish_task.ps1 -Quality
powershell -NoProfile -ExecutionPolicy Bypass -File tools/commit_task.ps1 -Message "<message>" -Paths <explicit paths>
powershell -NoProfile -ExecutionPolicy Bypass -File tools/log_summary.ps1 -Description "<diagnostic description>"
```

## File Formats

Programming projects use YAML and JSON for standardized project memory, registries, diagnostics, configuration, indexes, and AI-readable structured documents.

Markdown in programming projects is reserved for scratch intake such as `_INSTRUCTIONS.md`, temporary notes, rough drafts, and short human-facing docs.

## Quality Gate

`tools/run_quality_gate.ps1` auto-detects common ecosystems.

For serious projects, pass an explicit command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1 -Command "npm test"
```
