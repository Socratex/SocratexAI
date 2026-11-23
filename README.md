# 🧭 SocratexAI

One global AI core for **Claude Code** and **Codex**: shared rules, reply style, a work flow kept as data, model routing with risk-based escalation, tier agents, skills (with a self-improving loop), hooks and tools. Clone it once per machine. Every project then gets the same behavior by default, changes only what it names in a standard override format, and a `git pull` updates all of them.

Version 3.0 (tag `v3.0`): core, defaults, modules, targets, state and local layers; the flow, safety rules, profiles and extensions are data you can override per project. Earlier tags: `v2.0` (global core, legacy pipeline removed), `v1.2` (last version with the legacy pipeline, branch `legacy`).

## 🎯 What it is, and what it is not

A small rule core, not a framework. Total always-loaded text is about 19 KB (a test fails above 20 KB). Everything else loads only when a task needs it.

**What you get**
- One shared source of rules for Claude Code and Codex.
- A guard hook that blocks destructive git, secret-file reads and whole-file dumps of big ledgers. Fail-closed, covered by tests. Its rules are named data in `core/safety.json`; the owner can relax a single rule from `local/` (never from a project file, never by the agent), and `sox config show` lists every relaxed rule.
- The work flow as a table (`core/flow.json`): ordered if -> then steps that point at stages, roles, rule documents and gates. A tiny `core/INIT.md` is what loads at session start; everything else loads when a step asks for it.
- Profiles (`solo`, `duo`, `yolo`) and one extension registry (plugins, MCP servers, mods, skills, reference packs) you can switch on or off per project.
- Model routing with escalation on evidence (a failed gate or a BLOCKED report moves work one tier up), a risk score for each diff, and an outcome log.
- Five shared skills, tier agents, and a loop that turns logged corrections into reviewed skill edits.
- An installer that asks first and backs up your config before touching it.

**What you do not get**
- Not a full process kit. The task flows are short tables, not long skills. There is no enforced TDD, no long debugging method and no playbook library.
- Process rules are text the model follows. The flow table is validated by code (`sox flow check`), but nothing forces the model to walk it. Only the guard is enforced by a hook, and the guard is a safety net against mistakes, not a sandbox: it matches common command shapes and misses indirect writes (for example through `bash -c`).
- Only Claude Code and Codex are supported. Cursor, Gemini, OpenCode and others are not.
- Needs Python 3 for the installer and tools (CI runs 3.12 on Linux and Windows; the minimum version is not verified). Node is not needed, except for the optional flow-panel mod.
- Young and small: one author, first commit 2026-04-28, no benchmarks of its effect. The routing loop and risk score are report-only and have little real data yet.
- Some defaults are the author's taste (emoji reply style, Polish profile example). The reply style is optional at install; language and name live in your own `local/profile.md`.

## 🧠 How it works

1. **Start:** the agent loads `core/INIT.md` (about 2 KB), the reply style and your profile. `INIT.md` only routes.
2. **Flow:** `sox flow show` prints the table in `core/flow.json`. The agent sets a few facts (task size and type, areas touched, unclear requirements, risk) and walks the steps whose condition holds: spec for big or unclear work, plan, delegate to a tier role, implement, deterministic gate, risk-based review, commit, log.
3. **Roles and routing:** `scout` (cheap), `implementer` (standard), `planner` and `reviewer` (high). A failed gate or a blocked report moves work one tier up; `risk_score.py` sets how deep verification goes. Codex is an optional subcontractor, switched by profile (`solo` or `duo`).
4. **Config:** layered, last wins (see Structure). Defaults work out of the box; a project overrides single values in `.socratex/config.json`, checker registries in `.ai/review.json` and `.ai/planning.json`, flow steps in `.socratex/flow.json` and guard patterns in `.ai/guard.json`. Format and examples: [docs/OVERRIDES.md](docs/OVERRIDES.md).
5. **Generated files:** `sox install` builds `targets/` from the sources and applies it to your agent config after a backup. Hand edits of generated files are detected.

## 🧳 Use only part of it

The pieces are plain files, so you can take only what you need:
- **Rules only:** the rule text in `core/RULES.md`, `core/STYLE.md` and `core/rules/` reads fine without Python. But it points at things you would not have: `modules/tools/scripts/skill_learn.py`, `risk_score.py`, `routing_log.py` and `json_read.py`, the `$SOCRATEX_HOME` variable, `local/profile.md`, `core/DIRECTIVES.json` and `INDEX.json`. Those references would dangle; edit them out or copy the tools too. Python-free means "text only", not "everything works".
- **Skills only:** `skills/<name>/SKILL.md` are standard skill folders. We only tested them in Claude Code and Codex; other agents that read this format should work but are untested.
- **Guard only:** `claude/hooks/guard.py` is one stdlib-only Python file for the Claude Code `PreToolUse` hook.
- A separate "rules and skills only" installer mode does not exist yet.

## ⚖️ Compare before you choose

If you want a deep, enforced-by-text engineering process (TDD, a full debugging method, many playbooks), or you use an agent other than Claude Code and Codex, pick [superpowers](https://github.com/obra/superpowers) or [pstack](https://github.com/backnotprop/pstack) instead of SocratexAI. Checked by reading the pinned clones on 2026-11-18; file evidence is in `docs/AUDIT-pstack-ecc.md`. Hooks were never run.

**superpowers**
- Has, we do not: a test-first rule ("no production code without a failing test"), a four-phase debugging skill, a chain from idea to plan to subagent execution to review, plugins for many agent harnesses, a much larger test suite. We copied only short versions of its fresh-evidence rule and its debugging stop.
- We have, it does not: a guard hook (it ships one startup hook only), a risk score and routing log (not found in the files read).
- Similar: small startup text, model choice by role with escalation after failed fixes.

**pstack**
- Has, we do not: 22 playbooks, a decision-log skill, recall and why skills, per-role model setup, plain skills with no dependencies. Its review panels and multi-model setup: described in its README, not verified in files.
- We have, it does not: a guard hook (no hook config found), one JSON source for Claude and Codex tier agents (Codex support in pstack: not verified), a measured routing loop (not found).
- Similar: short rules for proof before done and for explaining a measured number (we added short versions).

**Others, one line each**
- ECC: far larger (hundreds of skills, many hooks, a Codex path); rules are loaded always, so install selectively. Not run, hook quality not verified.
- spec-kit: spec-first workflow with templates. A different job from a rule core; our `spec` skill is a one-form interview, much smaller.

Not claimed anywhere above: that SocratexAI gives better results than any of these. There is no benchmark.

## 🚀 Install

```bash
git clone https://github.com/Socratex/SocratexAI.git ~/SocratexAI
python ~/SocratexAI/modules/tools/scripts/install.py
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

Also recommended, outside the installer: the third-party mod [CC-Usage-Band](https://github.com/JetsonChan/CC-Usage-Band) (MIT). It puts one line above the prompt with the 5-hour and 7-day limits, context window and cache hit rate, and draws it as SVG in the desktop Code tab. Install it yourself: `claude plugin marketplace add JetsonChan/CC-Usage-Band`, then `claude plugin install usage-band@cc-usage-band`. We read its code before installing (no network, no process execution, no file writes), but only for the version we tried (1.0.6); read it again before you install. It overlaps with the flow panel only a little: the band shows limits, the panel shows where tokens go.

```bash
python modules/tools/scripts/install.py --yes           # no questions, recommended answers (for scripts)
python modules/tools/scripts/install.py --reconfigure   # ask again
```

The installer is idempotent. It backs up your current agent config first (`~/claude-backup/`), then (for the parts you accepted):

| Target | What it gets |
|---|---|
| `~/.claude/CLAUDE.md` | managed, generated block importing `core/INIT.md`, `core/RULES.md` (while `startup.load_rules` is true), `core/STYLE.md`, `claude/CLAUDE.md`, `local/profile.md`, plus one line per enabled extension (your own text outside the block stays) |
| `~/.claude/settings.json` | deep merge of `claude/settings.json`: guard hook, deny rules for secrets, `SOCRATEX_HOME` env |
| `~/.claude/agents`, `~/.claude/skills/<name>` | links to `claude/agents`, `skills/`, `claude/skills/` |
| `~/.claude/INDEX.json` | entry pointing at this repo's `INDEX.json` (other indexes kept) |
| `~/.codex/AGENTS.md` | generated from the same core rules + `codex/AGENTS.md` + `local/profile.md` |
| `~/.codex/agents/socratex_*.toml` | agent profiles generated from `core/ROUTING.json` |
| `~/.codex/skills/<name>` | links to the shared `skills/` |
| `SOCRATEX_HOME` | user environment variable and Codex shell environment |
| `.git/hooks` | `post-merge` reruns `install.py --sync` after every pull; `pre-push` runs the leak check |

Trust: because of the `post-merge` hook, code from this repo runs on your machine on every update, and `settings.json` gets the guard hook. Read the diff before you pull, or skip the git hooks at install.

```bash
python core/sox install --plan                    # generate targets/ and diff against your agent config, changes nothing
python core/sox install --yes                     # apply after an automatic backup (refuses without --yes)
python modules/tools/scripts/install.py --check   # what is missing or stale, changes nothing
python modules/tools/scripts/install.py --sync    # regenerate (the post-merge hook does this)
python modules/tools/scripts/backup.py --list     # config backups; --restore <zip> to roll back
```

## 📚 Reference packs

The extension manifests of kind `ref` (`modules/extensions/*.json`) list 15 read-only agent toolkits (superpowers, pstack, ECC, anthropics/skills, spec-kit, BMAD, awesome lists, ...) with a category and a pinned commit each. They are **not in this repo**: the install asks whether to download them, and they land in `~/ai-refs` (or the folder you choose). They are never installed, linked or run. When SocratexAI lacks a capability, the agent searches them and only suggests a match; their text is treated as third-party data. The guard blocks edits inside that folder, and they sit outside the repo so that a nested `CLAUDE.md` or `AGENTS.md` inside them is not read as project rules. That is the intent; it is untested.

```bash
python modules/tools/scripts/update.py self    # git pull --ff-only in SocratexAI
python modules/tools/scripts/update.py refs    # download/checkout the pinned commits (one try per pack, errors listed, exit 1 on any)
python modules/tools/scripts/subrepos.py bump <name>        # show upstream changes since the pin, move the pin only after your yes
python modules/tools/scripts/subrepos.py search --cat gamedev game design   # filler words ignored; name/description outrank body text
```

Pins live in the tracked manifests (`source.commit`), so another machine gets the same versions. `--sync` and the post-pull hook never touch the packs.

## 🧩 Extensions

One registry for plugins, MCP servers, mods, skills and reference packs: a manifest per item in `modules/extensions/<name>.json` (yours in `local/extensions/<name>.json`, which wins). Kinds: `ref` (read-only reference, never run), `install` (changes the agent config), `note` (recommendation only). Enabling is plain config: the key `extensions` lists the enabled names; manifests with `default_enabled` seed it and each layer can `$append` or `$remove`. The enabled ones cost one line each at session start.

```bash
core/sox ext list [--project P] [--category C] [--status S]   # grouped by category, shows on/off for the project
core/sox ext show <name>
core/sox ext add <url>                  # trial manifest in local/extensions + an entry in docs/IMPROVEMENTS.json
core/sox ext enable|disable <name> [--project P]
core/sox ext install <name> [--yes]     # dry run; --yes backs up the agent config first, then runs the commands
```

## 🚪 Onboarding a project

`sox project check` audits a project against the current setup (rules: `core/project-check.json`): leftovers of the v1 pipeline, missing or invalid `.socratex/config.json`, long or duplicated entry files, forked core scripts, non-standard overrides. It only reads. `sox project init` creates the files a project is missing from `templates/project/` and never overwrites.

```bash
core/sox project check <path> [--json] [--strict]   # one line per finding; exit 1 on errors (--strict: warnings too), 2 on wrong usage
core/sox project init <path> [--write]              # dry run by default; --write creates only the missing files
core/sox project explain <RULE-ID>                  # what the rule means and how to fix it
```

Extra folders to skip: config key `project_check.exclude` (globs) and `read_only_dirs` in `.ai/guard.json`. Project model tiers: only the config key `routing.tier_overrides`; `.ai/ROUTING.json` is deprecated.

## 🧱 Structure

```
SocratexAI/
  core/          in the repo, not overridden by users: the part that decides
    INIT.md        the only startup file; routes to the flow
    flow.json      ordered if -> then work steps (stages, roles, rules, gates)
    safety.json    named safety rules the guard enforces; relaxable only by the owner
    core.py        resolver: merges the layers, validates them, writes state/effective.json
    sox            the one command line (config, flow, ext, install, index, ...)
    *.schema.json  schemas of config, flow, profile, safety, module and extension files
    RULES.md, STYLE.md, DIRECTIVES.json, ROUTING.json, RISK-RULES.json, rules/, templates/
  defaults/      what works without any setup
    config.json    base config
    profiles/      solo, duo, yolo (bundles of config values)
    preferences/   code and communication standards (pointers to the rule documents)
  modules/       self-contained capabilities, each with module.json and tests next to the code
    stages/        review and planning (checker registries, selectors, reports)
    engine/        shared engine of both stages (chunking, merge, findings schema)
    routing/       tiers, roles and escalation (risk score, routing log; tier agents live in claude/agents)
    memory/        skill learnings and the improvements ledger
    tools/scripts/ install, backup, update, check_leaks, build_index, state, subrepos, ...
    extensions/    one manifest per plugin, MCP server, mod, skill or reference pack
      gpt/         ChatGPT share and archive tools (a module nested in the registry)
    core/          manifest that owns the core files above
  targets/       generated agent files (`sox install`); gitignored, never edit by hand
  claude/, codex/  adapters: Claude Code agents, hook, mods, settings; Codex entry file
  skills/        shared skills (spec, memory-review, skill-reflect, ...)
  templates/project/  starting files for a project (AGENTS.md, CLAUDE.md, INDEX.json)
  tests/         tests of the core, resolver and sox
  docs/          FLOW.md (generated), OVERRIDES.md, specs/, ledgers
  tools/         thin redirects to the old script paths for projects that still call them (`sox shims`)
  state/         logs, effective config, ledgers: machine output with rotation (gitignored)
  local/         your private layer (gitignored); `local.example/` seeds it
    overrides/     global overrides of defaults, stages, profiles and extensions
    projects/<project>/  private per-project overrides and settings that do not live in the project repo
```

Three kinds of place: **in the repo** (`core/`, `defaults/`, `modules/`, adapters; changed by pull requests), **generated** (`targets/`, `docs/FLOW.md`, `INDEX.json`; rebuilt from sources) and **yours** (`local/`, `state/`; never committed).

Config layers, last wins: `defaults/` and `modules/` -> `local/overrides/` -> the project's `.socratex/config.json` -> `local/projects/<project>/`. Safety rules can only be relaxed from the owner's `local/` layers. `sox config show` prints every value with its source. Project rules win over the core, except safety rules, which projects can only make stricter. Projects keep their own `INDEX.json`, `AGENTS.md`, `CLAUDE.md` and optional `.ai/` overrides; start from `templates/project/`. Override format (files, keys, merge rules, examples): `docs/OVERRIDES.md`.

What to run when: [docs/FLOW.md](docs/FLOW.md) (generated: `sox flow doc`).

## 🧰 Tools

The `sox` command line (`python core/sox <command>`):

| Command | Purpose |
|---|---|
| `sox config show [--project P]` | effective config with the source of every value, relaxed safety rules, enabled extensions, stage registry changes |
| `sox flow show \| check \| doc` | print the flow table (`--match fact=value`), validate it, regenerate `docs/FLOW.md` |
| `sox modules` | modules by kind: what, when to run, entry commands |
| `sox ext ...` | extension registry (see Extensions) |
| `sox install --plan \| --check \| --yes` | generated targets and the agent config install |
| `sox index [--check]` | regenerate `INDEX.json` from files and module manifests |
| `sox state rotate \| adopt-logs`, `sox backup`, `sox test`, `sox migrate`, `sox shims` | log rotation, config backup, test suite, schema migrations, old-path redirects |

Scripts:

| Tool | Purpose |
|---|---|
| `modules/tools/scripts/risk_score.py` | 0-10 risk score of the current diff -> model tier and effort (`core/RISK-RULES.json`, project override `.ai/RISK-RULES.json`) |
| `modules/tools/scripts/routing_log.py`, `modules/tools/scripts/routing_stats.py` | log routing outcomes per project and propose rule tuning |
| `modules/tools/scripts/json_read.py` | read one key or search a big JSON file without loading it whole |
| `modules/tools/scripts/skill_learn.py` | log a correction or failure next to a skill (`LEARNINGS.jsonl`); merges repeats, marks a skill READY for `skill-reflect` |
| `modules/tools/scripts/improvements_check.py` | list ledger items whose `verify` command fails on this machine (report only) |
| `modules/tools/scripts/backup.py` | zip and restore global agent config (never credential files) |
| `modules/tools/scripts/build_index.py` | regenerate `INDEX.json`; `--check` in CI |
| `modules/tools/scripts/check_leaks.py` | block private paths, tokens and local patterns before a push |
| `claude/hooks/guard.py` | PreToolUse guard: destructive git, secrets, project big files and read-only folders |

## 🧩 Agents and skills

- **Tier agents** (`claude/agents/`): `scout` (cheap search), `implementer` (execution from a spec), `planner` (plans, read-only), `reviewer` (independent review; a finding is CONFIRMED only when reproduced). Codex gets matching profiles generated from `core/ROUTING.json`.
- **Shared skills** (`skills/`): `spec` (one-form interview ending in `SPEC.md`), `memory-review` (monthly clean-up), `skill-reflect` (turns logged learnings into owner-approved edits of `SKILL.md`), `token-efficient-code`, `gpt-share-read`.
- **Claude-only skill** (`claude/skills/`): `usage-optimize` (token and cost analysis with `prompt-analytics`).
- **On-demand rules** (`core/rules/`): code style, commits, review, ROI, routing, safety, security review (business projects only), task gating.

## 📚 Docs

- `docs/FLOW.md`: what to run when (flow table, sox commands, directory map); generated, `sox flow doc --check` keeps it current.
- `docs/OVERRIDES.md`: the per-project override format (files, keys, merge rules, examples).
- `docs/specs/restructure/SPEC.md`: the spec and the record of the 3.0 restructure.
- `docs/AI-PRACTICES.md`: findings about working with AI agents (what helped, what failed, why).
- `docs/IMPROVEMENTS.json`: one ledger of every idea we weighed. Each item has a `status` (adopted, rejected, considering), the promise (`expected_result`), our verdict (`result`) and proof (`result_evidence`, `own:` = measured by us). Check it before proposing a plugin or tool again.
- `docs/AUDIT-pstack-ecc.md`: why we borrow ideas from pstack and ECC but install neither.
- `docs/ROUTER-LOOP.md`: the measure -> route -> learn loop for model choice.
- `docs/SETUP-NOTES.md`: machine setup notes.

## 🔒 Privacy

Everything that names you, your machine or private projects belongs in `local/`. The pre-push hook runs `modules/tools/scripts/check_leaks.py`, which blocks user-profile paths, tokens and every pattern in `local/sensitive-patterns.txt`.

## 📄 License

See `LICENSE` and `NOTICE`.
