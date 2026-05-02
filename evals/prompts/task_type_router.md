# Eval Prompt: Task Type Router

A user asks:

> Fix the issue where import errors sometimes appear after a refactor, but also update the plan if this reveals a larger architecture problem.

The project has:

```text
STATE.yaml
_PLAN.yaml
BUGS.yaml
ORCHESTRATION.yaml
context-docs/
project/code/WORKFLOW.yaml
tools/knowledge_code_context.ps1
tools/done.ps1
```

Evaluate whether the agent classifies the request before broad reads, chooses the smallest useful context for a mixed bug and plan-impact task, loads code engineering context before editing, separates the bugfix from any plan update, and avoids reading unrelated documents.
