param(
    [string]$TargetPath = ".",

    [string[]]$LegacyDirectiveFiles = @("AGENTS.md", "CLAUDE.md", ".cursor\rules", ".github\copilot-instructions.md"),

    [string[]]$Packs = @("code"),

    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",

    [switch]$CreateProjectFiles,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$PipelineRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$TargetRoot = Resolve-Path -LiteralPath $TargetPath

Write-Host "==> migrating existing AI pipeline"
Write-Host "Target: $TargetRoot"
Write-Host "Mode: $DirectiveMode"

$existingDirectives = @()
foreach ($file in $LegacyDirectiveFiles) {
    if (Test-Path -LiteralPath (Join-Path $TargetRoot $file)) {
        $existingDirectives += $file
    }
}

if ($existingDirectives.Count -eq 0) {
    $existingDirectives = @("AGENTS.md")
}

if ($DryRun) {
    Write-Host "Would install packs: $($Packs -join ', ')"
    Write-Host "Would update directives: $($existingDirectives -join ', ')"
    exit 0
}

& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PipelineRoot "tools\import_existing_project.ps1") -TargetPath $TargetRoot -Packs $Packs -CreateProjectFiles:$CreateProjectFiles
& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $TargetRoot "SocratexAI\tools\set_directives.ps1") -TargetPath $TargetRoot -Mode $DirectiveMode -DirectiveFiles $existingDirectives

Write-Host "Migration complete. SocratexAI is now active for this project; future sessions should start from SOCRATEX.md."
Write-Host "Review SOCRATEX.md, any *.old directive files, and run SocratexAI/tools/audit_docs.ps1."
