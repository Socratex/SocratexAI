param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [string]$TargetPath = ".",

    [ValidateSet("Auto", "LocalPath", "Zip", "Git")]
    [string]$SourceMode = "Auto",

    [string]$GitRef = "main",

    [string[]]$Packs = @("code"),

    [string]$Profile = "",

    [ValidateSet("snapshot", "merge", "replace")]
    [string]$DirectiveMode = "merge",

    [string[]]$DirectiveFiles = @("AGENTS.md"),

    [switch]$ReinitializeNew,

    [switch]$FullVerify,

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetRoot = Resolve-Path -LiteralPath $TargetPath
$InstallRoot = Join-Path $TargetRoot "SocratexAI"
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("socratex-pipeline-update-" + [guid]::NewGuid().ToString("N"))

function Resolve-PowerShellCommand {
    $pwsh = Get-Command "pwsh" -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }
    $powershell = Get-Command "powershell" -ErrorAction SilentlyContinue
    if ($powershell) {
        return $powershell.Source
    }
    $powershellExe = Get-Command "powershell.exe" -ErrorAction SilentlyContinue
    if ($powershellExe) {
        return $powershellExe.Source
    }
    throw "Neither pwsh nor powershell is available."
}

function Get-ConfigContent {
    param([object]$Config)

    if ($null -ne $Config -and
        $Config.PSObject.Properties.Name.Contains("content") -and
        $null -ne $Config.content) {
        return $Config.content
    }
    return $Config
}

function Resolve-ConfiguredProfile {
    param([string]$ConfigPath)

    if (-not [string]::IsNullOrWhiteSpace($Profile)) {
        return $Profile
    }
    if (-not (Test-Path -LiteralPath $ConfigPath -PathType Leaf)) {
        return ""
    }
    try {
        $config = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
        $content = Get-ConfigContent -Config $config
        if ($content.pipeline -and $content.pipeline.profile) {
            return [string]$content.pipeline.profile
        }
        if ($content.project_subcontext -and ([string]$content.project_subcontext).ToLowerInvariant() -eq "gamedev") {
            return "SocratexGamedev"
        }
    } catch {
        return ""
    }
    return ""
}

$PowerShellCommand = Resolve-PowerShellCommand

function Invoke-ExternalCommand {
    param(
        [string]$Command,
        [string[]]$Arguments
    )

    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Command $($Arguments -join ' ') failed with exit code $LASTEXITCODE"
    }
}

function Test-GitSource {
    param([string]$SourceValue)

    if ($SourceValue -match '^git\+') {
        return $true
    }
    if ($SourceValue -match '\.git(?:#.+)?$') {
        return $true
    }
    if ($SourceValue -match '^https?://github\.com/[^/]+/[^/]+/?(?:#.+)?$') {
        return $true
    }
    return $false
}

function Resolve-SourceRoot {
    param([string]$SourceValue)

    if ($SourceMode -eq "LocalPath" -or ($SourceMode -eq "Auto" -and (Test-Path -LiteralPath $SourceValue))) {
        return (Resolve-Path -LiteralPath $SourceValue).Path
    }

    New-Item -ItemType Directory -Force -Path $TempRoot | Out-Null

    if ($SourceMode -eq "Git" -or ($SourceMode -eq "Auto" -and (Test-GitSource -SourceValue $SourceValue))) {
        $repoUrl = $SourceValue -replace '^git\+', ''
        $refFromSource = ""
        if ($repoUrl.Contains("#")) {
            $hashIndex = $repoUrl.IndexOf("#", [System.StringComparison]::Ordinal)
            $refFromSource = $repoUrl.Substring($hashIndex + 1)
            $repoUrl = $repoUrl.Substring(0, $hashIndex)
        }
        $refToUse = if ([string]::IsNullOrWhiteSpace($refFromSource)) { $GitRef } else { $refFromSource }
        $cloneRoot = Join-Path $TempRoot "source"
        Invoke-ExternalCommand -Command "git" -Arguments @("clone", "--depth", "1", "--branch", $refToUse, $repoUrl, $cloneRoot)
        return $cloneRoot
    }

    $zipPath = Join-Path $TempRoot "pipeline.zip"
    Invoke-WebRequest -Uri $SourceValue -OutFile $zipPath
    Expand-Archive -LiteralPath $zipPath -DestinationPath $TempRoot -Force
    $candidates = @(Get-ChildItem -LiteralPath $TempRoot -Directory)
    if ($candidates.Count -eq 1) {
        return $candidates[0].FullName
    }
    return $TempRoot
}

$SourceRoot = Resolve-SourceRoot -SourceValue $Source
$ResolvedProfile = Resolve-ConfiguredProfile -ConfigPath (Join-Path $InstallRoot "PIPELINE-CONFIG.json")

Write-Host "==> updating SocratexPipeline"
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"
Write-Host "Install root: $InstallRoot"
if (-not [string]::IsNullOrWhiteSpace($ResolvedProfile)) {
    Write-Host "Project profile: $ResolvedProfile"
}

$syncPackageScript = Join-Path $SourceRoot "tools\pipeline\sync_managed_pipeline_package.ps1"
if (-not (Test-Path -LiteralPath $syncPackageScript)) {
    throw "Update source is missing required managed package sync script: $syncPackageScript"
}

$syncArgs = @(
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $syncPackageScript,
    "-SourceRoot",
    $SourceRoot,
    "-InstallRoot",
    $InstallRoot,
    "-ProjectRoot",
    $TargetRoot,
    "-PruneUnmanaged"
)
if (-not [string]::IsNullOrWhiteSpace($ResolvedProfile)) {
    $syncArgs += @("-Profile", $ResolvedProfile, "-ApplyProjectProfile")
}
if ($DryRun) {
    $syncArgs += "-DryRun"
}
& $PowerShellCommand @syncArgs
if ($LASTEXITCODE -ne 0) {
    throw "sync_managed_pipeline_package failed with exit code $LASTEXITCODE"
}

if (Test-Path -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md")) {
    if ($DryRun) {
        Write-Host "Would copy root controller: $(Join-Path $SourceRoot 'templates\SOCRATEX.md') -> $(Join-Path $TargetRoot 'SOCRATEX.md')"
    } else {
        Copy-Item -LiteralPath (Join-Path $SourceRoot "templates\SOCRATEX.md") -Destination (Join-Path $TargetRoot "SOCRATEX.md") -Force
    }
}

if (-not $DryRun) {
    if ($ReinitializeNew) {
        & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\pipeline\reinitialize_pipeline.ps1") -TargetPath $TargetRoot -Packs $Packs
        if ($LASTEXITCODE -ne 0) {
            throw "reinitialize_pipeline failed with exit code $LASTEXITCODE"
        }

        & $PowerShellCommand @syncArgs
        if ($LASTEXITCODE -ne 0) {
            throw "post-reinitialize sync_managed_pipeline_package failed with exit code $LASTEXITCODE"
        }
    }

    $syncFeatureListScript = Join-Path $InstallRoot "tools\repo\sync_pipeline_featurelist.ps1"
    if (Test-Path -LiteralPath $syncFeatureListScript) {
        & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File $syncFeatureListScript -TargetPath $TargetRoot
        if ($LASTEXITCODE -ne 0) {
            throw "sync_pipeline_featurelist failed with exit code $LASTEXITCODE"
        }
    }

    & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\pipeline\set_directives.ps1") -TargetPath $TargetRoot -Mode $DirectiveMode -DirectiveFiles $DirectiveFiles
    if ($LASTEXITCODE -ne 0) {
        throw "set_directives failed with exit code $LASTEXITCODE"
    }

    $featureContractCheckScript = Join-Path $InstallRoot "tools\repo\check_pipeline_feature_contracts.ps1"
    if (Test-Path -LiteralPath $featureContractCheckScript) {
        & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File $featureContractCheckScript
        if ($LASTEXITCODE -ne 0) {
            throw "check_pipeline_feature_contracts failed with exit code $LASTEXITCODE"
        }
    }

    if ($FullVerify) {
        $knowledgeCompileScript = Join-Path $InstallRoot "tools\knowledge\knowledge_compile.ps1"
        if (Test-Path -LiteralPath $knowledgeCompileScript) {
            & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File $knowledgeCompileScript
            if ($LASTEXITCODE -ne 0) {
                throw "knowledge_compile failed with exit code $LASTEXITCODE"
            }
        }
        & $PowerShellCommand -NoProfile -ExecutionPolicy Bypass -File (Join-Path $InstallRoot "tools\documents\audit_docs.ps1")
        if ($LASTEXITCODE -ne 0) {
            throw "audit_docs failed with exit code $LASTEXITCODE"
        }
    } else {
        Write-Host "Skipped full verification. Use -FullVerify to rebuild knowledge and run audit_docs."
    }
}

Write-Host "Pipeline update complete. SocratexAI is active for this project; future sessions should start from SOCRATEX.md."
