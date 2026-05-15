Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$tool = Join-Path $PSScriptRoot "knowledge_index.py"
$fileCompileScript = Join-Path $PSScriptRoot "knowledge_file_compile.ps1"
. (Join-Path $PSScriptRoot "..\pipeline\resolve_tool_runtime.ps1")
$python = Resolve-SocratexPython -SearchRoot $PSScriptRoot

Push-Location -LiteralPath $repoRoot
try {
	& $python $tool compile --repo-root $repoRoot
	$dbExitCode = $LASTEXITCODE
	if ($dbExitCode -ne 0) {
		Write-Warning "SQLite knowledge compile failed with exit code $dbExitCode. Falling back to compiled JSON table files."
		& powershell -NoProfile -ExecutionPolicy Bypass -File $fileCompileScript
		if ($LASTEXITCODE -ne 0) {
			exit $LASTEXITCODE
		}
		exit 0
	}
	if (Test-Path -LiteralPath $fileCompileScript -PathType Leaf) {
		& powershell -NoProfile -ExecutionPolicy Bypass -File $fileCompileScript
		if ($LASTEXITCODE -ne 0) {
			exit $LASTEXITCODE
		}
	}
} finally {
	Pop-Location
}
