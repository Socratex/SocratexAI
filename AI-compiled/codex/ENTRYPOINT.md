# Compiled Codex Entrypoint

Generated: source-36a62d090533

This directory is generated. Do not edit it by hand.
Edit source instructions, then run:

~~~bash
python -B tools/pipeline/rebuild_ai_compiled_context.py
~~~

Primary rule: use these compiled files for fast agent orientation, then read source files only when exact details or edits are needed.

Read order for Codex:

1. `AI-compiled/codex/RULES.compiled.md`
2. `AI-compiled/codex/WORKFLOW.compiled.md`
3. `docs-tech/PIPELINE-BOOTSTRAP.json` for source-pipeline routing indexes
4. `AI-compiled/codex/CONTEXTUAL-WORKFLOW.compiled.md` only when priority steering matters
5. `AI-compiled/codex/TEAM.compiled.md` only when a role is requested or routed
6. Source files referenced by the compiled layer when implementation requires exact detail

Generated checksum data lives in `AI-compiled/checksum.json`.
