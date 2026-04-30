param(
	[string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$unsafeCommands = "\b(Set-Content|Out-File|Add-Content)\b"
$violations = [System.Collections.Generic.List[string]]::new()

function Get-AddedLineNumbers {
	param([string]$Path)

	$previousErrorActionPreference = $ErrorActionPreference
	$ErrorActionPreference = "Continue"
	$tracked = git ls-files --error-unmatch -- $Path 2>$null
	if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tracked)) {
		$ErrorActionPreference = $previousErrorActionPreference
		return $null
	}

	$diffLines = @(git diff --unified=0 -- $Path)
	$ErrorActionPreference = $previousErrorActionPreference
	$lineNumbers = [System.Collections.Generic.HashSet[int]]::new()
	$currentNewLine = 0
	foreach ($diffLine in $diffLines) {
		if ($diffLine -match '^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@') {
			$currentNewLine = [int]$Matches[1]
			continue
		}
		if ($diffLine.StartsWith("+++") -or $diffLine.StartsWith("---")) {
			continue
		}
		if ($diffLine.StartsWith("+")) {
			$lineNumbers.Add($currentNewLine) | Out-Null
			$currentNewLine += 1
			continue
		}
		if ($diffLine.StartsWith("-")) {
			continue
		}
		if ($currentNewLine -gt 0) {
			$currentNewLine += 1
		}
	}
	return $lineNumbers
}

Push-Location -LiteralPath $repoRoot
try {
	foreach ($path in $Paths) {
		if ([string]::IsNullOrWhiteSpace($path)) {
			continue
		}
		if ($path -notmatch "\.ps1$") {
			continue
		}
		if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
			continue
		}
		$addedLineNumbers = Get-AddedLineNumbers -Path $path
		$lines = @(Get-Content -LiteralPath $path -Encoding UTF8)
		for ($index = 0; $index -lt $lines.Count; $index++) {
			$lineNumber = $index + 1
			if ($null -ne $addedLineNumbers -and -not $addedLineNumbers.Contains($lineNumber)) {
				continue
			}
			$line = [string]$lines[$index]
			$trimmed = $line.Trim()
			if ($trimmed.StartsWith("#")) {
				continue
			}
			if ($path -like "*check_utf8_writes.ps1" -and $line -match '\$unsafeCommands') {
				continue
			}
			if ($line -match $unsafeCommands) {
				$violations.Add("${path}:${lineNumber}: use Write-Utf8File / tools\write_utf8_file.ps1 instead of $($Matches[1])")
			}
		}
	}
} finally {
	Pop-Location
}

if ($violations.Count -gt 0) {
	Write-Host "ERROR: unsafe PowerShell text writes found:"
	foreach ($violation in $violations) {
		Write-Host " - $violation"
	}
	exit 1
}

Write-Host "OK: no unsafe PowerShell text writes in checked paths"
