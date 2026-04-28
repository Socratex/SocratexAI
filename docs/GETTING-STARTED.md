# Getting Started

## Summary

This guide shows how to initialize SocratexPipeline for a new project.

## Recommended First Run

Run the wizard:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/wizard.ps1
```

The first question asks for the language used in project conversation and status updates.

After that, answer the remaining questions in your preferred language.

For public link-based setup, use `PUBLIC-BOOTSTRAP.md`.

## Manual First Run

If you prefer agent-led setup, ask the agent to read:

1. `AGENTS.md`
2. `initializer/FIRST-RUN.md`

The agent should ask the initialization questions, create the selected artifacts, move unused packs to `temp/trash/`, and move `initializer/` to `temp/trash/initializer/`.

## Code Project Shortcut

For a standard code project:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Initialize-SocratexPipeline.ps1 -ProjectName "My Project" -Language "English" -AiMode Standard -KeepPacks code -CreateFiles -CompileAgent -RunAudit
```

This creates standardized code memory as YAML/JSON, with Markdown reserved for scratch intake such as `_INSTRUCTIONS.md`.

For branch-scoped code work, add:

```powershell
-BranchMode branch_scoped
```

The project profile and runtime status are stored in `PIPELINE-CONFIG.yaml`.

## After Initialization

For code projects, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_docs.ps1 -Initialized
```

Then configure the project-specific quality gate.

After initialization succeeds, the agent should switch the current session to root `SOCRATEX.md` and use the initialized pipeline for all future sessions in that project.

After the first prompt handled under the initialized pipeline, the agent should run `SocratexAI/core/ACTIVATION-CHECK.md` once to verify the loaded rules.
