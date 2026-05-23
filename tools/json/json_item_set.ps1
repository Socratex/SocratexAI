param(
	[string]$Path = "",
	[string]$Key = "",
	[string[]]$Text = @(),
	[string]$ValueJson = "",
	[string]$ValueJsonFile = "",
	[switch]$ValueJsonStdin,
	[string]$NewKey = "",
	[string]$Collection = "",
	[switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if ($Help) {
	@"
Usage:
  json_item_set.ps1 -Path <file> -Key <key> [-Collection content] [-NewKey <key>] (-ValueJson|-ValueJsonFile|-ValueJsonStdin|-Text)

For full node paths such as content.pass.steps, prefer:
  json_node_edit.ps1 -Operation set -Path <file> -Node <node> ...
"@
	exit 0
}

if ([string]::IsNullOrWhiteSpace($Path)) { throw "-Path is required. Use -Help for examples." }
if ([string]::IsNullOrWhiteSpace($Key)) { throw "-Key is required. Use -Help for examples." }

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "set-entry", $Path, $Key)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($NewKey -ne "") { $arguments += @("--new-key", $NewKey) }

$valueSourceCount = 0
if ($Text.Count -gt 0) { $valueSourceCount++ }
if ($ValueJson -ne "") { $valueSourceCount++ }
if ($ValueJsonFile -ne "") { $valueSourceCount++ }
if ($ValueJsonStdin) { $valueSourceCount++ }
if ($valueSourceCount -gt 1) {
	throw "Use only one of -Text, -ValueJson, -ValueJsonFile, or -ValueJsonStdin."
}

foreach ($line in $Text) { $arguments += @("--text", $line) }
if ($ValueJson -ne "") { $arguments += @("--value-json", $ValueJson) }
if ($ValueJsonFile -ne "") {
	$resolvedValueJsonFile = (Resolve-Path -LiteralPath $ValueJsonFile).Path
	$arguments += @("--value-json-file", $resolvedValueJsonFile)
}
if ($ValueJsonStdin) { $arguments += "--value-json-stdin" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_item_set failed with exit code $LASTEXITCODE"
}
