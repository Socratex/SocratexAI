$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$gamePath = Join-Path $repoRoot "Game"
$scriptsPath = Join-Path $gamePath "scripts"
$localPythonScriptsPath = Join-Path $repoRoot "Tools\Python312\Scripts"
$qualityGatePath = Join-Path $PSScriptRoot "run_quality_gate.ps1"

function Find-CommandPath {
	param(
		[string[]]$CandidateNames,
		[string[]]$CandidatePaths = @()
	)

	foreach ($candidatePath in $CandidatePaths) {
		if (Test-Path -LiteralPath $candidatePath) {
			return $candidatePath
		}
	}

	foreach ($name in $CandidateNames) {
		$command = Get-Command $name -ErrorAction SilentlyContinue
		if ($null -ne $command) {
			return $command.Source
		}
	}

	return $null
}

function Invoke-Step {
	param(
		[string]$Name,
		[scriptblock]$Action
	)

	Write-Host ("==> " + $Name)
	& $Action
	Write-Host ("OK: " + $Name)
}

$gdformatPath = Find-CommandPath @("gdformat") @(
	(Join-Path $localPythonScriptsPath "gdformat.exe")
)

if ($null -eq $gdformatPath) {
	throw "gdtoolkit formatter is not available in PATH. Install it in a local venv and expose gdformat before running this fixer."
}

if (-not (Test-Path -LiteralPath $qualityGatePath)) {
	throw ("Quality gate script not found at: " + $qualityGatePath)
}

Invoke-Step "gdformat" {
	& $gdformatPath $scriptsPath
}

Invoke-Step "quality gate" {
	& $qualityGatePath
}
