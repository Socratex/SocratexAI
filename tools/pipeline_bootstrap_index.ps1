param(
    [string]$Output = "docs-tech\PIPELINE-BOOTSTRAP.json",
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$script = Join-Path $PSScriptRoot "pipeline_bootstrap_index.py"
$arguments = @(
    $script,
    "--repo-root",
    $repoRoot,
    "--output",
    $Output
)
if ($Check) {
    $arguments += "--check"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "pipeline_bootstrap_index failed with exit code $LASTEXITCODE"
}
