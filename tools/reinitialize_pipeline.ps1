param(
    [string]$TargetPath = ".",
    [string[]]$Packs = @(),
    [ValidateSet("yes", "no", "auto")]
    [string]$UseChangelog = "auto",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$InstallRoot = Join-Path $TargetRoot "SocratexAI"
$TemplateRoot = Join-Path $InstallRoot "templates"
$ConfigPath = Join-Path $InstallRoot "PIPELINE-CONFIG.json"

function Read-ConfigText {
    if (Test-Path -LiteralPath $ConfigPath) {
        return Get-Content -Raw -LiteralPath $ConfigPath
    }
    return ""
}

function Get-ConfigList {
    param([string]$Text)

    if ([string]::IsNullOrWhiteSpace($Text)) {
        return @()
    }
    try {
        $config = $Text | ConvertFrom-Json
        if ($config.active_project_packs) {
            return @($config.active_project_packs | ForEach-Object { [string]$_ })
        }
    } catch {
        return @()
    }
    return @()
}

function Get-ChangelogEnabled {
    param([string]$Text)

    if ($UseChangelog -ne "auto") {
        return $UseChangelog -eq "yes"
    }
    try {
        $config = $Text | ConvertFrom-Json
        if ($config.changelog -and $null -ne $config.changelog.enabled) {
            $value = ([string]$config.changelog.enabled).ToLowerInvariant()
            return $value -notin @("no", "false", "disabled", "off")
        }
    } catch {
        return $true
    }
    return $true
}

function Ensure-Directory {
    param([string]$Path)

    if ($DryRun) {
        Write-Host "Would ensure directory: $Path"
        return
    }
    New-Item -ItemType Directory -Force -Path $Path | Out-Null
}

function Ensure-Template {
    param(
        [string]$TemplateRelativePath,
        [string]$DestinationRelativePath
    )

    $source = Join-Path $TemplateRoot $TemplateRelativePath
    $destination = Join-Path $InstallRoot $DestinationRelativePath
    if (-not (Test-Path -LiteralPath $source)) {
        Write-Host "Skipped missing template: $TemplateRelativePath"
        return
    }
    if (Test-Path -LiteralPath $destination) {
        return
    }
    if ($DryRun) {
        Write-Host "Would create missing initialized file: $destination"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $source -Destination $destination
    Write-Host "Created missing initialized file: $DestinationRelativePath"
}

function Ensure-ConfigDefaults {
    param(
        [string]$Text,
        [bool]$ChangelogEnabled
    )

    if (-not (Test-Path -LiteralPath $ConfigPath)) {
        return
    }

    try {
        $config = if ([string]::IsNullOrWhiteSpace($Text)) { [pscustomobject]@{} } else { $Text | ConvertFrom-Json }
    } catch {
        throw "PIPELINE-CONFIG.json is not valid JSON."
    }

    $changed = $false
    if (-not $config.PSObject.Properties.Name.Contains("changelog")) {
        $config | Add-Member -NotePropertyName "changelog" -NotePropertyValue ([pscustomobject]@{ enabled = $(if ($ChangelogEnabled) { "yes" } else { "no" }) })
        $changed = $true
    }
    if (-not $config.PSObject.Properties.Name.Contains("communication")) {
        $config | Add-Member -NotePropertyName "communication" -NotePropertyValue ([pscustomobject]@{ profile = "standard" })
        $changed = $true
    }
    if (-not $config.PSObject.Properties.Name.Contains("pipeline")) {
        $config | Add-Member -NotePropertyName "pipeline" -NotePropertyValue ([pscustomobject]@{})
        $changed = $true
    }
    if (-not $config.pipeline.PSObject.Properties.Name.Contains("reinitialize_command")) {
        $config.pipeline | Add-Member -NotePropertyName "reinitialize_command" -NotePropertyValue "powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/reinitialize_pipeline.ps1 -TargetPath ."
        $changed = $true
    }

    if ($changed) {
        if ($DryRun) {
            Write-Host "Would update PIPELINE-CONFIG.json with missing reinitialization defaults."
            return
        }
        [System.IO.File]::WriteAllText($ConfigPath, (($config | ConvertTo-Json -Depth 8) + [Environment]::NewLine), [System.Text.UTF8Encoding]::new($false))
        Write-Host "Updated PIPELINE-CONFIG.json with missing reinitialization defaults."
    }
}

if (-not (Test-Path -LiteralPath $InstallRoot)) {
    throw "Missing SocratexAI install root: $InstallRoot"
}
if (-not (Test-Path -LiteralPath $TemplateRoot)) {
    throw "Missing SocratexAI templates root: $TemplateRoot"
}

$configText = Read-ConfigText
if ($Packs.Count -eq 0) {
    $Packs = Get-ConfigList -Text $configText
}
if ($Packs.Count -eq 0) {
    $Packs = @("code")
}
$changelogEnabled = Get-ChangelogEnabled -Text $configText

Write-Host "==> reinitializing missing SocratexAI artifacts only"
Write-Host "Target: $TargetRoot"
Write-Host "Packs: $([string]::Join(', ', $Packs))"
Write-Host "Changelog enabled: $changelogEnabled"

Ensure-ConfigDefaults -Text $configText -ChangelogEnabled $changelogEnabled

Ensure-Template -TemplateRelativePath "WORKFLOW.json" -DestinationRelativePath "WORKFLOW.json"
Ensure-Template -TemplateRelativePath "team/product.json" -DestinationRelativePath "team/product.json"
Ensure-Template -TemplateRelativePath "team/technical.json" -DestinationRelativePath "team/technical.json"
Ensure-Template -TemplateRelativePath "team/performance.json" -DestinationRelativePath "team/performance.json"
Ensure-Template -TemplateRelativePath "team/experience.json" -DestinationRelativePath "team/experience.json"
Ensure-Template -TemplateRelativePath "team/pipeline.json" -DestinationRelativePath "team/pipeline.json"
Ensure-Template -TemplateRelativePath "docs-tech/KNOWLEDGE-VIEWS.json" -DestinationRelativePath "docs-tech/KNOWLEDGE-VIEWS.json"

foreach ($pack in $Packs) {
    if ($pack -eq "code") {
        Ensure-Template -TemplateRelativePath "code/DOCS.json" -DestinationRelativePath "DOCS.json"
        Ensure-Template -TemplateRelativePath "code/STATE.json" -DestinationRelativePath "STATE.json"
        Ensure-Template -TemplateRelativePath "code/_PLAN.json" -DestinationRelativePath "_PLAN.json"
        Ensure-Template -TemplateRelativePath "code/DECISIONS.json" -DestinationRelativePath "DECISIONS.json"
        Ensure-Template -TemplateRelativePath "code/PIPELINE-CONFIG.json" -DestinationRelativePath "PIPELINE-CONFIG.json"
        Ensure-Template -TemplateRelativePath "code/TODO.json" -DestinationRelativePath "TODO.json"
        Ensure-Template -TemplateRelativePath "code/BUGS.json" -DestinationRelativePath "BUGS.json"
        Ensure-Template -TemplateRelativePath "code/BUGS-SOLVED.json" -DestinationRelativePath "BUGS-SOLVED.json"
        Ensure-Template -TemplateRelativePath "code/_PROMPT-QUEUE.json" -DestinationRelativePath "_PROMPT-QUEUE.json"
        Ensure-Template -TemplateRelativePath "code/_INSTRUCTION-QUEUE.json" -DestinationRelativePath "_INSTRUCTION-QUEUE.json"
        Ensure-Template -TemplateRelativePath "code/current_task.json" -DestinationRelativePath "docs-tech/cache/current_task.json"
        Ensure-Template -TemplateRelativePath "code/context-docs/ENGINEERING.json" -DestinationRelativePath "context-docs/ENGINEERING.json"
        Ensure-Template -TemplateRelativePath "code/context-docs/TECHNICAL.json" -DestinationRelativePath "context-docs/TECHNICAL.json"
        Ensure-Template -TemplateRelativePath "code/context-docs/FROZEN_LAYERS.json" -DestinationRelativePath "context-docs/FROZEN_LAYERS.json"
        if ($changelogEnabled) {
            Ensure-Template -TemplateRelativePath "code/CHANGELOG.json" -DestinationRelativePath "CHANGELOG.json"
        }
    } else {
        Ensure-Template -TemplateRelativePath "DOCS.json" -DestinationRelativePath "DOCS.json"
        Ensure-Template -TemplateRelativePath "STATE.md" -DestinationRelativePath "STATE.md"
        Ensure-Template -TemplateRelativePath "_PLAN.md" -DestinationRelativePath "_PLAN.md"
        Ensure-Template -TemplateRelativePath "DECISIONS.md" -DestinationRelativePath "DECISIONS.md"
        Ensure-Template -TemplateRelativePath "BACKLOG.md" -DestinationRelativePath "BACKLOG.md"
        Ensure-Template -TemplateRelativePath "ISSUES.md" -DestinationRelativePath "ISSUES.md"
        Ensure-Template -TemplateRelativePath "JOURNAL.md" -DestinationRelativePath "JOURNAL.md"
        Ensure-Template -TemplateRelativePath "REVIEW.md" -DestinationRelativePath "REVIEW.md"
        Ensure-Template -TemplateRelativePath "PIPELINE-CONFIG.json" -DestinationRelativePath "PIPELINE-CONFIG.json"
    }
}

if (-not $DryRun) {
    $syncFeatureListScript = Join-Path $InstallRoot "tools\sync_pipeline_featurelist.ps1"
    if (Test-Path -LiteralPath $syncFeatureListScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $TargetRoot
    }
    $knowledgeCompileScript = Join-Path $InstallRoot "tools\knowledge_compile.ps1"
    if (Test-Path -LiteralPath $knowledgeCompileScript) {
        & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
        if ($LASTEXITCODE -ne 0) {
            throw "knowledge_compile failed with exit code $LASTEXITCODE"
        }
    }
}

Write-Host "Reinitialization complete. Existing project memory was preserved."
