# TODO

## Current Priority

1. Sweep upgrade tool.
   Automate the manual cross-project upgrade/smoke sweep used for Riftbound, SocratexPipeline, Socratex-Business-Dogfood, and future child projects. Target a Python-first orchestration tool with OS-agnostic path handling, explicit project list/config input, per-project update/smoke phases, clean status checks, and a concise summary of pass/fail/drift. Value: high on every pipeline update; cost target: one focused evening.

2. Python parity for `audit_docs.ps1` and `check_pipeline_feature_contracts.ps1`.
   Port or wrap the two highest-use pipeline smoke scripts with Python implementations so the core audit/feature-contract checks work without PowerShell as the primary runtime. Keep PowerShell wrappers as compatibility entrypoints, but make the portable implementation OS-agnostic and reusable by CI, child projects, and non-Windows/non-pwsh hosts.

3. Canonical JSON document format expansion.
   Make `index/content/metadata` the preferred format for every repository JSON document that can reasonably be a human/AI-readable source document. Exclude runtime/game data such as game configs, saves, logs, generated runtime artifacts, and other files whose shape is owned by an engine or external protocol. First pass: classify every JSON file as canonical doc, migration candidate, domain/runtime exception, generated artifact, template, eval/result, or external-schema file. Then migrate safe candidates and add audit enforcement so every JSON file has either the canonical shape or an explicit allowed exception.

4. Godot AI-readability sweeps, grouped by ownership area.
   Do not run one huge sweep. Split into focused passes such as application/session flow, runtime state and diagnostics, player/movement/combat, UI/HUD, content/data loading, and tooling/editor scripts. Each pass should identify major `.gd` systems that need clearer ownership, naming, boundaries, diagnostics, or a short `AI_CONTRACT` header.

5. Godot comment-discipline sweeps, grouped after the AI-readability passes.
   For each Godot ownership area, keep comments that explain constraints, invariants, engine quirks, diagnostics, or warnings. Remove or replace narrative comments that merely restate code with clearer names, smaller methods, or explicit contracts.

6. CI / quality gate publishing.
   After the JSON and Godot readability/comment passes, make the local `run_quality_gate` contract easy to publish into the selected CI or release workflow without committing provider-specific CI files before a provider is chosen.

## Side Backlog

- Task-specific research formalization flow: improve the pipeline so broad philosophy is converted into concrete task plans through contextual research instead of by stuffing every possible implementation-specific rule into always-loaded directives. The target code-touch flow is always-on: if a research-backed implementation plan already exists for the touched scope, execute it; if it does not exist, observe the task shape, load compact philosophy and project context, research known approaches/archetypes for this task/profile (for example AAA-style traversal, business bulk data, state management, security, migration strategy), share concise findings and tradeoffs, ask targeted scale/load/architecture questions when future pressure is unclear, formalize the plan with research conclusions, then execute or leave the plan ready for the next pass. This should prevent framing-inheritance failures where the agent inherits the user's symptom framing, such as "FPS drops, optimize like AAA", instead of noticing that the generic philosophy requires researching the structural model first. Preserve generic directives like "borrowed before invented", "better version now", and "avoid future refactor debt" while avoiding core directives that enumerate every domain-specific tactic such as physics indexing, ORM batching, or state-management details. Add an overengineering check: if research-driven better-version work becomes large or speculative, ask before expanding scope. This is a possible future pipeline feature, not an immediate always-loaded rule.
