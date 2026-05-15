param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Key = "",
	[int]$Line = 0,
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "read", $Path)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($Key -ne "") { $arguments += $Key }
if ($Line -gt 0) { $arguments += @("--line", [string]$Line) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_read failed with exit code $LASTEXITCODE"
}
