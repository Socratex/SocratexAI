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
