param(
	[string[]]$Paths = @(),
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$utf8Strict = [System.Text.UTF8Encoding]::new($false, $true)
$centralEuropean = [System.Text.Encoding]::GetEncoding(1250)
$westernEuropean = [System.Text.Encoding]::GetEncoding(1252)
$changedFiles = New-Object System.Collections.Generic.List[string]

function Get-RelativePath {
	param([string]$Path)

	$fullPath = [System.IO.Path]::GetFullPath($Path)
	$root = [System.IO.Path]::GetFullPath($repoRoot)
	if (-not $root.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
		$root = "$root$([System.IO.Path]::DirectorySeparatorChar)"
	}

	if ($fullPath.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
		return $fullPath.Substring($root.Length).Replace('\', '/')
	}

	return $fullPath
}

function Get-SuspicionScore {
	param([string]$Text)

	$score = 0
	$markers = @(
		[char]0x00C2,
		[char]0x00C4,
		[char]0x00C5,
		[char]0x00E2,
		[char]0x0103,
		[char]0x010F,
		[char]0x0110,
		[char]0x0111,
		[char]0x0139,
		[char]0x015F,
		[char]0x0161,
		[char]0xFFFD
	)

	foreach ($marker in $markers) {
		$score += ([regex]::Matches($Text, [regex]::Escape([string]$marker))).Count
	}

	for ($i = 0; $i -lt $Text.Length; $i++) {
		$code = [int][char]$Text[$i]
		if ($code -ge 0x0080 -and $code -le 0x009F) {
			$score += 1
		}
	}

	return $score
}

function Convert-MojibakeToken {
	param([string]$Token)

	$originalScore = Get-SuspicionScore -Text $Token
	if ($originalScore -eq 0) {
		return $Token
	}

	$bestText = $Token
	$bestScore = $originalScore

	foreach ($encoding in @($centralEuropean, $westernEuropean)) {
		try {
			$bytes = $encoding.GetBytes($Token)
			$candidate = $utf8Strict.GetString($bytes)
			$candidateScore = Get-SuspicionScore -Text $candidate
			if ($candidateScore -lt $bestScore -and -not $candidate.Contains([char]0xFFFD)) {
				$bestText = $candidate
				$bestScore = $candidateScore
			}
		} catch {
			continue
		}
	}

	return $bestText
}

function Repair-Text {
	param([string]$Text)

	return [regex]::Replace(
		$Text,
		'[^\x00-\x7F]+',
		{
			param($Match)
			return Convert-MojibakeToken -Token $Match.Value
		}
	)
}

function Get-DefaultTargets {
	$files = New-Object System.Collections.Generic.List[string]
	$tracked = & git -C $repoRoot ls-files "*.md" "*.json" "*.json" "*.ps1"
	if ($LASTEXITCODE -ne 0) {
		throw "git ls-files failed."
	}

	foreach ($path in $tracked) {
		if ([string]::IsNullOrWhiteSpace($path)) {
			continue
		}
		$files.Add((Join-Path $repoRoot $path)) | Out-Null
	}

	return $files
}

Push-Location -LiteralPath $repoRoot
try {
	if ($Paths.Count -eq 0) {
		$targetPaths = @(Get-DefaultTargets)
	} else {
		$targetPaths = @($Paths | ForEach-Object { Join-Path $repoRoot $_ })
	}

	foreach ($path in $targetPaths) {
		if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
			if ($Paths.Count -eq 0) {
				continue
			}
			throw "Missing target file: $path"
		}

		$content = [System.IO.File]::ReadAllText($path, $utf8NoBom)
		$repaired = Repair-Text -Text $content
		if ($repaired -eq $content) {
			continue
		}

		$relativePath = Get-RelativePath -Path $path
		$changedFiles.Add($relativePath) | Out-Null
		if (-not $Check) {
			[System.IO.File]::WriteAllText($path, $repaired, $utf8NoBom)
		}
	}

	if ($changedFiles.Count -gt 0) {
		foreach ($file in $changedFiles) {
			Write-Host "MOJIBAKE: $file"
		}

		if ($Check) {
			throw "mojibake repair check failed with $($changedFiles.Count) file(s) needing repair."
		}

		Write-Host "OK: repaired mojibake in $($changedFiles.Count) file(s)."
	} else {
		Write-Host "OK: no mojibake repairs needed."
	}
} finally {
	Pop-Location
}
