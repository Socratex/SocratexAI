param(
	[Parameter(Mandatory = $true)]
	[string]$ProjectPath,
	[string]$SourceFeatureListPath = "",
	[string[]]$ExcludePatterns = @("project_specific", "runtime_diagnostic"),
	[string]$OutputPath = ""
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

function Normalize-PatternList {
	param([string[]]$Patterns)

	$normalized = [System.Collections.Generic.List[string]]::new()
	foreach ($pattern in $Patterns) {
		foreach ($part in ([string]$pattern -split ",")) {
			$trimmed = $part.Trim()
			if ($trimmed.Length -gt 0) {
				$normalized.Add($trimmed) | Out-Null
			}
		}
	}
	return @($normalized)
}

function Get-ReportHash {
	param([string]$Json)

	$bytes = [System.Text.Encoding]::UTF8.GetBytes($Json)
	$sha = [System.Security.Cryptography.SHA256]::Create()
	try {
		$hashBytes = $sha.ComputeHash($bytes)
		return ([System.BitConverter]::ToString($hashBytes)).Replace("-", "").ToLowerInvariant()
	} finally {
		$sha.Dispose()
	}
}

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
if ([string]::IsNullOrWhiteSpace($SourceFeatureListPath)) {
	$SourceFeatureListPath = Join-Path $repoRoot "pipeline_featurelist.json"
}

$projectRoot = Resolve-Path -LiteralPath $ProjectPath
$projectFeatureListPath = Join-Path $projectRoot "pipeline_featurelist.json"
$ExcludePatterns = @(Normalize-PatternList -Patterns $ExcludePatterns)

$source = Read-JsonFile -Path $SourceFeatureListPath
$project = Read-JsonFile -Path $projectFeatureListPath

$sourceFeatures = Convert-ToFeatureList -Values @($source.features)
$projectFeatures = Convert-ToFeatureList -Values @($project.features)
$candidateFeatures = @($projectFeatures | Where-Object { $sourceFeatures -notcontains $_ })
$missingFromProject = @($sourceFeatures | Where-Object { $projectFeatures -notcontains $_ })

$candidates = @()
foreach ($feature in $candidateFeatures) {
	$excluded = Test-ExcludedFeature -Feature $feature -Patterns $ExcludePatterns
	$candidates += [ordered]@{
		id = $feature
		status = if ($excluded) { "excluded_by_pattern" } else { "review_candidate" }
		recommendation = if ($excluded) { "Keep project-specific unless a maintainer explicitly promotes it." } else { "Review for promotion into the source pipeline." }
	}
}

$reviewCandidates = @($candidates | Where-Object { $_.status -eq "review_candidate" } | ForEach-Object { $_.id })
$excludedCandidates = @($candidates | Where-Object { $_.status -eq "excluded_by_pattern" } | ForEach-Object { $_.id })

$hashPayload = [ordered]@{
	source_pipeline_id = [string]$source.pipeline_id
	project_pipeline_id = [string]$project.pipeline_id
	project_features_not_in_source = @($candidateFeatures)
	source_features_not_in_project = @($missingFromProject)
}
$hashJson = $hashPayload | ConvertTo-Json -Depth 8 -Compress

$payload = [ordered]@{
	schema = "socratex-pipeline-learning-report/v1"
	report_hash = Get-ReportHash -Json $hashJson
	generated_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
	source_featurelist_path = [string](Resolve-Path -LiteralPath $SourceFeatureListPath)
	project_path = [string]$projectRoot
	project_featurelist_path = [string](Resolve-Path -LiteralPath $projectFeatureListPath)
	source_pipeline_id = [string]$source.pipeline_id
	project_pipeline_id = [string]$project.pipeline_id
	candidate_count = $candidateFeatures.Count
	review_candidate_count = $reviewCandidates.Count
	excluded_candidate_count = $excludedCandidates.Count
	candidates = @($candidates)
	source_features_missing_from_project = @($missingFromProject)
	recommendation = "Use this report as intake only. Promote only reusable, project-agnostic feature IDs into the source pipeline."
}

$json = $payload | ConvertTo-Json -Depth 10
if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
	$fullOutputPath = if ([System.IO.Path]::IsPathRooted($OutputPath)) { $OutputPath } else { Join-Path $repoRoot $OutputPath }
	$parent = Split-Path -Parent $fullOutputPath
	if (-not [string]::IsNullOrWhiteSpace($parent)) {
		New-Item -ItemType Directory -Force -Path $parent | Out-Null
	}
	[System.IO.File]::WriteAllText($fullOutputPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
	Write-Host "OK: wrote pipeline learning report: $fullOutputPath"
	exit 0
}

Write-Output $json
