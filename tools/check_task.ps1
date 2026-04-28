param(
	[string[]]$Paths = @(),
	[switch]$Audit,
	[switch]$MarkdownEmoji,
	[switch]$NoLineIndex,
	[switch]$NoNormalize,
	[switch]$NoStat,
	[switch]$NoStatus
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$textNormalizeScript = Join-Path $PSScriptRoot "normalize_text_files.ps1"
$markdownEmojiScript = Join-Path $PSScriptRoot "normalize_markdown_emoji.ps1"
$auditScript = Join-Path $PSScriptRoot "audit_docs.ps1"
$lineIndexScript = Join-Path $PSScriptRoot "update_code_line_index.ps1"

function Invoke-CheckCommand {
	param(
		[string]$Label,
		[string]$Command,
		[string[]]$Arguments = @()
	)

	Write-Host ""
	Write-Host "==> $Label"
	& $Command @Arguments
	if ($LASTEXITCODE -ne 0) {
		throw "$Label failed with exit code $LASTEXITCODE"
	}
}

function Get-ChangedTextPaths {
	$changed = @(git diff --name-only --diff-filter=ACMR)
	$changed += @(git diff --cached --name-only --diff-filter=ACMR)
	return @($changed | Where-Object {
		$_ -match '\.(md|txt|json|ya?ml|cfg|gd|tscn|tres|ps1|py)$'
	} | Sort-Object -Unique)
}

function Get-CheckPaths {
	if ($Paths.Count -eq 0) {
		return @(Get-ChangedTextPaths)
	}

	$expanded = New-Object System.Collections.Generic.List[string]
	foreach ($path in $Paths) {
		foreach ($candidate in ($path -split ",")) {
			$trimmed = $candidate.Trim()
			if ($trimmed.Length -gt 0) {
				$expanded.Add($trimmed)
			}
		}
	}
	return @($expanded)
}

Push-Location -LiteralPath $repoRoot
try {
	$checkPaths = @(Get-CheckPaths)

	if (-not $NoNormalize) {
		if ($checkPaths.Count -gt 0) {
			$textNormalizeArgs = @(
				"-NoProfile",
				"-ExecutionPolicy",
				"Bypass",
				"-File",
				$textNormalizeScript,
				"-Check",
				"-Paths"
			)
			$textNormalizeArgs += $checkPaths
			Invoke-CheckCommand -Label "text normalization check" -Command "powershell" -Arguments $textNormalizeArgs
		} else {
			Write-Host ""
			Write-Host "==> text normalization check"
			Write-Host "skipped; no changed text paths and no -Paths were provided"
		}
	}

	if ($MarkdownEmoji) {
		if ($checkPaths.Count -gt 0) {
			$markdownEmojiArgs = @(
				"-NoProfile",
				"-ExecutionPolicy",
				"Bypass",
				"-File",
				$markdownEmojiScript,
				"-Check",
				"-Paths"
			)
			$markdownEmojiArgs += $checkPaths
			Invoke-CheckCommand -Label "markdown emoji normalization check" -Command "powershell" -Arguments $markdownEmojiArgs
		} else {
			Write-Host ""
			Write-Host "==> markdown emoji normalization check"
			Write-Host "skipped; no changed text paths and no -Paths were provided"
		}
	}

	Invoke-CheckCommand -Label "git diff --check" -Command "git" -Arguments @("diff", "--check")

	if (-not $NoLineIndex) {
		Invoke-CheckCommand -Label "code line index check" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$lineIndexScript,
			"-ChangedOnly",
			"-Check"
		)
	}

	if ($Audit) {
		Invoke-CheckCommand -Label "audit docs" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$auditScript
		)
	}

	if (-not $NoStat) {
		Invoke-CheckCommand -Label "git diff --stat" -Command "git" -Arguments @("diff", "--stat")
	}

	if (-not $NoStatus) {
		Invoke-CheckCommand -Label "git status --short" -Command "git" -Arguments @("status", "--short")
	}

	Write-Host ""
	Write-Host "OK: task check completed"
} finally {
	Pop-Location
}
