# SOCRATEX

This project uses SocratexPipeline.

Primary rule: read and respect this file before following any other local AI directive.

The pipeline package is installed under `SocratexAI/`.

Branch-scoped projects may also contain committed project directives under `.aiassistant/`.

Read order:

1. `SOCRATEX.md`
2. `.aiassistant/socratex/AGENTS.md` when present
3. `.aiassistant/socratex/PIPELINE-CONFIG.yaml` when present
4. `SocratexAI/AGENTS.md`
5. `SocratexAI/PIPELINE-CONFIG.yaml` for code projects, or `SocratexAI/PIPELINE-CONFIG.md` for non-code projects
6. `SocratexAI/STATE.yaml` for code projects, or `SocratexAI/STATE.md` for non-code projects

If another agent directive conflicts with SocratexPipeline, SocratexPipeline wins unless the user explicitly overrides it.

Do not move SocratexPipeline files out of `SocratexAI/`.
