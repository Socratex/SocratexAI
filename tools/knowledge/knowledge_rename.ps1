param(
	[Parameter(Mandatory = $true)]
	[string]$OldPath,
	[Parameter(Mandatory = $true)]
	[string]$NewPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
	$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
	if ($null -eq $pythonCommand) {
		throw "Python is required for knowledge index renames."
	}
	$python = $pythonCommand.Source
}

Push-Location -LiteralPath $repoRoot
try {
	& $python $tool rename --repo-root $repoRoot --old-path $OldPath --new-path $NewPath
	if ($LASTEXITCODE -ne 0) {
		exit $LASTEXITCODE
	}
} finally {
	Pop-Location
}
