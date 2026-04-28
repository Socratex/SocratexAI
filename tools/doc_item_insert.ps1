param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[string]$Title = "",
	[string]$Content = "",
	[string]$ContentFile = "",
	[string]$ItemFile = "",
	[ValidateSet("start", "end")]
	[string]$Position = "end",
	[string]$Before = "",
	[string]$After = "",
	[switch]$AllowEmpty,
	[switch]$Replace
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "doc_item.py"
$arguments = @($script, "insert", $Path, $Key, "--position", $Position)
if ($Title -ne "") { $arguments += @("--title", $Title) }
if ($Content -ne "") { $arguments += @("--content", $Content) }
if ($ContentFile -ne "") { $arguments += @("--content-file", $ContentFile) }
if ($ItemFile -ne "") { $arguments += @("--item-file", $ItemFile) }
if ($Before -ne "") { $arguments += @("--before", $Before) }
if ($After -ne "") { $arguments += @("--after", $After) }
if ($AllowEmpty) { $arguments += "--allow-empty" }
if ($Replace) { $arguments += "--replace" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "doc_item_insert failed with exit code $LASTEXITCODE"
}
