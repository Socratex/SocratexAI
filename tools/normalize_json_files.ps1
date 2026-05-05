param(
    [string[]]$Paths = @("**/*.json"),
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    $python = "python"
}

$script = Join-Path $PSScriptRoot "normalize_json_files.py"
$arguments = @(
    $script,
    "--repo-root",
    $repoRoot
)
if ($Check) {
    $arguments += "--check"
}
$arguments += $Paths

& $python @arguments
if ($LASTEXITCODE -ne 0) {
    throw "normalize_json_files failed with exit code $LASTEXITCODE"
}
