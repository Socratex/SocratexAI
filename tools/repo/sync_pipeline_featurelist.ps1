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

function Get-PipelineId {
	param(
		[object]$FeatureList,
		[string]$Fallback
	)

	if ($null -ne $FeatureList -and $FeatureList.PSObject.Properties.Name -contains "pipeline_id") {
		$value = ([string]$FeatureList.pipeline_id).Trim()
		if ($value.Length -gt 0) {
			return $value
		}
	}
	if ($null -ne $FeatureList -and $FeatureList.PSObject.Properties.Name -contains "metadata") {
		$metadata = $FeatureList.metadata
		if ($null -ne $metadata -and $metadata.PSObject.Properties.Name -contains "pipeline_id") {
			$value = ([string]$metadata.pipeline_id).Trim()
			if ($value.Length -gt 0) {
				return $value
			}
		}
	}
	return $Fallback
}

function Test-ListDocumentFeatureManifest {
	param([object]$FeatureList)

	if ($null -eq $FeatureList) {
		return $false
	}
	$names = @($FeatureList.PSObject.Properties.Name)
	if (-not ($names -contains "index") -or -not ($names -contains "content") -or -not ($names -contains "metadata")) {
		return $false
	}
	$content = $FeatureList.content
	return ($null -ne $content -and $content.PSObject.Properties.Name -contains "features")
}

function Test-TargetRequiresListDocumentFeatureManifest {
	param([string]$RootPath)

	$docsPath = Join-Path $RootPath "DOCS.json"
	if (-not (Test-Path -LiteralPath $docsPath -PathType Leaf)) {
		return $false
	}
	try {
		$docs = Read-JsonFile -Path $docsPath
		if (-not ($docs.PSObject.Properties.Name -contains "content")) {
			return $false
		}
		$content = $docs.content
		if ($null -eq $content -or -not ($content.PSObject.Properties.Name -contains "pipeline_featurelist.json")) {
			return $false
		}
		$description = (@($content."pipeline_featurelist.json") -join "`n").ToLowerInvariant()
		return (
			($description.Contains("root") -and $description.Contains("index") -and $description.Contains("content") -and $description.Contains("metadata")) -or
			$description.Contains("canonical json document shape")
		)
	} catch {
		return $false
	}
}

function ConvertTo-OrderedHashtable {
	param([object]$Value)

	$result = [ordered]@{}
	if ($null -eq $Value) {
		return $result
	}
	foreach ($property in $Value.PSObject.Properties) {
		$result[[string]$property.Name] = $property.Value
	}
	return $result
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
$sourceFeatures = Convert-ToFeatureList -Values @(Get-FeatureValues -FeatureList $source)
if ($sourceFeatures.Count -eq 0) {
	throw "Source feature list has no features: $SourceFeatureListPath"
}

$existingFeatures = @()
$existingContracts = [ordered]@{}
$existing = $null
$preserveListDocumentShape = $false
if (Test-Path -LiteralPath $OutputPath -PathType Leaf) {
	$existing = Read-JsonFile -Path $OutputPath
	$existingFeatures = Convert-ToFeatureList -Values @(Get-FeatureValues -FeatureList $existing)
	$existingContracts = Get-FeatureContracts -FeatureList $existing
	$preserveListDocumentShape = Test-ListDocumentFeatureManifest -FeatureList $existing
}
if (-not $preserveListDocumentShape) {
	$preserveListDocumentShape = Test-TargetRequiresListDocumentFeatureManifest -RootPath $targetRoot
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

$sourcePipelineId = Get-PipelineId -FeatureList $source -Fallback "socratex_pipeline"
$comparison = [ordered]@{
	same_as_source = ($missing.Count -eq 0 -and $extra.Count -eq 0)
	same = @($same)
	missing_from_instance = @($missing)
	extra_in_instance = @($extra)
}

if ($preserveListDocumentShape) {
	$indexValues = @()
	if ($null -ne $existing -and $existing.PSObject.Properties.Name -contains "index") {
		$indexValues = @($existing.index)
	}
	$index = [System.Collections.Generic.List[string]]::new()
	foreach ($value in (Convert-ToFeatureList -Values $indexValues)) {
		$index.Add($value) | Out-Null
	}
	foreach ($requiredKey in @("features", "comparison_to_source")) {
		if (-not $index.Contains($requiredKey)) {
			$index.Add($requiredKey) | Out-Null
		}
	}
	if ($extraContracts.Count -gt 0 -and -not $index.Contains("feature_contracts")) {
		$index.Add("feature_contracts") | Out-Null
	}

	$content = [ordered]@{}
	$existingContent = [ordered]@{}
	if ($null -ne $existing -and $existing.PSObject.Properties.Name -contains "content") {
		$existingContent = ConvertTo-OrderedHashtable -Value $existing.content
	}
	foreach ($property in $existingContent.Keys) {
		if (-not $index.Contains($property)) {
			$index.Add($property) | Out-Null
		}
	}
	foreach ($property in $index) {
		if ($property -eq "features") {
			$content[$property] = @($features)
		} elseif ($property -eq "comparison_to_source") {
			$content[$property] = $comparison
		} elseif ($property -eq "feature_contracts" -and $extraContracts.Count -gt 0) {
			$content[$property] = $extraContracts
		} elseif ($existingContent.Contains($property)) {
			$content[$property] = $existingContent[$property]
		} else {
			$content[$property] = @()
		}
	}

	$metadata = [ordered]@{}
	if ($null -ne $existing -and $existing.PSObject.Properties.Name -contains "metadata") {
		$metadata = ConvertTo-OrderedHashtable -Value $existing.metadata
	}
	if (-not $metadata.Contains("schema")) {
		$metadata["schema"] = "socratex-pipeline-featurelist/v2"
	}
	$metadata["pipeline_id"] = $PipelineId
	$metadata["role"] = "instance"
	$metadata["source_pipeline_id"] = $sourcePipelineId
	$metadata["updated_at"] = (Get-Date).ToString("yyyy-MM-dd")
	$metadata["comparison_contract"] = "features is the cheap comparison layer; project-owned content keeps its local list-document shape."

	$payload = [ordered]@{
		index = @($index.ToArray())
		content = $content
		metadata = $metadata
	}
} else {
	$payload = [ordered]@{
		schema = "socratex-pipeline-featurelist/v2"
		pipeline_id = $PipelineId
		role = "instance"
		source_pipeline_id = $sourcePipelineId
		updated_at = (Get-Date).ToString("yyyy-MM-dd")
		features = @($features)
		comparison_to_source = $comparison
	}
}
if (-not $preserveListDocumentShape -and $extraContracts.Count -gt 0) {
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
