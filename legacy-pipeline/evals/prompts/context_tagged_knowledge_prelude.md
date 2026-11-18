# Eval Prompt: Context-Tagged Knowledge Prelude

A user asks:

> I changed the pipeline again. Check whether this affects the eval plan and update only what is needed.

The project has:

```text
tools/knowledge/context_tags.py
tools/knowledge/knowledge_select.py
tools/knowledge/knowledge_file_select.py
AI-compiled/project/knowledge.sqlite
AI-compiled/project/knowledge-files/
project/code/WORKFLOW.json
context-docs/ENGINEERING.json
```

Evaluate whether the agent derives context tags from the substantive user request, queries the compiled knowledge layer with those tags before answering or editing, keeps the context prelude lightweight, and still reads exact source files before making changes.
