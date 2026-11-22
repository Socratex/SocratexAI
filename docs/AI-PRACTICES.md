---
type: log
title: AI Practices
description: Portable knowledge base and dated findings log on working well with AI coding agents (Claude Code, Codex).
updated: 2026-11-16
---

# AI-PRACTICES

Portable knowledge base: how to work well with AI coding agents (Claude Code, Codex) for game development and for B2B or freelance work.
The owner keeps appending every new finding here. Hand this file to any agent on any machine (for example a company Claude account) with: "Read AI-PRACTICES.md and apply the section 'Instructions for the receiving agent'."

Last updated: 2026-11-16.

## Owner profile (adapt your behavior)

- Replies in the owner's configured language. Style: short, result first, an emoji status line plus 3-6 bullets (profile "UCE"); details only on request. Text for other people (PRs, docs, tickets) in English prose.
- Very productive and energized by motion; **waiting / standby is the main friction**, not workload. Do not coach on rest or burnout. Design for flow: background long jobs, run independent work in parallel, chain approved tasks without asking, never ping-pong with many small questions.
- Ambiguity rule: when a request is imprecise or you are unsure what is meant, ask ALL missing questions at once in ONE form (see "Interview form rule"). One prompt = one answer.
- Quality does not depend on model tier: cheaper models must still produce clean architecture, borrowed-over-invented solutions and documented decisions; gates and diff review enforce it.

## What the owner already does well (keep doing it)

- **Small batches, commit per change** with a canonical finalizer script: the exact practice DORA 2025 names as the safety net for AI-speed code.
- **Routing sessions + cost-aware model tiers**: cheap model for routing, ops and subagents; expensive model only for architecture, review and hard debugging. Decisions are backed by a written token audit, not by feel.
- **Measure before optimizing**: usage audits found tool output was 64% of context cost, which led to concrete output-trimming rules (field-level JSON access, `git diff --stat` first, a subagent reads big logs). Tool choices are decided by A/B evidence (for example RTK was rejected after a test).
- **Deterministic quality gates + task ledger** (task file, finalizer, indexes) instead of trusting "done" from the model.
- **Independent second opinion**: Codex reviews Claude's diffs and vice versa (generation separated from evaluation). The always-on review gate was switched off for cost, which is the right trade.
- **Human owns taste**: the operator playtests for feel; automatic logs are treated as hypotheses; tasks go to status "test" until the operator accepts.
- **Persistent memory and written rules**: feedback becomes durable memory; rules are versioned in the repo; skills hold repeatable procedures.
- **Borrowed over invented**, documented decisions, no emphasis spam in prompts.
- **Emergency-only automation**: unattended AUTO loops are a fallback, not the default, because they re-pay context every turn.

## Instructions for the receiving agent

1. Read this file fully. Do not apply everything blindly: ask the owner (one form, see below) which items fit the current environment (company policy, client NDA, repo tooling).
2. Check the environment first: language and test runner, existing `.claude/settings.json`, whether hooks are allowed by company policy, what the single "verify" command is.
3. Implement in this order (highest quality ROI first):
   1. Interview form rule + `/spec` skill (sections below).
   2. Stop hook calling the repo's fast verify command.
   3. PreToolUse guard for zero-exception rules.
   4. Trim CLAUDE.md/AGENTS.md: every line must pass "would the agent err without it?"; procedures go to skills, per-directory rules to `.claude/rules/*.md` with `paths:`.
   5. Independent review against SPEC.md in a fresh context (subagent or another model).
4. When you discover something that works (or fails), append it under "Findings log" with date, what, evidence, verdict. Keep entries short.
5. Never put secrets, client names or client code into this file.

## Implemented in the reference game project (2026-11-14)

| Item | Where | Status |
|---|---|---|
| Interview form rule | project `CLAUDE.md` section on ambiguity + memory | active |
| /spec skill | `.claude/skills/spec/SKILL.md` | created, not yet field-tested |
| Stop hook gate | the project's stop-gate script + `Stop` in `.claude/settings.json` | verified: silent when unchanged, blocks (exit 2) on broken code |
| PreToolUse guard | the project's guard script + `PreToolUse` in `.claude/settings.json` | verified on about 24 allow/block cases |
| Worktree guidance | `CLAUDE.md` (role split) | added |
| Retired-engine archive and decoupling | an archive folder plus test fixtures | done; core code no longer reads the archive |

## Interview form rule

Principle: ambiguity is resolved by ONE structured questionnaire, never by a chain of single questions.

- Trigger: the request is imprecise, has several plausible readings, or the agent is not sure what the owner means. Things discoverable from the repo are checked by the agent itself, not asked.
- Tool: `AskUserQuestion`, up to 4 questions per call, 2-4 options each, recommended option first with "(Recommended)", every option states its consequence in one sentence.
- Over 4 gaps: ask the 4 that change the implementation most; for the rest pick a sensible default and list it as "assumed" in the reply so the owner can veto.
- Large or risky tasks (over about an hour, architecture, persistence, payments, auth): run the `/spec` skill, which ends with a SPEC.md as the definition of done.
- Small fixes and throwaway scripts: no form, just do it.
- Source: official Claude Code best practices ("Interview me until you could write the spec, then write it to SPEC.md"; build in a fresh session from the spec).

## Verification harness

Core idea (official docs): giving the agent a check to run is the highest-leverage quality practice. Layer checks by cost, and make the harness (not the model's memory) enforce them.

| Tier | When | Game project (engine + pure core library) | Typical B2B repo |
|---|---|---|---|
| 0 guard | every tool call, under 1 s | PreToolUse guard (implemented) | same, plus secrets deny rules |
| 1 fast gate | end of every turn that changed code | Stop hook: unit tests of the core library, slow golden-master tests excluded (implemented) | Stop hook: unit tests + typecheck/lint for the changed area |
| 2 deep check | on demand after a feature (a `/verify`-style skill) | engine EditMode tests via the engine CLI against the already-open Editor (seconds, no cold start), or compile/console check via the engine MCP; only when no other agent is using the Editor | integration tests, build, run the app and look at it |
| 3 finalizer | before commit | finalizer script with the quality gate (exists) | CI on the PR (same command as local) |
| 4 human | after merge to "test" | operator playtest (feel); logs are hypotheses | client acceptance, staging smoke test |
| Review | after tiers 1-2 pass | fresh-context reviewer (subagent or Codex) given only diff + SPEC.md: "is every requirement implemented, do edge cases have tests; skip style" | same |

Design rules learned (sources in the research summary and findings log):
- **One `verify` entry point per repo** (script, make target or npm script). The Stop hook, CI and humans all call it, so there is a single source of truth. For B2B repos create it first, then wire the hook to it.
- **Run only when relevant files changed** and cache the passing fingerprint; otherwise the gate taxes every turn.
- **Guard against loops**: Claude Code overrides a Stop hook after 8 consecutive blocks; a hook may also read `stop_hook_active` from stdin. The reference gate keeps blocking while red (the cap protects) and exits 0 on timeouts or its own crashes, so a broken hook never traps the session.
- **Tell the agent to fix code, not tests** in the hook's stderr message. A verifier cannot tell whether the agent weakened a test, so review the test diff.
- **Use `command` hooks for enforcement**; `prompt`/`agent` hooks are model judgments and not deterministic.
- **Game-engine specifics (Unity example)**: do not pass `-quit` with `-runTests`; one process per project folder (a GUI Editor blocks batchmode); EditMode first (fast), PlayMode only for engine behavior; keep the Editor warm instead of cold-starting batchmode. Do not put the engine inside the Stop hook while two agents share one Editor.
- **Cost**: a full planner/generator/evaluator harness produced a working result in an Anthropic example at about 20x the cost of a solo run; use it for big greenfield work with a hard acceptance test, not for daily work.

Per-stack fast gate examples for B2B (use what the repo already has): .NET `dotnet test`; TypeScript `tsc --noEmit` + test runner for the changed area; Python `pytest -x` + `ruff`/`mypy`; Java `mvn -q test` / `gradle test`. Keep it under about a minute, or run the heavy part in CI and keep only a smoke subset in the hook.

## Hard rules: PreToolUse guard

Principle: CLAUDE.md is advisory (followed most of the time); a rule with zero exceptions belongs in a hook (exit 2 blocks and sends stderr to the agent) or a deny rule. Keep the set small (about 10); preferences stay in CLAUDE.md or memory. A PreToolUse exit 2 block holds even in bypass-permissions mode. Exit 1 is only a warning and does NOT block.

Rules enforced in the reference game project:
1. A retired engine: no running it, no comparison flags against it, no editing its archive tree (legacy source kept read-only; some config tests read fixtures from it).
2. Destructive git: `reset --hard`, `clean -f/-d/-x`, `checkout .` / `restore .`, `stash drop|clear`, force push, `branch -D` (other agents share the working tree with uncommitted work).
3. No whole-file dumps of the big ledger JSONs (task ledger, plan, command registry): use the field-level JSON tool, or Read with limit <= 300.
4. Secret files (`.env*` except examples, `*.pem`, `*.pfx`, `*.key`, SSH keys) are never read or edited by the agent.

For client work add: deny rules for client secrets and production configs, and a list of files that must never leave the machine (see the B2B section of the research summary).

Reference script (adapt the BIG_JSON list and rules to the repo; register under `hooks.PreToolUse` with matcher `Bash|Read|Edit|Write`). The retired-tool rules are kept as an example of a project-specific rule; replace or drop them:

```python
"""Claude Code PreToolUse hook: deterministic guard for rules that have zero exceptions.

Reads the tool call as JSON on stdin. Exit 0 = allow, exit 2 = block (stderr goes to Claude).
Rules (keep this list short; preferences belong in CLAUDE.md, not here):
  1. A retired tool: no running it, no editing its archive tree.
  2. Destructive git that would wipe other agents' uncommitted work or rewrite shared history.
  3. Whole-file dumps of the big JSON ledgers (use the field-level JSON reader instead).
  4. Secret files (.env, keys) are never read or edited by the agent.
Opt out for one session with PROJECT_GUARD=0.
"""

import json
import os
import re
import sys

BIG_JSON = ("TASKS.json", "PLAN.json", "COMMANDS.json")
SECRET_NAME = re.compile(r"^(\.env(\..+)?|.+\.(pem|pfx|key)|id_rsa|id_ed25519)$", re.IGNORECASE)
SECRET_OK = re.compile(r"\.(example|sample|template)$", re.IGNORECASE)
READ_VERBS = r"(?:cat|type|Get-Content|gc|head|tail|more|less|bat)"
CMD_START = r"(?:^|[;&|(]\s*|&&\s*|\|\|\s*)"

BASH_RULES = (
    (re.compile(CMD_START + r"(?:\"[^\"]*\"|'[^']*'|\S*[\\/])?retiredtool[\w.\-]*(?:\.exe)?\b", re.IGNORECASE),
     "The retired tool must not be run."),
    (re.compile(r"\bgit\s+reset\s+--hard\b"),
     "git reset --hard would destroy uncommitted work (other agents share this tree)."),
    (re.compile(r"\bgit\s+clean\s+-\w*[fdx]"),
     "git clean would delete untracked work."),
    (re.compile(r"\bgit\s+(?:checkout|restore)\s+(?:--\s+)?\.(?:\s|$)"),
     "Bulk checkout/restore of '.' would wipe uncommitted work."),
    (re.compile(r"\bgit\s+stash\s+(?:drop|clear)\b"),
     "Dropping stashes loses work."),
    (re.compile(r"\bgit\s+push\b[^|;&]*\s(?:--force\b|-f\b)"),
     "Force push rewrites shared history; ask the owner."),
    (re.compile(r"\bgit\s+branch\s+-D\b"),
     "Force-deleting a branch loses commits; ask the owner."),
    (re.compile(READ_VERBS + r"\s+[^|;&]*(?:" + "|".join(re.escape(n) for n in BIG_JSON) + r")\b", re.IGNORECASE),
     "Do not dump a whole ledger JSON; use the field-level JSON reader."),
    (re.compile(READ_VERBS + r"\s+[^|;&]*\.env(?:\.(?!example|sample|template)\w+)?(?:\s|$|[\"'])", re.IGNORECASE),
     "Secret files are off limits."),
)


def block(reason):
    sys.stderr.write(f"Blocked by pretool_guard: {reason}\n")
    return 2


def check_file(tool, path, tool_input):
    norm = path.replace("\\", "/")
    name = norm.rsplit("/", 1)[-1]
    if SECRET_NAME.match(name) and not SECRET_OK.search(name):
        return block(f"{name} looks like a secret file; the agent must not read or edit it.")
    if tool in ("Edit", "Write") and re.search(r"(^|/)legacy-archive/", norm):
        return block("The legacy archive is retired and read-only; do not edit it.")
    if tool == "Read" and name in BIG_JSON:
        limit = tool_input.get("limit")
        if not isinstance(limit, int) or limit > 300:
            return block(f"{name} is huge; use the field-level JSON reader or Read with limit <= 300.")
    return 0


def main():
    if os.environ.get("PROJECT_GUARD") == "0":
        return 0
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input must not trap the session
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    if tool == "Bash":
        command = tool_input.get("command", "")
        for pattern, reason in BASH_RULES:
            if pattern.search(command):
                return block(reason)
        return 0
    if tool in ("Read", "Edit", "Write"):
        path = tool_input.get("file_path", "")
        return check_file(tool, path, tool_input) if path else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

## Skill /spec

Save as `.claude/skills/spec/SKILL.md` (adjust the spec path to the repo's conventions). Invoke with `/spec <task>` or let it trigger on large or ambiguous tasks. The version below is the English translation of the original skill; run the interview in the owner's language.

```markdown
---
name: spec
description: Form-based interview before non-trivial work, ending in a SPEC.md file (goal, out of scope, acceptance criteria, edge cases, how to verify). Use on /spec or when the task is larger than about an hour of work, touches architecture, data, persistence, payments or auth, or the requirements are underspecified. Do not use for small fixes and throwaway scripts.
---

# Interview -> SPEC.md

Goal: collect the missing decisions BEFORE writing code and record them as a checkable definition of done.

## When
- Yes: task over about an hour, architecture/data/persistence/payments/auth, code that outlives the conversation, unclear requirements.
- No: typo, small fix, prototype or one-off script. Then just act.

## Steps
1. First read what the repo can tell you (code, task ledger, state file). Do not ask about what is visible.
2. List the gaps in your head: scope, edge cases, error behavior, compatibility, performance, out of scope, how to verify.
3. Ask with the AskUserQuestion tool (a form):
   - at most 4 questions at a time, 2-4 options, the recommendation first with the suffix "(Recommended)",
   - every option with a one-sentence consequence,
   - only questions whose answer changes the implementation.
   Repeat rounds until the gaps are gone (usually 1-3 rounds).
4. Write `SPEC.md` (in a client repo: `docs/specs/<name>.md`; in the project's own convention otherwise), with sections:
   - **Goal** (1-2 sentences, why),
   - **Out of scope**,
   - **Decisions** (from the interview, each with a short reason),
   - **Acceptance criteria** (testable, numbered),
   - **Edge cases** (each with the expected result),
   - **Verification** (a concrete command/test/manual step; ideally write the test before the implementation),
   - **Risks and assumptions**.
5. Show the spec in 3-6 points and ask for acceptance. Building starts after acceptance, ideally in a fresh session with SPEC.md as the only input.
6. After implementation: review in a separate context (subagent or a second model) against SPEC.md: "is every requirement done, do edge cases have tests; skip style".

## Rules
- The spec is the source of truth. When the result is wrong, fix the spec and repeat; do not patch with prompts.
- Ledger tasks: link to the spec entry, do not copy its text.
- Report results in the owner's reply profile.
```

## Stop hook

Settings entries (`.claude/settings.json`; replace the interpreter and script paths with the repo's own):

```json
"hooks": {
  "Stop": [
    { "hooks": [ { "type": "command",
      "command": "python -I -B \"$CLAUDE_PROJECT_DIR/tools/stop_gate.py\"",
      "timeout": 300 } ] }
  ],
  "PreToolUse": [
    { "matcher": "Bash|Read|Edit|Write", "hooks": [ { "type": "command",
      "command": "python -I -B \"$CLAUDE_PROJECT_DIR/tools/pretool_guard.py\"",
      "timeout": 10 } ] }
  ]
}
```

Reference script (`tools/stop_gate.py`; for another repo change WATCHED, SUFFIXES and the test command; add `.claude/.stop_gate_state` to .gitignore):

```python
"""Claude Code Stop hook: run the fast core test gate when core code changed.

Exit 0 = let the turn end. Exit 2 = block the stop and send stderr back to Claude.
Skips silently when no src/ or tests/ C# changes exist, or when the same change set
already passed. Never launches the game engine. Opt out with PROJECT_STOP_GATE=0.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[1])
STATE = ROOT / ".claude" / ".stop_gate_state"
WATCHED = ("src", "tests")
SUFFIXES = (".cs", ".csproj")
TEST_PROJECT = "tests/Core.Tests/Core.Tests.csproj"
TIMEOUT_SECONDS = 280
TAIL_LINES = 40


def changed_files():
    result = subprocess.run(
        ["git", "status", "--porcelain", "-uall", "--", *WATCHED],
        cwd=ROOT, capture_output=True, text=True, timeout=30,
    )
    paths = []
    for line in result.stdout.splitlines():
        name = line[3:].strip().strip('"')
        if " -> " in name:
            name = name.split(" -> ", 1)[1]
        if name.endswith(SUFFIXES) and (ROOT / name).is_file():
            paths.append(name)
    return sorted(paths)


def fingerprint(paths):
    digest = hashlib.sha1()
    for name in paths:
        stat = (ROOT / name).stat()
        digest.update(f"{name}|{stat.st_size}|{stat.st_mtime_ns}\n".encode())
    return digest.hexdigest()


def main():
    if os.environ.get("PROJECT_STOP_GATE") == "0":
        return 0
    try:
        sys.stdin.read()
        paths = changed_files()
        if not paths:
            return 0
        current = fingerprint(paths)
        if STATE.exists() and STATE.read_text().strip() == current:
            return 0

        run = subprocess.run(
            ["dotnet", "test", TEST_PROJECT, "--disable-build-servers", "/m:1",
             "-p:UseSharedCompilation=false", "--filter", "Category!=GoldenMaster",
             "--nologo", "-v", "q"],
            cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        sys.stderr.write("Stop gate: core tests exceeded the time limit; run the gate manually.\n")
        return 0
    except Exception as error:  # a broken hook must not trap the session
        sys.stderr.write(f"Stop gate skipped: {error}\n")
        return 0

    if run.returncode == 0:
        STATE.write_text(current)
        return 0

    tail = "\n".join((run.stdout + run.stderr).splitlines()[-TAIL_LINES:])
    sys.stderr.write(f"Core tests failed after your changes. Fix the code, not the tests, before finishing:\n{tail}\n")
    return 2


if __name__ == "__main__":
    sys.exit(main())
```

## Research summary (2026-11-14, translated)

### Verdict in one paragraph

The owner's setup is already above average (session routing, subagents on the standard tier, cost audits, memory, gates, review by a second model). The biggest gaps are not tools but **process**: (1) no "interview -> spec" phase before work, (2) verification runs only at finalization (the finalizer script), not enforced by the harness during work, (3) some hard rules sit in CLAUDE.md/AGENTS.md (advisory) although they belong in hooks/deny, (4) AGENTS.md (286 lines) + a second rules file + CLAUDE.md are a large attention cost every session, (5) the quality of AI results is not measured, only cost, (6) for B2B there is no explicit AI policy towards clients.

### Top improvements by quality ROI

**1. Interview before work (form): high ROI, low cost.**
- This is the right methodology and is officially recommended: "Interview me until you could write the spec, then write it to SPEC.md". Claude asks multiple-choice questions about the underspecified (scope, edge cases, out of scope), then builds in a **fresh session** with `SPEC.md` as the definition of done.
- The form tool exists (AskUserQuestion: 2-4 options, recommendation first). Only the rule for when to use it was missing.
- Rule to avoid being tiresome: interview only when (a) the task is over about an hour of work, (b) it touches architecture/data/payments/auth, (c) the code outlives the conversation. Small things and prototypes: no interview ("vibe" is fine for one-off scripts).
- Questions only about what cannot be learned from the repo; max 4 at a time; each with a default recommendation so the owner can just click "yes".
- Implementation: a `/spec` skill (template: goal, out of scope, acceptance criteria, edge cases, how we verify, risks) + 3 lines in CLAUDE.md. Spec Kit/Kiro are not needed; a light `SPEC.md` is enough.

**2. Verification enforced by the harness (Stop hook): high ROI.**
- Officially: "give Claude a check to run" is the strongest quality lever. A `Stop` hook with exit 2 does not let the turn end until a fast check passes (limit: 8 consecutive blocks).
- For the game project: a fast C# core gate (build + core tests, no engine) as the Stop hook; for B2B projects: typecheck + unit tests.
- Rule: for every task first decide "how we verify" (in the SPEC), ideally a test written before the implementation (an external oracle).
- Note: `prompt`/`agent` hooks are not deterministic; use `command` for enforcement.

**3. Independent review against the spec: high ROI.**
- Lesson from Anthropic harnesses: models judge their own work poorly; **generation and evaluation must be separated** (separate context, ideally another model).
- `/codex:review` and subagents already exist. Formalization: the reviewer gets only the diff and `SPEC.md` and checks "is every requirement implemented and do edge cases have tests", skipping style.
- Plan approval is not verification; review is a separate step.

**4. Hard rules to hooks/deny, soft ones stay in CLAUDE.md: medium/high ROI.**
- CLAUDE.md is advisory (compliance about 70-80% per blogs; official docs say "works most of the time, not always"). A rule with zero exceptions goes to a `PreToolUse` hook (exit 2) or a deny rule.
- Candidates: ban on running a retired tool, ban on reading whole big JSON files, ban on editing other agents' uncommitted changes, `.env`/secrets. Before this work only graph-tool hooks existed.
- Do not overdo it: about 10 hooks, not 40. Preferences (the report style) stay in memory.

**5. Slim the startup context: medium ROI.**
- Every CLAUDE.md line costs attention on every task. Test for a line: "would Claude err without it?" If not, delete it.
- AGENTS.md 286 lines + second rules file (23) + CLAUDE.md (95) + a mandatory reading list at start. Candidates: procedures -> skills (load on demand), per-directory rules -> `.claude/rules/*.md` with `paths:` frontmatter, remove duplicates across files.
- Officially one can stop writing IMPORTANT/CAPS (new models over-apply the rule) and "do not be lazy, finish it".
- An audit already exists (a rules evaluation of 2026-11-03); this point continues it.

**6. Session and context hygiene: already done, refine.**
- `/clear` between unrelated tasks; `/compact` with a focus; tool output is the biggest cost (owner audit: 64%).
- For long tasks: a context reset with a structured handoff (progress file + git log) beats compaction per Anthropic. Checkpoint/state files already do this.
- A heavy multi-agent harness (planner/generator/evaluator) was 20x more expensive (USD 9 vs 200 in the Anthropic example) and produced a working result; keep for big greenfield work, not daily use.

**7. Measure quality, not impression: medium ROI.**
- METR 2025: experienced developers were 19% slower with AI while **feeling** 20% faster. In February 2026 METR called that result outdated (speedups likely) but calls the new data unreliable (selection effects). Conclusion: do not trust the feeling.
- DORA 2025: AI is an amplifier; it improves throughput but **increases delivery instability**; only 3% of developers trust results highly. Remedy: small batches, strong version control, fast rollback, a clear AI policy.
- Proposal: a light diary, three numbers per task (passed first time Y/N, number of fixes, whether a regression appeared). After a month it shows where AI really helps.
- "Commit on every change" is exactly the DORA practice (small batches + VCS as a safety net). Keep.

**8. B2B / freelance: AI policy towards clients: high ROI (legal risk), not technical.** Not legal advice; verify with a lawyer.
- Client code usually falls under the NDA confidentiality clause. Pasting it into a consumer AI plan that trains on data is a potential breach. Consumer plans offer no DPA to sign; Team/Enterprise/API usually do and disable training by default (check the provider's current terms).
- With client personal data the AI provider is a sub-processor and must be on the client-approved list.
- For 2026 contracts: (1) disclosure of AI use, (2) ownership of the output (pure AI output without human contribution may not be copyrightable), (3) list of AI tool categories allowed with client data, (4) scope of accuracy warranties and a liability cap at the order value. Name categories ("coding assistant"), not products.
- Practice: a per-client rules file ("AI allowed: yes/no/local only"), deny rules for `.env` and secrets, a sandbox, the client's consent in writing. When a client forbids AI, an exception is usually negotiable: "no client data in the prompt + full review of the output".

### Prompt engineering: what actually works

- Say what Claude cannot see: intent, constraints, why, what was already tried, definition of done. Do not repeat what is in the code.
- One task per session; a concrete path/file/symbol; acceptance criterion and how to check it in the prompt.
- Ask for evidence instead of declarations: "show the test result", "run it and describe what you see" (`/verify`).
- Input/output examples instead of long descriptions; negative examples only when necessary.
- Underspecified things -> interview (point 1), not guessing.
- No CAPS and exclamation marks; one plain, clear rule works better.

### What NOT to do (low ROI / cost > benefit)

- More helper tools: RTK, TOON, Repomix were already judged weak; keep the decision.
- Heavy spec-driven-development frameworks for one person; `SPEC.md` is enough.
- Multi-agent loops as the default mode (cost, drift); only when the task is large and has a hard check.
- A review gate that eats limits (already off, rightly).
- Writing everything "to be safe" into CLAUDE.md.

### Proposed implementation order

1. `/spec` skill + the rule for when to ask by form (the one-hour threshold).
2. Stop hook with the fast core gate + review of 5-10 rules for hooks/deny.
3. Trim AGENTS.md/CLAUDE.md (with the audit, without losing rules).
4. An "AI policy" template for B2B contracts + per-client rules file + deny for secrets.
5. Mini quality diary (3 numbers per task).

### Research limits

Some sources are third-party blogs (CLAUDE.md compliance percentages and spec-driven-development data are estimates). Strongest: official Claude Code docs, DORA, METR. The legal aspects come from blogs, not primary sources.

### Sources

- Claude Code: Best practices (official), https://code.claude.com/docs/en/best-practices
- Anthropic: Effective context engineering for AI agents, https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
- ZenML: Anthropic long-running agent harness, https://www.zenml.io/llmops-database/long-running-agent-harness-for-multi-context-software-development
- Claude Code hooks/subagents 2026 (creeta), https://news.creeta.com/en/claude-code-hooks-subagents-best-practices-2026/
- Advanced Claude Code tips 2026 (saascity), https://saascity.io/blog/advanced-claude-code-tips-2026
- SDD vs vibe coding (DEV), https://dev.to/datalaria/sdd-spec-driven-development-vs-vibe-coding-engineering-robust-software-with-ai-in-2026-1gcj
- METR: experiment design change (2026-02), https://metr.substack.com/p/2026-02-24-uplift-update
- DORA 2025: State of AI-assisted Software Development, https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf
- DORA AI Capabilities Model, https://services.google.com/fh/files/misc/2025_dora_ai_capabilities_model.pdf
- Anti-AI contract clauses 2026, https://delivvo.io/blog/anti-ai-contract-clauses-freelancers-2026
- Client data in AI tools / contractual breach, https://sonomos.ai/blog/client-contracts-ai-confidentiality-2026/
- AI Coding Tools and Client NDAs, https://heyeduardo.app/blog/developer-ai-privacy-guide-2026

## Findings log

- 2026-11-14: Research done. Official best-practices page: interview-first, Stop hook for verification, hooks over CLAUDE.md for zero-exception rules, drop IMPORTANT/CAPS. Verdict: adopt. Implemented /spec, Stop gate, PreToolUse guard, interview form rule.
- 2026-11-14: Hook gotchas confirmed by several write-ups: a Stop hook needs a loop guard (8-block cap, optionally `stop_hook_active`); exit 1 does not block, only exit 2 does; PreToolUse deny holds in bypass mode; hooks need timeouts and must never crash the session. Test hooks by piping sample JSON to the script (allow and block cases). Verdict: applied.
- 2026-11-14: Testing tip for Windows shells: build hook payloads with a real JSON serializer (json.dumps), not hand-typed strings; backslashes in paths get mangled by shell quoting and give false "allow" results.
- 2026-11-14: Game-engine agent verification: the engine CLI's EditMode test run against an open Editor returns results in seconds (a dedicated exit code means tests ran but failed); classic batchmode needs `-runTests` without `-quit`. Verdict: candidate for a tier 2 `/verify` skill; not implemented (the Editor is shared with Codex).
- 2026-11-14: Decision on `.claude/rules/` with `paths:`: skipped for now. CLAUDE.md is 107 lines (docs advise under 200) and AGENTS.md (278 lines, 29.7 KB) is shared with Codex, which ignores `.claude/rules/`. Revisit if CLAUDE.md passes about 200 lines or a client repo grows language-specific rules. `/doctor` (CLAUDE.md trim proposals) is interactive: run it by hand when needed.
- 2026-11-14: Added `claude --worktree <name>` guidance to CLAUDE.md (parallel Claude session without touching the tree shared with Codex).
- 2026-11-14: PARKED PROPOSAL, local side agent (owner has no free disk now, nothing installed). Goal: manual chat agent for trivial tasks (summarise logs, quick existence research, commit when Claude is down). Stack: Ollama + Qwen3-Coder-30B-A3B (about 18 GB, approximate) or gpt-oss-20b (about 13 GB); run through Claude Code (ANTHROPIC_BASE_URL to Ollama) or `codex --oss` so CLAUDE.md and the pretool guard still apply. Internet needs an MCP tool (fetch or search server, SearXNG, or Ollama web search API; limits unchecked); a skill only teaches usage. Built-in WebSearch/WebFetch likely do not work with a local model. Expect slow prefill on an 8 GB GPU + 32 GB RAM. First test when disk allows: measure speed, summarise a real log, dry-run a commit without push.
- 2026-11-14: Open items: field-test /spec on a real task; trim AGENTS.md further (29.7 of 32 KB); B2B AI-policy contract template (not legal advice); quality diary (3 numbers per task); tier 2 `/verify` skill for the game engine; the parked local agent above; remaining cleanup of a retired engine's references (shared docs, flow registry text, zip and remove the archive folder) is handled in another session.
- 2026-11-14: Social-media feature lists ("Claude Code iceberg", 30 terms). Triage method: check each term against the official features-overview and common-workflows docs, then classify as already used / adopt / hype. Verdict for this owner:
  - Already used: CLAUDE.md, skills (/spec, codex-handoff), MCP (game engine, Serena), hooks incl. PreToolUse and Stop, subagents (standard tier default), plugin (codex), auto memory, plan mode, compaction override.
  - Adopt (cheap, real value): `.claude/rules/*.md` with `paths:` frontmatter to move engine/C# or core-only rules out of the always-loaded CLAUDE.md; `claude --worktree <name>` for a parallel session that must not touch the shared tree; `claude -p` for scripted checks (e.g. a client-repo `verify` run in CI); `/doctor` to get trim proposals for an oversized CLAUDE.md; a code-intelligence plugin (LSP) for C# only if Serena proves insufficient.
  - Low ROI now: output styles and status line (cosmetic; the reply profile already lives in memory), own plugin marketplace (only worth it once a second repo or a team needs the same setup), GitHub Actions (only for B2B repos that have CI), Agent SDK and own MCP server (only when a concrete product needs them).
  - Experimental or situational, do not build habits on them: agent teams, dynamic workflows (many parallel subagents; cost scales with fan-out, the shared working tree with Codex makes parallel writers risky), channels (research preview), `--bare`.
  - Rule of thumb from the docs: add a feature when a recognisable trigger appears (same mistake twice, same prompt three times), not because a list says so.
- 2026-11-14: Local models ("billions of tokens of context in 10 GB RAM"). Verdict: hype for coding work. Quoted context sizes are architectural or marketing maxima; KV-cache memory grows with context, and needle-in-haystack results do not predict reasoning quality over long inputs. Realistic: 128K-256K usable context. Owner hardware (8 GB VRAM GPU, 32 GB RAM, no local runtime installed) fits at most a 20-30B mixture-of-experts model with CPU offload: slow, no project knowledge, clearly weaker than the cloud agents. Possible niche: free side agent for bulk mechanical work or data that must not leave the machine (client NDA code), via Ollama or LM Studio with Claude Code or `codex --oss`. Not adopted; trial only if a concrete bulk or privacy task appears. Benchmarks seen were vendor or blog numbers, unverified.
- 2026-11-14: Rules and tools audit. A full tools audit already existed (three audit files, 25+ findings each, incl. the rules layer); this pass did not redo it, it fixed the contradictions in the files this workflow owns. Fixed: (1) report-format conflict between AGENTS.md (Codex: four sections, no list emoji, status header) and CLAUDE.md (Claude: ultra-short profile): CLAUDE.md now states AGENTS.md formats apply to Codex and Claude follows its own reply section; (2) AGENTS.md "checkpoint-commit existing changes" contradicted CLAUDE.md "do not touch others' uncommitted work": now own paths only; (3) CLAUDE.md pointed at a non-existent checkpoint file: now conditional; (4) CLAUDE.md said the high tier "usually stays in the router" and also "router runs on the standard tier": unified; (5) AGENTS.md quality-gate commands used `python3`, which is only a Windows Store stub on that machine: now the project's bundled interpreter; (6) leftover wording about a retired engine removed from AGENTS.md; (7) `/spec` wrote non-English specs into a repo whose rule requires English: now English specs, interview in the owner's language. Added a test file for the pretool guard (6 tests; the audit flagged hooks as untested).
- 2026-11-14: Still open from audits (owner decisions, not touched): which start-of-session reads are authoritative (bootstrap vs state file vs workflow registry, audit C item 1); Codex default model tier (item 5); AUTO as main vs emergency mode (item 7); finalizer tooling profile red because of a watchdog test (audit A item 1); remaining retired-engine text in several registries (handled in the cleanup session). Best-practice yardstick used: instructions advisory, hooks deterministic; one owner per rule; no rule that cannot be satisfied together with another; every referenced file must exist.
- 2026-11-14: Owner decisions on audit conflicts. (1) Session start: read the state JSON plus one small index, a directives file ("about to do X -> rule Y applies"), kept in context by every agent; the heavy pipeline bootstrap and workflow registries are loaded only for project commands and document/JSON edits. Rationale: a short always-in-context pointer list is cheap; loading every rule up front is not, and long instruction files are followed less reliably. Applied in AGENTS.md, CLAUDE.md and the workflow registry. (2) AUTO is deprecated (it compensated for Codex not taking queue tasks one per prompt); bannered in AGENTS.md and the AUTO contract. (3) Model routing researched and written once: `model_tiers` in a routing JSON plus a routing guide; Codex workers now on the standard tier, the parent on the high tier; other docs point to the single source.
- 2026-11-14: Model routing research summary (sources: Morph planner+executor benchmark https://www.morphllm.com/multi-agent-model-routing, AgentPatterns cost-aware design https://agentpatterns.ai/token-engineering/cost-aware-agent-design/, CallSphere escalation https://callsphere.ai/blog/cost-aware-agent-orchestration-routing-cheap-expensive-llms-2026, Zylos https://zylos.ai/research/2026-05-06-ai-agent-multi-model-orchestration-runtime-selection/, HeyBento https://heybento.ai/blog/frontier-model-orchestrator). Consensus: the expensive model plans once, cheaper models execute, a cheap deterministic gate (tests, analyzers) decides escalation; use aliases not pinned IDs; cap tokens, steps and time per agent; watch the share of top-tier calls (about 15 percent is a warning sign); orchestration itself can cost 2-3x a single agent, so default to one agent and delegate only with a concrete advantage. Caveat: figures are vendor or blog numbers; one terminal-agent study found planner/executor gave only modest gains with weak models. Verdict: applied as described above; measure real cost per task before tuning further.
- 2026-11-14: Routing made operational. A dedicated machine-readable file (tiers, principles, escalation); the Codex bridge now builds its model choice from it, Claude gets tier agents `.claude/agents/{scout,implementer,planner,reviewer}.md` (frontmatter `model` outranks the `CLAUDE_CODE_SUBAGENT_MODEL` env per the sub-agents docs, so the env stays as the default for unclassified subagents), and a test fails if any agent definition or Codex profile drifts from the file. Portable lesson: put model choice in one machine-readable file, derive or test every consumer against it, and use frontmatter agents so delegation picks the tier by role instead of by remembering a flag.
- 2026-11-14: Owner decisions round 3. Language: source code 100% English (identifiers, comments, runtime strings, logs); documentation and owner talk in the owner's language. Commits: finish at the end of the prompt with the finalizer script restricted to own paths; format and squash rules live in a commit-rules doc; a squash script joins adjacent unpushed same-domain commits on a dirty tree via `git commit-tree` + `update-ref` and verifies the tree is unchanged. Tools: field-level JSON read/edit tools first, document tools only as fallback; docs in JSON, Markdown only for owner-edited free-form files. Mechanical text damage in rules fixed. Finalizer randomness: root cause is brief file locks from Dropbox/GoogleDriveFS/Defender/SearchIndexer making `os.replace` raise `PermissionError` (WinError 5); fixed with a retry helper. General lesson for any Windows project in cloud-synced folders: wrap atomic replaces in retry-with-backoff. AGENTS.md slimming is a proposal in a separate doc.
- 2026-11-14: Correction on AUTO: not fully deprecated. It stays as a Codex fallback script for when the Claude usage limit runs out and tasks remain; agents never start or propose it, only the owner types the command. Rule wording and machinery are kept.
- 2026-11-16: Compared our workflow with a "router picks model + effort, verify by risk, escalate, learned feedback" diagram. Matches: rule-based router (routing JSON), escalation on evidence. Gaps: effort fixed per agent role, verification depth by judgement, no feedback from outcomes to routing. Designed both missing parts (risk score from diff -> LIGHT/STANDARD/FULL; routing log + weekly stats -> routing proposals, owner approval only); see `ROUTER-LOOP.md`. Also wrote a short inventory for rebuilding the setup on a bare Claude (`IMPROVEMENTS.json`). Verdict at the time: design only; later the same day steps 1, 2 and 4 were implemented in report-only mode.
- 2026-11-16: One global core instead of a copy per project. Checked two outside methods: ICM (numbered stage folders, each with a small context contract) and the Open Knowledge Format (markdown notes with YAML frontmatter, an index file and a log). Most of it was already in place (index files, directives, an append-only findings log); adopted frontmatter on rule documents and a stage-contract template. The real gain came from layering: always-loaded core rules, a private gitignored owner profile, per-project INDEX/AGENTS/CLAUDE files with overrides, and the old framework behind a per-project flag. The installer generates the Claude entry file with `@imports` (Claude reads imports) and the Codex entry file by concatenation (Codex has none), links skills and agents as directory junctions (no admin rights on Windows), deep-merges settings, and reinstalls itself from a post-merge hook, so `git pull` updates every machine. Lessons: (1) an embedded framework copy in a child project drifts both ways; the child had generic fixes (retrying atomic writes, clearer JSON errors) that the upstream lacked, so diff both directions before retiring a copy; (2) a tool that finds its package by its own file path changes behavior when it is run from a shared location, so detaching a project needs a path review, not just a find-and-replace; (3) a public repo needs the private names kept outside it: the leak check reads its patterns from the ignored local folder and runs as a pre-push hook.
- 2026-11-16: Self-improving skills. Sources: ACE paper (Agentic Context Engineering, https://arxiv.org/abs/2510.04618, code https://github.com/ace-agent/ace), community reflect tools (https://github.com/BayramAnnakov/claude-reflect, https://github.com/haddock-development/claude-reflect-system), learnings-loop write-ups (MindStudio, developersdigest). Consensus: capture corrections, then distil them into the skill; separate reflection from curation; apply incremental delta edits (whole rewrites erode details: "context collapse"); dedupe and count repeats; cap and prune the learned section; keep skills in git and review diffs before trusting auto mode. Built: `modules/tools/scripts/skill_learn.py` (one-line capture into `LEARNINGS.jsonl` next to the skill, deterministic merge of similar notes with a counter, READY when 3+ open problems or a correction repeated twice; rejected ideas absorb repeats instead of returning) and skill `skill-reflect` (only READY skills, fix the causing step first, else one bullet in `## Learned` capped at 8, one owner form, close entries). Token cost: zero per session unless something goes wrong (one short command); the log is never loaded with the skill; reflect reads only READY skills. Not adopted: Stop-hook auto-reflect after every session (pays an LLM pass each session and edits without review) and self-scoring auto mode. Verdict: adopted with human gate; check after a month whether entries actually arrive (agents may forget to log; then add a deterministic capture hook).
- 2026-11-16: Legacy flows/workflow audit plus outside research (subagents). Kept as value: per-task-type flows, research gate, closure evidence, file-based handoff, project profile, frozen layers, decision records. Evidence (measured): more rules at once lower instruction-following (arXiv 2507.11538); context files did not raise task success and cost over 20 percent more (arXiv 2602.11988); models cannot self-correct without external feedback (arXiv 2310.01798); duplication up and refactoring down in AI-era code (GitClear, correlational); multi-agent costs about 15x tokens and fits wide read-heavy work (Anthropic). Vendor guidance: JSON progress files and fresh sessions for long work. No evidence found for: borrow-before-invent, code-as-narrative, decision records for AI work, emoji for ADHD readers (only a small dyslexia study). Verdict: kept as owner preferences (read-like-a-book, emoji on every line, frozen layers, domain invariants). Open follow-ups: audit always-loaded text for rules the agent could learn from code, and turn must-always rules into hooks.
- 2026-11-20: Flow panel showed no dots for a background sub-agent while the main loop waited (only tool calls set a node as running; a background Agent call returns at once). Another session fixed it first: the spawn keeps the node running until BG_IDLE_MS after the agent's last turn, and it survives a new prompt. My parallel fix (counting agent turns) was dropped as redundant. Lesson: before editing a shared mod, `git fetch` and read new remote commits. Verdict: applied (other session's version); not verified live.
