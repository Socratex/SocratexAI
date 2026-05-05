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
	[switch]$Audit,
	[switch]$MarkdownEmoji,
	[switch]$NoLineIndex,
	[switch]$NoNormalize,
	[switch]$NoStat,
	[switch]$NoStatus
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$insertScript = Join-Path $PSScriptRoot "insert_document_list_item.ps1"
$checkScript = Join-Path $PSScriptRoot "check_task.ps1"

$insertArgs = @(
	"-Path",
	$Path,
	"-Key",
	$Key,
	"-Text",
	$Text,
	"-DuplicateScope",
	$DuplicateScope
)
if ($Url -ne "") { $insertArgs += @("-Url", $Url) }
if ($CreateTitle -ne "") { $insertArgs += @("-CreateTitle", $CreateTitle) }
if ($AllowDuplicate) { $insertArgs += "-AllowDuplicate" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $insertScript @insertArgs
if ($LASTEXITCODE -ne 0) {
	throw "insert_checked_document_list_item insert failed with exit code $LASTEXITCODE"
}

$checkArgs = @("-Paths", $Path)
if ($Audit) { $checkArgs += "-Audit" }
if ($MarkdownEmoji) { $checkArgs += "-MarkdownEmoji" }
if ($NoLineIndex) { $checkArgs += "-NoLineIndex" }
if ($NoNormalize) { $checkArgs += "-NoNormalize" }
if ($NoStat) { $checkArgs += "-NoStat" }
if ($NoStatus) { $checkArgs += "-NoStatus" }

& powershell -NoProfile -ExecutionPolicy Bypass -File $checkScript @checkArgs
if ($LASTEXITCODE -ne 0) {
	throw "insert_checked_document_list_item task check failed with exit code $LASTEXITCODE"
}
