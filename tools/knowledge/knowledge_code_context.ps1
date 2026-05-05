param(
	[string[]]$Views = @(),
	[string[]]$AdditionalTags = @(),
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown",
	[switch]$SkipCheck
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$knowledgeCheck = Join-Path $PSScriptRoot "knowledge_check.ps1"
$knowledgeSelect = Join-Path $PSScriptRoot "knowledge_select.ps1"
$knowledgeFileSelect = Join-Path $PSScriptRoot "knowledge_file_select.ps1"
$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$codeContextGatePath = Join-Path $repoRoot "ignored/code_context_gate.json"

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

$baseCodeGuidanceTags = @(
	"engineering",
	"coding",
	"architecture",
	"best-practices",
	"borrowed-before-bespoke",
	"production-grade",
	"ddd-adiv",
	"future-first",
	"data-first",
	"ownership",
	"runtime",
	"diagnostics",
	"performance",
	"verification",
	"domain_modeling"
)
$selectedTags = @($baseCodeGuidanceTags + $AdditionalTags | Where-Object {
	-not [string]::IsNullOrWhiteSpace($_)
} | ForEach-Object {
	$_.Trim()
} | Sort-Object -Unique)

if (-not $SkipCheck) {
	$checkOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $knowledgeCheck 2>&1
	if ($LASTEXITCODE -ne 0) {
		$checkOutput | Write-Output
		exit $LASTEXITCODE
	}
}

Invoke-KnowledgeSelect -Arguments @(
	"-Tags", ($selectedTags -join ","),
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

$codeContextGate = [ordered]@{
	schema = 1
	tool = "knowledge_code_context"
	loaded_at = (Get-Date).ToUniversalTime().ToString("o")
	repo_head = (git -C $repoRoot rev-parse HEAD)
	base_tags = $baseCodeGuidanceTags
	additional_tags = $AdditionalTags
	selected_tags = $selectedTags
	views = @($Views | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_.Trim() })
	format = $Format
	full_base_loaded = $true
}
$codeContextGateDirectory = Split-Path -Parent $codeContextGatePath
if (-not (Test-Path -LiteralPath $codeContextGateDirectory -PathType Container)) {
	New-Item -ItemType Directory -Path $codeContextGateDirectory | Out-Null
}
$json = $codeContextGate | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($codeContextGatePath, $json, $utf8NoBom)
