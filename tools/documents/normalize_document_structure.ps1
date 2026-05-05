param(
	[string[]]$Paths = @("**/*.json"),
	[switch]$Check,
	[switch]$NoPostEdit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$python = Join-Path $PSScriptRoot "..\Python312\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
	$python = "python"
}

$script = Join-Path $PSScriptRoot "document_structure_normalizer_engine.py"
$arguments = @(
	$script,
	"--repo-root",
	$repoRoot
)
if ($Check) {
	$arguments += "--check"
}
$arguments += $Paths

$output = @(& $python @arguments)
$exitCode = $LASTEXITCODE
foreach ($line in $output) {
	Write-Host $line
}
if ($exitCode -ne 0) {
	throw "normalize_document_structure failed with exit code $exitCode"
}

if ((-not $Check) -and (-not $NoPostEdit)) {
	$changedPaths = @($output | Where-Object {
		$trimmed = $_.Trim()
		$trimmed.Length -gt 0 -and
			-not $trimmed.StartsWith("OK:") -and
			-not $trimmed.StartsWith("WARNING:") -and
			(Test-Path -LiteralPath $trimmed -PathType Leaf)
	})

	if ($changedPaths.Count -gt 0) {
		& powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "run_document_post_edit_checks.ps1") -Paths $changedPaths
		if ($LASTEXITCODE -ne 0) {
			throw "normalize_document_structure post-edit pipeline failed with exit code $LASTEXITCODE"
		}
	}
}
