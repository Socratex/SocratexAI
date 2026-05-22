param(
	[string]$Path = "",
	[string]$Key = "",
	[string[]]$Text = @(),
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
  json_line_insert.ps1 -Path <file> -Key <key> [-FieldPath steps] -Text <line> [-Position before -ReferenceText <line>]

For full node paths, preferred:
  json_node_edit.ps1 -Operation insert-line -Path <file> -Node content.item.steps -Text <line>
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }
if ($Text.Count -eq 0) { throw "-Text is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "insert-line", $Path, $Key, "--position", $Position)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($FieldPath -ne "") { $arguments += @("--field-path", $FieldPath) }
if ($ReferenceLine -gt 0) { $arguments += @("--reference-line", [string]$ReferenceLine) }
if ($ReferenceText -ne "") { $arguments += @("--reference-text", $ReferenceText) }
foreach ($line in $Text) { $arguments += @("--text", $line) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_line_insert failed with exit code $LASTEXITCODE"
}
