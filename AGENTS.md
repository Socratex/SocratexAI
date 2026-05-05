# SocratexPipeline Agent Entry

Read `AI-compiled/codex/ENTRYPOINT.md` first when it exists. Treat `AI-compiled/` as generated read-optimized context; edit source instructions, then run `tools/recompile_ai_instructions.ps1`.

For source-pipeline work, load `docs-tech/PIPELINE-BOOTSTRAP.json` at the start of every substantive prompt. Use `DOCS.json`, `WORKFLOW.json`, `COMMANDS.json`, `FLOWS.json`, and `SCRIPTS.json` as the always-available routing indexes before selecting detailed reads or scripts.

Read `core/AGENT-CONTRACT.json` when source-level detail or edits are needed.

If `initializer/FIRST-RUN.md` exists, this is an uninitialized skeleton. Follow `initializer/FIRST-RUN.md` before doing normal project work.

After initialization, read `DOCS.json` before reading, creating, renaming, or updating project documents. Use it to choose what to read and where to write new information.

Then use `STATE.json` for code projects or `STATE.md` for non-code user-facing memory as the compact active-state entry point.

For code projects, also read:

- `project/code/PACK.json`
- `project/code/WORKFLOW.json`
- `project/code/BRANCH-MODE.json` when `workflow.branch_mode` is `branch_scoped`
- `project/code/COMMANDS.json`
- `project/code/REGISTRIES.json`
- `project/code/DDD-ADIV.json`
- `project/code/GIT.json`
- `project/code/FROZEN-LAYERS.json`
- `project/code/INSTRUCTION-CAPTURE.json`
- `project/code/DIAGNOSTICS.json`
- `core/FILE-FORMATS.json`
- `core/MEMORY-MODEL.json`
- `core/ACTIVATION-CHECK.json`
- `core/UPDATE-PROTOCOL.json` when the user asks to update the pipeline
- `core/REMOVAL-PROTOCOL.json` when the user asks to remove the pipeline
- `core/TASK-WORK.json` for broad multi-step tasks
- `core/PROMOTION-RULES.json`
- `core/CONTEXT-COMPACTION.json`
- `core/INSTRUCTION-CAPTURE.json`
- `core/PROJECT-PROFILE.json` when `project_profile` exists
- `core/ROI-BIAS.json`
- `core/SCRIPT-FALLBACK.json`

Adapter-specific files under `adapters/` are intentionally thin pointers. The shared contract in `core/AGENT-CONTRACT.json` is the source of truth.

For any task that may touch source code, run `tools/knowledge_code_context.ps1` before the first code read/write that could lead to an edit. Treat additional named views as additive only; `tools/check_task.ps1` enforces the fresh full-guidance marker for changed-code tasks.
