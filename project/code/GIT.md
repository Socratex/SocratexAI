# Git Safety for Code Projects

## Summary

This file defines source-control safety rules for programming projects.

## Worktree Rules

- Assume the worktree may contain user changes.
- Do not revert changes you did not make unless explicitly requested.
- Ignore unrelated dirty files.
- If user changes touch files you must edit, read them carefully and work with them.
- If user changes make the task impossible, stop and ask.
- Never use destructive commands such as `git reset --hard` or checkout-based reverts unless explicitly requested.

## Branch Rules

- Use a project-specific branch prefix when configured.
- If no prefix is configured, use `work/` or the user's requested convention.
- Do not create or switch branches when it would hide unresolved local work.

## Staging Rules

- Stage only explicit paths.
- Do not stage generated artifacts unless intentionally part of the change.
- Do not stage unrelated formatting churn.
- Inspect `git status` before staging.
- Prefer path-bounded helper scripts over broad `git add .`.

## Commit Rules

- Commit messages should name the behavior or contract changed.
- Mention skipped verification in the final report.
- Do not commit when required verification failed unless the user explicitly asks for a checkpoint commit.

