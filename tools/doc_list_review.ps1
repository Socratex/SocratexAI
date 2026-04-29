param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Key = "",
	[ValidateSet("item", "document")]
	[string]$Scope = "document",
	[string]$Text = "",
	[string]$Url = "",
	[string[]]$Terms = @(),
	[int]$Limit = 12,
	[switch]$Json,
	[switch]$FailOnDuplicate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$checkScript = Join-Path $PSScriptRoot "doc_list_check.ps1"
$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}
$docListItemScript = Join-Path $PSScriptRoot "doc_list_item.py"

function Convert-JsonOutput {
	param(
		[string[]]$Lines
	)

	$text = ($Lines -join "`n").Trim()
	if ($text.Length -eq 0) {
		return @()
	}
	$result = $text | ConvertFrom-Json
	if ($null -eq $result) {
		return @()
	}
	return @($result)
}

function Write-CandidateSummary {
	param(
		[object[]]$Candidates
	)

	if ($Candidates.Count -eq 0) {
		Write-Host "OK: no candidate duplicates"
		return
	}

	Write-Host ("CANDIDATES: {0} title(s)" -f $Candidates.Count)
	foreach ($candidate in $Candidates) {
		$terms = @($candidate.matched_terms) -join ", "
		Write-Host ("- {0} [{1}]" -f $candidate.title, $candidate.key)
		Write-Host ("  terms: {0}" -f $terms)
		Write-Host ("  excerpt: {0}" -f $candidate.excerpt)
	}
}

$checkArgs = @("-Path", $Path, "-Scope", $Scope, "-Limit", [string]$Limit, "-Json")
if ($Key -ne "") { $checkArgs += @("-Key", $Key) }
if ($Text -ne "") { $checkArgs += @("-Text", $Text) }
if ($Url -ne "") { $checkArgs += @("-Url", $Url) }
if ($Terms.Count -gt 0) { $checkArgs += @("-Terms") + $Terms }

$candidateOutput = @(& powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript @checkArgs)
if ($LASTEXITCODE -ne 0) {
	throw "doc_list_review check failed with exit code $LASTEXITCODE"
}
$candidates = @(Convert-JsonOutput -Lines $candidateOutput)

$items = @()
if ($Terms.Count -gt 0 -and $candidates.Count -gt 0) {
	$titles = @($candidates | ForEach-Object { [string]$_.title } | Select-Object -Unique)
	$readArgs = @($docListItemScript, "read-titles", $Path, "--titles") + $titles + @("--json")
	$itemOutput = @(& $python @readArgs)
	if ($LASTEXITCODE -ne 0) {
		throw "doc_list_review read-titles failed with exit code $LASTEXITCODE"
	}
	$items = @(Convert-JsonOutput -Lines $itemOutput)
}

if ($Json) {
	[ordered]@{
		candidates = $candidates
		items = $items
	} | ConvertTo-Json -Depth 8
} else {
	Write-CandidateSummary -Candidates $candidates
	if ($Terms.Count -gt 0 -and $candidates.Count -gt 0) {
		Write-Host ""
		$titles = @($candidates | ForEach-Object { [string]$_.title } | Select-Object -Unique)
		$readArgs = @($docListItemScript, "read-titles", $Path, "--titles") + $titles
		& $python @readArgs
		if ($LASTEXITCODE -ne 0) {
			throw "doc_list_review read-titles failed with exit code $LASTEXITCODE"
		}
	}
}

if ($FailOnDuplicate -and $candidates.Count -gt 0) {
	throw "doc_list_review found $($candidates.Count) candidate duplicate(s)"
}
