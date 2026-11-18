---
type: rules
title: Codex-specific rules
description: Codex additions to the shared core; tools/install.py concatenates core rules, this file and the local profile into ~/.codex/AGENTS.md.
updated: 2026-11-16
---

# 🧠 Codex-specific rules

## 📌 Session start
- Read `$SOCRATEX_HOME/core/DIRECTIVES.json`, then the project's `INDEX.json` and `AGENTS.md`.
- `~/.codex/AGENTS.md` is generated; change the sources in SocratexAI and rerun `tools/install.py` (a `git pull` in SocratexAI reruns it through the post-merge hook).

## 🤖 Execution
- Prioritize execution, verification and concrete outcomes over stylistic discussion; keep status updates brief and factual.
- Reviewing code or plans: risks, regressions, trade-offs and missing evidence first.
- Several approaches: state the trade-offs and recommend one. Clear request: do the work instead of over-discussing it.
- Before clearly high-usage work (large-repo sweeps, broad refactors, long retry loops), say why it is expensive, offer a scoped cheaper option and get the owner's confirmation.
- Native agent profiles live in `~/.codex/agents/` (`socratex_quick`, `socratex_standard`, `socratex_deep`, `socratex_reviewer`, generated from `core/ROUTING.json`); a project may define its own in `.codex/agents/`.
- Delegates never commit, push, finalize, start unattended loops or mark tasks complete; the parent integrates, reviews and finalizes.

## 🔎 Tools
- For code exploration and verbose command output use the `token-efficient-code` skill; keep project workflows authoritative and inspect raw evidence when a compact result is not enough.
