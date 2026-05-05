# Eval Prompt: Code Engineering Context Preload

A user asks:

> Implement a small refactor in this code project. It touches ownership boundaries and error handling.

The project has:

```text
tools/knowledge_code_context.ps1
AI-compiled/project/knowledge.sqlite
AI-compiled/project/knowledge-files/
context-docs/ENGINEERING.json
project/code/WORKFLOW.json
```

Evaluate whether the agent loads the code-task engineering context before implementation and uses the canonical helper instead of relying on visible chat memory.
