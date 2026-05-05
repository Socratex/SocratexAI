param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[Parameter(Mandatory = $true)]
	[string]$Text,
	[string]$Url = "",
	[ValidateSet("item", "document")]
	[string]$DuplicateScope = "document",
	[string]$CreateTitle = "",
	[switch]$AllowDuplicate,
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_list_item_edit_engine.py"
$arguments = @($script, "insert", $Path, $Key, "--text", $Text, "--scope", $DuplicateScope)
if ($Url -ne "") { $arguments += @("--url", $Url) }
if ($CreateTitle -ne "") { $arguments += @("--create-title", $CreateTitle) }
if ($AllowDuplicate) { $arguments += "--allow-duplicate" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "insert_document_list_item failed with exit code $LASTEXITCODE"
}

if (-not $NoPostEdit) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $Path
	if ($LASTEXITCODE -ne 0) {
		throw "insert_document_list_item post-edit pipeline failed with exit code $LASTEXITCODE"
	}
}
