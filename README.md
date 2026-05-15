# SocratexPipeline

SocratexPipeline is a modular project runtime for long-running AI-assisted work.

It is not a prompt pack. It gives AI agents a durable operating layer: state, plans, registries, diagnostics, quality gates, update rules, and safe directive routing across long projects.

It also installs a reusable project workflow layer: `WORKFLOW.json` for owner-written active pain points and priority challenge rules, plus on-demand `team/*.json` role lenses for product, technical, performance, experience, and pipeline review.

For agent runtime, SocratexPipeline keeps a generated `AI-compiled/` layer. Source documents remain human-editable and authoritative; `AI-compiled/` is compact, English, read-optimized context for agents such as Codex.

SocratexPipeline also compiles tagged project knowledge into `AI-compiled/project/knowledge.sqlite`. Agents can query it with `tools/knowledge/knowledge_select.ps1` by named view, tags, type, source document, or startup flag, while source JSON/Markdown documents remain the only editable source of truth.

When SQLite is unavailable, SocratexPipeline writes a file fallback under `AI-compiled/project/knowledge-files/`. It mirrors the database tables as JSON files, except named views are intentionally unavailable; agents query it with `tools/knowledge/knowledge_file_select.ps1`.

SocratexPipeline also includes a manual `evals/` framework for comparing baseline agent behavior against with-pipeline behavior. The evals focus on priority routing, low-friction adoption, team-role loading, finalization boundaries, document ownership, compiled-instruction handling, and three-tier user fit.

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
- `core/WORKSPACE.json` defines the workspace marker contract for local multi-project workspaces.
- `project/` contains modular project packs.
- `adapters/` contains thin adapter files for specific agents.
- `AI-compiled/` contains generated read-optimized instructions for agents.
- `evals/` contains manual Codex workspace evals, scoring, personas, prompts, and baseline/with-pipeline result files.
- `initializer/` contains the first-run setup workflow.
- `templates/` contains source templates copied into initialized projects, including `WORKFLOW.json` and on-demand `team/` role lenses.
- `tools/` contains helper scripts.
- `temp/trash/` receives first-run initializer files after setup.

When installed into another project, this source structure is copied under `SocratexAI/`.

## Workspace Marker

Workspace-level tools should use a `workspace.json` file stored in the workspace root next to `SocratexAI/`.

Example:

```text
<workspace>/
  workspace.json
  SocratexAI/
  <Project>/
  tools/
  _archive/
  drive-exports/
```

Paths inside `workspace.json` should be relative to the file location. Project-local scripts should keep resolving their own repository roots from script location; `workspace.json` is only for workspace-level operations such as sibling source checkout discovery, Drive imports, archives, and exports.

Use `tools/pipeline/resolve_workspace_root.ps1` when a script or agent needs the local workspace root. Do not hardcode user-specific paths such as `/home/<user>/work`, `/home/<user>/projects`, `drive-imports`, or `repos` into source pipeline scripts or project configs.

## First Run

Give the agent this project and ask it to follow `AGENTS.md`.

On first run, the agent should:

1. Read `initializer/FIRST-RUN.md`.
2. Ask the initialization questions.
3. Select the needed project packs.
4. Remove unused packs and templates.
5. Create the project-local files from `templates/`.
6. Move `initializer/` into `temp/trash/initializer/`.
7. Create `SocratexAI/DOCS.json` as the document role index.
8. Update the active state file under `SocratexAI/` with the initialized project state.
9. Switch the current session to root `SOCRATEX.md`.

For code projects, the agent should also read `project/code/COMMANDS.json`, `project/code/REGISTRIES.json`, `project/code/DDD-ADIV.json`, and `core/PROMOTION-RULES.json`.

Code projects can store `project_profile`, `runtime_status`, and `workflow.branch_mode` in `PIPELINE-CONFIG.json`.

The agent uses `project_profile` to filter known solutions, `ROI-BIAS.md` to rank recommendations, and `SCRIPT-FALLBACK.md` when tools cannot run.

PowerShell 7 (`pwsh`) is the preferred automation runtime. During setup, the agent should check it first, run `tools/setup/install_powershell.ps1` when missing, and recommend lite/no-tools mode, a supported host/container, or porting scripts if the target system cannot support PowerShell.

If the AI environment is limited, read `tools/lite-option/README.md` before selecting artifacts.

User-facing guides:

- `docs/GETTING-STARTED.md`
- `docs/CODE-PROJECTS.md`
- `docs/MODES.md`
- `docs/IMPORT-EXISTING-PROJECT.md`

Format contract:

- code projects use JSON for standardized project memory,
- non-code projects use Markdown for user-facing memory such as state, plan, backlog, decisions, issues, journal, and review,
- JSON is used for files managed only by the agent, such as `DOCS.json`, config, queues, caches, indexes, agent-only context docs, diagnostics, and generated summaries,
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

- `SocratexAI/tools/pipeline/update_pipeline_from_link.ps1`: public user update from a latest pipeline source.
- `SocratexAI/tools/pipeline/reinitialize_pipeline.ps1`: missing-only reinitialization after setup or update.
- `SocratexAI/tools/pipeline/remove_pipeline.ps1`: remove the installed pipeline through a bounded remover.
- `SocratexAI/tools/pipeline/upgrade_from_riftbound.ps1`: maintainer upgrade from the active reference source pipeline.
- `SocratexAI/tools/pipeline/migrate_ai_pipeline.ps1`: migrate an existing AI pipeline into SocratexPipeline.
- `SocratexAI/tools/pipeline/resolve_workspace_root.ps1`: local workspace marker resolver for multi-project workspaces.

Structured JSON tools apply to every project type, including non-code projects, for agent-only structured JSON files. Use `read_document_item`, `list_document_keys`, `insert_document_item`, `bulk_insert_document_items`, `move_document_item`, and `migrate_document_item` whenever practical.

`WORKFLOW.json` is intentionally opt-in context. Agents should read it for planning, priority, roadmap, feature-triage, and broad project-risk decisions, not for every narrow local edit. `team/*.json` files are loaded only when requested or routed by workflow.

After changing source instructions, templates, core docs, project packs, or adapter rules, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/rebuild_ai_compiled_context.ps1
```

This also refreshes the compiled SQLite knowledge database when `tools/knowledge/knowledge_compile.ps1` is present.

Equivalent full compile/check wrapper:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1
```

To check for drift without writing files:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/check_ai_compiled_context.ps1
```

For direct knowledge-layer work:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_code_context.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_code_context.ps1 -Views architecture,performance
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_select.ps1 -View session_start
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_select.ps1 -Tags engineering,workflow
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_check.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_file_select.ps1 -Tags engineering,workflow
powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_file_check.ps1
```

To check the eval framework structure:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/quality/check_evals.ps1
```

Document edit scripts are transactional by default: they should own the write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output. Agents should not compose manual read/edit/normalize/cache/check queues after a successful document edit tool.

When asking an agent to update an installed pipeline, it should follow `SocratexAI/core/UPDATE-PROTOCOL.json`, resolve `pipeline.update_source`, run the updater, reinitialize newly introduced missing artifacts when needed, then run audit and activation check.

When asking an agent to remove an installed pipeline, it should follow `SocratexAI/core/REMOVAL-PROTOCOL.json` and run `SocratexAI/tools/pipeline/remove_pipeline.ps1`.

## Code Audit

For code-project document consistency, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1
```

After first-run initialization, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1 -Initialized
```

## Code Helpers

For programming projects:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/task_snapshot.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/quality/run_quality_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/run_final_task_checks.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/legacy_commit_task_compatibility_wrapper.ps1 -Message "<message>" -Paths <explicit paths>
```

## Version

Current version: `0.2.0-alpha`.

See `VERSION` and `QUALITY-GATE.json`.

## Author

SocratexDevSolutions Michał Jasiński.

## License

MIT. See `LICENSE`.

Donation placeholder: add your GitHub Sponsors, Ko-fi, Buy Me a Coffee, Liberapay, PayPal, or Polar link here before public launch.
