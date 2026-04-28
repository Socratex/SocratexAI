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
6. Which communication profile should this project use?
   - `standard`
   - `epistemic_skeptic`: truth-first discussion mode with skepticism, falsifiability, evidence/framing separation, confidence levels, concise structure, and tables when useful
7. What should the first concrete target be?
8. What should the agent optimize for?
   - speed
   - correctness
   - creative quality
   - low administrative overhead
   - high accountability
9. What should the agent avoid?
10. Which artifacts should exist after initialization?
11. Should the project use `CHANGELOG.yaml` for shipped history?
12. Should the project use Git?
13. Are there external tools, folders, accounts, or references the agent should know about?
14. What counts as a successful first session?

If the context is programming, also ask:

15. Should the AI commit changes?
16. Should the AI push changes?
17. Project Profile Interview:
   - lifecycle: greenfield / early / mature / legacy / sunset
   - test coverage: none / smoke-only / partial / comprehensive / tdd
   - framework: standard (name) / custom in-house / mixed / none
   - linter or typecheck: enforced / optional / none
   - CI/CD: full / partial / none
   - documentation state: current / partial / stale / none
   - team size: solo / small / medium / large
   - velocity expectation: experimental / iterating / shipping / maintenance
   - highest current pain
   - stack tags, suggested from `tools/detect_project_stack.ps1` when practical
18. Run `tools/check_runtime.py` when practical and record runtime availability.
   - If PowerShell 7 (`pwsh`) is missing, run `tools/install_powershell.ps1` to produce an install plan.
   - Ask for explicit user approval before installing with `-Apply`.
   - If PowerShell is unsupported, recommend lite/no-tools mode, a supported host/container, or porting required scripts.
19. Which branch workflow mode should this project use?
   - `branch_scoped`
   - `linear`
20. Can external changes happen while AI is working?
21. Should the AI force DDD-ADIV?
22. Should the AI import a pipeline package or dependency if the ecosystem supports it?
23. Should the AI detect package managers and frameworks, including Composer for PHP?
24. Should directive files be snapshotted, merged, or replaced?

## Initialization Actions

After receiving answers:

1. Update `README.md` with the actual project identity.
2. Create `DOCS.yaml` as the document role index.
3. Create `STATE.yaml` for code projects, or `STATE.md` for non-code user-facing memory.
4. Create the selected pack's recommended files from `templates/`.
5. Keep selected packs under `project/`.
6. Move unselected packs into `temp/trash/project/` unless the user asks to keep them.
7. Keep adapters thin.
8. Move `initializer/` into `temp/trash/initializer/`.
9. Record the initialization decision in `DECISIONS.yaml` for code projects, or `DECISIONS.md` for non-code user-facing memory, if that file exists.
10. Create `PIPELINE-CONFIG.yaml` with selected packs, language, operating mode, Git preference, and first-session success criteria.
11. Create `PIPELINE-CONFIG.yaml`; for code projects include `workflow`, `project_profile`, `runtime_status`, `communication.profile`, and `changelog.enabled`.
12. For branch-scoped code projects, create `ignored/ai-socratex/` branch memory files and ensure `/ignored` is gitignored when branch files are not English.
13. Compile project-local agent instructions with `tools/compile_agent_instructions.ps1` when practical.
14. Run `tools/audit_docs.ps1 -Initialized` for initialized projects when practical.
15. Activate the initialized pipeline for the current and future sessions.
16. End by proposing recommendations to improve the initialized pipeline toward the full SocratexPipeline reference level.
17. For code projects, include the three most relevant known-solution families for the project profile and ROI Picks for the first useful work pass.

## Post-Initialization Activation

After initialization succeeds, stop using `initializer/FIRST-RUN.md` as the active instruction source.

Immediately switch the current session to the initialized project pipeline:

1. Re-read root `SOCRATEX.md`.
2. Follow the read order defined there.
3. Read `SocratexAI/DOCS.yaml` before reading, creating, renaming, or updating project documents.
4. For branch-scoped code projects, read `.aiassistant/socratex/PIPELINE-CONFIG.yaml` when present, detect the current branch, and read branch STATE/PLAN.
5. Use the initialized `SocratexAI/` files for all future work in this project.
6. After the first user prompt handled under the initialized pipeline, run `SocratexAI/core/ACTIVATION-CHECK.yaml` once to verify that all rules are loaded, including communication format and emoji rules.
7. In future sessions, start from root `SOCRATEX.md` or the managed adapter directive that points to it.

Report this handoff explicitly:

`SocratexAI is now active for this project. Future sessions should start from SOCRATEX.md.`

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
