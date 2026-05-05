param(
	[string]$TargetPath = ".",
	[string]$SourceFeatureListPath = "",
	[string]$OutputPath = "",
	[string]$PipelineId = "",
	[string[]]$ExtraFeatures = @(),
	[switch]$DryRun
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

function Get-DefaultPipelineId {
	param([string]$RootPath)

	$name = Split-Path -Leaf $RootPath
	$id = $name.ToLowerInvariant() -replace '[^a-z0-9]+', '_'
	$id = $id.Trim('_')
	if ([string]::IsNullOrWhiteSpace($id)) {
		return "project_pipeline"
	}
	return $id
}

function Get-FeatureContracts {
	param([object]$FeatureList)

	$contracts = [ordered]@{}
	if ($null -eq $FeatureList -or -not ($FeatureList.PSObject.Properties.Name -contains "feature_contracts")) {
		return $contracts
	}

	foreach ($property in $FeatureList.feature_contracts.PSObject.Properties) {
		$contracts[[string]$property.Name] = $property.Value
	}
	return $contracts
}

$targetRoot = Resolve-Path -LiteralPath $TargetPath
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
	$OutputPath = Join-Path $targetRoot "pipeline_featurelist.json"
}
if ([string]::IsNullOrWhiteSpace($SourceFeatureListPath)) {
	$installedSource = Join-Path $targetRoot "SocratexAI\pipeline_featurelist.json"
	if (Test-Path -LiteralPath $installedSource -PathType Leaf) {
		$SourceFeatureListPath = $installedSource
	} else {
		$repoSource = Join-Path (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")) "pipeline_featurelist.json"
		$SourceFeatureListPath = $repoSource
	}
}

$source = Read-JsonFile -Path $SourceFeatureListPath
$sourceFeatures = Convert-ToFeatureList -Values @($source.features)
if ($sourceFeatures.Count -eq 0) {
	throw "Source feature list has no features: $SourceFeatureListPath"
}

$existingFeatures = @()
$existingContracts = [ordered]@{}
if (Test-Path -LiteralPath $OutputPath -PathType Leaf) {
	$existing = Read-JsonFile -Path $OutputPath
	$existingFeatures = Convert-ToFeatureList -Values @($existing.features)
	$existingContracts = Get-FeatureContracts -FeatureList $existing
}

$features = [System.Collections.Generic.List[string]]::new()
foreach ($feature in $sourceFeatures) {
	$features.Add($feature) | Out-Null
}
foreach ($feature in $existingFeatures + $ExtraFeatures) {
	if (-not $features.Contains($feature)) {
		$features.Add($feature) | Out-Null
	}
}

$same = @($sourceFeatures | Where-Object { $features.Contains($_) })
$missing = @($sourceFeatures | Where-Object { -not $features.Contains($_) })
$extra = @($features | Where-Object { $sourceFeatures -notcontains $_ })
$extraContracts = [ordered]@{}
foreach ($feature in $extra) {
	if ($existingContracts.Contains($feature)) {
		$extraContracts[$feature] = $existingContracts[$feature]
	}
}

if ([string]::IsNullOrWhiteSpace($PipelineId)) {
	$PipelineId = Get-DefaultPipelineId -RootPath $targetRoot
}

$payload = [ordered]@{
	schema = "socratex-pipeline-featurelist/v2"
	pipeline_id = $PipelineId
	role = "instance"
	source_pipeline_id = [string]$source.pipeline_id
	updated_at = (Get-Date).ToString("yyyy-MM-dd")
	features = @($features)
	comparison_to_source = [ordered]@{
		same_as_source = ($missing.Count -eq 0 -and $extra.Count -eq 0)
		same = @($same)
		missing_from_instance = @($missing)
		extra_in_instance = @($extra)
	}
}
if ($extraContracts.Count -gt 0) {
	$payload.feature_contracts = $extraContracts
	$payload.metadata = [ordered]@{
		comparison_contract = "Use features and comparison_to_source for cheap comparison; preserve feature_contracts only for instance-owned extra features that may be promoted upstream."
	}
}

$json = ($payload | ConvertTo-Json -Depth 20)
if ($DryRun) {
	Write-Host "Would write instance pipeline feature list: $OutputPath"
	Write-Host $json
	exit 0
}

$parent = Split-Path -Parent $OutputPath
if (-not [string]::IsNullOrWhiteSpace($parent)) {
	New-Item -ItemType Directory -Force -Path $parent | Out-Null
}
[System.IO.File]::WriteAllText($OutputPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Host "OK: synced pipeline feature list: $OutputPath"
Write-Host "same=$($same.Count) missing=$($missing.Count) extra=$($extra.Count)"
