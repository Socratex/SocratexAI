param(
	[switch]$Check,
	[switch]$AllHosts,
	[switch]$EnableProfileExecution
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$profilePaths = @($PROFILE.CurrentUserCurrentHost)
if ($AllHosts) {
	$profilePaths += $PROFILE.CurrentUserAllHosts
}
$profilePaths = @($profilePaths | Sort-Object -Unique)

$beginMarker = "# SocratexPipeline UTF-8 console setup - begin"
$endMarker = "# SocratexPipeline UTF-8 console setup - end"
$block = @"
$beginMarker
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new(`$false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new(`$false)
`$OutputEncoding = [System.Text.UTF8Encoding]::new(`$false)
try { chcp 65001 > `$null } catch {}
$endMarker
"@

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$missingProfiles = New-Object System.Collections.Generic.List[string]

if ($EnableProfileExecution -and -not $Check) {
	Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
	Write-Host "OK: set CurrentUser execution policy to RemoteSigned so the PowerShell profile can load."
}

foreach ($profilePath in $profilePaths) {
	$profileDir = Split-Path -Parent $profilePath
	if (-not (Test-Path -LiteralPath $profileDir)) {
		if ($Check) {
			$missingProfiles.Add($profilePath)
			continue
		}
		New-Item -ItemType Directory -Force -Path $profileDir | Out-Null
	}

	$content = ""
	if (Test-Path -LiteralPath $profilePath) {
		$content = [System.IO.File]::ReadAllText($profilePath, [System.Text.Encoding]::UTF8)
	}

	if ($content.Contains($beginMarker) -and $content.Contains($endMarker)) {
		Write-Host "OK: UTF-8 profile block already exists in $profilePath"
		continue
	}

	if ($Check) {
		$missingProfiles.Add($profilePath)
		continue
	}

	$prefix = $content.TrimEnd()
	if ($prefix.Length -gt 0) {
		$updated = "$prefix`n`n$block`n"
	} else {
		$updated = "$block`n"
	}
	[System.IO.File]::WriteAllText($profilePath, $updated, $utf8NoBom)
	Write-Host "OK: added UTF-8 profile block to $profilePath"
}

if ($Check -and $missingProfiles.Count -gt 0) {
	Write-Host "ERROR: UTF-8 profile block is missing from:"
	foreach ($profilePath in $missingProfiles) {
		Write-Host " - $profilePath"
	}
	exit 1
}

Write-Host "OK: PowerShell UTF-8 profile configuration checked"
