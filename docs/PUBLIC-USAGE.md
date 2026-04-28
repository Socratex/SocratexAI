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
5. If programming, run the Project Profile Interview.
6. Run the runtime check when tools are available.
7. Ask programming-specific questions, including branch workflow mode.
8. Install, merge, or migrate according to the user's answers.
9. Run audit if tools are available.
10. Activate the installed project pipeline by switching to root `SOCRATEX.md`.
11. End with first useful work recommendations and ROI Picks.

Installed projects should contain only `SOCRATEX.md` at the project root as the Socratex control file. All pipeline-owned files should live under `SocratexAI/`.

After setup succeeds, the agent should stop using the public bootstrap as the active instruction source and immediately continue from the installed project's `SOCRATEX.md`.

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
