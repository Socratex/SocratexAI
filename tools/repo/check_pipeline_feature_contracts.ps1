param(
    [string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$featureListPath = Join-Path $repoRoot "pipeline_featurelist.json"
$scriptCatalogPath = Join-Path $repoRoot "SCRIPTS.json"
$errors = [System.Collections.Generic.List[string]]::new()

function Add-ContractError {
    param([string]$Message)
    $errors.Add($Message) | Out-Null
}

function Read-JsonFile {
    param([string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "Missing JSON file: $Path"
    }
    return Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json
}

function Convert-ToStringList {
    param([object]$Value)

    $result = [System.Collections.Generic.List[string]]::new()
    if ($null -eq $Value) {
        return @()
    }

    foreach ($item in @($Value)) {
        $text = ([string]$item).Trim()
        if ($text.Length -gt 0 -and -not $result.Contains($text)) {
            $result.Add($text) | Out-Null
        }
    }
    return @($result)
}

function Expand-PathArguments {
    param([string[]]$RawPaths)

    $expanded = [System.Collections.Generic.List[string]]::new()
    foreach ($path in $RawPaths) {
        foreach ($part in ([string]$path -split ",")) {
            $trimmed = $part.Trim()
            if ($trimmed.Length -gt 0) {
                $expanded.Add((ConvertTo-RepoRelativePath -Path $trimmed)) | Out-Null
            }
        }
    }
    return @($expanded | Sort-Object -Unique)
}

function ConvertTo-RepoRelativePath {
    param([string]$Path)

    return (($Path -replace "\\", "/") -replace '^\./', '')
}

function Invoke-GitLines {
    param([string[]]$Arguments)

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = @(git @Arguments 2>&1)
    $exitCode = $LASTEXITCODE
    $ErrorActionPreference = $previousErrorActionPreference

    if ($exitCode -ne 0) {
        throw "git $($Arguments -join ' ') failed: $($output -join "`n")"
    }
    return @($output | Where-Object {
        $line = [string]$_
        -not [string]::IsNullOrWhiteSpace($line) -and
            $line -notmatch "^warning: in the working copy of '.+', (CRLF|LF) will be replaced by (LF|CRLF) the next time Git touches it$"
    })
}

function Get-ChangedPaths {
    $explicitPaths = @(Expand-PathArguments -RawPaths $Paths)
    if ($explicitPaths.Count -gt 0) {
        return $explicitPaths
    }

    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot ".git"))) {
        return @()
    }

    $changed = @()
    $changed += @(Invoke-GitLines -Arguments @("diff", "--name-only", "--diff-filter=ACMRD"))
    $changed += @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMRD"))
    $changed += @(Invoke-GitLines -Arguments @("ls-files", "--others", "--exclude-standard"))
    return @($changed | ForEach-Object { ConvertTo-RepoRelativePath -Path ([string]$_) } | Sort-Object -Unique)
}

function Test-PipelineOwnedPath {
    param([string]$Path)

    $normalized = ConvertTo-RepoRelativePath -Path $Path
    if ($normalized -match '^(tools|core|project|templates|adapters|evals)/') {
        return $true
    }
    if ($normalized -match '^AI-compiled/') {
        return $true
    }
    if ($normalized -match '^(AGENTS\.md|PUBLIC-BOOTSTRAP\.md|QUALITY-GATE\.json|CHANGELOG\.json|COMMANDS\.json|DOCS\.json|FLOWS\.json|SCRIPTS\.json|WORKFLOW\.json|pipeline_featurelist\.json)$') {
        return $true
    }
    return $false
}

function Test-PathCoveredByContract {
    param(
        [string]$Path,
        [string[]]$RequiredPaths
    )

    $normalizedPath = ConvertTo-RepoRelativePath -Path $Path
    foreach ($contractPath in $RequiredPaths) {
        $normalizedContractPath = ConvertTo-RepoRelativePath -Path $contractPath
        if ($normalizedContractPath.Length -eq 0) {
            continue
        }
        if ($normalizedPath -eq $normalizedContractPath -or $normalizedPath.StartsWith($normalizedContractPath.TrimEnd("/") + "/", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Test-ManagedSyncPath {
    param(
        [string]$Path,
        [string[]]$ManagedPaths
    )

    $normalizedPath = ConvertTo-RepoRelativePath -Path $Path
    foreach ($managedPath in $ManagedPaths) {
        $normalizedManagedPath = ConvertTo-RepoRelativePath -Path $managedPath
        if ($normalizedPath -eq $normalizedManagedPath -or $normalizedPath.StartsWith($normalizedManagedPath.TrimEnd("/") + "/", [System.StringComparison]::OrdinalIgnoreCase)) {
            return $true
        }
    }
    return $false
}

function Get-ManagedPackagePaths {
    $syncScriptPath = Join-Path $repoRoot "tools/pipeline/sync_managed_pipeline_package.ps1"
    if (-not (Test-Path -LiteralPath $syncScriptPath -PathType Leaf)) {
        return @()
    }

    $text = Get-Content -Raw -LiteralPath $syncScriptPath -Encoding UTF8
    $matches = [regex]::Matches($text, '"([^"]+)"')
    $paths = [System.Collections.Generic.List[string]]::new()
    foreach ($match in $matches) {
        $value = $match.Groups[1].Value
        if ($value -match '^[A-Za-z0-9_.\-/]+$' -and $value -notmatch '\.ps1$') {
            $paths.Add((ConvertTo-RepoRelativePath -Path $value)) | Out-Null
        }
    }
    return @($paths | Sort-Object -Unique)
}

function Test-RequiredRepoPath {
    param(
        [string]$Feature,
        [string]$RelativePath
    )

    $normalized = ConvertTo-RepoRelativePath -Path $RelativePath
    if ($normalized.Length -eq 0) {
        Add-ContractError "Feature '$Feature' has an empty required_paths entry."
        return
    }

    if ($normalized.Contains("*")) {
        $matches = @(Get-ChildItem -Path (Join-Path $repoRoot $normalized) -ErrorAction SilentlyContinue)
        if ($matches.Count -eq 0) {
            Add-ContractError "Feature '$Feature' required path pattern has no matches: $normalized"
        }
        return
    }

    if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $normalized))) {
        Add-ContractError "Feature '$Feature' required path is missing: $normalized"
    }
}

Push-Location -LiteralPath $repoRoot
try {
    Write-Host "==> pipeline feature contract check"

    $featureList = Read-JsonFile -Path $featureListPath
    $scriptCatalog = Read-JsonFile -Path $scriptCatalogPath
    $features = @(Convert-ToStringList -Value $featureList.features)
    $featureSet = [System.Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    foreach ($feature in $features) {
        if (-not $featureSet.Add($feature)) {
            Add-ContractError "Duplicate feature id in features index: $feature"
        }
    }

    if ($features.Count -eq 0) {
        Add-ContractError "pipeline_featurelist.json must contain a non-empty features index."
    }
    if ($null -eq $featureList.feature_contracts) {
        Add-ContractError "pipeline_featurelist.json must contain feature_contracts."
    }

    $contractNames = if ($null -eq $featureList.feature_contracts) { @() } else { @($featureList.feature_contracts.PSObject.Properties.Name) }
    foreach ($feature in $features) {
        if ($contractNames -notcontains $feature) {
            Add-ContractError "Missing feature contract for feature id: $feature"
        }
    }
    foreach ($contractName in $contractNames) {
        if (-not $featureSet.Contains($contractName)) {
            Add-ContractError "feature_contracts contains key not present in features index: $contractName"
        }
    }

    $allowedDirections = @("source_to_child", "child_to_source", "bidirectional", "source_only")
    $managedPaths = @(Get-ManagedPackagePaths)
    $allRequiredPaths = [System.Collections.Generic.List[string]]::new()

    foreach ($feature in $features) {
        if ($contractNames -notcontains $feature) {
            continue
        }

        $contract = $featureList.feature_contracts.PSObject.Properties[$feature].Value
        if ([string]::IsNullOrWhiteSpace([string]$contract.summary)) {
            Add-ContractError "Feature '$feature' contract is missing summary."
        }

        $requiredPaths = @(Convert-ToStringList -Value $contract.required_paths)
        $requiredScripts = @(Convert-ToStringList -Value $contract.required_scripts)
        $requiredDocs = @(Convert-ToStringList -Value $contract.required_docs)
        $promotionChecklist = @(Convert-ToStringList -Value $contract.promotion_checklist)
        $verificationCommands = @(Convert-ToStringList -Value $contract.verification_commands)
        $syncDirection = ([string]$contract.sync_direction).Trim()

        if ($requiredPaths.Count -eq 0) {
            Add-ContractError "Feature '$feature' must list at least one required_paths entry."
        }
        if ($promotionChecklist.Count -eq 0) {
            Add-ContractError "Feature '$feature' must list promotion_checklist."
        }
        if ($verificationCommands.Count -eq 0) {
            Add-ContractError "Feature '$feature' must list verification_commands."
        }
        if ([string]::IsNullOrWhiteSpace([string]$contract.known_failure_if_missing)) {
            Add-ContractError "Feature '$feature' must describe known_failure_if_missing."
        }
        if ($allowedDirections -notcontains $syncDirection) {
            Add-ContractError "Feature '$feature' has invalid sync_direction '$syncDirection'."
        }

        foreach ($requiredPath in $requiredPaths) {
            $allRequiredPaths.Add($requiredPath) | Out-Null
            Test-RequiredRepoPath -Feature $feature -RelativePath $requiredPath
            if (($syncDirection -eq "source_to_child" -or $syncDirection -eq "bidirectional") -and $managedPaths.Count -gt 0 -and -not (Test-ManagedSyncPath -Path $requiredPath -ManagedPaths $managedPaths)) {
                Add-ContractError "Feature '$feature' required path is not mirrored by managed package sync: $requiredPath"
            }
        }

        foreach ($scriptName in $requiredScripts) {
            if (-not ($scriptCatalog.content.PSObject.Properties.Name -contains $scriptName)) {
                Add-ContractError "Feature '$feature' requires script missing from SCRIPTS.json: $scriptName"
                continue
            }

            $scriptEntry = $scriptCatalog.content.PSObject.Properties[$scriptName].Value
            $scriptPath = [string]$scriptEntry.path
            if ([string]::IsNullOrWhiteSpace($scriptPath)) {
                Add-ContractError "Feature '$feature' requires script with empty path: $scriptName"
                continue
            }
            if (-not (Test-Path -LiteralPath (Join-Path $repoRoot $scriptPath) -PathType Leaf)) {
                Add-ContractError "Feature '$feature' requires script file missing from repo: $scriptName -> $scriptPath"
            }
        }

        foreach ($docPath in $requiredDocs) {
            Test-RequiredRepoPath -Feature $feature -RelativePath $docPath
        }

        if ($null -ne $contract.required_catalog_entries) {
            foreach ($catalogProperty in $contract.required_catalog_entries.PSObject.Properties) {
                $catalogName = [string]$catalogProperty.Name
                if ($catalogName -notmatch '\.json$') {
                    $catalogName = "$catalogName.json"
                }
                $catalogPath = Join-Path $repoRoot $catalogName
                if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
                    Add-ContractError "Feature '$feature' references missing catalog: $catalogName"
                    continue
                }

                $catalog = Read-JsonFile -Path $catalogPath
                foreach ($entryName in @(Convert-ToStringList -Value $catalogProperty.Value)) {
                    if (-not ($catalog.content.PSObject.Properties.Name -contains $entryName)) {
                        Add-ContractError "Feature '$feature' requires missing catalog entry: $catalogName -> $entryName"
                    }
                }
            }
        }
    }

    $changedPaths = @(Get-ChangedPaths)
    $pipelineChangedPaths = @($changedPaths | Where-Object { Test-PipelineOwnedPath -Path $_ })
    foreach ($path in $pipelineChangedPaths) {
        if ($path -eq "pipeline_featurelist.json") {
            continue
        }
        if (-not (Test-PathCoveredByContract -Path $path -RequiredPaths @($allRequiredPaths))) {
            Add-ContractError "Changed pipeline-owned path is not assigned to any feature contract required_paths: $path"
        }
    }

    if ($errors.Count -gt 0) {
        foreach ($issue in $errors) {
            Write-Host "ERROR: $issue"
        }
        throw "pipeline feature contract check failed with $($errors.Count) error(s)."
    }

    Write-Host "OK: feature contracts cover $($features.Count) feature(s)."
    if ($pipelineChangedPaths.Count -gt 0) {
        Write-Host "OK: changed pipeline-owned paths are assigned to feature contracts."
    }
} finally {
    Pop-Location
}
