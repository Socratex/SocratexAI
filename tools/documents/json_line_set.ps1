param(
	[string]$Path = "",
	[string]$Key = "",
	[int]$Line = 0,
	[string]$Text = "",
	[string]$FieldPath = "",
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_line_set.ps1 -Path <file> -Key <key> [-FieldPath steps] -Line <n> -Text <line>

For full node paths, preferred:
  json_node_edit.ps1 -Operation set-line -Path <file> -Node content.item.steps -Line <n> -Text <line>
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }
if ($Line -le 0) { throw "-Line must be greater than 0. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "set-line", $Path, $Key, "--line", [string]$Line, "--text", $Text)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($FieldPath -ne "") { $arguments += @("--field-path", $FieldPath) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_line_set failed with exit code $LASTEXITCODE"
}
