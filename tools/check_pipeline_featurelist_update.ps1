param(
	[string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")

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
	if ($Paths.Count -gt 0) {
		$expanded = [System.Collections.Generic.List[string]]::new()
		foreach ($path in $Paths) {
			foreach ($candidate in ($path -split ",")) {
				$trimmed = $candidate.Trim()
				if ($trimmed.Length -gt 0) {
					$expanded.Add($trimmed.Replace("\", "/")) | Out-Null
				}
			}
		}
		return @($expanded | Sort-Object -Unique)
	}

	$changed = @()
	$changed += @(Invoke-GitLines -Arguments @("diff", "--name-only", "--diff-filter=ACMRD"))
	$changed += @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMRD"))
	$changed += @(Invoke-GitLines -Arguments @("ls-files", "--others", "--exclude-standard"))
	return @($changed | ForEach-Object { ([string]$_).Replace("\", "/") } | Sort-Object -Unique)
}

function Test-PipelineOwnedPath {
	param([string]$Path)

	$normalized = $Path.TrimStart("./")
	if ($normalized -match '^(SocratexAI/)?(tools|core|project|templates|adapters|evals)/') {
		return $true
	}
	if ($normalized -match '^(SocratexAI/)?AI-compiled/') {
		return $true
	}
	if ($normalized -match '^(SocratexAI/)?(AGENTS\.md|PUBLIC-BOOTSTRAP\.md|QUALITY-GATE\.json|pipeline_featurelist\.json)$') {
		return $true
	}
	return $false
}

function Test-FeatureListPath {
	param([string]$Path)

	$normalized = $Path.TrimStart("./")
	return ($normalized -match '^(SocratexAI/)?pipeline_featurelist\.json$')
}

Push-Location -LiteralPath $repoRoot
try {
	$changedPaths = @(Get-ChangedPaths)
	$pipelinePaths = @($changedPaths | Where-Object { Test-PipelineOwnedPath -Path $_ })
	if ($pipelinePaths.Count -eq 0) {
		Write-Host "OK: no pipeline-owned changes; feature list guard skipped."
		exit 0
	}

	$featureListChanged = @($changedPaths | Where-Object { Test-FeatureListPath -Path $_ })
	if ($featureListChanged.Count -gt 0) {
		Write-Host "OK: pipeline feature list changed with pipeline-owned changes."
		exit 0
	}

	Write-Host "ERROR: pipeline-owned changes require a pipeline_featurelist.json update."
	Write-Host "Changed pipeline-owned paths:"
	foreach ($path in $pipelinePaths) {
		Write-Host " - $path"
	}
	Write-Host ""
	Write-Host "If this change adds or improves reusable pipeline behavior, add a feature ID to pipeline_featurelist.json."
	Write-Host "If it is intentionally not a pipeline capability change, keep it outside pipeline-owned paths or split it from pipeline improvement work."
	exit 1
} finally {
	Pop-Location
}
