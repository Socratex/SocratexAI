param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[ValidateSet("start", "end", "before", "after")]
	[string]$Position = "end",
	[string]$Reference = "",
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

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
