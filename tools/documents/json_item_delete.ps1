param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "delete-entry", $Path, $Key)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_item_delete failed with exit code $LASTEXITCODE"
}
