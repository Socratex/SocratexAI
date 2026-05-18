param(
    [Parameter(Mandatory = $true)]
    [string]$SourceRoot,

    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,

    [string]$ProjectRoot = "",

    [string]$Profile = "",

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

    [string[]]$ChildGeneratedPaths = @(
        "AI-compiled/project",
        "docs-tech/cache",
        "ignored/code_context_gate.json"
    ),

    [string[]]$ProtectedPaths = @(
        "PIPELINE-CONFIG.json"
    ),

    [switch]$ApplyProjectProfile,
    [switch]$PruneUnmanaged,
    [switch]$ForceManaged,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SourceRoot = (Resolve-Path -LiteralPath $SourceRoot).Path
$installRootFull = [System.IO.Path]::GetFullPath($InstallRoot)
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
    $ProjectRoot = Split-Path -Parent $installRootFull
}
$projectRootFull = [System.IO.Path]::GetFullPath($ProjectRoot)
$manifestPath = Join-Path $installRootFull "PIPELINE-PACKAGE.json"

function Get-RelativePath {
    param(
        [string]$Root,
        [string]$Path
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    if ($pathFull -eq $rootFull) {
        return ""
    }
    $rootPrefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $pathFull.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is not under root: $pathFull"
    }
    return ($pathFull.Substring($rootPrefix.Length) -replace "\\", "/")
}

function Assert-ChildPath {
    param(
        [string]$Root,
        [string]$Path
    )

    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
    $pathFull = [System.IO.Path]::GetFullPath($Path)
    $rootPrefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if ($pathFull -ne $rootFull -and -not $pathFull.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to operate outside root: $pathFull"
    }
}

function Get-FileHashSha256 {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        return ""
    }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function ConvertTo-PathSet {
    param([string[]]$Paths)

    $set = @{}
    foreach ($path in $Paths) {
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }
        $set[($path -replace "\\", "/").Trim("/")] = $true
    }
    return $set
}

function Test-UnderAnyPath {
    param(
        [string]$RelativePath,
        [System.Collections.IDictionary]$PathSet
    )

    $normalized = ($RelativePath -replace "\\", "/").Trim("/")
    foreach ($path in $PathSet.Keys) {
        if ($normalized -eq $path -or $normalized.StartsWith("$path/", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Get-DictionaryKeys {
    param([object]$Value)

    if ($Value -is [System.Collections.IDictionary]) {
        return @($Value.Keys | ForEach-Object { [string]$_ })
    }
    return @()
}

function Read-PackageManifest {
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        return [ordered]@{
            metadata = [ordered]@{}
            managed_files = [ordered]@{}
            project_profile_files = [ordered]@{}
            local_overrides = @()
            preserved_unmanaged = @()
            removed_unmanaged = @()
        }
    }
    try {
        return Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -AsHashtable
    } catch {
        throw "Existing package manifest is not valid JSON: $manifestPath"
    }
}

function Write-PackageManifest {
    param([System.Collections.IDictionary]$Manifest)

    $Manifest["metadata"] = [ordered]@{
        package = "SocratexAI"
        schema = "socratex-pipeline-package/v1"
        source_root = $SourceRoot
        synced_at_utc = [System.DateTime]::UtcNow.ToString("o")
        profile = $Profile
        model = "source-managed package plus child additions and explicit overrides"
        child_generated_paths = @($ChildGeneratedPaths)
        protected_paths = @($ProtectedPaths)
    }

    $json = $Manifest | ConvertTo-Json -Depth 20
    if ($DryRun) {
        Write-Host "Would write package manifest: $manifestPath"
        return
    }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $manifestPath) | Out-Null
    [System.IO.File]::WriteAllText($manifestPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
}

function Get-SourceFilesForPath {
    param([string]$RelativePath)

    $sourcePath = Join-Path $SourceRoot $RelativePath
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        return @()
    }
    if (Test-Path -LiteralPath $sourcePath -PathType Leaf) {
        return @($sourcePath)
    }
    return @(
        Get-ChildItem -LiteralPath $sourcePath -File -Recurse |
            Where-Object {
                $relative = Get-RelativePath -Root $SourceRoot -Path $_.FullName
                -not ($relative -like ".git/*") -and -not ($relative -like ".agents/*") -and -not ($relative -like ".codex/*")
            } |
            Where-Object {
                $relative = Get-RelativePath -Root $SourceRoot -Path $_.FullName
                -not (Test-UnderAnyPath -RelativePath $relative -PathSet (ConvertTo-PathSet -Paths $ChildGeneratedPaths))
            } |
            ForEach-Object { $_.FullName }
    )
}

function Copy-ManagedFile {
    param(
        [string]$RelativePath,
        [System.Collections.IDictionary]$PreviousManaged,
        [System.Collections.IDictionary]$NewManaged,
        [System.Collections.Generic.List[string]]$LocalOverrides
    )

    $sourcePath = Join-Path $SourceRoot $RelativePath
    $destinationPath = Join-Path $installRootFull $RelativePath
    Assert-ChildPath -Root $installRootFull -Path $destinationPath

    $sourceHash = Get-FileHashSha256 -Path $sourcePath
    $destinationHash = Get-FileHashSha256 -Path $destinationPath
    $previousHash = ""
    if ($PreviousManaged.Contains($RelativePath)) {
        $previousEntry = $PreviousManaged[$RelativePath]
        if ($previousEntry -is [System.Collections.IDictionary] -and $previousEntry.Contains("hash")) {
            $previousHash = [string]$previousEntry["hash"]
        }
    }

    $hasLocalChange = $false
    if ($destinationHash -ne "" -and $destinationHash -ne $sourceHash) {
        if ($previousHash -eq "" -or $destinationHash -ne $previousHash) {
            $hasLocalChange = $true
        }
    }

    if ($hasLocalChange -and -not $ForceManaged) {
        $LocalOverrides.Add($RelativePath) | Out-Null
        return
    }

    if ($DryRun) {
        if ($destinationHash -eq $sourceHash) {
            Write-Host "Unchanged managed file: $RelativePath"
        } else {
            Write-Host "Would update managed file: $RelativePath"
        }
    } else {
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationPath) | Out-Null
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
    }

    $NewManaged[$RelativePath] = [ordered]@{
        hash = $sourceHash
        source = $RelativePath
    }
}

function Apply-ManagedPackage {
    param(
        [System.Collections.IDictionary]$PreviousManifest,
        [System.Collections.IDictionary]$NewManifest,
        [System.Collections.Generic.List[string]]$LocalOverrides
    )

    $previousManaged = @{}
    if ($PreviousManifest.Contains("managed_files") -and $PreviousManifest["managed_files"] -is [System.Collections.IDictionary]) {
        $previousManaged = $PreviousManifest["managed_files"]
    }
    $newManaged = [ordered]@{}

    foreach ($path in $ManagedPaths) {
        if ([string]::IsNullOrWhiteSpace($path)) {
            continue
        }
        foreach ($sourceFile in (Get-SourceFilesForPath -RelativePath $path)) {
            $relative = Get-RelativePath -Root $SourceRoot -Path $sourceFile
            Copy-ManagedFile -RelativePath $relative -PreviousManaged $previousManaged -NewManaged $newManaged -LocalOverrides $LocalOverrides
        }
    }

    $script:ManagedFilesForManifest = $newManaged
}

function Apply-ProjectProfile {
    param(
        [System.Collections.IDictionary]$PreviousManifest,
        [System.Collections.IDictionary]$NewManifest,
        [System.Collections.Generic.List[string]]$LocalOverrides
    )

    if (-not $ApplyProjectProfile -or [string]::IsNullOrWhiteSpace($Profile)) {
        $script:ProjectProfileFilesForManifest = [ordered]@{}
        return
    }

    $profileRoot = Join-Path $SourceRoot "profiles\$Profile"
    $profileConfig = Join-Path $profileRoot "PROFILE.json"
    if (-not (Test-Path -LiteralPath $profileConfig -PathType Leaf)) {
        throw "Unknown pipeline profile '$Profile': $profileConfig"
    }
    $profileData = Get-Content -LiteralPath $profileConfig -Raw | ConvertFrom-Json -AsHashtable
    $profilePaths = @()
    if ($profileData.Contains("content") -and $profileData["content"].Contains("managed_project_files")) {
        $profilePaths = @($profileData["content"]["managed_project_files"]["paths"])
    }

    $previousProfileFiles = @{}
    if ($PreviousManifest.Contains("project_profile_files") -and $PreviousManifest["project_profile_files"] -is [System.Collections.IDictionary]) {
        $previousProfileFiles = $PreviousManifest["project_profile_files"]
    }
    $newProfileFiles = [ordered]@{}

    foreach ($path in $profilePaths) {
        $relative = ([string]$path -replace "\\", "/").Trim("/")
        if ([string]::IsNullOrWhiteSpace($relative)) {
            continue
        }
        $sourcePath = Join-Path $profileRoot $relative
        $destinationPath = Join-Path $projectRootFull $relative
        Assert-ChildPath -Root $projectRootFull -Path $destinationPath
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Profile '$Profile' is missing managed project file: $relative"
        }

        $sourceHash = Get-FileHashSha256 -Path $sourcePath
        $destinationHash = Get-FileHashSha256 -Path $destinationPath
        $previousHash = ""
        if ($previousProfileFiles.Contains($relative)) {
            $previousEntry = $previousProfileFiles[$relative]
            if ($previousEntry -is [System.Collections.IDictionary] -and $previousEntry.Contains("hash")) {
                $previousHash = [string]$previousEntry["hash"]
            }
        }

        $hasLocalChange = $false
        if ($destinationHash -ne "" -and $destinationHash -ne $sourceHash) {
            if ($previousHash -eq "" -or $destinationHash -ne $previousHash) {
                $hasLocalChange = $true
            }
        }

        if ($hasLocalChange -and -not $ForceManaged) {
            $LocalOverrides.Add($relative) | Out-Null
            continue
        }

        if ($DryRun) {
            if ($destinationHash -eq $sourceHash) {
                Write-Host "Unchanged profile file: $relative"
            } else {
                Write-Host "Would update profile file: $relative"
            }
        } else {
            New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destinationPath) | Out-Null
            Copy-Item -LiteralPath $sourcePath -Destination $destinationPath -Force
        }

        $newProfileFiles[$relative] = [ordered]@{
            hash = $sourceHash
            source = "profiles/$Profile/$relative"
        }
    }

    $script:ProjectProfileFilesForManifest = $newProfileFiles
}

function Prune-UnmanagedPackageFiles {
    param(
        [System.Collections.IDictionary]$NewManifest,
        [System.Collections.Generic.List[string]]$Preserved,
        [System.Collections.Generic.List[string]]$Removed
    )

    if (-not $PruneUnmanaged -or -not (Test-Path -LiteralPath $installRootFull)) {
        return
    }

    $managedSet = ConvertTo-PathSet -Paths (Get-DictionaryKeys -Value $NewManifest["managed_files"])
    $generatedSet = ConvertTo-PathSet -Paths $ChildGeneratedPaths
    $protectedSet = ConvertTo-PathSet -Paths ($ProtectedPaths + @("PIPELINE-PACKAGE.json"))
    $overrideSet = ConvertTo-PathSet -Paths @($localOverrides)

    foreach ($file in (Get-ChildItem -LiteralPath $installRootFull -File -Recurse)) {
        $relative = Get-RelativePath -Root $installRootFull -Path $file.FullName
        if ($managedSet.ContainsKey($relative) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $generatedSet) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $protectedSet) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $overrideSet)) {
            continue
        }

        if ($DryRun) {
            Write-Host "Would remove unmanaged package file: $relative"
        } else {
            Remove-Item -LiteralPath $file.FullName -Force
        }
        $Removed.Add($relative) | Out-Null
    }

    foreach ($directory in (Get-ChildItem -LiteralPath $installRootFull -Directory -Recurse | Sort-Object FullName -Descending)) {
        if (@(Get-ChildItem -LiteralPath $directory.FullName -Force).Count -eq 0) {
            if ($DryRun) {
                Write-Host "Would remove empty package directory: $(Get-RelativePath -Root $installRootFull -Path $directory.FullName)"
            } else {
                Remove-Item -LiteralPath $directory.FullName -Force
            }
        }
    }

    foreach ($file in (Get-ChildItem -LiteralPath $installRootFull -File -Recurse)) {
        $relative = Get-RelativePath -Root $installRootFull -Path $file.FullName
        if ($managedSet.ContainsKey($relative) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $generatedSet) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $protectedSet) -or (Test-UnderAnyPath -RelativePath $relative -PathSet $overrideSet)) {
            continue
        }
        $Preserved.Add($relative) | Out-Null
    }
}

if ($DryRun) {
    Write-Host "Would ensure install root: $installRootFull"
} else {
    New-Item -ItemType Directory -Force -Path $installRootFull | Out-Null
}

$previousManifest = Read-PackageManifest
$newManifest = [ordered]@{}
$script:ManagedFilesForManifest = [ordered]@{}
$script:ProjectProfileFilesForManifest = [ordered]@{}
$localOverrides = [System.Collections.Generic.List[string]]::new()
$preservedUnmanaged = [System.Collections.Generic.List[string]]::new()
$removedUnmanaged = [System.Collections.Generic.List[string]]::new()

Apply-ManagedPackage -PreviousManifest $previousManifest -NewManifest $newManifest -LocalOverrides $localOverrides
Apply-ProjectProfile -PreviousManifest $previousManifest -NewManifest $newManifest -LocalOverrides $localOverrides
$newManifest["managed_files"] = $script:ManagedFilesForManifest
$newManifest["project_profile_files"] = $script:ProjectProfileFilesForManifest
Prune-UnmanagedPackageFiles -NewManifest $newManifest -Preserved $preservedUnmanaged -Removed $removedUnmanaged

$newManifest["local_overrides"] = @($localOverrides | Sort-Object -Unique)
$newManifest["preserved_unmanaged"] = @($preservedUnmanaged | Sort-Object -Unique)
$newManifest["removed_unmanaged"] = @($removedUnmanaged | Sort-Object -Unique)
Write-PackageManifest -Manifest $newManifest

Write-Host "OK: managed SocratexAI package sync complete."
if ($localOverrides.Count -gt 0) {
    Write-Host "Preserved local overrides:"
    foreach ($path in ($localOverrides | Sort-Object -Unique)) {
        Write-Host " - $path"
    }
}
if ($removedUnmanaged.Count -gt 0) {
    Write-Host "Removed unmanaged package files:"
    foreach ($path in ($removedUnmanaged | Sort-Object -Unique)) {
        Write-Host " - $path"
    }
}
