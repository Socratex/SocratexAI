param(
	[string]$RepoRoot = "",
	[switch]$IncludeTemplates,
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$reportScript = Join-Path $PSScriptRoot "knowledge_tier_report.ps1"
$arguments = @{
	Strict = $true
	ShowEntries = $true
	Format = $Format
}
if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
	$arguments["RepoRoot"] = $RepoRoot
}
if ($IncludeTemplates) {
	$arguments["IncludeTemplates"] = $true
}

& $reportScript @arguments
if ($LASTEXITCODE -ne 0) {
	exit $LASTEXITCODE
}
