Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
$fileCheckScript = Join-Path $PSScriptRoot "knowledge_file_check.ps1"
$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
	$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
	if ($null -eq $pythonCommand) {
		throw "Python is required for knowledge index checks."
	}
	$python = $pythonCommand.Source
}

Push-Location -LiteralPath $repoRoot
try {
	& $python $tool check --repo-root $repoRoot
	if ($LASTEXITCODE -ne 0) {
		$dbExitCode = $LASTEXITCODE
		if (Test-Path -LiteralPath $fileCheckScript -PathType Leaf) {
			Write-Warning "SQLite knowledge check failed with exit code $dbExitCode. Checking compiled JSON table fallback."
			& powershell -NoProfile -ExecutionPolicy Bypass -File $fileCheckScript
			if ($LASTEXITCODE -eq 0) {
				exit 0
			}
		}
		exit $dbExitCode
	}
} finally {
	Pop-Location
}
