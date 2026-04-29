param(
    [Parameter(Mandatory = $true)]
    [string]$Message,

    [Parameter(Mandatory = $true)]
    [string[]]$Paths,

    [switch]$NoVerify,

    [switch]$NoPush
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

Push-Location -LiteralPath $Root
try {
    if (-not (Test-Path -LiteralPath ".git")) {
        throw "This project is not a Git repository."
    }

    Write-Host "==> git status before staging"
    git status --short

    foreach ($path in $Paths) {
        if (-not (Test-Path -LiteralPath $path)) {
            throw "Cannot stage missing path: $path"
        }
    }

    Write-Host "==> staging explicit paths"
    git add -- $Paths

    Write-Host "==> staged diff"
    git diff --cached --stat

    if (-not $NoVerify) {
        Write-Host "==> git diff --cached --check"
        git diff --cached --check
    }

    Write-Host "==> committing"
    git commit -m $Message
    if ($LASTEXITCODE -ne 0) {
        throw "git commit failed with exit code $LASTEXITCODE"
    }

    if (-not $NoPush) {
        Write-Host "==> pushing"
        git push origin HEAD
        if ($LASTEXITCODE -ne 0) {
            throw "git push failed with exit code $LASTEXITCODE"
        }
    }

    Write-Host "==> final repository state"
    $remaining = @(git status --short)
    if ($remaining.Count -eq 0) {
        Write-Host "OK: working tree clean; subtask closed."
    } else {
        Write-Host "WARN: working tree still has changes; subtask not fully closed."
        foreach ($line in $remaining) {
            Write-Host $line
        }
    }
} finally {
    Pop-Location
}
