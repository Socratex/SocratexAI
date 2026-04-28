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
- `core/PROJECT-PROFILE.md` when `project_profile` exists
- `core/ROI-BIAS.md`
- `core/SCRIPT-FALLBACK.md`
- `core/TASK-WORK.md` for broad multi-step tasks
- `project/code/WORKFLOW.md`
- `project/code/BRANCH-MODE.md` when `workflow.branch_mode` is `branch_scoped`
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
- `PROMPT`: execute or defragment prompt intake.
- `INSTRUCTIONS`: defragment raw user instruction intake.

## Helper Scripts

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_snapshot.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/finish_task.ps1 -Quality
powershell -NoProfile -ExecutionPolicy Bypass -File tools/commit_task.ps1 -Message "<message>" -Paths <explicit paths>
powershell -NoProfile -ExecutionPolicy Bypass -File tools/log_summary.ps1 -Description "<diagnostic description>"
python tools/check_runtime.py --root-key runtime_status
powershell -NoProfile -ExecutionPolicy Bypass -File tools/init_task_work.ps1 -Title "<task>" -SourceRequest "<request>"
```

## File Formats

Programming projects use YAML and JSON for standardized project memory, registries, diagnostics, configuration, indexes, and AI-readable structured documents.

Markdown in programming projects is reserved for scratch intake such as `_INSTRUCTIONS.md`, temporary notes, rough drafts, and short human-facing docs.

Branch-scoped mode also uses Markdown for local prompt-language working files under `ignored/ai-socratex/`.

## Project Profile

`PIPELINE-CONFIG.yaml` stores `project_profile`.

The agent uses it to filter known solutions. Legacy and low-test projects bias toward characterization tests, seams, adapters, and minimal-invasive modernization. Greenfield projects can bias toward cleaner DDD-ADIV structure and framework-native foundations.

## Branch-Scoped Mode

When `workflow.branch_mode` is `branch_scoped`, committed directives live under `.aiassistant/` while local branch memory lives under `ignored/ai-socratex/`.

The agent starts each session by detecting the branch and reading or creating `<branch>-STATE.md` and `<branch>-PLAN.md`.

## ROI Picks

Reviews, plans, and finish reports should include one to three ROI Picks when recommendations remain.

ROI Picks rank work by value axes, cost axes, profile fit, and why the improvement is worth doing now.

## Script Fallback

Before silently bypassing a script, the agent follows `core/SCRIPT-FALLBACK.md`.

Missing runtimes should be reported as setup issues with install hints before manual fallback.

## Broad Task Work

For broad multi-step tasks, the agent should create temporary task work at `docs-tech/cache/current_task.yaml`, track micro-task status during execution, then delete it or promote only durable facts.

For moving items between structured YAML documents, the agent should use `tools/doc_item_migrate.ps1` instead of manual editing.

## Quality Gate

`tools/run_quality_gate.ps1` auto-detects common ecosystems.

For serious projects, pass an explicit command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1 -Command "npm test"
```
