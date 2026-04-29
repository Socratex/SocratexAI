param(
	[Parameter(Mandatory = $true)]
	[string]$Message,
	[string[]]$Paths = @(),
	[switch]$Quality,
	[string[]]$QualityCommand,
	[switch]$StrictAudit,
	[switch]$NoAudit,
	[switch]$NoVerify,
	[switch]$NoPush,
	[switch]$AllowPreStaged
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$finishSubtaskScript = Join-Path $PSScriptRoot "finish_subtask.ps1"

if ([string]::IsNullOrWhiteSpace($Message)) {
	throw "Commit message must not be empty."
}

Push-Location -LiteralPath $repoRoot
try {
	if ($Paths.Count -gt 0) {
		Write-Host "commit_task.ps1 delegates to finish_subtask.ps1; explicit -Paths are accepted for compatibility but staging is git-derived."
	} else {
		Write-Host "commit_task.ps1 delegates to finish_subtask.ps1; prefer finish_subtask.ps1 for new automation."
	}

	$finishSubtaskArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$finishSubtaskScript,
		"-Message",
		$Message
	)
	if ($Quality) {
		$finishSubtaskArgs += "-Quality"
	}
	if ($QualityCommand -and $QualityCommand.Count -gt 0) {
		$finishSubtaskArgs += "-QualityCommand"
		$finishSubtaskArgs += $QualityCommand
	}
	if ($StrictAudit) {
		$finishSubtaskArgs += "-StrictAudit"
	}
	if ($NoAudit -or $NoVerify) {
		$finishSubtaskArgs += "-NoAudit"
	}
	if ($NoPush) {
		$finishSubtaskArgs += "-NoPush"
	}
	if ($AllowPreStaged) {
		$finishSubtaskArgs += "-AllowPreStaged"
	}

	& powershell @finishSubtaskArgs
	if ($LASTEXITCODE -ne 0) {
		throw "finish_subtask failed with exit code $LASTEXITCODE"
	}
} finally {
	Pop-Location
}
