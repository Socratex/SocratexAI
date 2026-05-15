param(
	[Parameter(Mandatory = $true)]
	[string]$Path,
	[Parameter(Mandatory = $true)]
	[string]$Key,
	[ValidateSet("start", "end")]
	[string]$Position = "end",
	[string]$Before = "",
	[string]$After = "",
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$script = Join-Path $PSScriptRoot "document_item_edit_engine.py"
$arguments = @($script, "move", $Path, $Key, "--position", $Position)
if ($Before -ne "") { $arguments += @("--before", $Before) }
if ($After -ne "") { $arguments += @("--after", $After) }

& $python @arguments
if ($LASTEXITCODE -ne 0) {
	throw "move_document_item failed with exit code $LASTEXITCODE"
}

if (-not $NoPostEdit) {
	& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $Path
	if ($LASTEXITCODE -ne 0) {
		throw "move_document_item post-edit pipeline failed with exit code $LASTEXITCODE"
	}
}
