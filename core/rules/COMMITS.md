---
type: rules
title: Commit rules
description: When and how Claude and Codex commit, push and squash.
updated: 2026-11-16
---

# 📦 Commit rules

- Commit and push your own finished work at the end of the prompt, not after each small edit, and without asking.
- Own paths only: `git commit -- <paths>` or the project finalizer with explicit paths. Never `git add -A`: other sessions may have uncommitted work in the tree.
- Format: subject line, blank line, up to about 6 short `-` bullets. Simple English, no emoji, understandable without domain knowledge; explain terms, no jargon. End with the attribution line the harness requires.
- Squash: after committing, look at unpushed commits; when two or more neighbors cover the same domain, merge them into one with one message. Never rewrite commits already pushed unless the owner asks for history cleanup.
- Squash on a dirty tree without rebase: `git commit-tree <tree> -p <parent> -F msg` (keep author and dates), then `git update-ref refs/heads/<branch> <new> <old>`, and check that the final tree is identical. When the project finalizer pushes immediately, run it with its no-push option first.
- No extra post-push verification unless the owner asks or the push fails.
