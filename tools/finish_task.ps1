param(
    [switch]$Quality,
    [string[]]$QualityCommand,
    [switch]$StrictAudit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location -LiteralPath $Root
try {
    Write-Host "==> finish task"

    & (Join-Path $PSScriptRoot "task_snapshot.ps1")

    if (Test-Path -LiteralPath ".git") {
        Write-Host ""
        Write-Host "==> git diff --check"
        git diff --check
    }

    Write-Host ""
    Write-Host "==> audit docs"
    if ($StrictAudit) {
        & (Join-Path $PSScriptRoot "audit_docs.ps1") -Strict
    } else {
        & (Join-Path $PSScriptRoot "audit_docs.ps1")
    }

    if ($Quality) {
        Write-Host ""
        if ($QualityCommand -and $QualityCommand.Count -gt 0) {
            & (Join-Path $PSScriptRoot "run_quality_gate.ps1") -Command $QualityCommand
        } else {
            & (Join-Path $PSScriptRoot "run_quality_gate.ps1")
        }
    }

    Write-Host "OK: finish task completed."
} finally {
    Pop-Location
}

