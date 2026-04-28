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
$lines.Add('Read `core/AGENT-CONTRACT.md` first.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Then read the active state file as the compact active project state. For code projects, use `STATE.yaml`.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/MEMORY-MODEL.md` for active state, branch-scoped state, plans, decisions, and context capsules.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/ACTIVATION-CHECK.md` after the first prompt handled under an installed pipeline to verify the rules are loaded.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/UPDATE-PROTOCOL.md` when the user asks to update, refresh, reinstall, or pull the latest pipeline.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/PROMOTION-RULES.md` before moving work between memory layers.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/PROJECT-PROFILE.md` when `PIPELINE-CONFIG.yaml` contains `project_profile`.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/ROI-BIAS.md` before ranking recommendations, planning work, or reviewing tradeoffs.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Read `core/SCRIPT-FALLBACK.md` before bypassing any script that cannot run.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add('Use `core/CONTEXT-COMPACTION.md` during long or drift-prone sessions.') | Out-Null
$lines.Add("") | Out-Null
$lines.Add("## Active Project Packs") | Out-Null
$lines.Add("") | Out-Null

foreach ($pack in $normalizedPacks) {
    $packPath = "project/$pack/PACK.md"
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
        "project/code/WORKFLOW.md",
        "project/code/BRANCH-MODE.md",
        "project/code/COMMANDS.md",
        "project/code/REGISTRIES.md",
        "project/code/DDD-ADIV.md",
        "project/code/GIT.md",
        "project/code/FROZEN-LAYERS.md",
        "project/code/INSTRUCTION-CAPTURE.md",
        "project/code/DIAGNOSTICS.md"
    )) {
        $lines.Add("- ``$path``") | Out-Null
    }
}

$output = Join-Path $Root $OutputPath
Set-Content -LiteralPath $output -Value ([string]::Join([Environment]::NewLine, $lines)) -NoNewline
Write-Host "Compiled agent instructions: $OutputPath"
