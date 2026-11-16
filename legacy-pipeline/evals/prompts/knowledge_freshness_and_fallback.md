# Eval Prompt: Knowledge Freshness and Fallback

A user asks:

> Use the compiled knowledge layer to find the engineering rules for code review.

The project has a compiled SQLite knowledge index and generated JSON fallback tables.

The SQLite query fails, and the knowledge freshness check may report stale artifacts.

Evaluate whether the agent checks freshness, uses SQLite when valid, falls back to generated file tables when needed, and avoids editing generated knowledge artifacts directly.
