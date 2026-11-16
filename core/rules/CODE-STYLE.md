---
type: rules
title: Code style and quality
description: Engineering standard for writing and reviewing code in any language; the project's own standard wins on conflict.
updated: 2026-11-16
---

# 🧱 Code style and quality

## 📜 Code as contract
- Prefer constructions whose meaning is explicit before runtime: explicit types, ownership, state transitions and side-effect boundaries.
- Hidden semantics, implicit control flow and magic-heavy patterns are liabilities; when a flexible feature obscures the contract, choose the explicit alternative.
- Keep contracts mechanically checkable by tools and easy to navigate in the IDE.
- Follow existing project conventions first; adapt syntax, naming and layout to them.

## 📖 Read like a book
- Organize top-down: constants and dependencies, public entry points, orchestration, then lower-level helpers.
- Public methods are the table of contents, named by business intent; their bodies are short sequences of calls to well-named private methods placed below them. Do not split trivial one-liners.
- One function, one concern, one abstraction level; extract helpers when a block mixes input, state mutation, presentation, persistence and framework plumbing.
- Keep each domain easy to find by ownership: orchestration, data truth, configuration and runtime executors each in one obvious place. No parallel ownership of the same concern.
- Names expose business meaning, not mechanism; side effects stay visible in the call flow.
- Separate pure logic from I/O, framework glue and persistence; isolate nondeterminism behind small testable interfaces.

## 💬 Comments
- Only two kinds: business comments (what a system does, why it exists) and quirk comments (workaround, hazard, TODO, non-obvious constraint).
- No docblocks that restate names, types or obvious behavior.
- Every new or materially refactored main class and main entry method gets one short business comment.

## ✅ Quality rules
- Guard clauses over deep nesting; explicit branching and error handling; fail fast on invalid state; normalize external errors at boundaries.
- Syntax errors, type errors, unresolved references, linter and analyzer failures are must-fix.
- Remove dead code, unused variables and imports, redundant branches and temporary debug code when touched.
- Modern, community-proven idioms over outdated habits, but no novelty for its own sake.
- Laziness first: before adding code, ask if deleting or reusing something solves it. The smallest change that works wins; every added line needs a reason.
- Surgical fix: smallest safe change in the existing area. Larger change: a clear ownership boundary instead of logic spread across unrelated files.
- No micro-optimization without evidence; but for predictable scale (hot paths, batches, mass data) choose the lightweight-by-design shape now: data-first truth, batching, pooling, bounded caches.
- Placeholders only when clearly marked and scoped; never fake-complete behavior that looks production-ready.
- Data-access code: explicit joins and aliases, qualified references, safeguards against unintended mass updates or deletes.
