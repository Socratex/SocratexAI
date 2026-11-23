---
type: rules
title: Claude-specific rules
description: Claude Code additions to the shared core (subagents, hooks, environment, tools); imported by the generated ~/.claude/CLAUDE.md.
updated: 2026-11-16
---

# 🤝 Claude-specific rules

The shared core (`defaults/RULES.md`, `defaults/STYLE.md`) applies first; this file adds what only Claude Code needs.

## 📌 Session start
- Read `$SOCRATEX_HOME/defaults/DIRECTIVES.json`, then the project's `INDEX.json` (and the project `DIRECTIVES` it points to, if any). Open further rule documents only when you do that thing.
- Check where you run (`Platform` in the session context): desktop Claude Code on Windows allows background commands and local tools; sandboxed VMs have time limits and no local apps.

## 🪆 Subagents
- The main session is the router: plans, delegates, waits, verifies and integrates.
- Session model: routing, ops and tests on sonnet; opus only for architecture, diff review and hard debugging, as a subagent or a separate session.
- Agents per tier live in `~/.claude/agents/` (linked from `claude/agents/`): `scout` (haiku, search), `implementer` (sonnet, execution from a spec), `planner` (opus, plans, read-only), `reviewer` (opus, independent review). Delegate with `subagent_type` instead of a hand-written `model`.
- The default subagent model is sonnet (`CLAUDE_CODE_SUBAGENT_MODEL`); pass `haiku` or `opus` explicitly.
- Give every subagent a complete brief (goal, paths, criteria, result format) and pass the reply profile when it writes to the owner. Do not delegate tasks whose brief is longer than the work.
- A separate session that must not touch the shared tree (big refactor, experiment): `claude --worktree <name>`.

## 🔒 Hooks (enforced by the harness, installed by `modules/tools/scripts/install.py`)
- `PreToolUse` runs `claude/hooks/guard.py` (destructive git, secret files, ledger dumps; projects add patterns in `.ai/guard.json`).
- UCE reply check (`claude/hooks/uce_check.py`) is no longer wired as a Stop hook (owner decision 2026-11-17): chat replies are never blocked or re-prompted. Follow `defaults/STYLE.md` yourself; when writing files, self-correct against the project style.
- A project may add its own `Stop` gate in its `.claude/settings.json` (fast tests of the changed area). Fix the code, not the tests.

## 🧰 Tools
- Standard tools (`rg`, Read, Edit) first. Code navigation by symbol (Serena MCP) or dependency graphs (graphify) only when the project lists them and they beat a plain search; graph hits are pointers, read the source before editing.
- Plugin `codex@openai-codex`: `/codex:review` (second opinion on a diff) and `/codex:rescue` (delegation). The always-on review gate stays off because it burns both agents' limits. Which work goes to Codex (search, internet research, non-mathematical 2D/3D art, summaries, mechanical edits, second opinions) and which stays with Claude (code, maths, architecture): `defaults/rules/ROUTING.md`, section load balancing.
- Disable MCP servers and plugins you do not use: each adds a fixed cost to every session.

## 🧪 When improving AI
- The owner names a plugin, tool, method or program to use or evaluate: read `$SOCRATEX_HOME/docs/IMPROVEMENTS.json` first (do not re-propose rejected items), then record the outcome there with status, expected_result, result and result_evidence, and commit it to SocratexAI. Details: `defaults/RULES.md`, bullet Named solutions ledger.

## 💬 Replies
- Follow `defaults/STYLE.md` (UCE). Codex-style report headers from project files (Usage/Impact blocks) are for Codex; Claude uses UCE.
