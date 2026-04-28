param(
	[string[]]$Paths = @("**\*.yaml", "**\*.yml"),
	[string]$OutputDir = "docs-tech\cache"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "doc_tool.py"
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
	throw "doc_build_cache failed with exit code $LASTEXITCODE"
}
