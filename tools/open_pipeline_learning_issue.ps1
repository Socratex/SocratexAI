param(
	[Parameter(Mandatory = $true)]
	[string]$ProjectPath,
	[string]$SourceFeatureListPath = "",
	[string]$Owner = "",
	[string]$Repo = "",
	[string]$IssueTitle = "SocratexPipeline Learning Report",
	[string]$LearnedSummary = "",
	[string[]]$ChangedScripts = @(),
	[string]$ReporterInstruction = "",
	[string[]]$ExcludePatterns = @("project_specific", "godot", "gdscript", "runtime_diagnostic"),
	[switch]$Open
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-RemoteRepository {
	$envRepo = [Environment]::GetEnvironmentVariable("GITHUB_REPOSITORY")
	if (-not [string]::IsNullOrWhiteSpace($envRepo) -and $envRepo -match '^([^/]+)/([^/]+)$') {
		return @($Matches[1], $Matches[2])
	}

	$remote = @(git remote get-url origin 2>$null)
	if ($LASTEXITCODE -ne 0 -or $remote.Count -eq 0) {
		return @("", "")
	}

	$url = ([string]$remote[0]).Trim()
	if ($url -match 'github\.com[:/]([^/]+)/([^/]+?)(?:\.git)?$') {
		return @($Matches[1], $Matches[2])
	}
	return @("", "")
}

function ConvertTo-MarkdownList {
	param([object[]]$Values)

	$items = @($Values)
	if ($items.Count -eq 0) {
		return "- none"
	}
	return (($items | ForEach-Object { "- ``$($_)``" }) -join [Environment]::NewLine)
}

function ConvertTo-IssueBody {
	param(
		[object]$Report,
		[string]$LearnedSummary,
		[string[]]$ChangedScripts,
		[string]$ReporterInstruction
	)

	$review = @($Report.candidates | Where-Object { $_.status -eq "review_candidate" } | ForEach-Object { $_.id })
	$excluded = @($Report.candidates | Where-Object { $_.status -eq "excluded_by_pattern" } | ForEach-Object { $_.id })
	$missing = @($Report.source_features_missing_from_project)
	$changedScriptList = @($ChangedScripts | ForEach-Object { ([string]$_).Trim() } | Where-Object { $_.Length -gt 0 })
	$summary = $LearnedSummary.Trim()
	if ([string]::IsNullOrWhiteSpace($summary)) {
		$summary = "The reporting project exposes pipeline feature IDs that should be reviewed against the source SocratexPipeline feature list."
	}
	$extraInstruction = $ReporterInstruction.Trim()
	$reportedAt = if ($Report.generated_at -is [datetime]) {
		$Report.generated_at.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
	} else {
		[string]$Report.generated_at
	}

	$lines = [System.Collections.Generic.List[string]]::new()
	foreach ($line in @(
		"<!-- socratex-pipeline-learning-report:$($Report.report_hash) -->",
		"# SocratexPipeline Learning Report",
		"",
		"## Source",
		"",
		"- Source pipeline: ``$($Report.source_pipeline_id)``",
		"- Project pipeline: ``$($Report.project_pipeline_id)``",
		"- Reported: $reportedAt",
		"- Report hash: ``$($Report.report_hash)``",
		"",
		"## What AI Learned",
		"",
		$summary,
		"",
		"## What This Intake Tool Does",
		"",
		"- ``tools/report_pipeline_learning.ps1`` compares a project ``pipeline_featurelist.json`` with the source manifest and classifies unknown feature IDs.",
		"- ``tools/open_pipeline_learning_issue.ps1`` turns that report into this prefilled GitHub Issue URL without using a write token or API write.",
		"- ``tools/learn_pipeline_features.ps1`` is the maintainer-side promotion tool for reviewed reusable feature IDs.",
		"- ``tools/sync_pipeline_featurelist.ps1`` propagates source feature IDs back into installed project instance manifests after the source learns something reusable.",
		"",
		"## Changed Scripts Or Files To Review",
		"",
		(ConvertTo-MarkdownList -Values $changedScriptList),
		"",
		"## Review Candidates",
		"",
		(ConvertTo-MarkdownList -Values $review),
		"",
		"## Excluded Candidates",
		"",
		(ConvertTo-MarkdownList -Values $excluded),
		"",
		"## Source Features Missing From Project",
		"",
		(ConvertTo-MarkdownList -Values $missing),
		"",
		"## Recommendation",
		"",
		"Use this report as intake only. Promote only reusable, project-agnostic feature IDs into the source pipeline after review.",
		"",
		"## Maintainer Instructions",
		"",
		"1. Check whether each review candidate is reusable outside the reporting project.",
		"2. Keep project-specific, framework-specific, or domain-specific IDs out of the source manifest unless they describe a generic pipeline capability.",
		"3. Promote selected reusable IDs with:",
		"",
		'```powershell',
		'powershell -NoProfile -ExecutionPolicy Bypass -File tools/learn_pipeline_features.ps1 -ProjectPath "<project>" -Apply -IncludeFeatures <ids>',
		'```',
		"",
		"4. After promotion, update or reinitialize consuming projects so ``tools/sync_pipeline_featurelist.ps1`` can refresh their instance manifests.",
		"",
		"## Reporter Notes",
		""
	)) {
		$lines.Add($line) | Out-Null
	}
	if ([string]::IsNullOrWhiteSpace($extraInstruction)) {
		$lines.Add("- none") | Out-Null
	} else {
		$lines.Add($extraInstruction) | Out-Null
	}
	return [string]::Join([Environment]::NewLine, $lines)
}

function ConvertTo-QueryValue {
	param([string]$Value)

	return [System.Uri]::EscapeDataString($Value)
}

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$reportScript = Join-Path $PSScriptRoot "report_pipeline_learning.ps1"
if (-not (Test-Path -LiteralPath $reportScript -PathType Leaf)) {
	throw "Missing learning report tool: $reportScript"
}

Push-Location -LiteralPath $repoRoot
try {
	if ([string]::IsNullOrWhiteSpace($Owner) -or [string]::IsNullOrWhiteSpace($Repo)) {
		$remoteRepo = Get-RemoteRepository
		if ([string]::IsNullOrWhiteSpace($Owner)) {
			$Owner = $remoteRepo[0]
		}
		if ([string]::IsNullOrWhiteSpace($Repo)) {
			$Repo = $remoteRepo[1]
		}
	}

	if ([string]::IsNullOrWhiteSpace($Owner) -or [string]::IsNullOrWhiteSpace($Repo)) {
		throw "Missing GitHub repository. Pass -Owner and -Repo or configure origin/GITHUB_REPOSITORY."
	}

	$reportArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$reportScript,
		"-ProjectPath",
		$ProjectPath,
		"-ExcludePatterns",
		($ExcludePatterns -join ",")
	)
	if (-not [string]::IsNullOrWhiteSpace($SourceFeatureListPath)) {
		$reportArgs += "-SourceFeatureListPath"
		$reportArgs += $SourceFeatureListPath
	}

	$reportJson = @(powershell @reportArgs)
	if ($LASTEXITCODE -ne 0) {
		throw "Learning report failed with exit code $LASTEXITCODE"
	}
	$report = ($reportJson -join [Environment]::NewLine) | ConvertFrom-Json

	$title = "${IssueTitle}: $($report.project_pipeline_id)"
	$body = ConvertTo-IssueBody -Report $report -LearnedSummary $LearnedSummary -ChangedScripts $ChangedScripts -ReporterInstruction $ReporterInstruction
	$url = "https://github.com/$Owner/$Repo/issues/new?title=$(ConvertTo-QueryValue -Value $title)&body=$(ConvertTo-QueryValue -Value $body)&labels=socratex-pipeline,learning-inbox"

	if ($url.Length -gt 7500) {
		Write-Host "WARNING: generated issue URL is long ($($url.Length) characters). If the browser truncates it, rerun with a smaller report or paste the generated body manually."
	}

	Write-Host "OK: generated prefilled GitHub Issue URL."
	Write-Host $url

	if ($Open) {
		Start-Process $url
	}
} finally {
	Pop-Location
}
