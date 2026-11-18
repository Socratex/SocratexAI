---
type: doc
title: flow-panel mod
description: Claude Code mod that draws an animated graph of Claude's work (you, Claude, sub-agents, tools, MCP, skills) with the 5-hour limit growth and a per-path cost estimate in a side panel.
updated: 2026-11-18
---

# flow-panel

A side panel for Claude Code (desktop app). It costs no model tokens: it only listens to engine events and draws SVG.

- Layout: a vertical file-tree, left-aligned (10px margin) with rounded elbows. `User` on top, `Claude` below, one branch per path.
- Trunk `User -> Claude`: growth of the account's 5-hour limit in percent since the mod first saw the current window.
- Lines from Claude: estimated share of the limit each path cost, in percent (3 decimals). Sub-agents use their exact turn usage; tools, MCP and skills are charged by the size of their result (the call itself counts as 0). A learned factor converts weighted tokens to percent, so the figure is `...` until the limit has moved once.
- Colours: user blue, Claude orange, sessions and sub-agents cyan, tool burgundy, MCP purple, skill yellow, desktop-app tools orange. A component working right now has a border in a lighter shade of its own colour; an idle one has none. Red ring = error, green = background work.

## Always on

`tools/install.py` adds `CLAUDE_CODE_PLUGIN_DIRS` (this folder) to the `env` block of `~/.claude/settings.json`, so the mod loads in every session after a restart. The panel opens at session start and again at every prompt.

## Switching off (outside SocratexAI)

Set `FLOW_PANEL` to `0` in the `env` block of a settings file; the project value wins over the global one.

- Everywhere: `~/.claude/settings.json` -> `"env": { "FLOW_PANEL": "0" }`
- One project: `<project>/.claude/settings.json` (or `settings.local.json`) -> `"env": { "FLOW_PANEL": "0" }`
- Back on for one project while globally off: `"FLOW_PANEL": "1"` in that project.

`/flow-panel` opens the panel by hand even when it is switched off. Changing the env needs a new session.

## Limits

- The limit figure is the whole account's, so other sessions inflate it and the learned factor.
- Lit paths (moving dots) follow the main turn. A state change that would draw the same picture is held back, not written, so the pane redraws (and blinks) only when something visible changes. SVG is pinned top-left, margin 5px.
- Sessions started from here (start_session) show as grey "Session N" tiles holding their own full tree, nested. Each session with the mod writes its tree to `$SOCRATEX_HOME/local/flow/<session id>.json`; the parent attaches files born within 2 min of its start_session call (a heuristic, so an unrelated session started at the same moment can be attached by mistake).
- The last view is saved to `local/flow/` (one file per session) and restored at session start, so a restart does not begin empty.
- A session that ends or is archived marks its file as ended, and a file not updated for 15 minutes is dropped, so finished sessions leave the tree (an idle live session disappears after 15 minutes of silence).
- A new prompt clears the segments; only paths used since then are shown.
- Lit paths (moving dots) follow the main turn. A state change that would draw the same picture is held back, not written, so the pane redraws (and blinks) only when something visible changes. SVG is pinned top-left, margin 5px.
- Sessions started from here (start_session) show as grey "Session N" tiles holding their own full tree, nested. Each session with the mod writes its tree to `$SOCRATEX_HOME/local/flow/<session id>.json`; the parent attaches files born within 2 min of its start_session call (a heuristic, so an unrelated session started at the same moment can be attached by mistake).
- The last view is saved to `local/flow/` (one file per session) and restored at session start, so a restart does not begin empty.
- A session that ends or is archived marks its file as ended, and a file not updated for 15 minutes is dropped, so finished sessions leave the tree (an idle live session disappears after 15 minutes of silence).
- A new prompt clears the segments; only paths used since then are shown.
- Figures refresh after each main turn, not continuously. Redraws are batched to one per 2 seconds, with dots keeping their phase, to avoid blinking.
- Tuning constants (font, weights) are at the top of `hooks/register.tsx`.
