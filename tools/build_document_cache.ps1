param(
	[string[]]$Paths = @("**\*.json"),
	[string]$OutputDir = "docs-tech\cache"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

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
