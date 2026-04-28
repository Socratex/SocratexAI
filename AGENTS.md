# SocratexPipeline Agent Entry

Read `core/AGENT-CONTRACT.yaml` first.

If `initializer/FIRST-RUN.md` exists, this is an uninitialized skeleton. Follow `initializer/FIRST-RUN.md` before doing normal project work.

After initialization, use `STATE.md` as the compact active-state entry point.

For code projects, also read:

- `project/code/PACK.yaml`
- `project/code/WORKFLOW.yaml`
- `project/code/BRANCH-MODE.yaml` when `workflow.branch_mode` is `branch_scoped`
- `project/code/COMMANDS.yaml`
- `project/code/REGISTRIES.yaml`
- `project/code/DDD-ADIV.yaml`
- `project/code/GIT.yaml`
- `project/code/FROZEN-LAYERS.yaml`
- `project/code/INSTRUCTION-CAPTURE.yaml`
- `project/code/DIAGNOSTICS.yaml`
- `core/FILE-FORMATS.yaml`
- `core/MEMORY-MODEL.yaml`
- `core/ACTIVATION-CHECK.yaml`
- `core/UPDATE-PROTOCOL.yaml` when the user asks to update the pipeline
- `core/REMOVAL-PROTOCOL.yaml` when the user asks to remove the pipeline
- `core/TASK-WORK.yaml` for broad multi-step tasks
- `core/PROMOTION-RULES.yaml`
- `core/CONTEXT-COMPACTION.yaml`
- `core/INSTRUCTION-CAPTURE.yaml`
- `core/PROJECT-PROFILE.yaml` when `project_profile` exists
- `core/ROI-BIAS.yaml`
- `core/SCRIPT-FALLBACK.yaml`

Adapter-specific files under `adapters/` are intentionally thin pointers. The shared contract in `core/AGENT-CONTRACT.yaml` is the source of truth.
