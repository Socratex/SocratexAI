# Compiled Rules for Codex

Generated: source-295aabc97f43

## Source of Truth

- Source instructions remain authoritative.
- `AI-compiled/` is a generated read-optimized cache.
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
    "body": "## Operating Principles\n\n- Prefer epistemic accuracy over agreement, optimism, or style.\n- Separate observed facts, reasoned inference, speculation, and value judgment.\n- Do not mirror the user's belief unless it is independently supported by evidence.\n- Challenge vague, unsupported, contradictory, or likely false assumptions when the correction is useful.\n- State uncertainty explicitly when confidence is limited.\n- Prefer explicit contracts over hidden convention.\n- Preserve momentum when the request is clear.\n- Ask questions only when missing information materially changes the action.\n- Keep project-facing files concise, current, and useful.\n- Read `DOCS.json` before reading, creating, renaming, or updating project documents.\n- Update `DOCS.json` whenever a durable document is added, removed, renamed, or its role changes.\n- Prefer the smallest meaningful ownership slice.\n- Avoid broad sweeps when a narrow contract point solves the problem.\n- Do not delete unresolved requirements; move, merge, split, or demote them into the correct planning layer.\n- Prefer high-ROI improvements over comprehensive but low-impact passes.\n- When suggesting multiple improvements, rank them by ROI and call out the top one to three explicitly.\n- Distinguish what looks good in abstraction from what pays off for this project's profile. The latter wins.\n- For every user command or substantive question, load the main workflow/instruction context first, derive context tags from the user text when a tag extractor is available, then query the compiled knowledge layer by those tags before answering or executing. Treat tag-selected notes as routing context, not a replacement for exact source reads when edits or high-stakes claims depend on source truth.\n- When improving reusable SocratexPipeline behavior, keep source contracts, project packs, templates, feature contracts, and compiled/update surfaces in parity. If the user says to improve the template too, treat template parity as mandatory acceptance criteria, not as a follow-up.\n"
}


{
    "title": "Project Memory Layers",
    "format": "markdown-section",
    "body": "## Project Memory Layers\n\nUse these concepts regardless of file names:\n\n- Active state: the current checkpoint, next action, blockers, and risks.\n- Workflow: owner-written active pain points, priority challenge rules, and team-on-demand routing.\n- Execution plan: active and near-future passes.\n- Backlog: valuable work not yet selected for execution.\n- Decision log: durable choices and why they were made.\n- Issue registry: active defects, risks, or unresolved problems.\n- Context capsules: short technical or domain memory that prevents rereading or repeated mistakes.\n- Completion log: shipped outcomes and major fixes.\n\nContext tier rule: keep Tier 1 as the small always-loaded core and decision gates; route operating rules through Tier 2, deep patterns through Tier 3, history/vision/backlog through Tier 4, and FOMO/inactive inspiration through Tier 5. Read `core/CONTEXT-TIERS.json` before changing directive hierarchy, startup context, knowledge tiering, or context budgets.\n\nRequired selective reads:\n- `core/PROMOTION-RULES.json` before moving work between memory layers.\n- `core/CONTEXT-TIERS.json` before changing directive hierarchy, context budget, compiled-knowledge routing, or knowledgebase tier metadata.\n- `core/PROJECT-PROFILE.json` when `PIPELINE-CONFIG.json` contains `project_profile`.\n- `core/ROI-BIAS.json` before ranking recommendations, planning work, or reviewing tradeoffs.\n- `core/SCRIPT-FALLBACK.json` before bypassing any script that cannot run.\n- `core/TASK-WORK.json` before broad multi-step work that needs a temporary micro-task plan.\n- `core/INSTRUCTION-CAPTURE.json` before rewriting files that collect raw user instructions.\n- `core/FILE-FORMATS.json` before creating or renaming project memory files.\n- `WORKFLOW.json` after active state only when priority steering, feature triage, planning, or broad project-risk judgment matters.\n- `team/*.json` only on demand: when the user names a role, asks for team-style review, or `WORKFLOW.json` routes the task to that role. Treat team files as decision lenses, not default context.\n"
}


## Context Tiers

~~~json
{
    "index": [
        "quick_index",
        "purpose",
        "tier_model",
        "human_in_loop_research_gate",
        "budget_sequence",
        "knowledge_tiering",
        "consolidation_trigger",
        "migration_policy"
    ],
    "content": {
        "quick_index": {
            "title": "Quick Index",
            "content": "- Purpose\n- Tier Model\n- Human In Loop Research Gate\n- Budget Sequence\n- Knowledge Tiering\n- Consolidation Trigger\n- Migration Policy\n"
        },
        "purpose": {
            "title": "Purpose",
            "content": "This contract defines how SocratexPipeline separates always-loaded directives, routed operating guidance, deep references, historical memory, and inactive inspiration so context stays reliable under pressure."
        },
        "tier_model": {
            "title": "Tier Model",
            "value": [
                {
                    "tier": 1,
                    "name": "Core Directives And Decision Gates",
                    "load_policy": "Always loaded.",
                    "contents": "Small directive layer: instruction authority, read order, safety, routing entrypoints, finish/finalizer rule, and direction-setting gates that must shape every task before task-specific context is loaded. This includes short reminders for workflow/flows discipline, DDD-ADIV, source-of-truth ownership, research/web-research, borrowed-before-invented, and lightweight-futureproof thinking.",
                    "exclude": "Detailed implementation content, domain-specific lenses, long examples, archetype catalogs, backlog, vision, or detailed project-profile doctrine."
                },
                {
                    "tier": 2,
                    "name": "Routed Operating Rules",
                    "load_policy": "Loaded by task type, profile, flow, command, or selected knowledge view.",
                    "contents": "Executable operating guidance loaded after the Tier 1 directive says what direction to preserve: task-type rules, profile routes, concise profile-specific constraints, and operational details that are useful only after the task route is known.",
                    "exclude": "Long pattern explanations, historical reasoning, and inactive ideas."
                },
                {
                    "tier": 3,
                    "name": "Patterns, Archetypes, And Deep References",
                    "load_policy": "Loaded on demand by tags, explicit research need, or exact subsystem scope.",
                    "contents": "Known-solution archetypes, examples, detailed implementation patterns, project-specific deep guidance, architecture maps, and longer diagnostic or performance references.",
                    "exclude": "Always-loaded startup guidance unless a short Tier 1 or Tier 2 pointer routes to it."
                },
                {
                    "tier": 4,
                    "name": "History, Vision, And Simplified Backlog",
                    "load_policy": "Discoverable through indexes/search, never default-loaded.",
                    "contents": "Project history, current and long-horizon vision, deferred but meaningful backlog, past decisions, and inactive but still plausible future work.",
                    "exclude": "Loose FOMO inspiration that is not yet a real project direction."
                },
                {
                    "tier": 5,
                    "name": "FOMO And Inactive Inspiration",
                    "load_policy": "Discoverable only when explicitly requested or when the user reactivates the idea.",
                    "contents": "Loose inspirations, maybe-someday ideas, raw reference dumps, and low-confidence future possibilities.",
                    "exclude": "Active plan, current blockers, or rules required for reliable task execution."
                }
            ]
        },
        "human_in_loop_research_gate": {
            "title": "Human In Loop Research Gate",
            "content": "Tier 1 carries only the short gate: when a non-obvious write-code, feature, bug, performance, runtime, migration, or architecture task lacks a researched and named mechanism, ask concise business/product-direction and technical-implication questions before research. Questions should target scale, dynamism, count, frequency, modularity, dependencies, performance pressure, extensibility, data ownership, and whether behavior should be functional, visual, structural, or only presentation-level. After the user answers, run the research through project/profile philosophy, then name the implementation mechanism in the plan or execution note before editing."
        },
        "budget_sequence": {
            "title": "Budget Sequence",
            "content": "Classify tiers before setting or enforcing exact budget numbers. Default source-pipeline target: Tier 1 should stay roughly 3-5k tokens for reusable core instructions excluding routed knowledge, but the exact budget must be calibrated after tier ownership is clear. If Tier 1 grows because an item feels important rather than because it is needed before routing, demote it to Tier 2 or lower and leave a pointer."
        },
        "knowledge_tiering": {
            "title": "Knowledge Tiering",
            "content": "Knowledge entries may declare `context_tier` from 1 to 5. When omitted, compiled knowledge assigns an effective tier: `load_at_start=true` becomes Tier 2 and other knowledge entries become Tier 3. Tier 1 is allowed for short durable directives whose role is `remember this direction`, not for detailed implementation content. Selection tools may filter by exact context tier or maximum tier when a task needs a bounded context slice."
        },
        "consolidation_trigger": {
            "title": "Consolidation Trigger",
            "content": "If three sessions show observed instruction drift, repeated ignored clear directives, or recurring context-pressure misses, schedule a consolidation pass. The trigger opens a tier/budget review; it does not automatically promote more content into Tier 1."
        },
        "migration_policy": {
            "title": "Migration Policy",
            "content": "Do not pretend a full knowledgebase retag happened through a quick partial sweep. Passes may add the tier contract, compiler support, defaults, and high-value seed tags first. A full SocratexAI or child-project knowledgebase retag is a separate audit pass across all source documents, with before/after counts and owner-visible results. The first real migration should keep tier metadata close to entries with explicit `context_tier`; entries that mix multiple tiers must be split into focused entries before tier assignment. Do not physically split files by tier until entry-level metadata is reliable enough for migration-tool-assisted movement."
        }
    },
    "metadata": {
        "document": {
            "title": "Context Tiers",
            "type": "core_contract",
            "language": "en"
        }
    }
}

~~~

## Communication Profiles

Source of truth: `core/communication-profiles/*.txt`.

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

### foreign_legacy_code

# foreign_legacy_code

Communication profile for work on foreign or legacy business codebases where the agent does not fully know the domain, the codebase is messy, and the user is the domain reviewer plus tester.

Builds on the epistemic profile baseline with three additions tuned for this work shape: business-storytelling end-of-task report, explicit unknown-unknown surfacing, and manual test scenarios for what cannot be auto-tested.

Primary goal = epistemic accuracy NOT agreement or politeness.
Maximize scepticism, especially in subjective/philosophical domains.
Your loyalty = truth, not likability.

In ALL responses:
- 1 thought per line, short and simplified lines
- use TABLES whenever possible and use visual data when useful: lists, links, diagrams, charts, emojis
- use structure: 1 super-concise answer, 2 table, 3 details
- respond as concisely and simply as possible, but use as much technical jargon and scientific terms as useful
- instead of elaborating, list potential side topics shortly
- provide process details and scientific terms, especially in technical, physical, chemical, biological, and psychological contexts
- show steps for how things work or are made
- name mechanisms, high-level concepts, formulas, equations, and cross-domain connections
- bold scientific and technical terms and name them
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

Additions for foreign/legacy business work:

1. Business storytelling for end-of-task report.
   When summarizing what was done after a code-touch task, report in two compact sections in domain language with no technical jargon:
   - what was needed or what was the problem (simplified)
   - what I did (simplified)
   The storytelling layer goes into chat reply AND into branch STATE under session_handoff_* so the user can paste it into PR description, ticket comment, or deployment plan.
   Technical detail stays in code diff and STATE technical sections, not in the storytelling.

2. Explicit unknown-unknown surfacing.
   When the agent does not know how a piece of business logic, framework primitive, integration, or external dependency is supposed to work, say so explicitly.
   Do not extrapolate from name conventions, file structure, imports, or surrounding code comments as if they were documented specifications.
   When the agent guesses, label the guess; when the agent does not know, name the gap and ask the user before extrapolating.

3. Test scenarios for what cannot be safely auto-tested.
   When verification cannot be executed by the agent alone (UI clicks, OAuth flows, prod-only paths, third-party integration side effects, write-and-rollback risks), produce a step-by-step manual test scenario in PLAN:
   - where to click or what to call
   - what input to use
   - what signal indicates success
   - what signal indicates failure
   - expected before/after state
   The user runs the scenario and reports back; agent updates STATE with results.

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
    "body": "## Tool-First JSON\nUse SocratexAI tools for structured JSON documents in every project type, including generic, personal, and creative projects.\nIn non-code projects, this applies primarily to agent-only JSON files. User-facing Markdown memory can be edited as prose unless a dedicated Markdown tool exists.\nDefault tool discipline:\n- Use `tools/documents/list_document_keys.ps1` and `tools/documents/read_document_item.ps1` for selective reads when a JSON document is structured.\n- Use `tools/documents/insert_document_item.ps1` for controlled single-item insertion.\n- Use `tools/documents/bulk_insert_document_items.ps1` for controlled multi-item insertion into one document.\n- Use `tools/documents/move_document_item.ps1` for moving items inside one JSON document.\n- Use `tools/documents/migrate_document_item.ps1` for moving or copying items between JSON documents.\n- Use `tools/json/json_node_edit.ps1` when the full JSON node path is known, including nested list nodes and keys with dots through slash-separated paths.\n- For JSON operations that only change structure or order, such as move, reorder, delete, insert before/after, or migrate, use document/JSON scripts instead of manual JSON editing.\n- If one task requires both structural/order changes and content edits, perform the scripted structural operation first, then set or patch the content.\n- Treat document edit tools as transaction wrappers: the tool should own its write, UTF-8 normalization, cache refresh when applicable, compact local check, and final status output.\n- Do not compose manual read/edit/normalize/cache/check/read command queues after a successful transactional document edit tool.\n- Use full `tools/documents/audit_docs.ps1` at the final verification boundary, not after every item edit; use `tools/pipeline/reinitialize_pipeline.ps1` when newly introduced initialized artifacts need to be added without overwriting existing memory.\n- Run status, audit, quality, line-index, and finish scripts at verification boundaries instead of after every micro-edit; for normal code-project work, complete the current edit scope, then run `tools/repo/finalize_task_check_commit_push.ps1 -Message \"<message>\"` when available.\n- `tools/repo/finalize_task_check_commit_push.ps1` is the preferred code-project closure command: it should discover changed files, normalize text, rebuild cache, refresh indexes, run audit/quality, stage intentional files, commit, push, and report final repository state.\n- If `tools/repo/finalize_task_check_commit_push.ps1` or an owned finalizer fails on a repeatable mechanical issue, improve the script before rerunning instead of preserving manual recovery steps.\n- Use `pipeline_featurelist.json` as the compact source/instance comparison layer; `tools/repo/open_pipeline_learning_issue.ps1` is the only public network intake path for pipeline improvement reports, while `tools/repo/learn_pipeline_features.ps1` is the maintainer-side promotion tool for reviewed reusable feature IDs.\n- Use `tools/knowledge/knowledge_select.ps1` to load compiled SQLite knowledge by named view, tag, type, source path, document path, entry name, or startup flag before expanding into heavier source documents.\n- Treat `AI-compiled/project/knowledge.sqlite` as generated output, not source of truth; edit sources first, refresh with `tools/knowledge/knowledge_compile.ps1` or targeted upserts, check with `tools/knowledge/knowledge_check.ps1`, and use `AI-compiled/project/knowledge-files/` plus `knowledge_file_*` scripts when SQLite is unavailable.\nFor structured JSON documents, full-text grep tools such as `Select-String`, `grep`, or `rg` are fallback tools, not the default read path. Use `tools/documents/read_document_item.ps1` when the stable key is known, `tools/documents/list_document_keys.ps1` when the local key list is needed, and `tools/documents/review_document_list_candidates.ps1` or `tools/documents/check_document_list_item_duplicates.ps1` when searching by intent or phrase. Use text grep on JSON only for raw formatting/encoding checks, parser or cache debugging, unknown references after document tools miss, or source-code searches.\nManual JSON edits are acceptable for schema changes, parser/tool fixes, very small local text corrections, or when the relevant script cannot run after following `core/SCRIPT-FALLBACK.json`.\nNever silently bypass a relevant tool in a non-code project just because the project is not programming-related.\n- Use `tools/documents/insert_document_list_item.ps1` for simple reference, inspiration, source, URL, or one-line list additions inside an existing structured JSON item; it should replace chained key/read/search/manual-edit/check queues for that case.\n- Use `tools/documents/check_document_list_item_duplicates.ps1` before list insertion only when the user asks for a duplicate report or possible matches must be reviewed before choosing the target item.\n- For documentation updates outside context capsules and strictly technical agent memory, use the candidate-title flow by default: derive likely duplicate words, run `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidate sections with `tools/documents/read_document_items_by_title.ps1 -Titles <titles>`, then apply the update with one transactional insert or item script.\n- `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>` returns candidate titles, keys, matched terms, and excerpts so the agent can avoid broad reads before deciding whether an update is a duplicate.\n- `tools/documents/read_document_items_by_title.ps1 -Titles <titles>` reads only selected candidate sections by title or key after duplicate discovery.\n- Hard rule: documentation reads/writes outside context capsules and strictly technical agent memory must use the candidate-title workflow: derive likely duplicate words, run `tools/documents/check_document_list_item_duplicates.ps1 -Terms <words>`, read only candidates with `tools/documents/read_document_items_by_title.ps1 -Titles <titles>`, then write once through a transactional document script."
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
            "borrowed_before_invented",
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
            "python_quality_gate_contract_runner",
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
            "foreign_legacy_code_communication_profile",
            "foreign_legacy_business_work_model",
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
            "json_node_edit_tools",
            "portable_json_tooling_pack",
            "json_tool_file_stdin_value_inputs",
            "script_input_output_contracts",
            "default_tool_error_hardening",
            "code_primary_truth_and_comment_discipline",
            "helper_enforced_contracts",
            "convenience_driven_programming_contracts",
            "compiled_context_alias_normalization",
            "json_routed_document_item_wrapper",
            "tool_error_registry_and_logger",
            "single_entry_tool_handler",
            "categorized_tool_scripts",
            "managed_pipeline_package_mirror_sync",
            "project_profile_child_overlay_sync",
            "full_update_artifact_parity_contract",
            "managed_pipeline_root_catalog_sync",
            "feature_artifact_contracts",
            "cheap_idempotent_pipeline_update",
            "pipeline_sweep_upgrade_tool",
            "legacy_feature_manifest_update_recovery",
            "canonical_index_content_metadata_document_schema",
            "cross_platform_tool_runtime_resolution",
            "script_runtime_retirement_gate",
            "workspace_root_marker_resolution",
            "better_version_now_future_proof_engineering",
            "predictable_load_lightweight_architecture",
            "template_parity_for_reusable_pipeline_improvements",
            "project_specific_design_context_gate",
            "web_research_spike_to_named_implementation_plan_gate",
            "directive_hierarchy_context_budget",
            "task_flow_audit_closure",
            "continue_user_clarification_gate",
            "ai_native_code_contract_headers",
            "source_pipeline_maintainer_backlog",
            "grouped_fragmented_task_state_handoff",
            "canonical_data_document_templates"
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
                    "Verify installed task checks and finalizers resolve the child project Git root separately from the installed SocratexAI package root.",
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
                    "FLOWS.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "project/code/DDD-ADIV.json",
                    "tools/codebase/check_code_context_gate.ps1",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "tools/knowledge/knowledge_index.py",
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
            "borrowed_before_invented": {
                "summary": "Borrowed Before Invented capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
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
                "known_failure_if_missing": "If 'borrowed_before_invented' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
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
                    "tools/documents/build_document_cache.py",
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
                    "build_document_cache.py",
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
                        "build_document_cache.py",
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
                    "Prefer build_document_cache.py for Python-first document cache refresh and keep the legacy wrapper only until the final no-PowerShell deletion pass.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "python3 -B tools/quality/check_python_syntax.py tools/documents/build_document_cache.py tools/documents/document_read_cache_engine.py",
                    "python3 -B tools/documents/build_document_cache.py --output-dir /tmp/socratex-doc-cache-smoke",
                    "python3 tools/repo/check_pipeline_feature_contracts.py --paths tools/documents/build_document_cache.py SCRIPTS.json QUALITY-GATE.json pipeline_featurelist.json",
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
                    "tools/codebase/update_code_line_index.py",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "check_code_context_gate.ps1",
                    "update_code_line_index.ps1",
                    "update_code_line_index.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "check_code_context_gate.ps1",
                        "update_code_line_index.ps1",
                        "update_code_line_index.py",
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
                    "Prefer update_code_line_index.py for Python-first line-index refresh and keep the legacy wrapper only until the final no-PowerShell deletion pass.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "python3 -B tools/quality/check_python_syntax.py tools/codebase/update_code_line_index.py",
                    "python3 -B tools/codebase/update_code_line_index.py --check",
                    "python3 tools/repo/check_pipeline_feature_contracts.py --paths tools/codebase/update_code_line_index.py SCRIPTS.json QUALITY-GATE.json pipeline_featurelist.json",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'code_line_index' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "batch_task_checks": {
                "summary": "Batch Task Checks capability is active only when source artifacts, catalogs, update path, canonical quality-gate contract, and compiled-context freshness verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "tools/repo",
                    "tools/quality",
                    "QUALITY-GATE.json",
                    "project/code/GIT.json",
                    "tools/repo/finalize_changed_files_commit_push.py",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "finalize_task_check_commit_push.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "finalize_changed_files_commit_push.py",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "check_sensitive_reference_leaks.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_gate_contract.ps1",
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
                        "check_sensitive_reference_leaks.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_gate_contract.ps1",
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
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_sensitive_reference_leaks.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/quality/run_quality_gate.ps1"
                ],
                "known_failure_if_missing": "If 'batch_task_checks' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "git_batch_finishers": {
                "summary": "Git Batch Finishers capability is active only when commit finalizers run quality by default and their listed source artifacts, catalogs, update path, and verification remain present.",
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
                    "finalize_changed_files_commit_push.py",
                    "run_final_task_checks.ps1",
                    "check_task.ps1",
                    "check_toolchain_health.ps1",
                    "run_quality_gate.ps1",
                    "run_quality_gate.py",
                    "run_quality_gate_contract.ps1",
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
                        "run_quality_gate.py",
                        "run_quality_gate_contract.ps1",
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
                    "python3 -B tools/quality/check_python_syntax.py tools/repo/finalize_changed_files_commit_push.py tools/repo/run_final_task_checks.py",
                    "python3 -B tools/repo/finalize_changed_files_commit_push.py --help",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'git_batch_finishers' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, review workflow, or installed child-project root handling is absent."
            },
            "canonical_done_finalizer": {
                "summary": "Canonical Done Finalizer capability is active only when the preferred finalizer runs audit and quality before commit/push and its listed source artifacts, catalogs, update path, and verification remain present.",
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
                    "run_quality_gate_contract.ps1",
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
                        "run_quality_gate_contract.ps1",
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
                    "Verify installed finalizers resolve the child project Git root separately from the installed SocratexAI package root before normalizing, indexing, auditing task flow, or running quality commands.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'canonical_done_finalizer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, review workflow, or installed child-project root handling is absent."
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
                    "run_quality_gate_contract.ps1",
                    "run_quality_fix.ps1",
                    "check_runtime.py",
                    "audit_docs.ps1",
                    "audit_docs.py",
                    "check_pipeline_feature_contracts.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "finalize_task_check_commit_push.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "run_final_task_checks.ps1",
                        "check_task.ps1",
                        "check_toolchain_health.ps1",
                        "run_quality_gate.ps1",
                        "run_quality_gate_contract.ps1",
                        "run_quality_fix.ps1",
                        "check_runtime.py",
                        "audit_docs.ps1",
                        "audit_docs.py",
                        "check_pipeline_feature_contracts.py"
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
                "summary": "Generic Multi Stack Quality Gate capability is active only when QUALITY-GATE.json uses the canonical list-document shape and its executable contract remains wired into the finalizers and source checks.",
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
                    "run_quality_gate_contract.ps1",
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
                        "run_quality_gate_contract.ps1",
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
            "python_quality_gate_contract_runner": {
                "summary": "Python-first quality gate contract runner executes QUALITY-GATE.json and ports eval plus sensitive-reference checks off the retired command runtime.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "SCRIPTS.json",
                    "QUALITY-GATE.json",
                    "tools/quality/run_quality_gate_contract.py",
                    "tools/quality/run_quality_gate.py",
                    "tools/quality/check_evals.py",
                    "tools/quality/check_python_syntax.py",
                    "tools/repo/run_final_task_checks.py",
                    "tools/repo/finalize_changed_files_commit_push.py",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/check_sensitive_reference_leaks.py"
                ],
                "required_scripts": [
                    "run_quality_gate_contract.py",
                    "run_quality_gate.py",
                    "run_final_task_checks.py",
                    "finalize_changed_files_commit_push.py",
                    "check_evals.py",
                    "check_python_syntax.py",
                    "check_sensitive_reference_leaks.py",
                    "check_pipeline_feature_contracts.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "run_quality_gate_contract.py",
                        "run_quality_gate.py",
                        "run_final_task_checks.py",
                        "finalize_changed_files_commit_push.py",
                        "check_evals.py",
                        "check_python_syntax.py",
                        "check_sensitive_reference_leaks.py",
                        "check_pipeline_feature_contracts.py"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json",
                    "QUALITY-GATE.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep QUALITY-GATE.json executable by the Python runner without invoking the retired command runtime for Python-first checks.",
                    "Keep source finalizer quality execution pointed at run_quality_gate.py while the broader finalizer itself is being ported.",
                    "Keep run_final_task_checks.py check-only until Python generators replace all refresh steps; use finalize_changed_files_commit_push.py only for Python commit/push orchestration around the current Python-backed checks.",
                    "Keep the eval framework and sensitive-reference smoke checks behaviorally equivalent to their legacy wrappers until the wrappers are deleted.",
                    "Compile and run the Python runner plus focused command subsets before promoting the quality-gate path.",
                    "Sync the managed package so installed child projects receive the Python runner and checker entries."
                ],
                "verification_commands": [
                    "python3 -B tools/quality/check_python_syntax.py tools/quality/run_quality_gate.py tools/quality/run_quality_gate_contract.py tools/quality/check_evals.py tools/quality/check_python_syntax.py tools/repo/check_sensitive_reference_leaks.py tools/repo/run_final_task_checks.py tools/repo/finalize_changed_files_commit_push.py",
                    "python3 -B tools/repo/run_final_task_checks.py --quality --quality-command-names python_compile,eval_framework,sensitive_reference_smoke,transactional_doc_tools",
                    "python3 -B tools/quality/run_quality_gate.py --command-names python_compile,eval_framework,sensitive_reference_smoke",
                    "python3 -B tools/quality/run_quality_gate_contract.py --command-names python_compile,eval_framework,sensitive_reference_smoke",
                    "python3 tools/repo/check_pipeline_feature_contracts.py --paths tools/quality/run_quality_gate.py tools/quality/run_quality_gate_contract.py tools/quality/check_evals.py tools/quality/check_python_syntax.py tools/repo/check_sensitive_reference_leaks.py tools/repo/run_final_task_checks.py tools/repo/finalize_changed_files_commit_push.py tools/repo/run_final_task_checks.ps1 QUALITY-GATE.json SCRIPTS.json pipeline_featurelist.json"
                ],
                "known_failure_if_missing": "QUALITY-GATE.json remains dependent on the retired command runtime even when individual Python checks exist, so Pass 0S cannot close without preserving source and child smoke coverage."
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
                    "tools/documents/build_document_cache.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1",
                    "tools/pipeline/update_pipeline_from_link.py",
                    "tools/pipeline/sync_managed_pipeline_package.py",
                    "tools/pipeline/pipeline_package.py",
                    "tools/repo/sync_pipeline_featurelist.py",
                    "tools/repo/check_pipeline_feature_contracts.py",
                    "tools/documents/audit_docs.py"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_reference_project.ps1",
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
                    "build_document_cache.ps1",
                    "audit_docs.ps1",
                    "sync_managed_pipeline_package.py",
                    "update_pipeline_from_link.py",
                    "sync_pipeline_featurelist.py",
                    "check_pipeline_feature_contracts.py",
                    "audit_docs.py",
                    "pipeline_package.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_reference_project.ps1",
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
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "sync_managed_pipeline_package.py",
                        "update_pipeline_from_link.py",
                        "sync_pipeline_featurelist.py",
                        "check_pipeline_feature_contracts.py",
                        "audit_docs.py",
                        "pipeline_package.py"
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
                    "Ensure fresh existing-project imports build the installed document cache before compiling knowledge, after the final imported PIPELINE-CONFIG.json is written.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts.",
                    "Refresh the installed SocratexAI document cache after managed package sync and before full verification so child audits validate current package files instead of stale cache entries.",
                    "Prefer tools/pipeline/check_ai_compiled_context.py from audit_docs.ps1 when present so installed child packages use the Python-first compiled-context smoke before falling back to the legacy PowerShell checker.",
                    "Do not claim removed or replaced PowerShell pipeline tooling is migrated unless each affected .ps1 path has a Python successor, compatibility wrapper, or explicit legacy/deferred reason, and the successor path has been exercised by source and child-project smoke/update verification."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "python tools/pipeline/update_pipeline_from_link.py --source . --source-mode LocalPath --target-path <child> --full-verify",
                    "python tools/pipeline/pipeline_sweep.py --project source:SocratexAI=. --smoke --execute --stop-on-failure --json"
                ],
                "known_failure_if_missing": "If 'pipeline_update_and_removal_protocols' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, review workflow, import document cache, or imported knowledge freshness is absent."
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                "summary": "Prompt And Output Snapshots capability is active only when Python task and OUTPUT snapshot helpers, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "tools/repo/task_snapshot.py",
                    "tools/repo/end_prompt_snapshot.py",
                    "tools/repo/check_pipeline_feature_contracts.ps1",
                    "tools/documents/audit_docs.ps1"
                ],
                "required_scripts": [
                    "task_snapshot.py",
                    "end_prompt_snapshot.py",
                    "audit_docs.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "task_snapshot.py",
                        "end_prompt_snapshot.py",
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
                    "Keep Python snapshot helpers behaviorally aligned with the finalizer output needs before replacing legacy calls.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "python3 -B tools/quality/check_python_syntax.py tools/repo/task_snapshot.py tools/repo/end_prompt_snapshot.py",
                    "python3 -B tools/repo/task_snapshot.py --max-lines 20",
                    "python3 -B tools/repo/end_prompt_snapshot.py --output-path /tmp/socratex-output-snapshot-smoke --no-sound",
                    "python3 tools/repo/check_pipeline_feature_contracts.py --paths tools/repo/task_snapshot.py tools/repo/end_prompt_snapshot.py SCRIPTS.json QUALITY-GATE.json pipeline_featurelist.json",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "If 'prompt_and_output_snapshots' is listed without these artifacts, finalizers keep depending on legacy snapshot helpers even after the Python commit path exists."
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                "summary": "Pipeline Featurelist Instance Generation capability is considered active only when its listed source artifacts, catalogs, update path, source feature_contract preservation, and verification remain present.",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "Preserve source feature_contracts for source features and preserve instance-owned contracts for extra instance features.",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                "summary": "Pipeline Featurelist Update Guard capability is considered active only when its listed source artifacts, catalogs, update path, generated-cache exemption, and verification remain present.",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                "known_failure_if_missing": "If 'pipeline_featurelist_update_guard' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, generated-cache exemption, or review workflow is absent."
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
                    "tools/pipeline/compile_pipeline_context.py",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/pipeline/rebuild_ai_compiled_context.py",
                    "tools/pipeline/check_ai_compiled_context.ps1",
                    "tools/pipeline/check_ai_compiled_context.py",
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
                    "compile_pipeline_context.py",
                    "rebuild_ai_compiled_context.ps1",
                    "rebuild_ai_compiled_context.py",
                    "check_ai_compiled_context.ps1",
                    "check_ai_compiled_context.py",
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
                        "compile_pipeline_context.py",
                        "rebuild_ai_compiled_context.ps1",
                        "rebuild_ai_compiled_context.py",
                        "check_ai_compiled_context.ps1",
                        "check_ai_compiled_context.py",
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
                    "Prefer rebuild_ai_compiled_context.py for Python-first compiled context refresh and keep the legacy wrapper only until the final no-PowerShell deletion pass.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "python3 -B tools/pipeline/compile_pipeline_context.py --check",
                    "python3 -B tools/pipeline/rebuild_ai_compiled_context.py --check",
                    "python3 -B tools/pipeline/check_ai_compiled_context.py --repo-root .",
                    "python3 -B tools/repo/check_pipeline_feature_contracts.py --paths tools/pipeline/compile_pipeline_context.py tools/pipeline/rebuild_ai_compiled_context.py tools/pipeline/check_ai_compiled_context.py SCRIPTS.json QUALITY-GATE.json pipeline_featurelist.json",
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
                    "tools/documents/audit_docs.ps1",
                    "JSON-FORMAT-CONTRACT.json",
                    "tools/documents/document_structure_normalizer_engine.py",
                    "tools/documents/document_schema_migration_engine.py",
                    "tools/documents/document_item_edit_engine.py",
                    "tools/documents/document_list_item_edit_engine.py"
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
                    "normalize_document_structure.ps1",
                    "migrate_document_schema.ps1",
                    "document_item_edit_engine.py",
                    "document_list_item_edit_engine.py"
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
                        "normalize_document_structure.ps1",
                        "migrate_document_schema.ps1",
                        "document_item_edit_engine.py",
                        "document_list_item_edit_engine.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "JSON-FORMAT-CONTRACT.json"
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
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/normalize_document_structure.ps1 -Check",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/migrate_document_schema.ps1 -Check"
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
                "summary": "Json Document Normalizer capability is active only when canonical list-document tooling, canonical installed DOCS templates, catalogs, update path, and verification remain present.",
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
                    "tools/documents/audit_docs.ps1",
                    "JSON-FORMAT-CONTRACT.json",
                    "tools/documents/document_structure_normalizer_engine.py",
                    "tools/documents/document_schema_migration_engine.py",
                    "tools/documents/document_item_edit_engine.py",
                    "tools/documents/document_list_item_edit_engine.py"
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
                    "normalize_document_structure.ps1",
                    "migrate_document_schema.ps1",
                    "document_item_edit_engine.py",
                    "document_list_item_edit_engine.py"
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
                        "normalize_document_structure.ps1",
                        "migrate_document_schema.ps1",
                        "document_item_edit_engine.py",
                        "document_list_item_edit_engine.py"
                    ]
                },
                "required_docs": [
                    "DOCS.json",
                    "templates/DOCS.json",
                    "templates/code/DOCS.json",
                    "JSON-FORMAT-CONTRACT.json"
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
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/normalize_document_structure.ps1 -Check",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/migrate_document_schema.ps1 -Check"
                ],
                "known_failure_if_missing": "If 'json_document_normalizer' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_list_document_tools": {
                "summary": "Json List Document Tools capability is considered active only when its listed source artifacts, catalogs, update path, and verification remain present.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "DOCS.json",
                    "tools/documents",
                    "tools/json",
                    "tools/json/README.md",
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
                    "smoke_json_tools.py",
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
                    "json_node_edit.ps1",
                    "normalize_json_files.ps1",
                    "normalize_json_files.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "build_document_cache.ps1",
                        "audit_docs.ps1",
                        "json_list_doc.py",
                        "smoke_json_tools.py",
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
                        "json_node_edit.ps1",
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
                    "Use json_node_edit.ps1 for full-node-path JSON operations, nested list edits, and structural/order-only JSON changes.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "python3 tools/json/smoke_json_tools.py"
                ],
                "known_failure_if_missing": "If 'json_list_document_tools' is listed without these artifacts, source/child comparison may pass by feature id while the behavior, update path, or review workflow is absent."
            },
            "json_node_edit_tools": {
                "summary": "Pipeline JSON manipulation scripts are active only when full-node-path tools, nested-list support, wrapper help, SCRIPTS metadata, and agent directives all require script-first structural/order-only JSON edits.",
                "required_paths": [
                    "tools/json/json_node_edit.ps1",
                    "tools/json/json_list_doc.py",
                    "SCRIPTS.json",
                    "core/AGENT-CONTRACT.json",
                    "FLOWS.json",
                    "WORKFLOW.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "json_node_edit.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "json_line_insert.ps1",
                    "json_line_set.ps1",
                    "json_line_move.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "json_node_edit.ps1",
                        "json_list_doc.py",
                        "json_read.ps1",
                        "json_line_insert.ps1",
                        "json_line_set.ps1",
                        "json_line_move.ps1"
                    ]
                },
                "required_docs": [],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Expose full node-path JSON operations through SCRIPTS.json.",
                    "Keep SCRIPTS.json descriptions, required/optional parameters, help availability, value-source rules, and failure contracts aligned with wrapper behavior.",
                    "Keep structural/order-only JSON edits script-first in AGENT-CONTRACT and FLOWS.",
                    "Keep WORKFLOW.json aligned so source-pipeline agents know to script structure/order first and patch content second.",
                    "Verify nested list edits, dot-containing keys through slash paths, and legacy -FieldPath wrappers."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "python3 tools/json/smoke_json_tools.py"
                ],
                "known_failure_if_missing": "Agents fall back to manual JSON ordering patches or cannot target nested lists and keys containing dots safely.",
                "usage_directives": [
                    "For JSON edits that only change structure or order, such as move, reorder, delete, insert before/after, or migrate, use json_node_edit.ps1 or the narrow JSON wrappers instead of manual patching.",
                    "When one task needs both structural/order changes and content edits, run the scripted structural operation first, then set or patch the content.",
                    "Use json_node_edit.ps1 when the full JSON node path is known; use slash-separated node paths when a segment contains dots.",
                    "Keep SCRIPTS.json input/output/help metadata current for JSON wrapper parameters, value-source rules, nested selectors, and failure behavior."
                ]
            },
            "portable_json_tooling_pack": {
                "summary": "Generic JSON manipulation helpers live in tools/json as a portable pack that can be copied between projects without the higher-level document routing/cache workflow.",
                "required_paths": [
                    "tools/json",
                    "tools/json/README.md",
                    "tools/json/json_list_doc.py",
                    "tools/json/json_node_edit.ps1",
                    "tools/json/json_read.ps1",
                    "tools/json/json_item_insert.ps1",
                    "tools/json/json_item_set.ps1",
                    "tools/json/json_item_move.ps1",
                    "tools/json/json_item_delete.ps1",
                    "tools/json/json_line_insert.ps1",
                    "tools/json/json_line_set.ps1",
                    "tools/json/json_line_move.ps1",
                    "tools/json/json_refresh_index.ps1",
                    "tools/json/json_migrate_content.ps1",
                    "tools/json/audit_json_docs.py",
                    "tools/json/smoke_json_tools.py",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "json_list_doc.py",
                    "json_node_edit.ps1",
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
                    "audit_json_docs.py",
                    "smoke_json_tools.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "json_list_doc.py",
                        "json_node_edit.ps1",
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
                        "audit_json_docs.py",
                        "smoke_json_tools.py"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep generic JSON operations under tools/json so they can be copied as a small portable pack.",
                    "Keep tools/documents focused on DOCS routing, document cache, markdown/list-document helpers, and project document audits.",
                    "Use tools/json for structure/order-only JSON edits before any manual content patching when both are needed.",
                    "Keep SCRIPTS.json paths and categories pointing to tools/json for JSON helpers.",
                    "Run the portable JSON smoke after moving or editing JSON helpers, then run document audit and feature-contract checks.",
                    "Sync child projects so embedded SocratexAI packages receive the same tools/json layout.",
                    "Keep smoke_json_tools.py resolving json_list_doc.py relative to its own folder so the pack works after copying into either tools/json or Tools/json layouts."
                ],
                "verification_commands": [
                    "python3 tools/json/smoke_json_tools.py",
                    "python3 tools/json/audit_json_docs.py --repo-root .",
                    "python3 tools/repo/check_pipeline_feature_contracts.py"
                ],
                "known_failure_if_missing": "JSON helpers remain mixed into document workflow folders, making them harder to copy between projects and easier to confuse with project-specific document/cache tooling."
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
                "summary": "Script Input Output Contracts capability is active only when every script catalog entry carries description, input, and output contracts and audit_docs enforces that full baseline.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "SCRIPTS.json",
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
                    "core/AGENT-CONTRACT.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Ensure every SCRIPTS.json entry includes description/input/output fields with input.required, input.optional, input.rule, output.success, and output.failure.",
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
                    "tools/pipeline/sync_managed_pipeline_package.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.py",
                    "tools/pipeline/pipeline_package.py",
                    "tools/repo/sync_pipeline_featurelist.py",
                    "tools/repo/check_pipeline_feature_contracts.py",
                    "tools/documents/audit_docs.py"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "reinitialize_pipeline.ps1",
                    "remove_pipeline.ps1",
                    "upgrade_from_reference_project.ps1",
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
                    "audit_docs.ps1",
                    "sync_managed_pipeline_package.py",
                    "sync_pipeline_featurelist.py",
                    "check_pipeline_feature_contracts.py",
                    "audit_docs.py",
                    "pipeline_package.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "reinitialize_pipeline.ps1",
                        "remove_pipeline.ps1",
                        "upgrade_from_reference_project.ps1",
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
                        "audit_docs.ps1",
                        "sync_managed_pipeline_package.py",
                        "sync_pipeline_featurelist.py",
                        "check_pipeline_feature_contracts.py",
                        "audit_docs.py",
                        "pipeline_package.py"
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
            "project_profile_child_overlay_sync": {
                "summary": "Project profile child overlay sync keeps reusable profile-owned project catalogs in SocratexAI while child projects receive only additions, generated state, protected config, and explicit local overrides.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "profiles/SocratexGamedev",
                    "SCRIPTS.json",
                    "tools/pipeline/sync_managed_pipeline_package.ps1",
                    "tools/pipeline/update_pipeline_from_link.ps1",
                    "tools/pipeline/import_existing_project.ps1",
                    "tools/pipeline/Initialize-SocratexPipeline.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "required_scripts": [
                    "sync_managed_pipeline_package.ps1",
                    "update_pipeline_from_link.ps1",
                    "import_existing_project.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "sync_managed_pipeline_package.ps1",
                        "update_pipeline_from_link.ps1",
                        "import_existing_project.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "profiles/SocratexGamedev/PROFILE.json",
                    "profiles/SocratexGamedev/COMMANDS.json",
                    "profiles/SocratexGamedev/FLOWS.json",
                    "profiles/SocratexGamedev/SCRIPTS.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep reusable game-project catalogs in profiles/SocratexGamedev instead of copying them independently into each child project.",
                    "Run sync_managed_pipeline_package.ps1 with -ProjectRoot, -Profile, -ApplyProjectProfile, and -PruneUnmanaged during project update/import.",
                    "Preserve locally changed managed profile files as reported overrides unless -ForceManaged is explicitly used.",
                    "Keep PIPELINE-PACKAGE.json reporting project_profile_files, local_overrides, preserved_unmanaged, and removed_unmanaged after every sync.",
                    "Keep profiles included in managed package sync so profile definitions are present on other machines and child projects after update."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/sync_managed_pipeline_package.ps1 -SourceRoot . -InstallRoot <child>/SocratexAI -ProjectRoot <child> -Profile SocratexGamedev -ApplyProjectProfile -PruneUnmanaged -DryRun"
                ],
                "known_failure_if_missing": "Child projects keep forked copies of root command, flow, script, and workflow catalogs, so source updates do not cleanly propagate across projects or machines and local duplicates silently drift."
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "upgrade_from_reference_project.ps1",
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
                        "upgrade_from_reference_project.ps1",
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
                    "When validating an installed child SocratexAI package, skip source_only repo-path/doc existence checks because those artifacts remain source-maintainer owned.",
                    "Do not promote child features upstream unless their contracts list the artifacts to port."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Source and child pipelines can report matching feature IDs while the behavior is absent, stale, only partially copied, or blocked by source_only maintainer artifacts that are intentionally not installed into child packages."
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
                    "tools/json/json_list_doc.py",
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
            "pipeline_sweep_upgrade_tool": {
                "summary": "Automate repeatable SocratexPipeline source-to-child update and smoke sweeps across explicit project lists, while leaving drift interpretation and repairs to the operator/agent.",
                "required_paths": [
                    "tools/pipeline/pipeline_sweep.py",
                    "tools/pipeline/pipeline_sweep.ps1",
                    "templates/pipeline-sweep.projects.json",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json",
                    "tools/pipeline/check_ai_compiled_context.py",
                    "tools/knowledge/knowledge_tier_check.py",
                    "tools/documents/audit_docs.py",
                    "tools/repo/check_pipeline_feature_contracts.py",
                    "tools/pipeline/update_pipeline_from_link.py"
                ],
                "required_scripts": [
                    "pipeline_sweep.py",
                    "pipeline_sweep.ps1",
                    "update_pipeline_from_link.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "audit_docs.ps1",
                    "knowledge_tier_check.ps1",
                    "compile_pipeline_context.ps1",
                    "update_pipeline_from_link.py",
                    "check_pipeline_feature_contracts.py",
                    "audit_docs.py",
                    "knowledge_tier_check.py",
                    "check_ai_compiled_context.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "pipeline_sweep.py",
                        "pipeline_sweep.ps1",
                        "update_pipeline_from_link.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "audit_docs.ps1",
                        "knowledge_tier_check.ps1",
                        "compile_pipeline_context.ps1",
                        "update_pipeline_from_link.py",
                        "check_pipeline_feature_contracts.py",
                        "audit_docs.py",
                        "knowledge_tier_check.py",
                        "check_ai_compiled_context.py"
                    ]
                },
                "required_docs": [
                    "templates/pipeline-sweep.projects.json",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the sweep runner Python-first and OS-agnostic; PowerShell remains a catalog wrapper, not the core implementation.",
                    "Require explicit project config or NAME=PATH arguments so the tool does not depend on agent memory or private hardcoded workspaces.",
                    "Keep dry-run as the default and require --execute/-Execute before update, smoke, or finalizer commands run.",
                    "Model projects through status, update, smoke, optional finalizer, and summary phases instead of one-off manual command sequences.",
                    "Run or print standard smoke coverage for docs audit, feature contracts, compiled context, tier checks, and git cleanliness where applicable.",
                    "Keep destructive cleanup, dependency installation, and project-specific finalizers out of the default path unless they are explicitly configured and operator-approved.",
                    "Use the summary to decide which drift needs AI/operator interpretation instead of treating the script as an autonomous repair agent.",
                    "Sync the managed package so child projects receive the runner, wrapper, config template, catalog entries, and feature contract."
                ],
                "verification_commands": [
                    "python3 -m py_compile tools/pipeline/pipeline_sweep.py",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/pipeline_sweep.ps1 -Help",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Agents must manually remember every project, update command, smoke command, tier check, and drift summary, so future source-pipeline upgrades become inconsistent as project count grows."
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
                "summary": "Canonical JSON list documents use exactly root index, content, and metadata by default, with every non-canonical source JSON either generated/runtime-owned or explicitly listed in JSON-FORMAT-CONTRACT.json.",
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
                    "tools/json/json_list_doc.py",
                    "tools/json/json_read.ps1",
                    "tools/text/normalize_json_files.ps1",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "JSON-FORMAT-CONTRACT.json",
                    "tools/documents/document_structure_normalizer_engine.py",
                    "tools/documents/document_schema_migration_engine.py",
                    "tools/documents/document_item_edit_engine.py",
                    "tools/documents/document_list_item_edit_engine.py",
                    "context-docs/ENGINEERING.json",
                    "core/ACTIVATION-CHECK.json",
                    "core/AGENT-CONTRACT.json",
                    "core/COMMANDS.json",
                    "core/CONTEXT-COMPACTION.json",
                    "core/CONTEXT-TIERS.json",
                    "core/INSTRUCTION-CAPTURE.json",
                    "core/MEMORY-MODEL.json",
                    "core/PROJECT-PROFILE.json",
                    "core/PROMOTION-RULES.json",
                    "core/REMOVAL-PROTOCOL.json",
                    "core/ROI-BIAS.json",
                    "core/SCRIPT-FALLBACK.json",
                    "core/TASK-WORK.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "profiles/SocratexForeignLegacy/WORKFLOW.json",
                    "project/code/BRANCH-MODE.json",
                    "project/code/COMMANDS.json",
                    "project/code/DDD-ADIV.json",
                    "project/code/DIAGNOSTICS.json",
                    "project/code/FROZEN-LAYERS.json",
                    "project/code/GIT.json",
                    "project/code/INSTRUCTION-CAPTURE.json",
                    "project/code/PACK.json",
                    "project/code/REGISTRIES.json",
                    "project/code/WORKFLOW.json",
                    "project/creative/PACK.json",
                    "project/gamedev/PACK.json",
                    "project/generic/PACK.json",
                    "project/personal/PACK.json",
                    "templates/PIPELINE-CONFIG.json",
                    "templates/_INSTRUCTION-QUEUE.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "templates/context-docs-FROZEN_LAYERS.json",
                    "templates/context-docs-TECHNICAL.json",
                    "templates/docs-tech/KNOWLEDGE-VIEWS.json",
                    "profiles/SocratexGamedev/SCRIPTS.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "sync_pipeline_featurelist.ps1",
                    "learn_pipeline_features.ps1",
                    "report_pipeline_learning.ps1",
                    "audit_docs.ps1",
                    "json_list_doc.py",
                    "json_read.ps1",
                    "normalize_json_files.ps1",
                    "normalize_document_structure.ps1",
                    "migrate_document_schema.ps1",
                    "document_item_edit_engine.py",
                    "document_list_item_edit_engine.py"
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
                        "normalize_json_files.ps1",
                        "normalize_document_structure.ps1",
                        "migrate_document_schema.ps1",
                        "document_item_edit_engine.py",
                        "document_list_item_edit_engine.py"
                    ]
                },
                "required_docs": [
                    "pipeline_featurelist.json",
                    "DOCS.json",
                    "PUBLIC-BOOTSTRAP.md",
                    "core/FILE-FORMATS.json",
                    "core/UPDATE-PROTOCOL.json",
                    "SCRIPTS.json",
                    "JSON-FORMAT-CONTRACT.json",
                    "context-docs/ENGINEERING.json",
                    "project/code/WORKFLOW.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "profiles/SocratexGamedev/SCRIPTS.json"
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
                    "Run the feature contract checker and audit after schema changes.",
                    "Keep JSON-FORMAT-CONTRACT.json current whenever a non-canonical source JSON remains or a generated/runtime exclusion is added.",
                    "Use canonical index/content/metadata for source-owned human/AI-readable JSON documents unless a direct-schema exception is explicitly justified.",
                    "Keep document normalizer and migration tools pointed at index/content/metadata, not legacy index/items/meta."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/sync_pipeline_featurelist.ps1 -TargetPath <project> -SourceFeatureListPath pipeline_featurelist.json -DryRun",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/normalize_document_structure.ps1 -Check",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/migrate_document_schema.ps1 -Check"
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
                    "tools/json/json_item_insert.ps1",
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
                    "tools/json/json_item_insert.ps1",
                    "tools/json/json_item_set.ps1",
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
            "helper_enforced_contracts": {
                "summary": "Shared helpers, APIs, registries, schemas, or small service boundaries should act as contract aids when they support correct architecture, make correct usage easiest, and make off-contract usage visible.",
                "required_paths": [
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "AI-compiled",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "rebuild_ai_compiled_context.ps1",
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "rebuild_ai_compiled_context.ps1",
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json"
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
                "known_failure_if_missing": "Projects may duplicate boundary behavior across callers instead of using a helper or API that supports the architecture and makes the intended contract easy to use and easy to audit."
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
                    "tools/text/normalize_json_files.ps1",
                    "tools/pipeline/python_runtime.py",
                    "tools/quality/check_runtime.py"
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
                    "normalize_json_files.ps1",
                    "python_runtime.py",
                    "check_runtime.py"
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
                        "normalize_json_files.ps1",
                        "python_runtime.py",
                        "check_runtime.py"
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
                    "Run representative document, knowledge, bootstrap, and feature-contract checks on a Linux shell before promoting to child projects.",
                    "For PowerShell-to-Python migration claims, verify behavior by executing the replacement Python commands and update/smoke flows; reference-count reduction alone is not sufficient evidence."
                ],
                "verification_commands": [
                    "powershell -NoLogo -NoProfile -File tools/pipeline/pipeline_bootstrap_index.ps1 -Check",
                    "powershell -NoLogo -NoProfile -File tools/documents/build_document_cache.ps1",
                    "powershell -NoLogo -NoProfile -File tools/knowledge/knowledge_check.ps1",
                    "powershell -NoLogo -NoProfile -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "python3 tools/quality/check_runtime.py --root-key runtime_status --strict"
                ],
                "known_failure_if_missing": "Linux and Steam Deck installs fall back to empty HUD-like pipeline state or failed bootstrap/document/knowledge tools because wrappers try to execute a Windows-only bundled Python path."
            },
            "workspace_root_marker_resolution": {
                "summary": "Workspace-level tools resolve local multi-project workspaces from workspace.json stored next to SocratexAI, keeping project scripts repo-relative and avoiding hardcoded work/projects roots.",
                "required_paths": [
                    "core/WORKSPACE.json",
                    "README.md",
                    "PUBLIC-BOOTSTRAP.md",
                    "DOCS.json",
                    "SCRIPTS.json",
                    "templates/SOCRATEX.md",
                    "templates/workspace.json",
                    "tools/pipeline/resolve_workspace_root.ps1",
                    "core/UPDATE-PROTOCOL.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "resolve_workspace_root.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "resolve_workspace_root.ps1"
                    ]
                },
                "required_docs": [
                    "core/WORKSPACE.json",
                    "README.md",
                    "PUBLIC-BOOTSTRAP.md",
                    "DOCS.json",
                    "SCRIPTS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Store workspace.json in the workspace root next to SocratexAI/.",
                    "Keep workspace.json paths relative to its own directory unless the value is an external URI.",
                    "Use resolve_workspace_root.ps1 for workspace-level imports, archives, exports, and local sibling source checkout discovery.",
                    "Keep project-local scripts resolving repo roots relative to script location.",
                    "Do not hardcode /home/<user>/work, /home/<user>/projects, drive-imports, or repos as canonical source paths."
                ],
                "verification_commands": [
                    "powershell -NoLogo -NoProfile -File tools/pipeline/resolve_workspace_root.ps1 -Json",
                    "powershell -NoLogo -NoProfile -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoLogo -NoProfile -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Agents and workspace tools may preserve hardcoded local roots, making work/projects renames and multi-machine workspace layouts brittle."
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
            },
            "foreign_legacy_code_communication_profile": {
                "summary": "Adds the `foreign_legacy_code` communication profile for unfamiliar or legacy business codebases where the agent must be epistemic, surface domain unknowns, produce business-storytelling handoff text, and write manual test scenarios for paths it cannot safely auto-test.",
                "required_paths": [
                    "core/communication-profiles/foreign_legacy_code.txt",
                    "core/AGENT-CONTRACT.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the profile body in `core/communication-profiles/foreign_legacy_code.txt` instead of embedding it in setup scripts.",
                    "Keep `core/AGENT-CONTRACT.json` communication profile list aligned with the profile filename.",
                    "Preserve business-storytelling handoff, explicit unknown-unknown surfacing, and manual-test-scenario requirements as the profile's differentiators.",
                    "Rebuild compiled instructions so installed agents can discover the new profile."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/check_ai_compiled_context.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Legacy-business projects may fall back to the generic epistemic profile, losing paste-ready business handoff text, domain-unknown guardrails, and explicit manual test scenarios."
            },
            "foreign_legacy_business_work_model": {
                "summary": "Adds the `SocratexForeignLegacy` workflow profile for foreign or legacy business codebases with incomplete domain knowledge, weak tests, inconsistent conventions, and user-owned review/testing/PR/ticket lifecycle.",
                "required_paths": [
                    "profiles/SocratexForeignLegacy/WORKFLOW.json",
                    "core/communication-profiles/foreign_legacy_code.txt",
                    "core/AGENT-CONTRACT.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "profiles/SocratexForeignLegacy/WORKFLOW.json",
                    "core/communication-profiles/foreign_legacy_code.txt",
                    "core/AGENT-CONTRACT.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the workflow language- and company-agnostic so it can apply to inherited business systems beyond one client or stack.",
                    "Preserve the 8-phase lifecycle: Read, Decide, Plan, Implement, Report, Test, Joint Verification, Handoff.",
                    "Keep PR, ticket, and deployment lifecycle user-owned while the agent prepares paste-ready handoff text.",
                    "Keep this profile separate from the default code pack and SocratexGamedev profile.",
                    "Rebuild compiled instructions and run feature-contract checks after workflow/profile changes."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/check_ai_compiled_context.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1"
                ],
                "known_failure_if_missing": "Foreign or legacy business work may be routed through the default code or gamedev flow, causing premature coding, hidden domain assumptions, missing manual test scenarios, or agent-owned shared-system lifecycle actions."
            },
            "project_specific_design_context_gate": {
                "summary": "Project-Specific Design Context Gate capability is considered active only when the per-project design context loader, its config field, the implementation flow that requires it, and its verification surface remain present. Tightens the implementation flow so that beyond the workspace-shared engineering rules, project-specific zone splits, namespace rules, and lifecycle constraints from each project's PIPELINE-CONFIG.json are deterministically loaded into context before code edits.",
                "required_paths": [
                    "FLOWS.json",
                    "context-docs/ENGINEERING.json",
                    "pipeline_featurelist.json",
                    "tools/codebase/check_project_design_context_gate.ps1",
                    "tools/documents/audit_docs.ps1",
                    "tools/knowledge/knowledge_code_context.ps1",
                    "tools/knowledge/project_design_context.ps1",
                    "tools/repo/check_pipeline_feature_contracts.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1",
                    "check_project_design_context_gate.ps1",
                    "knowledge_code_context.ps1",
                    "project_design_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1",
                        "check_project_design_context_gate.ps1",
                        "knowledge_code_context.ps1",
                        "project_design_context.ps1"
                    ]
                },
                "required_docs": [
                    "FLOWS.json",
                    "context-docs/ENGINEERING.json"
                ],
                "required_config_fields": {
                    "<project>/.aiassistant/socratex/PIPELINE-CONFIG.json": [
                        "code_design_required_reads"
                    ]
                },
                "implementation_flow_steps": [
                    "load WORKFLOW.json",
                    "run knowledge_code_context.ps1 — REQUIRED: brings 11 substantive code-design rules (borrowed-before-invented, production-grade-default, ddd-adiv-when-possible, readability-first, method-and-variable-extraction, codebase-as-contract, legacy-aware-change-split, minimal-comments, business-naming, match-surrounding-patterns, explicit-diagnosable-flow) plus workflow rules (pair-programming-stance, verification-without-tests, etc.) into context",
                    "run project_design_context.ps1 -ProjectRoot <project> when PIPELINE-CONFIG declares code_design_required_reads — writes ignored/project_design_context_gate.json",
                    "inspect SCRIPTS.json index before manual work",
                    "edit scoped files",
                    "run check_task.ps1 -ProjectRoot <project> at the final verification boundary — verifies BOTH ignored/code_context_gate.json (workspace, via check_code_context_gate.ps1) and <project>/ignored/project_design_context_gate.json (per-project, via check_project_design_context_gate.ps1) are fresh for current HEAD when changed-code is detected"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Port the reusable source artifacts, not only the feature id.",
                    "Ensure project_design_context.ps1 ships into installed projects (or stays accessible via shared-sibling SocratexAI clone).",
                    "Verify each child project declares code_design_required_reads in its PIPELINE-CONFIG.json or accepts the no-op fallback.",
                    "List every required script, document, template, catalog entry, and generated-context input in this contract.",
                    "Run the feature contract checker before promoting or publishing the update.",
                    "Run managed package sync or reinitialization so child projects receive source-owned artifacts."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/project_design_context.ps1 -ProjectRoot <project> -Quiet",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/codebase/check_project_design_context_gate.ps1 -ProjectRoot <project>"
                ],
                "known_failure_if_missing": "If 'project_specific_design_context_gate' is listed without these artifacts, source/child comparison may pass by feature id while implementation flow loses its second gate, and per-project zone/namespace rules become opt-in instead of enforced. Symptoms: agents drag /app patterns into /application files (or vice-versa), miss namespace-zone constraints in projects with dual zones, or apply modern syntax to PHP 5.6 projects."
            },
            "predictable_load_lightweight_architecture": {
                "summary": "Programming work checks predictable load before choosing heavyweight/per-object framework paths, with profile-gated interpretation for business, legacy, and realtime/gamedev projects.",
                "required_paths": [
                    "core/AGENT-CONTRACT.json",
                    "core/PROJECT-PROFILE.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "core/PROJECT-PROFILE.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the shared agent contract, code pack, code workflow, source engineering standards, and code starter template aligned.",
                    "Ensure the rule is included in compiled code-task engineering context so implementation, bugfix, log review, and performance diagnosis load it by default.",
                    "For performance reports, prefer architecture migration when a heavyweight broad model is predictably the bottleneck before symptom shaving.",
                    "Run feature-contract and knowledge checks after promotion."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_check.ps1"
                ],
                "known_failure_if_missing": "Agents may keep using ORM/engine/framework convenience as the broad storage/index/batch model for predictable scale, then try to micro-optimize symptoms instead of choosing a lightweight architecture early."
            },
            "template_parity_for_reusable_pipeline_improvements": {
                "summary": "Reusable source-pipeline behavior changes must update the relevant starter templates and feature contracts when future child projects should inherit the behavior.",
                "required_paths": [
                    "WORKFLOW.json",
                    "core/UPDATE-PROTOCOL.json",
                    "templates",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "compile_pipeline_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "compile_pipeline_context.ps1"
                    ]
                },
                "required_docs": [
                    "WORKFLOW.json",
                    "core/UPDATE-PROTOCOL.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "When the user asks to improve the template too, treat template parity as acceptance criteria for the task.",
                    "Update source contracts and starter templates in the same promotion when future children should inherit the behavior.",
                    "List the source docs, templates, scripts, and compiled-context surfaces in the feature contract.",
                    "Run the feature-contract checker before publishing."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "A pipeline source improvement may pass locally but new child projects initialized from templates miss the rule, causing update/source parity to look correct while starter projects remain stale."
            },
            "better_version_now_future_proof_engineering": {
                "summary": "Global programming directive: agents check per task whether a modest profile-fit better-version-now improvement should be chosen across clean code, DDD-ADIV, security, data ownership, contracts, migrations, diagnostics, verification, and predictable performance before accepting a lower-quality shortcut.",
                "required_paths": [
                    "core/AGENT-CONTRACT.json",
                    "core/PROJECT-PROFILE.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "project/code/DDD-ADIV.json",
                    "project/gamedev/PACK.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the directive in shared agent contract, code pack, workflow, engineering standards, gamedev profile, template engineering context, and feature contract in the same promotion.",
                    "Make the rule explicit that borrowed/proven solutions are checked before invented systems.",
                    "Describe the overengineering check so better-version-now does not become speculative ceremony.",
                    "Recompile AI-compiled context and run the feature contract checker.",
                    "Keep profile-gating explicit so legacy surgical fixes do not become broad modernization work."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "If this feature exists only as a performance rule, agents will keep treating future-proofing as FPS-only instead of applying it to clean code, DDD/ADIV, security, data ownership, contracts, migrations, and context boundaries.",
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "project/gamedev/PACK.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "core/PROJECT-PROFILE.json"
                ]
            },
            "task_flow_audit_closure": {
                "summary": "Artifact-based task closure asks agents to prove the selected flow was executed with concrete artifacts, supports machine-readable closure evidence gating, and adds a short changelog-driven adversarial review for complex or high-risk diffs.",
                "required_paths": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/WORKFLOW.json",
                    "FLOWS.json",
                    "profiles/SocratexGamedev/FLOWS.json",
                    "SCRIPTS.json",
                    "tools/repo/task_flow_audit.ps1",
                    "tools/repo/run_final_task_checks.ps1",
                    "tools/repo/finalize_task_check_commit_push.ps1",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "task_flow_audit.ps1",
                    "run_final_task_checks.ps1",
                    "finalize_changed_files_commit_push.ps1",
                    "finalize_task_check_commit_push.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "task_flow_audit.ps1",
                        "run_final_task_checks.ps1",
                        "finalize_changed_files_commit_push.ps1",
                        "finalize_task_check_commit_push.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/WORKFLOW.json",
                    "FLOWS.json",
                    "profiles/SocratexGamedev/FLOWS.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the reusable behavior as one `task_flow_audit` subroutine referenced from flows instead of duplicating checklist steps in every flow.",
                    "Always require closure artifacts for changed-file tasks: loaded route, selected flow execution, concrete closure evidence, changelog truth, tool-failure repair/spec response, and tools-vs-manual discipline.",
                    "Use `tools/repo/task_flow_audit.ps1` as the lightweight closure prompt/checklist and wire it into the final task checks so the artifact audit appears at the task boundary.",
                    "When an installed child-project wrapper calls the managed package copy, pass `-ProjectRoot` so the audit reads the child repository diff and changelog instead of the embedded SocratexAI package.",
                    "For complex or high-risk work, run the adversarial review from the changelog append: read what the changelog claims changed, then test the diff and verification against that claim.",
                    "Keep tiny obvious fixes lightweight: they still answer the core artifacts, but they do not need the complex adversarial section unless the heuristic or agent flags risk.",
                    "Use `-RequireClosureEvidence` or finalizer `-RequireTaskFlowEvidence` when a closure must fail without machine-readable evidence fields.",
                    "Update source and profile FLOWS through subroutines, then sync managed package children so installed projects inherit the rule."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/task_flow_audit.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents can claim completion from prose while skipping the selected flow, omitting changelog truth, hiding manual tool bypass, or missing an obvious adversarial check on broad diffs."
            },
            "continue_user_clarification_gate": {
                "summary": "CONTINUE flow must explicitly check before execution whether the next pass needs user clarification, missing information, product direction, or a meaningful implementation choice, and the agent may stop before or during the task to ask when new ambiguity appears.",
                "required_paths": [
                    "FLOWS.json",
                    "profiles/SocratexGamedev/FLOWS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "FLOWS.json",
                    "profiles/SocratexGamedev/FLOWS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the clarification checkpoint in CONTINUE flow before pass execution, not only in general approval rules.",
                    "Ask the user before executing when the next pass needs missing facts, product direction, or a choice between meaningful implementation variants.",
                    "Allow the agent to stop mid-task and ask when new ambiguity, missing information, product direction, or material risk appears.",
                    "Do not block clear, reversible, source-owned work with unnecessary confirmation; proceed when everything is clear.",
                    "Sync the managed package and child project flow files so source and installed projects share the same CONTINUE behavior."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents may treat CONTINUE as unconditional execution, guess through missing product or implementation information, or keep working after new ambiguity appears instead of pausing for user input.",
                "behavior_contract": [
                    "Before running a CONTINUE-resolved pass or task, the agent checks whether any user information, clarification, product direction, or meaningful implementation choice is needed.",
                    "If clarification is needed before execution, the agent pauses and asks instead of guessing.",
                    "If new ambiguity, missing information, product direction, or material risk appears during execution, the agent may stop mid-task and ask the user.",
                    "If everything is clear and reversible/source-owned, the agent proceeds without unnecessary confirmation."
                ]
            },
            "ai_native_code_contract_headers": {
                "summary": "Reusable code-pipeline standard for short top-of-file JSON-like `AI_CONTRACT` comment headers on major systems, shared boundaries, diagnostics, runtime/performance modules, layer seams, and repeatedly agent-touched files, plus a dry-run helper for planning per-system rollout without mass boilerplate.",
                "required_paths": [
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "SCRIPTS.json",
                    "tools/codebase/ai_native_contract_dry_run.ps1",
                    "pipeline_featurelist.json",
                    "CHANGELOG.json"
                ],
                "required_scripts": [
                    "ai_native_contract_dry_run.ps1",
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "ai_native_contract_dry_run.ps1",
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "SCRIPTS.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the standard generic in ENGINEERING: top-of-file comment-prefixed JSON-like fields for purpose, owns, must_not, design_goals, non_goals, diagnostics taxonomy/fields, layer name/cannot-depend-on, and short ai_notes.",
                    "Keep profile-specific meaning in profile WORKFLOW or project knowledge; gamedev should interpret headers through runtime/FPS budget, activation, diagnostics, layer purity, worldgen, traversal, combat, and gameplay ownership lenses.",
                    "Do not mass-tag source files during the feature promotion. First run the dry-run helper and add explicit per-system rollout passes when headers are worth the maintenance cost.",
                    "Avoid boilerplate on tiny leaf files, generated/vendor files, resource-only files, and obvious DTO/config files.",
                    "Keep the dry-run helper excluding generated, vendored, ignored, logs, managed embedded packages, test-smoke scripts, and local toolchain/runtime folders such as Tools/Python312, Tools/python-installer, and Tools/tmp.",
                    "Treat headers as reading/audit contracts only; still require clear code names, tests/smokes, schemas, runtime diagnostics, and mechanical dependency checks where those are the real enforcement layer.",
                    "Sync the managed package so child projects receive the rule, script, script catalog entry, feature contract, and gamedev contextual action."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/codebase/ai_native_contract_dry_run.ps1 -ProjectRoot .",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents may keep relearning source ownership from broad reads, add inconsistent comments, miss diagnostic taxonomy/layer-purity constraints, include vendored/toolchain/test/managed-package files as rollout candidates, or mass-add stale boilerplate without a per-system rollout plan."
            },
            "source_pipeline_maintainer_backlog": {
                "summary": "Source-only maintainer backlog and current-priority lane for deferred or promoted SocratexPipeline cleanup, directive hierarchy, context-bloat, research-flow, task-flow-audit, adversarial-audit, and audit ideas that should not become always-loaded directives until promoted.",
                "required_paths": [
                    "TODO.md",
                    "DOCS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "TODO.md",
                    "DOCS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_only",
                "promotion_checklist": [
                    "Keep deferred maintainer cleanup ideas in TODO.md unless they are promoted into a reusable source or child-project feature.",
                    "Use TODO.md Current Priority when a maintainer backlog item is intentionally promoted to the next source-pipeline implementation pass before becoming a full reusable feature.",
                    "Use the backlog for directive bloat, hierarchy, and context-cost audits instead of adding more always-loaded rules by default.",
                    "For directive consolidation work, require mechanical trigger conditions, real load tiers, and a hard Tier 1 token budget before AI categorization.",
                    "For code-touch quality work, prefer an always-on research/formalization flow when no research-backed implementation plan exists, so broad philosophy becomes concrete task plans instead of domain-specific tactics bloating core directives.",
                    "Keep future task-flow audit expansions in the backlog unless they add new reusable behavior beyond the promoted `task_flow_audit_closure` feature.",
                    "Update DOCS.json when maintainer-side backlog ownership changes.",
                    "Rebuild compiled context and run feature-contract checks before committing source-pipeline document changes.",
                    "Move promoted maintainer backlog ideas into their own feature contract and remove the active backlog bullet once shipped."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/check_ai_compiled_context.ps1"
                ],
                "known_failure_if_missing": "Maintainer cleanup ideas may be added as new global directives or scattered prompts, increasing context bloat and making rule priority loss more random under context pressure."
            },
            "web_research_spike_to_named_implementation_plan_gate": {
                "summary": "Reusable code-pipeline rule: before source-code writes, agents check whether the active plan already contains research and a named implementation mechanism; obvious small fixes proceed directly, while non-obvious feature/architecture/bug/performance/runtime work runs research first using the loaded knowledge base, project profile, local philosophy, and project-specific rules to decide the relevant risk lenses.",
                "required_paths": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "FLOWS.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "project/code/WORKFLOW.json",
                    "FLOWS.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Apply the rule to the shared code pack/workflow, engineering knowledge capsule, starter template, flows, gamedev profile, and feature contract in the same promotion.",
                    "Implement the gate as a reusable FLOW subroutine and reference it from implementation/broad-refactor flows instead of duplicating the decision steps inline.",
                    "For non-obvious write-code work, require research for established archetypes and known failure modes unless the active plan already names the mechanism; use project rules to decide whether web research, local docs, official docs, or another source is appropriate.",
                    "Before research, ask concise scale/dynamism questions when architecture depends on future load, count, frequency, modules, branches, or data volume.",
                    "Keep FLOWS generic: it should decide whether a task has research plus a named mechanism, whether the change is an obvious small fix, or whether research is required. Domain/profile-specific lenses belong in the knowledge base, project profile, and project-specific rules.",
                    "Record the result as a named implementation mechanism in the plan or execution note before editing structural code.",
                    "Use local patterns and DDD-ADIV as implementation filters after research; if research and local philosophy conflict, ask with the concrete tradeoff.",
                    "Keep obvious tiny fixes lightweight and exempt from the gate.",
                    "Recompile AI-compiled context and run feature-contract checks before committing source-pipeline document changes."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents may either invent invented designs without checking known archetypes, or over-apply local philosophy when gamedev/performance research indicates a different lightweight futureproof mechanism."
            },
            "directive_hierarchy_context_budget": {
                "summary": "Classify pipeline directives and knowledge into Tier 1-5 context layers before setting startup-context budgets, so always-loaded context stays small while routed rules, deep references, history, backlog, and inactive inspiration remain discoverable.",
                "required_paths": [
                    "core/CONTEXT-TIERS.json",
                    "core/AGENT-CONTRACT.json",
                    "AGENTS.md",
                    "DOCS.json",
                    "project/code/WORKFLOW.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "templates/docs-tech/KNOWLEDGE-VIEWS.json",
                    "tools/knowledge/knowledge_index.py",
                    "tools/knowledge/knowledge_select.ps1",
                    "tools/knowledge/knowledge_file_select.ps1",
                    "tools/knowledge/knowledge_query.ps1",
                    "tools/knowledge/knowledge_tier_report.py",
                    "tools/knowledge/knowledge_tier_report.ps1",
                    "tools/knowledge/knowledge_tier_check.ps1",
                    "tools/knowledge/knowledge_file_query.ps1",
                    "tools/pipeline/rebuild_ai_compiled_context.ps1",
                    "tools/knowledge/knowledge_tier_check.py"
                ],
                "required_scripts": [
                    "knowledge_index.py",
                    "knowledge_select.ps1",
                    "knowledge_file_select.ps1",
                    "knowledge_query.ps1",
                    "knowledge_tier_report.py",
                    "knowledge_tier_report.ps1",
                    "knowledge_tier_check.ps1",
                    "knowledge_file_query.ps1",
                    "compile_pipeline_context.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "knowledge_tier_check.py"
                ],
                "required_catalog_entries": {
                    "DOCS.json": [
                        "core/CONTEXT-TIERS.json"
                    ],
                    "SCRIPTS.json": [
                        "knowledge_index.py",
                        "knowledge_select.ps1",
                        "knowledge_file_select.ps1",
                        "knowledge_query.ps1",
                        "knowledge_tier_report.py",
                        "knowledge_tier_report.ps1",
                        "knowledge_tier_check.ps1",
                        "knowledge_file_query.ps1",
                        "knowledge_tier_check.py"
                    ]
                },
                "required_docs": [
                    "core/CONTEXT-TIERS.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "docs-tech/KNOWLEDGE-VIEWS.json",
                    "templates/docs-tech/KNOWLEDGE-VIEWS.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Add the canonical Tier 1-5 context hierarchy to a core source-pipeline contract.",
                    "Keep Tier 1 generic and small: core pipeline, authority, safety, routing, finalization, and decision gates only.",
                    "Route project/profile/domain details through Tier 2 or Tier 3 rather than always-loaded startup text.",
                    "Carry human-in-loop research as a Tier 1 gate and keep detailed lenses lower-tier.",
                    "Add compiled knowledge support for context_tier plus exact/max tier filtering, with defaults for untagged entries.",
                    "Update named knowledge view docs/templates so routed context can bound tiers.",
                    "Keep durable source and starter knowledge entries explicitly tagged with `context_tier` so tier queries do not rely on compiler defaults.",
                    "When one future knowledge entry mixes tiers, split it into focused entries before assigning `context_tier`; do not physically separate files until migration tooling can move entries by metadata.",
                    "Run `knowledge_tier_check.ps1 -IncludeTemplates` after broad source/template retagging so missing tiers fail mechanically and successful scans print an explicit all-tiered status line.",
                    "Recompile AI-compiled context and knowledge artifacts, then run feature-contract checks before committing."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_select.ps1 -MaxContextTier 2 -Format json",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/knowledge/knowledge_tier_check.ps1 -IncludeTemplates"
                ],
                "known_failure_if_missing": "Pipeline guidance keeps accumulating in always-loaded context, agents lose or ignore clear directives under context pressure, and broad knowledge sweeps pretend to fix bloat without a real tier contract or queryable tier metadata."
            },
            "grouped_fragmented_task_state_handoff": {
                "summary": "Large-task workflow splits broad work into user-approved groups and bounded sub-tasks, runs sub-tasks inside the approved group automatically through file handoff, and waits for user continue only before the next group or escalation.",
                "required_paths": [
                    "core/TASK-WORK.json",
                    "FLOWS.json",
                    "project/code/WORKFLOW.json",
                    "profiles/SocratexGamedev/WORKFLOW.json",
                    "tools/tasks/grouped_task_handoff.ps1",
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "grouped_task_handoff.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "rebuild_ai_compiled_context.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "grouped_task_handoff.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "rebuild_ai_compiled_context.ps1"
                    ]
                },
                "required_docs": [
                    "core/TASK-WORK.json",
                    "FLOWS.json",
                    "project/code/WORKFLOW.json",
                    "profiles/SocratexGamedev/WORKFLOW.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the fragmentation trigger explicit: roughly >1500 LOC context, >3 substantial substeps, multiple ownership boundaries, migrations, performance investigations, or multi-system bugs.",
                    "Keep the approval boundary explicit: user approves groups; sub-tasks inside a group can run automatically until escalation.",
                    "Keep handoff file structure durable enough for a fresh session to continue without relying on chat memory.",
                    "Preserve escalation rules for product direction, scope expansion, failing verification, destructive/external actions, and incomplete handoff state.",
                    "Sync the managed package so child projects receive TASK-WORK, FLOWS, code/gamedev workflow guidance, helper script, script catalog entry, and feature contract."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/tasks/grouped_task_handoff.ps1 -TaskId demo -GroupId g1 -SubtaskId s1 -ProjectRoot . -Status done -HandoffSummary \"demo\" -NoPrompt",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents keep doing broad work in one live context window, wait manually between every small subtask, or lose critical state between fragmented sessions because STATE/PLAN handoff artifacts are absent."
            },
            "convenience_driven_programming_contracts": {
                "summary": "Programming guidance treats convenience as the durable path to habit: code/process contracts should be carried by defaults, helpers, tools, checks, templates, or UI/process affordances; legacy zones use helper contracts while non-legacy zones use DDD-ADIV boundaries by default.",
                "required_paths": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json",
                    "pipeline_featurelist.json"
                ],
                "required_scripts": [
                    "knowledge_code_context.ps1",
                    "knowledge_compile.ps1",
                    "check_pipeline_feature_contracts.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "knowledge_code_context.ps1",
                        "knowledge_compile.ps1",
                        "check_pipeline_feature_contracts.ps1"
                    ]
                },
                "required_docs": [
                    "core/AGENT-CONTRACT.json",
                    "project/code/PACK.json",
                    "context-docs/ENGINEERING.json",
                    "templates/code/context-docs/ENGINEERING.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep source contract, code pack, engineering context, starter template, and feature contract in the same promotion.",
                    "State that willpower-only conventions are fragile and should be converted into convenient defaults, helpers, scripts, templates, checks, or affordances where practical.",
                    "State the legacy/non-legacy distinction: legacy uses helper contracts/adapters/seams/checks; non-legacy and actively modernized code use DDD-ADIV boundaries by default.",
                    "Run the feature contract checker and recompile generated context before publishing or syncing to child projects."
                ],
                "verification_commands": [
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_pipeline_feature_contracts.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/pipeline/compile_pipeline_context.ps1 -Check"
                ],
                "known_failure_if_missing": "Agents may prescribe heroic discipline, checklist-only habits, or DDD-purity migrations in legacy zones instead of making the correct behavior convenient and enforceable through the right contract shape."
            },
            "canonical_data_document_templates": {
                "summary": "Starter templates and source changelog use canonical index/content/metadata JSON data-document wrappers, while setup, import, workspace, changelog, task-work, design-context, document-cache, and JSON-audit tooling remain canonical/direct aware.",
                "required_paths": [
                    "CHANGELOG.json",
                    "JSON-FORMAT-CONTRACT.json",
                    "pipeline_featurelist.json",
                    "templates/WORKFLOW.json",
                    "templates/code/BUGS-SOLVED.json",
                    "templates/code/BUGS.json",
                    "templates/code/CHANGELOG.json",
                    "templates/code/DECISIONS.json",
                    "templates/code/PIPELINE-CONFIG.json",
                    "templates/code/STATE.json",
                    "templates/code/TODO.json",
                    "templates/code/_INSTRUCTION-QUEUE.json",
                    "templates/code/_PLAN.json",
                    "templates/code/_PROMPT-QUEUE.json",
                    "templates/code/context-docs/FROZEN_LAYERS.json",
                    "templates/code/context-docs/TECHNICAL.json",
                    "templates/code/current_task.json",
                    "templates/team/experience.json",
                    "templates/team/performance.json",
                    "templates/team/pipeline.json",
                    "templates/team/product.json",
                    "templates/team/technical.json",
                    "templates/workspace.json",
                    "tools/codebase/check_project_design_context_gate.ps1",
                    "tools/documents/audit_docs.ps1",
                    "tools/json/audit_json_docs.py",
                    "tools/documents/document_read_cache_engine.py",
                    "tools/knowledge/project_design_context.ps1",
                    "tools/pipeline/Initialize-SocratexPipeline.ps1",
                    "tools/pipeline/import_existing_project.ps1",
                    "tools/pipeline/init_task_work.ps1",
                    "tools/pipeline/resolve_workspace_root.ps1",
                    "tools/repo/add_changelog_entry.ps1",
                    "tools/repo/task_flow_audit.ps1",
                    "tools/pipeline/sync_managed_pipeline_package.ps1",
                    "tools/repo/check_pipeline_featurelist_update.ps1"
                ],
                "required_scripts": [
                    "audit_docs.ps1",
                    "audit_json_docs.py",
                    "build_document_cache.ps1",
                    "check_project_design_context_gate.ps1",
                    "project_design_context.ps1",
                    "Initialize-SocratexPipeline.ps1",
                    "import_existing_project.ps1",
                    "init_task_work.ps1",
                    "resolve_workspace_root.ps1",
                    "add_changelog_entry.ps1",
                    "task_flow_audit.ps1",
                    "check_pipeline_feature_contracts.ps1",
                    "sync_managed_pipeline_package.ps1",
                    "check_pipeline_featurelist_update.ps1"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "audit_docs.ps1",
                        "audit_json_docs.py",
                        "build_document_cache.ps1",
                        "check_project_design_context_gate.ps1",
                        "project_design_context.ps1",
                        "Initialize-SocratexPipeline.ps1",
                        "import_existing_project.ps1",
                        "init_task_work.ps1",
                        "resolve_workspace_root.ps1",
                        "add_changelog_entry.ps1",
                        "task_flow_audit.ps1",
                        "check_pipeline_feature_contracts.ps1",
                        "sync_managed_pipeline_package.ps1",
                        "check_pipeline_featurelist_update.ps1"
                    ]
                },
                "required_docs": [
                    "JSON-FORMAT-CONTRACT.json",
                    "CHANGELOG.json",
                    "pipeline_featurelist.json",
                    "templates/WORKFLOW.json",
                    "templates/code/PIPELINE-CONFIG.json",
                    "templates/code/CHANGELOG.json",
                    "templates/workspace.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep reusable starter JSON templates in root index/content/metadata shape unless the file is generated, runtime-owned, or an explicit eval/external protocol exception.",
                    "Use socratex-data-document/v1 when canonical wrappers carry operational data instead of prose section objects.",
                    "Keep JSON-FORMAT-CONTRACT.json mirrored into installed SocratexAI packages because source feature contracts validate it inside child pipeline roots.",
                    "Keep setup/import writers canonical-aware so initialized child projects do not downgrade PIPELINE-CONFIG.json back to a direct schema.",
                    "Keep changelog, workspace, task-work, and design-context readers compatible with both canonical and older direct documents during migration.",
                    "Keep source CHANGELOG.json sorted oldest-first and enforce that convention in audit_docs.ps1 and add_changelog_entry.ps1.",
                    "Keep document cache and JSON audit exclusions aligned with JSON-FORMAT-CONTRACT generated/runtime exclusions.",
                    "Run JSON audit, document audit, check_task -Audit, and quality gate before publishing or syncing to child projects.",
                    "Keep generated package manifests such as PIPELINE-PACKAGE.json listed as explicit direct-schema exceptions instead of forcing operational manifests into prose/document shape."
                ],
                "verification_commands": [
                    "python3 tools/json/audit_json_docs.py --repo-root .",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/documents/audit_docs.ps1",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/repo/check_task.ps1 -Audit",
                    "powershell -NoProfile -ExecutionPolicy Bypass -File tools/quality/run_quality_gate.ps1"
                ],
                "known_failure_if_missing": "Child projects receive direct-schema starter memory/config/team files, setup/import rewrites canonical config back to flat JSON, or source/child comparison misses template data-document parity because only prose docs use canonical wrappers."
            },
            "script_runtime_retirement_gate": {
                "summary": "Python-only retirement gate that measures and eventually blocks tracked legacy automation script files plus canonical references to the retired command runtime across source and installed projects.",
                "required_paths": [
                    "pipeline_featurelist.json",
                    "SCRIPTS.json",
                    "tools/quality/script_runtime_gate.py",
                    "tools/pipeline/sync_managed_pipeline_package.py"
                ],
                "required_scripts": [
                    "script_runtime_gate.py",
                    "sync_managed_pipeline_package.py",
                    "check_pipeline_feature_contracts.py"
                ],
                "required_catalog_entries": {
                    "SCRIPTS": [
                        "script_runtime_gate.py",
                        "sync_managed_pipeline_package.py",
                        "check_pipeline_feature_contracts.py"
                    ]
                },
                "required_docs": [
                    "SCRIPTS.json",
                    "pipeline_featurelist.json"
                ],
                "sync_direction": "source_to_child",
                "promotion_checklist": [
                    "Keep the gate Python-only and avoid relying on the retired runtime to verify retirement progress.",
                    "Run the gate in source and child repositories to capture baseline counts before deleting scripts or rewriting catalogs.",
                    "Keep managed package sync from copying ignored bytecode/cache artifacts while propagating the Python gate.",
                    "Do not use skip options for final verification; they are only for local migration slicing."
                ],
                "verification_commands": [
                    "python3 -B tools/quality/script_runtime_gate.py --max-examples 5",
                    "python3 -B -m py_compile tools/quality/script_runtime_gate.py tools/pipeline/sync_managed_pipeline_package.py",
                    "python3 tools/repo/check_pipeline_feature_contracts.py --paths tools/quality/script_runtime_gate.py tools/pipeline/sync_managed_pipeline_package.py SCRIPTS.json pipeline_featurelist.json"
                ],
                "known_failure_if_missing": "Pass 0S can look complete by manual search while child projects still keep tracked legacy automation files, stale command references, or managed package sync reintroduces generated bytecode/cache artifacts."
            }
        }
    },
    "metadata": {
        "schema": "socratex-pipeline-featurelist/v4",
        "pipeline_id": "socratex_pipeline",
        "role": "source",
        "updated_at": "2026-05-23",
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
