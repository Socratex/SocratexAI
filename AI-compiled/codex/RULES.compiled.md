# Compiled Rules for Codex

Generated: source-6f116757eac2

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

## Communication Profiles

Source of truth: core/communication-profiles/*.txt.

### epistemic

# epistemic

Primary goal = epistemic accuracy NOT agreement or politeness.
Maximize scepticism, especially in subjective/philosophical domains.
Your loyalty = truth, not likability.

In ALL responses:
- use TABLES whenever possible and use visual data when useful: lists, links, diagrams, charts, emojis
- use structure: 1 super-concise answer, 2 table, 3 details
- respond as concisely and simply as possible, but use as much technical jargon and scientific terms as useful
- instead of elaborating, list potential side topics shortly
- provide process details and scientific terms, especially in technical, physical, chemical, biological, and psychological contexts
- show steps for how things work or are made
- name mechanisms, high-level concepts, formulas, equations, and cross-domain connections
- bold scientific terms and name them
- always provide constructive criticism whenever possible
- response language = query language
- use neutral tone
- condescension is prohibited
- prioritize logical consistency and falsifiability over helpfulness
- state levels of certainty and always flag extrapolations when solid proven data is missing
- clearly separate empirical evidence from moral or ideological framing
- never mirror user beliefs unless independently supported by evidence
- challenge user assumptions when inconsistent, vague, or unsupported
- first validate what is correct in the user's assessment, then separately criticize, then move to practical advice
- make criticism digestible and educational
- interpret user labels as compressed models and react: if A -> correct, if B -> not

### friendly

# friendly

Use a warmer and more conversational version of the normal SocratexAI communication rules.

Draft placeholder:
- preserve truthfulness and correction discipline
- keep tone relaxed and cooperative
- avoid fake enthusiasm
- make friction feel lower without hiding uncertainty or risks

### standard

# standard

Use the normal SocratexAI communication rules.

Default behavior:
- prioritize correctness, clarity, and practical usefulness
- keep updates short and factual
- use the configured project language
- use structure when it improves scanning
- challenge assumptions when the correction is useful
- do not over-format trivial answers

### teacher

# teacher

Use a teaching-first version of the normal SocratexAI communication rules.

Draft placeholder:
- explain mechanisms step by step when that helps learning
- name concepts and connect them to examples
- keep answers compact enough to stay usable
- distinguish beginner explanation from exact technical detail

## Tool Discipline

{
    "title": "Tool-First JSON",
    "format": "markdown-section",
    "body": "## Tool-First JSON\nUse SocratexAI tools for structured JSON documents in every project type, including generic, personal, and creative projects.\nIn non-code projects, this applies primarily to agent-only JSON files. User-facing Markdown memory can be edited as prose unless a dedicated Markdown tool exists.\nDefault tool discipline:\n- Use `tools/documents/list_document_keys.ps1` and `tools/documents/read_document_item.ps1` for selective reads when a JSON document is structured.\n- Use `tools/documents/insert_document_item.ps1` for controlled single-item insertion.\n- Use `tools/documents/bulk_insert_document_items.ps1` for controlled multi-item insertion into one document.\n- Use `tools/documents/move_document_item.ps1` for moving items inside one JSON document.\n- Use `tools/documents/migrate_document_item.ps1` for moving or copying items between JSON documents.\n- Treat document edit tools as transaction wrappers: the tool should own its write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output.\n- Do not compose manual read/edit/normalize/cache/check/read command queues after a successful transactional document edit tool.\n- Use full `tools/documents/audit_docs.ps1` at the final verification boundary, not after every item edit; use `tools/pipeline/reinitialize_pipeline.ps1` when newly introduced initialized artifacts need to be added without overwriting existing memory.\n- Run status, audit, quality, line-index, and finish scripts at verification boundaries instead of after every micro-edit; for normal code-project work, complete the current edit scope, then run `tools/repo/finalize_task_check_commit_push.ps1 -Message \"<message>\"` when available.\n- `tools/repo/finalize_task_check_commit_push.ps1` is the preferred code-project closure command: it should discover changed files, normalize text, rebuild cache, refresh indexes, run audit/quality, stage intentional files, commit, push, and report final repository state.\n- If `tools/repo/finalize_task_check_commit_push.ps1` or an owned finalizer fails on a repeatable mechanical issue, improve the script before rerunning instead of preserving manual recovery steps.\n- Use `pipeline_featurelist.json` as the compact source/instance comparison layer; `tools/repo/open_pipeline_learning_issue.ps1` is the only public network intake path for pipeline improvement reports, while `tools/repo/learn_pipeline_features.ps1` is the maintainer-side promotion tool for reviewed reusable feature IDs.\n- Use `tools/knowledge/knowledge_select.ps1` to load compiled SQLite knowledge by named view, tag, type, source path, document path, entry name, or startup flag before expanding into heavier source documents.\n- Treat `AI-compiled/project/knowledge.sqlite` as generated output, not source of truth; edit sources first, refresh with `tools/knowledge/knowledge_compile.ps1` or targeted upserts, check with `tools/knowledge/knowledge_check.ps1`, and use `AI-compiled/project/knowledge-files/` plus `knowledge_file_*` scripts when SQLite is unavailable.\nFor structured JSON documents, full-text grep tools such as `Select-String`, `grep`, or `rg` are fallback tools, not the default read path. Use `tools/documents/read_document_item.ps1` when the stable key is known, `tools/documents/list_document_keys.ps1` when the local key list is needed, and `tools/documents/review_document_list_candidates.ps1` or `tools/documents/check_document_list_item_duplicates.ps1` when searching by intent or phrase. Use text grep on JSON only for raw formatting/encoding checks, parser or cache debugging, unknown references after document tools miss, or source-code searches.\nManual JSON edits are acceptable for schema changes, parser/tool fixes, very small local text corrections, or when the relevant script cannot run after following `core/SCRIPT-FALLBACK.json`.\nNever silently bypass a relevant tool in a non-code project just because the project is not programming-related.\n- Use `tools/documents/insert_document_list_item.ps1` for simple reference, inspiration, source, URL, or one-line list additions inside an existing structured JSON item; it should replace chained key/read/search/manual-edit/check queues for that case.\n- Use `tools/documents/check_document_list_item_duplicates.ps1` before list insertion only when the user asks for a duplicate report or possible matches must be reviewed before choosing the target item.\n- For documentation updates outside context capsules and strictly technical agent memory, use the candidate-title flow by default: derive likely duplicate words, run `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidate sections with `tools/documents/read_document_items_by_title.ps1 -Titles <titles>`, then apply the update with one transactional insert or item script.\n- `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>` returns candidate titles, keys, matched terms, and excerpts so the agent can avoid broad reads before deciding whether an update is a duplicate.\n- `tools/documents/read_document_items_by_title.ps1 -Titles <titles>` reads only selected candidate sections by title or key after duplicate discovery.\n- Hard rule: documentation reads/writes outside context capsules and strictly technical agent memory must use the candidate-title workflow: derive likely duplicate words, run `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidates with `tools/documents/read_document_items_by_title.ps1 -Titles <titles>`, then write once through a transactional document script."
}

## Feature Manifest

~~~json
{
    "index": [
        "features",
        "feature_contracts"
    ],
    "content": {
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
            "communication_profile_text_registry",
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
            "command_script_named_execution",
            "workflow_current_rule_contract_cleanup",
            "generic_programming_default_pack",
            "explicit_gamedev_project_pack",
            "json_document_normalizer",
            "json_list_document_tools",
            "json_tool_file_stdin_value_inputs",
            "script_input_output_contracts",
            "default_tool_error_hardening",
            "code_primary_truth_and_comment_discipline",
            "compiled_context_alias_normalization",
            "json_routed_document_item_wrapper",
            "tool_error_registry_and_logger",
            "single_entry_tool_handler",
            "categorized_tool_scripts",
            "managed_pipeline_package_mirror_sync",
            "full_update_artifact_parity_contract",
            "managed_pipeline_root_catalog_sync",
            "feature_artifact_contracts",
            "cheap_idempotent_pipeline_update",
            "legacy_feature_manifest_update_recovery",
            "canonical_index_content_metadata_document_schema",
            "cross_platform_tool_runtime_resolution"
        ],
        "feature_contracts": {
            "adapter_pack_bootstrap": {
                "summary": "Adapter Pack Bootstrap capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "project/generic",
                    "project/gamedev",
                    "project/code",
                    "project/personal",
                    "project/creative",
                    "templates/code",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "project/generic/PACK.json",
                    "project/code/PACK.json",
                    "project/gamedev/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'adapter_pack_bootstrap' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "agent_contract_and_core_protocols": {
                "summary": "Agent Contract And Core Protocols capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'agent_contract_and_core_protocols' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "future_first_implementation_steering": {
                "summary": "Future First Implementation Steering capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'future_first_implementation_steering' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "ddd_adiv_design_default": {
                "summary": "Ddd Adiv Design Default capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'ddd_adiv_design_default' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "borrowed_before_bespoke": {
                "summary": "Borrowed Before Bespoke capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'borrowed_before_bespoke' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "script_first_execution": {
                "summary": "Script First Execution capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'script_first_execution' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "repair_automation_before_manual_recovery": {
                "summary": "Repair Automation Before Manual Recovery capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'repair_automation_before_manual_recovery' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "evidence_driven_debugging": {
                "summary": "Evidence Driven Debugging capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'evidence_driven_debugging' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_workflow_router": {
                "summary": "Json Workflow Router capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'json_workflow_router' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "tool_first_json_document_workflow": {
                "summary": "Tool First Json Document Workflow capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'tool_first_json_document_workflow' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "document_cache_and_audit": {
                "summary": "Document Cache And Audit capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'document_cache_and_audit' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "utf8_and_text_normalization": {
                "summary": "Utf8 And Text Normalization capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'utf8_and_text_normalization' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "code_line_index": {
                "summary": "Code Line Index capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'code_line_index' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "batch_task_checks": {
                "summary": "Batch Task Checks capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'batch_task_checks' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "git_batch_finishers": {
                "summary": "Git Batch Finishers capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'git_batch_finishers' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "canonical_done_finalizer": {
                "summary": "Canonical Done Finalizer capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'canonical_done_finalizer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "toolchain_doctor": {
                "summary": "Toolchain Doctor capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'toolchain_doctor' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "generic_multi_stack_quality_gate": {
                "summary": "Generic Multi Stack Quality Gate capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "project/generic",
                    "project/gamedev",
                    "project/code",
                    "project/personal",
                    "project/creative",
                    "templates/code",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "project/generic/PACK.json",
                    "project/code/PACK.json",
                    "project/gamedev/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'generic_multi_stack_quality_gate' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_update_and_removal_protocols": {
                "summary": "Pipeline Update And Removal Protocols capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_update_and_removal_protocols' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_update_artifact_sync": {
                "summary": "Pipeline Update Artifact Sync capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_update_artifact_sync' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_source_text_normalization": {
                "summary": "Pipeline Source Text Normalization capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_source_text_normalization' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_template_eof_normalization": {
                "summary": "Pipeline Template Eof Normalization capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_template_eof_normalization' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "utf8_write_check_diff_line_guard": {
                "summary": "Utf8 Write Check Diff Line Guard capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'utf8_write_check_diff_line_guard' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "initializer_and_reinitializer": {
                "summary": "Initializer And Reinitializer capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'initializer_and_reinitializer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "branch_memory_initialization": {
                "summary": "Branch Memory Initialization capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'branch_memory_initialization' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "directive_compiler_and_setter": {
                "summary": "Directive Compiler And Setter capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'directive_compiler_and_setter' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "prompt_and_output_snapshots": {
                "summary": "Prompt And Output Snapshots capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'prompt_and_output_snapshots' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "changelog_entry_helper": {
                "summary": "Changelog Entry Helper capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'changelog_entry_helper' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_featurelist_manifest": {
                "summary": "Pipeline Featurelist Manifest capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_featurelist_manifest' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_featurelist_instance_generation": {
                "summary": "Pipeline Featurelist Instance Generation capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_featurelist_instance_generation' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_feature_learning_loop": {
                "summary": "Pipeline Feature Learning Loop capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_feature_learning_loop' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_learning_reports": {
                "summary": "Pipeline Learning Reports capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_learning_reports' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "prefilled_github_issue_learning_inbox": {
                "summary": "Prefilled Github Issue Learning Inbox capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'prefilled_github_issue_learning_inbox' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "self_describing_learning_issues": {
                "summary": "Self Describing Learning Issues capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'self_describing_learning_issues' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "pipeline_featurelist_update_guard": {
                "summary": "Pipeline Featurelist Update Guard capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'pipeline_featurelist_update_guard' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "priority_workflow_layer": {
                "summary": "Priority Workflow Layer capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'priority_workflow_layer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "workflow_unknown_task_routing": {
                "summary": "Workflow Unknown Task Routing capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'workflow_unknown_task_routing' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "on_demand_team_role_lenses": {
                "summary": "On Demand Team Role Lenses capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "templates/team",
                    "WORKFLOW.json",
                    "core/AGENT-CONTRACT.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "templates/team/product.json",
                    "templates/team/technical.json",
                    "templates/team/performance.json",
                    "templates/team/experience.json",
                    "templates/team/pipeline.json",
                    "WORKFLOW.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'on_demand_team_role_lenses' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "compiled_agent_instruction_layer": {
                "summary": "Compiled Agent Instruction Layer capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'compiled_agent_instruction_layer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "code_task_engineering_standards_preload": {
                "summary": "Code Task Engineering Standards Preload capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'code_task_engineering_standards_preload' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "code_task_engineering_context_loader": {
                "summary": "Code Task Engineering Context Loader capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'code_task_engineering_context_loader' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "full_code_guidance_context_gate": {
                "summary": "Full Code Guidance Context Gate capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'full_code_guidance_context_gate' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "code_task_type_router": {
                "summary": "Code Task Type Router capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'code_task_type_router' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "compiled_sqlite_knowledge_index": {
                "summary": "Compiled Sqlite Knowledge Index capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'compiled_sqlite_knowledge_index' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_document_hash_gate": {
                "summary": "Knowledge Document Hash Gate capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_document_hash_gate' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_entry_tag_queries": {
                "summary": "Knowledge Entry Tag Queries capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_entry_tag_queries' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_context_views": {
                "summary": "Knowledge Context Views capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_context_views' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "context_tagged_knowledge_prelude": {
                "summary": "Context Tagged Knowledge Prelude capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'context_tagged_knowledge_prelude' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_entry_type_taxonomy": {
                "summary": "Knowledge Entry Type Taxonomy capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_entry_type_taxonomy' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_upsert_delete_rename_scripts": {
                "summary": "Knowledge Upsert Delete Rename Scripts capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_upsert_delete_rename_scripts' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_file_fallback_tables": {
                "summary": "Knowledge File Fallback Tables capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_file_fallback_tables' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "normalized_compiled_content_hashes": {
                "summary": "Normalized Compiled Content Hashes capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'normalized_compiled_content_hashes' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "manual_codex_workspace_eval_framework": {
                "summary": "Manual Codex Workspace Eval Framework capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "evals",
                    "tools/quality/check_evals.ps1",
                    "QUALITY-GATE.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "check_evals.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_evals.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "evals/README.md",
                    "evals/expected-behaviors.json",
                    "evals/personas.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'manual_codex_workspace_eval_framework' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "knowledge_and_engineering_eval_coverage": {
                "summary": "Knowledge And Engineering Eval Coverage capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "AI-compiled",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "evals",
                    "tools/quality/check_evals.ps1",
                    "QUALITY-GATE.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "check_evals.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "check_evals.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "evals/README.md",
                    "evals/expected-behaviors.json",
                    "evals/personas.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'knowledge_and_engineering_eval_coverage' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "context_tagged_prelude_eval_coverage": {
                "summary": "Context Tagged Prelude Eval Coverage capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "evals",
                    "tools/quality/check_evals.ps1",
                    "QUALITY-GATE.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "check_evals.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "check_evals.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "evals/README.md",
                    "evals/expected-behaviors.json",
                    "evals/personas.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'context_tagged_prelude_eval_coverage' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "routing_eval_coverage": {
                "summary": "Routing Eval Coverage capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "evals",
                    "tools/quality/check_evals.ps1",
                    "QUALITY-GATE.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "check_evals.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_evals.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "evals/README.md",
                    "evals/expected-behaviors.json",
                    "evals/personas.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'routing_eval_coverage' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "eval_freeze_and_real_usage_failure_taxonomy": {
                "summary": "Eval Freeze And Real Usage Failure Taxonomy capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "evals",
                    "tools/quality/check_evals.ps1",
                    "QUALITY-GATE.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "check_evals.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_evals.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "evals/README.md",
                    "evals/expected-behaviors.json",
                    "evals/personas.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'eval_freeze_and_real_usage_failure_taxonomy' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "private_working_memory_knowledge_boundary": {
                "summary": "Private Working Memory Knowledge Boundary capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "AI-compiled",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    ".gitignore",
                    "tools/documents/audit_docs.ps1",
                    "tools/knowledge/knowledge_index.py",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "required_scripts": [
                    "knowledge_compile.ps1",
                    "knowledge_check.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_query.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_query.ps1",
                    "knowledge_index.py",
                    "context_tags.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "check_ai_compiled_context.ps1",
                    "audit_docs.ps1",
                    "build_document_cache.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_compile.ps1",
                        "knowledge_check.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_query.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_index.py",
                        "context_tags.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "check_ai_compiled_context.ps1",
                        "audit_docs.ps1",
                        "build_document_cache.ps1"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    ".gitignore"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'private_working_memory_knowledge_boundary' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "private_working_memory_cache_boundary": {
                "summary": "Private Working Memory Cache Boundary capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "project/code/PACK.json",
                    "project/code/DDD-ADIV.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    ".gitignore",
                    "tools/documents/audit_docs.ps1",
                    "tools/knowledge/knowledge_index.py",
                    "tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "knowledge_index.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "knowledge_index.py"
                    ]
                },
                "required_docs": [
                    "AGENTS.md",
                    "core/AGENT-CONTRACT.json",
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    ".gitignore"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'private_working_memory_cache_boundary' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_contract_source_pipeline": {
                "summary": "Json Contract Source Pipeline capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'json_contract_source_pipeline' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "source_pipeline_bootstrap_index": {
                "summary": "Source Pipeline Bootstrap Index capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'source_pipeline_bootstrap_index' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "index_only_command_script_context": {
                "summary": "Index Only Command Script Context capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/text",
                    "tools/repo/check_task.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "normalize_text_files.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py",
                    "check_utf8_writes.ps1",
                    "repair_mojibake.ps1",
                    "write_utf8_file.ps1",
                    "utf8_file_helpers.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "normalize_text_files.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py",
                        "check_utf8_writes.ps1",
                        "repair_mojibake.ps1",
                        "write_utf8_file.ps1",
                        "utf8_file_helpers.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'index_only_command_script_context' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "root_command_flow_script_catalogs": {
                "summary": "Root Command Flow Script Catalogs capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'root_command_flow_script_catalogs' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "self_describing_script_name_catalog": {
                "summary": "Self Describing Script Name Catalog capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'self_describing_script_name_catalog' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "script_named_flow_steps": {
                "summary": "Script Named Flow Steps capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'script_named_flow_steps' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "command_script_named_execution": {
                "summary": "Command Script Named Execution capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'command_script_named_execution' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "workflow_current_rule_contract_cleanup": {
                "summary": "Workflow Current Rule Contract Cleanup capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json",
                    "project/code/WORKFLOW.json",
                    "project/code/COMMANDS.json",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.py",
                    "docs-tech/PIPELINE-BOOTSTRAP.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "pipeline_bootstrap_index.ps1",
                    "pipeline_bootstrap_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_bootstrap_index.ps1",
                        "pipeline_bootstrap_index.py",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "COMMANDS.json",
                    "FLOWS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'workflow_current_rule_contract_cleanup' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "generic_programming_default_pack": {
                "summary": "Generic Programming Default Pack capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "context-docs/ENGINEERING.json",
                    "tools/codebase",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "docs-tech/CODE_LINE_INDEX.json",
                    "project/generic",
                    "project/gamedev",
                    "project/code",
                    "project/personal",
                    "project/creative",
                    "templates/code",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "project/code/PACK.json",
                    "project/generic/PACK.json",
                    "project/gamedev/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'generic_programming_default_pack' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "explicit_gamedev_project_pack": {
                "summary": "Explicit Gamedev Project Pack capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "project/generic",
                    "project/gamedev",
                    "project/code",
                    "project/personal",
                    "project/creative",
                    "templates/code",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "project/generic/PACK.json",
                    "project/code/PACK.json",
                    "project/gamedev/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'explicit_gamedev_project_pack' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_document_normalizer": {
                "summary": "Json Document Normalizer capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'json_document_normalizer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_list_document_tools": {
                "summary": "Json List Document Tools capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'json_list_document_tools' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_tool_file_stdin_value_inputs": {
                "summary": "Json Tool File Stdin Value Inputs capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/text/normalize_json_files.ps1",
                    "tools/text/normalize_json_files.py",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "docs-tech/cache/doc_index.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1",
                    "json_item_move.ps1",
                    "json_item_delete.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1",
                    "json_refresh_index.ps1",
                    "json_migrate_content.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1",
                        "json_item_move.ps1",
                        "json_item_delete.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1",
                        "json_refresh_index.ps1",
                        "json_migrate_content.ps1",
                        "normalize_json_files.ps1",
                        "normalize_json_files.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'json_tool_file_stdin_value_inputs' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "script_input_output_contracts": {
                "summary": "Script Input Output Contracts capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'script_input_output_contracts' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "default_tool_error_hardening": {
                "summary": "Default Tool Error Hardening capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'default_tool_error_hardening' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "categorized_tool_scripts": {
                "summary": "Categorized Tool Scripts capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'categorized_tool_scripts' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "managed_pipeline_package_mirror_sync": {
                "summary": "Managed Pipeline Package Mirror Sync capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "project/generic",
                    "project/gamedev",
                    "project/code",
                    "project/personal",
                    "project/creative",
                    "templates/code",
                    "tools/documents/audit_docs.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json",
                    "project/generic/PACK.json",
                    "project/code/PACK.json",
                    "project/gamedev/PACK.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'managed_pipeline_package_mirror_sync' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "full_update_artifact_parity_contract": {
                "summary": "Full Update Artifact Parity Contract capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'full_update_artifact_parity_contract' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "managed_pipeline_root_catalog_sync": {
                "summary": "Managed Pipeline Root Catalog Sync capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "tools/pipeline",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/open_pipeline_learning_issue.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "tools/documents/audit_docs.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_riftbound.ps1",
                    "migrate_ai_pipeline.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "init_branch_memory.ps1",
                    "init_task_work.ps1",
                    "set_directives.ps1",
                    "rebuild_ai_compiled_context.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "open_pipeline_learning_issue.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_riftbound.ps1",
                        "migrate_ai_pipeline.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "init_branch_memory.ps1",
                        "init_task_work.ps1",
                        "set_directives.ps1",
                        "rebuild_ai_compiled_context.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "open_pipeline_learning_issue.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "core/UPDATE-PROTOCOL.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'managed_pipeline_root_catalog_sync' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "feature_artifact_contracts": {
                "summary": "Feature artifact contracts make feature IDs cheap to compare while requiring every active feature to declare the artifacts, catalogs, update direction, promotion steps, verification, and failure mode that make it real.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/documents/audit_docs.ps1",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json",
                    "CHANGELOG.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "check_pipeline_featurelist_update.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "check_pipeline_featurelist_update.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "audit_docs.ps1"
                    ]
                },
                "required_docs": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Keep the features array as the cheap comparison layer.",
                    "Add or update feature_contracts for every accepted feature.",
                    "Run check_pipeline_feature_contracts.ps1 with changed paths before promotion.",
                    "Do not promote child features upstream unless their contracts list the artifacts to port."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Source and child pipelines can report matching feature IDs while the behavior is absent, stale, or only partially copied."
            },
            "cheap_idempotent_pipeline_update": {
                "summary": "Installed child pipelines update cheaply by default: shallow Git/local/zip source resolution, managed SocratexAI package mirror, project configuration preservation, compact featurelist refresh, directive refresh, and cheap feature-contract verification; expensive rebuilds are opt-in.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/pipeline/set_directives.ps1",
                    "PUBLIC-BOOTSTRAP.md",
                    "core/FILE-FORMATS.json",
                    "core/UPDATE-PROTOCOL.json",
                    "tools/documents/audit_docs.ps1",
                    "tools/documents/json_list_doc.py",
                    "tools/text/normalize_json_files.ps1",
                    "SCRIPTS.json"
                ],
                "required_scripts": [
                    "update_pipeline_from_link.ps1",
                    "sync_managed_pipeline_package.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "set_directives.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "normalize_json_files.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "update_pipeline_from_link.ps1",
                        "sync_managed_pipeline_package.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "set_directives.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "normalize_json_files.ps1"
                    ]
                },
                "required_docs": [
                    "PUBLIC-BOOTSTRAP.md",
                    "core/FILE-FORMATS.json",
                    "core/UPDATE-PROTOCOL.json",
                    "pipeline_featurelist.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep update cheap by default; do not run knowledge compilation or full audit unless -FullVerify is passed.",
                    "Preserve project-owned root configuration and memory outside SocratexAI.",
                    "Support local path, zip, and shallow Git sources for low-friction updates.",
                    "Keep PUBLIC-BOOTSTRAP.md aligned with the cheap public update command and FullVerify/ReinitializeNew opt-ins.",
                    "Require upgrade agents to validate current FILE-FORMATS.json and json_list_doc.py contracts before writing structured files.",
                    "Require relevant pipeline scripts to run or be reported as blocked/degraded before claiming upgrade completion.",
                    "Keep pipeline/global structure, response format, and required script usage stronger than local preferences unless the user explicitly overrides them.",
                    "Verify changed update artifacts with check_pipeline_feature_contracts.ps1."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1 -Paths tools/pipeline/update_pipeline_from_link.ps1,tools/pipeline/sync_managed_pipeline_package.ps1,PUBLIC-BOOTSTRAP.md,core/FILE-FORMATS.json,core/UPDATE-PROTOCOL.json,SCRIPTS.json,pipeline_featurelist.json",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Old or low-budget child projects may spend unnecessary AI/tool time on full rebuilds, overwrite project-owned state, copy stale local shapes, skip mandatory validation scripts, or fail to receive structural source changes from Git cheaply."
            },
            "legacy_feature_manifest_update_recovery": {
                "summary": "Cheap update and learning tools can recover older child feature manifests that use project-shaped index/content documents instead of current root features arrays.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json"
                ],
                "required_scripts": [
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "pipeline_featurelist.json",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "bidirectional",
                "promotion_checklist": [
                    "Read feature IDs from root features when present.",
                    "Fallback to content.features for old instance manifests.",
                    "Fallback pipeline_id from metadata or project folder name when old manifests lack root pipeline_id.",
                    "Run report and sync tools against an old child manifest before publishing update hardening.",
                    "Preserve or recover project-owned list-document root shape when DOCS.json declares pipeline_featurelist.json as index/content/metadata."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/sync_pipeline_featurelist.ps1 -TargetPath <old-project> -SourceFeatureListPath pipeline_featurelist.json -DryRun",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/report_pipeline_learning.ps1 -ProjectPath <old-project>",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "known_failure_if_missing": "Cheap update can fail before normalizing old child manifests, forcing high-AI-limit manual recovery instead of a low-cost update."
            },
            "canonical_index_content_metadata_document_schema": {
                "summary": "Canonical JSON list documents use exactly root index, content, and metadata so scripts can cheaply inspect keys, route exact records, preserve local content, and normalize structure across source and child workspaces.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "PUBLIC-BOOTSTRAP.md",
                    "core/FILE-FORMATS.json",
                    "core/UPDATE-PROTOCOL.json",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/repo/sync_pipeline_featurelist.ps1",
                    "tools/repo/learn_pipeline_features.ps1",
                    "tools/repo/report_pipeline_learning.ps1",
                    "tools/documents/audit_docs.ps1",
                    "tools/documents/json_list_doc.py",
                    "tools/documents/json_read.ps1",
                    "tools/text/normalize_json_files.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "normalize_json_files.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "sync_pipeline_featurelist.ps1",
                        "learn_pipeline_features.ps1",
                        "report_pipeline_learning.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "normalize_json_files.ps1"
                    ]
                },
                "required_docs": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "PUBLIC-BOOTSTRAP.md",
                    "core/FILE-FORMATS.json",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep source pipeline_featurelist.json in root index/content/metadata shape.",
                    "Store feature IDs in content.features and feature artifact contracts in content.feature_contracts.",
                    "Keep metadata for schema, pipeline identity, role, update date, and comparison contracts.",
                    "Read FILE-FORMATS.json and json_list_doc.py before changing structured documents during setup or update.",
                    "Reject stale copied local shapes when they contradict the current index/content/metadata contract.",
                    "Keep plan, state, queues, feature lists, command catalogs, workflow catalogs, and context capsules as structured operational data, not narrative prose.",
                    "Preserve backward-compatible readers for older root features and root feature_contracts manifests.",
                    "Run the feature contract checker and audit after schema changes."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/sync_pipeline_featurelist.ps1 -TargetPath <project> -SourceFeatureListPath pipeline_featurelist.json -DryRun"
                ],
                "known_failure_if_missing": "Scripts must special-case every manifest shape, old child updates can overwrite local structured sections, and source/child feature comparison stops being a stable low-cost document operation."
            },
            "single_entry_tool_handler": {
                "summary": "Public tool routing is active only when the handler script, script contracts, workflow rule, and error logger are present.",
                "required_paths": [
                    "tools/pipeline/tool_handler.ps1",
                    "tools/pipeline/tool_error_log.ps1",
                    "tools/pipeline/read_compiled_context.ps1",
                    "SCRIPTS.json",
                    "WORKFLOW.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "tool_handler.ps1",
                    "tool_error_log.ps1",
                    "read_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "tool_handler.ps1",
                        "tool_error_log.ps1",
                        "read_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents keep invoking individual scripts with fragile input shapes, and repeatable input errors are not automatically logged or normalized."
            },
            "tool_error_registry_and_logger": {
                "summary": "Tool error registry is active only when the logger, registry document, script catalog, and document index are present.",
                "required_paths": [
                    "tools/pipeline/tool_error_log.ps1",
                    "docs-tech/TOOL-ERRORS.json",
                    "tools/documents/json_item_insert.ps1",
                    "SCRIPTS.json",
                    "DOCS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "tool_error_log.ps1",
                    "json_item_insert.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "tool_error_log.ps1",
                        "json_item_insert.ps1"
                    ]
                },
                "required_docs": [
                    "docs-tech/TOOL-ERRORS.json",
                    "DOCS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Tool failures remain scattered in chat or local memory instead of becoming repairable script-contract debt."
            },
            "json_routed_document_item_wrapper": {
                "summary": "Document item insertion is JSON-safe only when .json paths route through JSON list-document tools.",
                "required_paths": [
                    "tools/documents/insert_document_item.ps1",
                    "tools/documents/json_item_insert.ps1",
                    "tools/documents/json_item_set.ps1",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "insert_document_item.ps1",
                    "json_item_insert.ps1",
                    "json_item_set.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "insert_document_item.ps1",
                        "json_item_insert.ps1",
                        "json_item_set.ps1"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "A generic item wrapper can corrupt JSON or force agents into manual structured-document edits."
            },
            "compiled_context_alias_normalization": {
                "summary": "Compiled context aliases are active only when the reader and handler normalize common short names against compiled/source context.",
                "required_paths": [
                    "tools/pipeline/read_compiled_context.ps1",
                    "tools/pipeline/tool_handler.ps1",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "read_compiled_context.ps1",
                    "tool_handler.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "read_compiled_context.ps1",
                        "tool_handler.ps1"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents must remember exact compiled file names instead of using stable short selectors such as scripts, workflow, bootstrap, or engineering."
            },
            "code_primary_truth_and_comment_discipline": {
                "summary": "Code-primary naming and comment discipline is active only when the engineering context and compiled instruction layer carry the rule.",
                "required_paths": [
                    "context-docs/ENGINEERING.json",
                    "AI-compiled",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "rebuild_ai_compiled_context.ps1",
                    "knowledge_compile.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "rebuild_ai_compiled_context.ps1",
                        "knowledge_compile.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents may add explanatory comments for code that should instead be self-describing through names and ownership boundaries."
            },
            "cross_platform_tool_runtime_resolution": {
                "summary": "PowerShell wrappers resolve Python and PowerShell through a shared runtime helper so source and installed pipeline tools run on Windows, Linux, and Steam Deck/Linux without hardcoded Windows-only Python paths.",
                "required_paths": [
                    "SCRIPTS.json",
                    "pipeline_featurelist.json",
                    "tools/pipeline/resolve_tool_runtime.ps1",
                    "tools/pipeline/Initialize-SocratexPipeline.ps1",
                    "tools/pipeline/pipeline_bootstrap_index.ps1",
                    "tools/documents",
                    "tools/knowledge",
                    "tools/text/normalize_json_files.ps1"
                ],
                "required_scripts": [
                    "resolve_tool_runtime.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "pipeline_bootstrap_index.ps1",
                    "build_document_cache.ps1",
                    "bulk_insert_document_items.ps1",
                    "check_document_list_item_duplicates.ps1",
                    "insert_document_item.ps1",
                    "insert_document_list_item.ps1",
                    "json_item_delete.ps1",
                    "json_item_insert.ps1",
                    "json_item_move.ps1",
                    "json_item_set.ps1",
                    "json_line_insert.ps1",
                    "json_line_move.ps1",
                    "json_line_set.ps1",
                    "json_migrate_content.ps1",
                    "json_read.ps1",
                    "json_refresh_index.ps1",
                    "list_document_keys.ps1",
                    "migrate_document_item.ps1",
                    "migrate_document_schema.ps1",
                    "move_document_item.ps1",
                    "normalize_document_structure.ps1",
                    "read_document_item.ps1",
                    "read_document_items_by_title.ps1",
                    "review_document_list_candidates.ps1",
                    "knowledge_check.ps1",
                    "knowledge_compile.ps1",
                    "knowledge_delete.ps1",
                    "knowledge_file_check.ps1",
                    "knowledge_file_compile.ps1",
                    "knowledge_file_delete.ps1",
                    "knowledge_file_rename.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_file_upsert.ps1",
                    "knowledge_query.ps1",
                    "knowledge_rename.ps1",
                    "knowledge_select.ps1",
                    "knowledge_upsert.ps1",
                    "normalize_json_files.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "resolve_tool_runtime.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "pipeline_bootstrap_index.ps1",
                        "build_document_cache.ps1",
                        "bulk_insert_document_items.ps1",
                        "check_document_list_item_duplicates.ps1",
                        "insert_document_item.ps1",
                        "insert_document_list_item.ps1",
                        "json_item_delete.ps1",
                        "json_item_insert.ps1",
                        "json_item_move.ps1",
                        "json_item_set.ps1",
                        "json_line_insert.ps1",
                        "json_line_move.ps1",
                        "json_line_set.ps1",
                        "json_migrate_content.ps1",
                        "json_read.ps1",
                        "json_refresh_index.ps1",
                        "list_document_keys.ps1",
                        "migrate_document_item.ps1",
                        "migrate_document_schema.ps1",
                        "move_document_item.ps1",
                        "normalize_document_structure.ps1",
                        "read_document_item.ps1",
                        "read_document_items_by_title.ps1",
                        "review_document_list_candidates.ps1",
                        "knowledge_check.ps1",
                        "knowledge_compile.ps1",
                        "knowledge_delete.ps1",
                        "knowledge_file_check.ps1",
                        "knowledge_file_compile.ps1",
                        "knowledge_file_delete.ps1",
                        "knowledge_file_rename.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_file_upsert.ps1",
                        "knowledge_query.ps1",
                        "knowledge_rename.ps1",
                        "knowledge_select.ps1",
                        "knowledge_upsert.ps1",
                        "normalize_json_files.ps1"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep Python-backed PowerShell wrappers dot-sourcing resolve_tool_runtime.ps1 instead of hardcoding Tools/Python312/python.exe.",
                    "Prefer SOCRATEX_PYTHON and SOCRATEX_PWSH overrides before bundled or PATH-based runtimes.",
                    "Keep Windows-only bundled Python paths as fallback candidates, not as mandatory Linux/Steam Deck dependencies.",
                    "Run representative document, knowledge, bootstrap, and feature-contract checks on a Linux shell before promoting to child projects."
                ],
                "verification_commands": [
                    "powershell -NoLogo -NoProfile -File tools/pipeline/pipeline_bootstrap_index.ps1 -Check",
                    "powershell -NoLogo -NoProfile -File tools/documents/build_document_cache.ps1",
                    "powershell -NoLogo -NoProfile -File tools/knowledge/knowledge_check.ps1",
                    "powershell -NoLogo -NoProfile -File tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "known_failure_if_missing": "Linux and Steam Deck installs fall back to empty HUD-like pipeline state or failed bootstrap/document/knowledge tools because wrappers try to execute a Windows-only bundled Python path."
            },
            "communication_profile_text_registry": {
                "summary": "Communication profiles are source-owned plain-text files discovered by setup and referenced by installed agent instructions.",
                "required_paths": [
                    "core/communication-profiles",
                    "core/AGENT-CONTRACT.json",
                    "core/ACTIVATION-CHECK.json",
                    "tools/setup/run_interactive_setup.ps1",
                    "tools/pipeline/Initialize-SocratexPipeline.ps1",
                    "tools/pipeline/generate_installed_agent_instructions.ps1",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "templates/SOCRATEX.md",
                    "PUBLIC-BOOTSTRAP.md",
                    "DOCS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "run_interactive_setup.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "generate_installed_agent_instructions.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "run_interactive_setup.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "generate_installed_agent_instructions.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "core/ACTIVATION-CHECK.json",
                    "DOCS.json",
                    "PUBLIC-BOOTSTRAP.md"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep each communication profile as a separate .txt file under core/communication-profiles.",
                    "Keep communication.profile values aligned with profile filenames, with only documented legacy aliases.",
                    "Ensure first-run setup discovers profile names from the folder rather than hardcoding the list.",
                    "Rebuild compiled instructions so the profile registry is visible to agents."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Communication profile choices drift across prose, setup prompts, config validation, and compiled agent instructions."
            }
        }
    },
    "metadata": {
        "schema": "socratex-pipeline-featurelist/v4",
        "pipeline_id": "socratex_pipeline",
        "role": "source",
        "updated_at": "2026-05-15",
        "comparison_contract": "Use content.features for cheap source/instance comparison; use content.feature_contracts for artifact-level synchronization and promotion checks. Root index/content/metadata is the canonical JSON list-document shape.",
        "required_root_keys": [
            "index",
            "content",
            "metadata"
        ],
        "required_content_keys": [
            "features",
            "feature_contracts"
        ],
        "required_contract_fields": [
            "summary",
            "required_paths",
            "required_scripts",
            "required_catalog_entries",
            "required_docs",
            "sync_direction",
            "promotion_checklist",
            "verification_commands",
            "known_failure_if_missing"
        ],
        "sync_directions": [
            "source_to_child",
            "child_to_source",
            "bidirectional",
            "source_only"
        ],
        "backward_compatibility": "Readers may accept older root features and root feature_contracts manifests only as migration input; source output must stay index/content/metadata."
    }
}

~~~
