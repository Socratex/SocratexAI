# CI Self-Check

## Summary

SocratexPipeline does not assume one CI provider.

Use this document as an instruction for AI agents to create a provider-specific CI workflow.

## Required Checks

Every CI provider should run:

1. Python syntax check for top-level `tools/*.py`.
2. `tools/documents/audit_docs.py`.
3. Initialization dry run for at least one code project.

## Recommended Commands

Read `QUALITY-GATE.json` for the canonical self-check command list.

On Windows shell:

```bash
python3 -B tools/documents/audit_docs.py
```

For a code init dry run:

```bash
python3 -B tools/pipeline/Initialize-SocratexPipeline.py -ProjectName "Demo Project" -Language "English" -AiMode Enterprise -KeepPacks code -CreateFiles -CompileAgent -RunAudit -DryRun
```

## Provider Guidance

For GitHub Actions, create `.github/workflows/self-check.json`.

For GitLab CI, create `.gitlab-ci.json`.

For other providers, map the same checks into their shell runner format.

Do not commit provider-specific CI files unless the project has chosen that provider.
