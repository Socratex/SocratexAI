param(
	[string[]]$Views = @(),
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown",
	[switch]$SkipCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$knowledgeCheck = Join-Path $PSScriptRoot "knowledge_check.ps1"
$knowledgeSelect = Join-Path $PSScriptRoot "knowledge_select.ps1"
$knowledgeFileSelect = Join-Path $PSScriptRoot "knowledge_file_select.ps1"

function Invoke-KnowledgeSelect {
	param(
		[string[]]$Arguments,
		[switch]$AllowFileFallback
	)

	& powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeSelect @Arguments
	if ($LASTEXITCODE -eq 0) {
		return
	}

	$dbExitCode = $LASTEXITCODE
	if ($AllowFileFallback -and (Test-Path -LiteralPath $knowledgeFileSelect -PathType Leaf)) {
		Write-Warning "SQLite knowledge select failed with exit code $dbExitCode. Falling back to compiled JSON table knowledge."
		$fileArgs = @()
		for ($index = 0; $index -lt $Arguments.Count; $index += 1) {
			if ($Arguments[$index] -eq "-View") {
				$index += 1
				continue
			}
			$fileArgs += $Arguments[$index]
		}
		& powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeFileSelect @fileArgs
		if ($LASTEXITCODE -eq 0) {
			return
		}
	}

	exit $dbExitCode
}

if (-not $SkipCheck) {
	$checkOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCheck 2>&1
	if ($LASTEXITCODE -ne 0) {
		$checkOutput | Write-Output
		exit $LASTEXITCODE
	}
}

Invoke-KnowledgeSelect -Arguments @(
	"-Tags", "engineering,coding,architecture",
	"-Match", "any",
	"-Type", "rule",
	"-Format", $Format
) -AllowFileFallback

foreach ($view in $Views) {
	if ([string]::IsNullOrWhiteSpace($view)) {
		continue
	}
	Invoke-KnowledgeSelect -Arguments @(
		"-View", $view.Trim(),
		"-Format", $Format
	)
}
