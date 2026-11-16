# Import Existing Project

## Summary

Use `tools/pipeline/import_existing_project.py` to install SocratexPipeline into an existing repository or project folder.

## Dry Run

Always start with a dry run:

```bash
python3 -B tools/pipeline/import_existing_project.py -TargetPath "C:\Path\To\Project" -Packs code -CreateProjectFiles -DryRun
```

## Import

Then run:

```bash
python3 -B tools/pipeline/import_existing_project.py -TargetPath "C:\Path\To\Project" -Packs code -CreateProjectFiles
```

## Safety

The importer skips existing files by default.

It does not overwrite existing project memory, source files, or documentation.

It installs pipeline-owned files under `SocratexAI/` and creates root `SOCRATEX.md`.

For code imports, standardized project memory is created as JSON and generated diagnostic/index artifacts should be JSON.

After code import, review `SOCRATEX.md`, `SocratexAI/PIPELINE-CONFIG.json`, and run:

```bash
python3 -B SocratexAI/tools/documents/audit_docs.py -Initialized
```

For non-code imports, review `SocratexAI/PIPELINE-CONFIG.json` instead.
