param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [string]$TargetPath = ".",

    [string[]]$Packs = @("code"),

    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",

    [string[]]$DirectiveFiles = @("AGENTS.md"),

    [switch]$ReinitializeNew,

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

    if (Test-Path -LiteralPath $SourcePath -PathType Container) {
        New-Item -ItemType Directory -Force -Path $DestinationPath | Out-Null
        foreach ($child in Get-ChildItem -LiteralPath $SourcePath -Force) {
            Copy-Item -LiteralPath $child.FullName -Destination $DestinationPath -Recurse -Force
        }
        return
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $DestinationPath) | Out-Null
    Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
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

foreach ($path in @(
    ".gitignore",
    "AI-compiled",
    "adapters",
    "core",
    "docs",
    "docs-tech",
    "evals",
    "initializer",
    "learning",
    "project",
    "templates",
    "tools",
    "AGENTS.md",
    "LICENSE",
    "PUBLIC-BOOTSTRAP.md",
    "QUALITY-GATE.json",
    "README.md",
    "RECOMMENDATION.md",
    "VERSION",
    "pipeline_featurelist.json"
)) {
    $sourcePath = Join-Path $SourceRoot $path
    if (Test-Path -LiteralPath $sourcePath) {
        Copy-Tree -SourcePath $sourcePath -DestinationPath (Join-Path $InstallRoot $path)
    }
}

if (Test-Path -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md")) {
    Copy-Tree -SourcePath (Join-Path $SourceRoot "templates\SOCRATEX.md") -DestinationPath (Join-Path $TargetRoot "SOCRATEX.md")
}

if (-not $DryRun) {
    if ($ReinitializeNew) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\reinitialize_pipeline.ps1") -TargetPath $TargetRoot -Packs $Packs
    }
    $syncFeatureListScript = Join-Path $InstallRoot "tools\sync_pipeline_featurelist.ps1"
    if (Test-Path -LiteralPath $syncFeatureListScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $TargetRoot
    }
    $knowledgeCompileScript = Join-Path $InstallRoot "tools\knowledge_compile.ps1"
    if (Test-Path -LiteralPath $knowledgeCompileScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
        if ($LASTEXITCODE -ne 0) {
            throw "knowledge_compile failed with exit code $LASTEXITCODE"
        }
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\set_directives.ps1") -TargetPath $TargetRoot -Mode $DirectiveMode -DirectiveFiles $DirectiveFiles
    if ($LASTEXITCODE -ne 0) {
        throw "set_directives failed with exit code $LASTEXITCODE"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\audit_docs.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "audit_docs failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Pipeline update complete. SocratexAI is active for this project; future sessions should start from SOCRATEX.md."
