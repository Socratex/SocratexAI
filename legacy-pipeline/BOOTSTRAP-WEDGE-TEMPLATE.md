# BOOTSTRAP PENDING — SocratexPipeline not yet installed for this project

**On the first AI session that does real work in this project, run the bootstrap procedure before doing anything else.**

## What to do

1. Read the bootstrap doc from the local SocratexAI source checkout.
2. Read the workspace convention from the local workspace root when one exists.
3. Look at the bootstrapped reference projects for layout examples:
   - `<workspace>/reference-projects/mature-migrated/` (mature, migrated)
   - `<workspace>/reference-projects/fresh-bootstrap/` (fresh bootstrap)
4. Ask the user the bootstrap questions (language → context → programming subset).
5. Inspect this project for ecosystem signals (composer.json, package.json, pyproject.toml, go.mod, Cargo.toml, *.csproj, etc).
6. Install the project-local pipeline:
   - `.aiassistant/socratex/AGENTS.md` — project working rules (use the fresh-bootstrap reference project's `.aiassistant/socratex/AGENTS.md` as a template; rewrite for this project's stack)
   - `.aiassistant/socratex/DOCS.md` — document roles
   - `.aiassistant/socratex/PIPELINE-CONFIG.yaml` — link to global SocratexAI + project metadata
   - `.aiassistant/<project>.md` — project-specific code-gen rules (optional; use the mature reference project shape when available)
   - `AI.md` at project root — branch STATE/PLAN convention (copy from the mature reference project and adjust the working-rules pointer)
   - `CLAUDE.md` at project root — merge with whatever exists; add the "Pipeline Source" section pointing at the resolved SocratexAI source checkout
   - `ignored/ai-socratex/.gitkeep` — ensure the dir exists
7. Add `/ignored` (or equivalent) to `.gitignore` if it's not already there.
8. **Delete this `BOOTSTRAP-PENDING.md` file** when bootstrap is complete.

## Hard rules during bootstrap

- Do NOT touch any existing root file (CLAUDE.md, AGENTS.md, AI.md) without first snapshotting it to `pipeline-snapshots/YYYY-MM-DD-pre-bootstrap/`.
- Default merge mode is **merge** (preserve existing content, add Pipeline Source section).
- `.aiassistant/` is English only and committed.
- `ignored/ai-socratex/` is gitignored and matches the user's prompt language.
- Never run git commands during bootstrap — show the diff and let the user commit.

## Path adjustment

If this project is at `<workspace>/<name>/`, the global pipeline is usually at `../SocratexAI/`.
If this project is nested under a workspace subfolder, resolve the SocratexAI source checkout through the workspace marker instead of hardcoding a personal or project-specific path.
