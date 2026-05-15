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
	[switch]$Replace,
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "document_item_edit_engine.py"
$arguments = @($script, "migrate", $Source, $Target, $Key, "--position", $Position)
if ($Before -ne "") { $arguments += @("--before", $Before) }
if ($After -ne "") { $arguments += @("--after", $After) }
if ($KeepSource) { $arguments += "--keep-source" }
if ($Replace) { $arguments += "--replace" }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "migrate_document_item failed with exit code $LASTEXITCODE"
}

if (-not $NoPostEdit) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $Source,$Target
	if ($LASTEXITCODE -ne 0) {
		throw "migrate_document_item post-edit pipeline failed with exit code $LASTEXITCODE"
	}
}
