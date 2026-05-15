param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Collection = "content"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "refresh-index", $Path)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_refresh_index failed with exit code $LASTEXITCODE"
}
