param(
	[string]$Path = "",
	[string]$Key = "",
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_item_delete.ps1 -Path <file> -Key <key> [-Collection content]

For full node paths, preferred:
  json_node_edit.ps1 -Operation delete -Path <file> -Node content.item
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "delete-entry", $Path, $Key)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_item_delete failed with exit code $LASTEXITCODE"
}
