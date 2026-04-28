param(
    [Parameter(Mandatory = $true)]
    [string]$TargetPath,

    [string[]]$Packs = @("code"),

    [ValidateSet("Lite", "Standard", "Enterprise")]
    [string]$AiMode = "Standard",

    [string]$Language = "English",

    [switch]$CreateProjectFiles,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SourceRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$InstallRoot = Join-Path $TargetRoot "SocratexAI"

$normalizedPacks = @()
foreach ($pack in $Packs) {
    $normalizedPacks += ($pack -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
$Packs = $normalizedPacks

function Copy-ItemSafe {
    param(
        [string]$Source,
        [string]$Destination
    )

    if ($DryRun) {
        Write-Host "Would copy: $Source -> $Destination"
        return
    }

    if (Test-Path -LiteralPath $Destination) {
        Write-Host "Skip existing: $Destination"
        return
    }

    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse
}

Write-Host "==> importing SocratexPipeline into existing project"
Write-Host "Target: $TargetRoot"
Write-Host "Install root: $InstallRoot"

foreach ($path in @("core", "adapters", "tools")) {
    Copy-ItemSafe -Source (Join-Path $SourceRoot $path) -Destination (Join-Path $InstallRoot $path)
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Join-Path $InstallRoot "project") | Out-Null
}
foreach ($pack in $Packs) {
    $sourcePack = Join-Path $SourceRoot "project\$pack"
    if (-not (Test-Path -LiteralPath $sourcePack)) {
        throw "Unknown pack: $pack"
    }

    Copy-ItemSafe -Source $sourcePack -Destination (Join-Path $InstallRoot "project\$pack")
}

Copy-ItemSafe -Source (Join-Path $SourceRoot "AGENTS.md") -Destination (Join-Path $InstallRoot "AGENTS.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "RECOMMENDATION.md") -Destination (Join-Path $InstallRoot "RECOMMENDATION.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "PUBLIC-BOOTSTRAP.md") -Destination (Join-Path $InstallRoot "PUBLIC-BOOTSTRAP.md")
Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\SOCRATEX.md") -Destination (Join-Path $TargetRoot "SOCRATEX.md")

if ($CreateProjectFiles) {
    $hasCodePack = $Packs -contains "code"
    $templateMap = if ($hasCodePack) {
        @{
            "code/STATE.yaml" = "STATE.yaml"
            "code/_PLAN.yaml" = "_PLAN.yaml"
            "code/TODO.yaml" = "TODO.yaml"
            "code/DECISIONS.yaml" = "DECISIONS.yaml"
            "code/CHANGELOG.yaml" = "CHANGELOG.yaml"
            "code/BUGS.yaml" = "BUGS.yaml"
            "code/BUGS-SOLVED.yaml" = "BUGS-SOLVED.yaml"
            "_INSTRUCTIONS.md" = "_INSTRUCTIONS.md"
            "code/_INSTRUCTION-QUEUE.yaml" = "_INSTRUCTION-QUEUE.yaml"
            "code/PIPELINE-CONFIG.yaml" = "PIPELINE-CONFIG.yaml"
            "code/context-docs/TECHNICAL.yaml" = "context-docs\TECHNICAL.yaml"
            "code/context-docs/FROZEN_LAYERS.yaml" = "context-docs\FROZEN_LAYERS.yaml"
            "logs-.gitkeep" = "logs\.gitkeep"
        }
    } else {
        @{
            "STATE.md" = "STATE.md"
            "_PLAN.md" = "_PLAN.md"
            "TODO.md" = "TODO.md"
            "DECISIONS.md" = "DECISIONS.md"
            "PIPELINE-CONFIG.md" = "PIPELINE-CONFIG.md"
        }
    }

    foreach ($entry in $templateMap.GetEnumerator()) {
        Copy-ItemSafe -Source (Join-Path $SourceRoot "templates\$($entry.Key)") -Destination (Join-Path $InstallRoot $entry.Value)
    }
}

if (-not $DryRun) {
    $hasCodePack = $Packs -contains "code"
    $configPath = if ($hasCodePack) {
        Join-Path $InstallRoot "PIPELINE-CONFIG.yaml"
    } else {
        Join-Path $InstallRoot "PIPELINE-CONFIG.md"
    }
    if (-not (Test-Path -LiteralPath $configPath)) {
        if ($hasCodePack) {
            $packLines = ($Packs | ForEach-Object { "  - $_" }) -join [Environment]::NewLine
            $config = @"
summary: Imported SocratexPipeline configuration.
language: $Language
active_project_packs:
$packLines
ai_operating_mode: $AiMode
"@
        } else {
            $config = @"
# Pipeline Config

## Summary

Imported SocratexPipeline configuration.

## Language

$Language

## Active Project Packs

$([string]::Join(", ", $Packs))

## AI Operating Mode

$AiMode

"@
        }
        Set-Content -LiteralPath $configPath -Value $config -NoNewline
    }
}

Write-Host "Import complete. Review SOCRATEX.md and run SocratexAI/tools/audit_docs.ps1 when ready."
