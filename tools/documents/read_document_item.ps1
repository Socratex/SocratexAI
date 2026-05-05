param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Selector,
	[switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_read_cache_engine.py"
$arguments = @($script, "read", $Path, $Selector)
if ($Json) {
	$arguments += "--json"
}

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "read_document_item failed with exit code $LASTEXITCODE"
}
