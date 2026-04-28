# Core Commands

These commands are conceptual. A project may implement them as scripts, agent instructions, or manual workflows.

## INIT

Initialize a new project from this skeleton.

Use `initializer/FIRST-RUN.md` while it exists.

## CONTINUE

Resume the next active pass from the execution plan.

If no active pass exists, use the active state and backlog to propose the next best target.

## CAPTURE

Capture loose input without immediately executing it.

Classify the input as a task, decision, issue, reference, risk, or backlog item.

## PLAN

Turn selected backlog or captured input into one or more execution passes.

## REVIEW

Inspect the current artifact, plan, or change set for defects, risks, contradictions, and missing verification.

## AUDIT

Check project memory consistency:

- active state matches the plan,
- completed work is not still listed as active,
- unresolved requirements are preserved,
- decisions with durable impact are recorded,
- project packs do not duplicate core rules.

## FINISH

Close the current work unit:

- run the relevant quality gate,
- update active state,
- update completion log when something shipped,
- remove completed active passes,
- report what changed and what was not verified.

