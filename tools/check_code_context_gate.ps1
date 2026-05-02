param(
	[string[]]$Paths = @(),
	[int]$MaxAgeMinutes = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$gatePath = Join-Path $repoRoot "ignored/code_context_gate.json"
$requiredTags = @(
	"engineering",
	"coding",
	"architecture",
	"best-practices",
	"borrowed-before-bespoke",
	"aaa-gamedev",
	"ddd-adiv",
	"future-first",
	"data-first",
	"godot",
	"runtime",
	"diagnostics",
	"performance",
	"verification"
)
$codePathPattern = '\.(gd|cs|csproj|props|targets|sln|ps1|psm1|psd1|py|js|jsx|ts|tsx|mjs|cjs|sh|bash|zsh|lua|rs|go|java|kt|kts|c|cc|cpp|h|hpp|php|rb|swift)$'

function Invoke-GitLines {
	param([string[]]$Arguments)

	$output = @(git -C $repoRoot @Arguments 2>&1)
	if ($LASTEXITCODE -ne 0) {
		throw "git $($Arguments -join ' ') failed: $($output -join "`n")"
	}
	return @($output | Where-Object {
		$line = [string]$_
		-not [string]::IsNullOrWhiteSpace($line) -and
			$line -notmatch "^warning: "
	})
}

function Get-ChangedPaths {
	if ($Paths.Count -gt 0) {
		$expanded = New-Object System.Collections.Generic.List[string]
		foreach ($path in $Paths) {
			foreach ($candidate in ($path -split ",")) {
				$trimmed = $candidate.Trim()
				if ($trimmed.Length -gt 0) {
					$expanded.Add($trimmed)
				}
			}
		}
		return @($expanded | Sort-Object -Unique)
	}

	$changed = @()
	$changed += @(Invoke-GitLines -Arguments @("diff", "--name-only", "--diff-filter=ACMR"))
	$changed += @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMR"))
	$changed += @(Invoke-GitLines -Arguments @("ls-files", "--others", "--exclude-standard"))
	return @($changed | Sort-Object -Unique)
}

function Test-CodePath {
	param([string]$Path)

	$normalized = $Path.Replace("\", "/")
	if ($normalized -eq "OUTPUT" -or
		$normalized.StartsWith("ignored/") -or
		$normalized.StartsWith("logs/") -or
		$normalized.StartsWith("logs-diagnostics/") -or
		$normalized.StartsWith("logs-performance/") -or
		$normalized.StartsWith("tools/tmp/") -or
		$normalized.StartsWith("AI-compiled/") -or
		$normalized.StartsWith("SocratexAI/AI-compiled/") -or
		$normalized.StartsWith("docs-tech/cache/")) {
		return $false
	}
	return $normalized -match $codePathPattern
}

$codePaths = @(Get-ChangedPaths | Where-Object { Test-CodePath -Path $_ })
if ($codePaths.Count -eq 0) {
	Write-Host "OK: no changed code paths require compiled code-guidance context."
	exit 0
}

if (-not (Test-Path -LiteralPath $gatePath -PathType Leaf)) {
	throw "Changed code paths require a fresh full compiled code-guidance load. Run tools/knowledge_code_context.ps1 before code work."
}

$gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
if (-not $gate.full_base_loaded) {
	throw "Code context gate marker does not confirm a full base code-guidance load. Run tools/knowledge_code_context.ps1."
}

if ($MaxAgeMinutes -gt 0) {
	$loadedAt = [datetime]::Parse($gate.loaded_at).ToUniversalTime()
	$ageMinutes = ((Get-Date).ToUniversalTime() - $loadedAt).TotalMinutes
	if ($ageMinutes -gt $MaxAgeMinutes) {
		throw "Code context gate marker is stale ($([math]::Round($ageMinutes, 1)) minutes old). Run tools/knowledge_code_context.ps1 again."
	}
}

$currentHead = (git -C $repoRoot rev-parse HEAD).Trim()
if ([string]$gate.repo_head -ne $currentHead) {
	throw "Code context gate marker was loaded for a different HEAD. Run tools/knowledge_code_context.ps1 again."
}

$selectedTags = @($gate.selected_tags | ForEach-Object { [string]$_ })
$missingTags = @($requiredTags | Where-Object { $_ -notin $selectedTags })
if ($missingTags.Count -gt 0) {
	throw "Code context gate marker is missing required tags: $($missingTags -join ', '). Run tools/knowledge_code_context.ps1."
}

Write-Host "OK: full compiled code-guidance context loaded for changed code paths."
