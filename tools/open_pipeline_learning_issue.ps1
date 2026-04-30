param(
	[Parameter(Mandatory = $true)]
	[string]$ProjectPath,
	[string]$SourceFeatureListPath = "",
	[string]$Owner = "",
	[string]$Repo = "",
	[string]$IssueTitle = "SocratexPipeline Learning Report",
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
	param([object]$Report)

	$review = @($Report.candidates | Where-Object { $_.status -eq "review_candidate" } | ForEach-Object { $_.id })
	$excluded = @($Report.candidates | Where-Object { $_.status -eq "excluded_by_pattern" } | ForEach-Object { $_.id })
	$missing = @($Report.source_features_missing_from_project)
	$reportedAt = if ($Report.generated_at -is [datetime]) {
		$Report.generated_at.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
	} else {
		[string]$Report.generated_at
	}

	return [string]::Join([Environment]::NewLine, @(
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
		"Use this report as intake only. Promote only reusable, project-agnostic feature IDs into the source pipeline after review."
	))
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
	$body = ConvertTo-IssueBody -Report $report
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
