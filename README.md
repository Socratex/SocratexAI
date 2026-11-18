# 🧭 SocratexAI

One global AI core for **Claude Code** and **Codex**: shared rules, reply style, model routing, risk scoring, tier agents, skills (with a self-improving loop), hooks and tools. Clone it once per machine. Every project then gets the same behavior by default, and a `git pull` updates all of them.

## 🎯 What it is, and what it is not

A small rule core, not a framework. Total always-loaded text is about 19 KB (a test fails above 20 KB). Everything else loads only when a task needs it.

**What you get**
- One shared source of rules for Claude Code and Codex.
- A guard hook that blocks destructive git, secret-file reads and whole-file dumps of big ledgers. Fail-closed, covered by tests.
- Model routing with escalation on evidence (a failed gate or a BLOCKED report moves work one tier up), a risk score for each diff, and an outcome log.
- Five shared skills, tier agents, and a loop that turns logged corrections into reviewed skill edits.
- An installer that asks first and backs up your config before touching it.

**What you do not get**
- Not a full process kit. The task flows are short tables, not long skills. If you want enforced TDD, a long debugging method or many playbooks, [superpowers](https://github.com/obra/superpowers) and [pstack](https://github.com/backnotprop/pstack) go much deeper.
- Process rules are text the model follows. Only the guard is enforced by a hook.
- Only Claude Code and Codex are supported. Cursor, Gemini, OpenCode and others are not.
- Needs Python 3 for the installer and tools (CI runs 3.12 on Linux and Windows; the minimum version is not verified). Node is not needed, except for the optional flow-panel mod.
- Young and small: one author, history from 2026-11, no benchmarks showing it beats other setups. The routing loop and risk score are report-only and have little real data yet.
- Some defaults are the author's taste (emoji reply style, Polish profile example). The reply style is optional at install; language and name live in your own `local/profile.md`.

**Compared with others** (read from pinned clones on 2026-11-18, details in `docs/AUDIT-pstack-ecc.md`): smaller startup than ECC and gstack, a stronger guard than superpowers and pstack (they ship none), and a measured routing loop none of the files we read had. Behind them in process depth, test volume, and supported tools.

## 🧳 Use only part of it

The pieces are plain files, so you can take only what you need:
- **Rules only:** copy `core/RULES.md` and `core/rules/` into your own agent instructions. No Python needed.
- **Skills only:** `skills/<name>/SKILL.md` are standard skill folders. We only tested them in Claude Code and Codex; other agents that read this format should work but are untested.
- **Guard only:** `claude/hooks/guard.py` is one stdlib-only Python file for the Claude Code `PreToolUse` hook.
- A separate "rules and skills only" installer mode does not exist yet.

## 🚀 Install

```bash
git clone https://github.com/Socratex/SocratexAI.git ~/SocratexAI
python ~/SocratexAI/tools/install.py
```

## 🙋 What it changes on your machine

Nothing happens before you answer. The installer asks, shows the reason for each question, and Enter takes the recommended answer. Your answers are saved in `local/install.json` (gitignored); `--sync` and the post-pull hook reuse them and never ask or widen anything.

| Question | Recommended | Why it exists |
|---|---|---|
| Config folders | auto-detected (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`, else `~/.claude`, `~/.codex`) | non-default layouts just work |
| Claude Code / Codex | whatever is detected | each side is optional |
| Merge into `settings.json` | yes | installs the guard hook and secret deny rules; without it the guard is **not** active |
| Codex plugin in Claude | only if Codex is present | adds `/codex:review` and `/codex:rescue` |
| Flow panel mod | no | optional local usage view |
| UCE reply style | yes (a personal style, say no for neutral replies) | very short, emoji-led replies |
| Git hooks, `SOCRATEX_HOME` variable | yes | auto-sync after pull, leak scan before push |

```bash
python tools/install.py --yes           # no questions, recommended answers (for scripts)
python tools/install.py --reconfigure   # ask again
```

The installer is idempotent. It backs up your current agent config first (`~/claude-backup/`), then (for the parts you accepted):

| Target | What it gets |
|---|---|
| `~/.claude/CLAUDE.md` | managed block importing `core/RULES.md`, `core/STYLE.md`, `claude/CLAUDE.md`, `local/profile.md` (your own text outside the block stays) |
| `~/.claude/settings.json` | deep merge of `claude/settings.json`: guard hook, deny rules for secrets, `SOCRATEX_HOME` env |
| `~/.claude/agents`, `~/.claude/skills/<name>` | links to `claude/agents`, `skills/`, `claude/skills/` |
| `~/.claude/INDEX.json` | entry pointing at this repo's `INDEX.json` (other indexes kept) |
| `~/.codex/AGENTS.md` | generated from the same core rules + `codex/AGENTS.md` + `local/profile.md` |
| `~/.codex/agents/socratex_*.toml` | agent profiles generated from `core/ROUTING.json` |
| `~/.codex/skills/<name>` | links to the shared `skills/` |
| `SOCRATEX_HOME` | user environment variable and Codex shell environment |
| `.git/hooks` | `post-merge` reruns `install.py --sync` after every pull; `pre-push` runs the leak check |

```bash
python tools/install.py --check   # what is missing or stale, changes nothing
python tools/install.py --sync    # regenerate (the post-merge hook does this)
python tools/backup.py --list     # config backups; --restore <zip> to roll back
```

## 📚 Reference packs

`subrepos.json` lists 15 read-only agent toolkits (superpowers, pstack, ECC, anthropics/skills, spec-kit, BMAD, awesome lists, ...) with a category and a pinned commit each. They are **not in this repo**: the install asks whether to download them, and they land in `~/ai-refs` (or the folder you choose). They are never installed, linked or run. When SocratexAI lacks a capability, the agent searches them and only suggests a match; their text is treated as third-party data. The guard blocks edits inside that folder, and because it is outside the repo no agent loads their instructions as nested project rules.

```bash
python tools/update.py self    # git pull --ff-only in SocratexAI
python tools/update.py refs    # download/checkout the pinned commits (one try per pack, errors listed, exit 1 on any)
python tools/subrepos.py bump <name>        # show upstream changes since the pin, move the pin only after your yes
python tools/subrepos.py search --cat gamedev game design   # filler words ignored; name/description outrank body text
```

Pins live in the tracked `subrepos.json`, so another machine gets the same versions. `--sync` and the post-pull hook never touch the packs.

## 🧱 Layers

1. **Core** (`core/`): always loaded. `RULES.md` (epistemics, ambiguity, work loop, context economy, routing, safety, finishing), `STYLE.md` (reply profile), `DIRECTIVES.json` (situation -> rule document), on-demand rules in `core/rules/`, `ROUTING.json`, `RISK-RULES.json`, templates.
2. **Local** (`local/`, gitignored): your language, name, machine paths and private leak patterns. Created from `local.example/` on install.
3. **Project**: each project keeps its own `INDEX.json`, `AGENTS.md`, `CLAUDE.md` and optional `.ai/` overrides (`guard.json`, `RISK-RULES.json`, `ROUTING.json`). No copy of SocratexAI inside projects. Start from `templates/project/`.

Project rules win over the core, except safety rules, which projects can only make stricter.

## 🧰 Tools

| Tool | Purpose |
|---|---|
| `tools/risk_score.py` | 0-10 risk score of the current diff -> model tier and effort (`core/RISK-RULES.json`, project override `.ai/RISK-RULES.json`) |
| `tools/routing_log.py`, `tools/routing_stats.py` | log routing outcomes per project and propose rule tuning |
| `tools/json_read.py` | read one key or search a big JSON file without loading it whole |
| `tools/skill_learn.py` | log a correction or failure next to a skill (`LEARNINGS.jsonl`); merges repeats, marks a skill READY for `skill-reflect` |
| `tools/improvements_check.py` | list ledger items whose `verify` command fails on this machine (report only) |
| `tools/backup.py` | zip and restore global agent config (never credential files) |
| `tools/build_index.py` | regenerate `INDEX.json`; `--check` in CI |
| `tools/check_leaks.py` | block private paths, tokens and local patterns before a push |
| `claude/hooks/guard.py` | PreToolUse guard: destructive git, secrets, project big files and read-only folders |

## 🧩 Agents and skills

- **Tier agents** (`claude/agents/`): `scout` (cheap search), `implementer` (execution from a spec), `planner` (plans, read-only), `reviewer` (independent review; a finding is CONFIRMED only when reproduced). Codex gets matching profiles generated from `core/ROUTING.json`.
- **Shared skills** (`skills/`): `spec` (one-form interview ending in `SPEC.md`), `memory-review` (monthly clean-up), `skill-reflect` (turns logged learnings into owner-approved edits of `SKILL.md`), `token-efficient-code`, `gpt-share-read`.
- **Claude-only skill** (`claude/skills/`): `usage-optimize` (token and cost analysis with `prompt-analytics`).
- **On-demand rules** (`core/rules/`): code style, commits, review, ROI, routing, safety, security review (business projects only), task gating.

## 📚 Docs

- `docs/AI-PRACTICES.md`: findings about working with AI agents (what helped, what failed, why).
- `docs/IMPROVEMENTS.json`: one ledger of every idea we weighed. Each item has a `status` (adopted, rejected, considering), the promise (`expected_result`), our verdict (`result`) and proof (`result_evidence`, `own:` = measured by us). Check it before proposing a plugin or tool again.
- `docs/AUDIT-pstack-ecc.md`: why we borrow ideas from pstack and ECC but install neither.
- `docs/ROUTER-LOOP.md`: the measure -> route -> learn loop for model choice.
- `docs/SETUP-NOTES.md`: machine setup notes.

## 🔒 Privacy

Everything that names you, your machine or private projects belongs in `local/`. The pre-push hook runs `tools/check_leaks.py`, which blocks user-profile paths, tokens and every pattern in `local/sensitive-patterns.txt`.

## 📄 License

See `LICENSE` and `NOTICE`.
