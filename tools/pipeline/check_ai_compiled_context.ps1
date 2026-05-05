param(
	[string]$OutputDir = "AI-compiled"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script = Join-Path $PSScriptRoot "rebuild_ai_compiled_context.ps1"
if (-not (Test-Path -LiteralPath $script -PathType Leaf)) {
	throw "Missing recompile script: $script"
}

& powershell -NoProfile -ExecutionPolicy Bypass -File $script -OutputDir $OutputDir -Check
if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}
