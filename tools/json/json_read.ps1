param(
	[string]$Path = "",
	[string]$Key = "",
	[string]$FieldPath = "",
	[int]$Line = 0,
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_read.ps1 -Path <file> [-Collection content] [-Key <key>] [-FieldPath steps] [-Line <n>]

For full node paths, use:
  json_node_edit.ps1 -Operation read -Path <file> -Node content.item.steps
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "read", $Path)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($Key -ne "") { $arguments += $Key }
if ($FieldPath -ne "") { $arguments += @("--field-path", $FieldPath) }
if ($Line -gt 0) { $arguments += @("--line", [string]$Line) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_read failed with exit code $LASTEXITCODE"
}
