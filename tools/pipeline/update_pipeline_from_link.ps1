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

$syncPackageScript = Join-Path $SourceRoot "tools\pipeline\sync_managed_pipeline_package.ps1"
if (-not (Test-Path -LiteralPath $syncPackageScript)) {
    throw "Update source is missing required managed package sync script: $syncPackageScript"
}

$syncArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $syncPackageScript,
    "-SourceRoot",
    $SourceRoot,
    "-InstallRoot",
    $InstallRoot
)
if ($DryRun) {
    $syncArgs += "-DryRun"
}
& powershell @syncArgs
if ($LASTEXITCODE -ne 0) {
    throw "sync_managed_pipeline_package failed with exit code $LASTEXITCODE"
}

if (Test-Path -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md")) {
    if ($DryRun) {
        Write-Host "Would copy root controller: $(Join-Path $SourceRoot 'templates\SOCRATEX.md') -> $(Join-Path $TargetRoot 'SOCRATEX.md')"
    } else {
        Copy-Item -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md") -Destination (Join-Path $TargetRoot "SOCRATEX.md") -Force
    }
}

if (-not $DryRun) {
    if ($ReinitializeNew) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\pipeline\reinitialize_pipeline.ps1") -TargetPath $TargetRoot -Packs $Packs
    }
    $syncFeatureListScript = Join-Path $InstallRoot "tools\repo\sync_pipeline_featurelist.ps1"
    if (Test-Path -LiteralPath $syncFeatureListScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $TargetRoot
    }
    $knowledgeCompileScript = Join-Path $InstallRoot "tools\knowledge\knowledge_compile.ps1"
    if (Test-Path -LiteralPath $knowledgeCompileScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
        if ($LASTEXITCODE -ne 0) {
            throw "knowledge_compile failed with exit code $LASTEXITCODE"
        }
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\pipeline\set_directives.ps1") -TargetPath $TargetRoot -Mode $DirectiveMode -DirectiveFiles $DirectiveFiles
    if ($LASTEXITCODE -ne 0) {
        throw "set_directives failed with exit code $LASTEXITCODE"
    }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\documents\audit_docs.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "audit_docs failed with exit code $LASTEXITCODE"
    }
}

Write-Host "Pipeline update complete. SocratexAI is active for this project; future sessions should start from SOCRATEX.md."
