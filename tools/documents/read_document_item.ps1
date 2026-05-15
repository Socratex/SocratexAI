param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Selector,
	[switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "document_read_cache_engine.py"
$arguments = @($script, "read", $Path, $Selector)
if ($Json) {
	$arguments += "--json"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "read_document_item failed with exit code $LASTEXITCODE"
}
