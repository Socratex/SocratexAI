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

## Supported Contexts

Ask:

`What is the context of this project?`

Supported contexts:

- programming
- generic project
- personal
- creative
- mixed

## Programming Questions

If the context is programming, ask:

1. Should the AI commit changes?
2. Should the AI push changes?
3. Do you work on branches?
4. Can there be external changes from other people, CI, tools, or branches while the AI is working?
5. Should the AI force DDD-ADIV as a required design discipline?
6. Should the AI import a pipeline package or dependency when the ecosystem supports it?
7. Should the AI detect package managers and frameworks, such as Composer for PHP?
8. Should the AI replace current directives after saving a snapshot, or merge with current directives?
9. Which directive files should be managed?
   - `AGENTS.md`
   - `CLAUDE.md`
   - `.cursor/rules`
   - `.github/copilot-instructions.md`
   - other
10. What should the first useful work pass be?

## Programming Detection

Before installing, inspect the project for common ecosystem signals:

- PHP: `composer.json`, `composer.lock`, `artisan`, `symfony.lock`
- Node: `package.json`, `pnpm-lock.yaml`, `yarn.lock`
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
3. Create or update YAML/JSON project memory files under `SocratexAI/`.
4. Keep Markdown only for scratch intake and short user-facing notes.
5. Install code pack files under `SocratexAI/project/code/`.
6. Install tools under `SocratexAI/tools/`.
7. Create `SocratexAI/PIPELINE-CONFIG.yaml`.
8. Apply directive merge or replace mode.
9. Run document audit when possible.
10. End with upgrade recommendations.

For non-programming projects:

1. Create root `SOCRATEX.md`.
2. Install all pipeline files under `SocratexAI/`.
3. Keep user-facing files as Markdown.
4. Use YAML only for large AI-only internal memory files.
5. Install only the selected project packs.
6. Avoid code-only tools unless explicitly requested.

## Update, Upgrade, Migrate

Use these tools when available:

- `tools/update_pipeline_from_link.ps1`: update a user's project from the latest public pipeline source.
- `tools/upgrade_from_riftbound.ps1`: maintainer-only upgrade from the active gamedev source pipeline.
- `tools/migrate_ai_pipeline.ps1`: migrate an existing non-Socratex AI pipeline into SocratexPipeline.
