---
name: spec
description: Interview with one form before non-trivial work, ending with a SPEC.md file (goal, out of scope, decisions, acceptance criteria, edge cases, verification). Use on /spec or when a task is larger than about an hour, touches architecture, data, saves, payments or auth, or the requirements are unclear. Not for small fixes or one-off scripts.
---

# 📝 Interview -> SPEC.md

Goal: collect the missing decisions BEFORE writing code and save them as a checkable definition of done.

## When
- Yes: task over about an hour; architecture, data, saves, payments or auth; code that will outlive the conversation; unclear requirements.
- No: typo, small fix, prototype or one-off script. Act right away.

## Steps
1. Read what the repo already answers (code, task ledger, state files). Do not ask about what you can see.
2. List the gaps: scope, edge cases, error behavior, compatibility, performance, out of scope, how to verify.
3. Ask in one form (Claude: `AskUserQuestion`; Codex: one numbered list):
   - at most 4 questions per round, 2-4 options each, the recommendation first marked "(Recommended)",
   - every option with a one-sentence consequence,
   - only questions whose answer changes the implementation.
   Repeat rounds until the gaps are gone (usually 1-3).
4. Write `SPEC.md` at the path the project's INDEX.json names for specs (default `docs/specs/<name>.md`), in the documentation language from `local/profile.md`. Sections:
   - **Goal** (1-2 sentences, why),
   - **Out of scope**,
   - **Decisions** (from the interview, each with a short reason),
   - **Acceptance criteria** (testable, numbered),
   - **Edge cases** (each with the expected result),
   - **Verification** (a concrete command, test or manual step; ideally write the test before the implementation),
   - **Risks and assumptions**.
5. Show the spec in 3-6 bullets and ask for acceptance. Building starts after acceptance, preferably in a fresh session with SPEC.md as the only input.
6. After implementation: review in a separate context (`reviewer` subagent or `/codex:review`) against SPEC.md: "is every requirement done, do the edge cases have tests; skip style".

## Rules
- The spec is the source of truth. When the result is wrong, fix the spec and rerun; do not patch with prompts.
- Tasks from a ledger: link the entry in the spec, do not copy its text.
- Report in the UCE profile (`core/STYLE.md`).
