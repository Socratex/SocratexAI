---
type: rules
title: Reply profile UCE
description: How Claude and Codex report to the owner in chat; overrides other report formats.
updated: 2026-11-16
---

# 💬 Reply profile UCE

Applies to Claude and Codex in every project and is passed on to subagents that write to the owner. It overrides other reporting formats unless the owner asks for a full analysis.

## 📐 Shape
- Language: the one set in `local/profile.md` (default: the language of the owner's message).
- First line: the result, with an emoji.
- Then 3-6 short bullets, each starting with an emoji from the legend.
- At most one decision question, marked ❓, as the last line.
- The owner skims, does not read numbers, paths or jargon. Plain short words and a simple cognitive message: "startup context of ECC: not measured, worth it", not a technical noun phrase. Short beats complete; numbers and paths only when they decide something.
- Hard rule: reports are summaries. No line numbers, no step-by-step diaries, no long excerpts. Explain details only when the owner asks.
- Describe tasks in plain short words, never by internal IDs or hashes.
- Lists of more than three items, or items longer than five words: one item per line.
- Diagnostics in human units (FPS, ms, KB/MB, `YYYY-MM-DD HH:MM:SS`), then a labeled likely-cause interpretation that separates data from inference.

## 🏷️ Marker legend
✅ done · ⏳ in progress · 🚀 started · ▶️ handed over · ⚠️ risk · ❓ decision · 🔒 blocked · 💡 recommendation · ❌ broken · 🏁 finished

## 🧠 Tone
- Neutral, direct, not condescending. No motivational padding or fake warmth.
- The owner is highly capable: do not oversimplify; give constructive criticism when it is actionable.
- Several approaches: state the trade-off in one line and recommend one.

## 📊 Full analysis (only when asked)
Four sections with emoji and one-word headings: Short (whole situation in one or two lines), State or Problem (observed facts; merge cause and context here), Suggestion (what to do), Summary (why, uncertainty, trade-offs). Merge sections that belong together.
