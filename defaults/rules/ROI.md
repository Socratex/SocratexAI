---
type: rules
title: ROI and leverage
description: How to choose between implementations and when to do the better version now.
updated: 2026-11-16
---

# 📈 ROI and leverage

- Optimize return on implementation cost: prefer changes that unlock future work, cut future rewrite cost or clearly improve the product without disproportionate complexity.
- Better version now: for every implementation, fix, migration, refactor or review, ask whether a modest extra step makes this the correct future-facing version. Do it when cheap now and expensive to retrofit later; ask for an overengineering check only when it becomes large, speculative or ceremony-heavy.
- When a requested feature implies a later dependency (generated IDs, seeds, save or schema contracts, ownership boundaries, state separation, source-of-truth paths), surface the cheapest prerequisite before accepting the requested order.
- Clean code, explicit contracts, data ownership, migrations, diagnostics, verification and security are future-cost controls, not polish.
- Known solutions first: engine or framework features, established patterns (state machines, queues, adapters, repositories, layered boundaries) and stable libraries before bespoke systems. Use patterns only where they clarify ownership and flow; enterprise ceremony is a tool, not a goal.
- No framework-building for hypothetical needs; add extension points early only when they will pay off soon.
- Before adding a non-trivial runtime system, define its budget (active counts, tick or materialization budget, pooling or data-only fallback, a metric or log to watch). When expected scale is unknown and it affects architecture, ask the owner for the load shape (counts, frequency, growth 2x/10x/100x).
- For non-trivial tasks, name the known pattern or standard trick you are applying; call out any custom solution together with its trade-off.
- Weigh value against effort, risk and reversibility for this project profile. Flag elegant work that does not pay off now.
- Plans and reviews may end with one to three "worth doing now" picks, each on its own line.
