# Recommendation

## Summary

SocratexPipeline should become a modular project runtime, not a single universal prompt.

## Product Shape

The recommended product structure is:

- `core/`: small shared operating contract for memory, planning, decisions, execution, and quality.
- `project/`: domain packs that extend the core.
- `adapters/`: thin pointers for specific AI agents.
- `templates/`: starter artifacts copied during initialization.
- `tools/`: optional executable quality and consistency helpers.

## Recommended Initial Product

Start with two real product modes:

- code projects,
- generic non-code projects.

Then add personal and creative packs as separate modules once the core behavior is stable.

## Why Code First

The code pack has the clearest quality gates, strongest need for reproducibility, and easiest validation through tests, linting, typechecks, builds, and source diffs.

It should become the reference implementation for stricter project-runtime behavior.

## Main Risk

The main product risk is excessive ceremony.

Use three operating levels:

- Lite: `STATE`, `PLAN`, `BACKLOG`, `DECISIONS`.
- Standard: Lite plus review, issues, and completion log.
- Pro: Standard plus registries, context capsules, audits, quality gates, and command workflows.

## Near-Term Recommendation

Make the code pack fully operational before expanding other packs.

That means:

- command workflows are deterministic,
- registry rules are explicit,
- document promotion rules are auditable,
- DDD-ADIV is defined as a practical engineering default,
- the first-run initializer can produce a usable project without manual cleanup.

## Learning Inbox Recommendation

Use GitHub Issues as the shared network inbox for cross-project pipeline learning.

The recommended pattern is:

- local project generates a structured learning report,
- source pipeline publishes it into one stable `SocratexPipeline Learning Inbox` issue,
- duplicate reports are skipped by hash,
- Discord or email stays optional alerting, not the durable inbox,
- reusable features are promoted only after review.

This keeps learning visible across machines and projects without turning every candidate into a separate notification.
