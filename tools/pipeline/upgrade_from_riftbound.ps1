param(
    [Parameter(Mandatory = $true)]
    [string]$RiftboundPath,
    [string]$TargetPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SourceRoot = Resolve-Path -LiteralPath $RiftboundPath
$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$SourceTools = Join-Path $SourceRoot "Tools"
$TargetTools = Join-Path $TargetRoot "tools"
$ReferenceTools = Join-Path $TargetTools "upstream-riftbound"

Write-Host "==> maintainer upgrade from Riftbound"
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"

if (-not (Test-Path -LiteralPath $SourceTools)) {
    throw "Missing source Tools folder: $SourceTools"
}

if ($DryRun) {
    Write-Host "Would refresh upstream reference tools: $ReferenceTools"
} else {
    if (Test-Path -LiteralPath $ReferenceTools) {
        Remove-Item -LiteralPath $ReferenceTools -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path $ReferenceTools | Out-Null
    foreach ($child in Get-ChildItem -LiteralPath $SourceTools -Force) {
        Copy-Item -LiteralPath $child.FullName -Destination $ReferenceTools -Recurse -Force
    }
}

Write-Host "Riftbound tools were refreshed as a recursive reference tree."
Write-Host "Reusable source changes must be ported into categorized source tools explicitly, then cataloged in SCRIPTS.json and pipeline_featurelist.json."

if (-not $DryRun) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $TargetTools "documents\audit_docs.ps1")
}

Write-Host "Maintainer upgrade complete."
