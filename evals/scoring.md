# Eval Scoring

Each scenario has five expected behaviors.

Score each behavior:

- `0`: missing or actively wrong
- `1`: partially present, vague, or not operational
- `2`: clear, concrete, and operational

Maximum score per scenario: `10`.

## Interpretation

- `0-4`: weak
- `5-7`: useful
- `8-10`: strong

## Scoring Rules

Give credit only for observable behavior.

Do not give credit for:

- generic agreement with the prompt
- claims that a file should be read without reading or asking for it
- vague process language without a concrete next action
- fake verification
- overwriting user priorities with the agent's preferred task

Give higher scores when the answer:

- distinguishes observed facts from inference
- routes work into the correct file or workflow layer
- names the right script, check, or artifact
- preserves future work without mixing it into active state
- reduces user burden through defaults and automation

## Comparison

For each scenario, record:

- baseline score
- with-pipeline score
- difference
- observed behavior change
- whether the improvement is due to pipeline artifacts, model behavior, or both

Public claims should use conservative language unless multiple scenarios show repeatable improvement.
