param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[string]$Key = "",
	[ValidateSet("item", "document")]
	[string]$Scope = "document",
	[string]$Text = "",
	[string]$Url = "",
	[string[]]$Terms = @(),
	[int]$Limit = 12,
	[switch]$Json,
	[switch]$FailOnDuplicate
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_list_item_edit_engine.py"
$arguments = @($script, "check", $Path, "--scope", $Scope)
if ($Key -ne "") { $arguments += @("--key", $Key) }
if ($Text -ne "") { $arguments += @("--text", $Text) }
if ($Url -ne "") { $arguments += @("--url", $Url) }
if ($Terms.Count -gt 0) { $arguments += @("--terms") + $Terms }
if ($Limit -ne 12) { $arguments += @("--limit", [string]$Limit) }
if ($Json) { $arguments += "--json" }
if ($FailOnDuplicate) { $arguments += "--fail-on-duplicate" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "check_document_list_item_duplicates failed with exit code $LASTEXITCODE"
}
