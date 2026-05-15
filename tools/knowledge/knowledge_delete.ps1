param(
	[Parameter(Mandatory = $true)]
	[string[]]$Path,
	[string]$Name = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

$arguments = @($tool, "delete", "--repo-root", $repoRoot)
foreach ($item in $Path) {
	$arguments += @("--path", $item)
}
if ($Name -ne "") {
	$arguments += @("--name", $Name)
}

Push-Location -LiteralPath $repoRoot
try {
	& $python @arguments
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
} finally {
	Pop-Location
}
