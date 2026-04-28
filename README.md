# SocratexPipeline

SocratexPipeline is a modular project runtime for long-running AI-assisted work.

It is not a prompt pack. It gives AI agents a durable operating layer: state, plans, registries, diagnostics, quality gates, update rules, and safe directive routing across long projects.

## Why

AI agents often lose context, mix backlog with active work, forget verification, overwrite local conventions, or bury project rules inside one giant instruction file.

SocratexPipeline fixes that by installing one root control file and a structured `SocratexAI/` package.

Installed projects use this layout:

- root `SOCRATEX.md` is the only required root control file,
- `SocratexAI/` contains pipeline files, tools, packs, state, registries, templates, and docs,
- existing AI directive files should only point to `SOCRATEX.md`.

## Public Bootstrap

To use this from any AI agent, point the agent at `PUBLIC-BOOTSTRAP.md` and say:

```text
use this link to setup pipeline <link-to-PUBLIC-BOOTSTRAP.md>
```

The agent should detect the language of that setup request, ask the pipeline language question first, then continue the setup questions in the chosen language.

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
7. Update the active state file under `SocratexAI/` with the initialized project state.

For code projects, the agent should also read `project/code/COMMANDS.md`, `project/code/REGISTRIES.md`, `project/code/DDD-ADIV.md`, and `core/PROMOTION-RULES.md`.

If the AI environment is limited, read `tools/lite-option/README.md` before selecting artifacts.

User-facing guides:

- `docs/GETTING-STARTED.md`
- `docs/CODE-PROJECTS.md`
- `docs/MODES.md`
- `docs/IMPORT-EXISTING-PROJECT.md`

Format contract:

- code projects use YAML/JSON for standardized project memory,
- code projects use Markdown only for scratch or short human-facing notes,
- non-code user-facing files remain Markdown by default,
- non-code YAML is reserved for large AI-only files.

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
- `SocratexAI/tools/upgrade_from_riftbound.ps1`: maintainer upgrade from the active gamedev source pipeline.
- `SocratexAI/tools/migrate_ai_pipeline.ps1`: migrate an existing AI pipeline into SocratexPipeline.

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

Current version: `0.1.0-alpha`.

See `VERSION` and `QUALITY-GATE.yaml`.

## License

MIT. See `LICENSE`.

Donation placeholder: add your GitHub Sponsors, Ko-fi, Buy Me a Coffee, Liberapay, PayPal, or Polar link here before public launch.
