# Public Usage

## Summary

This guide describes how to publish SocratexPipeline so any AI can install it from a link.

## Recommended Public Link

Publish `PUBLIC-BOOTSTRAP.md` as the main public setup link.

Example user prompt:

```text
use this link to setup pipeline https://example.com/PUBLIC-BOOTSTRAP.md
```

If the user writes in any language, the agent should default to that language unless the user chooses otherwise.

## Public Flow

The AI should:

1. Read `PUBLIC-BOOTSTRAP.md`.
2. Detect the setup request language when possible.
3. Ask the pipeline language question first.
4. Ask context questions.
5. If programming, ask programming-specific questions.
6. Install, merge, or migrate according to the user's answers.
7. Run audit if tools are available.

Installed projects should contain only `SOCRATEX.md` at the project root as the Socratex control file. All pipeline-owned files should live under `SocratexAI/`.

## Public Update

Users can update from a link with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/update_pipeline_from_link.ps1 -Source "<zip-or-local-source>" -Packs code
```

In an installed project, run the updater from `SocratexAI/tools/update_pipeline_from_link.ps1`.

## Maintainer Upgrade

The maintainer can pull improvements from the active gamedev pipeline with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/upgrade_from_riftbound.ps1
```

## Migration

Users can migrate another AI pipeline with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/migrate_ai_pipeline.ps1 -Packs code -DirectiveMode merge -CreateProjectFiles
```

`merge` appends a short instruction to existing directive files telling the AI to prioritize `SOCRATEX.md`.

`replace` saves existing directive files as `.old` and writes a thin directive pointing to `SOCRATEX.md`.
