param(
	[string]$OutputDir = "AI-compiled",
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$recompileScript = Join-Path $PSScriptRoot "recompile_ai_instructions.ps1"
$checkScript = Join-Path $PSScriptRoot "check_compiled_instructions.ps1"
$bootstrapScript = Join-Path $PSScriptRoot "pipeline_bootstrap_index.ps1"

if ($Check) {
	if (Test-Path -LiteralPath $bootstrapScript) {
		& powershell -NoProfile -ExecutionPolicy Bypass -File $bootstrapScript -Check
		if ($LASTEXITCODE -ne 0) {
			exit $LASTEXITCODE
		}
	}
	& powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript -OutputDir $OutputDir
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
	exit 0
}

if (Test-Path -LiteralPath $bootstrapScript) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File $bootstrapScript
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $recompileScript -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript -OutputDir $OutputDir
if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}
