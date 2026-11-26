---
type: doc
title: flow-panel mod
description: Claude Code mod that draws an animated graph of Claude's work (you, Claude, sub-agents, tools, MCP, skills) with the 5-hour limit growth and a per-path cost estimate in a side panel.
updated: 2026-11-26
---

# flow-panel

Colloquial name: **"kropki"** (the dots), after the moving dots on its lines.

A side panel for Claude Code (desktop app). It costs no model tokens: it only listens to engine events and draws SVG.

- Layout: a vertical file-tree, left-aligned (10px margin) with rounded elbows. `User` on top, `Claude` below, one branch per path.
- Trunk `User -> Claude`: growth of the account's 5-hour limit in percent since the mod first saw the current window.
- Lines from Claude: what each path cost: US cents (¢, rounded like the percent figures) below one dollar, then dollars with one decimal ($1.2), from the engine's own cost ledger (`$.session.usage().cost`, the figure `/cost` shows; free to read). Sub-agents get the ledger growth over their own turns; tools, MCP and skills get their result size priced at the session's average dollars per weighted token (`...` until known); a Session tile shows the sum of its branches while it works (so the figure grows as they finish) and, once idle, what it really spent since its last prompt. Parallel agents blur each other a little. The figure between User and Claude is the sum of the branches below.
- Dots: an active line has two lanes. The request goes down on one side of the line (west/south), the result comes back up on the other (east/north); the two lanes are 12 px apart and start half a second apart. Every second each lane sends a batch of 1 to 8 dots, in a row 1 px apart, all at the same speed (120 px/s). Up lane: batch size is the tier of the result's token pace (tokens per second of the turn or tool result: input + output + cache-write over wall time). Down lane: the tier of the request's pace (size of the call arguments over the call's duration); only tool calls have it, other lines send one dot down. Eight tiers, from almost nothing to tons; thresholds (220/375/560/800/1250/2300/5500 tok/s) are the p10..p95 of the owner's own turns and live in one table, `TIERS`, in `hooks/format.ts`. The line pulses with each batch. Timing follows the wall clock, so a redraw does not restart the dots.
- `/btw` (and `/subtask`, `/fork`): a fork that a command starts, not the Agent tool, shows as a pink `Side` branch with its own cost and dots, active while its turn runs. The engine gives no field that tells these three commands apart, so they share one branch.
- Toggle: a button above the drawing picks the figure on every line: cost (¢), time or tokens (shown in K, then M, one decimal; fresh tokens the path moved: agent turns = input + output + cache write, tools = request + result) and time (seconds and minutes, summed execution time, counting live while a path runs: the picture pre-draws one label per second for 70 s and a SMIL animation swaps them, and while anything runs one redraw per minute refills them; at most 6 ticking times per drawing; a session shows the sum of its branches, so parallel work adds up). The choice is this pane's own and is not shared with other sessions.
- Colours: user blue, Claude orange, sessions and sub-agents cyan, tool burgundy, background command or monitor (/tasks) dark blue, MCP purple, skill yellow, desktop-app tools orange, side forks pink. A component working right now has a border in a lighter shade of its own colour; an idle one has none. Red ring = error, grey = background work. Each session started from here gets a small shift of the whole palette (hue a few degrees, lightness a little up or down; table `SHADES` in `hooks/palette.ts`), shared by its tile and everything below it: fills, active borders, glow, lines and dots. This session's own tree is unshifted; state rings and text keep their colours because they carry meaning.

## Always on

`modules/tools/scripts/install.py` adds `CLAUDE_CODE_PLUGIN_DIRS` (this folder) to the `env` block of `~/.claude/settings.json`, so the mod loads in every session after a restart. The panel opens at session start and again at every prompt.

## Switching off (outside SocratexAI)

Set `FLOW_PANEL` to `0` in the `env` block of a settings file; the project value wins over the global one.

- Everywhere: `~/.claude/settings.json` -> `"env": { "FLOW_PANEL": "0" }`
- One project: `<project>/.claude/settings.json` (or `settings.local.json`) -> `"env": { "FLOW_PANEL": "0" }`
- Back on for one project while globally off: `"FLOW_PANEL": "1"` in that project.

`/flow-panel` opens the panel by hand even when it is switched off. Changing the env needs a new session.

## Data sources and cadence

One `reconcile()` rebuilds what is shown from real sources. Events (tool results, task notifications, `TaskStop`, Stop) only update an in-memory cache optimistically and may ask for a reconcile (at most one per 2 s); none of them is the only way a state ends.

- Cadence: a reconcile runs when the pane first draws and then every 30 s. It is armed by whichever hook fires first (`session.start`, `prompt.submit`, `turn.start`, `tool.call`, `classic.Stop`, the pane render), so a resumed session that never raised `session.start` still gets it. The old 3 s poll is gone.
- Sub-sessions: the desktop app's session store (`claude-code-sessions/<account>/<org>/local_*.json`, read with `$.fs`), one listing and only changed files re-read per reconcile. Children are found by `spawnedFrom.sessionId` equal to this session's local id, recursively (children of children). Only archived sessions and forks are hidden. A child with no `cliSessionId` yet shows as a "(starting)" tile. A child's own subtree comes from the store, not from its shared file.
- This session's local id: the engine gives no local id, so it is the store entry whose `cliSessionId` equals `$.session.id()`, else whose `lastAssistantCliSessionId` or `priorCliSessionIds` holds it (the engine id changes after a clear or compaction). Once learned it is kept. Until the app has written such an entry no tiles change.
- Tasks: `$.agent.list()` (subagents) and the last Stop event's `background_tasks` (shell, subagent, monitor, workflow); see the background tasks bullet for the rules and the limit.
- A session started elsewhere with the mod writes its tree to `local/flow/<id>.json` as before; the store file format is unchanged.

## Limits

- The limit figure is the whole account's, so other sessions inflate it and the learned factor.
- Lit paths (moving dots) follow the main turn. A state change that would draw the same picture is held back, not written, so the pane redraws (and blinks) only when something visible changes. SVG is pinned top-left, margin 5px.
- Sessions started from here (start_session, hand_off_to_session) show as grey "Session N" tiles holding their own full tree, nested. Each session with the mod writes its tree to `$SOCRATEX_HOME/local/flow/<session id>.json`. Which sessions are ours comes only from the desktop app's session store (see Data sources and cadence); where there is no store (not the desktop app) no tiles are drawn: the old brief-matching guess (first prompt versus the start_session brief, 2 min start window) was removed.
- The last view is saved to `local/flow/` (one file per session) and restored at session start, so a restart does not begin empty.
- A session that ends or is archived marks its file as ended. A child leaves the tree only when the store says it is archived (or a fork); there is no silence timeout and no age cutoff, so an idle live session stays.
- A new prompt clears the segments; only paths used since then are shown.
- Background agents (`run_in_background`) survive a new prompt: they stay as a running (grey) branch with moving dots. The agent start event says outright that it is a background one. The end comes from the reconcile: `$.agent.list()` lists the agent as completed, failed or killed (closed at once), or does not list it in 2 reconciles in a row (a freshly started agent is not judged for 30 s).
- Background tasks (what `/tasks` lists besides agents): a background Bash (`run_in_background`, Ctrl+B, or moved there by a timeout) and a Monitor show as one block each, with a grey ring, from the moment the tool returns its task id until the task ends. Events end one at once: the engine's task notification (a prompt with origin `task-notification`, or its transcript row, `ui.render` UserMessage with `task.id` + `task.status`, because a notification delivered into a running turn may raise no prompt event), a `TaskStop` result, or a finite Monitor's deadline (+5 s backstop). Such a notification is not the owner's prompt: it neither clears the panel nor restarts the prompt's cost. Events are never the only way a task ends: the reconcile closes a cached task that the last Stop event's `background_tasks` list no longer holds (or lists as completed / failed / killed) in 2 reconciles in a row. **Honest limit:** the types expose no `/tasks` API (`$.agent.list()` holds only agents), so the truth for shells and monitors arrives only with a Stop event; a Stop older than the task's start says nothing about it, and a task that ends while the session sits idle is closed only after the next Stop (or its notification). A task still running in the stored view that this process never saw start is closed by the next reconcile. Label: the task name cut to 8 characters (Bash: description, else the command; Monitor: description); the tooltip holds the full name. A failed task gets the red ring for a few seconds. The first end notification (and the first notification that is not an end) is written once to the debug log (`$SOCRATEX_HOME/state/flow-debug/<session>.log`, lines `task end ...`), to compare with `/tasks`.
- No usage, no dots: a task has no token or cost data, so its block is drawn like the others but without dots: the line pulses, the block pulses and glows, and a small grey blinking status LED sits in its top-right corner. The figure on its line is only time (ticking); cost and tokens show "-" and the task is left out of every sum, time included (a dev server running for 30 minutes does not inflate a session's or the total time). Background agents have per-turn usage, so they keep their dots and get no LED.
- Merged blocks: per category (tool, MCP, skill, app) the leaf blocks (no children) that cost under 1 cent merge into one block ("Tools", "MCP", "Skills", "Apps"), but only when a category has two or more of them; a single cheap block stays as it is. The threshold is always by cost, whatever the toggle shows, so blocks do not jump when the unit changes. The merged block shows the sum in the chosen unit; its tooltip lists the members in that unit, one per line ("Grep 0.2¢", "Read (x2) 0.4¢"; the same name twice is one line with a call counter). It is active if any member is, the red error ring beats the grey one, and it has the LED if any member has one. Blocks with an unknown cost ("...") and tasks are never merged. The merge happens before sessions are folded; the session rules are unchanged.
- Figures refresh after each main turn, not continuously. Redraws are batched to one per 2 seconds, with dots keeping their phase, to avoid blinking.
- Size guard: the pane refuses an SVG over 131072 characters and then shows "nothing to show yet" for the whole panel. Idle sessions sink to the bottom of their level and show no children. From 10 idle sessions on one level they become one tile "12 sessions" with their summed figure and a tooltip of their names, one per line (nested ones indented); working sessions keep their branches. A drawing still over 126000 characters folds all idle sessions, then loses moving dots and ticking times, then fewer nested session levels.
- At most 12 blocks per session level (`MAX_NODES`); the idlest finished one is dropped first, a running one never.
- Tuning constants: timings and weights in `hooks/model.ts`, drawing sizes at the top of `hooks/draw.ts`. The pure files have tests (`modules/tools/scripts/tests/test_flow_*.py`, loaded by `flow_js.py` with Node 22+): tiers and formats, merged blocks, task parsing and reconcile, the session tree, the rules (one test per closing reason: `test_flow_rules.py`) and the whole drawing with fixed data.

## Structure (where to edit what)

Imports only go downwards; the files are imported without an extension (what the engine resolves). Read `hooks/rules.ts` first: its header states the life cycle and the cadence.

| File | Layer | What it does |
| --- | --- | --- |
| `hooks/register.tsx` | hooks | The entry. Each engine event becomes one `dispatch` call; some also ask for a reconcile. No rules. |
| `hooks/schedule.ts` | cadence | Timers only: reconcile at init, every 30 s, debounced 2 s after an event; the 60 s refresh of ticking times. Reads the sources and hands the truth to the store. |
| `hooks/state.ts` | state | The one store. The only place the state is replaced (`nextState`, `reconcile`) and the saved picture and shared file are written (batched, skipped when the picture would not change). |
| `hooks/rules.ts` | rules | Pure functions, the clock passed in. `nextState(state, event)` for hook events, `reconcile(state, truth, now)` for tasks and the session tree. `CLOSE_RULES` lists every reason a task or agent is closed (one line each); the sub-session visibility rules are the comment above `isShownChild`. |
| `hooks/sources.ts` | sources | Read-only truth as plain data: the desktop app's session store, `$.agent.list()`, `local/flow/<id>.json` (read, and the one write), the transcript title. Stop `background_tasks` arrive as an event and are kept in the state. |
| `hooks/debug.ts` | debug | The debug log under `state/flow-debug/` (a debugging aid, nothing reads it). |
| `hooks/model.ts` | shared | Constants (cadence, weights), the state and event data types, `INITIAL`. |
| `hooks/draw.ts` | view | FlowView to SVG string. Asks `statusOf`, `isShownNode`, `isSessionIdle` from the rules; decides no status itself. |
| `hooks/format.ts` | view | Tiers, number and time text, merging of cheap blocks. |
| `hooks/palette.ts` | view | Colours and the per-session shade. |
| `hooks/pane.tsx` | view | The pane's elements (figure toggle and drawing), from ready data. |

State life cycle: a followed background task or agent is `running` until one rule of `CLOSE_RULES` closes it (`closed(reason)`); it is never reopened. To change when something closes, edit that rule (or its constant: `TASK_GRACE_MS`, `TASK_MISSES`, `TASK_ENDED`). To change which sub-sessions show, edit `isShownChild`. To change a hook's effect, edit its case in `nextState`.
