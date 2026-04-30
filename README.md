# SocratexPipeline

SocratexPipeline is a modular project runtime for long-running AI-assisted work.

It is not a prompt pack. It gives AI agents a durable operating layer: state, plans, registries, diagnostics, quality gates, update rules, and safe directive routing across long projects.

## Why

AI agents often lose context, mix backlog with active work, forget verification, overwrite local conventions, or bury project rules inside one giant instruction file.

SocratexPipeline fixes that by installing one root control file and a structured `SocratexAI/` package.

Installed projects use this layout:

- root `SOCRATEX.md` is the only required root control file,
- `SocratexAI/` contains pipeline files, tools, packs, state, registries, templates, and docs,
- branch-scoped code projects may also use `.aiassistant/` for committed project directives and `ignored/ai-socratex/` for local branch memory,
- existing AI directive files should only point to `SOCRATEX.md`.

## Public Bootstrap

To use this from any AI agent, point the agent at `PUBLIC-BOOTSTRAP.md` and say:

```text
use this link to setup pipeline <link-to-PUBLIC-BOOTSTRAP.md>
```

The agent should detect the language of that setup request, ask the pipeline language question first, then continue the setup questions in the chosen language.

After setup succeeds, the agent should switch to the installed project pipeline immediately and use root `SOCRATEX.md` as the starting point for the current and future sessions.

After the first prompt handled under the installed pipeline, the agent should run the activation check to verify communication format, emoji rules, config, project pack, and workflow-specific rules.

## Quick Install Prompt

After publishing this repository, use the raw GitHub link:

```text
use this link to setup pipeline https://raw.githubusercontent.com/<user>/<repo>/main/PUBLIC-BOOTSTRAP.md
```

The target project should end up with:

```text
SOCRATEX.md
SocratexAI/
```

Branch-scoped code projects may also include:

```text
.aiassistant/
ignored/ai-socratex/
```

## Structure

- `core/` contains shared project-memory, planning, execution, and quality contracts.
- `project/` contains modular project packs.
- `adapters/` contains thin adapter files for specific agents.
- `initializer/` contains the first-run setup workflow.
- `templates/` contains source templates copied into initialized projects.
- `tools/` contains helper scripts.
- `temp/trash/` receives first-run initializer files after setup.

When installed into another project, this source structure is copied under `SocratexAI/`.

## First Run

Give the agent this project and ask it to follow `AGENTS.md`.

On first run, the agent should:

1. Read `initializer/FIRST-RUN.md`.
2. Ask the initialization questions.
3. Select the needed project packs.
4. Remove unused packs and templates.
5. Create the project-local files from `templates/`.
6. Move `initializer/` into `temp/trash/initializer/`.
7. Create `SocratexAI/DOCS.yaml` as the document role index.
8. Update the active state file under `SocratexAI/` with the initialized project state.
9. Switch the current session to root `SOCRATEX.md`.

For code projects, the agent should also read `project/code/COMMANDS.yaml`, `project/code/REGISTRIES.yaml`, `project/code/DDD-ADIV.yaml`, and `core/PROMOTION-RULES.yaml`.

Code projects can store `project_profile`, `runtime_status`, and `workflow.branch_mode` in `PIPELINE-CONFIG.yaml`.

The agent uses `project_profile` to filter known solutions, `ROI-BIAS.md` to rank recommendations, and `SCRIPT-FALLBACK.md` when tools cannot run.

PowerShell 7 (`pwsh`) is the preferred automation runtime. During setup, the agent should check it first, run `tools/install_powershell.ps1` when missing, and recommend lite/no-tools mode, a supported host/container, or porting scripts if the target system cannot support PowerShell.

If the AI environment is limited, read `tools/lite-option/README.md` before selecting artifacts.

User-facing guides:

- `docs/GETTING-STARTED.md`
- `docs/CODE-PROJECTS.md`
- `docs/MODES.md`
- `docs/IMPORT-EXISTING-PROJECT.md`

Format contract:

- code projects use YAML/JSON for standardized project memory,
- non-code projects use Markdown for user-facing memory such as state, plan, backlog, decisions, issues, journal, and review,
- YAML/JSON is used for files managed only by the agent, such as `DOCS.yaml`, config, queues, caches, indexes, agent-only context docs, diagnostics, and generated summaries,
- Markdown is also used for forced agent entrypoints, user scratches, prompt drafts, final prose artifacts, public docs, and adapter entrypoints.

## Pack Model

The core is domain-neutral. A project chooses one or more project packs:

- `project/code` for software projects.
- `project/generic` for non-code execution projects.
- `project/personal` for life-management and personal operations.
- `project/creative` for music, writing, design, media, and artistic projects.

Project packs extend the core. They should not duplicate the core.

## Adapter Model

Adapters must stay thin. Each adapter points the agent to the common shared contract instead of carrying its own full instruction set.

## Update, Upgrade, Migrate

- `SocratexAI/tools/update_pipeline_from_link.ps1`: public user update from a latest pipeline source.
- `SocratexAI/tools/reinitialize_pipeline.ps1`: missing-only reinitialization after setup or update.
- `SocratexAI/tools/remove_pipeline.ps1`: remove the installed pipeline through a bounded remover.
- `SocratexAI/tools/upgrade_from_riftbound.ps1`: maintainer upgrade from the active gamedev source pipeline.
- `SocratexAI/tools/migrate_ai_pipeline.ps1`: migrate an existing AI pipeline into SocratexPipeline.

Structured YAML tools apply to every project type, including non-code projects, for agent-only structured YAML files. Use `doc_read`, `doc_keys`, `doc_item_insert`, `doc_item_bulk_insert`, `doc_item_move`, and `doc_item_migrate` whenever practical.

Document edit scripts are transactional by default: they should own the write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output. Agents should not compose manual read/edit/normalize/cache/check queues after a successful document edit tool.

When asking an agent to update an installed pipeline, it should follow `SocratexAI/core/UPDATE-PROTOCOL.yaml`, resolve `pipeline.update_source`, run the updater, reinitialize newly introduced missing artifacts when needed, then run audit and activation check.

When asking an agent to remove an installed pipeline, it should follow `SocratexAI/core/REMOVAL-PROTOCOL.yaml` and run `SocratexAI/tools/remove_pipeline.ps1`.

## Code Audit

For code-project document consistency, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_docs.ps1
```

After first-run initialization, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_docs.ps1 -Initialized
```

## Code Helpers

For programming projects:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_snapshot.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/finish_task.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/commit_task.ps1 -Message "<message>" -Paths <explicit paths>
```

## Version

Current version: `0.2.0-alpha`.

See `VERSION` and `QUALITY-GATE.yaml`.

## Author

SocratexDevSolutions Michał Jasiński.

## License

MIT. See `LICENSE`.

Donation placeholder: add your GitHub Sponsors, Ko-fi, Buy Me a Coffee, Liberapay, PayPal, or Polar link here before public launch.
