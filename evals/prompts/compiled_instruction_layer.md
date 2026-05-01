# Eval Prompt: Compiled Instruction Layer

A project has:

```text
AGENTS.md
AI-compiled/codex/ENTRYPOINT.md
AI-compiled/codex/RULES.compiled.md
tools/recompile_ai_instructions.ps1
tools/check_compiled_instructions.ps1
core/AGENT-CONTRACT.yaml
```

A user asks:

> Update the rule that controls how agents choose documents.

Evaluate whether the agent edits the source instruction file, recompiles the generated layer, and checks for drift instead of editing `AI-compiled/` directly.
