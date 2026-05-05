# Eval Prompt: Task Type Router

A user asks:

> Fix the issue where import errors sometimes appear after a refactor, but also update the plan if this reveals a larger architecture problem.

The project has:

```text
STATE.json
_PLAN.json
BUGS.json
WORKFLOW.json
context-docs/
project/code/WORKFLOW.json
tools/knowledge/knowledge_code_context.ps1
tools/repo/finalize_task_check_commit_push.ps1
```

Evaluate whether the agent classifies the request before broad reads, chooses the smallest useful context for a mixed bug and plan-impact task, loads code engineering context before editing, separates the bugfix from any plan update, and avoids reading unrelated documents.
