# Eval Prompt: Knowledge Entry Lifecycle

A user says:

> Add this reusable rule to the knowledge layer, rename an older duplicate, delete an obsolete entry, and tag the new rule for code review and architecture.

The project has source knowledge documents, compiled SQLite knowledge, generated JSON fallback tables, and scripts for upsert, delete, rename, query, select, and file-table operations.

Evaluate whether the agent uses controlled source-level knowledge scripts and preserves tags/type taxonomy instead of manually editing generated compiled artifacts.
