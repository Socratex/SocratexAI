# Compiled Codex Entrypoint

Generated: source-186ef47da162

This directory is generated. Do not edit it by hand.
Edit source instructions, then run:

~~~powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/recompile_ai_instructions.ps1
~~~

Primary rule: use these compiled files for fast agent orientation, then read source files only when exact details or edits are needed.

Read order for Codex:

1. AI-compiled/codex/RULES.compiled.md
2. AI-compiled/codex/WORKFLOW.compiled.md
3. AI-compiled/codex/ORCHESTRATION.compiled.md only when priority steering matters
4. AI-compiled/codex/TEAM.compiled.md only when a role is requested or routed
5. Source files referenced by the compiled layer when implementation requires exact detail

Generated checksum data lives in AI-compiled/checksum.json.
