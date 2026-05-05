# Compiled Rules for Codex

Generated: source-497156e27702

## Source of Truth

- Source instructions remain authoritative.
- AI-compiled/ is a generated read-optimized cache.
- Do not edit compiled files manually.
- Recompile after source instruction, workflow, template, or pack changes.

## Core Contract Extracts

{
    "title": "Purpose",
    "format": "markdown-section",
    "body": "## Purpose\n\nThis file is the shared instruction contract for all adapters and project packs.\n\nThe agent's job is to preserve project continuity, make state explicit, execute concrete work, and keep decisions falsifiable.\n"
}

{
    "title": "Operating Principles",
    "format": "markdown-section",
    "body": "## Operating Principles\n\n- Prefer epistemic accuracy over agreement, optimism, or style.\n- Separate observed facts, reasoned inference, speculation, and value judgment.\n- Do not mirror the user's belief unless it is independently supported by evidence.\n- Challenge vague, unsupported, contradictory, or likely false assumptions when the correction is useful.\n- State uncertainty explicitly when confidence is limited.\n- Prefer explicit contracts over hidden convention.\n- Preserve momentum when the request is clear.\n- Ask questions only when missing information materially changes the action.\n- Keep project-facing files concise, current, and useful.\n- Read `DOCS.json` before reading, creating, renaming, or updating project documents.\n- Update `DOCS.json` whenever a durable document is added, removed, renamed, or its role changes.\n- Prefer the smallest meaningful ownership slice.\n- Avoid broad sweeps when a narrow contract point solves the problem.\n- Do not delete unresolved requirements; move, merge, split, or demote them into the correct planning layer.\n- Prefer high-ROI improvements over comprehensive but low-impact passes.\n- When suggesting multiple improvements, rank them by ROI and call out the top one to three explicitly.\n- Distinguish what looks good in abstraction from what pays off for this project's profile. The latter wins.\n- For every user command or substantive question, load the main workflow/instruction context first, derive context tags from the user text when a tag extractor is available, then query the compiled knowledge layer by those tags before answering or executing. Treat tag-selected notes as routing context, not a replacement for exact source reads when edits or high-stakes claims depend on source truth.\n"
}

{
    "title": "Project Memory Layers",
    "format": "markdown-section",
    "body": "## Project Memory Layers\n\nUse these concepts regardless of file names:\n\n- Active state: the current checkpoint, next action, blockers, and risks.\n- Workflow: owner-written active pain points, priority challenge rules, and team-on-demand routing.\n- Execution plan: active and near-future passes.\n- Backlog: valuable work not yet selected for execution.\n- Decision log: durable choices and why they were made.\n- Issue registry: active defects, risks, or unresolved problems.\n- Context capsules: short technical or domain memory that prevents rereading or repeated mistakes.\n- Completion log: shipped outcomes and major fixes.\n\nRequired selective reads:\n- `core/PROMOTION-RULES.json` before moving work between memory layers.\n- `core/PROJECT-PROFILE.json` when `PIPELINE-CONFIG.json` contains `project_profile`.\n- `core/ROI-BIAS.json` before ranking recommendations, planning work, or reviewing tradeoffs.\n- `core/SCRIPT-FALLBACK.json` before bypassing any script that cannot run.\n- `core/TASK-WORK.json` before broad multi-step work that needs a temporary micro-task plan.\n- `core/INSTRUCTION-CAPTURE.json` before rewriting files that collect raw user instructions.\n- `core/FILE-FORMATS.json` before creating or renaming project memory files.\n- `WORKFLOW.json` after active state only when priority steering, feature triage, planning, or broad project-risk judgment matters.\n- `team/*.json` only on demand: when the user names a role, asks for team-style review, or `WORKFLOW.json` routes the task to that role. Treat team files as decision lenses, not default context.\n"
}

## Tool Discipline

{
    "title": "Tool-First JSON",
    "format": "markdown-section",
    "body": "## Tool-First JSON\nUse SocratexAI tools for structured JSON documents in every project type, including generic, personal, and creative projects.\nIn non-code projects, this applies primarily to agent-only JSON files. User-facing Markdown memory can be edited as prose unless a dedicated Markdown tool exists.\nDefault tool discipline:\n- Use `tools/list_document_keys.ps1` and `tools/read_document_item.ps1` for selective reads when a JSON document is structured.\n- Use `tools/insert_document_item.ps1` for controlled single-item insertion.\n- Use `tools/bulk_insert_document_items.ps1` for controlled multi-item insertion into one document.\n- Use `tools/move_document_item.ps1` for moving items inside one JSON document.\n- Use `tools/migrate_document_item.ps1` for moving or copying items between JSON documents.\n- Treat document edit tools as transaction wrappers: the tool should own its write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output.\n- Do not compose manual read/edit/normalize/cache/check/read command queues after a successful transactional document edit tool.\n- Use full `tools/audit_docs.ps1` at the final verification boundary, not after every item edit; use `tools/reinitialize_pipeline.ps1` when newly introduced initialized artifacts need to be added without overwriting existing memory.\n- Run status, audit, quality, line-index, and finish scripts at verification boundaries instead of after every micro-edit; for normal code-project work, complete the current edit scope, then run `tools/finalize_task_check_commit_push.ps1 -Message \"<message>\"` when available.\n- `tools/finalize_task_check_commit_push.ps1` is the preferred code-project closure command: it should discover changed files, normalize text, rebuild cache, refresh indexes, run audit/quality, stage intentional files, commit, push, and report final repository state.\n- If `tools/finalize_task_check_commit_push.ps1` or an owned finalizer fails on a repeatable mechanical issue, improve the script before rerunning instead of preserving manual recovery steps.\n- Use `pipeline_featurelist.json` as the compact source/instance comparison layer; `tools/open_pipeline_learning_issue.ps1` is the only public network intake path for pipeline improvement reports, while `tools/learn_pipeline_features.ps1` is the maintainer-side promotion tool for reviewed reusable feature IDs.\n- Use `tools/knowledge_select.ps1` to load compiled SQLite knowledge by named view, tag, type, source path, document path, entry name, or startup flag before expanding into heavier source documents.\n- Treat `AI-compiled/project/knowledge.sqlite` as generated output, not source of truth; edit sources first, refresh with `tools/knowledge_compile.ps1` or targeted upserts, check with `tools/knowledge_check.ps1`, and use `AI-compiled/project/knowledge-files/` plus `knowledge_file_*` scripts when SQLite is unavailable.\nFor structured JSON documents, full-text grep tools such as `Select-String`, `grep`, or `rg` are fallback tools, not the default read path. Use `tools/read_document_item.ps1` when the stable key is known, `tools/list_document_keys.ps1` when the local key list is needed, and `tools/doc_route.ps1` or `tools/doc_search.ps1` when searching by intent or phrase. Use text grep on JSON only for raw formatting/encoding checks, parser or cache debugging, unknown references after document tools miss, or source-code searches.\nManual JSON edits are acceptable for schema changes, parser/tool fixes, very small local text corrections, or when the relevant script cannot run after following `core/SCRIPT-FALLBACK.json`.\nNever silently bypass a relevant tool in a non-code project just because the project is not programming-related.\n- Use `tools/insert_document_list_item.ps1` for simple reference, inspiration, source, URL, or one-line list additions inside an existing structured JSON item; it should replace chained key/read/search/manual-edit/check queues for that case.\n- Use `tools/check_document_list_item_duplicates.ps1` before list insertion only when the user asks for a duplicate report or possible matches must be reviewed before choosing the target item.\n- For documentation updates outside context capsules and strictly technical agent memory, use the candidate-title flow by default: derive likely duplicate words, run `tools/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidate sections with `tools/read_document_items_by_title.ps1 -Titles <titles>`, then apply the update with one transactional insert or item script.\n- `tools/check_document_list_item_duplicates.ps1 -Terms <words>` returns candidate titles, keys, matched terms, and excerpts so the agent can avoid broad reads before deciding whether an update is a duplicate.\n- `tools/read_document_items_by_title.ps1 -Titles <titles>` reads only selected candidate sections by title or key after duplicate discovery.\n- Hard rule: documentation reads/writes outside context capsules and strictly technical agent memory must use the candidate-title workflow: derive likely duplicate words, run `tools/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidates with `tools/read_document_items_by_title.ps1 -Titles <titles>`, then write once through a transactional document script."
}

## Feature Manifest

~~~json
{
    "schema": "socratex-pipeline-featurelist/v2",
    "pipeline_id": "socratex_pipeline",
    "role": "source",
    "updated_at": "2026-05-05",
    "features": [
        "adapter_pack_bootstrap",
        "agent_contract_and_core_protocols",
        "future_first_implementation_steering",
        "ddd_adiv_design_default",
        "borrowed_before_bespoke",
        "script_first_execution",
        "repair_automation_before_manual_recovery",
        "evidence_driven_debugging",
        "json_workflow_router",
        "tool_first_json_document_workflow",
        "document_cache_and_audit",
        "utf8_and_text_normalization",
        "code_line_index",
        "batch_task_checks",
        "git_batch_finishers",
        "canonical_done_finalizer",
        "toolchain_doctor",
        "generic_multi_stack_quality_gate",
        "pipeline_update_and_removal_protocols",
        "pipeline_update_artifact_sync",
        "pipeline_source_text_normalization",
        "pipeline_template_eof_normalization",
        "utf8_write_check_diff_line_guard",
        "initializer_and_reinitializer",
        "branch_memory_initialization",
        "directive_compiler_and_setter",
        "prompt_and_output_snapshots",
        "changelog_entry_helper",
        "pipeline_featurelist_manifest",
        "pipeline_featurelist_instance_generation",
        "pipeline_feature_learning_loop",
        "pipeline_learning_reports",
        "prefilled_github_issue_learning_inbox",
        "self_describing_learning_issues",
        "pipeline_featurelist_update_guard",
        "priority_workflow_layer",
        "workflow_unknown_task_routing",
        "on_demand_team_role_lenses",
        "compiled_agent_instruction_layer",
        "code_task_engineering_standards_preload",
        "code_task_engineering_context_loader",
        "full_code_guidance_context_gate",
        "code_task_type_router",
        "compiled_sqlite_knowledge_index",
        "knowledge_document_hash_gate",
        "knowledge_entry_tag_queries",
        "knowledge_context_views",
        "context_tagged_knowledge_prelude",
        "knowledge_entry_type_taxonomy",
        "knowledge_upsert_delete_rename_scripts",
        "knowledge_file_fallback_tables",
        "normalized_compiled_content_hashes",
        "manual_codex_workspace_eval_framework",
        "knowledge_and_engineering_eval_coverage",
        "context_tagged_prelude_eval_coverage",
        "routing_eval_coverage",
        "eval_freeze_and_real_usage_failure_taxonomy",
        "private_working_memory_knowledge_boundary",
        "private_working_memory_cache_boundary",
        "json_contract_source_pipeline",
        "source_pipeline_bootstrap_index",
        "index_only_command_script_context",
        "root_command_flow_script_catalogs",
        "self_describing_script_name_catalog",
        "script_named_flow_steps",
        "generic_programming_default_pack",
        "explicit_gamedev_project_pack",
        "json_document_normalizer"
    ]
}

~~~
