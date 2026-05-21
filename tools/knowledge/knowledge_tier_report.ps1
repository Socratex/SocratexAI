param(
	[string]$RepoRoot = "",
	[switch]$IncludeTemplates,
	[switch]$Strict,
	[switch]$ShowEntries,
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$defaultRepoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$repoRootValue = if ([string]::IsNullOrWhiteSpace($RepoRoot)) { $defaultRepoRoot } else { Resolve-Path -LiteralPath $RepoRoot }
$tool = Join-Path $PSScriptRoot "knowledge_tier_report.py"
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$arguments = @($tool, "--repo-root", $repoRootValue, "--format", $Format)
if ($IncludeTemplates) {
	$arguments += "--include-templates"
}
if ($Strict) {
	$arguments += "--strict"
}
if ($ShowEntries) {
	$arguments += "--show-entries"
}

Push-Location -LiteralPath $repoRootValue
try {
	& $python @arguments
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
} finally {
	Pop-Location
}
