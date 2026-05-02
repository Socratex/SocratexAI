# SocratexPipeline Evals

These evals test whether SocratexPipeline improves long-running Codex workspace behavior.

They are intentionally manual first. The goal is to create a clear, inspectable validation package before adding runner infrastructure.

## Scope

This framework evaluates behavior that matters for long-running Codex workspace use:

- priority routing instead of blind task acceptance
- low-friction adoption from simple prompts to structured workflow
- on-demand role loading instead of context flooding
- completion discipline through project finalizers
- document ownership and non-duplication
- compiled instruction usage without treating generated files as source of truth
- engineering standards preload before code work
- compiled knowledge freshness, SQLite use, and file fallback behavior
- controlled knowledge entry lifecycle through scripts
- pipeline update artifact synchronization
- context-tagged knowledge prelude before substantive answers or execution
- task-type routing before broad reads or edits
- unknown-task workflow proposal before speculative execution
- fit across power, moderately technical, and basic users

## How to Run

1. Create or choose a small test workspace.
2. Run each prompt from `evals/prompts/` once without SocratexPipeline context.
3. Score the answer in `evals/results/baseline.yaml`.
4. Install or expose SocratexPipeline context.
5. Run the same prompt again with the relevant pipeline files available.
6. Score the answer in `evals/results/with-pipeline.yaml`.
7. Compare behavior against `evals/expected-behaviors.yaml` and `evals/scoring.md`.

Do not give credit for claims the agent makes without concrete action, routing, verification, or a correct refusal to overreach.

## Eval Freeze

This scenario set is intentionally capped for the current pipeline stage.

Do not add new synthetic scenarios for every new script, generated file, or small workflow refinement.

Only add a new eval when real usage exposes a repeated failure pattern that is not covered by the current scenarios.

## Real Usage Failure Taxonomy

When using SocratexPipeline in real projects, classify failures before expanding the eval suite:

- `missed_context`: the agent missed relevant state, instructions, plans, or knowledge.
- `wrong_routing`: the agent chose the wrong task type or workflow.
- `overread`: the agent loaded too much unrelated context.
- `underread`: the agent acted without enough source or evidence.
- `wrong_document`: the agent wrote durable information to the wrong memory layer.
- `bad_priority_challenge`: the agent failed to challenge, or over-challenged, priority.
- `finish_failure`: the agent skipped, bypassed, or mishandled the finalizer/check boundary.
- `too_much_ceremony`: the pipeline added process cost without improving the outcome.

## Evidence Standard

Scores are not product claims by themselves.

A useful result needs:

- the prompt version
- the model or Codex surface used
- whether the run had pipeline context
- observed behavior
- scored behavior
- concrete failure notes

## Public Use

These evals help maintainers and users check whether SocratexPipeline behaves like a low-friction maturity path from ad hoc Codex usage to structured, auditable, long-running agent workflows.

They do not claim that SocratexPipeline invents new agent primitives. They test whether packaging best practices into defaults, scripts, and project-local conventions makes mature behavior easier to obtain.
