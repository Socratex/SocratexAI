param(
	[string[]]$Paths = @(),
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "repair_mojibake.py"
$arguments = @(
	$script,
	"--repo-root",
	$repoRoot
)
if ($Check) {
	$arguments += "--check"
}
$arguments += $Paths

& $python -B @arguments
if ($LASTEXITCODE -ne 0) {
	throw "repair_mojibake failed with exit code $LASTEXITCODE"
}
