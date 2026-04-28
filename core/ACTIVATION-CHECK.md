# Activation Check

## Purpose

Use this check after the first user prompt handled under an installed SocratexAI pipeline.

The goal is to verify that the agent has actually loaded and applied the installed rules instead of continuing with bootstrap defaults, stale chat context, or a partial adapter directive.

## When To Run

Run once per newly installed or newly updated project, at the first natural point after setup handoff.

Also run when:

- a session starts from an adapter directive and the agent is unsure whether `SOCRATEX.md` was followed,
- the communication format looks wrong,
- emoji rules are not being applied,
- branch-scoped memory is expected but was not read,
- ROI, profile, or script-fallback rules are missing from behavior.

Do not turn this into a long recurring ceremony. Once the pipeline is clearly active, keep using the normal workflow.

## Required Checks

Confirm that the agent has loaded:

- root `SOCRATEX.md`,
- `SocratexAI/AGENTS.md`,
- `SocratexAI/PIPELINE-CONFIG.yaml` or `SocratexAI/PIPELINE-CONFIG.md`,
- `SocratexAI/core/AGENT-CONTRACT.md`,
- selected project pack files,
- `core/PROJECT-PROFILE.md` when `project_profile` exists,
- `core/ROI-BIAS.md`,
- `core/SCRIPT-FALLBACK.md`,
- `project/code/BRANCH-MODE.md` and branch STATE/PLAN when `workflow.branch_mode` is `branch_scoped`.

Confirm that the current response behavior applies:

- configured pipeline language,
- context-appropriate emoji at section or standalone status starts,
- communication structure from `core/AGENT-CONTRACT.md`,
- known-solutions and profile-fit checks,
- ROI ranking when recommendations are present,
- script-first and script-fallback discipline,
- correct memory promotion rules.

## Report Shape

When the check runs, report it briefly:

```text
## <emoji> Activation
SocratexAI activation check passed: SOCRATEX.md, AGENTS.md, config, core contract, project pack, communication format, emoji rule, and workflow-specific rules are loaded.
```

If something is missing, name it and load it before continuing.

If a file is absent because the selected mode does not require it, say it is not applicable.

## Failure Handling

If activation is incomplete:

1. Stop the current task briefly.
2. Load the missing file or explain why it is unavailable.
3. Re-evaluate the user's prompt under the complete pipeline rules.
4. Continue only after the missing rule source is handled or explicitly marked not applicable.

