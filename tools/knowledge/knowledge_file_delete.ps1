param(
	[Parameter(Mandatory = $true)]
	[string[]]$Path,
	[string]$Name = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
	$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
	if ($null -eq $pythonCommand) {
		throw "Python is required for knowledge file fallback deletes."
	}
	$python = $pythonCommand.Source
}

$arguments = @($tool, "file-delete", "--repo-root", $repoRoot)
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
