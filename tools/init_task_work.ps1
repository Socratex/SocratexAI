param(
    [string]$Path = "docs-tech\cache\current_task.yaml",
    [string]$Title = "TBD",
    [string]$SourceRequest = "TBD",
    [switch]$Force,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$targetPath = Join-Path $repoRoot $Path
$templatePath = Join-Path $repoRoot "templates\code\current_task.yaml"

if (-not (Test-Path -LiteralPath $templatePath)) {
    throw "Missing task work template: $templatePath"
}

if ((Test-Path -LiteralPath $targetPath) -and -not $Force) {
    Write-Host "Task work file already exists: $targetPath"
    exit 0
}

if ($DryRun) {
    Write-Host "Would create task work file: $targetPath"
    exit 0
}

New-Item -ItemType Directory -Force -Path (Split-Path -Parent $targetPath) | Out-Null
$content = Get-Content -Raw -LiteralPath $templatePath
$content = $content.Replace("title: TBD", "title: $Title")
$content = $content.Replace("source_request: TBD", "source_request: $SourceRequest")
Set-Content -LiteralPath $targetPath -Value $content -Encoding UTF8 -NoNewline
Write-Host "Created task work file: $targetPath"
