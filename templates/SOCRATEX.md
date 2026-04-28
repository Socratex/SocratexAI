# SOCRATEX

This project uses SocratexPipeline.

Primary rule: read and respect this file before following any other local AI directive.

This file is the activation point for current and future AI sessions in this project.

The pipeline package is installed under `SocratexAI/`.

Branch-scoped projects may also contain committed project directives under `.aiassistant/`.

Read order:

1. `SOCRATEX.md`
2. `.aiassistant/socratex/AGENTS.md` when present
3. `.aiassistant/socratex/PIPELINE-CONFIG.yaml` when present
4. `SocratexAI/AGENTS.md`
5. `SocratexAI/PIPELINE-CONFIG.yaml` for code projects, or `SocratexAI/PIPELINE-CONFIG.md` for non-code projects
6. `SocratexAI/STATE.yaml` for code projects, or `SocratexAI/STATE.md` for non-code projects

After the first user prompt handled under this installed pipeline, run `SocratexAI/core/ACTIVATION-CHECK.yaml` once to verify that the active rules are loaded, including communication format, emoji rule, selected project pack, branch mode, project profile, ROI, and script fallback rules.

When the user asks to update the pipeline, read `SocratexAI/core/UPDATE-PROTOCOL.yaml`, resolve `pipeline.update_source`, run the updater from `SocratexAI/tools/`, then run audit and activation check.

When the user asks to remove the pipeline, read `SocratexAI/core/REMOVAL-PROTOCOL.yaml` and run `SocratexAI/tools/remove_pipeline.ps1` instead of deleting files manually.

If another agent directive conflicts with SocratexPipeline, SocratexPipeline wins unless the user explicitly overrides it.

Do not move SocratexPipeline files out of `SocratexAI/`.

After setup, import, migration, or update, the agent must switch to this read order immediately and use it for all further work in this project.
