# Eval Prompt: Context-Tagged Knowledge Prelude

A user asks:

> I changed the pipeline again. Check whether this affects the eval plan and update only what is needed.

The project has:

```text
tools/context_tags.ps1
tools/knowledge_select.ps1
tools/knowledge_file_select.ps1
AI-compiled/project/knowledge.sqlite
AI-compiled/project/knowledge-files/
project/code/WORKFLOW.yaml
context-docs/ENGINEERING.yaml
```

Evaluate whether the agent derives context tags from the substantive user request, queries the compiled knowledge layer with those tags before answering or editing, keeps the context prelude lightweight, and still reads exact source files before making changes.
