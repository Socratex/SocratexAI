param(
	[string[]]$Summary = @(),
	[string]$Why = "",
	[string]$Timestamp = "",
	[string]$Path = "CHANGELOG.yaml"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-ChangelogDate {
	param([string]$DateText)

	return [datetime]::ParseExact($DateText, "yyyy-MM-dd HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
}

if ($Summary.Count -eq 0) {
	throw "At least one -Summary line is required."
}

$trimmedSummary = @($Summary | ForEach-Object { $_.Trim() } | Where-Object { $_.Length -gt 0 })
if ($trimmedSummary.Count -eq 0) {
	throw "At least one non-empty -Summary line is required."
}

$autoTimestamp = [string]::IsNullOrWhiteSpace($Timestamp)
$entryDate = if ($autoTimestamp) { Get-Date } else { Get-ChangelogDate -DateText $Timestamp }
$fullPath = Join-Path $repoRoot $Path
if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
	throw "Missing changelog file: $Path"
}

$content = Get-Content -Raw -LiteralPath $fullPath -Encoding UTF8
if ($content -notmatch '^# Changelog\s*') {
	throw "Changelog must start with '# Changelog'."
}

$headings = @(Select-String -LiteralPath $fullPath -Pattern '^##\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})\s*$' -Encoding UTF8)
if ($headings.Count -gt 0) {
	$lastHeading = $headings[$headings.Count - 1]
	$lastDate = Get-ChangelogDate -DateText $lastHeading.Matches[0].Groups[1].Value
	if ($autoTimestamp -and $entryDate -lt $lastDate) {
		$entryDate = $lastDate.AddMinutes(1)
	}
	if ($entryDate -lt $lastDate) {
		throw "Refusing to append an older changelog timestamp. Last entry is $($lastDate.ToString("yyyy-MM-dd HH:mm")); requested $($entryDate.ToString("yyyy-MM-dd HH:mm"))."
	}
}
$Timestamp = $entryDate.ToString("yyyy-MM-dd HH:mm")

$entryLines = New-Object System.Collections.Generic.List[string]
$entryLines.Add("## $Timestamp") | Out-Null
foreach ($line in $trimmedSummary) {
	$entryLines.Add("- $line") | Out-Null
}
if (-not [string]::IsNullOrWhiteSpace($Why)) {
	$compassEmoji = [char]::ConvertFromUtf32(0x1F9ED)
	$entryLines.Add("- $compassEmoji Why: $($Why.Trim())") | Out-Null
}

$normalized = $content.TrimEnd()
$newContent = $normalized + "`n`n" + (($entryLines -join "`n").TrimEnd()) + "`n"
[System.IO.File]::WriteAllText($fullPath, $newContent, $utf8NoBom)
Write-Host "OK: appended changelog entry at $Timestamp."
