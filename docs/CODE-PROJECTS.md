# Code Projects

## Summary

This guide explains the programming-specific SocratexPipeline workflow.

## Required Reads

For code projects, the agent reads:

- `core/AGENT-CONTRACT.yaml`
- `core/FILE-FORMATS.yaml`
- `core/PROMOTION-RULES.yaml`
- `core/CONTEXT-COMPACTION.yaml`
- `core/INSTRUCTION-CAPTURE.yaml`
- `core/PROJECT-PROFILE.yaml` when `project_profile` exists
- `core/ROI-BIAS.yaml`
- `core/SCRIPT-FALLBACK.yaml`
- `core/TASK-WORK.yaml` for broad multi-step tasks
- `project/code/WORKFLOW.yaml`
- `project/code/BRANCH-MODE.yaml` when `workflow.branch_mode` is `branch_scoped`
- `project/code/COMMANDS.yaml`
- `project/code/REGISTRIES.yaml`
- `project/code/DDD-ADIV.yaml`
- `project/code/GIT.yaml`
- `project/code/FROZEN-LAYERS.yaml`
- `project/code/INSTRUCTION-CAPTURE.yaml`
- `project/code/DIAGNOSTICS.yaml`

## Main Commands

- `CONTINUE`: execute the next active pass.
- `PLAN`: promote backlog into executable passes.
- `BUG`: work the best active bug.
- `REVIEW`: inspect risk and defects first.
- `AUDIT`: check document consistency.
- `FINISH`: run checks and close the task.
- `COMMIT`: stage explicit paths and commit.
- `DIAGNOSTICS`: inspect logs and evidence.
- `PROMPT`: execute or defragment prompt intake.
- `INSTRUCTIONS`: defragment raw user instruction intake.

## Helper Scripts

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/task_snapshot.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File tools/finish_task.ps1 -Quality
powershell -NoProfile -ExecutionPolicy Bypass -File tools/commit_task.ps1 -Message "<message>" -Paths <explicit paths>
powershell -NoProfile -ExecutionPolicy Bypass -File tools/log_summary.ps1 -Description "<diagnostic description>"
python tools/check_runtime.py --root-key runtime_status
powershell -NoProfile -ExecutionPolicy Bypass -File tools/init_task_work.ps1 -Title "<task>" -SourceRequest "<request>"
```

## File Formats

Programming projects use YAML and JSON for standardized project memory, registries, diagnostics, configuration, indexes, and AI-readable structured documents.

Markdown in programming projects is reserved for scratch intake such as `_INSTRUCTIONS.md`, temporary notes, rough drafts, and short human-facing docs.

Branch-scoped mode also uses Markdown for local prompt-language working files under `ignored/ai-socratex/`.

## Project Profile

`PIPELINE-CONFIG.yaml` stores `project_profile`.

The agent uses it to filter known solutions. Legacy and low-test projects bias toward characterization tests, seams, adapters, and minimal-invasive modernization. Greenfield projects can bias toward cleaner DDD-ADIV structure and framework-native foundations.

## Feature And Bug Steering

For every new feature request, suggestion, or architecture discussion, the agent should first check whether the requested work can be implemented in the most future-proof, maintainable, profile-fitting way.

For software and game projects, use AAA-grade architecture as the steer-direction when appropriate: explicit ownership, data flow, contracts, diagnostics, performance budget, toolability, deterministic behavior where relevant, testability, and low retrofit cost.

For bug reports, first check whether the bug exposes a deeper ownership, lifecycle, contract, data-flow, tooling, observability, or architecture weakness. Prefer the smallest fix that removes the bug class or improves diagnosis instead of only patching the symptom.

## Branch-Scoped Mode

When `workflow.branch_mode` is `branch_scoped`, committed directives live under `.aiassistant/` while local branch memory lives under `ignored/ai-socratex/`.

The agent starts each session by detecting the branch and reading or creating `<branch>-STATE.md` and `<branch>-PLAN.md`.

## ROI Picks

Reviews, plans, and finish reports should include one to three ROI Picks when recommendations remain.

ROI Picks rank work by value axes, cost axes, profile fit, and why the improvement is worth doing now.

## Script Fallback

Before silently bypassing a script, the agent follows `core/SCRIPT-FALLBACK.yaml`.

Missing runtimes should be reported as setup issues with install hints before manual fallback.

PowerShell 7 (`pwsh`) is the preferred automation runtime. If it is missing during setup, run `tools/install_powershell.ps1`, ask before applying the install command, then rerun the runtime check. If PowerShell is unsupported, recommend lite/no-tools mode, a supported host/container, or porting required scripts.

## Broad Task Work

For broad multi-step tasks, the agent should create temporary task work at `docs-tech/cache/current_task.yaml`, track micro-task status during execution, then delete it or promote only durable facts.

For moving items between structured YAML documents, the agent should use `tools/doc_item_migrate.ps1` instead of manual editing.

## Transactional Document Editing

For structured YAML documents, use document edit tools instead of ad hoc inline PowerShell or manual command queues.

Use:

- `tools/doc_item_insert.ps1` for one keyed item,
- `tools/doc_item_bulk_insert.ps1` for multiple keyed items in one document,
- `tools/doc_item_move.ps1` for ordering inside one document,
- `tools/doc_item_migrate.ps1` for moving or copying between documents,
- `tools/docs_slim.ps1` and `tools/docs_migrator.ps1` for whole-document format passes.

These scripts should own the write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output.

Do not manually repeat normalize, cache, check, or readback commands after a successful transactional document edit unless the wrapper failed, `-NoPostEdit` was intentionally used, or a broader verification boundary requires it.

## YAML Read Discipline

For structured YAML documents, use document tools before text grep:

- `tools/doc_read.ps1` when the stable key is known,
- `tools/doc_keys.ps1` when the local key list is needed,
- `tools/doc_route.ps1` or `tools/doc_search.ps1` when searching by intent or phrase.

`Select-String`, `grep`, and `rg` are fallback tools for YAML documents. Use them only for raw formatting or encoding checks, parser/cache debugging, unknown references after document tools miss, or source-code searches.

## Verification Boundary

Use targeted reads, outlines, search, and diffs during exploration and editing.

Run status, audit, quality, line-index, finish, and commit helpers at workflow boundaries:

- once near the end of a small task,
- once after a coherent change block in broad multi-boundary work,
- again only after a fix that could affect the checked gate.

Do not run `git status`, `git diff --check`, `tools/check_task.ps1`, `tools/run_quality_gate.ps1`, `tools/update_code_line_index.ps1`, or `tools/finish_task.ps1` after every small edit.

Do not follow a successful `tools/doc_read.ps1` with a full `Get-Content` of the same document unless the selected output is insufficient, raw formatting matters, or the document structure looks suspicious.

## Quality Gate

`tools/run_quality_gate.ps1` auto-detects common ecosystems.

For serious projects, pass an explicit command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/run_quality_gate.ps1 -Command "npm test"
```
