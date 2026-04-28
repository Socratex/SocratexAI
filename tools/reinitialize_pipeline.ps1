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
$ConfigPath = Join-Path $InstallRoot "PIPELINE-CONFIG.yaml"

function Read-ConfigText {
    if (Test-Path -LiteralPath $ConfigPath) {
        return Get-Content -Raw -LiteralPath $ConfigPath
    }
    return ""
}

function Get-ConfigScalar {
    param(
        [string]$Text,
        [string]$Key,
        [string]$Default
    )

    if ($Text -match "(?m)^\s*$([regex]::Escape($Key)):\s*(.+?)\s*$") {
        return $Matches[1].Trim().Trim('"').Trim("'")
    }
    return $Default
}

function Get-ConfigList {
    param([string]$Text)

    $result = New-Object System.Collections.Generic.List[string]
    $lines = $Text -split "`r?`n"
    $inPacks = $false
    foreach ($line in $lines) {
        if ($line -match '^active_project_packs:\s*$') {
            $inPacks = $true
            continue
        }
        if ($inPacks -and $line -match '^\S') {
            break
        }
        if ($inPacks -and $line -match '^\s*-\s*(.+?)\s*$') {
            $result.Add($Matches[1].Trim()) | Out-Null
        }
    }
    return @($result)
}

function Get-ChangelogEnabled {
    param([string]$Text)

    if ($UseChangelog -ne "auto") {
        return $UseChangelog -eq "yes"
    }
    if ($Text -match "(?ms)^changelog:\s*\r?\n\s+enabled:\s*(.+?)\s*(\r?\n\S|$)") {
        $value = $Matches[1].Trim().Trim('"').Trim("'").ToLowerInvariant()
        return $value -notin @("no", "false", "disabled", "off")
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

    $updated = $Text
    if ($updated -notmatch "(?m)^changelog:\s*$") {
        $enabledText = if ($ChangelogEnabled) { "yes" } else { "no" }
        $updated = $updated.TrimEnd() + "`nchangelog:`n  enabled: $enabledText`n"
    }
    if ($updated -notmatch "(?m)^\s+reinitialize_command:\s*") {
        $updated = $updated -replace "(?m)^(\s+remove_command:\s*.+)$", "`$1`n  reinitialize_command: powershell -NoProfile -ExecutionPolicy Bypass -File SocratexAI/tools/reinitialize_pipeline.ps1 -TargetPath ."
    }

    if ($updated -ne $Text) {
        if ($DryRun) {
            Write-Host "Would update PIPELINE-CONFIG.yaml with missing reinitialization defaults."
            return
        }
        Set-Content -LiteralPath $ConfigPath -Value $updated -NoNewline
        Write-Host "Updated PIPELINE-CONFIG.yaml with missing reinitialization defaults."
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

foreach ($pack in $Packs) {
    if ($pack -eq "code") {
        Ensure-Template -TemplateRelativePath "code/STATE.yaml" -DestinationRelativePath "STATE.yaml"
        Ensure-Template -TemplateRelativePath "code/_PLAN.yaml" -DestinationRelativePath "_PLAN.yaml"
        Ensure-Template -TemplateRelativePath "code/DECISIONS.yaml" -DestinationRelativePath "DECISIONS.yaml"
        Ensure-Template -TemplateRelativePath "code/PIPELINE-CONFIG.yaml" -DestinationRelativePath "PIPELINE-CONFIG.yaml"
        Ensure-Template -TemplateRelativePath "code/TODO.yaml" -DestinationRelativePath "TODO.yaml"
        Ensure-Template -TemplateRelativePath "code/BUGS.yaml" -DestinationRelativePath "BUGS.yaml"
        Ensure-Template -TemplateRelativePath "code/BUGS-SOLVED.yaml" -DestinationRelativePath "BUGS-SOLVED.yaml"
        Ensure-Template -TemplateRelativePath "code/_PROMPT-QUEUE.yaml" -DestinationRelativePath "_PROMPT-QUEUE.yaml"
        Ensure-Template -TemplateRelativePath "code/_INSTRUCTION-QUEUE.yaml" -DestinationRelativePath "_INSTRUCTION-QUEUE.yaml"
        Ensure-Template -TemplateRelativePath "code/current_task.yaml" -DestinationRelativePath "docs-tech/cache/current_task.yaml"
        Ensure-Template -TemplateRelativePath "code/context-docs/TECHNICAL.yaml" -DestinationRelativePath "context-docs/TECHNICAL.yaml"
        Ensure-Template -TemplateRelativePath "code/context-docs/FROZEN_LAYERS.yaml" -DestinationRelativePath "context-docs/FROZEN_LAYERS.yaml"
        if ($changelogEnabled) {
            Ensure-Template -TemplateRelativePath "code/CHANGELOG.yaml" -DestinationRelativePath "CHANGELOG.yaml"
        }
    } else {
        Ensure-Template -TemplateRelativePath "STATE.yaml" -DestinationRelativePath "STATE.yaml"
        Ensure-Template -TemplateRelativePath "_PLAN.yaml" -DestinationRelativePath "_PLAN.yaml"
        Ensure-Template -TemplateRelativePath "DECISIONS.yaml" -DestinationRelativePath "DECISIONS.yaml"
        Ensure-Template -TemplateRelativePath "BACKLOG.yaml" -DestinationRelativePath "BACKLOG.yaml"
        Ensure-Template -TemplateRelativePath "ISSUES.yaml" -DestinationRelativePath "ISSUES.yaml"
        Ensure-Template -TemplateRelativePath "JOURNAL.yaml" -DestinationRelativePath "JOURNAL.yaml"
        Ensure-Template -TemplateRelativePath "REVIEW.yaml" -DestinationRelativePath "REVIEW.yaml"
        Ensure-Template -TemplateRelativePath "PIPELINE-CONFIG.yaml" -DestinationRelativePath "PIPELINE-CONFIG.yaml"
    }
}

Write-Host "Reinitialization complete. Existing project memory was preserved."
