param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[string[]]$Text = @(),
	[string]$ValueJson = "",
	[string]$ValueJsonFile = "",
	[switch]$ValueJsonStdin,
	[string]$NewKey = "",
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

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
