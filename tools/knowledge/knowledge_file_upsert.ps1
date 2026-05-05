param(
	[Parameter(Mandatory = $true)]
	[string[]]$Path
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
	$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
	if ($null -eq $pythonCommand) {
		throw "Python is required for knowledge file fallback upserts."
	}
	$python = $pythonCommand.Source
}

$arguments = @($tool, "file-upsert", "--repo-root", $repoRoot)
foreach ($item in $Path) {
	$arguments += @("--path", $item)
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
