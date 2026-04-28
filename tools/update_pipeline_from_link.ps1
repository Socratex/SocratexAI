param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [string]$TargetPath = ".",

    [string[]]$Packs = @("code"),

    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",

    [string[]]$DirectiveFiles = @("AGENTS.md"),

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$InstallRoot = Join-Path $TargetRoot "SocratexAI"
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("socratex-pipeline-update-" + [guid]::NewGuid().ToString("N"))

function Copy-Tree {
    param(
        [string]$SourcePath,
        [string]$DestinationPath
    )

    if ($DryRun) {
        Write-Host "Would copy: $SourcePath -> $DestinationPath"
        return
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DestinationPath) | Out-Null
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Recurse -Force
}

function Resolve-SourceRoot {
    param([string]$SourceValue)

    if (Test-Path -LiteralPath $SourceValue) {
        return (Resolve-Path -LiteralPath $SourceValue).Path
    }

    New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null
    $zipPath = Join-Path $TempRoot "pipeline.zip"
    Invoke-WebRequest -Uri $SourceValue -OutFile $zipPath
    Expand-Archive -LiteralPath $zipPath -DestinationPath $TempRoot -Force
    $candidates = @(Get-ChildItem -LiteralPath $TempRoot -Directory)
    if ($candidates.Count -eq 1) {
        return $candidates[0].FullName
    }
    return $TempRoot
}

$SourceRoot = Resolve-SourceRoot -SourceValue $Source

Write-Host "==> updating SocratexPipeline"
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"
Write-Host "Install root: $InstallRoot"

foreach ($path in @("core", "tools", "templates", "docs", "adapters", "PUBLIC-BOOTSTRAP.md", "README.md", "RECOMMENDATION.md")) {
    $sourcePath = Join-Path $SourceRoot $path
    if (Test-Path -LiteralPath $sourcePath) {
        Copy-Tree -SourcePath $sourcePath -DestinationPath (Join-Path $InstallRoot $path)
    }
}

if (-not $DryRun) {
    New-Item -ItemType Directory -Force -Path (Join-Path $InstallRoot "project") | Out-Null
}
foreach ($pack in $Packs) {
    $sourcePack = Join-Path $SourceRoot "project\$pack"
    if (Test-Path -LiteralPath $sourcePack) {
        Copy-Tree -SourcePath $sourcePack -DestinationPath (Join-Path $InstallRoot "project\$pack")
    }
}

if (Test-Path -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md")) {
    Copy-Tree -SourcePath (Join-Path $SourceRoot "templates\SOCRATEX.md") -DestinationPath (Join-Path $TargetRoot "SOCRATEX.md")
}

if (-not $DryRun) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\set_directives.ps1") -TargetPath $TargetRoot -Mode $DirectiveMode -DirectiveFiles $DirectiveFiles
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\audit_docs.ps1")
}

Write-Host "Pipeline update complete."
