param(
	[string]$Path = "",
	[string]$Key = "",
	[ValidateSet("start", "end", "before", "after")]
	[string]$Position = "end",
	[string]$Reference = "",
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_item_move.ps1 -Path <file> -Key <key> [-Collection content] -Position before -Reference <key>

For full node paths, preferred:
  json_node_edit.ps1 -Operation move -Path <file> -Node content.item -Position before -ReferenceNode content.other
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "move-entry", $Path, $Key, "--position", $Position)
if ($Reference -ne "") { $arguments += @("--reference", $Reference) }
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_item_move failed with exit code $LASTEXITCODE"
}
