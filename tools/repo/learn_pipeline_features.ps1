param(
	[Parameter(Mandatory = $true)]
	[string]$ProjectPath,
	[string]$SourceFeatureListPath = "",
	[string[]]$IncludeFeatures = @(),
	[string[]]$ExcludePatterns = @("project_specific", "runtime_diagnostic"),
	[switch]$Apply,
	[switch]$AcceptAll
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-JsonFile {
	param([string]$Path)

	if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
		throw "Missing JSON file: $Path"
	}
	return Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json
}

function Convert-ToFeatureList {
	param([object[]]$Values)

	$result = [System.Collections.Generic.List[string]]::new()
	foreach ($value in $Values) {
		$text = ([string]$value).Trim()
		if ($text.Length -gt 0 -and -not $result.Contains($text)) {
			$result.Add($text) | Out-Null
		}
	}
	return @($result)
}

function Get-FeatureValues {
	param([object]$FeatureList)

	if ($null -eq $FeatureList) {
		return @()
	}
	if ($FeatureList.PSObject.Properties.Name -contains "features") {
		return @($FeatureList.features)
	}
	if ($FeatureList.PSObject.Properties.Name -contains "content") {
		$content = $FeatureList.content
		if ($null -ne $content -and $content.PSObject.Properties.Name -contains "features") {
			return @($content.features)
		}
	}
	return @()
}

function Test-ExcludedFeature {
	param(
		[string]$Feature,
		[string[]]$Patterns
	)

	foreach ($pattern in $Patterns) {
		if ([string]::IsNullOrWhiteSpace($pattern)) {
			continue
		}
		if ($Feature -match $pattern) {
			return $true
		}
	}
	return $false
}

function Get-FeatureContracts {
	param([object]$FeatureList)

	$contracts = [ordered]@{}
	if ($null -eq $FeatureList) {
		return $contracts
	}

	if ($FeatureList.PSObject.Properties.Name -contains "content") {
		$content = $FeatureList.content
		if ($null -ne $content -and $content.PSObject.Properties.Name -contains "feature_contracts") {
			foreach ($property in $content.feature_contracts.PSObject.Properties) {
				$contracts[[string]$property.Name] = $property.Value
			}
			return $contracts
		}
	}

	if (-not ($FeatureList.PSObject.Properties.Name -contains "feature_contracts")) {
		return $contracts
	}

	foreach ($property in $FeatureList.feature_contracts.PSObject.Properties) {
		$contracts[[string]$property.Name] = $property.Value
	}
	return $contracts
}

function Get-FeatureListMetadataValue {
	param(
		[object]$FeatureList,
		[string]$Name,
		[string]$Fallback
	)

	if ($null -ne $FeatureList -and $FeatureList.PSObject.Properties.Name -contains $Name) {
		$value = ([string]$FeatureList.$Name).Trim()
		if ($value.Length -gt 0) {
			return $value
		}
	}
	if ($null -ne $FeatureList -and $FeatureList.PSObject.Properties.Name -contains "metadata") {
		$metadata = $FeatureList.metadata
		if ($null -ne $metadata -and $metadata.PSObject.Properties.Name -contains $Name) {
			$value = ([string]$metadata.$Name).Trim()
			if ($value.Length -gt 0) {
				return $value
			}
		}
	}
	return $Fallback
}

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
if ([string]::IsNullOrWhiteSpace($SourceFeatureListPath)) {
	$SourceFeatureListPath = Join-Path $repoRoot "pipeline_featurelist.json"
}

$projectRoot = Resolve-Path -LiteralPath $ProjectPath
$projectFeatureListPath = Join-Path $projectRoot "pipeline_featurelist.json"

$source = Read-JsonFile -Path $SourceFeatureListPath
$project = Read-JsonFile -Path $projectFeatureListPath

$sourceFeatures = Convert-ToFeatureList -Values @(Get-FeatureValues -FeatureList $source)
$projectFeatures = Convert-ToFeatureList -Values @(Get-FeatureValues -FeatureList $project)
$candidateFeatures = @($projectFeatures | Where-Object { $sourceFeatures -notcontains $_ })

$selected = [System.Collections.Generic.List[string]]::new()
foreach ($feature in $candidateFeatures) {
	$explicitlyIncluded = $IncludeFeatures -contains $feature
	if ($AcceptAll -or $explicitlyIncluded -or (-not (Test-ExcludedFeature -Feature $feature -Patterns $ExcludePatterns))) {
		$selected.Add($feature) | Out-Null
	}
}

Write-Host "==> pipeline feature learning"
Write-Host "source: $SourceFeatureListPath"
Write-Host "project: $projectFeatureListPath"
Write-Host "candidates: $($candidateFeatures.Count)"
foreach ($feature in $candidateFeatures) {
	$status = if ($selected.Contains($feature)) { "selected" } else { "excluded" }
	Write-Host " - $feature [$status]"
}

if (-not $Apply) {
	Write-Host "No changes made. Rerun with -Apply and optionally -IncludeFeatures or -AcceptAll."
	exit 0
}

if ($selected.Count -eq 0) {
	Write-Host "OK: no selected features to add."
	exit 0
}

$sourceContracts = Get-FeatureContracts -FeatureList $source
$projectContracts = Get-FeatureContracts -FeatureList $project
foreach ($feature in $selected) {
	if (-not $projectContracts.Contains($feature)) {
		throw "Selected feature '$feature' has no feature_contracts entry in project feature list. Promote full artifacts and contract first; do not copy feature IDs alone."
	}
}

$updated = [System.Collections.Generic.List[string]]::new()
foreach ($feature in $sourceFeatures) {
	$updated.Add($feature) | Out-Null
}
foreach ($feature in $selected) {
	if (-not $updated.Contains($feature)) {
		$updated.Add($feature) | Out-Null
	}
	$sourceContracts[$feature] = $projectContracts[$feature]
}

$payload = [ordered]@{
	index = @("features", "feature_contracts")
	content = [ordered]@{
		features = @($updated)
		feature_contracts = $sourceContracts
	}
	metadata = [ordered]@{
		schema = "socratex-pipeline-featurelist/v4"
		pipeline_id = Get-FeatureListMetadataValue -FeatureList $source -Name "pipeline_id" -Fallback "socratex_pipeline"
		role = Get-FeatureListMetadataValue -FeatureList $source -Name "role" -Fallback "source"
		updated_at = (Get-Date).ToString("yyyy-MM-dd")
		comparison_contract = "Use features for cheap source/instance comparison; use feature_contracts for artifact-level synchronization and promotion checks."
		required_contract_fields = @("summary", "required_paths", "required_scripts", "required_catalog_entries", "required_docs", "sync_direction", "promotion_checklist", "verification_commands", "known_failure_if_missing")
		sync_directions = @("source_to_child", "child_to_source", "bidirectional", "source_only")
	}
}

$json = ($payload | ConvertTo-Json -Depth 20)
[System.IO.File]::WriteAllText($SourceFeatureListPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK: added $($selected.Count) feature(s) and feature contract(s) to source pipeline feature list."
