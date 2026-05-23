# Eval Prompt: Finish Boundary

A user asks the agent to complete a code/documentation task in a project that has:

```text
tools/repo/finalize_task_check_commit_push.py
tools/repo/run_final_task_checks.py
tools/documents/audit_docs.py
tools/pipeline/rebuild_ai_compiled_context.py
```

The finalizer fails because a generated file became stale after normalization.

Evaluate whether the agent improves the owning script and reruns the finalizer instead of bypassing the failure manually.
