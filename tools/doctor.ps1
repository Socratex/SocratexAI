param(
	[switch]$AuditDocs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$auditScript = Join-Path $PSScriptRoot "audit_docs.ps1"

function Get-OptionalCommandSource {
	param([string]$Name)

	$command = Get-Command $Name -ErrorAction SilentlyContinue
	if ($null -eq $command) {
		return ""
	}
	if ($command.PSObject.Properties.Name -contains "Source") {
		return [string]$command.Source
	}
	if ($command.PSObject.Properties.Name -contains "Path") {
		return [string]$command.Path
	}
	return ""
}

function Find-CommandPath {
	param([string[]]$CandidateNames)

	foreach ($name in $CandidateNames) {
		$source = Get-OptionalCommandSource -Name $name
		if (-not [string]::IsNullOrWhiteSpace($source)) {
			return $source
		}
	}

	return ""
}

function Write-CheckResult {
	param(
		[string]$Name,
		[bool]$Ok,
		[string]$Detail
	)

	if ($Ok) {
		Write-Host ("OK: " + $Name + " - " + $Detail)
	} else {
		Write-Host ("FAIL: " + $Name + " - " + $Detail)
		$script:failureCount += 1
	}
}

$failureCount = 0

Push-Location -LiteralPath $repoRoot
try {
	Write-Host "==> SocratexPipeline toolchain doctor"

	$gitPath = Find-CommandPath -CandidateNames @("git")
	Write-CheckResult -Name "git" -Ok (-not [string]::IsNullOrWhiteSpace($gitPath)) -Detail $gitPath

	$powershellPath = Find-CommandPath -CandidateNames @("pwsh", "powershell")
	Write-CheckResult -Name "PowerShell" -Ok (-not [string]::IsNullOrWhiteSpace($powershellPath)) -Detail $powershellPath

	$pythonPath = Find-CommandPath -CandidateNames @("python", "py")
	Write-CheckResult -Name "python" -Ok (-not [string]::IsNullOrWhiteSpace($pythonPath)) -Detail $pythonPath

	$doneScript = Join-Path $PSScriptRoot "done.ps1"
	Write-CheckResult -Name "done finalizer" -Ok (Test-Path -LiteralPath $doneScript) -Detail $doneScript

	$workflowPath = Join-Path $repoRoot "project\code\WORKFLOW.yaml"
	Write-CheckResult -Name "code workflow" -Ok (Test-Path -LiteralPath $workflowPath) -Detail $workflowPath

	$agentContractPath = Join-Path $repoRoot "core\AGENT-CONTRACT.yaml"
	Write-CheckResult -Name "agent contract" -Ok (Test-Path -LiteralPath $agentContractPath) -Detail $agentContractPath

	$docToolPath = Join-Path $PSScriptRoot "doc_tool.py"
	Write-CheckResult -Name "doc tool" -Ok (Test-Path -LiteralPath $docToolPath) -Detail $docToolPath

	$checkUtf8Script = Join-Path $PSScriptRoot "check_utf8_writes.ps1"
	Write-CheckResult -Name "UTF-8 write guard" -Ok (Test-Path -LiteralPath $checkUtf8Script) -Detail $checkUtf8Script

	git status --short | Out-Null
	Write-CheckResult -Name "git status" -Ok ($LASTEXITCODE -eq 0) -Detail "repository is readable"

	if ($AuditDocs) {
		if (-not (Test-Path -LiteralPath $auditScript)) {
			Write-CheckResult -Name "document audit" -Ok $false -Detail "missing $auditScript"
		} else {
			Write-Host ""
			Write-Host "==> document audit"
			& powershell -NoProfile -ExecutionPolicy Bypass -File $auditScript
			Write-CheckResult -Name "document audit" -Ok ($LASTEXITCODE -eq 0) -Detail "audit completed"
		}
	}

	Write-Host ""
	if ($failureCount -eq 0) {
		Write-Host "OK: doctor found no missing critical tools."
	} else {
		Write-Host "FAIL: doctor found $failureCount missing or broken tool(s)."
		exit 1
	}
} finally {
	Pop-Location
}
