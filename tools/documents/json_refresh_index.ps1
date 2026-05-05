param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Collection = "content"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "refresh-index", $Path)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_refresh_index failed with exit code $LASTEXITCODE"
}
