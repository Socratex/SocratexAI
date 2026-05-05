param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Key = "",
	[int]$Line = 0,
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "read", $Path)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($Key -ne "") { $arguments += $Key }
if ($Line -gt 0) { $arguments += @("--line", [string]$Line) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_read failed with exit code $LASTEXITCODE"
}
