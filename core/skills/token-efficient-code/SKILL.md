---
name: token-efficient-code
description: Select locally installed RTK, ast-grep, Serena, Graphify, TOON and Repomix for bounded code retrieval, CLI output reduction and context exports when the task benefits from those operations. Follow the active project workflow and preserve original verification evidence.
---

# 🧰 Local code-context tools

🧭 Follow the active project's `WORKFLOW.json` token_efficient_tools policy. This file supplies invocation details, not project architecture or a requirement to run all six programs. Source location: `core/skills/token-efficient-code/SKILL.md`; installed package: `SocratexAI/core/skills/token-efficient-code/SKILL.md`.

## 🔎 Choose the matching operation

| Need | Tool | Boundary |
| --- | --- | --- |
| Verbose supported Git/search/build output | RTK OSS | Keep canonical check entrypoints, raw logs and exit codes |
| Syntax shapes such as allocations/declarations/calls | ast-grep | Use rg for literal names; AST matches do not resolve types |
| Semantic symbols, references or implementations | Serena LSP/MCP | Scope paths and bodies; verify the connection with an actual query |
| Repeated cross-file architecture exploration | Graphify | Fresh bounded local code-only graph; verify important edges in source |
| Selected uniform JSON records | TOON | Compare compact JSON; preserve canonical data and round-trip fidelity |
| An explicitly needed multi-file handoff/export | Repomix | Explicit includes/excludes, token budget, security scanning, local output |

## 🐧 Linux and macOS

🛠️ Discover `rtk`, `ast-grep`, `serena`, `graphify`, `toon`, `repomix` on PATH; user installs may be in `~/.local/bin`. Prefer `ast-grep` because `sg` can name a different system utility. Inspect `--help` for the installed version instead of assuming Windows suffixes or an owner's home directory.

📊 RTK example: `rtk git status --short`. If a sandbox cannot write its default statistics directory, set `RTK_DB_PATH` to a writable local database outside tracked source, for example a verified Git-ignored `ignored/ai-tools/rtk/history.db`. Use the same variable for `rtk gain`. Do not replace the executable, weaken the sandbox, or filter required verification receipts just to collect metrics.

🔍 AST example: `ast-grep run --lang csharp --pattern 'new $TYPE($$$ARGS)' <small-scope>`. Select the actual supported language. Pass patterns as literal arguments so shell expansion cannot alter them.

🧠 Serena example: `serena start-mcp-server --context codex --agent-interface tools --project-from-cwd --enable-web-dashboard false --open-web-dashboard false`. Configure MCP with the discovered executable and required environment; read initial_instructions, retain its session id and activate the exact project. Use read-only project configuration and exclude generated/vendor/frozen areas for retrieval. C# in Serena 2.1 requires .NET 10 and the local Roslyn dependency; check actual prerequisites before claiming readiness. Config changes may require restarting the client; a CLI version check or a separate diagnostic client does not prove the current agent session has native MCP tools. Obtain symbol paths from find_symbol/get_symbols_overview before reference queries to distinguish types from same-named constructors.

🕸️ Graphify example: `graphify extract <small-scope> --code-only --no-cluster --max-workers 2 --out <external-output-dir>`; the tested CLI writes `<external-output-dir>/graphify-out/graph.json`. Query with `graphify query '<question>' --graph <graph.json> --budget 1200`. Never substitute default extraction, semantic LLM backends, clustering or a whole-repository scan without task justification and required authorization.

📦 TOON example: `toon <selected.json> --stats`, then `toon --decode <encoded.toon>`. Compare decoded JSON with the original values. Nested/nonuniform payloads may be larger; do not convert operational source documents preemptively.

📚 Repomix example: `repomix <small-scope> --include '<globs>' --ignore '<excluded-globs>' --output <external-file> --token-budget 6000`. Keep default security scanning enabled. Do not use remote/publishing options for a local-only task. Check the actual output: --compress is not guaranteed to reduce C# or preserve enough implementation evidence.

## 🪟 Windows

🛠️ Use `Get-Command` to discover executable locations: commonly `rtk.exe`, `ast-grep.exe`, `serena`, `graphify.exe`, `toon.cmd`, `repomix.cmd`. Set `$env:RTK_DB_PATH` when needed. Use argument arrays/literal patterns and the installed version's help. Do not reuse a Linux path or hardcode a particular Windows user profile.

## 📌 Evidence and fallback

🛡️ Tools are retrieval projections, not canonical owners. Follow project document readers, quality gates, finalizers and frozen-layer rules. Missing tools, stale graphs, incomplete LSP results or excessive context cost justify a narrow source/rg fallback; disclose material limitations once. No automatic installs, cloud backends, paid services or unsupported whole-task savings claims are implied.
