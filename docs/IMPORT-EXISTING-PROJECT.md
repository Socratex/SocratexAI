# Import Existing Project

## Summary

Use `tools/import_existing_project.ps1` to install SocratexPipeline into an existing repository or project folder.

## Dry Run

Always start with a dry run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/import_existing_project.ps1 -TargetPath "C:\Path\To\Project" -Packs code -CreateProjectFiles -DryRun
```

## Import

Then run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tools/import_existing_project.ps1 -TargetPath "C:\Path\To\Project" -Packs code -CreateProjectFiles
```

## Safety

The importer skips existing files by default.

It does not overwrite existing project memory, source files, or documentation.

It installs pipeline-owned files under `SocratexAI/` and creates root `SOCRATEX.md`.

For code imports, standardized project memory is created as YAML and generated diagnostic/index artifacts should be JSON.

After code import, review `SOCRATEX.md`, `SocratexAI/PIPELINE-CONFIG.yaml`, and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/audit_docs.ps1 -Initialized
```

For non-code imports, review `SocratexAI/PIPELINE-CONFIG.md` instead.
