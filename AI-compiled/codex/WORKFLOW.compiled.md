# Compiled Workflow for Codex

Generated: source-cdf23628038d

## Code Read Order

title: Read Order
format: markdown-section
body: |
  ## Read Order

  For ordinary code work:

  1. `AGENTS.md`
  2. `STATE.yaml`
  3. `PIPELINE-CONFIG.yaml`
  4. `ORCHESTRATION.yaml` only when priority steering, feature triage, planning, or broad project-risk judgment matters
  5. `team/*.yaml` only when the user names a role, asks for team-style review, or ORCHESTRATION.yaml routes the task to that role
  6. `core/PROJECT-PROFILE.yaml` when `project_profile` exists
  7. `core/ROI-BIAS.yaml`
  8. `core/TASK-WORK.yaml` for broad multi-step work
  9. `_PLAN.yaml`
  10. smallest relevant file under `context-docs/`
  11. source files in the touched ownership slice

  For broad architecture, ownership, persistence, API, build, toolchain, or registry work, also read:

  1. `core/PROMOTION-RULES.yaml`
  2. `project/code/DDD-ADIV.yaml`
  3. `project/code/GIT.yaml`
  4. `project/code/FROZEN-LAYERS.yaml`

  For branch-scoped projects, also read:

  1. `project/code/BRANCH-MODE.yaml`
  2. branch state and plan from the configured `workflow.branch_files_dir`

  For raw user instruction buffers, also read:

  1. `core/INSTRUCTION-CAPTURE.yaml`
  2. `project/code/INSTRUCTION-CAPTURE.yaml`

  For logs, traces, crashes, console output, and evidence-driven debugging, also read:

  1. `project/code/DIAGNOSTICS.yaml`


## General Workflow

title: General Workflow
format: markdown-section
body: |
  ## General Workflow

  1. Start from the smallest state source that answers the question.
  2. Identify the ownership slice.
  3. Check existing scripts and project automation before doing repeatable work manually.
  4. For every new feature request, suggestion, or architecture discussion, first check whether the requested work can be implemented in the most future-proof, maintainable, profile-fitting way before executing the literal request.
  5. For software and game projects, use AAA-grade architecture as the steer-direction where appropriate: explicit ownership, data flow, contracts, diagnostics, performance budget, toolability, deterministic behavior where relevant, testability, and low retrofit cost.
  6. For bug reports, first check whether the bug exposes a deeper ownership, lifecycle, contract, data-flow, tooling, observability, or architecture weakness; prefer the smallest fix that removes the bug class or improves diagnosis.
  7. Check whether a known solution, pattern, or tool is cheaper than custom design.
  8. For planning or feature triage, check `ORCHESTRATION.yaml` before changing active plan or backlog; challenge the request when it bypasses a higher-priority active pain point.
  9. Load `team/*.yaml` role lenses only on demand or when orchestration routing selects them.
  10. Check whether a future-facing prerequisite should happen before the requested implementation.
  11. For broad multi-step work, create or refresh `docs-tech/cache/current_task.yaml` and split the request into micro-tasks.
  12. For structural or multi-boundary work, write a short impact note or plan before editing.
  13. Rank recommendations or candidate passes by ROI when there are multiple options.
  14. Implement within the scoped boundary, updating micro-task status when task work tracking is active.
  15. Verify with the strongest practical gate at a natural verification boundary.
  16. Update only the memory layers whose current truth changed.
  17. Finish with concrete changed files, verification, residual risk, and ROI Picks when follow-up recommendations exist.


## Verification Boundary

title: Verification Boundary
format: markdown-section
body: |
  ## Verification Boundary

  Treat status, audit, quality, line-index, and finish scripts as boundary tools, not as reflex tools after every small edit.

  Default cadence:

  1. Use targeted reads, outlines, search, and diffs while exploring and editing.
  2. Make all code and document edits for the current scope before running broad checks.
  3. Run `tools/done.ps1 -Message "<message>"` near the end of the scope when a Git-backed task should be committed and pushed. It should discover changed files from git, normalize text, rebuild document cache, refresh code-line indexes, run audit/quality, stage intentional files, commit, push, and report status.
  4. For broad multi-boundary tasks, run one finalizer after each coherent subtask block before moving to the next block.
  5. Rerun a gate only after fixing something that could plausibly affect that gate.

  Avoid full-file reads immediately after a successful structured read unless the structured output is missing the needed section, the document shape is suspicious, or exact raw formatting matters.

  Do not manually repeat normalize/cache/index/check steps after each micro-edit or after a successful transactional document edit tool unless the wrapper failed, `-NoPostEdit` was intentionally used, or a broader verification boundary requires it.

  If `tools/done.ps1` or an owned finalizer fails on a repeated mechanical issue, update the script so the same class of issue is handled automatically before rerunning the finalizer.


## Recompile Command

Use this command after changing source instructions, templates, core docs, project packs, or compiled-output rules:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
~~~

Use this command to check for drift:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_compiled_instructions.ps1
~~~
