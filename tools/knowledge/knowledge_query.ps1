param(
	[string[]]$Tags = @(),
	[ValidateSet("all", "any")]
	[string]$Match = "all",
	[string]$Type = "",
	[switch]$LoadAtStart,
	[string]$SourcePath = "",
	[string]$DocumentPath = "",
	[string]$Name = "",
	[ValidateSet("markdown", "json")]
	[string]$Format = "markdown"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$tagValues = @()
foreach ($tag in $Tags) {
	if ([string]::IsNullOrWhiteSpace($tag)) {
		continue
	}
	$tagValues += @($tag.Split(",") | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
}

$arguments = @($tool, "select", "--repo-root", $repoRoot, "--match", $Match, "--format", $Format)
if ($tagValues.Count -gt 0) {
	$arguments += "--tags"
	$arguments += $tagValues
}
if ($Type -ne "") {
	$arguments += @("--type", $Type)
}
if ($LoadAtStart) {
	$arguments += "--load-at-start"
}
if ($SourcePath -ne "") {
	$arguments += @("--source-path", $SourcePath)
}
if ($DocumentPath -ne "") {
	$arguments += @("--document-path", $DocumentPath)
}
if ($Name -ne "") {
	$arguments += @("--name", $Name)
}

Push-Location -LiteralPath $repoRoot
try {
	& $python @arguments
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
} finally {
	Pop-Location
}
