param(
    [string]$Output = "",
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

function Convert-ToNativeRelativePath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        return (Join-Path "docs-tech" "PIPELINE-BOOTSTRAP.json")
    }
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }

    $parts = @($Path -split '[\\/]' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($parts.Count -eq 0) {
        return $Path
    }
    return [System.IO.Path]::Combine($parts)
}

$Output = Convert-ToNativeRelativePath -Path $Output

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
