param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[Parameter(Mandatory = $true)]
	[string[]]$Text,
	[ValidateSet("start", "end", "before", "after")]
	[string]$Position = "end",
	[int]$ReferenceLine = 0,
	[string]$ReferenceText = "",
	[string]$Collection = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "json_list_doc.py"
$arguments = @($script, "insert-line", $Path, $Key, "--position", $Position)
if ($Collection -ne "") { $arguments += @("--collection", $Collection) }
if ($ReferenceLine -gt 0) { $arguments += @("--reference-line", [string]$ReferenceLine) }
if ($ReferenceText -ne "") { $arguments += @("--reference-text", $ReferenceText) }
foreach ($line in $Text) { $arguments += @("--text", $line) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "json_line_insert failed with exit code $LASTEXITCODE"
}
