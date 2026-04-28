# SocratexPipeline Agent Entry

Read `core/AGENT-CONTRACT.md` first.

If `initializer/FIRST-RUN.md` exists, this is an uninitialized skeleton. Follow `initializer/FIRST-RUN.md` before doing normal project work.

After initialization, use `STATE.md` as the compact active-state entry point.

For code projects, also read:

- `project/code/PACK.md`
- `project/code/WORKFLOW.md`
- `project/code/BRANCH-MODE.md` when `workflow.branch_mode` is `branch_scoped`
- `project/code/COMMANDS.md`
- `project/code/REGISTRIES.md`
- `project/code/DDD-ADIV.md`
- `project/code/GIT.md`
- `project/code/FROZEN-LAYERS.md`
- `project/code/INSTRUCTION-CAPTURE.md`
- `project/code/DIAGNOSTICS.md`
- `core/FILE-FORMATS.md`
- `core/MEMORY-MODEL.md`
- `core/PROMOTION-RULES.md`
- `core/CONTEXT-COMPACTION.md`
- `core/INSTRUCTION-CAPTURE.md`
- `core/PROJECT-PROFILE.md` when `project_profile` exists
- `core/ROI-BIAS.md`
- `core/SCRIPT-FALLBACK.md`

Adapter-specific files under `adapters/` are intentionally thin pointers. The shared contract in `core/AGENT-CONTRACT.md` is the source of truth.
