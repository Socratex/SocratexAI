param(
    [switch]$NoGit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location -LiteralPath $Root
try {
    Write-Host "==> task snapshot"
    Write-Host "Root: $Root"

    if (-not $NoGit -and (Test-Path -LiteralPath ".git")) {
        Write-Host ""
        Write-Host "==> git branch"
        git branch --show-current

        Write-Host ""
        Write-Host "==> git status"
        git status --short
    }

    foreach ($file in @("STATE.yaml", "_PLAN.yaml", "TODO.yaml", "BUGS.yaml")) {
        if (Test-Path -LiteralPath $file) {
            $lineCount = @(Get-Content -LiteralPath $file).Count
            Write-Host "${file}: $lineCount line(s)"
        }
    }
} finally {
    Pop-Location
}
