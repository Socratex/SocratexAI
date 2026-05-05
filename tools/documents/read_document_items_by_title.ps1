param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string[]]$Titles,
	[switch]$Json
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_list_item_edit_engine.py"
$arguments = @($script, "read-titles", $Path, "--titles") + $Titles
if ($Json) { $arguments += "--json" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "read_document_items_by_title failed with exit code $LASTEXITCODE"
}
