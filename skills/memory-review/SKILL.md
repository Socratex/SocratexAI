---
name: memory-review
description: Monthly review of agent memory, scripts, skills and rule documents - merges duplicates, flags stale or unused items, asks the owner in one form what to change. Use on /memory-review or when the owner asks to clean up memory or tidy the tools.
---

# 🧹 Memory and tool review

Goal: keep memory and tools short, true and useful. Delete nothing without approval; move items to a `_trash/` folder instead.

## Steps
1. Back up first: `python $SOCRATEX_HOME/modules/tools/scripts/backup.py`.
2. Load the memory index (Claude: the project's `memory/MEMORY.md`; Codex: its memories), `$SOCRATEX_HOME/INDEX.json`, the project's `INDEX.json`, the list of skills and the latest `docs/AI-PRACTICES.md` findings.
3. Look for:
   - duplicates and memory entries that say the same thing (propose a merge),
   - stale or contradictory entries (check that the file, folder or script they name still exists),
   - entries about things the repository already shows (redundant),
   - scripts and skills unused for more than 2 months (modification date, mentions in logs),
   - actions repeated 3 times without a script (automation candidates),
   - size: memory index over about 50 lines, an always-loaded rules file over about 150 lines,
   - INDEX.json entries whose path no longer exists (`python $SOCRATEX_HOME/modules/tools/scripts/build_index.py --check`).
4. Run `python $SOCRATEX_HOME/modules/tools/scripts/skill_learn.py status`; for READY skills follow skill `skill-reflect` and put its edits into the same form as step 6.
5. If `prompt-analytics` is installed, add 2-3 numbers (cost, strong-model share, fixed session start cost) and compare with last month.
6. Ask in one form (up to 4 questions, recommendation first, one-sentence consequence per option), for example: which merges to approve (multi-select), what to do with unused scripts (move to `_trash/` / keep / show list), whether to automate a repeated action with a script.
7. Apply only approved changes. Report in UCE: entries merged, items moved, new index size.
8. Add a dated finding to `docs/AI-PRACTICES.md` when the review taught something new.

## Rules
- Memory can be wrong: fix or remove a false entry (after approval).
- Never store secrets or client data in memory.
