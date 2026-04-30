param(
	[string[]]$Paths = @()
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$unsafeCommands = "\b(Set-Content|Out-File|Add-Content)\b"
$violations = [System.Collections.Generic.List[string]]::new()

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
		$lines = @(Get-Content -LiteralPath $path -Encoding UTF8)
		for ($index = 0; $index -lt $lines.Count; $index++) {
			$line = [string]$lines[$index]
			$trimmed = $line.Trim()
			if ($trimmed.StartsWith("#")) {
				continue
			}
			if ($path -like "*check_utf8_writes.ps1" -and $line -match '\$unsafeCommands') {
				continue
			}
			if ($line -match $unsafeCommands) {
				$violations.Add("${path}:$($index + 1): use Write-Utf8File / tools\write_utf8_file.ps1 instead of $($Matches[1])")
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
