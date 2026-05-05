param(
	[string]$OutputPath = "",
	[string]$CompletionSoundScriptPath = $env:CODEX_COMPLETION_SOUND_SCRIPT,
	[int]$StateTailLines = 80,
	[int]$MaxListItems = 40,
	[switch]$NoSound
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
	$OutputPath = Join-Path $repoRoot "OUTPUT"
}

function Add-Section {
	param(
		[System.Collections.Generic.List[string]]$Lines,
		[string]$Title
	)

	$Lines.Add("")
	$Lines.Add("## $Title")
}

function Invoke-CapturedCommand {
	param(
		[string]$Command,
		[string[]]$Arguments = @()
	)

	try {
		$previousErrorActionPreference = $ErrorActionPreference
		$ErrorActionPreference = "Continue"
		$output = & $Command @Arguments 2>&1
		$exitCode = $LASTEXITCODE
		$ErrorActionPreference = $previousErrorActionPreference
		if ($exitCode -ne 0) {
			return @("command failed: $Command $($Arguments -join ' ')", "exit code: $exitCode") + @($output)
		}
		if ($null -eq $output) {
			return @()
		}
		return @($output)
	} catch {
		if ($null -ne $previousErrorActionPreference) {
			$ErrorActionPreference = $previousErrorActionPreference
		}
		return @("command failed: $Command $($Arguments -join ' ')", $_.Exception.Message)
	}
}

function Remove-LocalGitLineEndingWarnings {
	param([object[]]$Output)

	return @($Output | Where-Object {
		([string]$_) -notmatch "^warning: in the working copy of '.+', (LF|CRLF) will be replaced by (LF|CRLF) the next time Git touches it$"
	})
}

function Add-CommandOutput {
	param(
		[System.Collections.Generic.List[string]]$Lines,
		[string]$Title,
		[string]$Command,
		[string[]]$Arguments = @(),
		[int]$MaxLines = 80
	)

	Add-Section -Lines $Lines -Title $Title
	$output = @(Invoke-CapturedCommand -Command $Command -Arguments $Arguments)
	if ($Command -eq "git") {
		$output = @(Remove-LocalGitLineEndingWarnings -Output $output)
	}
	if ($output.Count -eq 0) {
		$Lines.Add("(no output)")
		return
	}

	foreach ($line in ($output | Select-Object -First $MaxLines)) {
		$Lines.Add([string]$line)
	}
	if ($output.Count -gt $MaxLines) {
		$Lines.Add("... truncated $($output.Count - $MaxLines) lines")
	}
}

function Get-GitTrackedRecentFiles {
	param([int]$Limit)

	$tracked = Remove-LocalGitLineEndingWarnings -Output @(Invoke-CapturedCommand -Command "git" -Arguments @("diff", "--name-only", "HEAD"))
	$untracked = Remove-LocalGitLineEndingWarnings -Output @(Invoke-CapturedCommand -Command "git" -Arguments @("ls-files", "--others", "--exclude-standard"))
	return @($tracked + $untracked |
		Where-Object { -not [string]::IsNullOrWhiteSpace([string]$_) } |
		Sort-Object -Unique |
		Select-Object -First $Limit)
}

function Add-QualityGateSummary {
	param([System.Collections.Generic.List[string]]$Lines)

	Add-Section -Lines $Lines -Title "Last Quality Gate Log"
	$candidates = @()
	$searchRoots = @(
		(Join-Path $repoRoot "Tools\tmp"),
		(Join-Path $repoRoot "logs"),
		(Join-Path $repoRoot ".")
	)

	foreach ($root in $searchRoots) {
		if (-not (Test-Path -LiteralPath $root)) {
			continue
		}
		$candidates += Get-ChildItem -LiteralPath $root -File -Recurse -ErrorAction SilentlyContinue |
			Where-Object {
				$_.Name -match "(quality|gate|gdlint|gdformat|headless)" -and
				$_.Extension -in @(".log", ".txt", ".out")
			}
	}

	$latest = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
	if ($null -eq $latest) {
		$Lines.Add("No quality gate log file found.")
		return
	}

	$Lines.Add("File: $($latest.FullName)")
	$Lines.Add("Modified: $($latest.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))")
	$content = @(Get-Content -LiteralPath $latest.FullName -Tail 80 -ErrorAction SilentlyContinue)
	if ($null -eq $content -or $content.Count -eq 0) {
		$Lines.Add("(empty)")
		return
	}
	foreach ($line in $content) {
		$Lines.Add([string]$line)
	}
}

function Add-ConsoleLogSummary {
	param([System.Collections.Generic.List[string]]$Lines)

	Add-Section -Lines $Lines -Title "CONSOLE-LOG Errors And Warnings"
	$consoleLogPath = Join-Path $repoRoot "CONSOLE-LOG"
	if (-not (Test-Path -LiteralPath $consoleLogPath)) {
		$Lines.Add("CONSOLE-LOG is missing.")
		return
	}

	$item = Get-Item -LiteralPath $consoleLogPath
	$Lines.Add("Present: yes")
	$Lines.Add("Modified: $($item.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss"))")

	$matches = @(Select-String -LiteralPath $consoleLogPath -Pattern "ERROR|WARNING|SCRIPT ERROR|GDScript backtrace" -CaseSensitive:$false -ErrorAction SilentlyContinue |
		Select-Object -Last 80)
	if ($null -eq $matches -or $matches.Count -eq 0) {
		$Lines.Add("No ERROR/WARNING lines found.")
		return
	}

	foreach ($match in $matches) {
		$Lines.Add("$($match.LineNumber): $($match.Line)")
	}
}

function Add-DebugLogPairSummary {
	param([System.Collections.Generic.List[string]]$Lines)

	Add-Section -Lines $Lines -Title "Debug Log Pairs"
	$logsRoot = Join-Path $repoRoot "logs"
	if (-not (Test-Path -LiteralPath $logsRoot)) {
		$Lines.Add("logs/ is missing.")
		return
	}

	$jsonLogs = @(Get-ChildItem -LiteralPath $logsRoot -File -Filter "*.json" -ErrorAction SilentlyContinue |
		Sort-Object LastWriteTime -Descending |
		Select-Object -First $MaxListItems)
	if ($null -eq $jsonLogs -or $jsonLogs.Count -eq 0) {
		$Lines.Add("No root logs/*.json debug dumps found.")
	} else {
		foreach ($log in $jsonLogs) {
			$pngPath = Join-Path $log.DirectoryName "$($log.BaseName).png"
			$pngStatus = if (Test-Path -LiteralPath $pngPath) { "png=yes" } else { "png=no" }
			$Lines.Add("$($log.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")) $($log.Name) $pngStatus")
		}
	}

	$diagnosticsRoot = Join-Path $repoRoot "logs-diagnostics"
	if (Test-Path -LiteralPath $diagnosticsRoot) {
		$diagnostics = @(Get-ChildItem -LiteralPath $diagnosticsRoot -File -ErrorAction SilentlyContinue |
			Sort-Object LastWriteTime -Descending |
			Select-Object -First $MaxListItems)
		if ($null -ne $diagnostics -and $diagnostics.Count -gt 0) {
			$Lines.Add("")
			$Lines.Add("Diagnostics:")
			foreach ($file in $diagnostics) {
				$Lines.Add("$($file.LastWriteTime.ToString("yyyy-MM-dd HH:mm:ss")) $($file.Name)")
			}
		}
	}
}

function Add-StateTail {
	param([System.Collections.Generic.List[string]]$Lines)

	Add-Section -Lines $Lines -Title "docs-tech/STATE.json Summary"
	$statePath = Join-Path $repoRoot "docs-tech/STATE.json"
	if (-not (Test-Path -LiteralPath $statePath)) {
		$Lines.Add("docs-tech/STATE.json is missing.")
		return
	}

	$docRead = Join-Path $PSScriptRoot "doc_read.ps1"
	if (Test-Path -LiteralPath $docRead) {
		foreach ($selector in @("current", "immediate_focus", "risks")) {
			$Lines.Add("")
			$Lines.Add("### $selector")
			$output = @(Invoke-CapturedCommand -Command "powershell.exe" -Arguments @(
				"-NoProfile",
				"-ExecutionPolicy",
				"Bypass",
				"-File",
				$docRead,
				"docs-tech/STATE.json",
				$selector
			))
			foreach ($line in ($output | Select-Object -First $StateTailLines)) {
				$Lines.Add([string]$line)
			}
		}
		return
	}

	$Lines.Add("JSON reader unavailable; using raw tail fallback.")
	foreach ($line in (Get-Content -LiteralPath $statePath -Tail $StateTailLines)) {
		$Lines.Add([string]$line)
	}
}

Push-Location -LiteralPath $repoRoot
try {
	$lines = [System.Collections.Generic.List[string]]::new()
	$lines.Add("# Prompt Snapshot")
	$lines.Add("Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz")")
	$lines.Add("Repository: $repoRoot")

	Add-CommandOutput -Lines $lines -Title "Git Branch" -Command "git" -Arguments @("branch", "--show-current") -MaxLines 10
	Add-CommandOutput -Lines $lines -Title "Last Commit" -Command "git" -Arguments @("log", "-1", "--oneline", "--decorate") -MaxLines 10
	Add-CommandOutput -Lines $lines -Title "Git Status Short" -Command "git" -Arguments @("status", "--short") -MaxLines 120
	Add-CommandOutput -Lines $lines -Title "Staged Diff Summary" -Command "git" -Arguments @("diff", "--cached", "--stat") -MaxLines 80
	Add-CommandOutput -Lines $lines -Title "Unstaged Diff Summary" -Command "git" -Arguments @("diff", "--stat") -MaxLines 80

	Add-Section -Lines $lines -Title "Recently Changed Files"
	$recentFiles = @(Get-GitTrackedRecentFiles -Limit $MaxListItems)
	if ($recentFiles.Count -eq 0) {
		$lines.Add("(none)")
	} else {
		foreach ($file in $recentFiles) {
			$lines.Add([string]$file)
		}
	}

	Add-CommandOutput -Lines $lines -Title "Untracked Files" -Command "git" -Arguments @("ls-files", "--others", "--exclude-standard") -MaxLines 120
	Add-QualityGateSummary -Lines $lines
	Add-ConsoleLogSummary -Lines $lines
	Add-DebugLogPairSummary -Lines $lines
	Add-StateTail -Lines $lines

	Set-Content -LiteralPath $OutputPath -Value $lines -Encoding UTF8
	Write-Host "Prompt snapshot written to: $OutputPath"
} finally {
	Pop-Location
}

if (-not $NoSound) {
	if (-not [string]::IsNullOrWhiteSpace($CompletionSoundScriptPath) -and (Test-Path -LiteralPath $CompletionSoundScriptPath)) {
		Start-Process powershell.exe -ArgumentList @(
			"-ExecutionPolicy",
			"Bypass",
			"-File",
			$CompletionSoundScriptPath,
			"-TestSound"
		) -WindowStyle Hidden
	} else {
		[Console]::Beep(1100, 250)
	}
}
