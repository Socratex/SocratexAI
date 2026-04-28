param(
	[Parameter(Mandatory = $true)]
	[string]$Source,
	[Parameter(Mandatory = $true)]
	[string]$Target,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[ValidateSet("start", "end")]
	[string]$Position = "end",
	[string]$Before = "",
	[string]$After = "",
	[switch]$KeepSource,
	[switch]$Replace
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "doc_item.py"
$arguments = @($script, "migrate", $Source, $Target, $Key, "--position", $Position)
if ($Before -ne "") { $arguments += @("--before", $Before) }
if ($After -ne "") { $arguments += @("--after", $After) }
if ($KeepSource) { $arguments += "--keep-source" }
if ($Replace) { $arguments += "--replace" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "doc_item_migrate failed with exit code $LASTEXITCODE"
}
