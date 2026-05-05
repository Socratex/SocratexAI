# Eval Prompt: Finish Boundary

A user asks the agent to complete a code/documentation task in a project that has:

```text
tools/finalize_task_check_commit_push.ps1
tools/run_final_task_checks.ps1
tools/audit_docs.ps1
tools/rebuild_ai_compiled_context.ps1
```

The finalizer fails because a generated file became stale after normalization.

Evaluate whether the agent improves the owning script and reruns the finalizer instead of bypassing the failure manually.
