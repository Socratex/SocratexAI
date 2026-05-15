param(
	[string[]]$Paths = @("**\*.json"),
	[string]$OutputDir = "docs-tech\cache"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "document_read_cache_engine.py"
$arguments = @(
	$script,
	"build-cache"
)
$arguments += $Paths
$arguments += @(
	"--output-dir",
	(Join-Path $repoRoot $OutputDir),
	"--repo-root",
	$repoRoot
)

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "build_document_cache failed with exit code $LASTEXITCODE"
}
