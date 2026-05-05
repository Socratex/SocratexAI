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
    Get-ChildItem -LiteralPath $SourceTools -File | ForEach-Object {
        Copy-Item -LiteralPath $_.FullName -Destination $ReferenceTools -Force
    }
}

$existingToolNames = @(Get-ChildItem -LiteralPath $TargetTools -File | ForEach-Object Name)
Get-ChildItem -LiteralPath $SourceTools -File | ForEach-Object {
    if ($existingToolNames -contains $_.Name) {
        return
    }
    if ($DryRun) {
        Write-Host "Would import new tool: $($_.Name)"
    } else {
        Copy-Item -LiteralPath $_.FullName -Destination $TargetTools -Force
        Write-Host "Imported new tool: $($_.Name)"
    }
}

if (-not $DryRun) {
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $TargetTools "audit_docs.ps1")
}

Write-Host "Maintainer upgrade complete."
