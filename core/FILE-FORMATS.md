# File Formats

## Summary

This file defines format choices across SocratexPipeline project types.

## Code Projects

Code projects should use YAML and JSON for standardized project memory, registries, configuration, indexes, diagnostics, and AI-readable structured documents.

Use Markdown in code projects only for scratch-style files:

- raw user instruction intake,
- temporary notes,
- rough drafts,
- human scratchpads,
- short README-style user-facing docs when no structured state is stored.

Preferred code-project formats:

- `STATE.yaml`
- `_PLAN.yaml`
- `TODO.yaml`
- `BUGS.yaml`
- `BUGS-SOLVED.yaml`
- `CHANGELOG.yaml`
- `DECISIONS.yaml`
- `PIPELINE-CONFIG.yaml`
- `context-docs/*.yaml`
- generated indexes or caches as `.json`
- diagnostics summaries as `.json` when machine-read, `.yaml` when agent-read

## Non-Code Projects

Non-code user-facing files should remain Markdown by default.

Use YAML in non-code projects only for large AI-only files, structured internal memory, or mega-files that are primarily read by the agent rather than the user.

Do not force users to read YAML when Markdown is clearer for human-facing work.

## Migration Rule

When converting a code project from Markdown to YAML/JSON:

1. Preserve all unresolved requirements.
2. Convert standardized registries first.
3. Keep raw scratch files as Markdown.
4. Update the audit rules and initializer together.

