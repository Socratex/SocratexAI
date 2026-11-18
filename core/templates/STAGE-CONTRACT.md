---
type: template
title: Stage contract
description: Template for one stage of a multi-stage pipeline with a human review after each stage (numbered folders, contract, output handoff).
updated: 2026-11-16
---

# 🧩 Stage contract template

Use for linear pipelines where a person reviews each stage's output before the next one runs (asset pipelines, content production, research to draft to final). Not for concurrent or branching multi-agent work.

Layout: one numbered folder per stage, a `CONTEXT.md` contract in each, an `output/` folder as the handoff. The next stage reads whatever is in the previous `output/`, including the owner's edits.

```text
<pipeline>/
  CONTEXT.md            routing: what the pipeline is for, list of stages
  _config/              stable reference shared by all stages (style guides, rules)
  01_<stage>/
    CONTEXT.md          this contract
    references/         optional stage-only reference material
    output/             handoff to the next stage
  02_<stage>/
    ...
```

Copy the block below into each stage's `CONTEXT.md`:

```markdown
---
type: stage
title: 01 <stage name>
description: <one line: what this stage produces>
updated: <YYYY-MM-DD>
---

## Inputs
| What | Where | Required |
| --- | --- | --- |
| previous output | ../00_<prev>/output/ | yes |
| reference | ../_config/<file> | yes |

## Process
1. <step>
2. <step>
- Load only the inputs listed above (keep the stage context small).
- Mechanical work goes to scripts, judgment to the agent.

## Outputs
| File | Format | Done when |
| --- | --- | --- |
| output/<name> | <format> | <acceptance check> |

## Review
The owner reviews `output/` and may edit it; the next stage starts only after that.
```
