param(
	[string]$Path = "",
	[string]$Key = "",
	[int]$Line = 0,
	[string]$FieldPath = "",
	[ValidateSet("start", "end", "before", "after")]
	[string]$Position = "end",
	[int]$ReferenceLine = 0,
	[string]$ReferenceText = "",
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_line_move.ps1 -Path <file> -Key <key> [-FieldPath steps] -Line <n> -Position before -ReferenceLine <n>

For full node paths, preferred:
  json_node_edit.ps1 -Operation move-line -Path <file> -Node content.item.steps -Line <n> -Position before -ReferenceLine <n>
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }
if ($Line -le 0) { throw "-Line must be greater than 0. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "move-line", $Path, $Key, "--line", [string]$Line, "--position", $Position)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($FieldPath -ne "") { $arguments += @("--field-path", $FieldPath) }
if ($ReferenceLine -gt 0) { $arguments += @("--reference-line", [string]$ReferenceLine) }
if ($ReferenceText -ne "") { $arguments += @("--reference-text", $ReferenceText) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_line_move failed with exit code $LASTEXITCODE"
}
