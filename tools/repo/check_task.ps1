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

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$textNormalizeScript = Join-Path $repoRoot "tools\text\normalize_text_files.ps1"
$jsonNormalizeScript = Join-Path $repoRoot "tools\text\normalize_json_files.ps1"
$bootstrapScript = Join-Path $repoRoot "tools\pipeline\pipeline_bootstrap_index.ps1"
$markdownEmojiScript = Join-Path $repoRoot "tools\documents\normalize_markdown_emoji.ps1"
$auditScript = Join-Path $repoRoot "tools\documents\audit_docs.ps1"
$lineIndexScript = Join-Path $repoRoot "tools\codebase\update_code_line_index.ps1"
$utf8WriteCheckScript = Join-Path $repoRoot "tools\text\check_utf8_writes.ps1"
$pipelineFeatureListCheckScript = Join-Path $PSScriptRoot "check_pipeline_featurelist_update.ps1"
$codeContextGateScript = Join-Path $repoRoot "tools\codebase\check_code_context_gate.ps1"

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
	$changed += @(git ls-files --others --exclude-standard)
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

function Invoke-TextNormalization {
	param(
		[string]$Label,
		[switch]$Check
	)

	if ($NoNormalize) {
		return
	}
	if ($checkPaths.Count -eq 0) {
		Write-Host ""
		Write-Host "==> $Label"
		Write-Host "skipped; no changed text paths and no -Paths were provided"
		return
	}

	$normalizationArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$textNormalizeScript
	)
	if ($Check) {
		$normalizationArgs += "-Check"
	}
	$normalizationArgs += "-Paths"
	$normalizationArgs += $checkPaths
	Invoke-CheckCommand -Label $Label -Command "powershell" -Arguments $normalizationArgs
}

Push-Location -LiteralPath $repoRoot
try {
	$checkPaths = @(Get-CheckPaths)

	if (Test-Path -LiteralPath $codeContextGateScript -PathType Leaf) {
		$codeContextArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$codeContextGateScript
		)
		if ($checkPaths.Count -gt 0) {
			$codeContextArgs += "-Paths"
			$codeContextArgs += ($checkPaths -join ",")
		}
		Invoke-CheckCommand -Label "compiled code-guidance context gate" -Command "powershell" -Arguments $codeContextArgs
	}

	Invoke-TextNormalization -Label "text normalization refresh"
	if ((-not $NoNormalize) -and (Test-Path -LiteralPath $jsonNormalizeScript)) {
		$jsonArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$jsonNormalizeScript
		)
		Invoke-CheckCommand -Label "JSON normalization refresh" -Command "powershell" -Arguments $jsonArgs
	}
	if (Test-Path -LiteralPath $bootstrapScript) {
		Invoke-CheckCommand -Label "pipeline bootstrap index refresh" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$bootstrapScript
		)
	}
	Invoke-TextNormalization -Label "text normalization check" -Check
	if ((-not $NoNormalize) -and (Test-Path -LiteralPath $jsonNormalizeScript)) {
		$jsonCheckArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$jsonNormalizeScript,
			"-Check"
		)
		Invoke-CheckCommand -Label "JSON normalization check" -Command "powershell" -Arguments $jsonCheckArgs
	}
	if (Test-Path -LiteralPath $bootstrapScript) {
		Invoke-CheckCommand -Label "pipeline bootstrap index check" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$bootstrapScript,
			"-Check"
		)
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

	$diffCheckArgs = @("-c", "core.safecrlf=false", "diff", "--check")
	if ($checkPaths.Count -gt 0) {
		$diffCheckArgs += "--"
		$diffCheckArgs += $checkPaths
	}
	Invoke-CheckCommand -Label "git diff --check" -Command "git" -Arguments $diffCheckArgs

	if ($checkPaths.Count -gt 0 -and (Test-Path -LiteralPath $utf8WriteCheckScript)) {
		$utf8WriteArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$utf8WriteCheckScript,
			"-Paths"
		)
		$utf8WriteArgs += $checkPaths
		Invoke-CheckCommand -Label "PowerShell UTF-8 write check" -Command "powershell" -Arguments $utf8WriteArgs
	}

	if ($checkPaths.Count -gt 0 -and (Test-Path -LiteralPath $pipelineFeatureListCheckScript)) {
		$pipelineFeatureListArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$pipelineFeatureListCheckScript
		)
		Invoke-CheckCommand -Label "pipeline feature list guard" -Command "powershell" -Arguments $pipelineFeatureListArgs
	}

	if (-not $NoLineIndex) {
		Invoke-CheckCommand -Label "code line index refresh" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$lineIndexScript,
			"-ChangedOnly"
		)
		Invoke-TextNormalization -Label "post-generator text normalization refresh"
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
