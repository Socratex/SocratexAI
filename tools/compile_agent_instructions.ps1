param(
    [string[]]$Packs = @("generic"),
    [string]$OutputPath = "AGENTS.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

$normalizedPacks = @()
foreach ($pack in $Packs) {
    $normalizedPacks += ($pack -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("# Agent Instructions") | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/AGENT-CONTRACT.yaml` first.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Then read the active state file as the compact active project state. For code projects, use `STATE.yaml`; for non-code user-facing memory, use `STATE.md`.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/MEMORY-MODEL.yaml` for active state, branch-scoped state, plans, decisions, and context capsules.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/ACTIVATION-CHECK.yaml` after the first prompt handled under an installed pipeline to verify the rules are loaded.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/UPDATE-PROTOCOL.yaml` when the user asks to update, refresh, reinstall, or pull the latest pipeline.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/REMOVAL-PROTOCOL.yaml` when the user asks to remove, uninstall, delete, or disable the pipeline.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/PROMOTION-RULES.yaml` before moving work between memory layers.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/PROJECT-PROFILE.yaml` when `PIPELINE-CONFIG.yaml` contains `project_profile`.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/ROI-BIAS.yaml` before ranking recommendations, planning work, or reviewing tradeoffs.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/SCRIPT-FALLBACK.yaml` before bypassing any script that cannot run.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/CONTEXT-COMPACTION.yaml` during long or drift-prone sessions.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add("## Active Project Packs") | Out-Null
$lines.Add("") | Out-Null

foreach ($pack in $normalizedPacks) {
    $packPath = "project/$pack/PACK.yaml"
    if (-not (Test-Path -LiteralPath (Join-Path $Root $packPath))) {
        throw "Unknown or unavailable pack: $pack"
    }

    $lines.Add("- ``$packPath``") | Out-Null
}

if ($normalizedPacks -contains "code") {
    $lines.Add("") | Out-Null
    $lines.Add("## Code Project Reads") | Out-Null
    $lines.Add("") | Out-Null
    foreach ($path in @(
        "project/code/WORKFLOW.yaml",
        "project/code/BRANCH-MODE.yaml",
        "project/code/COMMANDS.yaml",
        "project/code/REGISTRIES.yaml",
        "project/code/DDD-ADIV.yaml",
        "project/code/GIT.yaml",
        "project/code/FROZEN-LAYERS.yaml",
        "project/code/INSTRUCTION-CAPTURE.yaml",
        "project/code/DIAGNOSTICS.yaml"
    )) {
        $lines.Add("- ``$path``") | Out-Null
    }
}

$output = Join-Path $Root $OutputPath
Set-Content -LiteralPath $output -Value ([string]::Join([Environment]::NewLine, $lines)) -NoNewline
Write-Host "Compiled agent instructions: $OutputPath"
