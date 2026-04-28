# Branch Mode

## Purpose

Branch-scoped mode separates committed project directives from local working memory.

Use it when `PIPELINE-CONFIG.yaml` contains:

```yaml
workflow:
  branch_mode: branch_scoped
```

## Layout

Committed project directives live under `.aiassistant/`.

Local branch work lives under `ignored/ai-socratex/` and should be gitignored.

Recommended layout:

```text
.aiassistant/
  socratex/AGENTS.md
  socratex/DOCS.md
  socratex/PIPELINE-CONFIG.yaml
  <project>.md
ignored/ai-socratex/
  <branch>-STATE.md
  <branch>-PLAN.md
  TODO.md
```

## Session Start

1. Detect the current Git branch.
2. Normalize the branch name for filenames.
3. Read `ignored/ai-socratex/<branch>-STATE.md` if it exists.
4. Read `ignored/ai-socratex/<branch>-PLAN.md` if it exists.
5. Create both files from templates when missing and branch-scoped mode is active.

If branch detection fails, use `unknown-branch` and report the uncertainty.

## File Language

Files under `ignored/ai-socratex/` use the user's prompt language.

This is intentional because these files are local working memory, not review-facing project directives.

Committed files under `.aiassistant/` should remain English-only unless the project explicitly chooses another review language.

## State and Plan Contract

`<branch>-STATE.md` stores facts:

- findings,
- root causes,
- changes made,
- verification,
- current blockers,
- decisions that may need promotion.

`<branch>-PLAN.md` stores next steps only:

- immediate next action,
- remaining scoped tasks,
- checks still needed,
- open questions.

Do not keep history in the plan.

Update branch STATE and PLAN continuously during the branch, not only at the end.

## Branch End

When the branch is merged or closed:

- promote durable findings to `context-docs/`,
- promote durable decisions to `DECISIONS.yaml`,
- record shipped outcomes in `CHANGELOG.yaml` when appropriate,
- leave local branch files as reference unless the user asks to clean them.

Do not promote every scratch note.

