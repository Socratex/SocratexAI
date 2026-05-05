param(
	[Parameter(Mandatory = $true)]
	[string]$Message,
	[string[]]$QualityCommand = @(),
	[switch]$StrictAudit,
	[switch]$NoPush,
	[switch]$NoAudit,
	[switch]$AllowPreStaged
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$finishSubtaskScript = Join-Path $PSScriptRoot "finalize_changed_files_commit_push.ps1"

if ([string]::IsNullOrWhiteSpace($Message)) {
	throw "Commit message must not be empty."
}

if (-not (Test-Path -LiteralPath $finishSubtaskScript)) {
	throw "Subtask finalizer not found at: $finishSubtaskScript"
}

Push-Location -LiteralPath $repoRoot
try {
	Write-Host "==> finalize task: check, commit, and push"
	Write-Host "message: $Message"
	Write-Host "quality: full"
	Write-Host "push: $(-not $NoPush)"

	$finishArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$finishSubtaskScript,
		"-Message",
		$Message,
		"-Quality"
	)

	if ($QualityCommand -and $QualityCommand.Count -gt 0) {
		$finishArgs += "-QualityCommand"
		$finishArgs += $QualityCommand
	}
	if ($StrictAudit) {
		$finishArgs += "-StrictAudit"
	}
	if ($NoPush) {
		$finishArgs += "-NoPush"
	}
	if ($NoAudit) {
		$finishArgs += "-NoAudit"
	}
	if ($AllowPreStaged) {
		$finishArgs += "-AllowPreStaged"
	}

	& powershell @finishArgs
	if ($LASTEXITCODE -ne 0) {
		throw "finalize_task_check_commit_push failed because finalize_changed_files_commit_push failed with exit code $LASTEXITCODE"
	}

	Write-Host ""
	Write-Host "OK: task finalized; checks passed before commit/push."
} catch {
	Write-Host ""
	Write-Host "FAILED: task finalizer did not commit or push a completed task."
	Write-Host $_.Exception.Message
	Write-Host ""
	Write-Host "Next step: fix the reported failure. If the failure is mechanical and reusable, improve the owning script before rerunning the task finalizer."
	exit 1
} finally {
	Pop-Location
}
