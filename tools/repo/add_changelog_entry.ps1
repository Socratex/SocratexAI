param(
	[string[]]$Summary = @(),
	[string]$Why = "",
	[string]$Feature = "manual_changelog_entry",
	[string]$Version = "0.2.0-alpha",
	[string]$Timestamp = "",
	[string]$Path = "CHANGELOG.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-ChangelogDate {
	param([string]$DateText)

	return [datetime]::ParseExact($DateText, "yyyy-MM-dd HH:mm", [System.Globalization.CultureInfo]::InvariantCulture)
}

function Test-ChangelogDate {
	param([string]$DateText)

	if ([string]::IsNullOrWhiteSpace($DateText)) {
		return $true
	}

	$parsed = [datetime]::MinValue
	return [datetime]::TryParseExact(
		$DateText,
		"yyyy-MM-dd HH:mm",
		[System.Globalization.CultureInfo]::InvariantCulture,
		[System.Globalization.DateTimeStyles]::None,
		[ref]$parsed
	)
}

function Add-JsonChangelogEntry {
	param(
		[string]$Content,
		[string]$FullPath,
		[datetime]$EntryDate,
		[string]$EntryFeature,
		[string]$EntryVersion,
		[string[]]$EntrySummary,
		[string]$EntryWhy
	)

	$document = $Content | ConvertFrom-Json
	if (-not $document.PSObject.Properties.Name.Contains("entries")) {
		throw "JSON changelog must contain top-level entries field."
	}

	$change = ($EntrySummary -join " ").Trim()
	if (-not [string]::IsNullOrWhiteSpace($EntryWhy)) {
		$change = "$change Why: $($EntryWhy.Trim())"
	}

	$entries = @($document.entries)
	$entries += [pscustomobject]@{
		version = $EntryVersion
		date = $EntryDate.ToString("yyyy-MM-dd")
		feature = $EntryFeature
		change = $change
	}
	$document.entries = $entries
	$newContent = ($document | ConvertTo-Json -Depth 8) + [Environment]::NewLine
	[System.IO.File]::WriteAllText($FullPath, $newContent, $utf8NoBom)
	Write-Host "OK: appended JSON changelog entry for $EntryFeature."
}

if (-not (Test-ChangelogDate -DateText $Timestamp)) {
	throw "Invalid -Timestamp value '$Timestamp'. If this was intended as another summary line, pass -Summary as an explicit array: -Summary @('line one','line two')."
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
$fullPath = if ([System.IO.Path]::IsPathRooted($Path)) { $Path } else { Join-Path $repoRoot $Path }
if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
	throw "Missing changelog file: $Path"
}

$content = Get-Content -Raw -LiteralPath $fullPath -Encoding UTF8

if ([System.IO.Path]::GetExtension($fullPath) -eq ".json") {
	Add-JsonChangelogEntry -Content $content -FullPath $fullPath -EntryDate $entryDate -EntryFeature $Feature -EntryVersion $Version -EntrySummary $trimmedSummary -EntryWhy $Why
	exit 0
}

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
