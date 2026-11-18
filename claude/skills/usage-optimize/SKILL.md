---
name: usage-optimize
description: Analyze token usage and cost of Claude Code work with `prompt-analytics` (local JSONL) and say what to optimize in the workflow (router sessions, cross-agent handoff, subagents, CLAUDE.md/AGENTS.md, MCP). Use when the owner asks about cost, usage, tokens, limits, "what to optimize", or provides a CSV from `prompt-analytics export`.
---

# 💸 Usage analysis -> optimizations

🎯 Result: 3-6 concrete workflow changes, each with an estimated saving in $ and %. No generic advice like "write shorter prompts".

## 1. 📥 Data
- CLI: `prompt-analytics` (installed with `uv tool install`). It reads `~/.claude/projects` live; a CSV is not required.
- Run from the scratchpad (the CLI writes `./output`), always with `--format json` and a range `--since YYYY-MM-DD` (default: last 7 days; whole range when there are less than 3 days of data).
- A CSV from `export --flat` helps with per-prompt or per-session rankings (`prompt_preview`, `subagent_tokens`, `category`), but run the CLI reports anyway.

| Report | What you take from it |
|---|---|
| `summary` | total cost, subagent share |
| `by-token-type` | context rent (cache read/write) vs generation |
| `by-context` | what fills the context: tool output, config, conversation, files |
| `overhead` | fixed session start cost (system prompt + CLAUDE.md + MCP) |
| `ttl` | losses after breaks over 5 min / over 1 h |
| `context` | context growth with session depth |
| `sessions` / `prompts --top 15` | most expensive sessions and prompts |
| `model-category --whatif <cheaper model>` | what a cheaper model would save |
| `by-file` | files read repeatedly or expensive in rent |
| `recommend`, `compactions` | whether /compact or a new session pays off |

`by-category` works only after `prompt-analytics categorize`, which calls an LLM and costs money: run it only with the owner's approval.

## 2. 🔎 Signal -> lever
- **Tool output over 40% of context**: big dumps (logs, diffs, JSON, other agents' results) go through a subagent or `head` / `tools/json_read.py`; wide searches through a cheap subagent.
- **Config or turn-1 overhead over about 60k**: trim always-loaded rules, disable unused MCP servers, move rare rules to on-demand documents.
- **`ttl` losses after 1h+ breaks**: start a new session from a short state file instead of resuming a fat one.
- **Router session with many expensive notifications**: every notification is a full turn with the whole context; batch steps, let a cheap subagent collect results and return 3 lines.
- **What-if shows big savings for ops/notification/test**: route those to sonnet or haiku; keep opus for plans, architecture and review.
- **Context grows with depth or `recommend` is not empty**: /compact or a new session at a batch boundary.
- **Expensive single "continue" prompts or long pastes**: shorter start prompt, a link to a state file instead of pasted history.
- **Subagents over 30% of cost**: check for duplicated work or repeated reads; narrower briefs and cheaper models.
- Also run `python $SOCRATEX_HOME/tools/routing_stats.py` in the project and include its proposals.

Saving estimate: source cost x realistic reduction %. State the assumption in a few words, for example "~50% tool output".

## 3. 📤 Report (UCE)
```
💸 <period>: $X (context rent Y%, generation Z%)
* 🔥 Top 1: <lever> -> ~$A/day (<assumption>)
* 🔥 Top 2: ...
* 💡 Quick: <one-line change>
* ❓ <decision for the owner, if any>
```
- No tables or session IDs unless the owner asks.
- Offer to apply the top lever (rules change, routing, skill, habit); apply only after a yes.
- Save a short dated summary to the project's `audits/usage_<YYYYMMDD>.md` so the next analysis can compare the trend.
