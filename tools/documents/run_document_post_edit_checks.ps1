param(
	[Parameter(Mandatory = $true)]
	[string[]]$Paths,
	[switch]$NoCache,
	[switch]$Audit,
	[switch]$NoAudit
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..")
$normalizeScript = Join-Path $repoRoot "tools\text\normalize_text_files.ps1"
$cacheScript = Join-Path $PSScriptRoot "build_document_cache.ps1"
$checkScript = Join-Path $repoRoot "tools\repo\check_task.ps1"

function Get-RelativePath {
	param(
		[string]$Path
	)

	$resolved = (Resolve-Path -LiteralPath $Path).Path
	$root = $repoRoot.Path.TrimEnd([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
	if ($resolved.StartsWith($root, [System.StringComparison]::OrdinalIgnoreCase)) {
		return $resolved.Substring($root.Length).TrimStart([System.IO.Path]::DirectorySeparatorChar, [System.IO.Path]::AltDirectorySeparatorChar)
	}
	return $resolved
}

Push-Location -LiteralPath $repoRoot
try {
	$normalizedPaths = New-Object System.Collections.Generic.List[string]
	foreach ($path in $Paths) {
		foreach ($candidate in ($path -split ",")) {
			$trimmed = $candidate.Trim()
			if ($trimmed.Length -eq 0) {
				continue
			}
			$normalizedPaths.Add((Get-RelativePath -Path $trimmed))
		}
	}

	if ($normalizedPaths.Count -eq 0) {
		throw "run_document_post_edit_checks requires at least one path."
	}

	Write-Host "==> doc post-edit"
	& powershell -NoProfile -ExecutionPolicy Bypass -File $normalizeScript -Paths $normalizedPaths
	if ($LASTEXITCODE -ne 0) {
		throw "text normalization failed with exit code $LASTEXITCODE"
	}

	$checkPaths = New-Object System.Collections.Generic.List[string]
	foreach ($path in $normalizedPaths) {
		$checkPaths.Add($path)
	}

	$hasYaml = @($normalizedPaths | Where-Object { $_ -match '\.ya?ml$' }).Count -gt 0
	if ($hasYaml -and -not $NoCache) {
		& powershell -NoProfile -ExecutionPolicy Bypass -File $cacheScript | Out-Null
		if ($LASTEXITCODE -ne 0) {
			throw "doc cache rebuild failed with exit code $LASTEXITCODE"
		}
		$cachePath = "docs-tech\cache\doc_index.json"
		if (Test-Path -LiteralPath $cachePath) {
			$checkPaths.Add($cachePath)
		}
	}

	$checkArgs = @(
		"-NoProfile",
		"-ExecutionPolicy",
		"Bypass",
		"-File",
		$checkScript,
		"-Paths"
	)
	$checkArgs += $checkPaths
	$checkArgs += @("-NoNormalize", "-NoLineIndex", "-NoStat", "-NoStatus")
	if ($Audit -and -not $NoAudit) {
		$checkArgs += "-Audit"
	}

	& powershell @checkArgs
	if ($LASTEXITCODE -ne 0) {
		throw "document post-edit check failed with exit code $LASTEXITCODE"
	}

	Write-Host ("OK: document edit pipeline completed for {0} file(s)." -f $normalizedPaths.Count)
} finally {
	Pop-Location
}
