param(
	[Parameter(Mandatory = $true)]
	[string]$ProjectPath,
	[string]$SourceFeatureListPath = "",
	[string]$Owner = "",
	[string]$Repo = "",
	[string]$IssueTitle = "SocratexPipeline Learning Inbox",
	[string[]]$Labels = @("socratex-pipeline", "learning-inbox"),
	[string[]]$ExcludePatterns = @("project_specific", "godot", "gdscript", "runtime_diagnostic"),
	[string]$Token = "",
	[switch]$DryRun,
	[switch]$Force
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

function Invoke-GitHubApi {
	param(
		[string]$Method,
		[string]$Uri,
		[object]$Body = $null
	)

	$headers = @{
		Accept = "application/vnd.github+json"
		Authorization = "Bearer $Token"
		"X-GitHub-Api-Version" = "2022-11-28"
		"User-Agent" = "SocratexPipeline"
	}
	if ($null -eq $Body) {
		return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers
	}
	return Invoke-RestMethod -Method $Method -Uri $Uri -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10) -ContentType "application/json"
}

function New-InboxBody {
	return [string]::Join([Environment]::NewLine, @(
		"<!-- socratex-pipeline-learning-inbox -->",
		"# SocratexPipeline Learning Inbox",
		"",
		"This issue is the shared network inbox for reusable pipeline learning reports.",
		"",
		"Reports are appended only when their report hash is new. The source pipeline should learn from these reports only after human or agent review.",
		"",
		"## Review Command",
		"",
		'```powershell',
		'powershell -NoProfile -ExecutionPolicy Bypass -File tools/learn_pipeline_features.ps1 -ProjectPath "<project>"',
		'```',
		"",
		"## Pending Reports"
	))
}

function ConvertTo-MarkdownList {
	param([object[]]$Values)

	$items = @($Values)
	if ($items.Count -eq 0) {
		return "- none"
	}
	return (($items | ForEach-Object { "- ``$($_)``" }) -join [Environment]::NewLine)
}

function ConvertTo-ReportBlock {
	param([object]$Report)

	$review = @($Report.candidates | Where-Object { $_.status -eq "review_candidate" } | ForEach-Object { $_.id })
	$excluded = @($Report.candidates | Where-Object { $_.status -eq "excluded_by_pattern" } | ForEach-Object { $_.id })
	$missing = @($Report.source_features_missing_from_project)
	$projectPath = [string]$Report.project_path
	$commandProjectPath = $projectPath.Replace("'", "''")
	$reportedAt = if ($Report.generated_at -is [datetime]) {
		$Report.generated_at.ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
	} else {
		[string]$Report.generated_at
	}

	$lines = [System.Collections.Generic.List[string]]::new()
	$lines.Add("") | Out-Null
	$lines.Add("<!-- socratex-pipeline-learning-report:$($Report.report_hash) -->") | Out-Null
	$lines.Add("### Project: $($Report.project_pipeline_id)") | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add("- Reported: $reportedAt") | Out-Null
	$lines.Add("- Project path: ``$projectPath``") | Out-Null
	$lines.Add("- Candidates: $($Report.candidate_count)") | Out-Null
	$lines.Add("- Review candidates: $($Report.review_candidate_count)") | Out-Null
	$lines.Add("- Excluded candidates: $($Report.excluded_candidate_count)") | Out-Null
	$lines.Add("- Source features missing from project: $($missing.Count)") | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add("#### Review Candidates") | Out-Null
	$lines.Add((ConvertTo-MarkdownList -Values $review)) | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add("#### Excluded Candidates") | Out-Null
	$lines.Add((ConvertTo-MarkdownList -Values $excluded)) | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add("#### Source Features Missing From Project") | Out-Null
	$lines.Add((ConvertTo-MarkdownList -Values $missing)) | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add("#### Recommended Action") | Out-Null
	$lines.Add("") | Out-Null
	$lines.Add('```powershell') | Out-Null
	$lines.Add("powershell -NoProfile -ExecutionPolicy Bypass -File tools/learn_pipeline_features.ps1 -ProjectPath '$commandProjectPath'") | Out-Null
	$lines.Add('```') | Out-Null
	return [string]::Join([Environment]::NewLine, $lines)
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

	if ([string]::IsNullOrWhiteSpace($Token)) {
		$Token = [Environment]::GetEnvironmentVariable("GITHUB_TOKEN")
	}
	if ([string]::IsNullOrWhiteSpace($Token)) {
		$Token = [Environment]::GetEnvironmentVariable("GH_TOKEN")
	}

	$reportArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$reportScript,
		"-ProjectPath",
		$ProjectPath,
		"-ExcludePatterns"
	)
	$reportArgs += ($ExcludePatterns -join ",")
	if (-not [string]::IsNullOrWhiteSpace($SourceFeatureListPath)) {
		$reportArgs += "-SourceFeatureListPath"
		$reportArgs += $SourceFeatureListPath
	}
	$reportJson = @(powershell @reportArgs)
	if ($LASTEXITCODE -ne 0) {
		throw "Learning report failed with exit code $LASTEXITCODE"
	}
	$report = ($reportJson -join [Environment]::NewLine) | ConvertFrom-Json

	if ($report.candidate_count -eq 0 -and -not $Force) {
		Write-Host "OK: no project feature candidates to publish."
		exit 0
	}

	$reportBlock = ConvertTo-ReportBlock -Report $report
	if ($DryRun) {
		Write-Host "Would publish SocratexPipeline learning report to GitHub issue:"
		Write-Host "repo: $Owner/$Repo"
		Write-Host "title: $IssueTitle"
		Write-Host "hash: $($report.report_hash)"
		Write-Host $reportBlock
		exit 0
	}

	if ([string]::IsNullOrWhiteSpace($Token)) {
		throw "Missing GitHub token. Set GITHUB_TOKEN or GH_TOKEN, or pass -Token. Use -DryRun to preview without network writes."
	}

	$issuesUri = "https://api.github.com/repos/$Owner/$Repo/issues?state=open&per_page=100"
	$issues = @(Invoke-GitHubApi -Method "Get" -Uri $issuesUri)
	$issue = $issues | Where-Object {
		$_.title -eq $IssueTitle -and -not ($_.PSObject.Properties.Name -contains "pull_request")
	} | Select-Object -First 1

	if ($null -eq $issue) {
		$body = (New-InboxBody) + $reportBlock
		$createUri = "https://api.github.com/repos/$Owner/$Repo/issues"
		$issue = Invoke-GitHubApi -Method "Post" -Uri $createUri -Body @{
			title = $IssueTitle
			body = $body
			labels = @($Labels)
		}
		Write-Host "OK: created GitHub learning inbox issue: $($issue.html_url)"
		exit 0
	}

	$existingBody = [string]$issue.body
	$hashMarker = "socratex-pipeline-learning-report:$($report.report_hash)"
	if ($existingBody.Contains($hashMarker) -and -not $Force) {
		Write-Host "OK: learning report already published to issue #$($issue.number); skipping duplicate."
		Write-Host $issue.html_url
		exit 0
	}

	if (-not $existingBody.Contains("socratex-pipeline-learning-inbox")) {
		$existingBody = (New-InboxBody) + [Environment]::NewLine + $existingBody
	}
	$updatedBody = $existingBody.TrimEnd() + [Environment]::NewLine + $reportBlock
	$updateUri = "https://api.github.com/repos/$Owner/$Repo/issues/$($issue.number)"
	$updated = Invoke-GitHubApi -Method "Patch" -Uri $updateUri -Body @{ body = $updatedBody }
	Write-Host "OK: updated GitHub learning inbox issue: $($updated.html_url)"
} finally {
	Pop-Location
}
