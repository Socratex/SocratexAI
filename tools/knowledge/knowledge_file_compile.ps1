Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

Push-Location -LiteralPath $repoRoot
try {
	& $python $tool file-compile --repo-root $repoRoot
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
} finally {
	Pop-Location
}
