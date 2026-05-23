# Portable JSON Tooling

This folder contains generic JSON editing and audit helpers that can be copied
between projects without the higher-level Socratex document workflow.

Use this folder for structural JSON operations such as:

- reading a full node path
- setting a node value
- inserting, moving, or deleting entries
- inserting, setting, or moving list lines
- refreshing a list-document index
- migrating simple content into canonical list-document shape

Document routing, DOCS catalog reads, document cache generation, Markdown list
helpers, and project-specific document audits stay in `tools/documents/`.
