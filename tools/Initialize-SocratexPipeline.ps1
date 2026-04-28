param(
    [string]$ProjectName = "Initialized SocratexPipeline Project",
    [string]$Language = "English",
    [ValidateSet("Lite", "Standard", "Enterprise")]
    [string]$AiMode = "Standard",
    [string]$FirstTarget = "TBD",
    [string]$FirstSessionSuccess = "TBD",
    [string]$UseGit = "TBD",
    [string]$AiMayCommit = "TBD",
    [string]$AiMayPush = "TBD",
    [string]$BranchWorkflow = "TBD",
    [string]$ExternalChangesPossible = "TBD",
    [string]$ForceDddAdiv = "TBD",
    [string]$ImportPipelinePackage = "TBD",
    [string]$PackageManagerDetection = "TBD",
    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",
    [string[]]$KeepPacks = @("generic"),
    [switch]$CreateFiles,
    [switch]$CompileAgent,
    [switch]$RunAudit,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$InstallRoot = Join-Path $Root "SocratexAI"
$ProjectDir = Join-Path $Root "project"
$TemplateDir = Join-Path $Root "templates"
$TrashDir = Join-Path $Root "temp\trash"
$TrashProjectDir = Join-Path $TrashDir "project"
$InitializerDir = Join-Path $Root "initializer"
$TrashInitializerDir = Join-Path $TrashDir "initializer"

New-Item -ItemType Directory -Force -Path $TrashProjectDir | Out-Null
New-Item -ItemType Directory -Force -Path $TrashDir | Out-Null

$allPacks = Get-ChildItem -Path $ProjectDir -Directory
$normalizedPacks = @()
foreach ($pack in $KeepPacks) {
    $normalizedPacks += ($pack -split "," | ForEach-Object { $_.Trim() } | Where-Object { $_ })
}
$KeepPacks = $normalizedPacks

$keep = @{}
foreach ($pack in $KeepPacks) {
    $keep[$pack.ToLowerInvariant()] = $true
}

$knownPacks = @{}
foreach ($packDir in (Get-ChildItem -Path $ProjectDir -Directory)) {
    $knownPacks[$packDir.Name.ToLowerInvariant()] = $true
}

foreach ($pack in $KeepPacks) {
    if (-not $knownPacks.ContainsKey($pack.ToLowerInvariant())) {
        throw "Unknown project pack: $pack"
    }
}

function Copy-TemplateFile {
    param(
        [string]$TemplateName,
        [string]$DestinationRelativePath
    )

    $source = Join-Path $TemplateDir $TemplateName
    $destination = Join-Path $InstallRoot $DestinationRelativePath
    $destinationParent = Split-Path -Parent $destination

    if ($DryRun) {
        Write-Output "Would copy template: $source -> $destination"
        return
    }

    New-Item -ItemType Directory -Force -Path $destinationParent | Out-Null
    if (-not (Test-Path $destination)) {
        Copy-Item -LiteralPath $source -Destination $destination
    }
}

function Copy-CodeTemplateFile {
    param(
        [string]$TemplateName,
        [string]$DestinationRelativePath
    )

    Copy-TemplateFile -TemplateName (Join-Path "code" $TemplateName) -DestinationRelativePath $DestinationRelativePath
}

function Set-TemplateValue {
    param(
        [string]$RelativePath,
        [hashtable]$Values
    )

    $destination = Join-Path $Root $RelativePath
    if ($DryRun) {
        Write-Output "Would update template values in: $destination"
        return
    }

    if (-not (Test-Path -LiteralPath $destination)) {
        return
    }

    $content = Get-Content -Raw -LiteralPath $destination
    foreach ($key in $Values.Keys) {
        $content = $content.Replace($key, [string]$Values[$key])
    }
    Set-Content -LiteralPath $destination -Value $content -NoNewline
}

if ($CreateFiles) {
    if ($DryRun) {
        Write-Output "Would copy root controller: $(Join-Path $TemplateDir 'SOCRATEX.md') -> $(Join-Path $Root 'SOCRATEX.md')"
    } else {
        Copy-Item -LiteralPath (Join-Path $TemplateDir "SOCRATEX.md") -Destination (Join-Path $Root "SOCRATEX.md") -Force
    }

    if ($keep.ContainsKey("code")) {
        Copy-CodeTemplateFile -TemplateName "STATE.yaml" -DestinationRelativePath "STATE.yaml"
        Copy-CodeTemplateFile -TemplateName "_PLAN.yaml" -DestinationRelativePath "_PLAN.yaml"
        Copy-CodeTemplateFile -TemplateName "DECISIONS.yaml" -DestinationRelativePath "DECISIONS.yaml"
        Copy-CodeTemplateFile -TemplateName "PIPELINE-CONFIG.yaml" -DestinationRelativePath "PIPELINE-CONFIG.yaml"
    } else {
        Copy-TemplateFile -TemplateName "STATE.md" -DestinationRelativePath "STATE.md"
        Copy-TemplateFile -TemplateName "_PLAN.md" -DestinationRelativePath "_PLAN.md"
        Copy-TemplateFile -TemplateName "DECISIONS.md" -DestinationRelativePath "DECISIONS.md"
        Copy-TemplateFile -TemplateName "JOURNAL.md" -DestinationRelativePath "JOURNAL.md"
        Copy-TemplateFile -TemplateName "REVIEW.md" -DestinationRelativePath "REVIEW.md"
        Copy-TemplateFile -TemplateName "PIPELINE-CONFIG.md" -DestinationRelativePath "PIPELINE-CONFIG.md"
    }

    if ($keep.ContainsKey("code") -and $AiMode -ne "Lite") {
        Copy-TemplateFile -TemplateName "_INSTRUCTIONS.md" -DestinationRelativePath "_INSTRUCTIONS.md"
        Copy-CodeTemplateFile -TemplateName "_INSTRUCTION-QUEUE.yaml" -DestinationRelativePath "_INSTRUCTION-QUEUE.yaml"
        Copy-CodeTemplateFile -TemplateName "TODO.yaml" -DestinationRelativePath "TODO.yaml"
        Copy-CodeTemplateFile -TemplateName "BUGS.yaml" -DestinationRelativePath "BUGS.yaml"
        Copy-CodeTemplateFile -TemplateName "BUGS-SOLVED.yaml" -DestinationRelativePath "BUGS-SOLVED.yaml"
        Copy-CodeTemplateFile -TemplateName "CHANGELOG.yaml" -DestinationRelativePath "CHANGELOG.yaml"
        Copy-CodeTemplateFile -TemplateName "context-docs\TECHNICAL.yaml" -DestinationRelativePath "context-docs\TECHNICAL.yaml"
        Copy-CodeTemplateFile -TemplateName "context-docs\FROZEN_LAYERS.yaml" -DestinationRelativePath "context-docs\FROZEN_LAYERS.yaml"
        Copy-TemplateFile -TemplateName "logs-.gitkeep" -DestinationRelativePath "logs\.gitkeep"
    } elseif ($keep.ContainsKey("code")) {
        Copy-CodeTemplateFile -TemplateName "TODO.yaml" -DestinationRelativePath "TODO.yaml"
        Copy-CodeTemplateFile -TemplateName "CHANGELOG.yaml" -DestinationRelativePath "CHANGELOG.yaml"
    }

    if ($keep.ContainsKey("generic") -or $keep.ContainsKey("personal") -or $keep.ContainsKey("creative")) {
        Copy-TemplateFile -TemplateName "BACKLOG.md" -DestinationRelativePath "BACKLOG.md"
        Copy-TemplateFile -TemplateName "ISSUES.md" -DestinationRelativePath "ISSUES.md"
    }

    Set-TemplateValue -RelativePath "PIPELINE-CONFIG.md" -Values @{
        "TBD." = "TBD."
        "TBD" = "TBD"
    }

    if (-not $DryRun -and (Test-Path -LiteralPath (Join-Path $InstallRoot "PIPELINE-CONFIG.md"))) {
        $config = @"
# Pipeline Config

## Summary

Initialized project configuration for SocratexPipeline.

## Language

$Language

## Active Project Packs

$([string]::Join(", ", $KeepPacks))

## AI Operating Mode

$AiMode

## Git

$UseGit

## First Target

$FirstTarget

## First-Session Success Criteria

$FirstSessionSuccess

"@
        Set-Content -LiteralPath (Join-Path $InstallRoot "PIPELINE-CONFIG.md") -Value $config -NoNewline
    }

    if (-not $DryRun -and (Test-Path -LiteralPath (Join-Path $InstallRoot "PIPELINE-CONFIG.yaml"))) {
        $packLines = ($KeepPacks | ForEach-Object { "  - $_" }) -join [Environment]::NewLine
        $configYaml = @"
summary: Initialized project configuration for SocratexPipeline.
language: $Language
active_project_packs:
$packLines
ai_operating_mode: $AiMode
git: $UseGit
ai_may_commit: $AiMayCommit
ai_may_push: $AiMayPush
branch_workflow: $BranchWorkflow
external_changes_possible: $ExternalChangesPossible
force_ddd_adiv: $ForceDddAdiv
import_pipeline_package: $ImportPipelinePackage
package_manager_detection: $PackageManagerDetection
directive_mode: $DirectiveMode
first_target: $FirstTarget
first_session_success_criteria: $FirstSessionSuccess
"@
        Set-Content -LiteralPath (Join-Path $InstallRoot "PIPELINE-CONFIG.yaml") -Value $configYaml -NoNewline
    }
}

$readmePath = Join-Path $Root "README.md"
if ($DryRun) {
    Write-Output "Would set project name in README.md to: $ProjectName"
} else {
    $readme = Get-Content -Raw -LiteralPath $readmePath
    $readme = $readme -replace "# SocratexPipeline", "# $ProjectName"
    Set-Content -LiteralPath $readmePath -Value $readme -NoNewline
}

foreach ($packDir in $allPacks) {
    if (-not $keep.ContainsKey($packDir.Name.ToLowerInvariant())) {
        $target = Join-Path $TrashProjectDir $packDir.Name
        if ($DryRun) {
            Write-Output "Would move project pack: $($packDir.FullName) -> $target"
        } else {
            if (Test-Path $target) {
                Remove-Item -LiteralPath $target -Recurse -Force
            }
            Move-Item -LiteralPath $packDir.FullName -Destination $target
        }
    }
}

if (Test-Path $InitializerDir) {
    if ($DryRun) {
        Write-Output "Would move initializer: $InitializerDir -> $TrashInitializerDir"
    } else {
        if (Test-Path $TrashInitializerDir) {
            Remove-Item -LiteralPath $TrashInitializerDir -Recurse -Force
        }
        Move-Item -LiteralPath $InitializerDir -Destination $TrashInitializerDir
    }
}

if ($CompileAgent) {
    if ($DryRun) {
        Write-Output "Would compile AGENTS.md for packs: $([string]::Join(', ', $KeepPacks))"
    } else {
        & (Join-Path $PSScriptRoot "compile_agent_instructions.ps1") -Packs $KeepPacks -OutputPath "AGENTS.md"
    }
}

if ($RunAudit -and $keep.ContainsKey("code")) {
    if ($DryRun) {
        Write-Output "Would run initialized code audit."
    } else {
        & (Join-Path $PSScriptRoot "audit_docs.ps1") -Initialized
    }
}

Write-Output "Initialization cleanup complete."
Write-Output "Recommended next improvements: configure quality gate command, Git convention, CI integration, frozen layer candidates, and domain-specific context capsules."
