---
type: rules
title: Task gating
description: When to just do it, when to plan first, when to research first and when to ask.
updated: 2026-11-16
---

# 🚦 Task gating

- Local, clear, reversible change: implement without asking.
- Complex, under-specified or multi-boundary work: short plan first.
- Research first for a new capability or system: how do established products and best practices solve it? Write a short note (known approaches, chosen one and why, resulting build order) before the architecture proposal. Not needed for local fixes.
- Before executing, check whether the task:
  - affects more than one system (UI, domain logic, persistence, world or data generation),
  - adds or changes state transitions,
  - assumes data formats or schemas,
  - adds randomness, async behavior or timing dependencies,
  - touches more than 2-3 files.
- Any yes: write a short impact note first (systems affected, transitions or schema assumptions, files and ownership boundaries likely to change).
- Ask only when the request is ambiguous, the change would force irreversible architecture or coupling, or it cannot stay modular without guesswork. Then ask early, in one form.
- If a task would increase coupling, hidden side effects, non-determinism or unclear ownership, stop and explain before changing anything.
- Prefer explicit state machines, typed data and isolated modules; never mix UI, domain logic and persistence in one function.
- Non-trivial structural work: propose the architecture (ownership boundaries, source of truth, runtime/data/view split, extension points, why this shape) and treat it as an approval checkpoint; then implement against it instead of improvising mid-flight.
