param(
	[string[]]$Paths = @("AGENTS.md", "DOCS.json"),
	[string]$Root = "",
	[switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$packageRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$repoRoot = if ([string]::IsNullOrWhiteSpace($Root)) {
	$packageRoot
} else {
	Resolve-Path -LiteralPath $Root
}

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "normalize_text_files.py"
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
	throw "normalize_text_files failed with exit code $LASTEXITCODE"
}
