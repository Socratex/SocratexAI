# Compiled Workflow for Codex

Generated: source-497156e27702

## Code Read Order

{
    "title": "Read Order",
    "format": "markdown-section",
    "body": "## Read Order\n\nFor ordinary code work:\n\n1. `AGENTS.md`\n2. `STATE.json`\n3. `PIPELINE-CONFIG.json`\n4. `WORKFLOW.json` only when priority steering, feature triage, planning, or broad project-risk judgment matters\n5. `team/*.json` only when the user names a role, asks for team-style review, or WORKFLOW.json routes the task to that role\n6. `core/PROJECT-PROFILE.json` when `project_profile` exists\n7. `core/ROI-BIAS.json`\n8. `core/TASK-WORK.json` for broad multi-step work\n9. `_PLAN.json`\n10. smallest relevant file under `context-docs/`\n11. source files in the touched ownership slice\n\nFor every programming implementation, code modification, refactor, bugfix, code review, or any task that may touch source code, load the full compiled code-guidance set before the first code read/write that could lead to an edit:\n\n1. Prefer `tools/knowledge_code_context.ps1` when available. It must load the full base guidance slice and write the local `ignored/code_context_gate.json` marker after success.\n2. Pass the most relevant named view when it exists, such as `-Views architecture`, `-Views performance`, `-Views debugging`, or another project-specific architecture/performance view. Treat views as additive task context, not replacements for the full base set.\n3. If the wrapper is unavailable, run `tools/knowledge_check.ps1`, then load all currently compiled engineering, coding, architecture, best-practices, borrowed-before-bespoke, production-grade software engineering, DDD-ADIV, future-first, data-first ownership, runtime, diagnostics, performance, and verification rules.\n4. If SQLite is unavailable, use `tools/knowledge_file_select.ps1` with the same tag/type intent.\n5. `tools/check_task.ps1` should fail changed-code checks when the fresh full-guidance marker is missing, stale, or does not include the required base tags.\n\nFor every user command or substantive question, perform a context-tag pass before answering or executing:\n\n1. Load the main workflow and instruction documents required by the active adapter/project profile.\n2. Run `tools/context_tags.ps1 <user text>` when available to derive relevant compiled-knowledge tags from the user's command or question.\n3. Query notes from the compiled knowledge layer with `tools/knowledge_select.ps1 -Tags <tags> -Match any`; if SQLite is unavailable, use `tools/knowledge_file_select.ps1` with the same tag intent.\n4. Use those notes to choose the smallest correct workflow, reads, risks, and implementation boundary before answering or editing.\n5. Do not let tag-selected notes replace exact source reads when changing source files, making high-stakes claims, or resolving ambiguity.\n\nFor broad architecture, ownership, persistence, API, build, toolchain, or registry work, also read:\n\n1. `core/PROMOTION-RULES.json`\n2. `project/code/DDD-ADIV.json`\n3. `project/code/GIT.json`\n4. `project/code/FROZEN-LAYERS.json`\n\nFor branch-scoped projects, also read:\n\n1. `project/code/BRANCH-MODE.json`\n2. branch state and plan from the configured `workflow.branch_files_dir`\n\nFor raw user instruction buffers, also read:\n\n1. `core/INSTRUCTION-CAPTURE.json`\n2. `project/code/INSTRUCTION-CAPTURE.json`\n\nFor logs, traces, crashes, console output, and evidence-driven debugging, also read:\n\n1. `project/code/DIAGNOSTICS.json`\n"
}

## General Workflow

{
    "title": "General Workflow",
    "format": "markdown-section",
    "body": "## General Workflow\n\n1. Start from the smallest state source that answers the question.\n2. Identify the ownership slice.\n3. Check existing scripts and project automation before doing repeatable work manually.\n4. Before any code touch, load the full compiled code-guidance set when the project provides a knowledge layer; prefer `tools/knowledge_code_context.ps1` and keep the returned rules active as implementation constraints, not optional background reading.\n5. For every new feature request, suggestion, or architecture discussion, first check whether the requested work can be implemented in the most future-proof, maintainable, profile-fitting way before executing the literal request.\n6. For software and game projects, use production-grade architecture as the steer-direction where appropriate: explicit ownership, data flow, contracts, diagnostics, performance budget, toolability, deterministic behavior where relevant, testability, and low retrofit cost.\n7. For bug reports, first check whether the bug exposes a deeper ownership, lifecycle, contract, data-flow, tooling, observability, or architecture weakness; prefer the smallest fix that removes the bug class or improves diagnosis.\n8. Check whether a known solution, pattern, or tool is cheaper than custom design.\n9. For planning or feature triage, check `WORKFLOW.json` before changing active plan or backlog; challenge the request when it bypasses a higher-priority active pain point.\n10. Load `team/*.json` role lenses only on demand or when workflow routing selects them.\n11. Check whether a future-facing prerequisite should happen before the requested implementation.\n12. For broad multi-step work, create or refresh `docs-tech/cache/current_task.json` and split the request into micro-tasks.\n13. For structural or multi-boundary work, write a short impact note or plan before editing.\n14. Rank recommendations or candidate passes by ROI when there are multiple options.\n15. Implement within the scoped boundary, updating micro-task status when task work tracking is active.\n16. Verify with the strongest practical gate at a natural verification boundary.\n17. Update only the memory layers whose current truth changed.\n18. Finish with concrete changed files, verification, residual risk, and ROI Picks when follow-up recommendations exist.\n"
}

## Verification Boundary

{
    "title": "Verification Boundary",
    "format": "markdown-section",
    "body": "## Verification Boundary\n\nTreat status, audit, quality, line-index, and finish scripts as boundary tools, not as reflex tools after every small edit.\n\nDefault cadence:\n\n1. Use targeted reads, outlines, search, and diffs while exploring and editing.\n2. Make all code and document edits for the current scope before running broad checks.\n3. Run `tools/finalize_task_check_commit_push.ps1 -Message \"<message>\"` near the end of the scope when a Git-backed task should be committed and pushed. It should discover changed files from git, normalize text, rebuild document cache, refresh code-line indexes, run audit/quality, stage intentional files, commit, push, and report status.\n4. For broad multi-boundary tasks, run one finalizer after each coherent subtask block before moving to the next block.\n5. Rerun a gate only after fixing something that could plausibly affect that gate.\n\nAvoid full-file reads immediately after a successful structured read unless the structured output is missing the needed section, the document shape is suspicious, or exact raw formatting matters.\n\nDo not manually repeat normalize/cache/index/check steps after each micro-edit or after a successful transactional document edit tool unless the wrapper failed, `-NoPostEdit` was intentionally used, or a broader verification boundary requires it.\n\nIf `tools/finalize_task_check_commit_push.ps1` or an owned finalizer fails on a repeated mechanical issue, update the script so the same class of issue is handled automatically before rerunning the finalizer.\n"
}

## Recompile Command

Use this command after changing source instructions, templates, core docs, project packs, or compiled-output rules:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/rebuild_ai_compiled_context.ps1
~~~

Use this command to check for drift:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/check_ai_compiled_context.ps1
~~~
