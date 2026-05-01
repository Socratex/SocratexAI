param(
    [string]$Branch,
    [string]$BranchFilesDir = "ignored/ai-socratex",
    [string]$TemplateDir,
    [switch]$EnsureGitignore,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
if (-not $TemplateDir) {
    $TemplateDir = Join-Path $repoRoot "templates\code\branch"
}

if (-not $Branch) {
    $detected = git branch --show-current 2>$null
    $Branch = if ($LASTEXITCODE -eq 0 -and $detected) { $detected.Trim() } else { "unknown-branch" }
}

$safeBranch = ($Branch -replace '[\\/:*?"<>|]', '-').Trim()
if (-not $safeBranch) {
    $safeBranch = "unknown-branch"
}

$targetDir = Join-Path $repoRoot $BranchFilesDir
$statePath = Join-Path $targetDir "$safeBranch-STATE.md"
$planPath = Join-Path $targetDir "$safeBranch-PLAN.md"
$todoPath = Join-Path $targetDir "TODO.md"

function Copy-BranchTemplate {
    param(
        [string]$TemplateName,
        [string]$Destination
    )

    $source = Join-Path $TemplateDir $TemplateName
    if (-not (Test-Path -LiteralPath $source)) {
        throw "Missing branch template: $source"
    }

    if ($DryRun) {
        Write-Host "Would create: $Destination"
        return
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Destination) | Out-Null
    if (-not (Test-Path -LiteralPath $Destination)) {
        Copy-Item -LiteralPath $source -Destination $Destination
    }
}

function Ensure-IgnoredDirectory {
    $gitignorePath = Join-Path $repoRoot ".gitignore"
    $comment = "# AI working files in user's prompt language - local-only, not for review"
    $ignoredLine = "/ignored"

    if ($DryRun) {
        Write-Host "Would ensure .gitignore contains: $ignoredLine"
        return
    }

    if (-not (Test-Path -LiteralPath $gitignorePath)) {
        Set-Content -LiteralPath $gitignorePath -Value "$comment`n$ignoredLine`n" -NoNewline
        return
    }

    $content = Get-Content -Raw -LiteralPath $gitignorePath
    $changed = $false
    if ($content -notmatch '(?m)^# AI working files in user''s prompt language - local-only, not for review$') {
        $content = $content.TrimEnd() + "`n$comment`n"
        $changed = $true
    }
    if ($content -notmatch '(?m)^/ignored/?$') {
        $content = $content.TrimEnd() + "`n$ignoredLine`n"
        $changed = $true
    }
    if ($changed) {
        Set-Content -LiteralPath $gitignorePath -Value $content -NoNewline
    }
}

if ($EnsureGitignore) {
    Ensure-IgnoredDirectory
}

Copy-BranchTemplate -TemplateName "BRANCH-STATE.md" -Destination $statePath
Copy-BranchTemplate -TemplateName "BRANCH-PLAN.md" -Destination $planPath
Copy-BranchTemplate -TemplateName "BRANCH-TODO.md" -Destination $todoPath

Write-Host "Branch memory ready:"
Write-Host "  state: $statePath"
Write-Host "  plan:  $planPath"
Write-Host "  todo:  $todoPath"
