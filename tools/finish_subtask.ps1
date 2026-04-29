param(
	[Parameter(Mandatory = $true)]
	[string]$Message,
	[switch]$Quality,
	[string[]]$QualityCommand,
	[switch]$StrictAudit,
	[switch]$NoAudit,
	[switch]$NoPush,
	[switch]$AllowPreStaged
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$finishScript = Join-Path $PSScriptRoot "finish_task.ps1"

function Invoke-GitLines {
	param([string[]]$Arguments)

	$previousErrorActionPreference = $ErrorActionPreference
	$ErrorActionPreference = "Continue"
	$output = @(git @Arguments 2>&1)
	$exitCode = $LASTEXITCODE
	$ErrorActionPreference = $previousErrorActionPreference

	if ($exitCode -ne 0) {
		throw "git $($Arguments -join ' ') failed: $($output -join "`n")"
	}
	return @($output | Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) })
}

function Test-GeneratedArtifactPath {
	param([string]$Path)

	$normalized = $Path.Replace("\", "/")
	return (
		$normalized -eq "OUTPUT" -or
		$normalized -eq "CONSOLE-LOG" -or
		$normalized -eq "CONSOLE-LOG-SUMMARY" -or
		$normalized -eq "PROMPT-SNAPSHOT" -or
		$normalized.StartsWith("logs/") -or
		$normalized.StartsWith("logs-diagnostics/") -or
		$normalized.StartsWith("logs-performance/") -or
		$normalized.StartsWith("temp/") -or
		$normalized.StartsWith("tmp/") -or
		$normalized.StartsWith("prompt-export/")
	)
}

function Get-GitChangedPaths {
	$paths = @()
	$paths += @(Invoke-GitLines -Arguments @("diff", "--name-only", "--diff-filter=ACMR"))
	$paths += @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only", "--diff-filter=ACMR"))
	$paths += @(Invoke-GitLines -Arguments @("ls-files", "--others", "--exclude-standard"))
	return @($paths | Sort-Object -Unique)
}

function Get-CommitCandidatePaths {
	return @(Get-GitChangedPaths | Where-Object {
		-not (Test-GeneratedArtifactPath -Path $_)
	})
}

if ([string]::IsNullOrWhiteSpace($Message)) {
	throw "Commit message must not be empty."
}

Push-Location -LiteralPath $repoRoot
try {
	if (-not (Test-Path -LiteralPath ".git")) {
		throw "This project is not a Git repository."
	}

	$preStaged = @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only"))
	if ($preStaged.Count -gt 0 -and -not $AllowPreStaged) {
		throw "Refusing to continue because staged changes already exist. Use -AllowPreStaged if intentional."
	}

	$initialCandidates = @(Get-CommitCandidatePaths)
	if ($initialCandidates.Count -eq 0) {
		throw "No changed non-local-artifact paths to close."
	}

	$finishArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$finishScript,
		"-NoSound"
	)
	if ($Quality) {
		$finishArgs += "-Quality"
	}
	if ($QualityCommand -and $QualityCommand.Count -gt 0) {
		$finishArgs += "-QualityCommand"
		$finishArgs += $QualityCommand
	}
	if ($StrictAudit) {
		$finishArgs += "-StrictAudit"
	}
	if ($NoAudit) {
		$finishArgs += "-NoAudit"
	}
	& powershell @finishArgs
	if ($LASTEXITCODE -ne 0) {
		throw "finish task failed with exit code $LASTEXITCODE"
	}

	$paths = @(Get-CommitCandidatePaths)
	if ($paths.Count -eq 0) {
		throw "No changed non-local-artifact paths after finish_task."
	}

	Write-Host ""
	Write-Host "==> staging git-derived paths"
	git add -- $paths
	if ($LASTEXITCODE -ne 0) {
		throw "git add failed with exit code $LASTEXITCODE"
	}

	$staged = @(Invoke-GitLines -Arguments @("diff", "--cached", "--name-only"))
	if ($staged.Count -eq 0) {
		throw "No staged changes after git add."
	}

	Write-Host ""
	Write-Host "==> staged files"
	foreach ($path in $staged) {
		Write-Host $path
	}

	git diff --cached --check
	if ($LASTEXITCODE -ne 0) {
		throw "git diff --cached --check failed with exit code $LASTEXITCODE"
	}

	git commit -m $Message
	if ($LASTEXITCODE -ne 0) {
		throw "git commit failed with exit code $LASTEXITCODE"
	}

	if (-not $NoPush) {
		Write-Host ""
		Write-Host "==> git push"
		$pushOutput = @(Invoke-GitLines -Arguments @("push", "origin", "HEAD"))
		foreach ($line in $pushOutput) {
			Write-Host $line
		}
	}

	Write-Host ""
	Write-Host "==> final repository state"
	$remaining = @(Invoke-GitLines -Arguments @("status", "--short"))
	if ($remaining.Count -eq 0) {
		Write-Host "OK: working tree clean; subtask closed."
	} else {
		Write-Host "WARN: working tree still has changes; subtask not fully closed."
		foreach ($line in $remaining) {
			Write-Host $line
		}
	}
} finally {
	Pop-Location
}
