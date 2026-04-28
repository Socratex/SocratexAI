# Code Diagnostics

## Summary

Use this workflow for logs, traces, crash dumps, test output, runtime errors, screenshots, and other evidence-driven debugging inputs.

Programming diagnostics should prefer JSON for generated summaries and YAML for agent-readable diagnostic state.

## Required Project Setup

For code projects, create a root-level `logs/` folder when diagnostics are expected.

Keep `logs/.gitkeep` if the directory should exist in source control.

Generated diagnostic dumps, screenshots, traces, and temporary summaries should normally stay untracked unless the project explicitly wants fixtures.

## Diagnostic Intake

Evidence may include:

- `.log` files,
- `.txt` console output,
- `.json` runtime dumps,
- screenshots,
- test output,
- crash reports,
- CI artifacts,
- profiler snapshots.

## Workflow

1. Identify the newest relevant evidence.
2. Extract current errors, warnings, stack traces, failing tests, and repeated symptoms.
3. Separate observed facts from hypotheses.
4. Translate raw payloads into human-readable units before reporting them.
5. Add a likely-cause interpretation after the observed facts.
6. Choose the smallest source-owned fix or the smallest useful diagnostic addition.
7. Run the relevant quality gate.
8. Update `BUGS.yaml`, `ISSUES.yaml`, or `STATE.yaml` when the evidence changes active work.
9. Ask for user confirmation before moving a suspected bug to `BUGS-SOLVED.yaml`.

## Generic Command

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/log_summary.ps1 -Description "<what to diagnose>"
```

The default output is `DIAGNOSTICS-SUMMARY.json`.

## Human-Readable Reporting

When reporting diagnostics to a user:

- show timing in milliseconds when practical,
- show memory in KB, MB, or GB,
- show throughput or frame rates in the most natural domain unit,
- show timestamps as `YYYY-MM-DD HH:MM:SS` when timestamps are present,
- include the relevant domain label or environment label when the evidence provides one,
- distinguish observed data from likely-cause inference,
- state uncertainty when the evidence is incomplete.

Do not paste large raw logs into chat when a compact summary is enough.

## Evidence Handling

Do not delete logs automatically after a fix attempt.

After the user confirms the issue is resolved, generated diagnostic files may be cleared while preserving `.gitkeep` and directory structure.
