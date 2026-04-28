# Update Protocol

## Purpose

Use this protocol when the user asks to update, refresh, reinstall, or pull the latest SocratexAI pipeline in an already configured project.

The agent must know where the pipeline comes from and which updater to run before changing files.

## Source Resolution

Determine the update source in this order:

1. `PIPELINE-CONFIG.yaml` or `PIPELINE-CONFIG.md` value `pipeline.update_source`.
2. `PIPELINE-CONFIG.yaml` or `PIPELINE-CONFIG.md` value `pipeline.public_bootstrap_url`.
3. The installed `SocratexAI/PUBLIC-BOOTSTRAP.md` source URL if documented by the project.
4. A user-provided URL or local source path.
5. Ask the user for the update source.

Do not guess a repository URL when no source is configured.

## Update Command

For public user updates, prefer:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/update_pipeline_from_link.ps1 -Source "<zip-or-local-source>" -Packs code
```

Use the selected project packs from config when available.

For maintainer-only upgrades from a private reference project, use the maintainer upgrade tool only when the user explicitly requests that source:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/upgrade_from_riftbound.ps1 -RiftboundPath "<path>"
```

For migration from another AI pipeline, use:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/migrate_ai_pipeline.ps1
```

## Workflow

1. Read root `SOCRATEX.md`.
2. Read installed pipeline config.
3. Resolve the update source.
4. Check runtime availability or follow `core/SCRIPT-FALLBACK.md`.
5. Run the updater with explicit source and packs.
6. Run `SocratexAI/tools/audit_docs.ps1` when available.
7. Run `SocratexAI/core/ACTIVATION-CHECK.md` after update.
8. Report updated source, packs, verification, skipped checks, and remaining risks.

## Safety

Do not overwrite project memory such as active state, branch state, plans, backlog, decisions, or context docs unless the updater explicitly preserves or migrates them.

Do not update from an untrusted URL without telling the user what source will be used.

If update source is missing, ask for it and stop before changing files.

