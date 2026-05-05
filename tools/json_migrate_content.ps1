param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$SourceKey
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "json_list_doc.py"
& $python $script migrate-content $Path $SourceKey
if ($LASTEXITCODE -ne 0) {
	throw "json_migrate_content failed with exit code $LASTEXITCODE"
}
