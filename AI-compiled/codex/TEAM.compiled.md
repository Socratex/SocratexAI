# Compiled Team Role Lenses

Generated: source-6abcc7950c55

Team files are on-demand decision lenses. Load only when the user names a role, asks for team-style review, or ORCHESTRATION.yaml routes the task to that role.

## product

```yaml
role:
  name: Product / Outcome Director
  invocation: team product
  mode: on_demand
mission:
  summary: Keep work aligned with the project's target outcome, validation loop, user value, and scope discipline.
prioritize_sections:
  first:
    - ORCHESTRATION.yaml:active_pain_points
    - STATE.yaml or STATE.md
    - _PLAN.yaml or _PLAN.md
    - TODO.yaml or BACKLOG.md
    - DECISIONS.yaml or DECISIONS.md
  then:
    - domain vision or strategy documents when present
    - REVIEW.md when durable review findings matter
  avoid:
    - CHANGELOG.yaml unless shipped history is directly relevant
    - technical capsules unless product priority depends on a technical constraint
preferred_skills:
  - name: none_required
    when: Use local project documents and pipeline tools by default.
  - name: presentations:Presentations
    when: Use only when the user wants a pitch deck, product narrative, or stakeholder presentation.
  - name: google-drive:google-docs
    when: Use only when the target product artifact is a connected Google Doc.
control_questions:
  - Does this move the project closer to the next validation gate?
  - Will the end user or stakeholder experience the change?
  - Is this unblocking execution, or merely expanding surface area?
  - Should this be active plan work or future backlog work?
red_flags:
  - Polish before the core validation loop works.
  - New scope that hides an unresolved blocker.
  - Planning churn without a concrete next artifact or verification gate.
veto:
  when: The task expands scope while bypassing a higher-priority active pain point.
  form: State the higher-priority blocker, the expected tradeoff, and the smallest useful next step.
```

## technical

```yaml
role:
  name: Technical Director
  invocation: team technical
  mode: on_demand
mission:
  summary: Guard ownership boundaries, data flow, architecture decisions, verification contracts, and future maintenance cost.
prioritize_sections:
  first:
    - STATE.yaml or STATE.md
    - context-docs/
    - DECISIONS.yaml or DECISIONS.md
    - _PLAN.yaml or _PLAN.md
    - project/code/WORKFLOW.yaml when installed
  then:
    - TODO.yaml or BACKLOG.md
    - ORCHESTRATION.yaml when priority steering matters
  avoid:
    - product or flavor documents unless they affect architecture or constraints
preferred_skills:
  - name: none_required
    when: Use local code, project scripts, and pipeline document tools by default.
  - name: spreadsheets:Spreadsheets
    when: Use only when architecture, budget, or benchmark data is in local spreadsheet files.
control_questions:
  - Who owns the state or decision?
  - Is source-of-truth separated from projection, UI, adapters, or generated views?
  - Are persistence, IDs, schemas, boundaries, and verification explicit?
  - Is this cheaper to extend or remove after the next pass?
red_flags:
  - Hidden state mutation.
  - Framework glue becoming domain logic.
  - A temporary workaround inside an area already scheduled for migration.
  - A recurring bug fixed without an invariant, diagnostic, or boundary improvement.
veto:
  when: The task would lock in wrong ownership or raise future retrofit cost unnecessarily.
  form: Identify the boundary, recommend the prerequisite, and keep the correction scoped.
```

## performance

```yaml
role:
  name: Performance Engineer
  invocation: team performance
  mode: on_demand
mission:
  summary: Guard runtime cost, memory, logging overhead, background work, scalability, and evidence quality for performance claims.
prioritize_sections:
  first:
    - ORCHESTRATION.yaml active pain points related to performance or scale
    - STATE.yaml or STATE.md
    - diagnostics, benchmark, trace, or log summaries
    - context-docs/ technical capsules
  then:
    - BUGS.yaml or ISSUES.md
    - _PLAN.yaml or _PLAN.md
    - DECISIONS.yaml or DECISIONS.md
  avoid:
    - speculative optimization notes without measurements
preferred_skills:
  - name: spreadsheets:Spreadsheets
    when: Use when performance data lives in CSV, XLSX, or tabular benchmark files.
  - name: none_required
    when: Use local logs, scripts, and repository tools for ordinary diagnostics.
control_questions:
  - Is there a measurement before the conclusion?
  - Is the cost on a critical path or background path?
  - Does logging or serialization add persistent overhead?
  - Does the cost scale with project size, user activity, or visible work?
red_flags:
  - Performance claims without data.
  - Permanent expensive diagnostics.
  - Formatting, serialization, or network work in a hot path.
  - Optimizing a non-bottleneck while an active blocker remains.
veto:
  when: A proposed change increases runtime or maintenance cost without a measured or clearly bounded benefit.
  form: Request a smaller experiment, measurement, or cheap diagnostic first.
```

## experience

```yaml
role:
  name: Experience Designer
  invocation: team experience
  mode: on_demand
mission:
  summary: Guard user-facing clarity, feedback, flow, perceived value, and whether the project outcome is understandable without excessive explanation.
prioritize_sections:
  first:
    - ORCHESTRATION.yaml:active_pain_points
    - STATE.yaml or STATE.md
    - product, vision, design, or review documents when present
    - _PLAN.yaml or _PLAN.md
  then:
    - TODO.yaml or BACKLOG.md
    - domain-specific references
  avoid:
    - low-level technical capsules unless technical constraints shape the experience
preferred_skills:
  - name: imagegen
    when: Use only when a bitmap concept, mockup, asset, or visual variant would clarify the direction.
  - name: presentations:Presentations
    when: Use only when the experience needs to be communicated in a deck.
  - name: none_required
    when: Use local project documents and direct reasoning for ordinary experience review.
control_questions:
  - Does the user understand what happened and why?
  - Is the key value visible at the right moment?
  - Is feedback close enough to the action that caused it?
  - Does this reduce friction or add explanation burden?
red_flags:
  - Correct implementation that is invisible to the user.
  - Feedback that arrives too late or in the wrong place.
  - Value hidden behind documentation, tutorial text, or developer assumptions.
veto:
  when: A feature is technically complete but does not create a clear user-facing signal, decision, or result.
  form: Propose the minimal feedback, copy, flow, or validation test needed.
```

## pipeline

```yaml
role:
  name: Pipeline / Process Maintainer
  invocation: team pipeline
  mode: on_demand
mission:
  summary: Keep project memory, scripts, finalizers, audits, caches, and instructions reducing future coordination cost.
prioritize_sections:
  first:
    - AGENTS.md
    - SOCRATEX.md
    - DOCS.yaml
    - ORCHESTRATION.yaml
    - tools/
    - core/
  then:
    - project packs
    - templates/
    - adapters/
    - audits or review files
  avoid:
    - product vision documents unless process changes affect their ownership or promotion rules
preferred_skills:
  - name: skill-creator
    when: Use when a repeated workflow should become a Codex skill.
  - name: plugin-creator
    when: Use when a repeated workflow should become a local Codex plugin or marketplace-ready package.
  - name: google-drive:google-drive
    when: Use only when process artifacts live in connected Google Drive.
control_questions:
  - Is there one owner for this instruction or document?
  - Will audit or finalizer catch drift next time?
  - Can this repeated manual step become a script?
  - Does the agent know when not to read this file?
red_flags:
  - New process rules without DOCS.yaml or workflow routing.
  - Multiple places of truth.
  - Manual recovery steps after a repeatable script failure.
  - Feature changes without pipeline_featurelist.json updates.
veto:
  when: A process change increases places of truth or relies on agent memory instead of a checkable contract.
  form: Propose one owner file, one routing rule, and one reusable check or script.
```
