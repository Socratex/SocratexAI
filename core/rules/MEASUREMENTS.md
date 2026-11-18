---
type: rules
title: Measurements
description: Before trusting or reporting a measured number (FPS, latency, speedup, eval result): decide first, find the limiter, rule out a wrong measurement.
updated: 2026-11-18
---

# 📏 Explain the number

Borrowed from pstack `principle-explain-the-number`. Load only when you measure or report a number.

- Write the decision before you run: what result would change it, and the noise floor. If run-to-run spread is bigger than the effect, stop.
- Ask "why not double?": name the limiter from a profile or counters taken during the run. A guess from reading code is not a limiter.
- List what else the number could measure (errors, skipped or cached work, code that never ran, noise, a piece too small to matter) and rule each out with evidence.
- Report the number with run count, spread and limiter.
