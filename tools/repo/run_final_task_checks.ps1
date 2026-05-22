param(
	[switch]$Quality,
	[string[]]$QualityCommand,
	[switch]$StrictAudit,
	[switch]$NoAudit,
	[switch]$NoLineIndex,
	[switch]$NoNormalize,
	[switch]$NoDocCache,
	[switch]$NoOutput,
	[switch]$NoSound,
	[switch]$RequireTaskFlowEvidence,
	[string]$TaskFlowEvidencePath = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-WorkTreeRoot {
	param([string]$FallbackRoot)

	$gitRoot = @(git -C $FallbackRoot rev-parse --show-toplevel 2>$null)
	if ($LASTEXITCODE -eq 0 -and $gitRoot.Count -gt 0 -and -not [string]::IsNullOrWhiteSpace([string]$gitRoot[0])) {
		return (Resolve-Path -LiteralPath ([string]$gitRoot[0])).Path
	}
	return (Resolve-Path -LiteralPath $FallbackRoot).Path
}

$packageRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")).Path
$repoRoot = Resolve-WorkTreeRoot -FallbackRoot $packageRoot
$taskSnapshotScript = Join-Path $PSScriptRoot "task_snapshot.ps1"
$taskFlowAuditScript = Join-Path $PSScriptRoot "task_flow_audit.ps1"
$auditScript = Join-Path $packageRoot "tools\documents\audit_docs.ps1"
$lineIndexScript = Join-Path $packageRoot "tools\codebase\update_code_line_index.ps1"
$textNormalizeScript = Join-Path $packageRoot "tools\text\normalize_text_files.ps1"
$docCacheScript = Join-Path $packageRoot "tools\documents\build_document_cache.ps1"
$qualityScript = Join-Path $packageRoot "tools\quality\run_quality_gate.ps1"
$outputScript = Join-Path $PSScriptRoot "end_prompt_snapshot.ps1"
$pipelineFeatureListCheckScript = Join-Path $PSScriptRoot "check_pipeline_featurelist_update.ps1"
$compiledInstructionsRecompileScript = Join-Path $packageRoot "tools\pipeline\rebuild_ai_compiled_context.ps1"
$compiledInstructionsCheckScript = Join-Path $packageRoot "tools\pipeline\check_ai_compiled_context.ps1"

function Invoke-RepoCommand {
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

function Invoke-ChangedTextNormalization {
	param([string]$Label)

	$changedTextPaths = @(Get-ChangedTextPaths)
	if ($NoNormalize -or $changedTextPaths.Count -eq 0) {
		return
	}

	$normalizeArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$textNormalizeScript,
		"-Root",
		$repoRoot,
		"-Paths"
	)
	$normalizeArgs += $changedTextPaths
	Invoke-RepoCommand -Label $Label -Command "powershell" -Arguments $normalizeArgs
}

Push-Location -LiteralPath $repoRoot
try {
	Write-Host "==> finish task"

	if (Test-Path -LiteralPath ".git") {
		Invoke-ChangedTextNormalization -Label "text normalization refresh"
	}

	if (-not $NoDocCache) {
		Invoke-RepoCommand -Label "document cache refresh" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$docCacheScript
		)
	}

	if ((Test-Path -LiteralPath ".git") -and (-not $NoLineIndex)) {
		Invoke-RepoCommand -Label "code line index refresh" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$lineIndexScript,
			"-Root",
			$repoRoot,
			"-ChangedOnly"
		)
		Invoke-ChangedTextNormalization -Label "post-generator text normalization refresh"
	}

	if (Test-Path -LiteralPath $compiledInstructionsRecompileScript) {
		Invoke-RepoCommand -Label "compiled AI instructions refresh" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$compiledInstructionsRecompileScript
		)
	}

	& powershell -NoProfile -ExecutionPolicy Bypass -File $taskSnapshotScript -Root $repoRoot
	if ($LASTEXITCODE -ne 0) {
		throw "task snapshot failed with exit code $LASTEXITCODE"
	}

	if (Test-Path -LiteralPath ".git") {
		Invoke-RepoCommand -Label "git diff --check" -Command "git" -Arguments @("diff", "--check")
	}

	if (Test-Path -LiteralPath $taskFlowAuditScript) {
		$taskFlowAuditArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$taskFlowAuditScript,
			"-ProjectRoot",
			$repoRoot
		)
		if ($RequireTaskFlowEvidence) {
			$taskFlowAuditArgs += "-RequireClosureEvidence"
			if (-not [string]::IsNullOrWhiteSpace($TaskFlowEvidencePath)) {
				$taskFlowAuditArgs += "-ClosureEvidencePath"
				$taskFlowAuditArgs += $TaskFlowEvidencePath
			}
		}
		Invoke-RepoCommand -Label "task flow audit" -Command "powershell" -Arguments $taskFlowAuditArgs
	}

	if ((Test-Path -LiteralPath ".git") -and (Test-Path -LiteralPath $pipelineFeatureListCheckScript)) {
		Invoke-RepoCommand -Label "pipeline feature list guard" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$pipelineFeatureListCheckScript
		)
	}

	if (Test-Path -LiteralPath $compiledInstructionsCheckScript) {
		Invoke-RepoCommand -Label "compiled AI instructions check" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$compiledInstructionsCheckScript
		)
	}

	if ((Test-Path -LiteralPath ".git") -and (-not $NoLineIndex)) {
		Invoke-RepoCommand -Label "code line index check" -Command "powershell" -Arguments @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$lineIndexScript,
			"-Root",
			$repoRoot,
			"-ChangedOnly",
			"-Check"
		)
	}

	if (-not $NoAudit) {
		$auditArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$auditScript
		)
		if ($StrictAudit) {
			$auditArgs += "-Strict"
		}
		Invoke-RepoCommand -Label "audit docs" -Command "powershell" -Arguments $auditArgs
	}

	if ($Quality) {
		$qualityArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$qualityScript,
			"-Root",
			$repoRoot
		)
		if ($QualityCommand -and $QualityCommand.Count -gt 0) {
			$qualityArgs += "-Command"
			$qualityArgs += $QualityCommand
		}
		Invoke-RepoCommand -Label "quality gate" -Command "powershell" -Arguments $qualityArgs
	} else {
		Write-Host ""
		Write-Host "==> quality gate"
		Write-Host "skipped; pass -Quality to run tools/quality/run_quality_gate.ps1"
	}

	if (-not $NoOutput) {
		$outputArgs = @(
			"-NoProfile",
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$outputScript,
			"-Root",
			$repoRoot
		)
		if ($NoSound) {
			$outputArgs += "-NoSound"
		}
		Invoke-RepoCommand -Label "OUTPUT snapshot" -Command "powershell" -Arguments $outputArgs
	}

	Write-Host ""
	Write-Host "OK: finish task checks completed"
} finally {
	Pop-Location
}
