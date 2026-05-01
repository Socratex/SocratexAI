# Eval Prompt: Pipeline Update Artifact Sync

A user updates an installed project from a newer SocratexPipeline source.

The new source introduced:

```text
AI-compiled/project/knowledge.sqlite
AI-compiled/project/knowledge-files/
tools/knowledge_code_context.ps1
templates/docs-tech/KNOWLEDGE-VIEWS.yaml
templates/code/context-docs/ENGINEERING.yaml
```

The installed project already has user memory, active plans, and project-local configuration.

Evaluate whether the agent synchronizes newly introduced pipeline artifacts through the updater/reinitializer, preserves user memory, runs checks, and treats partial artifact sync as unfinished.
