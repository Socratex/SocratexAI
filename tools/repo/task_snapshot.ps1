param(
    [string]$Root = "",
    [switch]$NoGit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-WorkTreeRoot {
    param([string]$FallbackRoot)

    $gitRoot = @(git -C $FallbackRoot rev-parse --show-toplevel 2>$null)
    if ($LASTEXITCODE -eq 0 -and $gitRoot.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$gitRoot[0])) {
        return (Resolve-Path -LiteralPath ([string]$gitRoot[0])).Path
    }
    return (Resolve-Path -LiteralPath $FallbackRoot).Path
}

$packageRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$Root = if ([string]::IsNullOrWhiteSpace($Root)) {
    Resolve-WorkTreeRoot -FallbackRoot $packageRoot
} else {
    (Resolve-Path -LiteralPath $Root).Path
}

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

    foreach ($file in @("DOCS.json", "STATE.json", "_PLAN.json", "TODO.json", "BUGS.json", "STATE.md", "_PLAN.md", "TODO.md", "ISSUES.md")) {
        if (Test-Path -LiteralPath $file) {
            $lineCount = @(Get-Content -LiteralPath $file).Count
            Write-Host "${file}: $lineCount line(s)"
        }
    }
} finally {
    Pop-Location
}
