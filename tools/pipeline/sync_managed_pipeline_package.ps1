param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,

    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,

    [string[]]$ManagedPaths = @(
        ".gitignore",
        "AI-compiled",
        "adapters",
        "context-docs",
        "core",
        "docs",
        "docs-tech",
        "evals",
        "initializer",
        "learning",
        "project",
        "templates",
        "tools",
        "AGENTS.md",
        "CHANGELOG.json",
        "COMMANDS.json",
        "DOCS.json",
        "FLOWS.json",
        "LICENSE",
        "PUBLIC-BOOTSTRAP.md",
        "QUALITY-GATE.json",
        "README.md",
        "RECOMMENDATION.md",
        "SCRIPTS.json",
        "VERSION",
        "WORKFLOW.json",
        "pipeline_featurelist.json"
    ),

    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$installRootFull = [System.IO.Path]::GetFullPath($InstallRoot)

function Assert-ChildPath {
    param(
        [string]$Root,
        [string]$Path
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $pathFull.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside install root: $pathFull"
    }
}

function Copy-ExactManagedPath {
    param(
        [string]$RelativePath
    )

    $sourcePath = Join-Path $SourceRoot $RelativePath
    $destinationPath = Join-Path $installRootFull $RelativePath
    Assert-ChildPath -Root $installRootFull -Path $destinationPath

    if (-not (Test-Path -LiteralPath $sourcePath)) {
        Write-Host "Skipped missing managed source path: $RelativePath"
        return
    }

    if ($DryRun) {
        Write-Host "Would mirror managed path: $sourcePath -> $destinationPath"
        return
    }

    if (Test-Path -LiteralPath $destinationPath) {
        Remove-Item -LiteralPath $destinationPath -Recurse -Force
    }

    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationPath) | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Recurse -Force
    Write-Host "Mirrored managed path: $RelativePath"
}

if ($DryRun) {
    Write-Host "Would ensure install root: $installRootFull"
} else {
    New-Item -ItemType Directory -Force -Path $installRootFull | Out-Null
}

foreach ($path in $ManagedPaths) {
    if ([string]::IsNullOrWhiteSpace($path)) {
        continue
    }
    Copy-ExactManagedPath -RelativePath $path
}

Write-Host "OK: managed SocratexAI package sync complete."
