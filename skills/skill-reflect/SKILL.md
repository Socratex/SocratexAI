---
name: skill-reflect
description: Turn logged skill learnings (LEARNINGS.jsonl next to each skill) into small owner-approved edits of SKILL.md. Use on /skill-reflect, during memory-review, or when skill_learn.py reports a skill as READY. Not for writing new skills from scratch.
---

# 🔁 Skill reflect

The second half of the self-improving skill loop, after capture (`modules/tools/scripts/skill_learn.py add`). Pattern: ACE (Reflector + Curator) with incremental delta edits and a human gate. Never rewrite a whole skill: whole rewrites erode details over time.

## Cost rules
- Start from `python $SOCRATEX_HOME/modules/tools/scripts/skill_learn.py status`. Touch only skills marked READY (or the one the owner named). If none: report one line and stop.
- Read a skill's open entries with `skill_learn.py show --skill <name>`, never the raw JSONL. Read only that skill's SKILL.md, not its other files, unless an entry names one.
- Run this on the standard tier. No reviewer subagent unless an edit touches safety, git or secret handling.

## Steps
1. **Reflect** (per READY skill): group the open entries by root cause. For each group decide one of:
   - fix an existing step or rule that caused it (preferred: the instruction was wrong or vague),
   - sharpen the `description` (kind `misfire`: the skill fired when it should not, or did not fire),
   - add one bullet to the `## Learned` section (a rule that has no natural home in the steps),
   - reject (one-off, wrong, or already covered). `win` entries confirm a rule; they never add text.
2. **Generalize**: write each edit as a rule that would have prevented the whole group ("Do X instead of Y, because Z"), not as a story of the one case. No dates, IDs or project names unless the skill is project-specific.
3. **Curate** (budget): `## Learned` holds at most 8 bullets. When it would go over, merge similar bullets or promote one into the steps and delete it from the list. SKILL.md stays under about 150 lines.
4. **Ask once**: one form for all skills (up to 4 questions; multi-select per skill; each option = one edit, shown as before -> after in the preview). Recommendation first.
5. **Apply** only the approved edits with Edit, then close the entries: `skill_learn.py close --skill <name> --ids ... --as applied`, and the rejected ones `--as rejected`.
6. Run `python $SOCRATEX_HOME/modules/tools/scripts/build_index.py --check` when a `description` changed. Commit per `core/rules/COMMITS.md` (message like "Refine <skill> from learnings").
7. Report in UCE: skills touched, edits applied or rejected, bullets in `## Learned` per skill.

## Rules
- Rejected entries stay in the log as `rejected`; a similar new note only raises their count and does not reopen them. A rejected entry with a count of 3 or more may be proposed once more, with that count as the evidence.
- Plugin skills (for example `unity:*`, `codex:*`) are not ours: never edit them. Log nothing for them.
- A skill whose learnings keep coming after two reflect passes is a design problem: propose splitting it or running the `spec` skill on it instead of adding more bullets.
