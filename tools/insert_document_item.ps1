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
	[switch]$Replace,
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_item_edit_engine.py"
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
	throw "insert_document_item failed with exit code $LASTEXITCODE"
}

if (-not $NoPostEdit) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $Path
	if ($LASTEXITCODE -ne 0) {
		throw "insert_document_item post-edit pipeline failed with exit code $LASTEXITCODE"
	}
}
