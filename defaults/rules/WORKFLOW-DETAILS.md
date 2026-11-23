---
type: rules
title: Workflow details moved out of the startup files
description: Verbatim detail bullets from defaults/RULES.md (named solutions, repeated fixes, skill learnings, context economy, finishing); the startup file keeps one short line per topic.
updated: 2026-11-21
---

# Workflow details

Opened from `defaults/RULES.md` when you actually do the thing described. The text below is moved verbatim from `defaults/RULES.md`.

## Named solutions ledger
- Named solutions ledger: whenever the owner asks to use, try or evaluate an existing named solution (plugin, skill pack, methodology, tool, program, MCP server), record it in `$SOCRATEX_HOME/docs/IMPROVEMENTS.json` (status adopted / rejected / considering, `expected_result`, `result`, `result_evidence`) and commit it to SocratexAI. Read the ledger first, so nothing already rejected is proposed again. Plain "remember this rule" requests are not named solutions and do not go there.

## Doing the work (details)
- Repeated mechanical fix (formatting, index drift, cache refresh): use or write a small owning script and wire it into the finalizer, so nobody has to remember the manual sequence. Third repetition of anything: propose script > skill > memory note.
- Two scripts doing the same thing: extract a shared helper and parameterize it, do not keep a second copy.
- Convenience drives habit: the correct path must be the default path (helper, template, lint gate); a rule that relies on willpower alone will not last.
- Skill learnings: when the owner corrects you while one of our skills is in use, or a skill step fails, needs a workaround or the skill misfires, log one sentence right away: `modules/tools/scripts/skill_learn.py add --skill <name> --kind correction|failure|workaround|misfire --note "<do X instead of Y>"`. Do not edit the skill then; skill `skill-reflect` applies batched edits.

## Context economy (details)
- Big JSON: read single fields with `$SOCRATEX_HOME/modules/tools/scripts/json_read.py`, never dump whole ledgers.
- Diffs: `git diff --stat` first; full diff only for logic files; a large diff (over about 150 lines) goes to a reviewer subagent that returns a verdict.
- Logs, test output, builds: filter with `tail` / `rg` for errors; a subagent reads full logs.
- Wide searches across many files: a cheap subagent returns the conclusion, not the dump.

## Finishing (details)
- After the commit: `modules/tools/scripts/risk_score.py --commit HEAD` (verification level, report-only until the owner switches it on) and log the outcome once with `modules/tools/scripts/routing_log.py` (see `defaults/rules/ROUTING.md`).
- Log every new finding about working with AI in `$SOCRATEX_HOME/docs/AI-PRACTICES.md` (findings log: date, what, evidence, verdict) and commit it with the core.
