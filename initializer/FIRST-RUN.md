# First-Run Initializer

## Purpose

This file is used only before the project is initialized.

The agent must ask the user the initialization questions, configure the project, remove unused packs, create project files, then move the whole `initializer/` folder to `temp/trash/initializer/`.

## Required Questions

Ask these questions before changing the skeleton:

1. Which language should the agent use for this project conversation and status updates?
   - Recommend answering the remaining initialization questions in the user's preferred language.
2. What is the project name?
3. What kind of project is this?
   - code
   - generic
   - personal
   - creative
   - mixed
4. Which project packs should remain active?
5. What AI operating mode should this project assume?
   - lite / limited AI context, tool use, budget, or reliability
   - standard / normal coding-agent usage
   - enterprise / high-context, high-tooling, long-session capable
6. What should the first concrete target be?
7. What should the agent optimize for?
   - speed
   - correctness
   - creative quality
   - low administrative overhead
   - high accountability
8. What should the agent avoid?
9. Which artifacts should exist after initialization?
10. Should the project use Git?
11. Are there external tools, folders, accounts, or references the agent should know about?
12. What counts as a successful first session?

If the context is programming, also ask:

13. Should the AI commit changes?
14. Should the AI push changes?
15. Do you work on branches?
16. Can external changes happen while AI is working?
17. Should the AI force DDD-ADIV?
18. Should the AI import a pipeline package or dependency if the ecosystem supports it?
19. Should the AI detect package managers and frameworks, including Composer for PHP?
20. Should directive files be snapshotted, merged, or replaced?

## Initialization Actions

After receiving answers:

1. Update `README.md` with the actual project identity.
2. Create `STATE.md`.
3. Create the selected pack's recommended files from `templates/`.
4. Keep selected packs under `project/`.
5. Move unselected packs into `temp/trash/project/` unless the user asks to keep them.
6. Keep adapters thin.
7. Move `initializer/` into `temp/trash/initializer/`.
8. Record the initialization decision in `DECISIONS.md` if that file exists.
9. Create `PIPELINE-CONFIG.md` with selected packs, language, operating mode, Git preference, and first-session success criteria.
10. Compile project-local agent instructions with `tools/compile_agent_instructions.ps1` when practical.
11. Run `tools/audit_docs.ps1 -Initialized` for code projects when practical.
12. End by proposing recommendations to improve the initialized pipeline toward the full SocratexPipeline reference level.

## Lite Mode

If the user selects lite / limited AI mode, read `tools/lite-option/README.md` before choosing artifacts.

Prefer fewer files and lower ceremony.

## Enterprise Mode

If the user selects enterprise mode, prefer the full code pack for programming projects:

- registries,
- quality gates,
- document audit,
- Git safety,
- context compaction,
- frozen-layer protocol.

## Final Recommendations

At the end of initialization, propose a short list of improvements that would bring the initialized project closer to the full reference pipeline.

For code projects, consider:

- project-specific quality gate command,
- Git branch and commit conventions,
- CI integration,
- domain-specific context capsules,
- frozen layer candidates,
- bug reproduction template,
- release checklist,
- stricter audit mode.

## Safety

Before deleting or moving anything outside `initializer/` or unselected `project/` packs, state the intended paths and get confirmation.
