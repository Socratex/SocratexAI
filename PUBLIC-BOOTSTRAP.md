# SocratexPipeline Public Bootstrap

## Purpose

Use this file when a user says something like:

`use this link to setup pipeline <link>`

The agent should read this file, ask the bootstrap questions, then install or merge SocratexPipeline into the user's project.

## Language Rule

Detect the language of the user's setup request when possible.

If the user's system locale or project language can be detected, mention it as the suggested language.

First ask:

`What language should the AI pipeline use? I can use <detected language> if that is correct.`

After the user answers, ask the remaining questions in that language.

## Communication Profile

Ask:

`Which communication profile should this project use?`

Supported profiles:

- `standard`: normal SocratexAI communication rules.
- `epistemic_skeptic`: truth-first discussion mode. Prioritizes epistemic accuracy over agreement, uses skepticism, confidence levels, falsifiability, evidence/framing separation, concise structure, tables when useful, and validate-then-criticize-then-advise ordering.

## Supported Contexts

Ask:

`What is the context of this project?`

Supported contexts:

- programming
- generic project
- personal
- creative
- mixed

## Project Profile Interview

For programming context, ask these questions before programming operation questions:

1. Project age or lifecycle stage:
   - `greenfield`
   - `early`
   - `mature`
   - `legacy`
   - `sunset`
2. Test coverage:
   - `none`
   - `smoke-only`
   - `partial`
   - `comprehensive`
   - `tdd`
3. Framework:
   - `standard (name)`
   - `custom in-house`
   - `mixed`
   - `none`
4. Linter or typecheck:
   - `enforced`
   - `optional`
   - `none`
5. CI/CD:
   - `full`
   - `partial`
   - `none`
6. Documentation state:
   - `current`
   - `partial`
   - `stale`
   - `none`
7. Team size:
   - `solo`
   - `small (2-5)`
   - `medium (6-20)`
   - `large (>20)`
8. Velocity expectation:
   - `experimental`
   - `iterating`
   - `shipping`
   - `maintenance`
9. Highest current pain: free text.
10. Stack tags: auto-suggest using `tools/setup/detect_project_stack.ps1` when possible, then ask the user to verify or edit the list.

Store answers in `PIPELINE-CONFIG.json` under `project_profile`.

After the profile interview, list the three most relevant known-solution families for this profile.

## Runtime Check

After Project Profile Interview and before programming questions, run the runtime check when tools are available:

```powershell
python tools/quality/check_runtime.py --root-key runtime_status
```

Report missing runtimes or libraries.

If something is missing, follow `core/SCRIPT-FALLBACK.json`: propose installing the missing runtime before using manual fallback.

If PowerShell 7 (`pwsh`) is missing, treat it as the first setup improvement:

1. Run `tools/setup/install_powershell.ps1` when PowerShell-compatible shell execution is available.
2. Present the detected install command and ask for explicit approval before using `-Apply`.
3. After installation, rerun `tools/quality/check_runtime.py --root-key runtime_status`.
4. If the platform cannot support PowerShell, recommend one of:
   - use lite/no-tools mode,
   - run SocratexAI from a supported host or container,
   - port required scripts to the target shell before relying on automation.

Store the result in `PIPELINE-CONFIG.json` under `runtime_status`.

## Programming Questions

If the context is programming, ask:

1. Should the project use `CHANGELOG.json` for shipped history?
   - `yes`: create and maintain `CHANGELOG.json` for shipped functionality and major fixes.
   - `no`: skip changelog files and do not require changelog promotion.
2. Should the AI commit changes?
3. Should the AI push changes?
4. Which branch workflow mode should this project use?
   - `branch_scoped`: use committed directives under `.aiassistant/` and local branch memory under `ignored/ai-socratex/`.
   - `linear`: use normal `STATE.json` and `_PLAN.json` under the SocratexAI installation.
   Default to `branch_scoped` when the user works on Git branches.
5. Can there be external changes from other people, CI, tools, or branches while the AI is working?
6. Should the AI force DDD-ADIV as a required design discipline?
7. Should the AI import a pipeline package or dependency when the ecosystem supports it?
8. Should the AI detect package managers and frameworks, such as Composer for PHP?
9. Should the AI replace current directives after saving a snapshot, or merge with current directives?
10. Which directive files should be managed?
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.cursor/rules`
   - `.github/copilot-instructions.md`
   - other
11. What should the first useful work pass be?

## Programming Detection

Before installing, inspect the project for common ecosystem signals:

- PHP: `composer.json`, `composer.lock`, `artisan`, `symfony.lock`
- Node: `package.json`, `pnpm-lock.json`, `yarn.lock`
- Python: `pyproject.toml`, `requirements.txt`, `uv.lock`
- .NET: `*.sln`, `*.csproj`
- Java: `pom.xml`, `build.gradle`, `build.gradle.kts`
- Go: `go.mod`
- Rust: `Cargo.toml`

If Composer is detected, ask whether the user wants pipeline package import guidance for PHP projects.

Do not add dependencies automatically without explicit user approval.

## Directive Merge Modes

Use one of these modes:

- snapshot: save current directive files under `pipeline-snapshots/` and create fresh SocratexPipeline directives.
- merge: preserve current directive content and append one directive telling the AI to read and prioritize root `SOCRATEX.md`.
- replace: save the current directive beside itself with a `.old` suffix, then replace it with a thin directive pointing to `SOCRATEX.md`.

Default to merge when uncertain.

## Installation Actions

For programming projects:

1. Create root `SOCRATEX.md`.
2. Install all pipeline files under `SocratexAI/`.
3. Create or update JSON project memory files under `SocratexAI/`.
4. Keep Markdown only for scratch intake, prompt-language branch files, and short user-facing notes.
5. Install code pack files under `SocratexAI/project/code/`.
6. Install tools under `SocratexAI/tools/`.
7. Create `SocratexAI/DOCS.json` as the document role index.
8. Create `SocratexAI/PIPELINE-CONFIG.json` with `workflow`, `project_profile`, `runtime_status`, `communication.profile`, `changelog.enabled`, and pipeline update source fields.
   - Set `pipeline.public_bootstrap_url` to `https://raw.githubusercontent.com/Socratex/SocratexAI/main/PUBLIC-BOOTSTRAP.md`.
   - Set `pipeline.update_source` to `https://github.com/Socratex/SocratexAI.git` when Git is available.
   - Set `pipeline.update_command` to the cheap update command shown in the update section unless the user explicitly wants a custom source.
9. If `workflow.branch_mode` is `branch_scoped`, create committed directives under `.aiassistant/socratex/`, create local branch memory under `ignored/ai-socratex/`, and ensure `/ignored` is gitignored.
10. Apply directive merge or replace mode.
11. Run document audit when possible.
12. Activate the installed pipeline for the current and future sessions.

Installed projects also receive `WORKFLOW.json` and `team/*.json` role lenses. These are not default context for every prompt. Use `WORKFLOW.json` when priority steering or broad project-risk judgment matters, and load a `team/` role only when the user asks for that lens or workflow routes the task to it.

Source pipeline repositories may include `AI-compiled/`, a generated agent-readable instruction cache. Treat it as read-only generated context. If source instructions change, run `tools/pipeline/rebuild_ai_compiled_context.ps1`.
13. End with first useful work pass recommendations and ROI Picks.

For non-programming projects:

1. Create root `SOCRATEX.md`.
2. Install all pipeline files under `SocratexAI/`.
3. Create `SocratexAI/DOCS.json` as the document role index.
4. Use Markdown for user-facing project memory, including state, plan, backlog, decisions, issues, journal, and review files.
5. Use JSON for files managed only by the agent, including configuration, queues, caches, indexes, agent-only context docs, diagnostics, and generated summaries.
6. Install only the selected project packs.
7. Use shared JSON/document tools for agent-only structured JSON files.
8. Avoid truly code-only tools unless explicitly requested.

## Post-Setup Activation

After setup, import, migration, or update succeeds, stop treating `PUBLIC-BOOTSTRAP.md` as the active instruction source.

Immediately switch the current session to the installed project pipeline:

1. Re-read root `SOCRATEX.md`.
2. Follow the read order defined there.
3. Read `SocratexAI/DOCS.json` before reading, creating, renaming, or updating project documents.
4. For branch-scoped projects, read `.aiassistant/socratex/PIPELINE-CONFIG.json` when present, then detect the current branch and read branch STATE/PLAN.
5. Use the installed `SocratexAI/` files for all future work in this project.
6. After the first user prompt handled under the installed pipeline, run `SocratexAI/core/ACTIVATION-CHECK.json` once to verify that all rules are loaded, including communication format and emoji rules.
7. In future sessions, start from root `SOCRATEX.md` or the managed adapter directive that points to it.

Report this handoff explicitly:

`SocratexAI is now active for this project. Future sessions should start from SOCRATEX.md.`

## Update, Upgrade, Migrate

Use these tools when available:

- `tools/pipeline/update_pipeline_from_link.ps1`: update a user's project from the latest public pipeline source.
- `tools/pipeline/reinitialize_pipeline.ps1`: add newly introduced initialized artifacts without overwriting existing project memory.
- `tools/pipeline/upgrade_from_riftbound.ps1`: maintainer-only upgrade from the active reference source pipeline.
- `tools/pipeline/migrate_ai_pipeline.ps1`: migrate an existing non-Socratex AI pipeline into SocratexPipeline.

When the user asks to update an installed pipeline, follow `core/UPDATE-PROTOCOL.json`.

Cheap update is the default. It should refresh the managed `SocratexAI/` package, preserve project-owned configuration and memory, refresh the instance feature list, update directives, and run the cheap feature-contract check. It should not rebuild compiled knowledge or run the full audit unless the user asks for full verification or the cheap check fails.

Preferred public update command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/pipeline/update_pipeline_from_link.ps1 -Source "https://github.com/Socratex/SocratexAI.git" -SourceMode Git
```

Use full verification only when the user has enough time/budget or when debugging the update itself:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/pipeline/update_pipeline_from_link.ps1 -Source "https://github.com/Socratex/SocratexAI.git" -SourceMode Git -FullVerify
```

Use `-ReinitializeNew` only when the update explicitly introduces newly initialized files that should be created in the project root. Reinitialization must be missing-only and must not overwrite project memory.

The agent should resolve the update source from `pipeline.update_source` or `pipeline.public_bootstrap_url` in config before asking the user. If `pipeline.public_bootstrap_url` points to this raw bootstrap file, prefer the Git repository source above for the actual update package.

If the updated pipeline includes initializer artifacts missing from the installed project, run `tools/pipeline/reinitialize_pipeline.ps1` in missing-only mode after update.

If no source is configured, ask for the URL or local source path before changing files.

When the user asks to remove an installed pipeline, follow `core/REMOVAL-PROTOCOL.json` and run `tools/pipeline/remove_pipeline.ps1` from the installed `SocratexAI/tools/` directory.
