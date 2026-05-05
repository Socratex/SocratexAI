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

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$finishSubtaskScript = Join-Path $PSScriptRoot "finalize_changed_files_commit_push.ps1"

if ([string]::IsNullOrWhiteSpace($Message)) {
	throw "Commit message must not be empty."
}

Push-Location -LiteralPath $repoRoot
try {
	if ($Paths.Count -gt 0) {
		Write-Host "legacy_commit_task_compatibility_wrapper.ps1 delegates to finalize_changed_files_commit_push.ps1; explicit -Paths are accepted for compatibility but staging is git-derived."
	} else {
		Write-Host "legacy_commit_task_compatibility_wrapper.ps1 delegates to finalize_changed_files_commit_push.ps1; prefer finalize_changed_files_commit_push.ps1 for new automation."
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
		throw "finalize_changed_files_commit_push failed with exit code $LASTEXITCODE"
	}
} finally {
	Pop-Location
}
