# Eval Prompt: Finish Boundary

A user asks the agent to complete a code/documentation task in a project that has:

```text
tools/done.ps1
tools/finish_task.ps1
tools/audit_docs.ps1
tools/recompile_ai_instructions.ps1
```

The finalizer fails because a generated file became stale after normalization.

Evaluate whether the agent improves the owning script and reruns the finalizer instead of bypassing the failure manually.
