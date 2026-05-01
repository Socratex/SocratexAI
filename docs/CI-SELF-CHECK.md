# CI Self-Check

## Summary

SocratexPipeline does not assume one CI provider.

Use this document as an instruction for AI agents to create a provider-specific CI workflow.

## Required Checks

Every CI provider should run:

1. PowerShell parse check for top-level `tools/*.ps1`.
2. `tools/audit_docs.ps1`.
3. Initialization dry run for at least one code project.

## Recommended Commands

Read `QUALITY-GATE.yaml` for the canonical self-check command list.

On Windows PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/audit_docs.ps1
```

For a code init dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/Initialize-SocratexPipeline.ps1 -ProjectName "Demo Project" -Language "English" -AiMode Enterprise -KeepPacks code -CreateFiles -CompileAgent -RunAudit -DryRun
```

## Provider Guidance

For GitHub Actions, create `.github/workflows/self-check.yml`.

For GitLab CI, create `.gitlab-ci.yml`.

For other providers, map the same checks into their shell runner format.

Do not commit provider-specific CI files unless the project has chosen that provider.
