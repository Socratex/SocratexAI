param(
    [string]$Path = "docs-tech\cache\current_task.json",
    [string]$Title = "TBD",
    [string]$SourceRequest = "TBD",
    [switch]$Force,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
. (Join-Path $repoRoot "tools\text\utf8_file_helpers.ps1")
$targetPath = Join-Path $repoRoot $Path
$templatePath = Join-Path $repoRoot "templates\code\current_task.json"

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
Write-Utf8File -Path $targetPath -Value $content -NoNewline
Write-Host "Created task work file: $targetPath"
