param(
	[string[]]$Paths = @("AGENTS.md", "DOCS.yaml"),
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Convert-TextToLf {
	param(
		[string]$Text
	)

	$normalized = $Text -replace "`r`n", "`n"
	$normalized = $normalized -replace "`r", "`n"
	return $normalized
}

function Get-TextFileContent {
	param(
		[string]$Path
	)

	$bytes = [System.IO.File]::ReadAllBytes($Path)
	return $utf8NoBom.GetString($bytes)
}

Push-Location -LiteralPath $repoRoot
try {
	$changedPaths = New-Object System.Collections.Generic.List[string]
	$expandedPaths = New-Object System.Collections.Generic.List[string]

	foreach ($path in $Paths) {
		foreach ($expandedPath in ($path -split ",")) {
			$trimmedPath = $expandedPath.Trim()
			if ($trimmedPath.Length -gt 0) {
				$expandedPaths.Add($trimmedPath)
			}
		}
	}

	foreach ($path in $expandedPaths) {
		$resolvedPath = Resolve-Path -LiteralPath $path
		$content = Get-TextFileContent -Path $resolvedPath
		$normalizedContent = Convert-TextToLf -Text $content
		$normalizedBytes = $utf8NoBom.GetBytes($normalizedContent)
		$currentBytes = [System.IO.File]::ReadAllBytes($resolvedPath)
		$needsWrite = $currentBytes.Length -ne $normalizedBytes.Length

		if (-not $needsWrite) {
			for ($index = 0; $index -lt $currentBytes.Length; $index++) {
				if ($currentBytes[$index] -ne $normalizedBytes[$index]) {
					$needsWrite = $true
					break
				}
			}
		}

		if ($needsWrite) {
			$changedPaths.Add($path)
			if (-not $Check) {
				[System.IO.File]::WriteAllBytes($resolvedPath, $normalizedBytes)
			}
		}
	}

	if ($changedPaths.Count -eq 0) {
		Write-Host "OK: text files already normalized"
		exit 0
	}

	if ($Check) {
		Write-Host "ERROR: text files need normalization:"
		foreach ($path in $changedPaths) {
			Write-Host " - $path"
		}
		exit 1
	}

	Write-Host "OK: normalized text files:"
	foreach ($path in $changedPaths) {
		Write-Host " - $path"
	}
} finally {
	Pop-Location
}
