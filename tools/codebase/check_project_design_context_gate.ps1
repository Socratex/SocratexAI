param(
	[string]$ProjectRoot = ".",
	[string[]]$Paths = @(),
	[int]$MaxAgeMinutes = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$resolvedRoot = (Resolve-Path -LiteralPath $ProjectRoot).Path
$gatePath = Join-Path $resolvedRoot "ignored/project_design_context_gate.json"
$configPath = Join-Path $resolvedRoot ".aiassistant/socratex/PIPELINE-CONFIG.json"
$codePathPattern = '\.(gd|cs|csproj|props|targets|sln|ps1|psm1|psd1|py|js|jsx|ts|tsx|mjs|cjs|sh|bash|zsh|lua|rs|go|java|kt|kts|c|cc|cpp|h|hpp|php|rb|swift)$'

function Invoke-GitLines {
	param([string[]]$Arguments)

	$output = @(git -C $resolvedRoot @Arguments 2>&1)
	if ($LASTEXITCODE -ne 0) {
		throw "git $($Arguments -join ' ') failed in ${resolvedRoot}: $($output -join "`n")"
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

# Skip if project does not declare any required reads (acceptable no-op)
if (-not (Test-Path -LiteralPath $configPath -PathType Leaf)) {
	Write-Host "OK: no PIPELINE-CONFIG.json at project root; skipping per-project design gate."
	exit 0
}

$config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
$declaredReads = @()
if ($config.PSObject.Properties.Name -contains "code_design_required_reads") {
	$declaredReads = @($config.code_design_required_reads)
}
if ($declaredReads.Count -eq 0) {
	Write-Host "OK: project declares no code_design_required_reads; per-project design gate is a no-op."
	exit 0
}

$codePaths = @(Get-ChangedPaths | Where-Object { Test-CodePath -Path $_ })
if ($codePaths.Count -eq 0) {
	Write-Host "OK: no changed code paths require per-project design context."
	exit 0
}

if (-not (Test-Path -LiteralPath $gatePath -PathType Leaf)) {
	throw "Changed code paths require a fresh per-project design context load. Run tools/knowledge/project_design_context.ps1 -ProjectRoot ${resolvedRoot} before code work."
}

$gate = Get-Content -LiteralPath $gatePath -Raw | ConvertFrom-Json
if (-not $gate.full_set_loaded) {
	throw "Project design context gate marker reports incomplete load (missing files in declared_reads). Re-run tools/knowledge/project_design_context.ps1 -ProjectRoot ${resolvedRoot} after fixing missing files."
}

if ($MaxAgeMinutes -gt 0) {
	$loadedAt = [datetime]::Parse($gate.loaded_at).ToUniversalTime()
	$ageMinutes = ((Get-Date).ToUniversalTime() - $loadedAt).TotalMinutes
	if ($ageMinutes -gt $MaxAgeMinutes) {
		throw "Project design context gate marker is stale ($([math]::Round($ageMinutes, 1)) minutes old). Run tools/knowledge/project_design_context.ps1 -ProjectRoot ${resolvedRoot} again."
	}
}

$currentHead = $null
try { $currentHead = (git -C $resolvedRoot rev-parse HEAD 2>$null) } catch { }
if ($null -ne $currentHead -and $null -ne $gate.repo_head -and [string]$gate.repo_head -ne $currentHead) {
	throw "Project design context gate marker was loaded for a different HEAD. Run tools/knowledge/project_design_context.ps1 -ProjectRoot ${resolvedRoot} again."
}

# Verify declared reads in the gate match the current config
$gateDeclared = @()
if ($gate.PSObject.Properties.Name -contains "declared_reads") {
	$gateDeclared = @($gate.declared_reads | ForEach-Object { [string]$_ })
}
$missingFromGate = @($declaredReads | Where-Object { $_ -notin $gateDeclared })
if ($missingFromGate.Count -gt 0) {
	throw "Project design context gate marker is missing declared reads from current config: $($missingFromGate -join ', '). Run tools/knowledge/project_design_context.ps1 -ProjectRoot ${resolvedRoot} again."
}

Write-Host "OK: per-project design context loaded for changed code paths ($($declaredReads.Count) file(s) from PIPELINE-CONFIG.code_design_required_reads)."
