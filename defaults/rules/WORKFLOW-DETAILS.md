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

## Self-improvement loop
- Trigger (DIRECTIVES row): you cannot do something, hit a limit, repeat a workaround, or the owner misses a capability. Run `sox ledger find "<2-5 words>" [--project <repo>]` (read-only, max 3 hits, exit 1 = no hits, exit 2 = query too short). `--all` also shows rejected items; use it only to check, never to suggest.
- Suggest in one UCE line, for example: `💡 w tym projekcie może pomóc X (pozycja N, status)`. Status "adopted, on": remind how to use it; "adopted, off": propose that the owner enables it; "considering": give the result and the entry condition.
- At most once per item per session, at most 3 hits, never rejected items. Never install, enable or run the suggested solution: the owner decides (`defaults/rules/SAFETY.md`).
- Zero hits: ask the owner whether to search the web for a ready solution of any kind (tool, plugin, MCP, skill, framework, method, script). Search only after a yes. Record anything adopted or evaluated in the ledger (section Named solutions ledger).
- Spec: `docs/specs/self-improvement-loop/SPEC.md`.

## Reference packs
- Packs are updated only on request: `modules/tools/scripts/update.py refs`; pins move only with `subrepos.py bump`.

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

## Env files (details)
- Agents never read `.env*` directly (the guard blocks it). To learn which variables a project needs or how two env files differ, run `python $SOCRATEX_HOME/modules/tools/scripts/env_safe.py <file>`: it prints `KEY=value` only when the value is provably non-secret (empty, boolean, small integer or port, local host, URL without credentials, path, placeholder, `${VAR}` reference) and `KEY=<masked>` for everything else, unknown values included. Secret-looking key names (password, secret, token, key, dsn, auth, salt, ...) are always masked.
- `--keys-only` prints names only; `--compare <other>` prints `<different>` for differing unsafe values (the Omega machine_constants comparator rule), `a -> b` for differing safe ones, and marks keys present in one file only.

## Finishing (details)
- After the commit: `modules/tools/scripts/risk_score.py --commit HEAD` (verification level, report-only until the owner switches it on) and log the outcome once with `modules/tools/scripts/routing_log.py` (see `defaults/rules/ROUTING.md`).
- Log every new finding about working with AI in `$SOCRATEX_HOME/docs/AI-PRACTICES.md` (findings log: date, what, evidence, verdict) and commit it with the core.
