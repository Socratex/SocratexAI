param(
	[string[]]$Paths = @(),
	[string]$DefaultEmoji = "🧭",
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-ProjectMarkdownPaths {
	$files = @(git ls-files "*.md")
	return @($files | Where-Object {
		$_ -notmatch '(^|/)Tools/Python312/' -and
		$_ -notmatch '(^|/)Tools/python-installer/' -and
		$_ -notmatch '(^|/)Tools/tmp/'
	})
}

function Get-TargetPaths {
	if ($Paths.Count -eq 0) {
		return @(Get-ProjectMarkdownPaths)
	}

	$targetPaths = New-Object System.Collections.Generic.List[string]
	foreach ($path in $Paths) {
		foreach ($expandedPath in ($path -split ",")) {
			$trimmedPath = $expandedPath.Trim()
			if ($trimmedPath.Length -gt 0) {
				$targetPaths.Add($trimmedPath)
			}
		}
	}
	return @($targetPaths)
}

function Test-StartsWithEmojiOrSymbol {
	param([string]$Text)

	if ([string]::IsNullOrWhiteSpace($Text)) {
		return $true
	}

	$trimmed = $Text.TrimStart()
	$firstChar = [string]$trimmed[0]
	return $firstChar -match '[^\x00-\x7F]'
}

function Add-EmojiToTocItemLine {
	param(
		[string]$Line,
		[string]$Emoji
	)

	$taskMatch = [regex]::Match($Line, '^(\s*(?:[-*+]|\d+[.)])\s+\[[ xX]\]\s+)(.*)$')
	if ($taskMatch.Success) {
		$prefix = $taskMatch.Groups[1].Value
		$text = $taskMatch.Groups[2].Value
		if (Test-StartsWithEmojiOrSymbol -Text $text) {
			return $Line
		}
		return "$prefix$Emoji $text"
	}

	$listMatch = [regex]::Match($Line, '^(\s*(?:[-*+]|\d+[.)])\s+)(.*)$')
	if (-not $listMatch.Success) {
		return $Line
	}

	$prefix = $listMatch.Groups[1].Value
	$text = $listMatch.Groups[2].Value
	if (Test-StartsWithEmojiOrSymbol -Text $text) {
		return $Line
	}

	return "$prefix$Emoji $text"
}

function Add-EmojiToHeadingLine {
	param(
		[string]$Line,
		[string]$Emoji
	)

	$headingMatch = [regex]::Match($Line, '^(#{1,6}\s+)(.*)$')
	if (-not $headingMatch.Success) {
		return $Line
	}

	$prefix = $headingMatch.Groups[1].Value
	$text = $headingMatch.Groups[2].Value
	if (Test-StartsWithEmojiOrSymbol -Text $text) {
		return $Line
	}

	return "$prefix$Emoji $text"
}

function Test-IsParagraphStartLine {
	param(
		[string[]]$Lines,
		[int]$Index
	)

	$line = $Lines[$Index]
	if ([string]::IsNullOrWhiteSpace($line)) {
		return $false
	}
	if ($line -match '^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*|\|)') {
		return $false
	}
	if ($line -match '^\s*(```|~~~|---+\s*$|\*\*\*+\s*$|___+\s*$|<!--)') {
		return $false
	}
	if (Test-StartsWithEmojiOrSymbol -Text $line) {
		return $false
	}

	for ($previousIndex = $Index - 1; $previousIndex -ge 0; $previousIndex--) {
		$previous = $Lines[$previousIndex]
		if ([string]::IsNullOrWhiteSpace($previous)) {
			return $true
		}
		if ($previous -match '^\s*(#{1,6}\s+|[-*+]\s+|\d+[.)]\s+|>\s*|\|)') {
			return $true
		}
		if ($previous -match '^\s*(```|~~~|---+\s*$|\*\*\*+\s*$|___+\s*$|<!--)') {
			return $true
		}
		return $false
	}

	return $true
}

function Add-EmojiToParagraphStartLine {
	param(
		[string]$Line,
		[string]$Emoji
	)

	$paragraphMatch = [regex]::Match($Line, '^(\s*)(.*)$')
	$indent = $paragraphMatch.Groups[1].Value
	$text = $paragraphMatch.Groups[2].Value
	return "$indent$Emoji $text"
}

function Convert-MarkdownEmoji {
	param(
		[string]$Content,
		[string]$Emoji
	)

	$normalized = $Content -replace "`r`n", "`n"
	$normalized = $normalized -replace "`r", "`n"
	$lines = $normalized -split "`n", -1
	$tocIndex = -1

	for ($index = 0; $index -lt [Math]::Min($lines.Count, 80); $index++) {
		$line = $lines[$index]
		if ($line -match '^##\s+(TOC|Table of Contents|Contents|Index)\s*$') {
			$tocIndex = $index
			break
		}
		if ($line -match '^##\s+' -and $line -notmatch '^##\s+(TOC|Table of Contents|Contents|Index)\s*$') {
			break
		}
	}

	$inFence = $false
	for ($index = 0; $index -lt $lines.Count; $index++) {
		$line = $lines[$index]
		if ($line -match '^\s*(```|~~~)') {
			$inFence = -not $inFence
			continue
		}
		if ($inFence) {
			continue
		}

		if ($line -match '^#{1,6}\s+') {
			$lines[$index] = Add-EmojiToHeadingLine -Line $line -Emoji $Emoji
			continue
		}

		if (Test-IsParagraphStartLine -Lines $lines -Index $index) {
			$lines[$index] = Add-EmojiToParagraphStartLine -Line $line -Emoji $Emoji
		}
	}

	if ($tocIndex -lt 0) {
		return ($lines -join "`n")
	}

	$inFence = $false
	for ($index = $tocIndex + 1; $index -lt $lines.Count; $index++) {
		$line = $lines[$index]
		if ($line -match '^\s*(```|~~~)') {
			$inFence = -not $inFence
			continue
		}
		if ($inFence) {
			continue
		}
		if ($line -match '^##\s+') {
			break
		}
		if ($line -match '^\s*(?:[-*+]|\d+[.)])\s+') {
			$lines[$index] = Add-EmojiToTocItemLine -Line $line -Emoji $Emoji
		}
	}

	return ($lines -join "`n")
}

Push-Location -LiteralPath $repoRoot
try {
	$targetPaths = @(Get-TargetPaths)
	$changedPaths = New-Object System.Collections.Generic.List[string]

	foreach ($path in $targetPaths) {
		$resolvedPath = Resolve-Path -LiteralPath $path
		$content = $utf8NoBom.GetString([System.IO.File]::ReadAllBytes($resolvedPath))
		if ($content.StartsWith([string][char]0xFEFF)) {
			$content = $content.Substring(1)
		}
		$updatedContent = Convert-MarkdownEmoji -Content $content -Emoji $DefaultEmoji

		if ($updatedContent -ne $content) {
			$changedPaths.Add($path)
			if (-not $Check) {
				[System.IO.File]::WriteAllBytes($resolvedPath, $utf8NoBom.GetBytes($updatedContent))
			}
		}
	}

	if ($changedPaths.Count -eq 0) {
		Write-Host "OK: markdown TOC and paragraph emoji already normalized"
		exit 0
	}

	if ($Check) {
		Write-Host "ERROR: markdown files need TOC or paragraph emoji normalization:"
		foreach ($path in $changedPaths) {
			Write-Host " - $path"
		}
		exit 1
	}

	Write-Host "OK: normalized markdown TOC and paragraph emoji:"
	foreach ($path in $changedPaths) {
		Write-Host " - $path"
	}
} finally {
	Pop-Location
}
