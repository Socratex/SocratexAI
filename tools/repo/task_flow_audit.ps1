param(
	[string[]]$Paths = @(),
	[string]$ProjectRoot = "",
	[string]$ChangelogPath = "",
	[switch]$Complex,
	[switch]$NoChangelog,
	[switch]$RequireClosureEvidence,
	[string]$ClosureEvidencePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-WorkTreeRoot {
	param([string]$FallbackRoot)

	$gitRoot = @(git -C $FallbackRoot rev-parse --show-toplevel 2>$null)
	if ($LASTEXITCODE -eq 0 -and $gitRoot.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$gitRoot[0])) {
		return (Resolve-Path -LiteralPath ([string]$gitRoot[0])).Path
	}
	return (Resolve-Path -LiteralPath $FallbackRoot).Path
}

$packageRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$repoRoot = if ([string]::IsNullOrWhiteSpace($ProjectRoot)) {
	Resolve-WorkTreeRoot -FallbackRoot $packageRoot
} else {
	(Resolve-Path -LiteralPath $ProjectRoot).Path
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
	if ($Paths.Count -gt 0) {
		$result = New-Object System.Collections.Generic.List[string]
		foreach ($path in $Paths) {
			foreach ($candidate in ($path -split ",")) {
				$trimmed = $candidate.Trim()
				if ($trimmed.Length -gt 0) {
					$result.Add($trimmed)
				}
			}
		}
		return @($result | Sort-Object -Unique)
	}

	$changed = @()
	if (Test-Path -LiteralPath ".git") {
		$changed += @(Invoke-GitLines -Arguments @("diff", "--name-only", "--diff-filter=ACMRD"))
		$changed += @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMRD"))
		$changed += @(Invoke-GitLines -Arguments @("ls-files", "--others", "--exclude-standard"))
	}
	return @($changed | Sort-Object -Unique)
}

function Get-FirstExistingChangelogPath {
	if (-not [string]::IsNullOrWhiteSpace($ChangelogPath)) {
		return $ChangelogPath
	}

	foreach ($candidate in @("CHANGELOG.json", "CHANGELOG.md")) {
		if (Test-Path -LiteralPath $candidate -PathType Leaf) {
			return $candidate
		}
	}
	return ""
}

function Get-LatestJsonChangelogEntry {
	param([string]$Path)

	$document = Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json
	$changelog = $document
	if ($document.PSObject.Properties.Name.Contains("content") -and $null -ne $document.content) {
		$changelog = $document.content
	}
	if (-not $changelog.PSObject.Properties.Name.Contains("entries")) {
		return ""
	}

	$entries = @($changelog.entries)
	if ($entries.Count -eq 0) {
		return ""
	}

	$entry = $entries[$entries.Count - 1]
	$parts = @()
	foreach ($name in @("date", "feature", "change")) {
		if ($entry.PSObject.Properties.Name.Contains($name)) {
			$value = [string]$entry.$name
			if (-not [string]::IsNullOrWhiteSpace($value)) {
				$parts += "${name}: $value"
			}
		}
	}
	return ($parts -join " | ")
}

function Get-LatestMarkdownChangelogEntry {
	param([string]$Path)

	$lines = @(Get-Content -LiteralPath $Path -Encoding UTF8)
	$headingIndexes = New-Object System.Collections.Generic.List[int]
	for ($index = 0; $index -lt $lines.Count; $index += 1) {
		if ($lines[$index] -match '^##\s+') {
			$headingIndexes.Add($index)
		}
	}
	if ($headingIndexes.Count -eq 0) {
		return ""
	}

	$start = $headingIndexes[$headingIndexes.Count - 1]
	$entryLines = New-Object System.Collections.Generic.List[string]
	for ($index = $start; $index -lt $lines.Count; $index += 1) {
		$line = [string]$lines[$index]
		if ($index -gt $start -and $line -match '^##\s+') {
			break
		}
		if (-not [string]::IsNullOrWhiteSpace($line)) {
			$entryLines.Add($line.Trim())
		}
	}
	return (($entryLines | Select-Object -First 8) -join " ")
}

function Get-LatestChangelogEntry {
	param([string]$Path)

	if ([string]::IsNullOrWhiteSpace($Path) -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
		return ""
	}

	if ([System.IO.Path]::GetExtension($Path).ToLowerInvariant() -eq ".json") {
		return Get-LatestJsonChangelogEntry -Path $Path
	}
	return Get-LatestMarkdownChangelogEntry -Path $Path
}

function Test-ComplexTaskShape {
	param([string[]]$ChangedPaths)

	if ($Complex) {
		return $true
	}
	if ($ChangedPaths.Count -ge 6) {
		return $true
	}
	foreach ($path in $ChangedPaths) {
		$normalized = $path.Replace("\", "/")
		if ($normalized -match '(^|/)(core|project|profiles|tools|context-docs|docs-tech|templates)/') {
			return $true
		}
		if ($normalized -match '(^|/)(FLOWS|WORKFLOW|COMMANDS|SCRIPTS|pipeline_featurelist|_PLAN)\.json$') {
			return $true
		}
	}
	return $false
}

function Test-NonEmptyEvidenceValue {
	param(
		[object]$Evidence,
		[string]$PropertyName
	)

	if (-not ($Evidence.PSObject.Properties.Name -contains $PropertyName)) {
		return $false
	}
	$value = $Evidence.$PropertyName
	if ($null -eq $value) {
		return $false
	}
	if ($value -is [string]) {
		return -not [string]::IsNullOrWhiteSpace($value)
	}
	if ($value -is [System.Collections.IEnumerable]) {
		return @($value).Count -gt 0
	}
	return $true
}

function Test-ClosureEvidence {
	param(
		[string]$Path,
		[bool]$IsComplex
	)

	if ([string]::IsNullOrWhiteSpace($Path)) {
		throw "Closure evidence is required. Pass -ClosureEvidencePath <json>."
	}
	if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
		throw "Closure evidence file not found: $Path"
	}

	$evidence = Get-Content -Raw -LiteralPath $Path -Encoding UTF8 | ConvertFrom-Json
	$required = @(
		"context_route",
		"flow_execution",
		"closure_evidence",
		"changelog_truth",
		"tool_failure_response",
		"tool_discipline"
	)
	foreach ($name in $required) {
		if (-not (Test-NonEmptyEvidenceValue -Evidence $evidence -PropertyName $name)) {
			throw "Closure evidence is missing or empty: $name"
		}
	}

	if (-not ($evidence.closure_evidence.PSObject.Properties.Name -contains "changed_files") -or @($evidence.closure_evidence.changed_files).Count -eq 0) {
		throw "Closure evidence must include closure_evidence.changed_files."
	}
	if (-not ($evidence.closure_evidence.PSObject.Properties.Name -contains "verification_commands") -or @($evidence.closure_evidence.verification_commands).Count -eq 0) {
		throw "Closure evidence must include closure_evidence.verification_commands."
	}
	if ($IsComplex -and -not (Test-NonEmptyEvidenceValue -Evidence $evidence -PropertyName "adversarial_review")) {
		throw "Complex task closure evidence must include adversarial_review."
	}

	Write-Host ""
	Write-Host "OK: closure evidence file satisfies task-flow audit contract: $Path"
}

Push-Location -LiteralPath $repoRoot
try {
	$changedPaths = @(Get-ChangedPaths)
	$changelog = Get-FirstExistingChangelogPath
	$latestChangelogEntry = if ($NoChangelog) { "" } else { Get-LatestChangelogEntry -Path $changelog }
	$isComplex = Test-ComplexTaskShape -ChangedPaths $changedPaths

	Write-Host "==> task flow audit"
	Write-Host "Changed path count: $($changedPaths.Count)"
	if ($changedPaths.Count -gt 0) {
		foreach ($path in ($changedPaths | Select-Object -First 40)) {
			Write-Host "- $path"
		}
		if ($changedPaths.Count -gt 40) {
			Write-Host "... truncated $($changedPaths.Count - 40) path(s)"
		}
	}

	Write-Host ""
	Write-Host "Required closure artifacts:"
	Write-Host "- context_route: cite loaded FLOWS/WORKFLOW/DOCS/STATE/plan/context records that were relevant."
	Write-Host "- flow_execution: cite the selected flow and the concrete steps/subroutines followed."
	Write-Host "- closure_evidence: cite changed files, verification commands, generated artifacts, and remaining risk; do not close with prose only."
	Write-Host "- changelog_truth: state whether changelog was updated from actual shipped changes; if not needed, state why."
	Write-Host "- tool_failure_response: if a tool failed mechanically, state whether the tool or its input contract was fixed; if no tool failed, state that."
	Write-Host "- tool_discipline: state which repo tools/scripts were used and which edits were manual."

	if (-not $NoChangelog) {
		Write-Host ""
		if ([string]::IsNullOrWhiteSpace($changelog)) {
			Write-Host "Changelog: no changelog file found; closure must justify why no changelog artifact exists."
		} elseif ([string]::IsNullOrWhiteSpace($latestChangelogEntry)) {
			Write-Host "Changelog: $changelog exists but no latest entry was detected; closure must justify/update it when required."
		} else {
			Write-Host "Latest changelog artifact from ${changelog}:"
			Write-Host $latestChangelogEntry
		}
	}

	if ($isComplex) {
		Write-Host ""
		Write-Host "Complex-task adversarial review required from changelog artifact:"
		Write-Host "- Re-read the changelog claim as if it were a bug report about this diff."
		Write-Host "- Check whether the diff actually implements the claim, not just the intended direction."
		Write-Host "- Check for missing verification, hidden scope expansion, tool bypass, stale plan/state, and future retrofit debt."
		Write-Host "- Report one concise pass/fail/risk result in closure."
	}

	if ($RequireClosureEvidence) {
		Test-ClosureEvidence -Path $ClosureEvidencePath -IsComplex $isComplex
	}
} finally {
	Pop-Location
}
