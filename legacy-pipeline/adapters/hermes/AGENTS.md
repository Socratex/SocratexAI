# Hermes Adapter

Read `../../core/AGENT-CONTRACT.json`.

Then read the selected project pack under `../../project/`.

If `../../initializer/FIRST-RUN.md` exists, follow it before normal work.

If `workflow.branch_mode` is `branch_scoped`, detect the current branch and read branch STATE/PLAN before implementation.

If a `tools/` script cannot run, follow `../../core/SCRIPT-FALLBACK.json`; never silently bypass it.

Hermes runs multiple sub-agents. The pipeline contract is per session and single-agent: each sub-agent obeys this same contract, and role/persona lenses (`../../templates/team/*.json`) stay on-demand decision lenses — never stand-in agents or default context loads.

This adapter intentionally contains no duplicated operating rules.
